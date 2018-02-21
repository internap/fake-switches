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

from time import time

from hamcrest import assert_that, less_than, greater_than
from tests.dell import enable
from tests.util.global_reactor import COMMIT_DELAY
from tests.util.protocol_util import with_protocol, SshTester, ProtocolTest


class DellEnabledWithCommitDelayTest(ProtocolTest):

    tester_class = SshTester
    test_switch = "commit-delayed-dell"

    @with_protocol
    def test_write_memory_with_delay(self, t):
        t.child.timeout = 10
        enable(t)

        t.write("copy running-config startup-config")

        t.readln("")
        t.readln("This operation may take a few minutes.")
        t.readln("Management interfaces will not be available during this time.")
        t.readln("")
        t.read("Are you sure you want to save? (y/n) ")
        start_time = time()
        t.write_raw("y")
        t.readln("")
        t.readln("")
        t.readln("Configuration Saved!")
        end_time = time()
        t.read("my_switch#")

        assert_that((end_time - start_time), greater_than(COMMIT_DELAY))

    @with_protocol
    def test_write_memory_abort_does_not_call_commit_delay(self, t):
        t.child.timeout = 10
        enable(t)

        t.write("copy running-config startup-config")

        t.readln("")
        t.readln("This operation may take a few minutes.")
        t.readln("Management interfaces will not be available during this time.")
        t.readln("")
        t.read("Are you sure you want to save? (y/n) ")
        t.write_raw("n")
        start_time = time()
        t.readln("")
        t.readln("")
        t.readln("Configuration Not Saved!")
        end_time = time()
        t.read("my_switch#")

        assert_that((end_time - start_time), less_than(COMMIT_DELAY))
