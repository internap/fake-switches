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

from hamcrest import assert_that
from hamcrest import greater_than
from tests.cisco import enable
from tests.util.global_reactor import COMMIT_DELAY
from tests.util.protocol_util import SshTester, with_protocol, ProtocolTest


class TestCiscoSwitchProtocolWithCommitDelay(ProtocolTest):
    tester_class = SshTester
    test_switch = "commit-delayed-cisco"

    @with_protocol
    def test_write_memory_with_commit_delay(self, t):
        t.child.timeout = 10
        enable(t)
        start_time = time()
        t.write("write memory")
        t.readln("Building configuration...")
        t.readln("OK")
        t.read("my_switch#")
        end_time = time()

        assert_that((end_time - start_time), greater_than(COMMIT_DELAY))

