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

from tests.arista import enable, remove_vlan, create_vlan, create_interface_vlan, configuring_interface_vlan, \
    remove_interface_vlan, assert_interface_configuration
from tests.util.protocol_util import ProtocolTest, SshTester, with_protocol


class TestAristaVarp(ProtocolTest):
    tester_class = SshTester
    test_switch = "arista"

    @with_protocol
    def test_ip_virtual_router(self, t):
        enable(t)

        create_vlan(t, "299")
        create_interface_vlan(t, "299")
        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299"
        ])

        configuring_interface_vlan(t, "299", do="ip virtual-router address 1.1.1.1")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip virtual-router address 1.1.1.1"
        ])

        configuring_interface_vlan(t, "299", do="ip virtual-router address 2.2.2.2")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip virtual-router address 1.1.1.1",
            "   ip virtual-router address 2.2.2.2"
        ])

        configuring_interface_vlan(t, "299", do="ip virtual-router address 1.1.1.1")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip virtual-router address 1.1.1.1",
            "   ip virtual-router address 2.2.2.2"
        ])

        configuring_interface_vlan(t, "299", do="ip virtual-router address 1.1.1.1/27")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip virtual-router address 1.1.1.1/27",
            "   ip virtual-router address 2.2.2.2"
        ])

        configuring_interface_vlan(t, "299", do="ip virtual-router address 2.2.2.2/32")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip virtual-router address 1.1.1.1/27",
            "   ip virtual-router address 2.2.2.2"
        ])

        configuring_interface_vlan(t, "299", do="no ip virtual-router address 2.2.2.2")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip virtual-router address 1.1.1.1/27"
        ])

        configuring_interface_vlan(t, "299", do="no ip virtual-router address")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299"
        ])

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")

    @with_protocol
    def test_ip_virtual_router_errors(self, t):
        enable(t)

        create_vlan(t, "2000")

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface vlan2000")
        t.read("my_arista(config-if-Vl2000)#")

        t.write("ip virtual-router address")
        t.readln("% Incomplete command")
        t.read("my_arista(config-if-Vl2000)#")

        t.write("ip virtual-router address patate")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Vl2000)#")

        t.write("ip virtual-router address 1.1.1.1 patate")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Vl2000)#")

        t.write("ip virtual-router address 1.1.1.256")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Vl2000)#")

        t.write("exit")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")
