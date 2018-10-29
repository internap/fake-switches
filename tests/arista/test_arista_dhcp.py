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
from hamcrest import assert_that, is_

from tests.arista import enable, remove_vlan, create_vlan, create_interface_vlan, configuring_interface_vlan, \
    remove_interface_vlan, with_eapi, assert_interface_configuration
from tests.util.protocol_util import ProtocolTest, SshTester, with_protocol


class TestAristaDHCP(ProtocolTest):
    tester_class = SshTester
    test_switch = "arista"

    @with_protocol
    def test_setup_in_running_config(self, t):
        enable(t)

        create_vlan(t, "299")
        create_interface_vlan(t, "299")
        configuring_interface_vlan(t, "299", do="ip helper-address 1.1.1.1")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip helper-address 1.1.1.1"
        ])

        configuring_interface_vlan(t, "299", do="ip helper-address one.one.one.one")
        configuring_interface_vlan(t, "299", do="ip helper-address one-one-one-one")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip helper-address 1.1.1.1",
            "   ip helper-address one.one.one.one",
            "   ip helper-address one-one-one-one",
        ])

        configuring_interface_vlan(t, "299", do="no ip helper-address one.one.one.one")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip helper-address 1.1.1.1",
            "   ip helper-address one-one-one-one",
        ])

        configuring_interface_vlan(t, "299", do="ip helper-address 1.1.1.1")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299",
            "   ip helper-address 1.1.1.1",
            "   ip helper-address one-one-one-one",
        ])

        configuring_interface_vlan(t, "299", do="no ip helper-address")

        assert_interface_configuration(t, "Vlan299", [
            "interface Vlan299"
        ])

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")

    @with_protocol
    @with_eapi
    def test_running_config_via_api(self, t, api):
        enable(t)

        create_vlan(t, "299")
        create_interface_vlan(t, "299")
        configuring_interface_vlan(t, "299", do="ip helper-address 1.1.1.1")
        configuring_interface_vlan(t, "299", do="ip helper-address 2.2.2.2")

        result = api.enable("show running-config interfaces Vlan299", strict=True, encoding="text")

        assert_that(result, is_([
            {
                "command": "show running-config interfaces Vlan299",
                "encoding": "text",
                "response": {
                    "output": "interface Vlan299\n   ip helper-address 1.1.1.1\n   ip helper-address 2.2.2.2\n"
                },
                "result": {
                    "output": "interface Vlan299\n   ip helper-address 1.1.1.1\n   ip helper-address 2.2.2.2\n"
                }
            }
        ]))

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")

    @with_protocol
    def test_show_ip_helper_address_invalid_values(self, t):
        enable(t)

        create_vlan(t, "299")

        t.write("configure terminal")
        t.read("my_arista(config)#")
        t.write("interface vlan 299")
        t.read("my_arista(config-if-Vl299)#")

        t.write("ip helper-address")
        t.readln("% Incomplete command")
        t.read("my_arista(config-if-Vl299)#")

        t.write("ip helper-address oh oh")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Vl299)#")

        t.write("ip helper-address oh;oh")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Vl299)#")

        t.write("ip helper-address oh_oh")
        t.readln("% Invalid input")
        t.read("my_arista(config-if-Vl299)#")

        t.write("ip helper-address 1234567890123456789012345678901234567890123456789012345678901234")
        t.read("my_arista(config-if-Vl299)#")

        t.write("ip helper-address 12345678901234567890123456789012345678901234567890123456789012345")
        t.readln("% Host name is invalid. Host name must contain only alphanumeric characters, '.' and '-'.")
        t.readln("It must begin and end with an alphanumeric character.")
        t.readln("Maximum characters in hostname is 64.")
        t.read("my_arista(config-if-Vl299)#")

        remove_interface_vlan(t, "299")
        remove_vlan(t, "299")
