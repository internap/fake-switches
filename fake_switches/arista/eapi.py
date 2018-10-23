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

from fake_switches.arista.command_processor.terminal_display import TerminalDisplay
from fake_switches.command_processing.piping_processor_base import NotPipingProcessor
from fake_switches.terminal import TerminalController


class EAPI(resource.Resource, object):
    isLeaf = True

    def __init__(self, switch_configuration, processor_stack_factory, logger):
        super(EAPI, self).__init__()

        self.switch_configuration = switch_configuration
        self.processor_stack_factory = processor_stack_factory
        self.logger = logger

    def render_POST(self, request):
        content = json.loads(request.content.read().decode())
        self.logger.info("Request in: {}".format(content))

        driver = driver_for(content["params"]["format"])

        command_processor = self.processor_stack_factory(display=driver.display_class())
        command_processor.init(
            switch_configuration=self.switch_configuration,
            terminal_controller=BufferingTerminalController(),
            logger=self.logger,
            piping_processor=NotPipingProcessor()
        )

        result = {
            "jsonrpc": content["jsonrpc"],
            "id": content["id"],
        }

        command_index = 1
        command_results = []
        try:
            for cmd in content["params"]["cmds"]:
                command_processor.process_command(cmd)
                command_results.append(driver.format_output(command_processor))
                command_index += 1
            result["result"] = command_results
        except CommandProcessorError as e:
            command_results.append(driver.format_errors([str(e)], base_obj=e.json_data))
            result["error"] = {
                "data": command_results,
                "message": "CLI command {index} of {count} '{cmd}' failed: {error}".format(
                    index=command_index,
                    count=len(content["params"]["cmds"]),
                    cmd=content["params"]["cmds"][command_index - 1],
                    error=e.error
                ),
                "code": e.code
            }

        return json.dumps(result).encode()


def driver_for(format):
    return {
        "json": JsonDriver(),
        "text": TextDriver()
    }[format]


class CommandProcessorError(Exception):
    code = None
    error = None

    def __init__(self, message, json_data):
        super(CommandProcessorError, self).__init__(message)

        self.json_data = json_data


class InvalidCommand(CommandProcessorError):
    code = 1002
    error = "invalid command"


class InvalidResult(CommandProcessorError):
    code = 1000
    error = "could not run command"


class JsonDisplay(object):
    def __init__(self, *_):
        self.display_object = None

    def invalid_command(self, processor, message, json_data=None):
        raise InvalidCommand(message, json_data=json_data)

    def invalid_result(self, processor, message, json_data=None):
        raise InvalidResult(message, json_data=json_data)

    def __getattr__(self, item):
        def collector(processor, obj):
            self.display_object = obj

        return collector


class JsonDriver(object):
    display_class = JsonDisplay

    def format_output(self, command_processor):
        obj = command_processor.display.display_object or {}
        obj['sourceDetail'] = ''
        return obj

    def format_errors(self, errors, base_obj):
        obj = base_obj or {}
        obj['sourceDetail'] = ''
        obj['errors'] = errors
        return obj


class TextDriver(object):
    display_class = TerminalDisplay

    def format_output(self, command_processor):
        return {
            "output": strip_prompt(command_processor, command_processor.terminal_controller.pop())
        }

    def format_errors(self, errors, base_obj):
        raise NotImplementedError


class BufferingTerminalController(TerminalController):

    def __init__(self):
        self.buffer = ""

    def pop(self):
        buffer = self.buffer
        self.buffer = ""
        return buffer

    def write(self, text):
        self.buffer += text


def strip_prompt(command_processor, content):
    prompt = command_processor.get_prompt()
    return content[:-len(prompt)]
