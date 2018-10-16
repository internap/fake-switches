# Copyright 2018 Inap.
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

from tests.arista import enable
from tests.util.protocol_util import with_protocol, ProtocolTest, SshTester


class TestAristaRunningConfig(ProtocolTest):
    tester_class = SshTester
    test_switch = "arista"

    @with_protocol
    def test_running_config_all(self, t):
        enable(t)

        t.write("show running-config all")
        t.readln("! Command: show running-config all")
        t.readln("! device: my_arista (vEOS, EOS-4.20.8M)")
        t.readln("!")
        t.readln("! boot system flash:/vEOS-lab.swi")
        t.readln("!")
        t.readln("vlan 1")
        t.readln("   name default")
        t.readln("   mac address learning")
        t.readln("   state active")
        t.readln("!")
        t.readln("end")
        t.read("my_arista#")
