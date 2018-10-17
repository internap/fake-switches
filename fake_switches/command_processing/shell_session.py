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


class ShellSession(object):
    def __init__(self, command_processor):
        self.command_processor = command_processor

        self.command_processor.show_prompt()

    def receive(self, line):
        self.command_processor.logger.debug("received: %s" % line)
        try:
            processed = self.command_processor.process_command(line)
        except TerminalExitSignal:
            return False

        if not processed:
            self.command_processor.logger.info("Command not supported : %s" % line)

            self.handle_unknown_command(line)

            self.command_processor.show_prompt()

        return not self.command_processor.is_done

    def handle_unknown_command(self, line):
        pass


class TerminalExitSignal(Exception):
    pass
