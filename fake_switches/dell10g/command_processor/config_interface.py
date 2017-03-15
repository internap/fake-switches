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

from fake_switches.dell.command_processor.config_interface import DellConfigInterfaceCommandProcessor, parse_vlan_list
from fake_switches.switch_configuration import AggregatedPort


class Dell10GConfigInterfaceCommandProcessor(DellConfigInterfaceCommandProcessor):
    def init(self, switch_configuration, terminal_controller, logger,
                 piping_processor, *args):
        super(Dell10GConfigInterfaceCommandProcessor, self).init(switch_configuration, terminal_controller, logger, piping_processor,
            args[0])
        self.description_strip_chars = "\"'"

    def get_prompt(self):
        short_name = self.port.name.split(' ')[1]
        return "{}(config-if-{}{})#".format(
            self.switch_configuration.name,
            "Po" if isinstance(self.port, AggregatedPort) else "Te",
            short_name)

    def configure_lldp_port(self, args, target_value):
        if "transmit".startswith(args[0]):
            self.port.lldp_transmit = target_value
        elif "receive".startswith(args[0]):
            self.port.lldp_receive = target_value
        elif "med".startswith(args[0]):
            if len(args) == 1:
                self.port.lldp_med = target_value
            elif "transmit-tlv".startswith(args[1]):
                if "capabilities".startswith(args[2]):
                    self.port.lldp_med_transmit_capabilities = target_value
                elif "network-policy".startswith(args[2]):
                    self.port.lldp_med_transmit_network_policy = target_value


    def do_switchport(self, *args):
        if "access".startswith(args[0]) and "vlan".startswith(args[1]):
            self.set_access_vlan(int(args[2]))
        elif "mode".startswith(args[0]):
            self.set_switchport_mode(args[1])
        elif ("general".startswith(args[0]) or "trunk".startswith(args[0])) and "allowed".startswith(args[1]):
            if "vlan".startswith(args[2]) and args[0] == "general":
                if len(args) > 5:
                    self.write_line("                                                                 ^")
                    self.write_line("% Invalid input detected at '^' marker.")
                else:
                    operation = args[3]
                    vlan_range = args[4]
                    self.update_trunk_vlans(operation, vlan_range)
                    return
            elif "vlan".startswith(args[2]) and args[0] == "trunk":
                if len(args) > 5:
                    self.write_line("                                                                 ^")
                    self.write_line("% Invalid input detected at '^' marker.")
                else:
                    if args[0:4] == ("trunk", "allowed", "vlan", "add"):
                        if self.port.trunk_vlans is not None:
                            self.port.trunk_vlans = sorted(list(set(self.port.trunk_vlans + parse_vlan_list(args[4]))))
                    elif args[0:4] == ("trunk", "allowed", "vlan", "remove"):
                        if self.port.trunk_vlans is None:
                            self.port.trunk_vlans = list(range(1, 4097))
                        for v in parse_vlan_list(args[4]):
                            if v in self.port.trunk_vlans:
                                self.port.trunk_vlans.remove(v)
                        if len(self.port.trunk_vlans) == 0:
                            self.port.trunk_vlans = None
                    elif args[0:4] == ("trunk", "allowed", "vlan", "none"):
                        self.port.trunk_vlans = []
                    elif args[0:4] == ("trunk", "allowed", "vlan", "all"):
                        self.port.trunk_vlans = None
                    elif args[0:3] == ("trunk", "allowed", "vlan"):
                        self.port.trunk_vlans = parse_vlan_list(args[3])
                    elif args[0:3] == ("trunk", "native", "vlan"):
                        self.port.trunk_native_vlan = int(args[3])
        elif "general".startswith(args[0]) and "pvid".startswith(args[1]):
            self.set_trunk_native_vlan(int(args[2]))

        self.write_line("")

    def do_no_switchport(self, *args):
        if "mode".startswith(args[0]):
            self.set_switchport_mode("access")
        elif "access".startswith(args[0]):
            if "vlan".startswith(args[1]):
                self.print_vlan_warning()
                self.port.access_vlan = None
        elif args[0] in ("trunk", "general") and args[1:3] == ("allowed", "vlan"):
            self.port.trunk_vlans = None
        elif "general".startswith(args[0]):
            if "pvid".startswith(args[1]):
                self.port.trunk_native_vlan = None

        self.write_line("")

    def do_mtu(self, *args):
        self.write_line("                                                     ^")
        self.write_line("% Invalid input detected at '^' marker.")
        self.write_line("")

    def do_no_mtu(self, *args):
        self.write_line("                                                     ^")
        self.write_line("% Invalid input detected at '^' marker.")
        self.write_line("")

    def set_switchport_mode(self, mode):
        if mode not in ("access", "trunk", "general"):
            self.write_line("                                         ^")
            self.write_line("% Invalid input detected at '^' marker.")
        else:
            self.port.mode = mode

    def set_trunk_native_vlan(self, native_vlan):
        vlan = self.switch_configuration.get_vlan(native_vlan)
        if vlan is None:
            self.write_line("Could not configure pvid.")
        else:
            self.port.trunk_native_vlan = vlan.number

    def print_vlan_warning(self):
        pass
