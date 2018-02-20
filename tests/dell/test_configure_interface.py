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

from hamcrest import assert_that, is_not, has_item

from tests.dell import enable, configuring_interface, \
    assert_interface_configuration, assert_running_config_contains_in_order, \
    get_running_config, configure, configuring_vlan, unconfigure_vlan, \
    configuring_a_vlan_on_interface, create_bond, remove_bond, \
    configuring_bond
from tests.util.protocol_util import with_protocol, ProtocolTest, SshTester, TelnetTester


class DellConfigureInterfaceTest(ProtocolTest):
    __test__ = False

    tester_class = SshTester
    test_switch = "dell"

    @with_protocol
    def test_show_run_vs_show_run_interface_same_output(self, t):
        enable(t)
        configuring_interface(t, "ethernet 1/g1", do="shutdown")
        assert_interface_configuration(t, "ethernet 1/g1", [
            "shutdown"
        ])

        assert_running_config_contains_in_order(t, [
            "interface ethernet 1/g1",
            "shutdown",
            "exit",
            "!",
        ])

        configuring_interface(t, "ethernet 1/g1", do="no shutdown")

        assert_interface_configuration(t, "ethernet 1/g1", [
            ""
        ])

        config = get_running_config(t)
        assert_that(config, is_not(has_item("interface ethernet 1/g1")))

    @with_protocol
    def test_shutting_down(self, t):
        enable(t)
        configuring_interface(t, "ethernet 1/g1", do="shutdown")

        assert_interface_configuration(t, "ethernet 1/g1", [
            "shutdown"
        ])

        configuring_interface(t, "ethernet 1/g1", do="no shutdown")

        assert_interface_configuration(t, "ethernet 1/g1", [
            ""
        ])

    @with_protocol
    def test_description(self, t):
        enable(t)
        configuring_interface(t, "ethernet 1/g1", do='description "hello WORLD"')
        assert_interface_configuration(t, "ethernet 1/g1", [
            "description 'hello WORLD'"
        ])

        configuring_interface(t, "ethernet 1/g1", do="description 'We dont know yet'")
        assert_interface_configuration(t, "ethernet 1/g1", [
            "description 'We dont know yet'"
        ])

        configuring_interface(t, "ethernet 1/g1", do='description YEEEAH')
        assert_interface_configuration(t, "ethernet 1/g1", [
            "description 'YEEEAH'"
        ])

        configuring_interface(t, "ethernet 1/g1", do='no description')
        assert_interface_configuration(t, "ethernet 1/g1", [
            ""
        ])

    @with_protocol
    def test_lldp_options_defaults_to_enabled(self, t):
        enable(t)
        configuring_interface(t, "ethernet 1/g1", do='no lldp transmit')
        configuring_interface(t, "ethernet 1/g1", do='no lldp receive')
        configuring_interface(t, "ethernet 1/g1", do='no lldp med transmit-tlv capabilities')
        configuring_interface(t, "ethernet 1/g1", do='no lldp med transmit-tlv network-policy')

        assert_interface_configuration(t, "ethernet 1/g1", [
            'no lldp transmit',
            'no lldp receive',
            'no lldp med transmit-tlv capabilities',
            'no lldp med transmit-tlv network-policy',
        ])

        configuring_interface(t, "ethernet 1/g1", do='lldp transmit')
        configuring_interface(t, "ethernet 1/g1", do='lldp receive')
        configuring_interface(t, "ethernet 1/g1", do='lldp med transmit-tlv capabilities')
        configuring_interface(t, "ethernet 1/g1", do='lldp med transmit-tlv network-policy')

        assert_interface_configuration(t, "ethernet 1/g1", [
            '',
        ])

    @with_protocol
    def test_spanning_tree(self, t):
        enable(t)
        configuring_interface(t, "ethernet 1/g1", do='spanning-tree disable')
        configuring_interface(t, "ethernet 1/g1", do='spanning-tree portfast')

        assert_interface_configuration(t, "ethernet 1/g1", [
            'spanning-tree disable',
            'spanning-tree portfast',
        ])

        configuring_interface(t, "ethernet 1/g1", do='no spanning-tree disable')
        configuring_interface(t, "ethernet 1/g1", do='no spanning-tree portfast')

        assert_interface_configuration(t, "ethernet 1/g1", [
            ''
        ])



    @with_protocol
    def test_access_vlan_that_doesnt_exist_prints_a_warning_and_config_is_unchanged(self, t):
        enable(t)
        configure(t)

        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport access vlan 1200")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("VLAN ID not found.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            ""
        ])

    @with_protocol
    def test_access_vlan(self, t):
        enable(t)

        configuring_vlan(t, 1264)

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("switchport access vlan 1264")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport access vlan 1264",
        ])

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("no switchport access vlan")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            ""
        ])

        unconfigure_vlan(t, 1264)

    @with_protocol
    def test_no_switchport_mode_in_trunk_mode(self, t):
        enable(t)

        configuring_vlan(t, 1264)

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("switchport mode trunk")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("switchport trunk allowed vlan add 1264")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan add 1264",
        ])

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("no switchport mode")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            ""
        ])

        unconfigure_vlan(t, 1264)

    @with_protocol
    def test_no_switchport_mode_in_access_mode(self, t):
        enable(t)

        configuring_vlan(t, 1264)

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("switchport access vlan 1264")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport access vlan 1264",
        ])

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("no switchport mode")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport access vlan 1264",
        ])

        unconfigure_vlan(t, 1264)

    @with_protocol
    def test_no_switchport_mode_in_general_mode(self, t):
        enable(t)

        configuring_vlan(t, 1264)

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("switchport mode general")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("switchport general pvid 1264")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general allowed vlan add 1264")

        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general pvid 1264",
            "switchport general allowed vlan add 1264",
        ])

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("no switchport mode")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            "",
        ])

        unconfigure_vlan(t, 1264)

    @with_protocol
    def test_switchport_mode(self, t):
        enable(t)

        configuring_vlan(t, 1264)
        configuring_vlan(t, 1265)

        assert_interface_configuration(t, 'ethernet 1/g1', [
            ""
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport mode access")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            ""
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport access vlan 1264")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport access vlan 1264"
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport mode access")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport access vlan 1264"
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport mode general")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general"
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport general pvid 1264")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general pvid 1264"
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport general allowed vlan add 1265")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general pvid 1264",
            "switchport general allowed vlan add 1265",
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport mode trunk")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk"
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport trunk allowed vlan add 1265")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan add 1265",
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport mode access")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            ""
        ])

        unconfigure_vlan(t, 1265)
        unconfigure_vlan(t, 1264)

    @with_protocol
    def test_switchport_mode_failure(self, t):
        enable(t)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport mode shizzle")
        t.readln("                                         ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_switchport_general_pvid(self, t):
        enable(t)

        configuring_vlan(t, 1264)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general pvid 1264")
        t.readln("")
        t.readln("Port is not general port.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport mode general")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general pvid 1500")
        t.readln("Could not configure pvid.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general pvid 1264")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general pvid 1264"
        ])

        configuring_interface(t, "ethernet 1/g1", do="no switchport general pvid")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport mode access")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "",
        ])

        unconfigure_vlan(t, 1264)

    @with_protocol
    def test_switchport_add_trunk_trunk_vlans_special_cases(self, t):
        enable(t)

        configuring_vlan(t, 1201)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport trunk allowed vlan add 1200")
        t.readln("Interface not in Trunk Mode.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport mode trunk")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport trunk allowed vlan add 1200")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 1")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport trunk allowed vlan add 1200-1202")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 2")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.readln("VLAN      1202 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport trunk allowed vlan remove 1200")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 1")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport trunk allowed vlan remove 1200-1202")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 2")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.readln("VLAN      1202 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport trunk allowed vlan add 1202-1201")
        t.readln("VLAN range - separate non-consecutive IDs with ',' and no spaces.  Use '-' for range.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport trunk allowed vlan add 1202 1201")
        t.readln("                                                                 ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport mode access")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        unconfigure_vlan(t, 1201)

    @with_protocol
    def test_switchport_add_general_trunk_vlans_special_cases(self, t):
        enable(t)

        configuring_vlan(t, 1201)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general allowed vlan add 1200")
        t.readln("Interface not in General Mode.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport mode general")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general allowed vlan add 1200")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 1")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general allowed vlan add 1200-1202")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 2")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.readln("VLAN      1202 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general allowed vlan remove 1200")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 1")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general allowed vlan remove 1200-1202")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 2")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.readln("VLAN      1202 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general allowed vlan add 1202-1201")
        t.readln("VLAN range - separate non-consecutive IDs with ',' and no spaces.  Use '-' for range.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport general allowed vlan add 1202 1201")
        t.readln("                                                                 ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("switchport mode access")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        unconfigure_vlan(t, 1201)

    @with_protocol
    def test_switchport_add_remove_trunk_trunk_vlans(self, t):
        enable(t)

        configuring_vlan(t, 1200)
        configuring_vlan(t, 1201)
        configuring_vlan(t, 1202)
        configuring_vlan(t, 1203)
        configuring_vlan(t, 1205)

        configuring_interface(t, "ethernet 1/g1", do="switchport mode trunk")
        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport trunk allowed vlan add 1200")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan add 1200",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport trunk allowed vlan add 1200,1201")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan add 1200-1201",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport trunk allowed vlan add 1201-1203,1205")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan add 1200-1203,1205",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport trunk allowed vlan remove 1202")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan add 1200-1201,1203,1205",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport trunk allowed vlan remove 1203,1205")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan add 1200-1201",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport trunk allowed vlan remove 1200-1203")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode trunk",
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport mode access")

        unconfigure_vlan(t, 1200)
        unconfigure_vlan(t, 1201)
        unconfigure_vlan(t, 1202)
        unconfigure_vlan(t, 1203)
        unconfigure_vlan(t, 1205)

    @with_protocol
    def test_switchport_add_remove_general_trunk_vlans(self, t):
        enable(t)

        configuring_vlan(t, 1200)
        configuring_vlan(t, 1201)
        configuring_vlan(t, 1202)
        configuring_vlan(t, 1203)
        configuring_vlan(t, 1205)

        configuring_interface(t, "ethernet 1/g1", do="switchport mode general")
        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport general allowed vlan add 1200")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport general allowed vlan add 1200,1201")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200-1201",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport general allowed vlan add 1201-1203,1205")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200-1203,1205",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport general allowed vlan remove 1202")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200-1201,1203,1205",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport general allowed vlan remove 1203,1205")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200-1201",
        ])

        configuring_a_vlan_on_interface(t, "ethernet 1/g1", do="switchport general allowed vlan remove 1200-1203")
        assert_interface_configuration(t, 'ethernet 1/g1', [
            "switchport mode general",
        ])

        configuring_interface(t, "ethernet 1/g1", do="switchport mode access")

        unconfigure_vlan(t, 1200)
        unconfigure_vlan(t, 1201)
        unconfigure_vlan(t, 1202)
        unconfigure_vlan(t, 1203)
        unconfigure_vlan(t, 1205)

    @with_protocol
    def test_show_interfaces_status(self, t):
        enable(t)

        create_bond(t, 1)
        create_bond(t, 2)
        create_bond(t, 3)
        create_bond(t, 4)
        create_bond(t, 5)
        create_bond(t, 6)
        create_bond(t, 7)
        create_bond(t, 8)
        create_bond(t, 9)
        create_bond(t, 10)

        t.write("show interfaces status")
        t.readln("")
        t.readln("Port   Type                            Duplex  Speed    Neg  Link  Flow Control")
        t.readln("                                                             State Status")
        t.readln("-----  ------------------------------  ------  -------  ---- --------- ------------")
        t.readln("1/g1   Gigabit - Level                 Full    Unknown  Auto Down      Inactive")
        t.readln("1/g2   Gigabit - Level                 Full    Unknown  Auto Down      Inactive")
        t.readln("1/xg1  10G - Level                     Full    Unknown  Auto Down      Inactive")
        t.readln("2/g1   Gigabit - Level                 Full    Unknown  Auto Down      Inactive")
        t.readln("2/g2   Gigabit - Level                 Full    Unknown  Auto Down      Inactive")
        t.readln("2/xg1  10G - Level                     Full    Unknown  Auto Down      Inactive")
        t.readln("")
        t.readln("")
        t.readln("Ch   Type                            Link")
        t.readln("                                     State")
        t.readln("---  ------------------------------  -----")
        t.readln("ch1  Link Aggregate                  Down")
        t.readln("ch2  Link Aggregate                  Down")
        t.readln("ch3  Link Aggregate                  Down")
        t.readln("ch4  Link Aggregate                  Down")
        t.readln("ch5  Link Aggregate                  Down")
        t.readln("ch6  Link Aggregate                  Down")
        t.readln("ch7  Link Aggregate                  Down")
        t.readln("ch8  Link Aggregate                  Down")
        t.read("--More-- or (q)uit")
        t.write_raw("m")
        t.readln("")
        t.readln("ch9  Link Aggregate                  Down")
        t.readln("ch10 Link Aggregate                  Down")
        t.readln("")
        t.readln("Flow Control:Enabled")
        t.readln("")
        t.read("my_switch#")

        remove_bond(t, 1)
        remove_bond(t, 2)
        remove_bond(t, 3)
        remove_bond(t, 4)
        remove_bond(t, 5)
        remove_bond(t, 6)
        remove_bond(t, 7)
        remove_bond(t, 8)
        remove_bond(t, 9)
        remove_bond(t, 10)

    @with_protocol
    def test_mtu(self, t):
        enable(t)

        configure(t)
        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("mtu what")
        t.readln("                            ^")
        t.readln("Invalid input. Please specify an integer in the range 1518 to 9216.")
        t.read("my_switch(config-if-1/g1)#")
        t.write("mtu 1517")
        t.readln("                            ^")
        t.readln("Value is out of range. The valid range is 1518 to 9216.")
        t.read("my_switch(config-if-1/g1)#")
        t.write("mtu 9217")
        t.readln("                            ^")
        t.readln("Value is out of range. The valid range is 1518 to 9216.")
        t.read("my_switch(config-if-1/g1)#")
        t.write("mtu 5000 lol")
        t.readln("                                  ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")
        t.write("mtu 5000")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, "ethernet 1/g1", [
            "mtu 5000"
        ])

        configuring_interface(t, "ethernet 1/g1", do="no mtu")

        assert_interface_configuration(t, "ethernet 1/g1", [
            ""
        ])

    @with_protocol
    def test_mtu_on_bond(self, t):
        enable(t)

        create_bond(t, 1)

        configure(t)
        t.write("interface port-channel 1")
        t.readln("")
        t.read("my_switch(config-if-ch1)#")
        t.write("mtu what")
        t.readln("                            ^")
        t.readln("Invalid input. Please specify an integer in the range 1518 to 9216.")
        t.read("my_switch(config-if-ch1)#")
        t.write("mtu 1517")
        t.readln("                            ^")
        t.readln("Value is out of range. The valid range is 1518 to 9216.")
        t.read("my_switch(config-if-ch1)#")
        t.write("mtu 9217")
        t.readln("                            ^")
        t.readln("Value is out of range. The valid range is 1518 to 9216.")
        t.read("my_switch(config-if-ch1)#")
        t.write("mtu 5000 lol")
        t.readln("                                  ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-ch1)#")
        t.write("mtu 5000")
        t.readln("")
        t.read("my_switch(config-if-ch1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, "port-channel 1", [
            "mtu 5000"
        ])

        configuring_bond(t, "port-channel 1", do="no mtu")

        assert_interface_configuration(t, "port-channel 1", [
            ""
        ])

        remove_bond(t, 1)


class DellConfigureInterfaceSshTest(DellConfigureInterfaceTest):
    __test__ = True
    tester_class = SshTester


class DellConfigureInterfaceTelnetTest(DellConfigureInterfaceTest):
    __test__ = True
    tester_class = TelnetTester
