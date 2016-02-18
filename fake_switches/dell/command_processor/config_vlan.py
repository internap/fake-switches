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

from fake_switches.command_processing.base_command_processor import \
    BaseCommandProcessor


class DellConfigureVlanCommandProcessor(BaseCommandProcessor):
    def get_prompt(self):
        return "\n" + self.switch_configuration.name + "(config-vlan)#"

    def do_vlan(self, *args):
        vlan_id = int(args[0])
        self.print_vlan_significant_delays_warning()
        self.write_line("")
        self.switch_configuration.add_vlan(self.switch_configuration.new("Vlan", vlan_id))

    def do_no_vlan(self, *args):
        vlan_id = int(args[0])
        self.print_vlan_significant_delays_warning()
        self.write_line("")

        vlan = self.switch_configuration.get_vlan(vlan_id)
        if vlan is not None:
            self.write_line("If any of the VLANs being deleted are for access ports, the ports will be")
            self.write_line("unusable until it is assigned a VLAN that exists.")
            self.switch_configuration.remove_vlan(vlan)
        else:
            self.write_line("")
            self.write_line("These VLANs do not exist:  {}.".format(vlan_id))

    def print_vlan_significant_delays_warning(self):
        self.write_line("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        self.write_line("delays in applying the configuration.")

    def do_exit(self):
        self.is_done = True
