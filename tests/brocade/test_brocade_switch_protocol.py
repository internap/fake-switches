import mock
from tests.util.protocol_util import SshTester, with_protocol, ProtocolTest


class TestBrocadeSwitchProtocol(ProtocolTest):
    tester_class = SshTester
    test_switch = "brocade"

    @with_protocol
    def test_enable_command_requires_a_password(self, t):
        t.write("enable")
        t.read("Password:")
        t.write_invisible(t.conf["extra"]["password"])
        t.read("SSH@my_switch#")

    @with_protocol
    def test_wrong_password(self, t):
        t.write("enable")
        t.read("Password:")
        t.write_invisible("hello_world")
        t.readln("Error - Incorrect username or password.")
        t.read("SSH@my_switch>")

    @with_protocol
    def test_no_password_works_for_legacy_reasons(self, t):
        t.write("enable")
        t.read("Password:")
        t.write_invisible("")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_exiting_loses_the_connection(self, t):
        t.write("enable")
        t.read("Password:")
        t.write_invisible(t.conf["extra"]["password"])
        t.read("SSH@my_switch#")
        t.write("exit")
        t.read_eof()

    @with_protocol
    def test_no_such_command_return_to_prompt(self, t):
        enable(t)

        t.write("shizzle")
        t.readln("Invalid input -> shizzle")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch#")

    @with_protocol
    @mock.patch("fake_switches.adapters.tftp_reader.read_tftp")
    def test_command_copy_failing(self, t, read_tftp):
        read_tftp.side_effect = Exception("Stuff")

        enable(t)

        t.write("ncopy tftp 1.2.3.4 my-file running-config")
        t.readln("TFTP: Download to running-config failed - Session timed out")
        t.read("SSH@my_switch#")

        read_tftp.assert_called_with("1.2.3.4", "my-file")

    @with_protocol
    @mock.patch("fake_switches.adapters.tftp_reader.read_tftp")
    def test_command_copy_success(self, t, read_tftp):
        enable(t)

        t.write("ncopy tftp 1.2.3.4 my-file running-config")
        t.readln("done")
        t.read("SSH@my_switch#")

        read_tftp.assert_called_with("1.2.3.4", "my-file")

    @with_protocol
    def test_command_show_run_int_vlan_empty(self, t):
        enable(t)

        t.write("skip-page-display")
        t.read("SSH@my_switch#")
        t.write("show running-config vlan | begin vlan 1299")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_command_add_vlan(self, t):
        enable(t)

        t.write("conf t")
        t.read("SSH@my_switch(config)#")
        t.write("vlan 123 name shizzle")
        t.read("SSH@my_switch(config-vlan-123)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")
        t.write("show running-config vlan | begin vlan 123")
        t.readln("vlan 123 name shizzle")
        t.readln("!")
        t.readln("!")
        t.readln("")
        t.read("SSH@my_switch#")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("no vlan 123")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")
        t.write("show running-config vlan | begin vlan 123")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_command_assign_access_vlan_to_port(self, t):
        enable(t)
        create_vlan(t, "123")
        set_interface_untagged_on_vlan(t, "ethernet 1/1", "123")

        t.write("show interfaces ethernet 1/1 | inc Member of")
        t.readln("  Member of VLAN 123 (untagged), port is in untagged mode, port state is Disabled")
        t.read("SSH@my_switch#")

        unset_interface_untagged_on_vlan(t, "ethernet 1/1", "123")

        t.write("show interfaces ethe1/1 | inc VLAN 1")
        t.readln("  Member of VLAN 1 (untagged), port is in untagged mode, port state is Disabled")
        t.read("SSH@my_switch#")

        remove_vlan(t, "123")

    @with_protocol
    def test_command_interface_tagged_with_native_default_vlan(self, t):
        enable(t)
        create_vlan(t, "123")
        configuring_vlan(t, "123", do="tagged ethernet 1/1")

        t.write("show interfaces ethe 1/1 | inc Member of")
        t.readln("  Member of VLAN 1 (untagged), 1 L2 VLANS (tagged), port is in dual mode (default vlan), port state is Disabled")
        t.read("SSH@my_switch#")

        configuring_vlan(t, "123", do="no tagged ethernet 1/1")

        t.write("show interfaces ethe1/1 | inc VLAN 1")
        t.readln("  Member of VLAN 1 (untagged), port is in untagged mode, port state is Disabled")
        t.read("SSH@my_switch#")

        remove_vlan(t, "123")

    @with_protocol
    def test_command_show_interface_invalid_interface_name(self, t):
        enable(t)

        t.write("show interface ethe 1/25")
        t.readln("Error - invalid interface 1/25")
        t.read("SSH@my_switch#")

        t.write("show interface ethe 1/64")
        t.readln("Error - invalid interface 1/64")
        t.read("SSH@my_switch#")

        t.write("show interface ethe 1/65")
        t.readln("Invalid input -> 1/65")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch#")

        t.write("show interface ethe 1/99")
        t.readln("Invalid input -> 1/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch#")

        t.write("show interface ethe 2/1")
        t.readln("Error - interface 2/1 is not an ETHERNET interface")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_command_no_interface_invalid_interface_name(self, t):
        enable(t)
        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")

        t.write("no interface ethe 1/25")
        t.readln("Error - invalid interface 1/25")
        t.read("SSH@my_switch(config)#")

        t.write("no interface ethe 1/64")
        t.readln("Error - invalid interface 1/64")
        t.read("SSH@my_switch(config)#")

        t.write("no interface ethe 1/65")
        t.readln("Invalid input -> 1/65")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config)#")

        t.write("no interface ethe 1/99")
        t.readln("Invalid input -> 1/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config)#")

        t.write("no interface ethe 2/1")
        t.readln("Error - interface 2/1 is not an ETHERNET interface")
        t.read("SSH@my_switch(config)#")

        t.write("exit")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_command_interface_invalid_interface_name(self, t):
        enable(t)
        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethe 1/25")
        t.readln("Error - invalid interface 1/25")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethe 1/64")
        t.readln("Error - invalid interface 1/64")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethe 1/65")
        t.readln("Invalid input -> 1/65")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethe 1/99")
        t.readln("Invalid input -> 1/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethe nonexistent99")
        t.readln("Invalid input -> nonexistent  99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethe 2/1")
        t.readln("Error - interface 2/1 is not an ETHERNET interface")
        t.read("SSH@my_switch(config)#")

        t.write("exit")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_remove_a_ports_from_a_vlan_should_print_an_error(self, t):
        enable(t)

        create_vlan(t, "123")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("vlan 123")
        t.read("SSH@my_switch(config-vlan-123)#")

        t.write("no untagged ethernet 1/1")
        t.readln("Error: ports ethe 1/1 are not untagged members of vlan 123")
        t.read("SSH@my_switch(config-vlan-123)#")

        t.write("no tagged ethernet 1/1")
        t.readln("Error: ports ethe 1/1 are not tagged members of vlan 123")
        t.read("SSH@my_switch(config-vlan-123)#")

        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_unknown_ports_when_tagging_prints_an_error(self, t):
        enable(t)

        create_vlan(t, "123")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("vlan 123")
        t.read("SSH@my_switch(config-vlan-123)#")

        t.write("untagged ethernet 1/99")
        t.readln("Invalid input -> 1/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vlan-123)#")

        t.write("tagged ethernet 1/99")
        t.readln("Invalid input -> 1/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vlan-123)#")

        t.write("no untagged ethernet 1/99")
        t.readln("Invalid input -> 1/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vlan-123)#")

        t.write("no tagged ethernet 1/99")
        t.readln("Invalid input -> 1/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vlan-123)#")

        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_command_interface_tagged_with_native_vlan(self, t):
        enable(t)
        create_vlan(t, "123")
        create_vlan(t, "124")
        create_vlan(t, "456")

        configuring_vlan(t, "123", do="tagged ethernet 1/1")
        configuring_vlan(t, "124", do="tagged ethernet 1/1")
        configuring_vlan(t, "456", do="untagged ethernet 1/1")

        t.write("show interfaces ethernet 1/1 | inc Member of")
        t.readln("  Member of VLAN 456 (untagged), 2 L2 VLANS (tagged), port is in dual mode, port state is Disabled")
        t.read("SSH@my_switch#")

        configuring_vlan(t, "123", do="no tagged ethernet 1/1")
        configuring_vlan(t, "124", do="no tagged ethernet 1/1")
        configuring_vlan(t, "456", do="no untagged ethernet 1/1")

        t.write("show interfaces ethe1/1 | inc VLAN 1")
        t.readln("  Member of VLAN 1 (untagged), port is in untagged mode, port state is Disabled")
        t.read("SSH@my_switch#")

        remove_vlan(t, "123")
        remove_vlan(t, "124")
        remove_vlan(t, "456")

    @with_protocol
    def test_command_interface_tagged_with_no_native_vlan(self, t):
        enable(t)
        create_vlan(t, "123")

        configuring_vlan(t, "123", do="tagged ethernet 1/1")
        configuring_vlan(t, "1", do="no untagged ethernet 1/1")

        t.write("show interfaces ethernet 1/1 | inc Member of")
        t.readln("  Member of 1 L2 VLAN(S) (tagged), port is in tagged mode, port state is Disabled")
        t.read("SSH@my_switch#")

        configuring_vlan(t, "123", do="no tagged ethernet 1/1")
        # untagged vlan 1 returns by default magically

        t.write("show interfaces ethe1/1 | inc VLAN 1")
        t.readln("  Member of VLAN 1 (untagged), port is in untagged mode, port state is Disabled")
        t.read("SSH@my_switch#")

        remove_vlan(t, "123")

    @with_protocol
    def test_show_interfaces(self, t):
        enable(t)

        configuring_interface(t, "1/2", do="port-name hello")
        configuring_interface(t, "1/3", do="enable")
        create_interface_vlan(t, "1000")
        configuring_interface_vlan(t, "1000", do="port-name Salut")
        create_interface_vlan(t, "2000")
        configuring_interface_vlan(t, "2000", do="ip address 1.1.1.1/24")

        t.write("show interfaces")
        t.readln("GigabitEthernet1/1 is disabled, line protocol is down")
        t.readln("  Hardware is GigabitEthernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Member of VLAN 1 (untagged), port is in untagged mode, port state is Disabled")
        t.readln("  No port name")
        t.readln("GigabitEthernet1/2 is disabled, line protocol is down")
        t.readln("  Hardware is GigabitEthernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Member of VLAN 1 (untagged), port is in untagged mode, port state is Disabled")
        t.readln("  Port name is hello")
        t.readln("GigabitEthernet1/3 is down, line protocol is down")
        t.readln("  Hardware is GigabitEthernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Member of VLAN 1 (untagged), port is in untagged mode, port state is Disabled")
        t.readln("  No port name")
        t.readln("GigabitEthernet1/4 is disabled, line protocol is down")
        t.readln("  Hardware is GigabitEthernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Member of VLAN 1 (untagged), port is in untagged mode, port state is Disabled")
        t.readln("  No port name")
        t.readln("Ve1000 is down, line protocol is down")
        t.readln("  Hardware is Virtual Ethernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  Port name is Salut")
        t.readln("  Vlan id: 1000")
        t.readln("  Internet address is 0.0.0.0/0, IP MTU 1500 bytes, encapsulation ethernet")
        t.readln("Ve2000 is down, line protocol is down")
        t.readln("  Hardware is Virtual Ethernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
        t.readln("  No port name")
        t.readln("  Vlan id: 2000")
        t.readln("  Internet address is 1.1.1.1/24, IP MTU 1500 bytes, encapsulation ethernet")
        t.read("SSH@my_switch#")

        configuring_interface(t, "1/2", do="no port-name hello")
        configuring_interface(t, "1/3", do="disable")

        configuring(t, do="no interface ve 1000")
        configuring(t, do="no vlan 1000")

        configuring(t, do="no interface ve 2000")
        configuring(t, do="no vlan 2000")

        remove_vlan(t, "123")

    @with_protocol
    def test_show_vlan_brief(self, t):
        enable(t)
        create_vlan(t, "123")
        create_vlan(t, "3333", "some-name")
        create_vlan(t, "2222", "your-name-is-at-the-maxi-length")  # 31 on brocade

        set_interface_untagged_on_vlan(t, "ethe1/1", "123")

        t.write("show vlan brief")
        t.readln("")
        t.readln("VLAN     Name       Encap ESI                              Ve    Pri Ports")
        t.readln("----     ----       ----- ---                              ----- --- -----")
        t.readln(
            "1        DEFAULT-VL                                        -     -   Untagged Ports : ethe 1/2 to 1/4")
        t.readln("123      [None]                                            -     -   Untagged Ports : ethe 1/1")
        t.readln("2222     your-name-                                        -     -")
        t.readln("3333     some-name                                         -     -")
        t.read("SSH@my_switch#")

        remove_interface_from_vlan(t, "ethe1/1", "123")
        remove_vlan(t, "123")
        remove_vlan(t, "1234")
        remove_vlan(t, "5555")

    @with_protocol
    def test_show_running_config_vlan(self, t):
        enable(t)
        create_vlan(t, "123")
        create_vlan(t, "999")
        create_vlan(t, "888")

        configuring_vlan(t, "123", do="untagged ethernet 1/2")
        configuring_vlan(t, "888", do="tagged ethernet 1/2")
        configuring_vlan(t, "888", do="router-interface ve 1888")
        configuring_vlan(t, "999", do="tagged ethe1/2")
        configuring_vlan(t, "999", do="untagged ethe1/1")

        t.write("show running-config vlan")
        t.readln("spanning-tree")
        t.readln("!")
        t.readln("!")
        t.readln("vlan 1 name DEFAULT-VLAN")
        t.readln(" no untagged ethe 1/3 to 1/4")
        t.readln("!")
        t.readln("vlan 123")
        t.readln(" untagged ethe 1/2")
        t.readln("!")
        t.readln("vlan 888")
        t.readln(" tagged ethe 1/2")
        t.readln(" router-interface ve 1888")
        t.readln("!")
        t.readln("vlan 999")
        t.readln(" untagged ethe 1/1")
        t.readln(" tagged ethe 1/2")
        t.readln("!")
        t.readln("!")
        t.readln("")
        t.read("SSH@my_switch#")

        configuring(t, do="no interface ve 1888")
        configuring(t, do="no vlan 123")
        configuring(t, do="no vlan 888")
        configuring(t, do="no vlan 999")

    @with_protocol
    def test_shutting_down(self, t):
        enable(t)

        t.write("show run interface ethernet 1/3")
        t.readln("")
        t.read("SSH@my_switch#")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ethe1/3")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")
        t.write("enable")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        t.write("show run interface ethernet 1/3")
        t.readln("interface ethernet 1/3")
        t.readln(" enable")
        t.readln("!")
        t.readln("")
        t.read("SSH@my_switch#")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ethe1/3")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")
        t.write("disable")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        t.write("show run interface ethernet 1/3")
        t.readln("")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_setup_an_interface(self, t):
        enable(t)

        t.write("show run int ve 2999")
        t.readln("Error - ve 2999 was not configured")
        t.read("SSH@my_switch#")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 2999")
        t.readln("Error - invalid virtual ethernet interface number.")
        t.read("SSH@my_switch(config)#")
        t.write("vlan 2999")
        t.read("SSH@my_switch(config-vlan-2999)#")
        t.write("router interface ve 2999")
        t.readln("Invalid input -> interface ve 2999")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vlan-2999)#")
        t.write("rout patate 2999")
        t.readln("Invalid input -> patate 2999")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vlan-2999)#")
        t.write("router-interface ve 2999")
        t.read("SSH@my_switch(config-vlan-2999)#")
        t.write("router-interface ve 3000")
        t.readln("Error: VLAN: 2999  already has router-interface 2999")
        t.read("SSH@my_switch(config-vlan-2999)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        t.write("show running-config vlan | begin vlan 2999")
        t.readln("vlan 2999")
        t.readln(" router-interface ve 2999")
        t.readln("!")
        t.readln("!")
        t.readln("")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "ve 2999", [
            "interface ve 2999",
            "!"
        ])

        configuring_interface_vlan(t, "2999", do="port-name hey ho")
        configuring_interface_vlan(t, "2999", do="ip address 2.2.2.2/24")
        configuring_interface_vlan(t, "2999", do="ip address 1.1.1.1/24")

        assert_interface_configuration(t, "ve 2999", [
            "interface ve 2999",
            " port-name hey ho",
            " ip address 1.1.1.1/24",
            " ip address 2.2.2.2/24",
            "!"])

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 2999")
        t.read("SSH@my_switch(config-vif-2999)#")
        t.write("ip address 1.1.1.1/24")
        t.readln("IP/Port: Errno(6) Duplicate ip address")
        t.read("SSH@my_switch(config-vif-2999)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        configuring(t, do="no interface ve 2999")
        assert_interface_configuration(t, "ve 2999", [
            "interface ve 2999",
            "!"
        ])

        configuring_vlan(t, "2999", do="no router-interface 2999")
        t.write("show run int ve 2999")
        t.readln("Error - ve 2999 was not configured")
        t.read("SSH@my_switch#")

        configuring(t, do="no vlan 2999")

    @with_protocol
    def test_setting_access_group(self, t):
        enable(t)

        create_interface_vlan(t, "2999")
        configuring_access_group_interface_vlan(t, "2999", do="ip access-group SHNITZLE in")
        configuring_access_group_interface_vlan(t, "2999", do="ip access-group WHIZZLE out")

        assert_interface_configuration(t, "ve 2999", [
            "interface ve 2999",
            " ip access-group SHNITZLE in",
            " ip access-group WHIZZLE out",
            "!"])

        configuring_interface_vlan(t, "2999", do="no ip access-group WHIZZLE out")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 2999")
        t.read("SSH@my_switch(config-vif-2999)#")
        t.write("no ip access-group wat in")
        t.readln("Error: Wrong Access List Name wat")
        t.read("SSH@my_switch(config-vif-2999)#")
        t.write("no ip access-group out")
        t.readln("Error: Wrong Access List Name out")
        t.read("SSH@my_switch(config-vif-2999)#")
        t.write("no ip access-group gneh out")
        t.readln("Error: Wrong Access List Name gneh")
        t.read("SSH@my_switch(config-vif-2999)#")
        t.write("no ip access-group SHNITZLE in")
        t.read("SSH@my_switch(config-vif-2999)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "ve 2999", [
            "interface ve 2999",
            "!"])

        configuring(t, do="no interface ve 2999")
        configuring(t, do="no vlan 2999")

    @with_protocol
    def test_removing_ip_address(self, t):
        enable(t)

        create_interface_vlan(t, "2999")
        configuring_interface_vlan(t, "2999", do="ip address 2.2.2.2/24")

        assert_interface_configuration(t, "ve 2999", [
            "interface ve 2999",
            " ip address 2.2.2.2/24",
            "!"])

        configuring_interface_vlan(t, "2999", do="no ip address 2.2.2.2/24")

        assert_interface_configuration(t, "ve 2999", [
            "interface ve 2999",
            "!"])

        configuring(t, do="no interface ve 2999")
        configuring(t, do="no vlan 2999")

    @with_protocol
    def test_static_routes(self, t):
        enable(t)
        configuring(t, do="ip route 100.100.100.100 255.255.255.0 2.2.2.2")
        configuring(t, do="ip route 1.1.2.0 255.255.255.0 2.2.2.3")
        t.write("show ip route static")
        t.readln("        Destination        Gateway        Port          Cost          Type Uptime src-vrf")
        t.readln("1       100.100.100.100/24 2.2.2.2")
        t.readln("2       1.1.2.0/24         2.2.2.3")
        t.readln("")
        t.read("SSH@my_switch#")

        configuring(t, do="no ip route 100.100.100.100 255.255.255.0 2.2.2.2")

        t.write("show ip route static")
        t.readln("        Destination        Gateway        Port          Cost          Type Uptime src-vrf")
        t.readln("1       1.1.2.0/24         2.2.2.3")

    @with_protocol
    def test_show_all_interfaces_in_running(self, t):
        enable(t)

        create_interface_vlan(t, "2998")

        create_interface_vlan(t, "2999")
        configuring_interface_vlan(t, "2999", do="ip address 2.2.2.2/24")
        configuring_access_group_interface_vlan(t, "2999", do="ip access-group SHNITZLE in")
        configuring_access_group_interface_vlan(t, "2999", do="ip access-group WHIZZLE out")

        create_interface_vlan(t, "3000")
        configuring_interface_vlan(t, "3000", do="port-name howdy")

        configuring_interface(t, "1/1", do="port-name one one")
        configuring_interface(t, "1/3", do="port-name one three")
        configuring_interface(t, "1/3", do="enable")
        configuring_interface(t, "1/4", do="enable")

        t.write("show running-config interface")
        t.readln("interface ethernet 1/1")
        t.readln(" port-name one one")
        t.readln("!")
        t.readln("interface ethernet 1/3")
        t.readln(" port-name one three")
        t.readln(" enable")
        t.readln("!")
        t.readln("interface ethernet 1/4")
        t.readln(" enable")
        t.readln("!")
        t.readln("interface ve 2998")
        t.readln("!")
        t.readln("interface ve 2999")
        t.readln(" ip address 2.2.2.2/24")
        t.readln(" ip access-group SHNITZLE in")
        t.readln(" ip access-group WHIZZLE out")
        t.readln("!")
        t.readln("interface ve 3000")
        t.readln(" port-name howdy")
        t.readln("!")
        t.readln("")
        t.read("SSH@my_switch#")

        configuring(t, do="no interface ve 2998")
        configuring(t, do="no vlan 2998")
        configuring(t, do="no interface ve 2999")
        configuring(t, do="no vlan 2999")
        configuring(t, do="no interface ve 3000")
        configuring(t, do="no vlan 3000")

        configuring_interface(t, "1/1", do="no port-name")
        configuring_interface(t, "1/3", do="no port-name")
        configuring_interface(t, "1/3", do="disable")
        
        configuring(t, do="no interface ethernet 1/4")

        t.write("show running-config interface")
        t.readln("")
        t.read("SSH@my_switch#")


    @with_protocol
    def test_configuring_no_interface_does_not_remove_interfaces_from_vlans(self, t):
        enable(t)

        create_vlan(t, "3000")
        configuring_vlan(t, "3000", do="untagged ethernet 1/1")
        configuring_vlan(t, "3000", do="tagged ethernet 1/2")

        create_vlan(t, "3001")
        configuring_vlan(t, "3001", do="untagged ethernet 1/3")

        configuring(t, do="no interface ethernet 1/1")
        configuring(t, do="no interface ethernet 1/2")

        t.write("show running-config vlan | begin vlan 3000")
        t.readln("vlan 3000")
        t.readln(" untagged ethe 1/1")
        t.readln(" tagged ethe 1/2")
        t.readln("!")
        t.readln("vlan 3001")
        t.readln(" untagged ethe 1/3")
        t.readln("!")

        t.readln("!")
        t.readln("")
        t.read("SSH@my_switch#")

        configuring(t, do="no vlan 3000")
        configuring(t, do="no vlan 3001")


    @with_protocol
    def test_overlapping_and_secondary_ips(self, t):
        enable(t)

        create_interface_vlan(t, "1000")
        create_interface_vlan(t, "2000")

        configuring_interface_vlan(t, "1000", do="ip address 2.2.2.2/24")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 2000")
        t.read("SSH@my_switch(config-vif-2000)#")

        t.write("ip address 2.2.2.75/25")
        t.readln("IP/Port: Errno(11) ip subnet overlap with another interface")

        t.read("SSH@my_switch(config-vif-2000)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")

        t.write("interface ve 1000")
        t.read("SSH@my_switch(config-vif-1000)#")

        t.write("ip address 2.2.2.4/24")
        t.readln("IP/Port: Errno(15) Can only assign one primary ip address per subnet")
        t.read("SSH@my_switch(config-vif-1000)#")

        t.write("ip address 2.2.2.5/25 secondary")
        t.read("SSH@my_switch(config-vif-1000)#")
        t.write("ip address 2.2.2.87/30 secondary")
        t.read("SSH@my_switch(config-vif-1000)#")
        t.write("ip address 2.2.2.72/29 secondary")
        t.read("SSH@my_switch(config-vif-1000)#")

        t.write("no ip address 2.2.2.2/24")
        t.readln("IP/Port: Errno(18) Delete secondary address before deleting primary address")
        t.read("SSH@my_switch(config-vif-1000)#")

        t.write("no ip address 2.2.2.5/25")
        t.read("SSH@my_switch(config-vif-1000)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "ve 1000", [
            "interface ve 1000",
            " ip address 2.2.2.2/24",
            " ip address 2.2.2.72/29 secondary",
            " ip address 2.2.2.87/30 secondary",
            "!"])

        configuring(t, do="no interface ve 2000")
        configuring(t, do="no vlan 2000")
        configuring(t, do="no interface ve 1000")
        configuring(t, do="no vlan 1000")

    @with_protocol
    def test_multiple_secondary_are_listed_at_the_end(self, t):
        enable(t)

        create_interface_vlan(t, "1000")

        configuring_interface_vlan(t, "1000", do="ip address 2.2.2.2/24")
        configuring_interface_vlan(t, "1000", do="ip address 2.2.2.3/24 secondary")

        configuring_interface_vlan(t, "1000", do="ip address 1.2.2.2/24")
        configuring_interface_vlan(t, "1000", do="ip address 1.2.2.3/24 secondary")

        assert_interface_configuration(t, "ve 1000", [
            "interface ve 1000",
            " ip address 1.2.2.2/24",
            " ip address 2.2.2.2/24",
            " ip address 1.2.2.3/24 secondary",
            " ip address 2.2.2.3/24 secondary",
            "!"])

        configuring(t, do="no interface ve 1000")
        configuring(t, do="no vlan 1000")

    @with_protocol
    def test_ip_vrf(self, t):
        enable(t)

        t.write("conf t")
        t.read("SSH@my_switch(config)#")
        t.write("ip vrf SOME-LAN")
        t.read("SSH@my_switch(config-vrf-SOME-LAN)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("no ip vrf SOME-LAN")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_ip_vrf_forwarding(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("ip vrf SOME-LAN")
        t.read("SSH@my_switch(config-vrf-SOME-LAN)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethe 1/3")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")
        t.write("vrf forwarding NOT-DEFAULT-LAN")
        t.readln("Error - VRF(NOT-DEFAULT-LAN) does not exist or Route-Distinguisher not specified or Address Family not configured")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")

        t.write("vrf forwarding SOME-LAN")
        t.readln("Warning: All IPv4 and IPv6 addresses (including link-local) on this interface have been removed")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")

        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "ethernet 1/3", [
            "interface ethernet 1/3",
            " vrf forwarding SOME-LAN",
            "!"])

        t.write("conf t")
        t.read("SSH@my_switch(config)#")
        t.write("no ip vrf SOME-LAN")
        t.read("SSH@my_switch(config)#")

        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "ethernet 1/3", [])

    @with_protocol
    def test_ip_vrf_default_lan(self, t):
        enable(t)

        t.write("conf t")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethe 1/3")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")
        t.write("vrf forwarding DEFAULT-LAN")
        t.readln("Warning: All IPv4 and IPv6 addresses (including link-local) on this interface have been removed")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")

        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "ethernet 1/3", [
            "interface ethernet 1/3",
            " vrf forwarding DEFAULT-LAN",
            "!"])

        t.write("conf t")
        t.read("SSH@my_switch(config)#")
        t.write("interface ethe 1/3")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")
        t.write("no vrf forwarding DEFAULT-LAN")
        t.readln("Warning: All IPv4 and IPv6 addresses (including link-local) on this interface have been removed")
        t.read("SSH@my_switch(config-if-e1000-1/3)#")

        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "ethernet 1/3", [])

    @with_protocol
    def test_ip_setting_vrf_forwarding_wipes_ip_addresses(self, t):
        enable(t)

        create_vlan(t, "4000")
        create_interface_vlan(t, "4000")
        configuring_interface_vlan(t, "4000", do="ip address 10.10.0.10/24")
        configuring_interface_vlan(t, "4000", do="ip address 10.10.1.10/24")

        assert_interface_configuration(t, "Vlan4000", [
            "interface ve 4000",
            " ip address 10.10.0.10/24",
            " ip address 10.10.1.10/24",
            "!"])

        t.write("conf t")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 4000")
        t.read("SSH@my_switch(config-vif-4000)#")
        t.write("vrf forwarding DEFAULT-LAN")
        t.readln("Warning: All IPv4 and IPv6 addresses (including link-local) on this interface have been removed")
        t.read("SSH@my_switch(config-vif-4000)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "Vlan4000", [
            "interface ve 4000",
            " vrf forwarding DEFAULT-LAN",
            "!"])

        configuring_interface_vlan(t, "4000", do="ip address 10.10.0.10/24")
        configuring_interface_vlan(t, "4000", do="ip address 10.10.1.10/24")

        t.write("conf t")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 4000")
        t.read("SSH@my_switch(config-vif-4000)#")
        t.write("no vrf forwarding")
        t.readln("Incomplete command.")
        t.read("SSH@my_switch(config-vif-4000)#")
        t.write("no vrf forwarding DEFAULT-LAN")
        t.readln("Warning: All IPv4 and IPv6 addresses (including link-local) on this interface have been removed")
        t.read("SSH@my_switch(config-vif-4000)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "Vlan4000", [
            "interface ve 4000",
            "!"])

        configuring(t, do="no interface ve 4000")
        configuring(t, do="no vlan 4000")

    @with_protocol
    def test_extreme_vlan_ranges(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")

        t.write("vlan -1")
        t.readln("Invalid input -> -1")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config)#")

        t.write("vlan 0")
        t.readln("Error: vlan ID value 0 not allowed.")
        t.read("SSH@my_switch(config)#")

        t.write("vlan 1")
        t.read("SSH@my_switch(config-vlan-1)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")

        t.write("vlan 4090")
        t.read("SSH@my_switch(config-vlan-4090)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("no vlan 4090")
        t.read("SSH@my_switch(config)#")

        t.write("vlan 4091")
        t.readln("Error: vlan id 4091 is outside of allowed max of 4090")
        t.read("SSH@my_switch(config)#")

        t.write("exit")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_show_vlan_ethernet_shows_all_vlans_on_an_interface(self, t):
        enable(t)

        t.write("show vlan ethe1/78")
        t.readln("Invalid input -> ethe1/78")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch#")

        t.write("show vlan ethe 1/78")
        t.readln("Invalid input -> 1/78")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch#")

        t.write("show vlan ethe 1/2")
        t.readln("VLAN: 1  Untagged")
        t.read("SSH@my_switch#")

        create_vlan(t, "1001")
        create_vlan(t, "1002")
        create_vlan(t, "1003")
        create_vlan(t, "1004")
        create_vlan(t, "1005")

        configuring_vlan(t, "1002", do="tagged ethe1/2")

        t.write("show vlan ethe 1/2")
        t.readln("VLAN: 1002  Tagged")
        t.read("SSH@my_switch#")

        configuring_vlan(t, "1003", do="untagged ethe1/2")

        configuring_vlan(t, "1001", do="tagged ethe1/2")
        configuring_vlan(t, "1002", do="tagged ethe1/2")
        configuring_vlan(t, "1004", do="tagged ethe1/2")

        configuring_vlan(t, "1005", do="tagged ethe1/3")

        t.write("show vlan ethe 1/2")
        t.readln("VLAN: 1001  Tagged")
        t.readln("VLAN: 1002  Tagged")
        t.readln("VLAN: 1003  Untagged")
        t.readln("VLAN: 1004  Tagged")
        t.read("SSH@my_switch#")

        configuring_vlan(t, "1001", do="no tagged ethe1/2")
        configuring_vlan(t, "1002", do="no tagged ethe1/2")
        configuring_vlan(t, "1004", do="no tagged ethe1/2")

        configuring_vlan(t, "1005", do="no tagged ethe1/3")

        t.write("show vlan ethe 1/2")
        t.readln("VLAN: 1003  Untagged")
        t.read("SSH@my_switch#")

        configuring_vlan(t, "1003", do="no untagged ethe1/2")

        t.write("show vlan ethe 1/2")
        t.readln("VLAN: 1  Untagged")
        t.read("SSH@my_switch#")

        configuring(t, do="no vlan 1001")
        configuring(t, do="no vlan 1002")
        configuring(t, do="no vlan 1003")
        configuring(t, do="no vlan 1004")
        configuring(t, do="no vlan 1005")

    @with_protocol
    def test_unknown_interface_shows_an_error(self, t):
        enable(t)

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")

        t.write("interface ethernet 909/99")
        t.readln("Invalid input -> 909/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config)#")

        t.write("exit")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_tagging_or_untagging_an_unknown_interface_shows_an_error(self, t):
        enable(t)

        create_vlan(t, "1000")

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("vlan 1000")
        t.read("SSH@my_switch(config-vlan-1000)#")

        t.write("tagged ethernet 999/99")
        t.readln("Invalid input -> 999/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vlan-1000)#")

        t.write("untagged ethernet 999/99")
        t.readln("Invalid input -> 999/99")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vlan-1000)#")

        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        configuring(t, do="no vlan 1000")

    @with_protocol
    def test_write_memory(self, t):
        enable(t)

        t.write("write memory")
        t.read("SSH@my_switch#")

    @with_protocol
    def test_vrrp(self, t):
        enable(t)
        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("vlan 2995 name HELLO_VLAN")
        t.read("SSH@my_switch(config-vlan-2995)#")
        t.write("tagged ethernet 1/1")
        t.read("SSH@my_switch(config-vlan-2995)#")
        t.write("router-interface ve 2995 ")
        t.read("SSH@my_switch(config-vlan-2995)#")
        t.write("interface ve 2995")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("ip address 10.0.0.2/29")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("ip vrrp-extended vrid 1")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("backup priority 160 track-priority 13")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("ip-address 10.0.0.1")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("ip-address 10.0.0.3")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("ip-address 10.0.0.4")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("hello-interval 5")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("dead-interval 15")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("advertise backup")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("track-port ethernet 2/4")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("backup priority 110 track-priority 50")
        t.read("SSH@my_switch(config-vif-2995-vrid-1)#")
        t.write("activate")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("ip vrrp-extended vrid 2")
        t.read("SSH@my_switch(config-vif-2995-vrid-2)#")
        t.write("exit")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("ip vrrp-extended auth-type simple-text-auth ABCD")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            " ip address 10.0.0.2/29",
            " ip vrrp-extended auth-type simple-text-auth ********",
            " ip vrrp-extended vrid 1",
            "  backup priority 110 track-priority 50",
            "  ip-address 10.0.0.1",
            "  ip-address 10.0.0.3",
            "  ip-address 10.0.0.4",
            "  advertise backup",
            "  dead-interval 15",
            "  hello-interval 5",
            "  track-port ethernet 2/4",
            "  activate",
            " ip vrrp-extended vrid 2",
            "  exit",
            "!"])

        configuring_interface_vlan_vrrp(t, 2995, 1, "no advertise backup")
        configuring_interface_vlan_vrrp(t, 2995, 1, "no ip-address 10.0.0.1")
        configuring_interface_vlan_vrrp(t, 2995, 1, "no ip-address 10.0.0.3")
        configuring_interface_vlan_vrrp(t, 2995, 1, "no ip-address 10.0.0.4")
        configuring_interface_vlan_vrrp(t, 2995, 1, "no activate")
        configuring_interface_vlan_vrrp(t, 2995, 1, "no dead-interval 15")
        configuring_interface_vlan_vrrp(t, 2995, 1, "no hello-interval 5")
        configuring_interface_vlan_vrrp(t, 2995, 1, "no track-port ethernet 2/4")
        configuring_interface_vlan_vrrp(t, 2995, 1, "no backup")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            " ip address 10.0.0.2/29",
            " ip vrrp-extended auth-type simple-text-auth ********",
            " ip vrrp-extended vrid 1",
            "  exit",
            " ip vrrp-extended vrid 2",
            "  exit",
            "!"])

        configuring_interface_vlan(t, 2995, "no ip vrrp-extended vrid 1")
        configuring_interface_vlan(t, 2995, "no ip vrrp-extended vrid 2")
        configuring_interface_vlan(t, 2995, "no ip address 10.0.0.2/29")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            " ip vrrp-extended auth-type simple-text-auth ********",
            "!"])

        configuring_interface_vlan(t, 2995, "no ip vrrp-extended auth-type simple-text-auth ABC")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            "!"])

        configuring(t, do="no interface ve 2995")
        remove_vlan(t, "2995")

    @with_protocol
    def test_ip_helper(self, t):
        enable(t)

        create_vlan(t, "2995")
        create_interface_vlan(t, "2995")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            "!"])

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 2995")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("ip helper-address")
        t.readln("Incomplete command.")
        t.read("SSH@my_switch(config-vif-2995)#")

        t.write("ip helper-address 10.10.0.1 EXTRA INFO")
        t.readln("Invalid input -> EXTRA INFO")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        configuring_interface_vlan(t, vlan="2995", do="ip helper-address 10.10.0.1")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            " ip helper-address 10.10.0.1",
            "!"])

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 2995")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("ip helper-address 10.10.0.1")
        t.readln("UDP: Errno(7) Duplicate helper address")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        configuring_interface_vlan(t, vlan="2995", do="ip helper-address 10.10.0.2")
        configuring_interface_vlan(t, vlan="2995", do="ip helper-address 10.10.0.3")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            " ip helper-address 10.10.0.1",
            " ip helper-address 10.10.0.2",
            " ip helper-address 10.10.0.3",
            "!"])

        configuring_interface_vlan(t, vlan="2995", do="no ip helper-address 10.10.0.1")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            " ip helper-address 10.10.0.2",
            " ip helper-address 10.10.0.3",
            "!"])

        t.write("configure terminal")
        t.read("SSH@my_switch(config)#")
        t.write("interface ve 2995")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("no ip helper-address")
        t.readln("Incomplete command.")
        t.read("SSH@my_switch(config-vif-2995)#")

        t.write("no ip helper-address 10.10.0.1")
        t.readln("UDP: Errno(10) Helper address not configured")
        t.read("SSH@my_switch(config-vif-2995)#")

        t.write("no ip helper-address 10.10.0.2 EXTRA INFO")
        t.readln("Invalid input -> EXTRA INFO")
        t.readln("Type ? for a list")
        t.read("SSH@my_switch(config-vif-2995)#")
        t.write("exit")
        t.read("SSH@my_switch(config)#")
        t.write("exit")
        t.read("SSH@my_switch#")

        configuring_interface_vlan(t, vlan="2995", do="no ip helper-address 10.10.0.2")
        configuring_interface_vlan(t, vlan="2995", do="no ip helper-address 10.10.0.3")

        assert_interface_configuration(t, "ve 2995", [
            "interface ve 2995",
            "!"])

        configuring(t, do="no interface ve 2995")
        remove_vlan(t, "2995")

    @with_protocol
    def test_show_vlan(self, t):
        enable(t)

        t.write("show vlan 1600")
        t.readln("Error: vlan 1600 is not configured")
        t.read("SSH@my_switch#")

        create_vlan(t, "1600")

        t.write("show vlan 1600")
        t.readln("")
        t.readln("PORT-VLAN 1600, Name [None], Priority Level -, Priority Force 0, Creation Type STATIC")
        t.readln("Topo HW idx    : 81    Topo SW idx: 257    Topo next vlan: 0")
        t.readln("L2 protocols   : STP")
        t.readln("Associated Virtual Interface Id: NONE")
        t.readln("----------------------------------------------------------")
        t.readln("No ports associated with VLAN")
        t.readln("Arp Inspection: 0")
        t.readln("DHCP Snooping: 0")
        t.readln("IPv4 Multicast Snooping: Disabled")
        t.readln("IPv6 Multicast Snooping: Disabled")
        t.readln("")
        t.readln("No Virtual Interfaces configured for this vlan")
        t.read("SSH@my_switch#")

        create_vlan(t, "1600", name="Shizzle")
        configuring_vlan(t, "1600", do="router-interface ve 999")

        t.write("show vlan 1600")
        t.readln("")
        t.readln("PORT-VLAN 1600, Name Shizzle, Priority Level -, Priority Force 0, Creation Type STATIC")
        t.readln("Topo HW idx    : 81    Topo SW idx: 257    Topo next vlan: 0")
        t.readln("L2 protocols   : STP")
        t.readln("Associated Virtual Interface Id: 999")
        t.readln("----------------------------------------------------------")
        t.readln("No ports associated with VLAN")
        t.readln("Arp Inspection: 0")
        t.readln("DHCP Snooping: 0")
        t.readln("IPv4 Multicast Snooping: Disabled")
        t.readln("IPv6 Multicast Snooping: Disabled")
        t.readln("")
        t.readln("Ve999 is down, line protocol is down")
        t.readln("  Type is Vlan (Vlan Id: 1600)")
        t.readln("  Hardware is Virtual Ethernet, address is 748e.f8a7.1b01 (bia 748e.f8a7.1b01)")
        t.readln("  No port name")
        t.readln("  Vlan id: 1600")
        t.readln("  Internet address is 0.0.0.0/0, IP MTU 1500 bytes, encapsulation ethernet")
        t.readln("  Configured BW 0 kbps")
        t.read("SSH@my_switch#")

        configuring_vlan(t, "1600", do="no router-interface 999")
        remove_vlan(t, "1600")

    @with_protocol
    def test_show_vlan_has_tagged_untagged_ports(self, t):
        enable(t)
        create_vlan(t, "1600")
        set_interface_untagged_on_vlan(t, "ethernet 1/2", "1600")

        t.write("show vlan 1600")
        t.readln("")
        t.readln("PORT-VLAN 1600, Name [None], Priority Level -, Priority Force 0, Creation Type STATIC")
        t.readln("Topo HW idx    : 81    Topo SW idx: 257    Topo next vlan: 0")
        t.readln("L2 protocols   : STP")
        t.readln("Untagged Ports : ethe 1/2")
        t.readln("Associated Virtual Interface Id: NONE")
        t.readln("----------------------------------------------------------")
        t.readln("Port  Type      Tag-Mode  Protocol  State")
        t.readln("1/2   PHYSICAL  UNTAGGED  STP       DISABLED")
        t.readln("Arp Inspection: 0")
        t.readln("DHCP Snooping: 0")
        t.readln("IPv4 Multicast Snooping: Disabled")
        t.readln("IPv6 Multicast Snooping: Disabled")
        t.readln("")
        t.readln("No Virtual Interfaces configured for this vlan")
        t.read("SSH@my_switch#")

        set_interface_tagged_on_vlan(t, "ethernet 1/4", "1600")

        t.write("show vlan 1600")
        t.readln("")
        t.readln("PORT-VLAN 1600, Name [None], Priority Level -, Priority Force 0, Creation Type STATIC")
        t.readln("Topo HW idx    : 81    Topo SW idx: 257    Topo next vlan: 0")
        t.readln("L2 protocols   : STP")
        t.readln("Statically tagged Ports    : ethe 1/4")
        t.readln("Untagged Ports : ethe 1/2")
        t.readln("Associated Virtual Interface Id: NONE")
        t.readln("----------------------------------------------------------")
        t.readln("Port  Type      Tag-Mode  Protocol  State")
        t.readln("1/2   PHYSICAL  UNTAGGED  STP       DISABLED")
        t.readln("1/4   PHYSICAL  TAGGED    STP       DISABLED")
        t.readln("Arp Inspection: 0")
        t.readln("DHCP Snooping: 0")
        t.readln("IPv4 Multicast Snooping: Disabled")
        t.readln("IPv6 Multicast Snooping: Disabled")
        t.readln("")
        t.readln("No Virtual Interfaces configured for this vlan")
        t.read("SSH@my_switch#")

        set_interface_tagged_on_vlan(t, "ethernet 1/3", "1600")

        t.write("show vlan 1600")
        t.readln("")
        t.readln("PORT-VLAN 1600, Name [None], Priority Level -, Priority Force 0, Creation Type STATIC")
        t.readln("Topo HW idx    : 81    Topo SW idx: 257    Topo next vlan: 0")
        t.readln("L2 protocols   : STP")
        t.readln("Statically tagged Ports    : ethe 1/3 to 1/4")
        t.readln("Untagged Ports : ethe 1/2")
        t.readln("Associated Virtual Interface Id: NONE")
        t.readln("----------------------------------------------------------")
        t.readln("Port  Type      Tag-Mode  Protocol  State")
        t.readln("1/2   PHYSICAL  UNTAGGED  STP       DISABLED")
        t.readln("1/3   PHYSICAL  TAGGED    STP       DISABLED")
        t.readln("1/4   PHYSICAL  TAGGED    STP       DISABLED")
        t.readln("Arp Inspection: 0")
        t.readln("DHCP Snooping: 0")
        t.readln("IPv4 Multicast Snooping: Disabled")
        t.readln("IPv6 Multicast Snooping: Disabled")
        t.readln("")
        t.readln("No Virtual Interfaces configured for this vlan")
        t.read("SSH@my_switch#")

        unset_interface_untagged_on_vlan(t, "ethernet 1/2", "1600")
        unset_interface_tagged_on_vlan(t, "ethernet 1/3", "1600")
        unset_interface_tagged_on_vlan(t, "ethernet 1/4", "1600")
        remove_vlan(t, "1600")

    @with_protocol
    def test_show_version(self, t):
        enable(t)

        t.write("show version")

        t.readln("System: NetIron CER (Serial #: 1P2539K036,  Part #: 40-1000617-02)")
        t.readln("License: RT_SCALE, ADV_SVCS_PREM (LID: XXXXXXXXXX)")
        t.readln("Boot     : Version 5.8.0T185 Copyright (c) 1996-2014 Brocade Communications Systems, Inc.")
        t.readln("Compiled on May 18 2015 at 13:03:00 labeled as ceb05800")
        t.readln(" (463847 bytes) from boot flash")
        t.readln("Monitor  : Version 5.8.0T185 Copyright (c) 1996-2014 Brocade Communications Systems, Inc.")
        t.readln("Compiled on May 18 2015 at 13:03:00 labeled as ceb05800")
        t.readln(" (463847 bytes) from code flash")
        t.readln("IronWare : Version 5.8.0bT183 Copyright (c) 1996-2014 Brocade Communications Systems, Inc.")
        t.readln("Compiled on May 21 2015 at 09:20:22 labeled as ce05800b")
        t.readln(" (17563175 bytes) from Primary")
        t.readln("CPLD Version: 0x00000010")
        t.readln("Micro-Controller Version: 0x0000000d")
        t.readln("Extended route scalability")
        t.readln("PBIF Version: 0x0162")
        t.readln("800 MHz Power PC processor 8544 (version 8021/0023) 400 MHz bus")
        t.readln("512 KB Boot Flash (MX29LV040C), 64 MB Code Flash (MT28F256J3)")
        t.readln("2048 MB DRAM")
        t.readln("System uptime is 109 days 4 hours 39 minutes 4 seconds")

        t.read("SSH@my_switch#")

    @with_protocol
    def test_ip_redirect(self, t):
        enable(t)

        create_interface_vlan(t, "1201")
        configuring_interface_vlan(t, "1201", do="no ip redirect")

        assert_interface_configuration(t, "ve 1201", [
            "interface ve 1201",
            " no ip redirect",
            "!"
        ])

        configuring_interface_vlan(t, "1201", do="ip redirect")

        assert_interface_configuration(t, "ve 1201", [
            "interface ve 1201",
            "!"
        ])

        remove_vlan(t, "1201")


