# Copyright 2015 Internap.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from functools import partial

import re
from fake_switches.command_processing.switch_tftp_parser import SwitchTftpParser
from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.cisco.command_processor.config import ConfigCommandProcessor
from fake_switches.switch_configuration import VlanPort
from fake_switches import group_sequences



class EnabledCommandProcessor(BaseCommandProcessor):

    def get_prompt(self):
        return self.switch_configuration.name + "#"

    def do_enable(self, *args):
        pass

    def do_configure(self, *_):
        self.write_line("Enter configuration commands, one per line.  End with CNTL/Z.")
        self.move_to(ConfigCommandProcessor)

    def do_show(self, *args):
        if "running-config".startswith(args[0]):
            if len(args) < 2:
                self.show_run()
            elif "vlan".startswith(args[1]):
                self.write_line("Building configuration...")
                self.write_line("")
                self.write_line("Current configuration:")
                for vlan in self.switch_configuration.vlans:
                    if vlan.number == int(args[2]):
                        self.write_line("\n".join(["!"] + build_running_vlan(vlan)))
                self.write_line("end")
                self.write_line("")
            elif "interface".startswith(args[1]):
                if_name = "".join(args[2:])
                port = self.switch_configuration.get_port_by_partial_name(if_name)

                if port:
                    self.write_line("Building configuration...")
                    self.write_line("")

                    data = ["!"] + build_running_interface(port) + ["end", ""]

                    self.write_line("Current configuration : %i bytes" % (len("\n".join(data)) + 1))
                    [self.write_line(l) for l in data]
                else:
                    self.write_line("                               ^")
                    self.write_line("% Invalid input detected at '^' marker.")
                    self.write_line("")

        elif "vlan".startswith(args[0]):
            self.write_line("")
            self.write_line("VLAN Name                             Status    Ports")
            self.write_line("---- -------------------------------- --------- -------------------------------")
            for vlan in sorted(self.switch_configuration.vlans, key=lambda v: v.number):
                ports = [port.get_subname(length=2) for port in self.switch_configuration.ports
                         if port.access_vlan == vlan.number or (vlan.number == 1 and port.access_vlan is None)]
                self.write_line("%-4s %-32s %s%s" % (
                    vlan.number,
                     vlan_name(vlan) if vlan_name(vlan) else "VLAN%s" % vlan.number,
                    "active",
                    ("    " + ", ".join(ports)) if ports else ""
                ))
            if len(args) == 1:
                self.write_line("")
                self.write_line("VLAN Type  SAID       MTU   Parent RingNo BridgeNo Stp  BrdgMode Trans1 Trans2")
                self.write_line("---- ----- ---------- ----- ------ ------ -------- ---- -------- ------ ------")
                for vlan in sorted(self.switch_configuration.vlans, key=lambda v: v.number):
                    self.write_line("%-4s enet  10%04d     1500  -      -      -        -    -        0      0" % (vlan.number, vlan.number))
                self.write_line("")
                self.write_line("Remote SPAN VLANs")
                self.write_line("------------------------------------------------------------------------------")
                self.write_line("")
                self.write_line("")
                self.write_line("Primary Secondary Type              Ports")
                self.write_line("------- --------- ----------------- ------------------------------------------")
                self.write_line("")
        elif "ip".startswith(args[0]):
            if "interface".startswith(args[1]):
                if_list = None
                if len(args) > 2:
                    interface = self.switch_configuration.get_port_by_partial_name("".join(args[2:]))
                    if interface:
                        if_list = [interface]
                    else:
                        self.write_line("                                 ^")
                        self.write_line("% Invalid input detected at '^' marker.")
                        self.write_line("")
                else:
                    if_list = sorted(self.switch_configuration.ports, key=lambda e: ("a" if isinstance(e, VlanPort) else "b") + e.name)
                if if_list:
                    for interface in if_list:
                        self.write_line("%s is down, line protocol is down" % interface.name)
                        if not isinstance(interface, VlanPort):
                            self.write_line("  Internet protocol processing disabled")
                        else:
                            if len(interface.ips) == 0:
                                self.write_line("  Internet protocol processing disabled")
                            else:
                                self.write_line("  Internet address is %s" % interface.ips[0])
                                for ip in interface.ips[1:]:
                                    self.write_line("  Secondary address %s" % ip)
                                self.write_line("  Outgoing access list is %s" % (interface.access_group_out if interface.access_group_out else "not set"))
                                self.write_line("  Inbound  access list is %s" % (interface.access_group_in if interface.access_group_in else "not set"))
                                if interface.vrf is not None:
                                    self.write_line("  VPN Routing/Forwarding \"%s\"" % interface.vrf.name)
            elif "route".startswith(args[1]):
                if "static".startswith(args[2]):
                    routes = self.switch_configuration.static_routes
                    for route in routes:
                        self.write_line("S        {0} [x/y] via {1}".format(route.destination, route.next_hop))
                self.write_line("")

    def do_copy(self, source_url, destination_url):
        dest_protocol, dest_file = destination_url.split(":")
        self.write("Destination filename [%s]? " % strip_leading_slash(dest_file))
        self.continue_to(partial(self.continue_validate_copy, source_url))

    def continue_validate_copy(self, source_url, _):
        self.write_line("Accessing %s..." % source_url)
        try:
            url, filename = re.match('tftp://([^/]*)/(.*)', source_url).group(1, 2)
            SwitchTftpParser(self.switch_configuration).parse(url, filename, ConfigCommandProcessor)
            self.write_line("Done (or some official message...)")
        except Exception as e:
            self.logger.warning("tftp parsing went wrong : %s" % str(e))
            self.write_line("Error opening %s (Timed out)" % source_url)

    def do_terminal(self, *args):
        pass

    def do_write(self, *args):
        pass

    def do_exit(self):
        self.is_done = True

    def show_run(self):

        all_data = [
            "version 12.1",
            "!",
            "hostname %s" % self.switch_configuration.name,
            "!",
            "!",
        ]
        for vlan in self.switch_configuration.vlans:
            all_data = all_data + build_running_vlan(vlan) + ["!"]
        for interface in sorted(self.switch_configuration.ports, key=lambda e: ("b" if isinstance(e, VlanPort) else "a") + e.name):
            all_data = all_data + build_running_interface(interface) + ["!"]
        if self.switch_configuration.static_routes:
            for route in self.switch_configuration.static_routes:
                all_data.append(build_static_routes(route))
            all_data.append("!")

        all_data += ["end", ""]

        self.write_line("Building configuration...")
        self.write_line("")

        self.write_line("Current configuration : %i bytes" % (len("\n".join(all_data)) + 1))
        [self.write_line(l) for l in all_data]


