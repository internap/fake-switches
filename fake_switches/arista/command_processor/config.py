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
from fake_switches.arista.command_processor import AristaBaseCommandProcessor


class ConfigCommandProcessor(AristaBaseCommandProcessor):
    interface_separator = ""

    def __init__(self, display_class, config_vlan):
        super(ConfigCommandProcessor, self).__init__(display_class)
        self.config_vlan_processor = config_vlan

    def get_prompt(self):
        return self.switch_configuration.name + "(config)#"

    def do_vlan(self, raw_number, *_):
        number = self.read_vlan_number(raw_number)

        if number is not None:
            vlan = self.switch_configuration.get_vlan(number)
            if not vlan:
                vlan = self.switch_configuration.new("Vlan", number)
                self.switch_configuration.add_vlan(vlan)
            self.move_to(self.config_vlan_processor, vlan)

    def do_no_vlan(self, *args):
        vlan = self.switch_configuration.get_vlan(int(args[0]))
        if vlan:
            self.switch_configuration.remove_vlan(vlan)

    def do_exit(self):
        self.is_done = True
