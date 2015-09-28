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

from fake_switches.brocade.command_processor.config_interface import ConfigInterfaceCommandProcessor
from fake_switches.brocade.command_processor.config_virtual_interface import \
    ConfigVirtualInterfaceCommandProcessor
from fake_switches.brocade.command_processor.config_vlan import ConfigVlanCommandProcessor
from fake_switches.brocade.command_processor.config_vrf import ConfigVrfCommandProcessor
from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.switch_configuration import VlanPort


class ConfigCommandProcessor(BaseCommandProcessor):
    def get_prompt(self):
        return "SSH@%s(config)#" % self.switch_configuration.name

    def do_vlan(self, raw_number, *args):
        number = int(raw_number)
        if number < 0:
            self.write_line("Invalid input -> -1")
            self.write_line("Type ? for a list")
        elif number == 0:
            self.write_line("Error: vlan ID value 0 not allowed.")
        elif number > 4090:
            self.write_line("Error: vlan id %s is outside of allowed max of 4090" % raw_number)
        else:
            vlan = self.switch_configuration.get_vlan(number)
            if not vlan:
                vlan = self.switch_configuration.new("Vlan", number)
                self.switch_configuration.add_vlan(vlan)
            if len(args) > 0:
                if "name".startswith(args[0]):
                    vlan.name = args[1]
            self.move_to(ConfigVlanCommandProcessor, vlan)

    def do_no_vlan(self, *args):
        vlan = self.switch_configuration.get_vlan(int(args[0]))
        if vlan:
            self.switch_configuration.remove_vlan(vlan)
            bound_ve = next(
                (p for p in self.switch_configuration.ports if isinstance(p, VlanPort) and p.vlan_id == vlan.number),
                None)
            if bound_ve:
                self.switch_configuration.remove_port(bound_ve)

            for port in self.switch_configuration.ports:
                if port.trunk_vlans is None:
                    if port.access_vlan == vlan.number:
                        port.access_vlan = None
                else:
                    if port.trunk_native_vlan == vlan.number:
                        port.trunk_native_vlan = None
                    if vlan.number in port.trunk_vlans:
                        port.trunk_vlans.remove(vlan.number)
                        if len(port.trunk_vlans) == 0:
                            port.trunk_vlans = None

    def do_interface(self, *args):
        port = self.switch_configuration.get_port_by_partial_name("".join(args))
        if port:
            if isinstance(port, VlanPort):
                self.move_to(ConfigVirtualInterfaceCommandProcessor, port)
            else:
                self.move_to(ConfigInterfaceCommandProcessor, port)
        else:
            if "ve".startswith(args[0]):
                self.write_line("Error - invalid virtual ethernet interface number.")
            else:
                self.write_line("Invalid input -> %s" % " ".join(args[1:]))
                self.write_line("Type ? for a list")

    def do_no_interface(self, *args):
        port = self.switch_configuration.get_port_by_partial_name("".join(args))
        if port and isinstance(port, VlanPort):
            self.switch_configuration.remove_port(port)
            self.switch_configuration.add_port(self.switch_configuration.new("VlanPort", port.vlan_id, port.name))

    def do_no_ip(self, cmd, *args):
        if "vrf".startswith(cmd):
            self.switch_configuration.remove_vrf(args[0])
        elif "route".startswith(cmd):
            self.switch_configuration.remove_static_route(args[0], args[1])

    def do_ip(self, cmd, *args):
        if "vrf".startswith(cmd):
            vrf = self.switch_configuration.new("VRF", args[0])
            self.switch_configuration.add_vrf(vrf)
            self.move_to(ConfigVrfCommandProcessor, vrf)
        elif "route".startswith(cmd):
            static_route = self.switch_configuration.new("Route", *args)
            self.switch_configuration.add_static_route(static_route)

    def do_exit(self):
        self.is_done = True
