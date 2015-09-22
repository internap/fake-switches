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

import unittest

from flexmock import flexmock_teardown

from tests.dell import enable, assert_running_config_contains_in_order, \
    configuring_vlan, configuring_interface_vlan, unconfigure_vlan, \
    ssh_protocol_factory, telnet_protocol_factory
from tests.util.protocol_util import with_protocol


class DellEnabledTest(unittest.TestCase):
    __test__ = False
    protocol_factory = None

    def setUp(self):
        self.protocol = self.protocol_factory()

    def tearDown(self):
        flexmock_teardown()

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
    def test_entering_configure_mode(self, t):
        enable(t)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_show_running_config_on_empty_ethernet_port(self, t):
        enable(t)

        t.write("show running-config interface ethernet 1/g1")
        t.readln("")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_show_running_config_on_ethernet_port_that_does_not_exists(self, t):
        enable(t)

        t.write("show running-config interface ethernet 4/g8")
        t.readln("")
        t.read("ERROR: Invalid input!")
        t.readln("")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_show_running_config_displays_header(self, t):
        enable(t)
        assert_running_config_contains_in_order(t, [
            '!Current Configuration:',
            '!System Description "PowerConnect 6224P, 3.3.7.3, VxWorks 6.5"',
            '!System Software Version 3.3.7.3',
            '!Cut-through mode is configured as disabled',
            '!',
            'configure',
        ])

    @with_protocol
    def test_show_vlan(self, t):
        enable(t)

        configuring_vlan(t, 10)
        configuring_vlan(t, 11)
        configuring_vlan(t, 12)
        configuring_vlan(t, 13)
        configuring_vlan(t, 14)
        configuring_vlan(t, 15)
        configuring_vlan(t, 16)
        configuring_vlan(t, 17)
        configuring_interface_vlan(t, 17, do="name this-name-is-too-long-buddy-budd")
        configuring_vlan(t, 18)
        configuring_vlan(t, 19)
        configuring_vlan(t, 20)
        configuring_vlan(t, 21)
        configuring_vlan(t, 22)
        configuring_vlan(t, 23)
        configuring_vlan(t, 24)
        configuring_vlan(t, 25)
        configuring_vlan(t, 26)
        configuring_vlan(t, 27)
        configuring_vlan(t, 28)
        configuring_vlan(t, 29)
        configuring_vlan(t, 300)
        configuring_vlan(t, 4000)
        configuring_interface_vlan(t, 300, do="name shizzle")

        t.write("show vlan")
        t.readln("")
        t.readln("VLAN       Name                         Ports          Type      Authorization")
        t.readln("-----  ---------------                  -------------  -----     -------------")
        t.readln("1      Default                                         Default   Required     ")
        t.readln("10                                                     Static    Required     ")
        t.readln("11                                                     Static    Required     ")
        t.readln("12                                                     Static    Required     ")
        t.readln("13                                                     Static    Required     ")
        t.readln("14                                                     Static    Required     ")
        t.readln("15                                                     Static    Required     ")
        t.readln("16                                                     Static    Required     ")
        t.readln("17     this-name-is-too-long-buddy-budd                Static    Required     ")
        t.readln("18                                                     Static    Required     ")
        t.readln("19                                                     Static    Required     ")
        t.readln("20                                                     Static    Required     ")
        t.readln("21                                                     Static    Required     ")
        t.readln("22                                                     Static    Required     ")
        t.readln("23                                                     Static    Required     ")
        t.readln("24                                                     Static    Required     ")
        t.readln("25                                                     Static    Required     ")
        t.readln("26                                                     Static    Required     ")
        t.readln("")
        t.read("--More-- or (q)uit")
        t.write_raw("m")
        t.readln("\r                     ")
        t.readln("")
        t.readln("")
        t.readln("VLAN       Name                         Ports          Type      Authorization")
        t.readln("-----  ---------------                  -------------  -----     -------------")
        t.readln("27                                                     Static    Required     ")
        t.readln("28                                                     Static    Required     ")
        t.readln("29                                                     Static    Required     ")
        t.readln("300    shizzle                                         Static    Required     ")
        t.readln("4000                                                   Static    Required     ")
        t.readln("")
        t.read("my_switch#")

        unconfigure_vlan(t, 10)
        unconfigure_vlan(t, 11)
        unconfigure_vlan(t, 12)
        unconfigure_vlan(t, 13)
        unconfigure_vlan(t, 14)
        unconfigure_vlan(t, 15)
        unconfigure_vlan(t, 16)
        unconfigure_vlan(t, 17)
        unconfigure_vlan(t, 18)
        unconfigure_vlan(t, 19)
        unconfigure_vlan(t, 20)
        unconfigure_vlan(t, 21)
        unconfigure_vlan(t, 22)
        unconfigure_vlan(t, 23)
        unconfigure_vlan(t, 24)
        unconfigure_vlan(t, 25)
        unconfigure_vlan(t, 26)
        unconfigure_vlan(t, 27)
        unconfigure_vlan(t, 28)
        unconfigure_vlan(t, 29)
        unconfigure_vlan(t, 300)
        unconfigure_vlan(t, 4000)


class DellEnabledSshTest(DellEnabledTest):
    __test__ = True
    protocol_factory = ssh_protocol_factory


class DellEnabledTelnetTest(DellEnabledTest):
    __test__ = True
    protocol_factory = telnet_protocol_factory
