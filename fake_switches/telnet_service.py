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
from twisted.conch.telnet import TelnetTransport, StatefulTelnetProtocol, ECHO
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver


class SwitchTelnetShell(StatefulTelnetProtocol):
    count = 0

    def __init__(self, switch_core):
        self.switch_core = switch_core
        self.processor = None

    def connectionMade(self):
        self.out('Username: ')
        self.state = 'USERNAME'

    def telnet_USERNAME(self, _):
        self.transport.will(ECHO)
        self.out('Password: ')
        return 'PASSWORD'

    def telnet_PASSWORD(self, _):
        def login(_):
            self.processor = self.switch_core.launch("telnet", self.out)
            self.state = 'COMMAND'

        self.transport.wont(ECHO).addCallback(login)
        return 'Discard'

    def telnet_COMMAND(self, line):
        keep_going = self.processor.receive(line)

        # NOTE(mmitchell): This does not fully implement replace_input's contract.
        #                  It will simply echo back or not characters, not replace them.
        if self.processor.command_processor.replace_input == '':
            if self.transport.getOptionState(ECHO).us.state == 'no':
                self.transport.will(ECHO)
        else:
            if self.transport.getOptionState(ECHO).us.state == 'yes':
                self.transport.wont(ECHO)

        if not keep_going:
            self.transport.loseConnection()

    def out(self, data):
        self.transport.write(data)

    def dataReceived(self, data):
        if data == "\r":
            data = "\r\n"
        return LineReceiver.dataReceived(self, data)


class SwitchShellFactory(object):
    def __init__(self, switch_core):
        self.switch_core = switch_core

    def __call__(self, *args, **kwargs):
        return SwitchTelnetShell(self.switch_core)


class SwitchTelnetFactory(Factory):
    def __init__(self, switch_core):
        self.switch_core = switch_core

    def _protocol(self):
        return TelnetTransport(SwitchShellFactory(self.switch_core))

    protocol = _protocol


class SwitchTelnetService(object):
    def __init__(self, ip, telnet_port=23, switch_core=None, **_):
        self.ip = ip
        self.port = telnet_port
        self.switch_core = switch_core

    def hook_to_reactor(self, reactor):
        factory = SwitchTelnetFactory(self.switch_core)
        port = reactor.listenTCP(port=self.port, factory=factory, interface=self.ip)
        logging.info(
            "%s (TELNET): Registered on %s tcp/%s" % (self.switch_core.switch_configuration.name, self.ip, self.port))
        return port