def strip_leading_slash(dest_file):
    return dest_file[1:]


def build_static_routes(route):
    return "ip route {0} {1} {2}".format(route.destination, route.mask, route.next_hop)

def build_running_vlan(vlan):
    data = [
        "vlan %s" % vlan.number,
    ]
    if vlan.name:
        data.append(" name %s" % vlan.name)
    return data


def build_running_interface(port):
    data = [
        "interface %s" % port.name
    ]
    if port.description:
        data.append(" description %s" % port.description)
    if port.access_vlan and port.access_vlan != 1:
        data.append(" switchport access vlan %s" % port.access_vlan)
    if port.trunk_encapsulation_mode is not None:
        data.append(" switchport trunk encapsulation %s" % port.trunk_encapsulation_mode)
    if port.trunk_native_vlan is not None:
        data.append(" switchport trunk native vlan %s" % port.trunk_native_vlan)
    if port.trunk_vlans is not None and len(port.trunk_vlans) < 4096 :
        data.append(" switchport trunk allowed vlan %s" % to_vlan_ranges(port.trunk_vlans))
    if port.mode:
        data.append(" switchport mode %s" % port.mode)
    if port.shutdown:
        data.append(" shutdown")
    if port.aggregation_membership:
        data.append(" channel-group %s mode active" % port.aggregation_membership[-1])
    if port.vrf:
        data.append(" ip vrf forwarding %s" % port.vrf.name)
    if isinstance(port, VlanPort):
        if len(port.ips) > 0:
            for ip in port.ips[1:]:
                data.append(" ip address %s %s secondary" % (ip.ip, ip.netmask))
            data.append(" ip address %s %s" % (port.ips[0].ip, port.ips[0].netmask))
        else:
            data.append(" no ip address")
        if port.access_group_in:
            data.append(" ip access-group %s in" % port.access_group_in)
        if port.access_group_out:
            data.append(" ip access-group %s out" % port.access_group_out)
        if "no ip redirects" in port.vendor_specific:
            data.append(" no ip redirects")
        for vrrp in port.vrrps:
            group = vrrp.group_id
            for i, ip_address in enumerate(vrrp.ip_addresses):
                data.append(" standby {group} ip {ip_address}{secondary}".format(group=group, ip_address=ip_address,
                                                                                 secondary=' secondary' if i > 0 else ''))
            if vrrp.timers_hello is not None and vrrp.timers_hold is not None:
                data.append(" standby {group} timers {hello_time} {hold_time}".format(group=group, hello_time=vrrp.timers_hello, hold_time=vrrp.timers_hold))
            if vrrp.priority is not None:
                data.append(" standby {group} priority {priority}".format(group=group, priority=vrrp.priority))
            if vrrp.preempt is not None:
                if vrrp.preempt_delay_minimum is not None:
                    data.append(" standby {group} preempt delay minimum {delay}".format(group=group, delay=vrrp.preempt_delay_minimum))
                else:
                    data.append(" standby {group} preempt".format(group=group))
            if vrrp.authentication is not None:
                data.append(" standby {group} authentication {authentication}".format(group=group, authentication=vrrp.authentication))
            for track, decrement in sorted(vrrp.track.items()):
                data.append(" standby {group} track {track} decrement {decrement}".format(group=group, track=track, decrement=decrement))
        for ip_address in port.ip_helpers:
            data.append(" ip helper-address {}".format(ip_address))
    return data


def vlan_name(vlan):
    return vlan.name or ("default" if vlan.number == 1 else None)


def to_vlan_ranges(vlans):
    if len(vlans) == 0:
        return "none"

    ranges = group_sequences(vlans, are_in_sequence=lambda a, b: a + 1 == b)

    return ",".join([to_range_string(r) for r in ranges])


def to_range_string(array_range):
    if len(array_range) < 3:
        return ",".join([str(n) for n in array_range])
    else:
        return "%s-%s" % (array_range[0], array_range[-1])

