# Copyright 2018 Internap.
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

from hamcrest import assert_that, is_
from pyeapi.eapilib import CommandError

from tests.arista import enable, remove_vlan, create_vlan, create_interface_vlan, configuring_interface_vlan, \
    remove_interface_vlan, with_eapi
from tests.util.protocol_util import ProtocolTest, SshTester, with_protocol


class TestAristaShowInterface(ProtocolTest):
    tester_class = SshTester
    test_switch = "arista"

    @with_protocol
    @with_eapi
    def test_show_interfaces(self, t, api):
        enable(t)

        create_vlan(t, "299")
        create_interface_vlan(t, "299")
        configuring_interface_vlan(t, "299", do="ip address 1.1.1.2/24")

        create_vlan(t, "777")
        create_interface_vlan(t, "777")
        configuring_interface_vlan(t, "777", do="ip address 7.7.7.7/24")

        t.write("show interfaces")
        t.readln("Ethernet1 is up, line protocol is up (connected)")
        t.readln("  Hardware is Ethernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Ethernet MTU 9214 bytes")
        t.readln("  Full-duplex, Unconfigured, auto negotiation: off, uni-link: n/a")
        t.readln("  Up 0 minutes, 0 seconds")
        t.readln("  Loopback Mode : None")
        t.readln("  0 link status changes since last clear")
        t.readln("  Last clearing of \"show interface\" counters never")
        t.readln("  0 minutes input rate 0 bps (- with framing overhead), 0 packets/sec")
        t.readln("  0 minutes output rate 0 bps (- with framing overhead), 0 packets/sec")
        t.readln("     0 packets input, 0 bytes")
        t.readln("     Received 0 broadcasts, 0 multicast")
        t.readln("     0 runts, 0 giants")
        t.readln("     0 input errors, 0 CRC, 0 alignment, 0 symbol, 0 input discards")
        t.readln("     0 PAUSE input")
        t.readln("     0 packets output, 0 bytes")
        t.readln("     Sent 0 broadcasts, 0 multicast")
        t.readln("     0 output errors, 0 collisions")
        t.readln("     0 late collision, 0 deferred, 0 output discards")
        t.readln("     0 PAUSE output")
        t.readln("Ethernet2 is up, line protocol is up (connected)")
        t.readln("  Hardware is Ethernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Ethernet MTU 9214 bytes")
        t.readln("  Full-duplex, Unconfigured, auto negotiation: off, uni-link: n/a")
        t.readln("  Up 0 minutes, 0 seconds")
        t.readln("  Loopback Mode : None")
        t.readln("  0 link status changes since last clear")
        t.readln("  Last clearing of \"show interface\" counters never")
        t.readln("  0 minutes input rate 0 bps (- with framing overhead), 0 packets/sec")
        t.readln("  0 minutes output rate 0 bps (- with framing overhead), 0 packets/sec")
        t.readln("     0 packets input, 0 bytes")
        t.readln("     Received 0 broadcasts, 0 multicast")
        t.readln("     0 runts, 0 giants")
        t.readln("     0 input errors, 0 CRC, 0 alignment, 0 symbol, 0 input discards")
        t.readln("     0 PAUSE input")
        t.readln("     0 packets output, 0 bytes")
        t.readln("     Sent 0 broadcasts, 0 multicast")
        t.readln("     0 output errors, 0 collisions")
        t.readln("     0 late collision, 0 deferred, 0 output discards")
        t.readln("     0 PAUSE output")
        t.readln("Vlan299 is up, line protocol is up (connected)")
        t.readln("  Hardware is Vlan, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Internet address is 1.1.1.2/24")
        t.readln("  Broadcast address is 255.255.255.255")
        t.readln("  IP MTU 1500 bytes")
        t.readln("  Up 0 minutes, 0 seconds")
        t.readln("Vlan777 is up, line protocol is up (connected)")
        t.readln("  Hardware is Vlan, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Internet address is 7.7.7.7/24")
        t.readln("  Broadcast address is 255.255.255.255")
        t.readln("  IP MTU 1500 bytes")
        t.readln("  Up 0 minutes, 0 seconds")
        t.read("my_arista#")

        result = api.enable("show interfaces")

        expected = [
            {
                "command": "show interfaces",
                "encoding": "json",
                "result": {
                    "sourceDetail": "",
                    "interfaces": {
                        "Ethernet1": {
                            "lastStatusChangeTimestamp": 0.0,
                            "name": "Ethernet1",
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
                                "counterRefreshTime": 0.0,
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
                        },
                        "Ethernet2": {
                            "lastStatusChangeTimestamp": 0.0,
                            "name": "Ethernet2",
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
                                "counterRefreshTime": 0.0,
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
                        },
                        "Vlan299": {
                            "bandwidth": 0,
                            "burnedInAddress": "00:00:00:00:00:00",
                            "description": "",
                            "forwardingModel": "routed",
                            "hardware": "vlan",
                            "interfaceAddress": [
                                {
                                    "broadcastAddress": "255.255.255.255",
                                    "dhcp": False,
                                    "primaryIp": {
                                        "address": "1.1.1.2",
                                        "maskLen": 24
                                    },
                                    "secondaryIps": {},
                                    "secondaryIpsOrderedList": [],
                                    "virtualIp": {
                                        "address": "0.0.0.0",
                                        "maskLen": 0
                                    },
                                    "virtualSecondaryIps": {},
                                    "virtualSecondaryIpsOrderedList": []
                                }
                            ],
                            "interfaceStatus": "connected",
                            "lastStatusChangeTimestamp": 0.0,
                            "lineProtocolStatus": "up",
                            "mtu": 1500,
                            "name": "Vlan299",
                            "physicalAddress": "00:00:00:00:00:00"
                        },
                        "Vlan777": {
                            "bandwidth": 0,
                            "burnedInAddress": "00:00:00:00:00:00",
                            "description": "",
                            "forwardingModel": "routed",
                            "hardware": "vlan",
                            "interfaceAddress": [
                                {
                                    "broadcastAddress": "255.255.255.255",
                                    "dhcp": False,
                                    "primaryIp": {
                                        "address": "7.7.7.7",
                                        "maskLen": 24
                                    },
                                    "secondaryIps": {},
                                    "secondaryIpsOrderedList": [],
                                    "virtualIp": {
                                        "address": "0.0.0.0",
                                        "maskLen": 0
                                    },
                                    "virtualSecondaryIps": {},
                                    "virtualSecondaryIpsOrderedList": []
                                }
                            ],
                            "interfaceStatus": "connected",
                            "lastStatusChangeTimestamp": 0.0,
                            "lineProtocolStatus": "up",
                            "mtu": 1500,
                            "name": "Vlan777",
                            "physicalAddress": "00:00:00:00:00:00"
                        }
                    }
                }
            }
        ]
        assert_that(result, is_(expected), "actual={}\nexpected={}".format(json.dumps(result), json.dumps(expected)))

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")

        remove_interface_vlan(t, "777")
        remove_vlan(t, "777")

    @with_protocol
    @with_eapi
    def test_show_interfaces_unknown(self, t, api):
        t.write("show interfaces Et3")
        t.readln("% Invalid input")
        t.read("my_arista>")

        with self.assertRaises(CommandError) as expect:
            api.enable("show interfaces Et3", strict=True)

        assert_that(str(expect.exception), is_(
            "Error [1002]: CLI command 2 of 2 'show interfaces Et3' failed: invalid command "
            "[Invalid input]"
        ))

    @with_protocol
    @with_eapi
    def test_show_interfaces_unknown(self, t, api):
        t.write("show interfaces Et3")
        t.readln("% Invalid input")
        t.read("my_arista>")

        with self.assertRaises(CommandError) as expect:
            api.enable("show interfaces Et3", strict=True)

        assert_that(str(expect.exception), is_(
            "Error [1002]: CLI command 2 of 2 'show interfaces Et3' failed: invalid command "
            "[Invalid input]"
        ))
