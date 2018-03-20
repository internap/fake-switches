# Copyright 2018 Internap.
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
from tests.cisco import enable, assert_interface_configuration, configuring_interface
from tests.util.protocol_util import SshTester, with_protocol, ProtocolTest


class TestCiscoSwitchInterface(ProtocolTest):
    __test__ = True

    tester_class = SshTester
    test_switch = "cisco6500"

    @with_protocol
    def test_disable_ntp(self, t):
        enable(t)

        configuring_interface(t, "FastEthernet 0/3", do="ntp disable")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " ntp disable",
            "end"])

        configuring_interface(t, "FastEthernet 0/3", do="no ntp disable")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            "end"])