def enable(t):
    t.write("enable")
    t.read("Password:")
    t.write_invisible(t.conf["extra"].get("password", "root"))
    t.read("SSH@my_switch#")


def create_vlan(t, vlan, name=None):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    if name:
        t.write("vlan {} name {}".format(vlan, name))
        t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    else:
        t.write("vlan {}".format(vlan))
        t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def remove_vlan(t, vlan):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("no vlan {}".format(vlan))
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def set_interface_untagged_on_vlan(t, interface, vlan):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("vlan {}".format(vlan))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("untagged {}".format(interface))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def unset_interface_untagged_on_vlan(t, interface, vlan):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("vlan {}".format(vlan))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("no untagged {}".format(interface))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def set_interface_tagged_on_vlan(t, interface, vlan):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("vlan {}".format(vlan))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("tagged {}".format(interface))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def unset_interface_tagged_on_vlan(t, interface, vlan):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("vlan {}".format(vlan))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("no tagged {}".format(interface))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def remove_interface_from_vlan(t, interface, vlan):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("vlan {}".format(vlan))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("no untagged {}".format(interface))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def assert_interface_configuration(t, interface, config):
    t.write("show running-config interface {} ".format(interface))
    for line in config:
        t.readln(line)
    t.readln("")
    t.read("SSH@my_switch#")


