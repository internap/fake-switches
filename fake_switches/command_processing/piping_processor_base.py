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

from fake_switches.command_processing.command_processor import CommandProcessor


class PipingProcessorBase(CommandProcessor):

    def __init__(self, logger):
        self.logger = logger
        self.active_command = None

    def start_listening(self, command):
        func, args = self.get_command_func(command)

        if not func:
            self.logger.debug("%s can't process piping : %s" % (self.__class__.__name__, command))
            return False

        self.active_command = func(*args)
        return True

    def is_listening(self):
        return self.active_command is not None

    def pipe(self, data):
        return self.active_command.pipe(data)

    def stop_listening(self):
        self.active_command = None


class NotPipingProcessor(PipingProcessorBase):
    def __init__(self):
        super(NotPipingProcessor, self).__init__(None)


class StartOutputAt(object):
    def __init__(self, lookup):
        self.lookup = lookup
        self.found_lookup = False

    def pipe(self, data):
        if not self.found_lookup:
            self.found_lookup = self.lookup in data

        if self.found_lookup:
            return data
        else:
            return False


class Grep(object):
    def __init__(self, lookup):
        self.lookup = lookup

    def pipe(self, data):
        if self.lookup in data:
            return data
        else:
            return False
