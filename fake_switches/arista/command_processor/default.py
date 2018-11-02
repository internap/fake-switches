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

from fake_switches.arista.command_processor import vlan_display_name, AristaBaseCommandProcessor, InvalidVlanNumber, \
    VlanNumberIsZero, with_valid_port_list
from fake_switches.command_processing.shell_session import TerminalExitSignal
from fake_switches.dell.command_processor.enabled import to_vlan_ranges
from fake_switches.switch_configuration import VlanPort


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
        elif "interfaces".startswith(args[0]) and "switchport".startswith(args[-1]):
            self._show_interfaces_switchport(*args[1:-1])
        elif "interfaces".startswith(args[0]):
            self._show_interfaces(*args[1:])
        else:
            raise NotImplementedError

    def _show_vlan(self, *args):
        if len(args) == 1:
            try:
                number = self.read_vlan_number(args[0])
            except VlanNumberIsZero:
                self.display.invalid_command(self, "Incomplete command")
                return
            except InvalidVlanNumber:
                self.display.invalid_command(self, "Invalid input")
                return

            vlans = list(filter(lambda e: e.number == number, self.switch_configuration.vlans))
            if len(vlans) == 0:
                self.display.invalid_result(self, "VLAN {} not found in current VLAN database".format(args[0]),
                                            json_data=_to_vlans_json([]))
                return
        else:
            vlans = self.switch_configuration.vlans

        self.display.show_vlans(self, _to_vlans_json(vlans))

    @with_valid_port_list
    def _show_interfaces(self, ports):
        self.display.show_interface(self, _to_interface_json(ports))

    @with_valid_port_list
    def _show_interfaces_switchport(self, ports):
        phys_ports = filter(lambda p: not isinstance(p, VlanPort), ports)
        self.display.show_interface_switchport(self, _to_switchport_json(phys_ports))


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


def _to_interface_json(ports):
    return {
        "interfaces": {
            port.name: _json_format_interface(port) for port in ports
        }
    }


def _json_format_interface(port):
    if isinstance(port, VlanPort):
        return _to_ip_interface_json(port)
    else:
        return _to_phys_interface_json(port)


def _to_phys_interface_json(port):
    return {
        "lastStatusChangeTimestamp": 0.0,
        "name": port.name,
        "interfaceStatus": "connected",
        "autoNegotiate": "unknown",
        "burnedInAddress": "00:00:00:00:00:00",
        "loopbackMode": "loopbackNone",
        "interfaceStatistics": {
            "inBitsRate": 0.0,
            "inPktsRate": 0.0,
            "outBitsRate": 0.0,
            "updateInterval": 0.0,
            "outPktsRate": 0.0
        },
        "mtu": 9214,
        "hardware": "ethernet",
        "duplex": "duplexFull",
        "bandwidth": 0,
        "forwardingModel": "bridged",
        "lineProtocolStatus": "up",
        "interfaceCounters": {
            "outBroadcastPkts": 0,
            "outUcastPkts": 0,
            "totalOutErrors": 0,
            "inMulticastPkts": 0,
            "counterRefreshTime": 0,
            "inBroadcastPkts": 0,
            "outputErrorsDetail": {
                "deferredTransmissions": 0,
                "txPause": 0,
                "collisions": 0,
                "lateCollisions": 0
            },
            "inOctets": 0,
            "outDiscards": 0,
            "outOctets": 0,
            "inUcastPkts": 0,
            "inTotalPkts": 0,
            "inputErrorsDetail": {
                "runtFrames": 0,
                "rxPause": 0,
                "fcsErrors": 0,
                "alignmentErrors": 0,
                "giantFrames": 0,
                "symbolErrors": 0
            },
            "linkStatusChanges": 5,
            "outMulticastPkts": 0,
            "totalInErrors": 0,
            "inDiscards": 0
        },
        "interfaceAddress": [],
        "physicalAddress": "00:00:00:00:00:00",
        "description": ""
    }


def _to_ip_interface_json(port):
    return {
        "bandwidth": 0,
        "burnedInAddress": "00:00:00:00:00:00",
        "description": "",
        "forwardingModel": "routed",
        "hardware": "vlan",
        "interfaceAddress": _interface_address_json(port),
        "interfaceStatus": "connected",
        "lastStatusChangeTimestamp": 0.0,
        "lineProtocolStatus": "up",
        "mtu": 1500,
        "name": port.name,
        "physicalAddress": "00:00:00:00:00:00"
    }


def _interface_address_json(port):
    if len(port.ips) == 0:
        if port.vendor_specific.get("has-internet-protocol", False):
            primary_ipn = IPNetwork("0.0.0.0/0")
            secondary_ipns = []
        else:
            return []
    else:
        primary_ipn = port.ips[0]
        secondary_ipns = port.ips[1:]

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


def _to_switchport_json(ports):
    return {
        "switchports": {
            port.name: {
                "enabled": True,
                "switchportInfo": {
                    "accessVlanId": 1,
                    "accessVlanName": "default",
                    "dot1qVlanTagRequired": False,
                    "dot1qVlanTagRequiredStatus": False,
                    "dynamicAllowedVlans": {},
                    "dynamicTrunkGroups": [],
                    "macLearning": True,
                    "mode": port.mode or "access",
                    "sourceportFilterMode": "enabled",
                    "staticTrunkGroups": [],
                    "tpid": "0x8100",
                    "tpidStatus": True,
                    "trunkAllowedVlans": _allow_vlans(port.trunk_vlans),
                    "trunkingNativeVlanId": 1,
                    "trunkingNativeVlanName": "default"
                }
            } for port in ports
        }
    }


def _allow_vlans(vlans):
    if vlans is None:
        return "ALL"
    if len(vlans) == 0:
        return "NONE"

    return to_vlan_ranges(vlans)
