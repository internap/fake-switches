# Copyright 2015-2016 Internap.
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

from tests.arista import enable, remove_vlan, create_vlan
from tests.util.protocol_util import with_protocol, ProtocolTest, SshTester


class TestAristaSwitchProtocol(ProtocolTest):
    __test__ = False
    test_switch = "arista"

    @with_protocol
    def test_enable(self, t):
        t.write("enable")
        t.read("my_arista#")

    @with_protocol
    def test_exiting_loses_the_connection(self, t):
        t.write("enable")
        t.read("my_arista#")
        t.write("exit")
        t.read_eof()

    @with_protocol
    def test_no_such_command_return_to_prompt(self, t):
        enable(t)

        t.write("shizzle")
        t.readln("% Invalid input")
        t.read("my_arista#")

    @with_protocol
    def test_command_show_vlan_empty(self, t):
        enable(t)

        t.write("terminal length 0")
        t.read("Pagination disabled.")
        t.read("my_arista#")
        t.write("show vlan 123")
        t.readln("% VLAN 123 not found in current VLAN database")
        t.read("my_arista#")

    @with_protocol
    def test_command_add_vlan(self, t):
        enable(t)

        t.write("conf t")
        t.read("my_arista(config)#")
        t.write("vlan 123")
        t.read("my_arista(config-vlan-123)#")
        t.write("name shizzle")
        t.read("my_arista(config-vlan-123)#")
        t.write("exit")
        t.read("my_arista(config)#")
        t.write("exit")
        t.read("my_arista#")
        t.write("show vlan 123")
        t.readln("VLAN  Name                             Status    Ports")
        t.readln("----- -------------------------------- --------- -------------------------------")
        t.readln("123   shizzle                          active")
        t.readln("")
        t.read("my_arista#")

        remove_vlan(t, "123")

        t.write("show vlan 123")
        t.readln("% VLAN 123 not found in current VLAN database")
        t.read("my_arista#")

    @with_protocol
    def test_command_add_vlan_errors(self, t):
        enable(t)

        t.write("conf t")
        t.read("my_arista(config)#")

        t.write("vlan shizzle")
        t.readln("% Invalid input")
        t.read("my_arista(config)#")

        t.write("vlan -1")
        t.readln("% Invalid input")
        t.read("my_arista(config)#")

        t.write("vlan 0")
        t.readln("% Incomplete command")
        t.read("my_arista(config)#")

        t.write("vlan 4095")
        t.readln("% Invalid input")
        t.read("my_arista(config)#")

        t.write("exit")
        t.read("my_arista#")

    @with_protocol
    def test_show_vlan(self, t):
        enable(t)
        create_vlan(t, "123")
        create_vlan(t, "3333", "some-name")
        create_vlan(t, "2222", "your-name-is-way-too-long-for-this-pretty-printed-interface-man")

        t.write("show vlan")
        t.readln("VLAN  Name                             Status    Ports")
        t.readln("----- -------------------------------- --------- -------------------------------")
        t.readln("1     default                          active")
        t.readln("123   VLAN0123                         active")
        t.readln("2222  your-name-is-way-too-long-for-th active")
        t.readln("3333  some-name                        active")
        t.readln("")
        t.read("my_arista#")

        remove_vlan(t, "123")
        remove_vlan(t, "2222")
        remove_vlan(t, "3333")

    @with_protocol
    def test_show_vlan_without_enable(self, t):
        t.write("show vlan")
        t.readln("VLAN  Name                             Status    Ports")
        t.readln("----- -------------------------------- --------- -------------------------------")
        t.readln("1     default                          active")
        t.readln("")
        t.read("my_arista>")


class TestAristaSwitchProtocolSSH(TestAristaSwitchProtocol):
    __test__ = True
    tester_class = SshTester
