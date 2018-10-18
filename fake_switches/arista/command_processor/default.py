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
from fake_switches.arista.command_processor import vlan_display_name, AristaBaseCommandProcessor
from fake_switches.command_processing.shell_session import TerminalExitSignal


class DefaultCommandProcessor(AristaBaseCommandProcessor):
    def __init__(self, display_class, enabled):
        super(DefaultCommandProcessor, self).__init__(display_class)
        self.enabled_processor = enabled

    def get_prompt(self):
        return self.switch_configuration.name + ">"

    def do_exit(self):
        raise TerminalExitSignal()

    def do_enable(self):
        self.move_to(self.enabled_processor)

    def do_show(self, *args):
        if "vlan".startswith(args[0]):
            if len(args) == 2:
                number = self.read_vlan_number(args[1])
                if number is None:
                    return

                vlans = list(filter(lambda e: e.number == number, self.switch_configuration.vlans))
                if len(vlans) == 0:
                    self.display.invalid_result("VLAN {} not found in current VLAN database".format(args[1]),
                                                json_data=_to_vlans_json([]))
                    return
            else:
                vlans = self.switch_configuration.vlans

            self.display.show_vlans(_to_vlans_json(vlans))


def _to_vlans_json(vlans):
    return {
        "vlans": {
            str(vlan.number): {
                "dynamic": False,
                "interfaces": {},
                "name": vlan_display_name(vlan),
                "status": "active"
            } for vlan in vlans
        }
    }
