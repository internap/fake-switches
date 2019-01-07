# Copyright 2019 Internap.
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

from hamcrest import assert_that, is_

from tests.arista import enable, create_vlan, create_interface_vlan, configuring_interface_vlan, \
    assert_interface_configuration, with_eapi, remove_interface_vlan, remove_vlan
from tests.util.protocol_util import ProtocolTest, SshTester, with_protocol


class TestAristaLoadInterval(ProtocolTest):
    tester_class = SshTester
    test_switch = "arista"

    def setUp(self):
        self.vlan = "299"
        super(TestAristaLoadInterval, self).setUp()
        self._prepare_vlan()

    def tearDown(self):
        self.cleanup_vlan()
        super(TestAristaLoadInterval, self).tearDown()

    @with_protocol
    def _prepare_vlan(self, t):
        enable(t)
        create_vlan(t, self.vlan)
        create_interface_vlan(t, self.vlan)

    @with_protocol
    def cleanup_vlan(self, t):
        enable(t)
        remove_interface_vlan(t, self.vlan)
        remove_vlan(t, self.vlan)

    @with_protocol
    def test_interface_with_load_interval(self, t):
        enable(t)
        configuring_interface_vlan(t, "299", do="load-interval 30")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   load-interval 30"
        ])

    @with_protocol
    @with_eapi
    def test_running_config_with_load_interval_via_api(self, t, api):
        enable(t)
        configuring_interface_vlan(t, "299", do="load-interval 30")

        result = api.enable("show running-config interfaces Vlan299", strict=True, encoding="text")

        assert_that(result, is_([
            {
                "command": "show running-config interfaces Vlan299",
                "encoding": "text",
                "response": {
                    "output": "interface Vlan299\n   load-interval 30\n"
                },
                "result": {
                    "output": "interface Vlan299\n   load-interval 30\n"
                }
            }
        ]))

    @with_protocol
    def test_no_load_interval(self, t):
        enable(t)
        configuring_interface_vlan(t, "299", do="load-interval 30")
        configuring_interface_vlan(t, "299", do="no load-interval")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299"
        ])

    @with_protocol
    def test_interface_with_incomplete_command(self, t):
        enable(t)
        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface vlan {}".format(self.vlan))
        t.read("my_arista(config-if-Vl{})#".format(self.vlan))

        t.write("load-interval")
        t.readln("% Incomplete command")

    @with_protocol
    def test_interface_with_invalid_load_interval(self, t):
        enable(t)
        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface vlan {}".format(self.vlan))
        t.read("my_arista(config-if-Vl{})#".format(self.vlan))

        t.write("load-interval 800")
        t.readln("% Invalid input")

        t.read("my_arista(config-if-Vl{})#".format(self.vlan))

        t.write("load-interval a")
        t.readln("% Invalid input")

    @with_protocol
    def test_interface_with_valid_ranges(self, t):
        enable(t)
        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface vlan {}".format(self.vlan))
        t.read("my_arista(config-if-Vl{})#".format(self.vlan))

        t.write("load-interval 0")
        t.read("my_arista(config-if-Vl{})#".format(self.vlan))

        t.write("load-interval 600")
        t.read("my_arista(config-if-Vl{})#".format(self.vlan))

        t.write("load-interval 30")
        t.read("my_arista(config-if-Vl{})#".format(self.vlan))
