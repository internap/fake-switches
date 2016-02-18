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

import logging

from fake_switches.cisco.command_processor.default import DefaultCommandProcessor
from fake_switches.cisco.command_processor.enabled import EnabledCommandProcessor
from fake_switches.cisco.command_processor.piping import PipingProcessor
from fake_switches.command_processing.shell_session import ShellSession
from fake_switches.terminal import LoggingTerminalController


class CiscoSwitchCore(object):
    def __init__(self, switch_configuration):
        self.switch_configuration = switch_configuration
        self.switch_configuration.add_vlan(self.switch_configuration.new("Vlan", 1))

        self.logger = None
        self.last_connection_id = 0

    def launch(self, protocol, terminal_controller):
        self.last_connection_id += 1

        self.logger = logging.getLogger("fake_switches.cisco.%s.%s.%s" % (self.switch_configuration.name, self.last_connection_id, protocol))
        if self.switch_configuration.auto_enabled:
            processor = EnabledCommandProcessor
        else:
            processor = DefaultCommandProcessor

        return CiscoShellSession(
            processor(
                self.switch_configuration,
                LoggingTerminalController(self.logger, terminal_controller),
                self.logger,
                PipingProcessor(self.logger)))

    def get_netconf_protocol(self):
        return None


class CiscoShellSession(ShellSession):
    def handle_unknown_command(self, line):
        self.command_processor.terminal_controller.write("No such command : %s\n" % line)





