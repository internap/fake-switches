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

from fake_switches.telnet.stateful_telnet import StatefulTelnet


class SwitchTelnetShell(StatefulTelnet):
    count = 0

    def __init__(self, switch_core):
        super(SwitchTelnetShell, self).__init__()
        self.switch_core = switch_core
        self.processor = None

    def connectionMade(self):
        super(SwitchTelnetShell, self).connectionMade()
        self.write('Username: ')
        self.handler = self.validate_username

    def validate_username(self, _):
        self.write('Password: ')
        self.enable_input_replacement("")
        self.handler = self.validate_password

    def validate_password(self, _):
        self.disable_input_replacement()
        self.processor = self.switch_core.launch("telnet", self.write)
        self.handler = self.command

    def command(self, line):
        keep_going = self.processor.receive(line)

        if self.processor.command_processor.replace_input is False:
            self.disable_input_replacement()
        else:
            self.enable_input_replacement(self.processor.command_processor.replace_input)

        if not keep_going:
            self.transport.loseConnection()


class SwitchTelnetFactory(Factory):
    def __init__(self, switch_core):
        self.switch_core = switch_core

    def protocol(self):
        return SwitchTelnetShell(self.switch_core)


class SwitchTelnetService(object):
    def __init__(self, ip, telnet_port=23, switch_core=None, **_):
        self.ip = ip
        self.port = telnet_port
        self.switch_core = switch_core

    def hook_to_reactor(self, reactor):
        factory = SwitchTelnetFactory(self.switch_core)
        port = reactor.listenTCP(port=self.port, factory=factory, interface=self.ip)
        logging.info("{} (TELNET): Registered on {} tcp/{}".format(
            self.switch_core.switch_configuration.name, self.ip, self.port))
        return port
