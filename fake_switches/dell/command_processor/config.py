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
from fake_switches.cisco.command_processor.config import \
    ConfigCommandProcessor


class DellConfigCommandProcessor(ConfigCommandProcessor):
    interface_separator = ' '

    def get_prompt(self):
        return "\n" + self.switch_configuration.name + "(config)#"

    def do_vlan(self, *args):
        if "database".startswith(args[0]):
            self.move_to(self.config_vlan_processor)

    def do_interface(self, *args):
        if 'vlan'.startswith(args[0]):
            vlan_id = int(args[1])
            vlan = self.switch_configuration.get_vlan(vlan_id)
            if vlan is None:
                self.write_line("VLAN ID not found.")
                return
        self.write_line("")
        super(DellConfigCommandProcessor, self).do_interface(*args)

    def do_backdoor(self, *args):
        if 'remove'.startswith(args[0]) and 'port-channel'.startswith(args[1]):
            self.switch_configuration.remove_port(
                self.switch_configuration.get_port_by_partial_name(" ".join(args[1:3])))

    def do_exit(self):
        self.write_line("")
        self.is_done = True

    def make_vlan_port(self, vlan_id, interface_name):
        return self.switch_configuration.new("VlanPort", vlan_id, interface_name)

    def make_aggregated_port(self, interface_name):
        return self.switch_configuration.new("AggregatedPort", interface_name)
