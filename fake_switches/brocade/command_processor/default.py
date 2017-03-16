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


class DefaultCommandProcessor(BaseCommandProcessor):
    def __init__(self, enabled):
        super(DefaultCommandProcessor, self).__init__()
        self.enabled_processor = enabled

    def get_prompt(self):
        return "SSH@%s>" % self.switch_configuration.name

    def delegate_to_sub_processor(self, line):
        processed = self.sub_processor.process_command(line)
        if self.sub_processor.is_done:
            self.is_done = True
        return processed

    def do_enable(self):
        self.write("Password:")
        self.replace_input = ''
        self.continue_to(self.continue_enabling)

    def continue_enabling(self, line):
        self.replace_input = False
        if line == "" or line in self.switch_configuration.privileged_passwords:
            self.move_to(self.enabled_processor)
        else:
            self.write_line("Error - Incorrect username or password.")

