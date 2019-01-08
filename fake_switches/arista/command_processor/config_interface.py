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

from netaddr import IPNetwork, AddrFormatError

from fake_switches.arista.command_processor import AristaBaseCommandProcessor, with_params, with_vlan_list, \
    short_port_name


class ConfigInterfaceCommandProcessor(AristaBaseCommandProcessor):
    def init(self, switch_configuration, terminal_controller, logger, piping_processor, *args):
        super(ConfigInterfaceCommandProcessor, self).init(switch_configuration, terminal_controller, logger,
                                                          piping_processor)
        self.port = args[0]

    def get_prompt(self):
        return self.switch_configuration.name + "(config-if-{})#".format(short_port_name(self.port.name))

    def do_ip(self, *args):
        if "address".startswith(args[0]):
            self._add_ip(args[1:])
        elif "helper-address".startswith(args[0]):
            self._add_ip_helper(args[1:])
        elif "virtual-router".startswith(args[0]) and "address".startswith(args[1]):
            self._add_virtual_router_address(*args[2:])
        else:
            raise NotImplementedError

    def do_no_ip(self, *args):
        if "address".startswith(args[0]):
            self._remove_ip(args[1:])
        elif "helper-address".startswith(args[0]):
            self._remove_ip_helper(args[1:])
        elif "virtual-router".startswith(args[0]) and "address".startswith(args[1]) and len(args) == 2:
            self._remove_all_virtual_router_addresses()
        elif "virtual-router".startswith(args[0]) and "address".startswith(args[1]):
            self._remove_virtual_router_address(*args[2:])
        else:
            raise NotImplementedError

    def do_load_interval(self, *args):
        if len(args) == 0:
            self.display.invalid_command(self, "Incomplete command")
            return None

        load_interval = args[0]
        if not _is_valid_load_interval(load_interval):
            self.display.invalid_command(self, "Invalid input")
            return None

        self.port.load_interval = load_interval

    def do_no_load_interval(self):
        self.port.load_interval = None

    def do_mpls(self, *args):
        if args[0] == 'ip':
            self.port.mpls_ip = True
        else:
            raise NotImplementedError

    def do_no_mpls(self, *args):
        if args[0] == 'ip':
            self.port.mpls_ip = False
        else:
            raise NotImplementedError

    def do_switchport(self, *args):
        operations = [
            (("mode",), self._switchport_mode),
            (("trunk", "allowed", "vlan", "add"), self._switchport_trunk_allowed_vlan_add),
            (("trunk", "allowed", "vlan", "remove"), self._switchport_trunk_allowed_vlan_remove),
            (("trunk", "allowed", "vlan", "none"), self._switchport_trunk_allowed_vlan_none),
            (("trunk", "allowed", "vlan", "all"), self._switchport_trunk_allowed_vlan_all),
            (("trunk", "allowed", "vlan"), self._switchport_trunk_allowed_vlan)
        ]

        for cmd, target in operations:
            if _is_cmd(args, *cmd):
                target(*args[len(cmd):])
                return

        self.display.invalid_command(self, "Incomplete command")

    def do_no_switchport(self, *args):
        if _is_cmd(args, "mode"):
            self.port.mode = None
        elif _is_cmd(args, "trunk", "allowed", "vlan"):
            self.port.trunk_vlans = None
        else:
            raise NotImplementedError

    def do_exit(self):
        self.is_done = True

    def _add_ip(self, args):
        new_ip, remainder = _read_ip(args)
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

    def _remove_ip(self, args):
        if len(args) == 0:
            for ip in list(reversed(self.port.ips)):
                self.port.remove_ip(ip)
        else:
            new_ip, remainder = _read_ip(args)

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

    def _add_ip_helper(self, args):
        helper_address = self._read_helper_address(args)

        if helper_address is not None and args[0] not in self.port.ip_helpers:
            self.port.ip_helpers.append(args[0])

    def _remove_ip_helper(self, args):
        if len(args) == 0:
            self.port.ip_helpers = []
        else:
            helper_address = self._read_helper_address(args)
            if helper_address:
                self.port.ip_helpers.remove(helper_address)

    def _read_helper_address(self, args):
        if len(args) == 0:
            self.display.invalid_command(self, "Incomplete command")
            return None

        if not _is_word(args[0]) or len(args) > 1:
            self.display.invalid_command(self, "Invalid input")
            return None

        if len(args[0]) > 64:
            self.display.invalid_result(
                self,
                "Host name is invalid. Host name must contain only alphanumeric characters, '.' and '-'.\n"
                "It must begin and end with an alphanumeric character.\n"
                "Maximum characters in hostname is 64.")
            return None

        return args[0]

    @with_params(1)
    def _switchport_mode(self, mode):
        mode = mode.lower()
        if mode not in ("trunk",):
            self.display.invalid_command(self, "Invalid input")
            return

        self.port.mode = mode

    @with_params(1)
    @with_vlan_list
    def _switchport_trunk_allowed_vlan_add(self, vlans):
        if not _has_all_vlans(self.port):
            self.port.trunk_vlans += vlans

    @with_params(1)
    @with_vlan_list
    def _switchport_trunk_allowed_vlan_remove(self, vlans):
        if self.port.trunk_vlans is None:
            self.port.trunk_vlans = list(range(1, 4095))
        for v in vlans:
            if v in self.port.trunk_vlans:
                self.port.trunk_vlans.remove(v)

    @with_params(0)
    def _switchport_trunk_allowed_vlan_none(self):
        self.port.trunk_vlans = []

    @with_params(0)
    def _switchport_trunk_allowed_vlan_all(self, *extra):
        self.port.trunk_vlans = None

    @with_params(1)
    @with_vlan_list
    def _switchport_trunk_allowed_vlan(self, vlans):
        self.port.trunk_vlans = vlans

    @with_params(1)
    def _add_virtual_router_address(self, address):
        try:
            ipn = IPNetwork(address)
        except AddrFormatError:
            self.display.invalid_command(self, "Invalid input")
            return

        for i, varp_address in enumerate(self.port.varp_addresses):
            if varp_address.ip == ipn.ip:
                self.port.varp_addresses[i] = ipn
                break
        else:
            self.port.varp_addresses.append(ipn)

    @with_params(1)
    def _remove_virtual_router_address(self, address):
        ipn = IPNetwork(address)

        for i, varp_address in enumerate(self.port.varp_addresses):
            if varp_address.ip == ipn.ip:
                self.port.varp_addresses.pop(i)
                return

        raise NotImplementedError

    def _remove_all_virtual_router_addresses(self):
        self.port.varp_addresses = []


def _is_valid_load_interval(text):
    try:
        number = int(text)
    except ValueError:
        return False

    return 0 <= number <= 600


def _read_ip(tokens):
    if "/" in tokens[0]:
        new_ip = IPNetwork(tokens[0])
        remainder = tokens[1:]
    else:
        new_ip = IPNetwork("{}/{}".format(tokens[0], tokens[1]))
        remainder = tokens[2:]

    return new_ip, remainder


def _is_word(word):
    return re.match("^[[a-zA-Z0-9\-.]+$", word)


def _is_cmd(args, *expected):
    for arg, expectation in zip(args, expected):
        if not expectation.startswith(arg):
            return False

    return True


def _has_all_vlans(port):
    return port.trunk_vlans is None
