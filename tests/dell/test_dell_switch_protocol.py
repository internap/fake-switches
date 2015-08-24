import pprint
import unittest

from flexmock import flexmock_teardown
from hamcrest import assert_that, is_, has_item, is_not

from tests.util.global_reactor import dell_privileged_password
from tests.util.global_reactor import dell_switch_ip, dell_switch_ssh_port
from tests.util.protocol_util import SshTester, with_protocol


class DellSwitchTest(unittest.TestCase):
    __test__ = False

    def setUp(self):
        self.protocol = SshTester("ssh", dell_switch_ip, dell_switch_ssh_port, 'root', 'root')

    def tearDown(self):
        flexmock_teardown()


class DellUnprivilegedProtocolTest(DellSwitchTest):
    __test__ = True

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


class DellEnabledProtocolTest(DellSwitchTest):
    __test__ = True

    @with_protocol
    def test_exit_returns_to_unprivileged_mode(self, t):
        enable(t)
        t.write("exit")
        t.readln("")
        t.read("my_switch>")

    @with_protocol
    def test_quit_disconnects(self, t):
        enable(t)
        t.write("quit")
        t.read_eof()

    @with_protocol
    def test_write_memory(self, t):
        enable(t)

        t.write("copy running-config startup-config")

        t.readln("")
        t.readln("This operation may take a few minutes.")
        t.readln("Management interfaces will not be available during this time.")
        t.readln("")
        t.read("Are you sure you want to save? (y/n) ")
        t.write_raw("y")
        t.read("y")
        t.readln("")
        t.readln("")
        t.readln("Configuration Saved!")
        t.read("my_switch#")

    @with_protocol
    def test_write_memory_abort(self, t):
        enable(t)

        t.write("copy running-config startup-config")

        t.readln("")
        t.readln("This operation may take a few minutes.")
        t.readln("Management interfaces will not be available during this time.")
        t.readln("")
        t.read("Are you sure you want to save? (y/n) ")
        t.write_raw("n")
        t.read("n")
        t.readln("")
        t.readln("")
        t.readln("Configuration Not Saved!")
        t.read("my_switch#")

    @with_protocol
    def test_write_memory_any_other_key_aborts(self, t):
        enable(t)

        t.write("copy running-config startup-config")

        t.readln("")
        t.readln("This operation may take a few minutes.")
        t.readln("Management interfaces will not be available during this time.")
        t.readln("")
        t.read("Are you sure you want to save? (y/n) ")
        t.write_raw("p")
        t.read("p")
        t.readln("")
        t.readln("")
        t.readln("Configuration Not Saved!")
        t.read("my_switch#")

    @with_protocol
    def test_invalid_command(self, t):
        enable(t)

        t.write("shizzle")
        t.readln("          ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")

    @with_protocol
    def test_entering_configure_mode(self, t):
        enable(t)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_show_running_config_on_empty_ethernet_port(self, t):
        enable(t)

        t.write("show running-config interface ethernet 1/g1")
        t.readln("")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_show_running_config_on_ethernet_port_that_does_not_exists(self, t):
        enable(t)

        t.write("show running-config interface ethernet 4/g8")
        t.readln("")
        t.read("ERROR: Invalid input!")
        t.readln("")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_show_running_config_displays_header(self, t):
        enable(t)
        assert_running_config_contains_in_order(t, [
            '!Current Configuration:',
            '!System Description "PowerConnect 6224P, 3.3.7.3, VxWorks 6.5"',
            '!System Software Version 3.3.7.3',
            '!Cut-through mode is configured as disabled',
            '!',
            'configure',
        ])

    @with_protocol
    def test_show_vlan(self, t):
        enable(t)

        configuring_vlan(t, 10)
        configuring_vlan(t, 11)
        configuring_vlan(t, 12)
        configuring_vlan(t, 13)
        configuring_vlan(t, 14)
        configuring_vlan(t, 15)
        configuring_vlan(t, 16)
        configuring_vlan(t, 17)
        configuring_interface_vlan(t, 17, do="name this-name-is-too-long-buddy-budd")
        configuring_vlan(t, 18)
        configuring_vlan(t, 19)
        configuring_vlan(t, 20)
        configuring_vlan(t, 21)
        configuring_vlan(t, 22)
        configuring_vlan(t, 23)
        configuring_vlan(t, 24)
        configuring_vlan(t, 25)
        configuring_vlan(t, 26)
        configuring_vlan(t, 27)
        configuring_vlan(t, 28)
        configuring_vlan(t, 29)
        configuring_vlan(t, 300)
        configuring_vlan(t, 4000)
        configuring_interface_vlan(t, 300, do="name shizzle")

        t.write("show vlan")
        t.readln("")
        t.readln("VLAN       Name                         Ports          Type      Authorization")
        t.readln("-----  ---------------                  -------------  -----     -------------")
        t.readln("1      Default                                         Default   Required     ")
        t.readln("10                                                     Static    Required     ")
        t.readln("11                                                     Static    Required     ")
        t.readln("12                                                     Static    Required     ")
        t.readln("13                                                     Static    Required     ")
        t.readln("14                                                     Static    Required     ")
        t.readln("15                                                     Static    Required     ")
        t.readln("16                                                     Static    Required     ")
        t.readln("17     this-name-is-too-long-buddy-budd                Static    Required     ")
        t.readln("18                                                     Static    Required     ")
        t.readln("19                                                     Static    Required     ")
        t.readln("20                                                     Static    Required     ")
        t.readln("21                                                     Static    Required     ")
        t.readln("22                                                     Static    Required     ")
        t.readln("23                                                     Static    Required     ")
        t.readln("24                                                     Static    Required     ")
        t.readln("25                                                     Static    Required     ")
        t.readln("26                                                     Static    Required     ")
        t.readln("")
        t.read("--More-- or (q)uit")
        t.write_raw("m")
        t.read("m")
        t.readln("\r                     ")
        t.readln("")
        t.readln("")
        t.readln("VLAN       Name                         Ports          Type      Authorization")
        t.readln("-----  ---------------                  -------------  -----     -------------")
        t.readln("27                                                     Static    Required     ")
        t.readln("28                                                     Static    Required     ")
        t.readln("29                                                     Static    Required     ")
        t.readln("300    shizzle                                         Static    Required     ")
        t.readln("4000                                                   Static    Required     ")
        t.readln("")
        t.read("my_switch#")

        unconfigure_vlan(t, 10)
        unconfigure_vlan(t, 11)
        unconfigure_vlan(t, 12)
        unconfigure_vlan(t, 13)
        unconfigure_vlan(t, 14)
        unconfigure_vlan(t, 15)
        unconfigure_vlan(t, 16)
        unconfigure_vlan(t, 17)
        unconfigure_vlan(t, 18)
        unconfigure_vlan(t, 19)
        unconfigure_vlan(t, 20)
        unconfigure_vlan(t, 21)
        unconfigure_vlan(t, 22)
        unconfigure_vlan(t, 23)
        unconfigure_vlan(t, 24)
        unconfigure_vlan(t, 25)
        unconfigure_vlan(t, 26)
        unconfigure_vlan(t, 27)
        unconfigure_vlan(t, 28)
        unconfigure_vlan(t, 29)
        unconfigure_vlan(t, 300)
        unconfigure_vlan(t, 4000)


