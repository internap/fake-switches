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

from netaddr import IPNetwork
from netaddr.ip import IPAddress

from fake_switches.switch_configuration import VlanPort
from fake_switches.command_processing.base_command_processor import BaseCommandProcessor


class ConfigInterfaceCommandProcessor(BaseCommandProcessor):

    def __init__(self, switch_configuration, terminal_controller, logger, piping_processor, port):
        BaseCommandProcessor.__init__(self, switch_configuration, terminal_controller, logger, piping_processor)
        self.description_strip_chars = "\""
        self.port = port

    def get_prompt(self):
        return self.switch_configuration.name + "(config-if)#"

    def do_switchport(self, *args):
        if args[0:1] == ("mode",):
            self.port.mode = args[1]
        elif args[0:2] == ("access", "vlan"):
            self.port.access_vlan = int(args[2])
        elif args[0:2] == ("trunk", "encapsulation"):
            self.port.trunk_encapsulation_mode = args[2]
        elif args[0:4] == ("trunk", "allowed", "vlan", "add"):
            if self.port.trunk_vlans is not None: #for cisco, no list = all vlans
                self.port.trunk_vlans += parse_vlan_list(args[4])
        elif args[0:4] == ("trunk", "allowed", "vlan", "remove"):
            if self.port.trunk_vlans is None:
                self.port.trunk_vlans = range(1, 4097)
            for v in parse_vlan_list(args[4]):
                if v in self.port.trunk_vlans:
                    self.port.trunk_vlans.remove(v)
        elif args[0:4] == ("trunk", "allowed", "vlan", "none"):
            self.port.trunk_vlans = []
        elif args[0:4] == ("trunk", "allowed", "vlan", "all"):
            self.port.trunk_vlans = None
        elif args[0:3] == ("trunk", "allowed", "vlan"):
            self.port.trunk_vlans = parse_vlan_list(args[3])
        elif args[0:3] == ("trunk", "native", "vlan"):
            self.port.trunk_native_vlan = int(args[3])

    def do_no_switchport(self, *args):
        if args[0:2] == ("access", "vlan"):
            self.port.access_vlan = None
        elif args[0:1] == ("mode",):
            self.port.mode = None
        elif args[0:3] == ("trunk", "allowed", "vlan"):
            self.port.trunk_vlans = None
        elif args[0:3] == ("trunk", "native", "vlan"):
            self.port.trunk_native_vlan = None

    def do_channel_group(self, *args):
        port_channel_id = args[0]
        port_channel_name = "Port-channel%s" % port_channel_id

        if not self.port_channel_exists(port_channel_name):
            self.write_line("Creating a port-channel interface Port-channel %s" % port_channel_id)
            self.create_port_channel(port_channel_name)
        self.port.aggregation_membership = port_channel_name

    def do_no_channel_group(self, *_):
        self.port.aggregation_membership = None

    def do_description(self, *args):
        self.port.description = " ".join(args).strip(self.description_strip_chars)

    def do_no_description(self, *_):
        self.port.description = None

    def do_shutdown(self, *_):
        self.port.shutdown = True

    def do_no_shutdown(self, *_):
        self.port.shutdown = False

    def do_ip(self, *args):

        if "address".startswith(args[0]):
            new_ip = IPNetwork("%s/%s" % (args[1], args[2]))
            ip_owner, existing_ip = self.switch_configuration.get_port_and_ip_by_ip(new_ip.ip)
            if not ip_owner or ip_owner == self.port:
                if len(args) == 4 and "secondary".startswith(args[3]):
                    self.port.add_ip(new_ip)
                else:
                    if len(self.port.ips) == 0:
                        self.port.add_ip(new_ip)
                    else:
                        if ip_owner == self.port:
                            self.port.remove_ip(new_ip)
                        self.port.ips[0] = new_ip
            else:
                if ip_owner.ips.index(existing_ip) == 0:
                    self.write_line("%% %s overlaps with secondary address on %s" % (existing_ip.network, ip_owner.name))
                else:
                    self.write_line("%% %s is assigned as a secondary address on %s" % (existing_ip.network, ip_owner.name))

        if "access-group".startswith(args[0]):
            if "in".startswith(args[2]):
                self.port.access_group_in = args[1]
            if "out".startswith(args[2]):
                self.port.access_group_out = args[1]

        if "vrf".startswith(args[0]):
            if "forwarding".startswith(args[1]):
                if isinstance(self.port, VlanPort):
                    for ip in self.port.ips[:]:
                        self.port.remove_ip(ip)
                vrf = self.switch_configuration.get_vrf(args[2])
                if vrf:
                    self.port.vrf = vrf
                else:
                    self.write_line("%% VRF %s not configured." % args[2])
        if "redirects".startswith(args[0]):
            del self.port.vendor_specific["no ip redirects"]

        if "helper-address".startswith(args[0]):
            if len(args) == 1:
                self.write_line("% Incomplete command.")
                self.write_line("")
            elif len(args) > 2:
                self.write_line(" ^")
                self.write_line("% Invalid input detected at '^' marker.")
                self.write_line("")
            else:
                ip_address = IPAddress(args[1])
                if ip_address not in self.port.ip_helpers:
                    self.port.ip_helpers.append(ip_address)

    def do_no_ip(self, *args):
        if "address".startswith(args[0]):
            if len(args) == 1:
                self.port.ips = []
            else:
                ip = IPNetwork("%s/%s" % (args[1], args[2]))
                is_secondary = "secondary".startswith(args[3]) if len(args) == 4 else False
                if is_secondary:
                    self.port.remove_ip(ip)
                else:
                    if len(self.port.ips) == 1:
                        self.port.remove_ip(ip)
                    else:
                        self.write_line("Must delete secondary before deleting primary")
        if "access-group".startswith(args[0]):
            direction = args[-1]
            if "in".startswith(direction):
                self.port.access_group_in = None
            elif "out".startswith(direction):
                self.port.access_group_out = None
        if "vrf".startswith(args[0]):
            if "forwarding".startswith(args[1]):
                self.port.vrf = None
        if "redirects".startswith(args[0]):
            self.port.vendor_specific["no ip redirects"] = True

        if "helper-address".startswith(args[0]):
            if len(args) > 2:
                self.write_line(" ^")
                self.write_line("% Invalid input detected at '^' marker.")
                self.write_line("")
            else:
                if len(args) == 1:
                    self.port.ip_helpers = []
                else:
                    ip_address = IPAddress(args[1])
                    if ip_address in self.port.ip_helpers:
                        self.port.ip_helpers.remove(ip_address)

    def do_standby(self, group, command, *args):
        vrrp = self.port.get_vrrp_group(group)
        if vrrp is None:
            vrrp = self.switch_configuration.new("VRRP", group)
            self.port.vrrps.append(vrrp)

        if "ip".startswith(command):
            vrrp.ip_addresses = vrrp.ip_addresses + [args[0], ] if vrrp.ip_addresses is not None and len(args) > 1 else [args[0]]

        if "timers".startswith(command):
            vrrp.timers_hello = args[0]
            vrrp.timers_hold = args[1]

        if "priority".startswith(command):
            vrrp.priority = args[0]

        if "authentication".startswith(command):
            vrrp.authentication = args[0]

        if "track".startswith(command) and "decrement".startswith(args[1]):
            vrrp.track.update({args[0]: args[2]})

        if "preempt".startswith(command):
            vrrp.preempt = True
            if len(args) > 0 and " ".join(args[0:2]) == "delay minimum":
                vrrp.preempt_delay_minimum = args[2]

    def do_no_standby(self, group, *cmd_args):
        vrrp = self.port.get_vrrp_group(group)

        if vrrp is None:
            return

        if len(cmd_args) == 0:
            self.port.vrrps.remove(vrrp)

        else:
            command = cmd_args[0]
            args = cmd_args[1:]

            if "ip".startswith(command):
                if args is None:
                    vrrp.ip_addresses = []
                else:
                    vrrp.ip_addresses.remove(args[0])

            if "authentication".startswith(command):
                vrrp.authentication = None

            if "priority".startswith(command):
                vrrp.priority = None

            if "timers".startswith(command):
                vrrp.timers_hello = None
                vrrp.timers_hold = None

            if "track".startswith(command) and args[0] in vrrp.track:
                del vrrp.track[args[0]]

            if "preempt".startswith(command):
                if "delay".startswith(args[0]):
                    vrrp.preempt_delay_minimum = None
                else:
                    vrrp.preempt_delay_minimum = None
                    vrrp.preempt = False

    def do_exit(self):
        self.is_done = True

    def port_channel_exists(self, name):
        return self.switch_configuration.get_port_by_partial_name(name) is not None

    def create_port_channel(self, name):
        port = self.switch_configuration.new("AggregatedPort", name)
        self.port.switch_configuration.add_port(port)


def parse_vlan_list(param):
    ranges = param.split(",")
    vlans = []
    for r in ranges:
        if "-" in r:
            start, stop = r.split("-")
            vlans += [v for v in range(int(start), int(stop) + 1)]
        else:
            vlans.append(int(r))

    return vlans

