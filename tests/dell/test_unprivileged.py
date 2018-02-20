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

from tests.util.protocol_util import with_protocol, ProtocolTest, SshTester, TelnetTester


class DellUnprivilegedTest(ProtocolTest):
    __test__ = False

    tester_class = SshTester
    test_switch = "dell"

    @with_protocol
    def test_entering_enable_mode_requires_a_password(self, t):
        t.write("enable")
        t.read("Password:")
        t.write_stars(t.conf["extra"]["password"])
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
    tester_class = SshTester


class DellUnprivilegedTelnetTest(DellUnprivilegedTest):
    __test__ = True
    tester_class = TelnetTester
