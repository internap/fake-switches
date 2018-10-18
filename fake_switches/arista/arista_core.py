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

from twisted.web import resource

from fake_switches.arista.command_processor.config import ConfigCommandProcessor
from fake_switches.arista.command_processor.config_vlan import ConfigVlanCommandProcessor
from fake_switches.arista.command_processor.default import DefaultCommandProcessor
from fake_switches.arista.command_processor.terminal_display import TerminalDisplay
from fake_switches.arista.command_processor.enabled import EnabledCommandProcessor
from fake_switches.arista.eapi import EAPI
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

        processor = self.processor_stack(display_class=TerminalDisplay)

        processor.init(self.switch_configuration,
                       LoggingTerminalController(self.logger, terminal_controller),
                       self.logger,
                       NotPipingProcessor())

        return AristaShellSession(processor)

    @staticmethod
    def get_default_ports():
        return []

    def processor_stack(self, display_class):
        common = (display_class,)

        return DefaultCommandProcessor(
            *common, enabled=EnabledCommandProcessor(
                *common, config=ConfigCommandProcessor(
                    *common, config_vlan=ConfigVlanCommandProcessor(*common)
                )
            )
        )

    def get_netconf_protocol(self):
        return None

    def get_http_resource(self):
        root = resource.Resource()
        root.putChild(b'command-api', EAPI(
            switch_configuration=self.switch_configuration,
            processor_stack_factory=self.processor_stack,
            logger=logging.getLogger("fake_switches.arista.{}.eapi".format(self.switch_configuration.name))
        ))
        return root


class AristaShellSession(ShellSession):
    def handle_unknown_command(self, line):
        self.command_processor.terminal_controller.write("% Invalid input\n")
