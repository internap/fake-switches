# Copyright 2015 Internap.
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

from tests.dell10g import enable, configuring_vlan, \
    assert_running_config_contains_in_order, add_vlan, configuring
from tests.util.protocol_util import with_protocol, ProtocolTest, SshTester, TelnetTester


class Dell10GConfigureVlanTest(ProtocolTest):
    __test__ = False

    tester_class = SshTester
    test_switch = "dell10g"

    @with_protocol
    def test_configuring_a_vlan(self, t):
        enable(t)

        add_vlan(t, 1000)
        add_vlan(t, 1001)
        add_vlan(t, 2000)
        configuring_vlan(t, 2000, do="name shizzle")
        assert_running_config_contains_in_order(t, [
            "vlan 2000",
            "name shizzle",
            "exit",
            "vlan 1,1000-1001",
            "exit",
        ])

        configuring(t, do="no vlan 1000")
        configuring(t, do="no vlan 1001")
        configuring(t, do="no vlan 2000")


class Dell10GConfigureVlanSshTest(Dell10GConfigureVlanTest):
    __test__ = True
    tester_class = SshTester


class Dell10GConfigureVlanTelnetTest(Dell10GConfigureVlanTest):
    __test__ = True
    tester_class = TelnetTester
