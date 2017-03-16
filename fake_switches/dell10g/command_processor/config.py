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
from fake_switches.dell.command_processor.config import DellConfigCommandProcessor


class Dell10GConfigCommandProcessor(DellConfigCommandProcessor):
    def do_vlan(self, raw_number, *_):
        number = int(raw_number)
        if number < 1 or number > 4094:
            self.write_line("")
            self.write_line("")
            self.write_line("          Failure Information")
            self.write_line("---------------------------------------")
            self.write_line("   VLANs failed to be configured : 1")
            self.write_line("---------------------------------------")
            self.write_line("   VLAN             Error")
            self.write_line("---------------------------------------")
            self.write_line("VLAN {: <9} ERROR: VLAN ID is out of range".format(number))
        else:
            vlan = self.switch_configuration.get_vlan(number)
            if not vlan:
                vlan = self.switch_configuration.new("Vlan", number)
                self.switch_configuration.add_vlan(vlan)
            self.move_to(self.config_vlan_processor, vlan)

    def do_no_vlan(self, number, *args):
        vlan = self.switch_configuration.get_vlan(int(number))
        if vlan:
            self.switch_configuration.remove_vlan(vlan)
        else:
            self.write_line("")
            self.write_line("These VLANs do not exist:  {}.".format(number))

    def show_unknown_interface_error_message(self):
        self.write_line("An invalid interface has been used for this function")
