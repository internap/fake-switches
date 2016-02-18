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

from fake_switches.adapters import tftp_reader
from fake_switches.command_processing.piping_processor_base import NotPipingProcessor
from fake_switches.terminal import NoopTerminalController


class SwitchTftpParser(object):
    def __init__(self, configuration, reader=None):
        self.configuration = configuration
        self.reader = reader if reader else tftp_reader
        self.logger = logging.getLogger("fake_switches.%s.tftp" % self.configuration.name)

    def parse(self, url, filename, command_processor_class):
        self.logger.info("Reading : %s/%s" % (url, filename))

        data = self.reader.read_tftp(url, filename).split("\n")

        command_processor = command_processor_class(
            self.configuration, NoopTerminalController(),
            self.logger, NotPipingProcessor())

        for line in data:
            self.logger.debug("Processing : %s" % line)
            command_processor.process_command(line)
