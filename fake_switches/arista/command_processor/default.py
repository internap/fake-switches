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

from fake_switches.arista.command_processor import vlan_display_name, AristaBaseCommandProcessor
from fake_switches.command_processing.shell_session import TerminalExitSignal


class DefaultCommandProcessor(AristaBaseCommandProcessor):
    def __init__(self, display_class, enabled):
        super(DefaultCommandProcessor, self).__init__(display_class)
        self.enabled_processor = enabled

    def get_prompt(self):
        return self.switch_configuration.name + ">"

    def do_exit(self):
        raise TerminalExitSignal()

    def do_enable(self):
        self.move_to(self.enabled_processor)

    def do_show(self, *args):
        if "vlan".startswith(args[0]):
            self._show_vlan(*args[1:])
        elif "interfaces".startswith(args[0]):
            self._show_interfaces(*args[1:])
        else:
            raise NotImplementedError

    def _show_vlan(self, *args):
        if len(args) == 1:
            number = self.read_vlan_number(args[0])
            if number is None:
                return

            vlans = list(filter(lambda e: e.number == number, self.switch_configuration.vlans))
            if len(vlans) == 0:
                self.display.invalid_result(self, "VLAN {} not found in current VLAN database".format(args[0]),
                                            json_data=_to_vlans_json([]))
                return
        else:
            vlans = self.switch_configuration.vlans

        self.display.show_vlans(self, _to_vlans_json(vlans))

    def _show_interfaces(self, *args):
        if len(args) > 2:
            raise NotImplementedError

        if len(args) == 0:
            interfaces = self.switch_configuration.get_vlan_ports()
        else:
            interface = self.switch_configuration.get_port_by_partial_name(self.read_interface_name(args))

            if interface is None:
                self.display.invalid_command(self, "Interface does not exist", json_data=None)
                return

            interfaces = [interface]

        self.display.show_interface(self, _to_ip_interface_json(interfaces))


def _to_vlans_json(vlans):
    return {
        "vlans": {
            str(vlan.number): {
                "dynamic": False,
                "interfaces": {},
                "name": vlan_display_name(vlan),
                "status": "active"
            } for vlan in vlans
        }
    }


def _to_ip_interface_json(interfaces):
    return {
        "interfaces": {
            interface.name: {
                "bandwidth": 0,
                "burnedInAddress": "00:00:00:00:00:00",
                "description": "",
                "forwardingModel": "routed",
                "hardware": "vlan",
                "interfaceAddress": _interface_address_json(interface),
                "interfaceStatus": "connected",
                "lastStatusChangeTimestamp": 0.0,
                "lineProtocolStatus": "up",
                "mtu": 1500,
                "name": interface.name,
                "physicalAddress": "00:00:00:00:00:00"
            } for interface in interfaces
        }
    }


def _interface_address_json(interface):
    if len(interface.ips) == 0:
        if interface.vendor_specific.get("has-internet-protocol", False):
            primary_ipn = IPNetwork("0.0.0.0/0")
            secondary_ipns = []
        else:
            return []
    else:
        primary_ipn = interface.ips[0]
        secondary_ipns = interface.ips[1:]

    return [{
        "broadcastAddress": "255.255.255.255",
        "dhcp": False,
        "primaryIp": {
            "address": str(primary_ipn.ip),
            "maskLen": primary_ipn.prefixlen
        },
        "secondaryIps": {
            str(ipn.ip): {
                "address": str(ipn.ip),
                "maskLen": ipn.prefixlen
            } for ipn in secondary_ipns
        },
        "secondaryIpsOrderedList": [
            {
                "address": str(ipn.ip),
                "maskLen": ipn.prefixlen
            }
            for ipn in secondary_ipns
        ],
        "virtualIp": {
            "address": "0.0.0.0",
            "maskLen": 0
        },
        "virtualSecondaryIps": {},
        "virtualSecondaryIpsOrderedList": []
    }]
