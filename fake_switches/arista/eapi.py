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

import json

from twisted.web import resource

from fake_switches.command_processing.piping_processor_base import NotPipingProcessor
from fake_switches.terminal import TerminalController


class EAPI(resource.Resource, object):
    isLeaf = True

    def __init__(self, switch_configuration, command_processor, logger):
        super(EAPI, self).__init__()

        self.switch_configuration = switch_configuration
        self.command_processor = command_processor
        self.logger = logger

    def render_POST(self, request):
        content = json.loads(request.content.read().decode())
        self.logger.info("Request in: {}".format(content))

        buffer = BufferingTerminalController()
        self.command_processor.init(
            switch_configuration=self.switch_configuration,
            terminal_controller=buffer,
            logger=self.logger,
            piping_processor=NotPipingProcessor()
        )

        result = {
            "jsonrpc": content["jsonrpc"],
            "id": content["id"],
            "result": []
        }

        for cmd in content["params"]["cmds"]:
            self.command_processor.process_command(cmd)
            result["result"].append({
                "output": strip_prompt(self.command_processor, buffer.pop())
            })

        return json.dumps(result).encode()


def strip_prompt(command_processor, content):
    prompt = command_processor.get_prompt()
    return content[:-len(prompt)]


class BufferingTerminalController(TerminalController):

    def __init__(self):
        self.buffer = ""

    def pop(self):
        buffer = self.buffer
        self.buffer = ""
        return buffer

    def write(self, text):
        self.buffer += text
