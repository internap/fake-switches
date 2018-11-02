# Copyright 2018 Inap.
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
from fake_switches.arista.command_processor import AristaBaseCommandProcessor, NameIsIncomplete, InvalidVlanNumber, \
    VlanNumberIsZero
from fake_switches.switch_configuration import split_port_name


class ConfigCommandProcessor(AristaBaseCommandProcessor):
    interface_separator = ""

    def __init__(self, display_class, config_vlan, config_interface):
        super(ConfigCommandProcessor, self).__init__(display_class)
        self.config_vlan_processor = config_vlan
        self.config_interface_processor = config_interface

    def get_prompt(self):
        return self.switch_configuration.name + "(config)#"

    def do_vlan(self, raw_number, *_):
        try:
            number = self.read_vlan_number(raw_number)
        except VlanNumberIsZero:
            self.display.invalid_command(self, "Incomplete command")
            return
        except InvalidVlanNumber:
            self.display.invalid_command(self, "Invalid input")
            return

        vlan = self.switch_configuration.get_vlan(number)
        if not vlan:
            vlan = self.switch_configuration.new("Vlan", number)
            self.switch_configuration.add_vlan(vlan)
        self.move_to(self.config_vlan_processor, vlan)

    def do_no_vlan(self, *args):
        vlan = self.switch_configuration.get_vlan(int(args[0]))
        if vlan:
            self.switch_configuration.remove_vlan(vlan)

    def do_interface(self, *args):
        try:
            interface_name = self.read_interface_name(args)
        except NameIsIncomplete:
            self.display.invalid_command(self, "Incomplete command")
            return
        except InvalidVlanNumber:
            self.display.invalid_command(self, "Invalid input")
            return

        port = self.switch_configuration.get_port_by_partial_name(interface_name)

        if port:
            self.move_to(self.config_interface_processor, port)
        else:
            name, if_id = split_port_name(interface_name)
            if name == "Vlan":
                new_vlan_interface = self.switch_configuration.new("VlanPort", if_id, interface_name)
                self.switch_configuration.add_port(new_vlan_interface)
                self.move_to(self.config_interface_processor, new_vlan_interface)
            else:
                raise NotImplementedError

    def do_no_interface(self, *args):
        port = self.switch_configuration.get_port_by_partial_name(self.read_interface_name(args))
        if port is not None:
            self.switch_configuration.remove_port(port)
        self.sub_processor = None

    def do_exit(self):
        self.is_done = True
