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

from twisted.internet.protocol import Factory

from fake_switches.terminal.telnet import SwitchTelnetShell
from fake_switches.transports.base_transport import BaseTransport


class SwitchTelnetFactory(Factory):
    def __init__(self, switch_core):
        self.switch_core = switch_core

    def protocol(self):
        return SwitchTelnetShell(self.switch_core)


class SwitchTelnetService(BaseTransport):
    def hook_to_reactor(self, reactor):
        factory = SwitchTelnetFactory(self.switch_core)
        port = reactor.listenTCP(port=self.port, factory=factory, interface=self.ip)
        logging.info("{} (TELNET): Registered on {} tcp/{}".format(
            self.switch_core.switch_configuration.name, self.ip, self.port))
        return port
