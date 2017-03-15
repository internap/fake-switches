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

from fake_switches.brocade.command_processor.config_vrf import ConfigVrfCommandProcessor
from fake_switches.brocade.command_processor.piping import \
    PipingProcessor
from fake_switches.dell.dell_core import DellSwitchCore, DellShellSession
from fake_switches.dell10g.command_processor.config import Dell10GConfigCommandProcessor
from fake_switches.dell10g.command_processor.config_interface import Dell10GConfigInterfaceCommandProcessor
from fake_switches.dell10g.command_processor.config_vlan import Dell10GConfigureVlanCommandProcessor
from fake_switches.dell10g.command_processor.default import \
    Dell10GDefaultCommandProcessor
from fake_switches.dell10g.command_processor.enabled import Dell10GEnabledCommandProcessor
from fake_switches.switch_configuration import Port
from fake_switches.terminal import LoggingTerminalController


class Dell10GSwitchCore(DellSwitchCore):
    def launch(self, protocol, terminal_controller):
        self.last_connection_id += 1
        self.logger = logging.getLogger("fake_switches.dell10g.%s.%s.%s" % (self.switch_configuration.name, self.last_connection_id, protocol))

        processor = Dell10GDefaultCommandProcessor(
            enabled=Dell10GEnabledCommandProcessor(
                config=Dell10GConfigCommandProcessor(
                    config_vlan=Dell10GConfigureVlanCommandProcessor(),
                    config_vrf=ConfigVrfCommandProcessor(),
                    config_interface=Dell10GConfigInterfaceCommandProcessor()
                )))
        processor.init(
            switch_configuration=self.switch_configuration,
            terminal_controller=LoggingTerminalController(self.logger, terminal_controller),
            piping_processor=PipingProcessor(self.logger),
            logger=self.logger)

        return DellShellSession(processor)

    @staticmethod
    def get_default_ports():
        return [
            Port("tengigabitethernet 0/0/1"),
            Port("tengigabitethernet 0/0/2"),
            Port("tengigabitethernet 1/0/1"),
            Port("tengigabitethernet 1/0/2")
        ]
