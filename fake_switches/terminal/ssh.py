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

from twisted.conch import recvline
from fake_switches.terminal import TerminalController


class SwitchSSHShell(recvline.HistoricRecvLine):
    def __init__(self, user, switch_core):
        self.user = user
        self.switch_core = switch_core
        self.session = None
        self.awaiting_keystroke = None

    # Hack to get rid of magical characters that reset the screen / clear / goto position 0, 0
    def initializeScreen(self):
        self.mode = 'insert'

    def connectionMade(self):
        recvline.HistoricRecvLine.connectionMade(self)
        self.session = self.switch_core.launch("ssh", SshTerminalController(
            shell=self
        ))

    def lineReceived(self, line):
        still_listening = self.session.receive(line)
        if not still_listening:
            self.terminal.loseConnection()

    def keystrokeReceived(self, keyID, modifier):
        if keyID in self._printableChars:
            if self.awaiting_keystroke is not None:
                args = self.awaiting_keystroke[1] + [keyID]
                cmd = self.awaiting_keystroke[0]
                cmd(*args)
                return

        super(SwitchSSHShell, self).keystrokeReceived(keyID, modifier)

    # replacing behavior of twisted/conch/recvline.py:205
    def characterReceived(self, ch, moreCharactersComing):
        command_processor = self.get_actual_processor()

        if command_processor.replace_input is False:
            self.terminal.write(ch)
        else:
            self.terminal.write(len(ch) * command_processor.replace_input)

        if self.mode == 'insert':
            self.lineBuffer.insert(self.lineBufferIndex, ch)
        else:
            self.lineBuffer[self.lineBufferIndex:self.lineBufferIndex+1] = [ch]
        self.lineBufferIndex += 1

    def get_actual_processor(self):
        proc = self.session.command_processor
        while proc.sub_processor is not None:
            proc = proc.sub_processor
        return proc


class SshTerminalController(TerminalController):
    def __init__(self, shell):
        self.shell = shell

    def write(self, text):
        self.shell.terminal.write(text)

    def add_any_key_handler(self, callback, *params):
        self.shell.awaiting_keystroke = (callback, list(params))

    def remove_any_key_handler(self):
        self.shell.awaiting_keystroke = None

