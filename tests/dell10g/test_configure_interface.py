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

from tests.dell10g import enable, assert_interface_configuration, assert_running_config_contains_in_order, \
    get_running_config, configuring_interface, add_vlan, configuring, \
    remove_bond, create_bond
from tests.util.protocol_util import with_protocol, ProtocolTest, SshTester, TelnetTester


class Dell10GConfigureInterfaceSshTest(ProtocolTest):
    tester_class = SshTester
    test_switch = "dell10g"

    @with_protocol
    def test_show_run_vs_show_run_interface_same_output(self, t):
        enable(t)
        configuring_interface(t, "tengigabitethernet 0/0/1", do="shutdown")
        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            "shutdown"
        ])

        assert_running_config_contains_in_order(t, [
            "interface tengigabitethernet 0/0/1",
            "shutdown",
            "exit",
            "!",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no shutdown")

        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            ""
        ])

        config = get_running_config(t)
        assert_that(config, is_not(has_item("interface tengigabitethernet 0/0/1")))

    @with_protocol
    def test_shutting_down(self, t):
        enable(t)
        configuring_interface(t, "tengigabitethernet 0/0/1", do="shutdown")

        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            "shutdown"
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no shutdown")

        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            ""
        ])

    @with_protocol
    def test_description(self, t):
        enable(t)
        configuring_interface(t, "tengigabitethernet 0/0/1", do='description "hello WORLD"')
        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            "description \"hello WORLD\""
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="description 'We dont know yet'")
        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            "description \"We dont know yet\""
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do='description YEEEAH')
        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            "description \"YEEEAH\""
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do='no description')
        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            ""
        ])

    @with_protocol
    def test_lldp_options_defaults_to_enabled(self, t):
        enable(t)
        configuring_interface(t, "tengigabitethernet 0/0/1", do='no lldp transmit')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='no lldp receive')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='no lldp med')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='no lldp med transmit-tlv capabilities')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='no lldp med transmit-tlv network-policy')

        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            'no lldp transmit',
            'no lldp receive',
            'no lldp med',
            'no lldp med transmit-tlv capabilities',
            'no lldp med transmit-tlv network-policy',
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do='lldp transmit')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='lldp receive')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='lldp med')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='lldp med transmit-tlv capabilities')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='lldp med transmit-tlv network-policy')

        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            '',
        ])

    @with_protocol
    def test_spanning_tree(self, t):
        enable(t)
        configuring_interface(t, "tengigabitethernet 0/0/1", do='spanning-tree disable')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='spanning-tree portfast')

        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            'spanning-tree disable',
            'spanning-tree portfast',
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do='no spanning-tree disable')
        configuring_interface(t, "tengigabitethernet 0/0/1", do='no spanning-tree portfast')

        assert_interface_configuration(t, "tengigabitethernet 0/0/1", [
            ''
        ])

    @with_protocol
    def test_access_vlan_that_doesnt_exist_prints_a_warning_and_config_is_unchanged(self, t):
        enable(t)
        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("interface tengigabitethernet 0/0/1")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport access vlan 1200")
        t.readln("")
        t.readln("VLAN ID not found.")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            ""
        ])

    @with_protocol
    def test_access_vlan(self, t):
        enable(t)

        add_vlan(t, 1264)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        
        t.write("interface tengigabitethernet 0/0/1")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")
        t.write("switchport access vlan 1264")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport access vlan 1264",
        ])

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface tengigabitethernet 0/0/1")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")
        t.write("no switchport access vlan")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            ""
        ])

        configuring(t, do="no vlan 1264")

    @with_protocol
    def test_switchport_mode(self, t):
        enable(t)

        add_vlan(t, 1264)
        add_vlan(t, 1265)

        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            ""
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode access")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            ""
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport access vlan 1264")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport access vlan 1264"
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode access")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport access vlan 1264"
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode general")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport access vlan 1264"
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general pvid 1264")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport access vlan 1264",
            "switchport general pvid 1264"
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no switchport access vlan")
        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general allowed vlan add 1265")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport general pvid 1264",
            "switchport general allowed vlan add 1265",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no switchport general pvid")
        configuring_interface(t, "tengigabitethernet 0/0/1", do="no switchport general allowed vlan")
        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode trunk")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk"
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode access")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            ""
        ])

        configuring(t, do="no vlan 1265")
        configuring(t, do="no vlan 1264")

    @with_protocol
    def test_switchport_mode_failure(self, t):
        enable(t)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface tengigabitethernet 0/0/1")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport mode shizzle")
        t.readln("                                         ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_switchport_general_pvid(self, t):
        enable(t)

        add_vlan(t, 1264)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface tengigabitethernet 0/0/1")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport mode general")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport general pvid 1500")
        t.readln("Could not configure pvid.")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport general pvid 1264")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport general pvid 1264"
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no switchport general pvid")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode access")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general pvid 1264")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport general pvid 1264",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no switchport general pvid")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "",
        ])

        configuring(t, do="no vlan 1264")

    @with_protocol
    def test_switchport_add_trunk_trunk_vlans_special_cases(self, t):
        enable(t)

        add_vlan(t, 1200)
        add_vlan(t, 1201)

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode trunk")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan add 1200")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan 1200")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan 1200",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan add 1201")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan 1200-1201",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan add 1202")
        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan remove 1203")
        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan remove 1200")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan 1201-1202",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no switchport trunk allowed vlan")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no switchport mode")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            ""
        ])

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface tengigabitethernet 0/0/1")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")
        t.write("switchport trunk allowed vlan add 1202 1201")
        t.readln("                                                                 ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        configuring(t, do="no vlan 1200")
        configuring(t, do="no vlan 1201")

    #general stays the same
    @with_protocol
    def test_switchport_add_general_trunk_vlans_special_cases(self, t):
        enable(t)

        add_vlan(t, 1201)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface tengigabitethernet 0/0/1")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport mode general")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport general allowed vlan add 1200")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 1")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport general allowed vlan add 1200-1202")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 2")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.readln("VLAN      1202 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport general allowed vlan remove 1200")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 1")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport general allowed vlan remove 1200-1202")
        t.readln("")
        t.readln("          Failure Information")
        t.readln("---------------------------------------")
        t.readln("   VLANs failed to be configured : 2")
        t.readln("---------------------------------------")
        t.readln("   VLAN             Error")
        t.readln("---------------------------------------")
        t.readln("VLAN      1200 ERROR: This VLAN does not exist.")
        t.readln("VLAN      1202 ERROR: This VLAN does not exist.")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport general allowed vlan add 1202-1201")
        t.readln("VLAN range - separate non-consecutive IDs with ',' and no spaces.  Use '-' for range.")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport general allowed vlan add 1202 1201")
        t.readln("                                                                 ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("switchport mode access")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        configuring(t, do="no vlan 1201")

    @with_protocol
    def test_switchport_add_remove_trunk_trunk_vlans(self, t):
        enable(t)

        add_vlan(t, 1200)
        add_vlan(t, 1201)
        add_vlan(t, 1202)
        add_vlan(t, 1203)
        add_vlan(t, 1205)

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode trunk")
        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan 1200")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan 1200",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan add 1200,1201")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan 1200-1201",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan add 1201-1203,1205")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan 1200-1203,1205",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan remove 1202")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan 1200-1201,1203,1205",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan remove 1203,1205")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
            "switchport trunk allowed vlan 1200-1201",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport trunk allowed vlan remove 1200-1203")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode trunk",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode access")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "",
        ])

        configuring(t, do="no vlan 1200")
        configuring(t, do="no vlan 1201")
        configuring(t, do="no vlan 1202")
        configuring(t, do="no vlan 1203")
        configuring(t, do="no vlan 1205")

    @with_protocol
    def test_switchport_add_remove_general_trunk_vlans(self, t):
        enable(t)

        add_vlan(t, 1200)
        add_vlan(t, 1201)
        add_vlan(t, 1202)
        add_vlan(t, 1203)
        add_vlan(t, 1205)

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode general")
        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general allowed vlan add 1200")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general allowed vlan add 1200,1201")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200-1201",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general allowed vlan add 1201-1203,1205")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200-1203,1205",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general allowed vlan remove 1202")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200-1201,1203,1205",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general allowed vlan remove 1203,1205")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
            "switchport general allowed vlan add 1200-1201",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport general allowed vlan remove 1200-1203")
        assert_interface_configuration(t, 'tengigabitethernet 0/0/1', [
            "switchport mode general",
        ])

        configuring_interface(t, "tengigabitethernet 0/0/1", do="switchport mode access")

        configuring(t, do="no vlan 1200")
        configuring(t, do="no vlan 1201")
        configuring(t, do="no vlan 1202")
        configuring(t, do="no vlan 1203")
        configuring(t, do="no vlan 1205")

    @with_protocol
    def test_show_interfaces_status(self, t):
        enable(t)

        configuring_interface(t, "tengigabitethernet 0/0/1", do="description \"longer name than whats allowed\"")
        create_bond(t, 43)

        t.write("show interfaces status")
        t.readln("")
        t.readln("Port      Description               Vlan  Duplex Speed   Neg  Link   Flow Ctrl")
        t.readln("                                                              State  Status")
        t.readln("--------- ------------------------- ----- ------ ------- ---- ------ ---------")
        t.readln("Te0/0/1   longer name than whats al       Full   10000   Auto Up     Active")
        t.readln("Te0/0/2                                   Full   10000   Auto Up     Active")
        t.readln("Te1/0/1                                   Full   10000   Auto Up     Active")
        t.readln("Te1/0/2                                   Full   10000   Auto Up     Active")
        t.readln("")
        t.readln("")
        t.readln("Port    Description                    Vlan  Link")
        t.readln("Channel                                      State")
        t.readln("------- ------------------------------ ----- -------")
        t.readln("Po43                                   trnk  Up")
        t.readln("")
        t.read("my_switch#")

        configuring_interface(t, "tengigabitethernet 0/0/1", do="no description")

        remove_bond(t, 43)

    @with_protocol
    def test_10g_does_not_support_mtu_command_on_interface(self, t):
        enable(t)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface tengigabitethernet 0/0/1")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("mtu 5000")
        t.readln("                                                     ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("no mtu")
        t.readln("                                                     ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-Te0/0/1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")


class Dell10GConfigureInterfaceTelnetTest(Dell10GConfigureInterfaceSshTest):
    tester_class = TelnetTester
