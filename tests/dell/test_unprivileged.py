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

from tests.dell import ssh_protocol_factory, telnet_protocol_factory
from tests.util.global_reactor import dell_privileged_password
from tests.util.protocol_util import with_protocol


class DellUnprivilegedTest(unittest.TestCase):
    __test__ = False
    protocol_factory = None

    def setUp(self):
        self.protocol = self.protocol_factory()

    def tearDown(self):
        flexmock_teardown()

    @with_protocol
    def test_entering_enable_mode_requires_a_password(self, t):
        t.write("enable")
        t.read("Password:")
        t.write_stars(dell_privileged_password)
        t.read("\r\n")
        t.read("my_switch#")

    @with_protocol
    def test_wrong_password(self, t):
        t.write("enable")
        t.read("Password:")
        t.write_stars("hello_world")
        t.readln("Incorrect Password!")
        t.read("my_switch>")

    @with_protocol
    def test_no_password_works_for_legacy_reasons(self, t):
        t.write("enable")
        t.read("Password:")
        t.write_stars("")
        t.read("\r\n")
        t.read("my_switch#")

    @with_protocol
    def test_exit_disconnects(self, t):
        t.write("exit")
        t.read_eof()

    @with_protocol
    def test_quit_disconnects(self, t):
        t.write("quit")
        t.read_eof()


class DellUnprivilegedSshTest(DellUnprivilegedTest):
    __test__ = True
    protocol_factory = ssh_protocol_factory


class DellUnprivilegedTelnetTest(DellUnprivilegedTest):
    __test__ = True
    protocol_factory = telnet_protocol_factory
