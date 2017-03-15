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

from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.switch_configuration import split_port_name, VlanPort


class ConfigVlanCommandProcessor(BaseCommandProcessor):
    def init(self, switch_configuration, terminal_controller, logger, piping_processor, *args):
        super(ConfigVlanCommandProcessor, self).init(switch_configuration, terminal_controller, logger, piping_processor)
        self.vlan = args[0]

    def get_prompt(self):
        return "SSH@%s(config-vlan-%s)#" % (self.switch_configuration.name, self.vlan.number)

    def do_untagged(self, *args):
        port = self.switch_configuration.get_port_by_partial_name(" ".join(args))
        if port is not None:
            if port.trunk_vlans is None:
                port.access_vlan = self.vlan.number
            else:
                port.trunk_native_vlan = self.vlan.number
        else:
            self.write_line("Invalid input -> %s" % " ".join(args[1:]))
            self.write_line("Type ? for a list")

    def do_no_untagged(self, *args):
        port = self.switch_configuration.get_port_by_partial_name(" ".join(args))

        if port is not None:
            if port.access_vlan != self.vlan.number and port.trunk_native_vlan != self.vlan.number:
                self.write_line("Error: ports ethe {} are not untagged members of vlan {}".format(args[1], self.vlan.number))
                return

            if port.trunk_vlans is None:
                port.access_vlan = None
            else:
                port.trunk_native_vlan = None
        else:
            self.write_line("Invalid input -> %s" % " ".join(args[1:]))
            self.write_line("Type ? for a list")

    def do_tagged(self, *args):
        port = self.switch_configuration.get_port_by_partial_name(" ".join(args))
        if port is not None:
            if port.trunk_vlans is None:
                port.trunk_vlans = []
                port.trunk_native_vlan = port.access_vlan or 1
                port.access_vlan = None
            if self.vlan.number not in port.trunk_vlans:
                port.trunk_vlans.append(self.vlan.number)
        else:
            self.write_line("Invalid input -> %s" % " ".join(args[1:]))
            self.write_line("Type ? for a list")

    def do_no_tagged(self, *args):
        port = self.switch_configuration.get_port_by_partial_name(" ".join(args))
        if port is not None:
            if port.trunk_vlans is None or self.vlan.number not in port.trunk_vlans:
                self.write_line("Error: ports ethe {} are not tagged members of vlan {}".format(args[1], self.vlan.number))
                return

            port.trunk_vlans.remove(self.vlan.number)
            if len(port.trunk_vlans) == 0:
                port.trunk_vlans = None
                if port.trunk_native_vlan and port.trunk_native_vlan != 1:
                    port.access_vlan = port.trunk_native_vlan
                port.trunk_native_vlan = None
        else:
            self.write_line("Invalid input -> %s" % " ".join(args[1:]))
            self.write_line("Type ? for a list")

    def do_router_interface(self, *args):
        if len(args) != 2 or args[0] != "ve":
            self.write_line("Invalid input -> {}".format(" ".join(args)))
            self.write_line("Type ? for a list")
        else:
            actual_ve = next(
                (p for p in self.switch_configuration.ports if isinstance(p, VlanPort) and p.vlan_id == self.vlan.number),
                False)
            if not actual_ve:
                name = "ve {}".format(args[1])
                self.switch_configuration.add_port(self.switch_configuration.new("VlanPort", self.vlan.number,
                                                                                 name))
            else:
                self.write_line("Error: VLAN: %s  already has router-interface %s" % (
                    self.vlan.number, split_port_name(actual_ve.name)[1]))

    def do_no_router_interface(self, *_):
        self.switch_configuration.remove_port(next(
            p for p in self.switch_configuration.ports if isinstance(p, VlanPort) and p.vlan_id == self.vlan.number))

    def do_exit(self):
        self.is_done = True
