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

from tests.dell import enable, configuring_vlan, \
    assert_running_config_contains_in_order, unconfigure_vlan, \
    assert_interface_configuration, ssh_protocol_factory,\
    telnet_protocol_factory
from tests.util.protocol_util import with_protocol


class DellConfigureVlanTest(unittest.TestCase):
    __test__ = False
    protocol_factory = None

    def setUp(self):
        self.protocol = self.protocol_factory()

    def tearDown(self):
        flexmock_teardown()

    @with_protocol
    def test_configuring_a_vlan(self, t):
        enable(t)

        configuring_vlan(t, 1234)

        assert_running_config_contains_in_order(t, [
            "vlan database",
            "vlan 1,1234",
            "exit"
        ])

        unconfigure_vlan(t, 1234)

        assert_running_config_contains_in_order(t, [
            "vlan database",
            "vlan 1",
            "exit"
        ])

    @with_protocol
    def test_unconfiguring_a_vlan_failing(self, t):
        enable(t)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("vlan database")
        t.readln("")
        t.read("my_switch(config-vlan)#")

        t.write("no vlan 3899")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("These VLANs do not exist:  3899.")
        t.readln("")

        t.read("my_switch(config-vlan)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_configuring_a_vlan_name(self, t):
        enable(t)

        configuring_vlan(t, 1234)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface vlan 1234")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("name")
        t.readln("")
        t.readln("Command not found / Incomplete command. Use ? to list commands.")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("name one two")
        t.readln("                                     ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("name this-name-is-too-long-buddy-buddy")
        t.readln("Name must be 32 characters or less.")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("name this-name-is-too-long-buddy-budd")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, "vlan 1234", [
            "interface vlan 1234",
            "name \"this-name-is-too-long-buddy-budd\"",
            "exit",
        ])

        unconfigure_vlan(t, 1234)


class DellConfigureVlanSshTest(DellConfigureVlanTest):
    __test__ = True
    protocol_factory = ssh_protocol_factory


class DellConfigureVlanTelnetTest(DellConfigureVlanTest):
    __test__ = True
    protocol_factory = telnet_protocol_factory