def configuring_interface(t, interface, do):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("interface ethe {}".format(interface))
    t.read("SSH@my_switch(config-if-e1000-{})#".format(interface))

    t.write(do)

    t.read("SSH@my_switch(config-if-e1000-{})#".format(interface))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def configuring_interface_vlan(t, vlan, do):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("interface ve {}".format(vlan))
    t.read("SSH@my_switch(config-vif-{})#".format(vlan))

    t.write(do)

    t.read("SSH@my_switch(config-vif-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def configuring_access_group_interface_vlan(t, vlan, do):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("interface ve {}".format(vlan))
    t.read("SSH@my_switch(config-vif-{})#".format(vlan))

    t.write(do)

    t.readln("Warning: An undefined or zero length ACL has been applied. "
             "Filtering will not occur for the specified interface VE {} (outbound).".format(vlan))
    t.read("SSH@my_switch(config-vif-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def configuring_interface_vlan_vrrp(t, vlan, group, do):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("interface ve {}".format(vlan))
    t.read("SSH@my_switch(config-vif-{})#".format(vlan))
    t.write("ip vrrp vrid {}".format(group))
    t.read("SSH@my_switch(config-vif-{}-vrid-{})#".format(vlan, group))

    t.write(do)

    t.read("SSH@my_switch(config-vif-{}-vrid-{})#".format(vlan, group))
    t.write("exit")
    t.read("SSH@my_switch(config-vif-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def configuring_vlan(t, vlan, do):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("vlan {}".format(vlan))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))

    t.write(do)

    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def configuring(t, do):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")

    t.write(do)

    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")


def create_interface_vlan(t, vlan):
    t.write("configure terminal")
    t.read("SSH@my_switch(config)#")
    t.write("vlan {}".format(vlan))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("router-interface ve {}".format(vlan))
    t.read("SSH@my_switch(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("SSH@my_switch(config)#")
    t.write("exit")
    t.read("SSH@my_switch#")
