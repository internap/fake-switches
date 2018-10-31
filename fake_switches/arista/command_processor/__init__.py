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
import re
from functools import wraps

from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.dell.command_processor.config_interface import parse_vlan_list


class AristaBaseCommandProcessor(BaseCommandProcessor):
    def __init__(self, display):
        self.display = display

    def read_vlan_number(self, input):
        try:
            number = int(input)
        except ValueError:
            self.display.invalid_command(self, "Invalid input")
            return None

        if number < 0 or number > 4094:
            self.display.invalid_command(self, "Invalid input")
        elif number == 0:
            self.display.invalid_command(self, "Incomplete command")
        else:
            return number

        return None

    def read_interface_name(self, tokens, return_remaining=False):
        if len(tokens) == 0:
            self.display.invalid_command(self, "Invalid input")
            return None

        name, number = safe_split_port_name(tokens[0])
        if number is not None:
            remaining_tokens = tokens[1:]
        elif len(tokens) > 1:
            name, number = tokens[0:2]
            remaining_tokens = tokens[2:]
        else:
            self.display.invalid_command(self, "Incomplete command")
            return None

        name = name.capitalize()
        if name == "Vlan":
            if number is None:
                self.display.invalid_command(self, "Incomplete command")
                return None

            number = self.read_vlan_number(number)
            if number is None:
                return None

            number = str(number)
        else:
            existing_port = self.switch_configuration.get_port_by_partial_name(name + number)
            if existing_port is None:
                raise NotImplementedError

        full_name = name + number

        return full_name if not return_remaining else (full_name, remaining_tokens)

    def read_multiple_interfaces_name(self, tokens):
        names = []
        while len(tokens) > 0:
            result = self.read_interface_name(tokens, return_remaining=True)
            if result is None:
                self.display.invalid_command(self, "Invalid input")
                return

            name, tokens = result

            names.append(name)

        return names


def vlan_name(vlan):
    return vlan.name or ("default" if vlan.number == 1 else None)


def vlan_display_name(vlan):
    return vlan_name(vlan) or "VLAN{:04d}".format(vlan.number)


def safe_split_port_name(name):
    matches = re.search('\d', name)
    if matches:
        number_start, _ = matches.span()
        return name[0:number_start], name[number_start:]
    else:
        return name, None


def with_params(count):
    def decorator(fn):
        @wraps(fn)
        def wrapper(self, *params):
            if len(params) < count:
                self.display.invalid_command(self, "Incomplete command")
            elif len(params) > count:
                self.display.invalid_command(self, "Invalid input")
            else:
                return fn(self, *params)

        return wrapper

    return decorator


def with_vlan_list(fn):
    @wraps(fn)
    def wrapper(self, vlans):
        try:
            vlans = parse_vlan_list(vlans)
        except ValueError:
            self.display.invalid_command(self, "Invalid input")
            return

        return fn(self, vlans)

    return wrapper
