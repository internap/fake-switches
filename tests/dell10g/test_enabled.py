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

from tests.dell10g import enable, assert_running_config_contains_in_order, \
    configuring_vlan, configuring, add_vlan, configuring_interface
from tests.util.protocol_util import with_protocol, SshTester, ProtocolTest, TelnetTester


class Dell10GEnabledTest(ProtocolTest):
    __test__ = False

    tester_class = SshTester
    test_switch = "dell10g"

    @with_protocol
    def test_terminal_length_0(self, t):
        enable(t)
        t.write("terminal length 0")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_exit_returns_to_unprivileged_mode(self, t):
        enable(t)
        t.write("exit")
        t.readln("")
        t.read("my_switch>")

    @with_protocol
    def test_quit_disconnects(self, t):
        enable(t)
        t.write("quit")
        t.read_eof()

    @with_protocol
    def test_write_memory(self, t):
        enable(t)

        t.write("copy running-config startup-config")

        t.readln("")
        t.readln("This operation may take a few minutes.")
        t.readln("Management interfaces will not be available during this time.")
        t.readln("")
        t.read("Are you sure you want to save? (y/n) ")
        t.write_raw("y")
        t.readln("")
        t.readln("")
        t.readln("Configuration Saved!")
        t.read("my_switch#")

    @with_protocol
    def test_write_memory_abort(self, t):
        enable(t)

        t.write("copy running-config startup-config")

        t.readln("")
        t.readln("This operation may take a few minutes.")
        t.readln("Management interfaces will not be available during this time.")
        t.readln("")
        t.read("Are you sure you want to save? (y/n) ")
        t.write_raw("n")
        t.readln("")
        t.readln("")
        t.readln("Configuration Not Saved!")
        t.read("my_switch#")

    @with_protocol
    def test_write_memory_any_other_key_aborts(self, t):
        enable(t)

        t.write("copy running-config startup-config")

        t.readln("")
        t.readln("This operation may take a few minutes.")
        t.readln("Management interfaces will not be available during this time.")
        t.readln("")
        t.read("Are you sure you want to save? (y/n) ")
        t.write_raw("p")
        t.readln("")
        t.readln("")
        t.readln("Configuration Not Saved!")
        t.read("my_switch#")

    @with_protocol
    def test_invalid_command(self, t):
        enable(t)

        t.write("shizzle")
        t.readln("          ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")

    @with_protocol
    def test_show_running_config_on_empty_ethernet_port(self, t):
        enable(t)

        t.write("show running-config interface tengigabitethernet 0/0/1")
        t.readln("")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_show_running_config_on_ethernet_port_that_does_not_exists(self, t):
        enable(t)

        t.write("show running-config interface tengigabitethernet 99/99/99")
        t.readln("")
        t.read("An invalid interface has been used for this function")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_show_running_config_displays_header(self, t):
        enable(t)
        assert_running_config_contains_in_order(t, [
            '!Current Configuration:',
            '!System Description "............."',
            '!System Software Version 3.3.7.3',
            '!Cut-through mode is configured as disabled',
            '!',
            'configure',
        ])

    @with_protocol
    def test_show_vlan(self, t):
        enable(t)

        add_vlan(t, 10)
        add_vlan(t, 11)
        add_vlan(t, 12)
        configuring_vlan(t, 17, do="name this-name-is-too-long-buddy-budd")
        add_vlan(t, 100)
        add_vlan(t, 1000)

        t.write("show vlan")
        t.readln("")
        t.readln("VLAN   Name                             Ports          Type")
        t.readln("-----  ---------------                  -------------  --------------")
        t.readln("1      default                                         Default")
        t.readln("10     VLAN10                                          Static")
        t.readln("11     VLAN11                                          Static")
        t.readln("12     VLAN12                                          Static")
        t.readln("17     this-name-is-too-long-buddy-budd                Static")
        t.readln("100    VLAN100                                         Static")
        t.readln("1000   VLAN1000                                        Static")
        t.readln("")
        t.read("my_switch#")

        configuring(t, do="no vlan 10")
        configuring(t, do="no vlan 11")
        configuring(t, do="no vlan 12")
        configuring(t, do="no vlan 17")
        configuring(t, do="no vlan 100")
        configuring(t, do="no vlan 1000")


    @with_protocol
    def test_show_vlan_with_port(self, t):
        enable(t)

        add_vlan(t, 10)

        configuring_interface(t, "tengigabitethernet 0/0/1", "switchport mode trunk")
        configuring_interface(t, "tengigabitethernet 0/0/1", "switchport trunk allowed vlan 10")

        t.write("show vlan")
        t.readln("")
        t.readln("VLAN   Name                             Ports          Type")
        t.readln("-----  ---------------                  -------------  --------------")
        t.readln("1      default                                         Default")
        t.readln("10     VLAN10                           Te0/0/1        Static")
        t.readln("")
        t.read("my_switch#")

        configuring_interface(t, "tengigabitethernet 0/0/1", "switchport trunk allowed vlan remove 10")
        configuring_interface(t, "tengigabitethernet 0/0/1", "no switchport mode")
        configuring(t, do="no vlan 10")

    @with_protocol
    def test_show_vlan_with_ports(self, t):
        enable(t)

        add_vlan(t, 10)
        add_vlan(t, 11)

        configuring_interface(t, "tengigabitethernet 0/0/1", "switchport mode trunk")
        configuring_interface(t, "tengigabitethernet 0/0/2", "switchport mode trunk")
        configuring_interface(t, "tengigabitethernet 1/0/2", "switchport mode trunk")

        configuring_interface(t, "tengigabitethernet 0/0/1", "switchport trunk allowed vlan 10-11")
        configuring_interface(t, "tengigabitethernet 0/0/2", "switchport trunk allowed vlan 10")
        configuring_interface(t, "tengigabitethernet 1/0/2", "switchport trunk allowed vlan 11")

        t.write("show vlan")
        t.readln("")
        t.readln("VLAN   Name                             Ports          Type")
        t.readln("-----  ---------------                  -------------  --------------")
        t.readln("1      default                                         Default")
        t.readln("10     VLAN10                           Te0/0/1-2      Static")
        t.readln("11     VLAN11                           Te0/0/1,       Static")
        t.readln("                                        Te1/0/2        ")
        t.readln("")
        t.read("my_switch#")

        configuring_interface(t, "tengigabitethernet 0/0/1", "no switchport mode")
        configuring_interface(t, "tengigabitethernet 0/0/2", "no switchport mode")
        configuring_interface(t, "tengigabitethernet 1/0/2", "no switchport mode")

        configuring_interface(t, "tengigabitethernet 0/0/1", "switchport trunk allowed vlan remove 10,11")
        configuring_interface(t, "tengigabitethernet 0/0/2", "switchport trunk allowed vlan remove 10")
        configuring_interface(t, "tengigabitethernet 1/0/2", "switchport trunk allowed vlan remove 11")

        configuring(t, do="no vlan 10")
        configuring(t, do="no vlan 11")

    @with_protocol
    def test_show_vlan_id(self, t):
        enable(t)

        add_vlan(t, 1000)

        t.write("show vlan id 500")
        t.readln("")
        t.readln("ERROR: This VLAN does not exist.")
        t.readln("")
        t.read("my_switch#")

        t.write("show vlan id 1000")
        t.readln("")
        t.readln("VLAN   Name                             Ports          Type")
        t.readln("-----  ---------------                  -------------  --------------")
        t.readln("1000   VLAN1000                                        Static")
        t.readln("")
        t.read("my_switch#")

        t.write("show vlan id bleh")
        t.readln("                     ^")
        t.readln("Invalid input. Please specify an integer in the range 1 to 4093.")
        t.readln("")
        t.read("my_switch#")

        t.write("show vlan id")
        t.readln("")
        t.readln("Command not found / Incomplete command. Use ? to list commands.")
        t.readln("")
        t.read("my_switch#")

        configuring(t, do="no vlan 1000")


class Dell10GEnabledSshTest(Dell10GEnabledTest):
    __test__ = True
    tester_class = SshTester


class Dell10GEnabledTelnetTest(Dell10GEnabledTest):
    __test__ = True
    tester_class = TelnetTester
