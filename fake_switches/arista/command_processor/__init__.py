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
from fake_switches.switch_configuration import split_port_name


class AristaBaseCommandProcessor(BaseCommandProcessor):
    def __init__(self, display):
        self.display = display

    def read_vlan_number(self, input):
        try:
            number = int(input)
        except ValueError:
            raise VlanNumberIsNotAnInt

        if number < 0 or number > 4094:
            raise VlanNumberIsNotValid
        elif number == 0:
            raise VlanNumberIsZero
        else:
            return number

    def read_interface_name(self, tokens, return_remaining=False):
        if len(tokens) == 0:
            raise NothingToRead

        name, number = safe_split_port_name(tokens[0])
        if number is not None:
            remaining_tokens = tokens[1:]
        elif len(tokens) > 1:
            name, number = tokens[0:2]
            remaining_tokens = tokens[2:]
        else:
            raise NameIsIncomplete

        name = name.capitalize()
        if name == "Vlan":
            number = str(self.read_vlan_number(number))

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


def with_valid_port_list(fn):
    @wraps(fn)
    def wrapper(self, *args):
        if len(args) == 0:
            ports = self.switch_configuration.ports
        else:
            try:
                result = self.read_interface_name(args, return_remaining=True)
            except NameIsIncomplete:
                self.display.invalid_command(self, "Incomplete command")
                return
            except InvalidVlanNumber:
                self.display.invalid_command(self, "Invalid input")
                return

            port_name, remaining = result
            if len(remaining) > 0:
                self.display.invalid_command(self, "Invalid input")
                return

            port = self.switch_configuration.get_port_by_partial_name(port_name)

            if port is None:
                if port_name.startswith("Vlan"):
                    self.display.invalid_command(self, "Interface does not exist")
                else:
                    self.display.invalid_command(self, "Invalid input")
                return

            ports = [port]

        return fn(self, ports)

    return wrapper


def short_port_name(port_name):
    name, if_id = split_port_name(port_name)
    return "{}{}".format(name[:2], if_id)


class NothingToRead(Exception):
    pass


class NameIsIncomplete(Exception):
    pass


class InvalidVlanNumber(Exception):
    pass


class VlanNumberIsNotAnInt(InvalidVlanNumber):
    pass


class VlanNumberIsNotValid(InvalidVlanNumber):
    pass


class VlanNumberIsZero(VlanNumberIsNotValid):
    pass
