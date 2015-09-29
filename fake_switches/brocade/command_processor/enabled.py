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

import re
from fake_switches import group_sequences
from fake_switches.brocade.command_processor.config import ConfigCommandProcessor
from fake_switches.command_processing.switch_tftp_parser import SwitchTftpParser
from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.switch_configuration import split_port_name, VlanPort


class EnabledCommandProcessor(BaseCommandProcessor):
    def get_prompt(self):
        return "SSH@%s#" % self.switch_configuration.name

    def do_configure(self, *_):
        self.move_to(ConfigCommandProcessor)

    def do_show(self, *args):
        if "running-config".startswith(args[0]):
            if "vlan".startswith(args[1]):
                self.show_run_vlan()
            if "interface".startswith(args[1]):
                self.show_run_int(args)
        elif "interfaces".startswith(args[0]):
            self.show_int(args)
        elif "vlan".startswith(args[0]):
            if "brief".startswith(args[1]):
                self.show_vlan_brief()
            elif "ethernet".startswith(args[1]):
                self.show_vlan_int(args)
            else:
                self.write_line("Invalid input -> %s" % args[1])
                self.write_line("Type ? for a list")
        elif "route".startswith(args[1]):
            if "static".startswith(args[2]):
                routes = self.switch_configuration.static_routes
                if routes:
                    self.write_line("        Destination        Gateway        Port          Cost          Type Uptime src-vrf")
                for n, route in enumerate(routes):
                    self.write_line("{index:<8}{destination:<18} {next_hop:}".format(index=n+1, destination=route.dest, next_hop=route.next_hop))
            self.write_line("")

    def do_ncopy(self, protocol, url, filename, target):
        try:
            SwitchTftpParser(self.switch_configuration).parse(url, filename, ConfigCommandProcessor)
            self.write_line("done")
        except Exception as e:
            self.logger.warning("tftp parsing went wrong : %s" % str(e))
            self.write_line("%s: Download to %s failed - Session timed out" % (protocol.upper(), target))

    def do_skip_page_display(self, *args):
        pass

    def do_write(self, *args):
        pass

    def do_exit(self):
        self.is_done = True

    def show_run_vlan(self):
        self.write_line("spanning-tree")
        self.write_line("!")
        self.write_line("!")
        for vlan in sorted(self.switch_configuration.vlans, key=lambda v: v.number):
            if vlan_name(vlan):
                self.write_line("vlan %d name %s" % (vlan.number, vlan_name(vlan)))
            else:
                self.write_line("vlan %d" % vlan.number)

            untagged_ports = []
            for port in self.switch_configuration.ports:
                if not isinstance(port, VlanPort):
                    if vlan.number == 1 and port.access_vlan is None and port.trunk_native_vlan is None:
                        untagged_ports.append(port)
                    elif port.access_vlan == vlan.number or port.trunk_native_vlan == vlan.number:
                        untagged_ports.append(port)

            if len(untagged_ports) > 0:
                if vlan.number == 1:
                    self.write_line(" no untagged %s" % to_port_ranges(untagged_ports))
                else:
                    self.write_line(" untagged %s" % to_port_ranges(untagged_ports))

            tagged_ports = [p for p in self.switch_configuration.ports if
                            p.trunk_vlans and vlan.number in p.trunk_vlans]
            if tagged_ports:
                self.write_line(" tagged %s" % to_port_ranges(tagged_ports))

            vif = next((p for p in self.switch_configuration.ports if isinstance(p, VlanPort) and p.vlan_id == vlan.number), False)
            if vif:
                self.write_line(" router-interface %s" % vif.name)

            self.write_line("!")
        self.write_line("!")
        self.write_line("")

    def show_run_int(self, args):
        port_list = []
        if len(args) < 3:
            port_list = sorted(self.switch_configuration.ports, key=lambda e: ("a" if not isinstance(e, VlanPort) else "b") + e.name)
        else:
            if "ve".startswith(args[2]):
                port = self.switch_configuration.get_port_by_partial_name(" ".join(args[2:]))
                if not port:
                    self.write_line("Error - %s was not configured" % " ".join(args[2:]))
                else:
                    port_list = [port]
            else:
                port_type, port_number = split_port_name("".join(args[2:]))
                port = self.switch_configuration.get_port_by_partial_name(port_number)
                if not port:
                    self.write_line("")
                else:
                    port_list = [port]
        if len(port_list) > 0:
            for port in port_list:
                attributes = get_port_attributes(port)
                if len(attributes) > 0 or isinstance(port, VlanPort):
                    self.write_line("interface %s" % port.name)
                    for a in attributes:
                        self.write_line(" " + a)
                    self.write_line("!")

            self.write_line("")

    def show_int(self, args):
        if len(args) > 1:
            ports = [self.switch_configuration.get_port_by_partial_name(" ".join(args[1:]))]
        else:
            ports = self.switch_configuration.ports

        for port in ports:
            if isinstance(port, VlanPort):
                _, port_id = split_port_name(port.name)
                self.write_line("Ve%s is down, line protocol is down" % port_id)
                self.write_line("  Hardware is Virtual Ethernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
                if port.description:
                    self.write_line("  Port name is %s" % port.description)
                else:
                    self.write_line("  No port name")

                self.write_line("  Vlan id: %s" % port.vlan_id)
                self.write_line("  Internet address is %s, IP MTU 1500 bytes, encapsulation ethernet" % (
                    port.ips[0] if port.ips else "0.0.0.0/0"))
            else:
                _, port_id = split_port_name(port.name)
                self.write_line("GigabitEthernet%s is %s, line protocol is down" % (
                    port_id, "down" if port.shutdown is False else "disabled"))
                self.write_line("  Hardware is GigabitEthernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
                self.write_line("  " + ", ".join([vlan_membership(port), port_mode(port), port_state(port)]))
                if port.description:
                    self.write_line("  Port name is %s" % port.description)
                else:
                    self.write_line("  No port name")

    def show_vlan_brief(self):
        self.write_line("")
        self.write_line("VLAN     Name       Encap ESI                              Ve    Pri Ports")
        self.write_line("----     ----       ----- ---                              ----- --- -----")
        for vlan in sorted(self.switch_configuration.vlans, key=lambda v: v.number):
            ports = [port for port in self.switch_configuration.ports
                     if port.access_vlan == vlan.number or (port.access_vlan is None and vlan.number == 1)]
            self.write_line("%-4s     %-10s                                        -     -%s" % (
                vlan.number,
                vlan_name(vlan)[:10] if vlan_name(vlan) else "[None]",
                ("   Untagged Ports : %s" % to_port_ranges(ports)) if ports else ""
            ))

    def show_vlan_int(self, args):
        port = self.switch_configuration.get_port_by_partial_name(" ".join(args[1:]))
        if port:
            untagged_vlan = port.access_vlan or (port.trunk_native_vlan if port.trunk_native_vlan != 1 else None)
            if untagged_vlan is None and port.trunk_vlans is None:
                self.write_line("VLAN: 1  Untagged")
            else:
                for vlan in sorted(port.trunk_vlans or []):
                    if untagged_vlan is not None and untagged_vlan < vlan:
                        self.write_line("VLAN: %s  Untagged" % untagged_vlan)
                        untagged_vlan = None
                    self.write_line("VLAN: %s  Tagged" % vlan)

                if untagged_vlan is not None:
                    self.write_line("VLAN: %s  Untagged" % untagged_vlan)
        else:
            self.write_line("Invalid input -> %s" % args[2])
            self.write_line("Type ? for a list")


def port_index(port):
    return int(re.match(".*(\d)$", port.name).groups()[0])


def to_port_ranges(ports):
    port_range_list = group_sequences(ports, are_in_sequence=lambda a, b: port_index(a) + 1 == port_index(b))

    out = []
    for port_range in port_range_list:
        if len(port_range) == 1:
            out.append("ethe %s" % split_port_name(port_range[0].name)[1])
        else:
            out.append("ethe %s to %s" %
                       (split_port_name(port_range[0].name)[1], split_port_name(port_range[-1].name)[1]))

    out_str = " ".join(out)
    return out_str


def vlan_name(vlan):
    return vlan.name or ("DEFAULT-VLAN" if vlan.number == 1 else None)


def get_port_attributes(port):
    attributes = []
    if port.description:
        attributes.append("port-name %s" % port.description)
    if port.shutdown is False:
        attributes.append("enable")
    if port.vrf is not None:
        attributes.append("vrf forwarding {}".format(port.vrf.name))
    if isinstance(port, VlanPort):
        for ip in sorted(port.ips, key=lambda e: e.ip):
            attributes.append("ip address %s" % ip)
        for ip in sorted(port.secondary_ips, key=lambda e: e.ip):
            attributes.append("ip address %s secondary" % ip)
        if port.access_group_in:
            attributes.append("ip access-group %s in" % port.access_group_in)
        if port.access_group_out:
            attributes.append("ip access-group %s out" % port.access_group_out)
        if port.vrrp_common_authentication:
            attributes.append("ip vrrp-extended auth-type simple-text-auth ********")
        for vrrp in port.vrrps:
            attributes.append("ip vrrp-extended vrid %s" % vrrp.group_id)
            if vrrp.priority and len(vrrp.track) > 0:
                attributes.append(" backup priority %s track-priority %s" % (vrrp.priority, vrrp.track.values()[0]))
            if vrrp.ip_addresses:
                for ip_address in vrrp.ip_addresses:
                    attributes.append(" ip-address %s" % ip_address)
            if vrrp.advertising:
                attributes.append(" advertise backup")
            if vrrp.timers_hold:
                attributes.append(" dead-interval %s" % vrrp.timers_hold)
            if vrrp.timers_hello:
                attributes.append(" hello-interval %s" % vrrp.timers_hello)
            if len(vrrp.track) > 0 and vrrp.track.keys()[0] is not None:
                attributes.append(" track-port %s" % vrrp.track.keys()[0])
            if vrrp.activated:
                attributes.append(" activate")
            else:
                attributes.append(" exit")
        for ip_address in port.ip_helpers:
            attributes.append("ip helper-address %s" % ip_address)

    return attributes


def vlan_membership(port):
    if port.access_vlan:
        return "Member of VLAN %s (untagged)" % port.access_vlan
    elif port.trunk_vlans and port.trunk_native_vlan:
        return "Member of VLAN %s (untagged), %d L2 VLANS (tagged)" % (port.trunk_native_vlan, len(port.trunk_vlans))
    elif port.trunk_vlans and not port.trunk_native_vlan:
        return "Member of %d L2 VLAN(S) (tagged)" % len(port.trunk_vlans)
    else:
        return "Member of VLAN 1 (untagged)"


def port_mode(port):
    if port.trunk_vlans and port.trunk_native_vlan == 1:
        return "port is in dual mode (default vlan)"
    elif port.trunk_vlans and port.trunk_native_vlan:
        return "port is in dual mode"
    elif port.access_vlan or port.trunk_vlans is None:
        return "port is in untagged mode"
    else:
        return "port is in tagged mode"


def port_state(_):
    return "port state is Disabled"
