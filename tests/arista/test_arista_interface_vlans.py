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
from hamcrest import assert_that, is_
from pyeapi.eapilib import CommandError

from tests.arista import enable, remove_vlan, create_vlan, create_interface_vlan, configuring_interface_vlan, \
    remove_interface_vlan, with_eapi
from tests.util.protocol_util import ProtocolTest, SshTester, with_protocol


class TestAristaInterfaceVlans(ProtocolTest):
    tester_class = SshTester
    test_switch = "arista"

    @with_protocol
    @with_eapi
    def test_ip_address_setup(self, t, api):
        enable(t)

        create_vlan(t, "299")
        create_interface_vlan(t, "299")
        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299"
        ])

        configuring_interface_vlan(t, "299", do="ip address 1.1.1.2/27")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip address 1.1.1.2/27"
        ])

        configuring_interface_vlan(t, "299", do="ip address 1.1.1.3 255.255.255.0")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip address 1.1.1.3/24"
        ])

        configuring_interface_vlan(t, "299", do="ip address 1.1.1.4/27 secondary")
        configuring_interface_vlan(t, "299", do="ip address 1.1.1.5/27 secondary")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip address 1.1.1.3/24",
            "   ip address 1.1.1.4/27 secondary",
            "   ip address 1.1.1.5/27 secondary"
        ])

        t.write("show interfaces vlan 0299")
        t.readln("Vlan299 is up, line protocol is up (connected)")
        t.readln("  Hardware is Vlan, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Internet address is 1.1.1.3/24")
        t.readln("  Secondary address is 1.1.1.4/27")
        t.readln("  Secondary address is 1.1.1.5/27")
        t.readln("  Broadcast address is 255.255.255.255")
        t.readln("  IP MTU 1500 bytes")
        t.readln("  Up 00 minutes, 00 seconds")
        t.read("my_arista#")

        result = api.enable("show interfaces VLAN0299")

        assert_that(result, is_([
            {
                "command": "show interfaces VLAN0299",
                "encoding": "json",
                "result": {
                    "sourceDetail": "",
                    "interfaces": {
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
                                        "address": "1.1.1.3",
                                        "maskLen": 24
                                    },
                                    "secondaryIps": {
                                        "1.1.1.4": {
                                            "address": "1.1.1.4",
                                            "maskLen": 27
                                        },
                                        "1.1.1.5": {
                                            "address": "1.1.1.5",
                                            "maskLen": 27
                                        }
                                    },
                                    "secondaryIpsOrderedList": [
                                        {
                                            "address": "1.1.1.4",
                                            "maskLen": 27
                                        },
                                        {
                                            "address": "1.1.1.5",
                                            "maskLen": 27
                                        }
                                    ],
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
                        }
                    }
                }
            }
        ]))

        configuring_interface_vlan(t, "299", do="no ip address")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299"
        ])

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")

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
        t.readln("Vlan299 is up, line protocol is up (connected)")
        t.readln("  Hardware is Vlan, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Internet address is 1.1.1.2/24")
        t.readln("  Broadcast address is 255.255.255.255")
        t.readln("  IP MTU 1500 bytes")
        t.readln("  Up 00 minutes, 00 seconds")
        t.readln("Vlan777 is up, line protocol is up (connected)")
        t.readln("  Hardware is Vlan, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Internet address is 7.7.7.7/24")
        t.readln("  Broadcast address is 255.255.255.255")
        t.readln("  IP MTU 1500 bytes")
        t.readln("  Up 00 minutes, 00 seconds")
        t.read("my_arista#")

        result = api.enable("show interfaces")

        assert_that(result, is_([
            {
                "command": "show interfaces",
                "encoding": "json",
                "result": {
                    "sourceDetail": "",
                    "interfaces": {
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
        ]))

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")

        remove_interface_vlan(t, "777")
        remove_vlan(t, "777")

    @with_protocol
    @with_eapi
    def test_new_interface_vlan_has_no_internet_address(self, t, api):
        enable(t)

        create_vlan(t, "299")
        create_interface_vlan(t, "299")

        t.write("show interfaces")
        t.readln("Vlan299 is up, line protocol is up (connected)")
        t.readln("  Hardware is Vlan, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  IP MTU 1500 bytes")
        t.readln("  Up 00 minutes, 00 seconds")
        t.read("my_arista#")

        result = api.enable("show interfaces Vlan299")

        assert_that(result, is_([
            {
                "command": "show interfaces Vlan299",
                "encoding": "json",
                "result": {
                    "sourceDetail": "",
                    "interfaces": {
                        "Vlan299": {
                            "lastStatusChangeTimestamp": 0.0,
                            "name": "Vlan299",
                            "interfaceStatus": "connected",
                            "burnedInAddress": "00:00:00:00:00:00",
                            "mtu": 1500,
                            "hardware": "vlan",
                            "bandwidth": 0,
                            "forwardingModel": "routed",
                            "lineProtocolStatus": "up",
                            "interfaceAddress": [],
                            "physicalAddress": "00:00:00:00:00:00",
                            "description": ""
                        }
                    }
                }
            }
        ]))

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")

    @with_protocol
    @with_eapi
    def test_interface_vlan_with_removed_ip_has_an_empty_interface_address(self, t, api):
        enable(t)

        create_vlan(t, "299")
        create_interface_vlan(t, "299")
        configuring_interface_vlan(t, "299", do="ip address 1.1.1.2/24")
        configuring_interface_vlan(t, "299", do="no ip address")

        t.write("show interfaces")
        t.readln("Vlan299 is up, line protocol is up (connected)")
        t.readln("  Hardware is Vlan, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  No Internet protocol address assigned")
        t.readln("  IP MTU 1500 bytes")
        t.readln("  Up 00 minutes, 00 seconds")
        t.read("my_arista#")


        result = api.enable("show interfaces Vlan299")
        assert_that(result, is_([
            {
                "command": "show interfaces Vlan299",
                "encoding": "json",
                "result": {
                    "sourceDetail": "",
                    "interfaces": {
                        "Vlan299": {
                            "lastStatusChangeTimestamp": 0.0,
                            "name": "Vlan299",
                            "interfaceStatus": "connected",
                            "burnedInAddress": "00:00:00:00:00:00",
                            "mtu": 1500,
                            "hardware": "vlan",
                            "bandwidth": 0,
                            "forwardingModel": "routed",
                            "lineProtocolStatus": "up",
                            "interfaceAddress": [
                                {
                                    "secondaryIpsOrderedList": [],
                                    "broadcastAddress": "255.255.255.255",
                                    "virtualSecondaryIps": {},
                                    "dhcp": False,
                                    "secondaryIps": {},
                                    "primaryIp": {
                                        "maskLen": 0,
                                        "address": "0.0.0.0"
                                    },
                                    "virtualSecondaryIpsOrderedList": [],
                                    "virtualIp": {
                                        "maskLen": 0,
                                        "address": "0.0.0.0"
                                    }
                                }
                            ],
                            "physicalAddress": "00:00:00:00:00:00",
                            "description": ""
                        }
                    }
                }
            }
        ]))

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")


    @with_protocol
    def test_interface_vlan_name_parsing(self, t):
        enable(t)

        create_vlan(t, "299")

        t.write("conf t")
        t.read("my_arista(config)#")

        t.write("interface vlan")
        t.readln("% Incomplete command")
        t.read("my_arista(config)#")

        t.write("interface vlan -1")
        t.readln("% Invalid input")
        t.read("my_arista(config)#")

        t.write("interface vlan 4095")
        t.readln("% Invalid input")
        t.read("my_arista(config)#")

        t.write("interface vlan wat")
        t.readln("% Invalid input")
        t.read("my_arista(config)#")

        t.write("interface vlan 123")
        t.read("my_arista(config-if-Vl123)#")

        t.write("no interface vlan0123")
        t.read("my_arista(config)#")

        t.write("exit")
        t.read("my_arista#")

        remove_vlan(t, "299")

    @with_protocol
    def test_removing_ip_address_special_cases(self, t):
        enable(t)

        create_vlan(t, "299")

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface vlan 299")
        t.read("my_arista(config-if-Vl299)#")

        t.write("ip address 1.1.1.1/21")
        t.read("my_arista(config-if-Vl299)#")

        t.write("ip address 2.2.2.2/22 secondary")
        t.read("my_arista(config-if-Vl299)#")

        t.write("no ip address 2.2.2.2/22")
        t.readln("% Address 2.2.2.2/22 does not match primary address 1.1.1.1/21")
        t.read("my_arista(config-if-Vl299)#")

        t.write("no ip address 2.2.2.2 255.255.252.0")
        t.readln("% Address 2.2.2.2/22 does not match primary address 1.1.1.1/21")
        t.read("my_arista(config-if-Vl299)#")

        t.write("no ip address 1.1.1.1/21")
        t.readln("% Primary address cannot be deleted before secondary")
        t.read("my_arista(config-if-Vl299)#")

        t.write("no ip address 1.1.1.1/21 secondary")
        t.readln("! Address 1.1.1.1/21 was not found for deletion")
        t.read("my_arista(config-if-Vl299)#")

        t.write("no ip address 2.2.2.2/22 secondary")
        t.read("my_arista(config-if-Vl299)#")

        t.write("no ip address 1.1.1.1/21")
        t.read("my_arista(config-if-Vl299)#")

        t.write("no interface vlan 299")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")

        remove_vlan(t, "299")

    @with_protocol
    def test_overlapping_ips(self, t):
        enable(t)

        create_vlan(t, "1000")
        create_interface_vlan(t, "1000")
        create_vlan(t, "2000")
        create_interface_vlan(t, "2000")

        configuring_interface_vlan(t, "1000", do="ip address 2.2.2.2/24")
        configuring_interface_vlan(t, "1000", do="ip address 3.3.3.3/24 secondary")

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface vlan2000")
        t.read("my_arista(config-if-Vl2000)#")

        t.write("ip address 2.2.2.75/25")
        t.readln("% Subnet 2.2.2.0 overlaps with existing subnet 2.2.2.0 of interface Vlan1000")
        t.read("my_arista(config-if-Vl2000)#")

        t.write("exit")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")

        remove_interface_vlan(t, "2000")
        remove_vlan(t, "2000")
        remove_interface_vlan(t, "1000")
        remove_vlan(t, "1000")

    @with_protocol
    @with_eapi
    def test_show_unknown_interface(self, t, api):
        t.write("show interface vlan 99")
        t.readln("% Interface does not exist")
        t.read("my_arista>")

        with self.assertRaises(CommandError) as expectation:
            api.enable(["show interfaces vlan18"])

        assert_that(str(expectation.exception), is_("Error [1002]: CLI command 2 of 2 'show interfaces vlan18' failed: "
                                                    "invalid command [Interface does not exist]"))

    @with_protocol
    def test_remove_unknown_interface_vlan_doesnt_care(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("my_arista(config)#")

        t.write("no interface vlan 123")
        t.read("my_arista(config)#")


def assert_interface_configuration(t, interface, config):
    t.write("show running-config interfaces {}".format(interface))
    for line in config:
        t.readln(line)
    t.read("my_arista#")
