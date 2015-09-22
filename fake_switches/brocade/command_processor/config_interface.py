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

from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.switch_configuration import split_port_name, VlanPort


class ConfigInterfaceCommandProcessor(BaseCommandProcessor):
    def __init__(self, switch_configuration, terminal_controller, logger, piping_processor, port):
        BaseCommandProcessor.__init__(self, switch_configuration, terminal_controller, logger, piping_processor)
        self.port = port

    def get_prompt(self):
        return "SSH@%s(config-if-e1000-%s)#" % (self.switch_configuration.name, split_port_name(self.port.name)[1])

    def do_enable(self, *_):
        self.port.shutdown = False

    def do_disable(self, *_):
        self.port.shutdown = None

    def do_vrf(self, *args):
        if "forwarding".startswith(args[0]):
            if len(args) > 1:
                if isinstance(self.port, VlanPort):
                    for ip in self.port.ips[:]:
                        self.port.remove_ip(ip)
                vrf = self.switch_configuration.get_vrf(args[1])
                if vrf is None:
                    self.write_line("Error - VRF({}) does not exist or Route-Distinguisher not specified or Address Family not configured".format(
                        args[1]))
                else:
                    self.port.vrf = vrf
                    self.write_line("Warning: All IPv4 and IPv6 addresses (including link-local) on this interface have been removed")

    def do_no_vrf(self, *args):
        if "forwarding".startswith(args[0]):
            if len(args) == 1:
                self.write_line("Incomplete command.")
            elif self.port.vrf.name != args[1]:
                self.write_line("Error - VRF({}) does not exist or Route-Distinguisher not specified or Address Family not configured".format(
                    args[1]))
            else:
                if isinstance(self.port, VlanPort):
                    for ip in self.port.ips[:]:
                        self.port.remove_ip(ip)
                self.port.vrf = None
                self.write_line("Warning: All IPv4 and IPv6 addresses (including link-local) on this interface have been removed")

    def do_exit(self):
        self.is_done = True

    def do_port_name(self, *args):
        self.port.description = " ".join(args)

    def do_no_port_name(self, *_):
        self.port.description = None
