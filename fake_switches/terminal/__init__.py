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

import re


def lf_to_crlf(text):
    nb_subst = 1
    while nb_subst:
        text, nb_subst = re.subn("(^|[^\r])\n", "\\1\r\n", text)
    return text


class TerminalController(object):
    """
    Allow a command processor to interact with the actual terminal.  Actually
    it is possible to write text on the terminal and intercept key strokes.

    >>> terminal_controller = NoopTerminalController()

    Output text on the terminal:
    >>> terminal_controller.write('Hello World!')

    Register a keystroke interceptor:
    >>> def my_callback(param1, param2, key):
    ...     assert (param1, param2) == ('first', 'second')
    >>> terminal_controller.add_any_key_handler(my_callback, 'first', 'second')

    Resume normal input handling:
    >>> terminal_controller.remove_any_key_handler()
    """

    def write(self, text):
        """
        Write text on the terminal.  Some implementation may replace the text
        before it is sent to the terminal (by adding '\r' before each '\n').
        """
        raise NotImplemented()

    def add_any_key_handler(self, callback, *params):
        """
        Registers a function as a callback to intercept every "printable"
        keystroke.

        The callback will be called with all params passed here plus the key
        stroke made by the "user"
        """
        raise NotImplemented()

    def remove_any_key_handler(self):
        """
        Remove the keystroke interceptor and resume normal behavior.

        When an interceptor is in place no character is echoed on the terminal
        or recorded in the line input buffer.
        """
        raise NotImplemented()


class LoggingTerminalController(TerminalController):

    def __init__(self, logger, terminal_controller):
        """
        :param logger: log everything written on the terminal as debug
        :type logger: logging.Logger
        :param terminal_controller: the real terminal controller
        :type terminal_controller: TerminalController
        """
        self.logger = logger
        self.terminal_controller = terminal_controller

    def write(self, text):
        self.logger.debug("replying: %s" % repr(text))
        return self.terminal_controller.write(text)

    def add_any_key_handler(self, callback, *params):
        return self.terminal_controller.add_any_key_handler(callback, *params)

    def remove_any_key_handler(self):
        return self.terminal_controller.remove_any_key_handler()


class NoopTerminalController(TerminalController):

    def write(self, text):
        return None

    def add_any_key_handler(self, callback, *params):
        return None

    def remove_any_key_handler(self):
        return None
