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
from hamcrest import assert_that, is_

from tests.arista import enable, create_vlan, create_interface_vlan, configuring_interface, configuring_interface_vlan, \
    with_eapi, remove_vlan, remove_interface_vlan
from tests.util.protocol_util import with_protocol, ProtocolTest, SshTester


class TestAristaRunningConfig(ProtocolTest):
    tester_class = SshTester
    test_switch = "arista"

    @with_protocol
    def test_running_config_all(self, t):
        enable(t)

        t.write("show running-config all")
        t.readln("! Command: show running-config all")
        t.readln("! device: my_arista (vEOS, EOS-4.20.8M)")
        t.readln("!")
        t.readln("! boot system flash:/vEOS-lab.swi")
        t.readln("!")
        t.readln("vlan 1")
        t.readln("   name default")
        t.readln("   mac address learning")
        t.readln("   state active")
        t.readln("!")
        t.readln("end")
        t.read("my_arista#")

    @with_protocol
    def test_running_config_unknown_interface(self, t):
        enable(t)

        t.write("show running-config interface vlan 999")
        t.read("my_arista#")

    @with_protocol
    @with_eapi
    def test_running_config_multiple_interfaces(self, t, api):
        enable(t)

        create_vlan(t, "1000")
        create_interface_vlan(t, "1000")

        create_vlan(t, "2000")
        create_interface_vlan(t, "2000")

        configuring_interface_vlan(t, "1000", do="ip address 1.1.1.1/27")
        configuring_interface_vlan(t, "2000", do="ip address 2.2.2.2/27")
        configuring_interface(t, "Et1", do="switchport trunk allowed vlan 123-124,127")
        configuring_interface(t, "Et3", do="switchport mode trunk")

        t.write("show running-config interfaces Et3 vla 2000 ETHERNET 1 vlan 1000")
        t.readln("interface Ethernet1")
        t.readln("   switchport trunk allowed vlan 123-124,127")
        t.readln("interface Ethernet3")
        t.readln("   switchport mode trunk")
        t.readln("interface Vlan1000")
        t.readln("   ip address 1.1.1.1/27")
        t.readln("interface Vlan2000")
        t.readln("   ip address 2.2.2.2/27")
        t.read("my_arista#")

        result = api.get_config(params="interfaces Vlan1000 Ethernet3 Ethernet1 Vlan2000")

        assert_that(result, is_([
            "interface Ethernet1",
            "   switchport trunk allowed vlan 123-124,127",
            "interface Ethernet3",
            "   switchport mode trunk",
            "interface Vlan1000",
            "   ip address 1.1.1.1/27",
            "interface Vlan2000",
            "   ip address 2.2.2.2/27",
            ""
        ]))

        configuring_interface(t, "Et1", do="no switchport trunk allowed vlan")
        configuring_interface(t, "Et3", do="no switchport mode")

        remove_interface_vlan(t, "1000")
        remove_vlan(t, "1000")

        remove_interface_vlan(t, "2000")
        remove_vlan(t, "2000")
