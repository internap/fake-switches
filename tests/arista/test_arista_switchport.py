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

from tests.arista import enable, assert_interface_configuration, configuring_interface, with_eapi, create_vlan, \
    remove_vlan, create_interface_vlan, remove_interface_vlan
from tests.util.protocol_util import ProtocolTest, SshTester, with_protocol


class TestAristaInterfaceVlans(ProtocolTest):
    tester_class = SshTester
    test_switch = "arista"

    @with_protocol
    def test_configure_trunk_port(self, t):
        enable(t)

        configuring_interface(t, "Et1", do="switchport mode TrunK")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport mode trunk"])

        # not really added because all vlan are in trunk by default on arista
        configuring_interface(t, "Et1", do="switchport trunk allowed vlan add 123")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport mode trunk"])

        configuring_interface(t, "Et1", do="switchport trunk allowed vlan none")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport trunk allowed vlan none",
            "   switchport mode trunk"])

        configuring_interface(t, "Et1", do="switchport trunk allowed vlan add 123")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport trunk allowed vlan 123",
            "   switchport mode trunk"])

        configuring_interface(t, "Et1", do="switchport trunk allowed vlan add 124,126-128")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport trunk allowed vlan 123-124,126-128",
            "   switchport mode trunk"])

        configuring_interface(t, "Et1", do="switchport trunk allowed vlan remove 123-124,127")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport trunk allowed vlan 126,128",
            "   switchport mode trunk"])

        configuring_interface(t, "Et1", do="switchport trunk allowed vlan all")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport mode trunk"])

        configuring_interface(t, "Et1", do="switchport trunk allowed vlan 123-124,127")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport trunk allowed vlan 123-124,127",
            "   switchport mode trunk"])

        configuring_interface(t, "Et1", do="no switchport trunk allowed vlan")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport mode trunk"])

        configuring_interface(t, "Et1", do="no switchport mode")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1"])

    @with_protocol
    def test_configure_trunk_port_by_removing_one_vlan_shows_all_others(self, t):
        enable(t)

        configuring_interface(t, "Et1", do="switchport trunk allowed vlan remove 100")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1",
            "   switchport trunk allowed vlan 1-99,101-4094"
        ])

        configuring_interface(t, "Et1", do="no switchport trunk allowed vlan")

        assert_interface_configuration(t, "Ethernet1", [
            "interface Ethernet1"])

    @with_protocol
    def test_switchport_trunk_mode_errors(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface Ethernet 1")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport mode")
        t.readln("% Incomplete command")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport mode trunk trunk")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport mode waatt")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("no switchport mode whatever this is ignored past mode")
        t.read("my_arista(config-if-Et1)#")

        t.write("exit")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")

    @with_protocol
    def test_switchport_trunk_allowed_vlan_add_errors(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface Ethernet 1")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan add")
        t.readln("% Incomplete command")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan add 1 2")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan add patate")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("no switchport trunk allowed vlan whatever this is ignored past mode")
        t.read("my_arista(config-if-Et1)#")

        t.write("exit")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")

    @with_protocol
    def test_switchport_trunk_allowed_vlan_remove_errors(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface Ethernet 1")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan add")
        t.readln("% Incomplete command")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan add 1 2")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan add patate")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("exit")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")

    @with_protocol
    def test_switchport_trunk_allowed_vlan_none_errors(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface Ethernet 1")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan none patate")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("exit")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")

    @with_protocol
    def test_switchport_trunk_allowed_vlan_errors(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface Ethernet 1")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan")
        t.readln("% Incomplete command")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan 1 2")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("switchport trunk allowed vlan patate")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Et1)#")

        t.write("exit")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")

    @with_protocol
    @with_eapi
    def test_show_interfaces_switchport_doesnt_show_vlan_interfaces(self, t, api):
        enable(t)

        create_vlan(t, "299")
        create_interface_vlan(t, "299")

        t.write("show interfaces switchport")
        t.readln("Default switchport mode: access")
        t.readln("")
        t.readln("Name: Et1")
        t.readln("Switchport: Enabled")
        t.readln("Administrative Mode: static access")
        t.readln("Operational Mode: static access")
        t.readln("MAC Address Learning: enabled")
        t.readln("Dot1q ethertype/TPID: 0x8100 (active)")
        t.readln("Dot1q Vlan Tag Required (Administrative/Operational): No/No")
        t.readln("Access Mode VLAN: 1 (default)")
        t.readln("Trunking Native Mode VLAN: 1 (default)")
        t.readln("Administrative Native VLAN tagging: disabled")
        t.readln("Trunking VLANs Enabled: ALL")
        t.readln("Static Trunk Groups:")
        t.readln("Dynamic Trunk Groups:")
        t.readln("Source interface filtering: enabled")
        t.readln("")
        t.readln("Name: Et2")
        t.readln("Switchport: Enabled")
        t.readln("Administrative Mode: static access")
        t.readln("Operational Mode: static access")
        t.readln("MAC Address Learning: enabled")
        t.readln("Dot1q ethertype/TPID: 0x8100 (active)")
        t.readln("Dot1q Vlan Tag Required (Administrative/Operational): No/No")
        t.readln("Access Mode VLAN: 1 (default)")
        t.readln("Trunking Native Mode VLAN: 1 (default)")
        t.readln("Administrative Native VLAN tagging: disabled")
        t.readln("Trunking VLANs Enabled: ALL")
        t.readln("Static Trunk Groups:")
        t.readln("Dynamic Trunk Groups:")
        t.readln("Source interface filtering: enabled")
        t.readln("")
        t.read("my_arista#")

        result = api.enable(["show interfaces switchport"], strict=True)

        expected_json_content = {
            "sourceDetail": "",
            "switchports": {
                "Ethernet1": {
                    "enabled": True,
                    "switchportInfo": {
                        "accessVlanId": 1,
                        "accessVlanName": "default",
                        "dot1qVlanTagRequired": False,
                        "dot1qVlanTagRequiredStatus": False,
                        "dynamicAllowedVlans": {},
                        "dynamicTrunkGroups": [],
                        "macLearning": True,
                        "mode": "access",
                        "sourceportFilterMode": "enabled",
                        "staticTrunkGroups": [],
                        "tpid": "0x8100",
                        "tpidStatus": True,
                        "trunkAllowedVlans": "ALL",
                        "trunkingNativeVlanId": 1,
                        "trunkingNativeVlanName": "default"
                    }
                },
                "Ethernet2": {
                    "enabled": True,
                    "switchportInfo": {
                        "accessVlanId": 1,
                        "accessVlanName": "default",
                        "dot1qVlanTagRequired": False,
                        "dot1qVlanTagRequiredStatus": False,
                        "dynamicAllowedVlans": {},
                        "dynamicTrunkGroups": [],
                        "macLearning": True,
                        "mode": "access",
                        "sourceportFilterMode": "enabled",
                        "staticTrunkGroups": [],
                        "tpid": "0x8100",
                        "tpidStatus": True,
                        "trunkAllowedVlans": "ALL",
                        "trunkingNativeVlanId": 1,
                        "trunkingNativeVlanName": "default"
                    }
                }
            }
        }

        assert_that(result, is_([
            {
                "command": "show interfaces switchport",
                "encoding": "json",
                "response": expected_json_content,
                "result": expected_json_content
            }
        ]))

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")

    @with_protocol
    def test_show_interfaces_switchport_trunk_vlans(self, t):
        enable(t)

        create_vlan(t, "13")
        create_vlan(t, "14")

        configuring_interface(t, "Et1", do="switchport mode trunk")
        configuring_interface(t, "Et1", do="switchport trunk allowed vlan 13-14")

        t.write("show interfaces et1 switchport")
        t.readln("Name: Et1")
        t.readln("Switchport: Enabled")
        t.readln("Administrative Mode: trunk")
        t.readln("Operational Mode: trunk")
        t.readln("MAC Address Learning: enabled")
        t.readln("Dot1q ethertype/TPID: 0x8100 (active)")
        t.readln("Dot1q Vlan Tag Required (Administrative/Operational): No/No")
        t.readln("Access Mode VLAN: 1 (default)")
        t.readln("Trunking Native Mode VLAN: 1 (default)")
        t.readln("Administrative Native VLAN tagging: disabled")
        t.readln("Trunking VLANs Enabled: 13-14")
        t.readln("Static Trunk Groups:")
        t.readln("Dynamic Trunk Groups:")
        t.readln("Source interface filtering: enabled")
        t.readln("")
        t.read("my_arista#")

        configuring_interface(t, "Et1", do="switchport trunk allowed vlan none")

        t.write("show interfaces ethernet 1 switchport")
        t.readln("Name: Et1")
        t.readln("Switchport: Enabled")
        t.readln("Administrative Mode: trunk")
        t.readln("Operational Mode: trunk")
        t.readln("MAC Address Learning: enabled")
        t.readln("Dot1q ethertype/TPID: 0x8100 (active)")
        t.readln("Dot1q Vlan Tag Required (Administrative/Operational): No/No")
        t.readln("Access Mode VLAN: 1 (default)")
        t.readln("Trunking Native Mode VLAN: 1 (default)")
        t.readln("Administrative Native VLAN tagging: disabled")
        t.readln("Trunking VLANs Enabled: NONE")
        t.readln("Static Trunk Groups:")
        t.readln("Dynamic Trunk Groups:")
        t.readln("Source interface filtering: enabled")
        t.readln("")
        t.read("my_arista#")

        remove_vlan(t, "13")
        remove_vlan(t, "14")

    @with_protocol
    def test_show_interfaces_switchport_errors(self, t):
        t.write("show interfaces patate switchport")
        t.readln("% Incomplete command")
        t.read("my_arista>")

        t.write("show interfaces ethernet 1 2 switchport")
        t.readln("% Invalid input")
        t.read("my_arista>")

        t.write("show interfaces et3 switchport")
        t.readln("% Invalid input")
        t.read("my_arista>")
