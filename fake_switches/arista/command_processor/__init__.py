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
from fake_switches.command_processing.base_command_processor import BaseCommandProcessor


class AristaBaseCommandProcessor(BaseCommandProcessor):
    def __init__(self, display_class):
        self.display = display_class(self)

    def read_vlan_number(self, input):
        try:
            number = int(input)
        except ValueError:
            self.display.invalid_command("Invalid input")
            return None

        if number < 0 or number > 4094:
            self.display.invalid_command("Invalid input")
        elif number == 0:
            self.display.invalid_command("Incomplete command")
        else:
            return number

        return None

def vlan_name(vlan):
    return vlan.name or ("default" if vlan.number == 1 else None)


def vlan_display_name(vlan):
    return vlan_name(vlan) or "VLAN{:04d}".format(vlan.number)
