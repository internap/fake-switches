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
from fake_switches.arista.command_processor import vlan_display_name
from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.command_processing.shell_session import TerminalExitSignal


class DefaultCommandProcessor(BaseCommandProcessor):
    def __init__(self, enabled):
        super(DefaultCommandProcessor, self).__init__()
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
                vlans = list(filter(lambda e: e.number == int(args[1]), self.switch_configuration.vlans))
                if len(vlans) == 0:
                    self.write_line("% VLAN {} not found in current VLAN database".format(args[1]))
                    return
            else:
                vlans = self.switch_configuration.vlans

            self.write_line("VLAN  Name                             Status    Ports")
            self.write_line("----- -------------------------------- --------- -------------------------------")
            for vlan in sorted(vlans, key=lambda v: v.number):
                self.write_line("{: <5} {: <32} active".format(vlan.number, vlan_display_name(vlan)))
            self.write_line("")
