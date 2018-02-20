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


class Cisco6500UnicastTest(ProtocolTest):
    __test__ = False

    tester_class = SshTester
    test_switch = "cisco6500"

    @with_protocol
    def test_set_unicast(self, t):
        enable(t)

        create_interface_vlan(t, "2999")
        configuring_interface_vlan(t, "2999", do="ip verify unicast source reachable-via rx")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " no ip address",
            " ip verify unicast source reachable-via rx",
            "end"])

        configuring_interface_vlan(t, "2999", do="no ip verify unicast")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " no ip address",
            "end"])

        configuring(t, do="no interface vlan 2999")


class Cisco6500UnicastProtocolSSHTest(Cisco6500UnicastTest):
    __test__ = True
    tester_class = SshTester


class Cisco6500UnicastProtocolTelnetTest(Cisco6500UnicastTest):
    __test__ = True
    tester_class = TelnetTester
