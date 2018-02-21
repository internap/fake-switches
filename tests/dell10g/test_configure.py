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

from tests.dell10g import enable
from tests.util.protocol_util import with_protocol, ProtocolTest, SshTester, TelnetTester


class Dell10GConfigureTest(ProtocolTest):
    __test__ = False

    tester_class = SshTester
    test_switch = "dell10g"

    @with_protocol
    def test_entering_configure_unknown_interface_mode(self, t):
        enable(t)
        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("interface tengigabitethernet 1/0/99")
        t.readln("")
        t.readln("An invalid interface has been used for this function")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_entering_configure_unknown_vlan(self, t):
        enable(t)
        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("vlan 5000")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 1")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN 5000      ERROR: VLAN ID is out of range")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_entering_remove_unknown_vlan(self, t):
        enable(t)
        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("no vlan 3999")
        t.readln("")
        t.readln("These VLANs do not exist:  3999.")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")


class Dell10GConfigureSshTest(Dell10GConfigureTest):
    __test__ = True
    tester_class = SshTester


class Dell10GConfigureTelnetTest(Dell10GConfigureTest):
    __test__ = True
    tester_class = TelnetTester
