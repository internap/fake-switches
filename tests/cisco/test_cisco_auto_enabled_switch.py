# Copyright 2016 Internap.
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
from tests.util.global_reactor import cisco_switch_ip, \
    cisco_auto_enabled_switch_ssh_port, cisco_auto_enabled_switch_telnet_port
from tests.util.protocol_util import SshTester, TelnetTester, with_protocol


class TestCiscoAutoEnabledSwitchProtocol(unittest.TestCase):
    __test__ = False

    def setUp(self):
        self.protocol = self.create_client()

    def tearDown(self):
        flexmock_teardown()

    @with_protocol
    def test_enable_command_requires_a_password(self, t):
        t.write("enable")
        t.read("my_switch#")
        t.write("terminal length 0")
        t.read("my_switch#")
        t.write("terminal width 0")
        t.read("my_switch#")
        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

    def create_client(self):
        raise NotImplementedError()


class TestCiscoSwitchProtocolSSH(TestCiscoAutoEnabledSwitchProtocol):
    __test__ = True

    def create_client(self):
        return SshTester("ssh", cisco_switch_ip, cisco_auto_enabled_switch_ssh_port, 'root', 'root')


class TestCiscoSwitchProtocolTelnet(TestCiscoAutoEnabledSwitchProtocol):
    __test__ = True

    def create_client(self):
        return TelnetTester("telnet", cisco_switch_ip, cisco_auto_enabled_switch_telnet_port, 'root', 'root')