class DellConfigureProtocolTest(DellSwitchTest):
    __test__ = True

    @with_protocol
    def test_entering_configure_interface_mode(self, t):
        enable(t)
        configure(t)

        t.write("interface ethernet 1/g1")
        t.readln("")
        t.read("my_switch(config-if-1/g1)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_entering_vlan_database_mode(self, t):
        enable(t)
        configure(t)

        t.write("vlan database")
        t.readln("")
        t.read("my_switch(config-vlan)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_editing_vlan(self, t):
        enable(t)
        configure(t)

        t.write("interface vlan 1260")
        t.readln("VLAN ID not found.")
        t.readln("")

        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        configuring_vlan(t, 1260)

        configure(t)
        t.write("interface vlan 1260")
        t.readln("")
        t.read("my_switch(config-if-vlan1260)#")

        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")

        unconfigure_vlan(t, 1260)


class DellConfigureVlanProtocolTest(DellSwitchTest):
    __test__ = True

    @with_protocol
    def test_configuring_a_vlan(self, t):
        enable(t)

        configuring_vlan(t, 1234)

        assert_running_config_contains_in_order(t, [
            "vlan database",
            "vlan 1,1234",
            "exit"
        ])

        unconfigure_vlan(t, 1234)

        assert_running_config_contains_in_order(t, [
            "vlan database",
            "vlan 1",
            "exit"
        ])

    @with_protocol
    def test_unconfiguring_a_vlan_failing(self, t):
        enable(t)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")

        t.write("vlan database")
        t.readln("")
        t.read("my_switch(config-vlan)#")

        t.write("no vlan 3899")
        t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        t.readln("delays in applying the configuration.")
        t.readln("")
        t.readln("")
        t.readln("These VLANs do not exist:  3899.")
        t.readln("")

        t.read("my_switch(config-vlan)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_configuring_a_vlan_name(self, t):
        enable(t)

        configuring_vlan(t, 1234)

        t.write("configure")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("interface vlan 1234")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("name")
        t.readln("")
        t.readln("Command not found / Incomplete command. Use ? to list commands.")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("name one two")
        t.readln("                                     ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("name this-name-is-too-long-buddy-buddy")
        t.readln("Name must be 32 characters or less.")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("name this-name-is-too-long-buddy-budd")
        t.readln("")
        t.read("my_switch(config-if-vlan1234)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch(config)#")
        t.write("exit")
        t.readln("")
        t.read("my_switch#")

        assert_interface_configuration(t, "vlan 1234", [
            "interface vlan 1234",
            "name \"this-name-is-too-long-buddy-budd\"",
            "exit",
        ])

        unconfigure_vlan(t, 1234)


class DellConfigureInterfaceProtocolTest(DellSwitchTest):
    __test__ = True

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
        t.read("m")
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


def enable(t):
    t.write("enable")
    t.read("Password:")
    t.write_stars(dell_privileged_password)
    t.readln("")
    t.read("my_switch#")


def configure(t):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")


def configuring_interface(t, interface, do):
    interface_short_name = interface.split(' ')[1]
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("interface %s" % interface)
    t.readln("")
    t.read("my_switch(config-if-%s)#" % interface_short_name)

    t.write(do)

    t.readln("")
    t.read("my_switch(config-if-%s)#" % interface_short_name)
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def configuring_a_vlan_on_interface(t, interface, do):
    interface_short_name = interface.split(' ')[1]
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("interface %s" % interface)
    t.readln("")
    t.read("my_switch(config-if-%s)#" % interface_short_name)

    t.write(do)

    t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
    t.readln("delays in applying the configuration.")
    t.readln("")
    t.readln("")
    t.read("my_switch(config-if-%s)#" % interface_short_name)
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def configuring_interface_vlan(t, vlan, do):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("interface vlan {}".format(vlan))
    t.readln("")
    t.read("my_switch(config-if-vlan{})#".format(vlan))

    t.write(do)

    t.readln("")
    t.read("my_switch(config-if-vlan{})#".format(vlan))
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def configuring_vlan(t, vlan_id):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")

    t.write("vlan database")
    t.readln("")
    t.read("my_switch(config-vlan)#")

    t.write("vlan %s" % vlan_id)
    t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
    t.readln("delays in applying the configuration.")
    t.readln("")

    t.readln("")
    t.read("my_switch(config-vlan)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def unconfigure_vlan(t, vlan_id):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")

    t.write("vlan database")
    t.readln("")
    t.read("my_switch(config-vlan)#")

    t.write("no vlan %s" % vlan_id)
    t.readln("Warning: The use of large numbers of VLANs or interfaces may cause significant")
    t.readln("delays in applying the configuration.")
    t.readln("")
    t.readln("If any of the VLANs being deleted are for access ports, the ports will be")
    t.readln("unusable until it is assigned a VLAN that exists.")
    t.readln("")

    t.read("my_switch(config-vlan)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def create_bond(t, bond_id):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("interface port-channel {}".format(bond_id))
    t.readln("")
    t.read("my_switch(config-if-ch{})#".format(bond_id))
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def remove_bond(t, bond_id):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("backdoor remove port-channel {}".format(bond_id))
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def assert_interface_configuration(t, interface, config):
    t.write("show running-config interface %s " % interface)
    for line in config:
        t.readln(line)
    t.readln("")
    t.read("my_switch#")


def assert_running_config_contains_in_order(t, lines):
    config = get_running_config(t)

    assert_lines_order(config, lines)


def get_running_config(t):
    t.write("show running-config")
    config = t.read_lines_until('my_switch#')
    return config


def assert_lines_order(config, lines):
    begin = config.index(lines[0])

    for (i, line) in enumerate(lines):
        expected_content = line
        expected_line_number = i + begin
        actual_content = config[expected_line_number]

        assert_that(actual_content, is_(expected_content),
                    "Item <%s> was expected to be found at line %s but found %s instead.\nWas looking for %s in %s" % (
                    line, expected_line_number, actual_content, pprint.pformat(lines), pprint.pformat(config)))
