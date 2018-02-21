# Copyright 2017 Internap.
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

from tests.cisco import enable, create_interface_vlan, configuring, configuring_interface_vlan, \
    assert_interface_configuration
from tests.util.protocol_util import SshTester, TelnetTester, with_protocol, ProtocolTest


class CiscoUnicastTest(ProtocolTest):
    __test__ = False
    test_switch = "cisco"

    @with_protocol
    def test_set_unicast_raise_error(self, t):
        enable(t)

        create_interface_vlan(t, "2999")

        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("interface vlan 2999")
        t.read("my_switch(config-if)#")

        t.write("ip verify unicast source reachable-via rx")
        t.readln("% ip verify configuration not supported on interface Vl2999")
        t.readln(" - verification not supported by hardware")
        t.readln("% ip verify configuration not supported on interface Vl2999")
        t.readln(" - verification not supported by hardware")
        t.readln("%Restoring the original configuration failed on Vlan2999 - Interface Support Failure")

        t.read("my_switch(config-if)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " no ip address",
            "end"])

        configuring(t, do="no interface vlan 2999")

    @with_protocol
    def test_set_unicast(self, t):
        enable(t)

        create_interface_vlan(t, "2999")
        configuring_interface_vlan(t, "2999", "no ip verify unicast source reachable-via rx")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " no ip address",
            "end"])

        configuring(t, do="no interface vlan 2999")


class CiscoUnicastProtocolSSHTest(CiscoUnicastTest):
    __test__ = True
    tester_class = SshTester


class CiscoUnicastProtocolTelnetTest(CiscoUnicastTest):
    __test__ = True
    tester_class = TelnetTester
