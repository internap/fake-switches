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

import string

from twisted.conch.telnet import ECHO, Telnet, SGA, CR, LF

from fake_switches.terminal import lf_to_crlf
from fake_switches.terminal import TerminalController


class StatefulTelnet(Telnet, object):
    """
    This is an easy telnet service to mock a telnet server
    It does not implement everything a terminal does, only what
    automated code calling it would require, example : line editing.
    """

    def __init__(self):
        super(StatefulTelnet, self).__init__()

        self.handler = None
        self._buffer = None
        self._key_handlers = None
        self._printable_chars = set(string.printable)
        self._replace_input = None

    def connectionMade(self):
        self.will(ECHO)
        self.will(SGA)

        self.handler = lambda data: None
        self._buffer = ""
        self._key_handlers = {
            CR: self._run_command,
            LF: self._run_command,
        }

    def applicationDataReceived(self, data):
        for key in data:
            m = self._key_handlers.get(key)
            if m is not None:
                m()
            elif key in self._printable_chars:
                self._buffer += key
                if self._replace_input is None:
                    self.write(key)
                elif self._replace_input != "":
                    self.write(self._replace_input)

    def write(self, data):
        self.transport.write(lf_to_crlf(data))

    def writeln(self, data):
        self.write(data)
        self.next_line()

    def next_line(self):
        self.write(CR + LF)

    def enable_input_replacement(self, replace_char):
        self._replace_input = replace_char

    def disable_input_replacement(self):
        self._replace_input = None

    def _run_command(self):
        self.next_line()
        self.handler(self._buffer)
        self._buffer = ""

    def disableRemote(self, option):
        return True

    def enableRemote(self, option):
        return True

    def enableLocal(self, option):
        return True

    def disableLocal(self, option):
        return True


class SwitchTelnetShell(StatefulTelnet):
    count = 0

    def __init__(self, switch_core):
        super(SwitchTelnetShell, self).__init__()
        self.switch_core = switch_core
        self.session = None
        self.awaiting_keystroke = None

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
        self.session = self.switch_core.launch(
            "telnet", TelnetTerminalController(shell=self))
        self.handler = self.command

    def command(self, line):
        keep_going = self.session.receive(line)

        if self.session.command_processor.replace_input is False:
            self.disable_input_replacement()
        else:
            self.enable_input_replacement(self.session.command_processor.replace_input)

        if not keep_going:
            self.transport.loseConnection()

    def applicationDataReceived(self, data):
        if data in self._printable_chars:
            if self.awaiting_keystroke is not None:
                args = self.awaiting_keystroke[1] + [data]
                cmd = self.awaiting_keystroke[0]
                cmd(*args)
                return

        super(SwitchTelnetShell, self).applicationDataReceived(data)

    def get_actual_processor(self):
        if not self.session:
            return None
        command_processor = self.session.command_processor
        while command_processor.sub_processor is not None:
            command_processor = command_processor.sub_processor
        return command_processor

    def handle_keystroke(self, data):
        command_processor = self.get_actual_processor()
        return command_processor is not None and command_processor.keystroke(data)


class TelnetTerminalController(TerminalController):
    def __init__(self, shell):
        self.shell = shell

    def write(self, text):
        self.shell.write(text)

    def add_any_key_handler(self, callback, *params):
        self.shell.awaiting_keystroke = (callback, list(params))

    def remove_any_key_handler(self):
        self.shell.awaiting_keystroke = None
