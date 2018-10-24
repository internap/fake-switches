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
from netaddr import IPNetwork

from fake_switches.arista.command_processor import AristaBaseCommandProcessor
from fake_switches.switch_configuration import split_port_name


class ConfigInterfaceCommandProcessor(AristaBaseCommandProcessor):
    def init(self, switch_configuration, terminal_controller, logger, piping_processor, *args):
        super(ConfigInterfaceCommandProcessor, self).init(switch_configuration, terminal_controller, logger,
                                                          piping_processor)
        self.port = args[0]

    def get_prompt(self):
        name, if_id = split_port_name(self.port.name)
        return self.switch_configuration.name + "(config-if-{}{})#".format(name[:2], if_id)

    def do_ip(self, *args):
        if "address".startswith(args[0]):
            new_ip, remainder = _read_ip(args[1:])

            if len(remainder) > 1:
                raise NotImplementedError

            ip_owner, existing_ip = self.switch_configuration.get_port_and_ip_by_ip(new_ip.ip)
            if not ip_owner or ip_owner == self.port:
                if len(remainder) > 0 and "secondary".startswith(remainder[0]):
                    self.port.add_ip(new_ip)
                else:
                    if len(self.port.ips) == 0:
                        self.port.add_ip(new_ip)
                    else:
                        self.port.ips[0] = new_ip
            else:
                self.display.invalid_result(
                    self, "Subnet {new} overlaps with existing subnet {current} of interface {owner}".format(
                        new=new_ip.network,
                        current=existing_ip.network,
                        owner=ip_owner.name))

            self.port.vendor_specific["has-internet-protocol"] = True

        else:
            raise NotImplementedError

    def do_no_ip(self, *args):
        if "address".startswith(args[0]):
            if len(args) == 1:
                for ip in list(reversed(self.port.ips)):
                    self.port.remove_ip(ip)
            else:
                new_ip, remainder = _read_ip(args[1:])

                if len(remainder) > 0 and "secondary".startswith(remainder[0]):
                    if new_ip not in self.port.ips[1:]:
                        self.display.warning(self, "Address {} was not found for deletion".format(new_ip))
                        return
                else:
                    if new_ip != self.port.ips[0]:
                        self.display.invalid_command(self, "Address {} does not match primary address {}"
                                                     .format(new_ip, self.port.ips[0]))
                        return

                    if len(self.port.ips) > 1:
                        self.display.invalid_command(self, "Primary address cannot be deleted before secondary")
                        return

                self.port.remove_ip(new_ip)
        else:
            raise NotImplementedError

    def do_exit(self):
        self.is_done = True


def _read_ip(tokens):
    if "/" in tokens[0]:
        new_ip = IPNetwork(tokens[0])
        remainder = tokens[1:]
    else:
        new_ip = IPNetwork("{}/{}".format(tokens[0], tokens[1]))
        remainder = tokens[2:]

    return new_ip, remainder
