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

import logging

from fake_switches.arista.command_processor.config import ConfigCommandProcessor
from fake_switches.arista.command_processor.config_vlan import ConfigVlanCommandProcessor
from fake_switches.arista.command_processor.default import DefaultCommandProcessor
from fake_switches.arista.command_processor.enabled import EnabledCommandProcessor
from fake_switches.command_processing.piping_processor_base import NotPipingProcessor
from fake_switches.command_processing.shell_session import ShellSession
from fake_switches.switch_core import SwitchCore
from fake_switches.terminal import LoggingTerminalController


class AristaSwitchCore(SwitchCore):

    def __init__(self, switch_configuration):
        super(AristaSwitchCore, self).__init__(switch_configuration)
        self.switch_configuration.add_vlan(self.switch_configuration.new("Vlan", 1))

        self.logger = None
        self.last_connection_id = 0

    def launch(self, protocol, terminal_controller):
        self.last_connection_id += 1

        self.logger = logging.getLogger("fake_switches.arista.{}.{}.{}"
                                        .format(self.switch_configuration.name, self.last_connection_id, protocol))

        processor = DefaultCommandProcessor(self.new_command_processor())

        processor.init(self.switch_configuration,
                       LoggingTerminalController(self.logger, terminal_controller),
                       self.logger,
                       NotPipingProcessor())

        return AristaShellSession(processor)

    @staticmethod
    def get_default_ports():
        return []

    def new_command_processor(self):
        return EnabledCommandProcessor(
            config=ConfigCommandProcessor(
                config_vlan=ConfigVlanCommandProcessor()
            )
        )

    def get_netconf_protocol(self):
        return None


class AristaShellSession(ShellSession):
    def handle_unknown_command(self, line):
        self.command_processor.terminal_controller.write("% Invalid input\n")
