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

from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.switch_configuration import VlanPort, AggregatedPort


class ConfigCommandProcessor(BaseCommandProcessor):
    interface_separator = ""

    def __init__(self, config_vlan, config_vrf, config_interface):
        super(ConfigCommandProcessor, self).__init__()
        self.config_vlan_processor = config_vlan
        self.config_vrf_processor = config_vrf
        self.config_interface_processor = config_interface

    def get_prompt(self):
        return self.switch_configuration.name + "(config)#"

    def do_vlan(self, raw_number, *_):
        number = int(raw_number)
        if number < 0:
            self.write_line("Command rejected: Bad VLAN list - character #1 ('-') delimits a VLAN number")
            self.write_line(" which is out of the range 1..4094.")
        elif number < 1 or number > 4094:
            self.write_line("Command rejected: Bad VLAN list - character #X (EOL) delimits a VLAN")
            self.write_line("number which is out of the range 1..4094.")
        else:
            vlan = self.switch_configuration.get_vlan(number)
            if not vlan:
                vlan = self.switch_configuration.new("Vlan", number)
                self.switch_configuration.add_vlan(vlan)
            self.move_to(self.config_vlan_processor, vlan)

    def do_no_vlan(self, *args):
        vlan = self.switch_configuration.get_vlan(int(args[0]))
        if vlan:
            self.switch_configuration.remove_vlan(vlan)

    def do_no_ip(self, cmd, *args):
        if "vrf".startswith(cmd):
            self.switch_configuration.remove_vrf(args[0])
        elif "route".startswith(cmd):
            self.switch_configuration.remove_static_route(args[0], args[1])

    def do_ip(self, cmd, *args):
        if "vrf".startswith(cmd):
            vrf = self.switch_configuration.new("VRF", args[0])
            self.switch_configuration.add_vrf(vrf)
            self.move_to(self.config_vrf_processor, vrf)
        elif "route".startswith(cmd):
            static_route = self.switch_configuration.new("Route", *args)
            self.switch_configuration.add_static_route(static_route)

    def do_interface(self, *args):
        interface_name = self.interface_separator.join(args)
        port = self.switch_configuration.get_port_by_partial_name(interface_name)
        if port:
            self.move_to(self.config_interface_processor, port)
        else:
            m = re.match("vlan{separator}(\d+)".format(separator=self.interface_separator), interface_name.lower())
            if m:
                vlan_id = int(m.groups()[0])
                new_vlan_interface = self.make_vlan_port(vlan_id, interface_name)
                self.switch_configuration.add_port(new_vlan_interface)
                self.move_to(self.config_interface_processor, new_vlan_interface)
            elif interface_name.lower().startswith('port-channel'):
                new_int = self.make_aggregated_port(interface_name)
                self.switch_configuration.add_port(new_int)
                self.move_to(self.config_interface_processor, new_int)
            else:
                self.show_unknown_interface_error_message()

    def do_no_interface(self, *args):
        port = self.switch_configuration.get_port_by_partial_name("".join(args))
        if isinstance(port, VlanPort) or isinstance(port, AggregatedPort):
            self.switch_configuration.remove_port(port)

    def do_default(self, cmd, *args):
        if 'interface'.startswith(cmd):
            interface_name = self.interface_separator.join(args)
            port = self.switch_configuration.get_port_by_partial_name(interface_name)
            if port:
                port.reset()
            else:
                self.show_unknown_interface_error_message()

    def do_exit(self):
        self.is_done = True

    def show_unknown_interface_error_message(self):
        self.write_line("              ^")
        self.write_line("% Invalid input detected at '^' marker (not such interface)")
        self.write_line("")

    def make_vlan_port(self, vlan_id, interface_name):
        return self.switch_configuration.new("VlanPort", vlan_id, interface_name.capitalize())

    def make_aggregated_port(self, interface_name):
        return self.switch_configuration.new("AggregatedPort", interface_name.capitalize())
