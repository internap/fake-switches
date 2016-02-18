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


class ConfigVlanCommandProcessor(BaseCommandProcessor):

    def __init__(self, switch_configuration, terminal_controller, logger, piping_processor, vlan):
        BaseCommandProcessor.__init__(self, switch_configuration, terminal_controller, logger, piping_processor)
        self.vlan = vlan

    def get_prompt(self):
        return self.switch_configuration.name + "(config-vlan)#"

    def do_name(self, *args):
        self.vlan.name = (args[0][:32])

    def do_exit(self):
        self.is_done = True
