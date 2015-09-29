import unittest

from flexmock import flexmock_teardown
import mock

from tests.util.global_reactor import cisco_privileged_password
from tests.util.global_reactor import cisco_switch_ssh_port, cisco_switch_telnet_port, cisco_switch_ip
from tests.util.protocol_util import SshTester, TelnetTester, with_protocol


class TestCiscoSwitchProtocol(unittest.TestCase):
    __test__ = False

    def create_client(self):
        raise NotImplemented()

    def setUp(self):
        self.protocol = self.create_client()

    def tearDown(self):
        flexmock_teardown()

    @with_protocol
    def test_enable_command_requires_a_password(self, t):
        t.write("enable")
        t.read("Password: ")
        t.write_invisible(cisco_privileged_password)
        t.read("my_switch#")

    @with_protocol
    def test_wrong_password(self, t):
        t.write("enable")
        t.read("Password: ")
        t.write_invisible("hello_world")
        t.readln("% Access denied")
        t.readln("")
        t.read("my_switch>")

    @with_protocol
    def test_no_password_works_for_legacy_reasons(self, t):
        t.write("enable")
        t.read("Password: ")
        t.write_invisible("")
        t.read("my_switch#")

    @with_protocol
    def test_exiting_loses_the_connection(self, t):
        t.write("enable")
        t.read("Password: ")
        t.write_invisible(cisco_privileged_password)
        t.read("my_switch#")
        t.write("exit")
        t.read_eof()

    @with_protocol
    def test_no_such_command_return_to_prompt(self, t):
        enable(t)

        t.write("shizzle")
        t.readln("No such command : shizzle")
        t.read("my_switch#")

    @with_protocol
    @mock.patch("fake_switches.adapters.tftp_reader.read_tftp")
    def test_command_copy_failing(self, t, read_tftp):
        read_tftp.side_effect = Exception("Stuff")

        enable(t)

        t.write("copy tftp://1.2.3.4/my-file system:/running-config")
        t.read("Destination filename [running-config]? ")
        t.write("gneh")
        t.readln("Accessing tftp://1.2.3.4/my-file...")
        t.readln("Error opening tftp://1.2.3.4/my-file (Timed out)")
        t.read("my_switch#")

        read_tftp.assert_called_with("1.2.3.4", "my-file")

    @with_protocol
    @mock.patch("fake_switches.adapters.tftp_reader.read_tftp")
    def test_command_copy_success(self, t, read_tftp):
        enable(t)

        t.write("copy tftp://1.2.3.4/my-file system:/running-config")
        t.read("Destination filename [running-config]? ")
        t.write_raw("\r")
        t.wait_for("\r\n")
        t.readln("Accessing tftp://1.2.3.4/my-file...")
        t.readln("Done (or some official message...)")
        t.read("my_switch#")

        read_tftp.assert_called_with("1.2.3.4", "my-file")

    @with_protocol
    def test_command_show_run_int_vlan_empty(self, t):
        enable(t)

        t.write("terminal length 0")
        t.read("my_switch#")
        t.write("show run vlan 120")
        t.readln("Building configuration...")
        t.readln("")
        t.readln("Current configuration:")
        t.readln("end")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_command_add_vlan(self, t):
        enable(t)

        t.write("conf t")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("vlan 123")
        t.read("my_switch(config-vlan)#")
        t.write("name shizzle")
        t.read("my_switch(config-vlan)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")
        t.write("show run vlan 123")
        t.readln("Building configuration...")
        t.readln("")
        t.readln("Current configuration:")
        t.readln("!")
        t.readln("vlan 123")
        t.readln(" name shizzle")
        t.readln("end")
        t.readln("")
        t.read("my_switch#")

        remove_vlan(t, "123")

        t.write("show running-config vlan 123")
        t.readln("Building configuration...")
        t.readln("")
        t.readln("Current configuration:")
        t.readln("end")
        t.read("")

    @with_protocol
    def test_command_assign_access_vlan_to_port(self, t):
        enable(t)
        create_vlan(t, "123")
        set_interface_on_vlan(t, "FastEthernet0/1", "123")

        assert_interface_configuration(t, "Fa0/1", [
            "interface FastEthernet0/1",
            " switchport access vlan 123",
            " switchport mode access",
            "end"])

        configuring_interface(t, "FastEthernet0/1", do="no switchport access vlan")

        assert_interface_configuration(t, "Fa0/1", [
            "interface FastEthernet0/1",
            " switchport mode access",
            "end"])

        configuring_interface(t, "FastEthernet0/1", do="no switchport mode access")

        assert_interface_configuration(t, "Fa0/1", [
            "interface FastEthernet0/1",
            "end"])

        remove_vlan(t, "123")

    @with_protocol
    def test_show_vlan_brief(self, t):
        enable(t)
        create_vlan(t, "123")
        create_vlan(t, "3333", "some-name")
        create_vlan(t, "2222", "your-name-is-way-too-long-for-this-pretty-printed-interface-man")

        set_interface_on_vlan(t, "FastEthernet0/1", "123")

        t.write("show vlan brief")
        t.readln("")
        t.readln("VLAN Name                             Status    Ports")
        t.readln("---- -------------------------------- --------- -------------------------------")
        t.readln("1    default                          active    Fa0/2, Fa0/3, Fa0/4")
        t.readln("123  VLAN123                          active    Fa0/1")
        t.readln("2222 your-name-is-way-too-long-for-th active")
        t.readln("3333 some-name                        active")
        t.read("my_switch#")

        revert_switchport_mode_access(t, "FastEthernet0/1")
        remove_vlan(t, "123")
        remove_vlan(t, "2222")
        remove_vlan(t, "3333")

    @with_protocol
    def test_show_vlan(self, t):
        enable(t)
        create_vlan(t, "123")
        create_vlan(t, "3333", "some-name")
        create_vlan(t, "2222", "your-name-is-way-too-long-for-this-pretty-printed-interface-man")

        set_interface_on_vlan(t, "FastEthernet0/1", "123")

        t.write("show vlan")
        t.readln("")
        t.readln("VLAN Name                             Status    Ports")
        t.readln("---- -------------------------------- --------- -------------------------------")
        t.readln("1    default                          active    Fa0/2, Fa0/3, Fa0/4")
        t.readln("123  VLAN123                          active    Fa0/1")
        t.readln("2222 your-name-is-way-too-long-for-th active")
        t.readln("3333 some-name                        active")
        t.readln("")
        t.readln("VLAN Type  SAID       MTU   Parent RingNo BridgeNo Stp  BrdgMode Trans1 Trans2")
        t.readln("---- ----- ---------- ----- ------ ------ -------- ---- -------- ------ ------")
        t.readln("1    enet  100001     1500  -      -      -        -    -        0      0")
        t.readln("123  enet  100123     1500  -      -      -        -    -        0      0")
        t.readln("2222 enet  102222     1500  -      -      -        -    -        0      0")
        t.readln("3333 enet  103333     1500  -      -      -        -    -        0      0")
        t.readln("")
        t.readln("Remote SPAN VLANs")
        t.readln("------------------------------------------------------------------------------")
        t.readln("")
        t.readln("")
        t.readln("Primary Secondary Type              Ports")
        t.readln("------- --------- ----------------- ------------------------------------------")
        t.readln("")
        t.read("my_switch#")

        revert_switchport_mode_access(t, "FastEthernet0/1")
        remove_vlan(t, "123")
        remove_vlan(t, "2222")
        remove_vlan(t, "3333")

    @with_protocol
    def test_shutting_down(self, t):
        enable(t)

        configuring_interface(t, "FastEthernet 0/3", do="shutdown")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " shutdown",
            "end"])

        configuring_interface(t, "FastEthernet 0/3", do="no shutdown")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            "end"])

    @with_protocol
    def test_configure_trunk_port(self, t):
        enable(t)

        configuring_interface(t, "Fa0/3", do="switchport mode trunk")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport mode trunk",
            "end"])

        # not really added because all vlan are in trunk by default on cisco
        configuring_interface(t, "Fa0/3", do="switchport trunk allowed vlan add 123")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport mode trunk",
            "end"])

        configuring_interface(t, "Fa0/3", do="switchport trunk allowed vlan none")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport trunk allowed vlan none",
            " switchport mode trunk",
            "end"])

        configuring_interface(t, "Fa0/3", do="switchport trunk allowed vlan add 123")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport trunk allowed vlan 123",
            " switchport mode trunk",
            "end"])

        configuring_interface(t, "Fa0/3", do="switchport trunk allowed vlan add 124,126-128")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport trunk allowed vlan 123,124,126-128",
            " switchport mode trunk",
            "end"])

        configuring_interface(t, "Fa0/3", do="switchport trunk allowed vlan remove 123-124,127")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport trunk allowed vlan 126,128",
            " switchport mode trunk",
            "end"])

        configuring_interface(t, "Fa0/3", do="switchport trunk allowed vlan all")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport mode trunk",
            "end"])

        configuring_interface(t, "Fa0/3", do="switchport trunk allowed vlan 123-124,127")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport trunk allowed vlan 123,124,127",
            " switchport mode trunk",
            "end"])

        configuring_interface(t, "Fa0/3", do="no switchport trunk allowed vlan")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            " switchport mode trunk",
            "end"])

        configuring_interface(t, "Fa0/3", do="no switchport mode")

        assert_interface_configuration(t, "FastEthernet0/3", [
            "interface FastEthernet0/3",
            "end"])

    @with_protocol
    def test_configure_native_vlan(self, t):
        enable(t)

        configuring_interface(t, "FastEthernet0/2", do="switchport trunk native vlan 555")

        assert_interface_configuration(t, "Fa0/2", [
            "interface FastEthernet0/2",
            " switchport trunk native vlan 555",
            "end"])

        configuring_interface(t, "FastEthernet0/2", do="no switchport trunk native vlan")

        assert_interface_configuration(t, "Fa0/2", [
            "interface FastEthernet0/2",
            "end"])

    @with_protocol
    def test_setup_an_interface(self, t):
        enable(t)

        create_interface_vlan(t, "2999")
        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " no ip address",
            "end"])

        configuring_interface_vlan(t, "2999", do="description hey ho")
        configuring_interface_vlan(t, "2999", do="ip address 1.1.1.2 255.255.255.0")
        configuring_interface_vlan(t, "2999", do="standby 1 ip 1.1.1.1")
        configuring_interface_vlan(t, "2999", do='standby 1 timers 5 15')
        configuring_interface_vlan(t, "2999", do='standby 1 priority 110')
        configuring_interface_vlan(t, "2999", do='standby 1 preempt delay minimum 60')
        configuring_interface_vlan(t, "2999", do='standby 1 authentication VLAN2999')
        configuring_interface_vlan(t, "2999", do='standby 1 track 10 decrement 50')
        configuring_interface_vlan(t, "2999", do='standby 1 track 20 decrement 50')

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " description hey ho",
            " ip address 1.1.1.2 255.255.255.0",
            " standby 1 ip 1.1.1.1",
            " standby 1 timers 5 15",
            " standby 1 priority 110",
            " standby 1 preempt delay minimum 60",
            " standby 1 authentication VLAN2999",
            " standby 1 track 10 decrement 50",
            " standby 1 track 20 decrement 50",
            "end"])

        configuring_interface_vlan(t, "2999", do="ip address 2.2.2.2 255.255.255.0")
        configuring_interface_vlan(t, "2999", do="standby 1 ip 2.2.2.1")
        configuring_interface_vlan(t, "2999", do="standby 1 ip 2.2.2.3 secondary")
        configuring_interface_vlan(t, "2999", do="no standby 1 authentication")
        configuring_interface_vlan(t, "2999", do="standby 1 preempt delay minimum 42")
        configuring_interface_vlan(t, "2999", do="no standby 1 priority")
        configuring_interface_vlan(t, "2999", do="no standby 1 timers")
        configuring_interface_vlan(t, "2999", do="no standby 1 track 10")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " description hey ho",
            " ip address 2.2.2.2 255.255.255.0",
            " standby 1 ip 2.2.2.1",
            " standby 1 ip 2.2.2.3 secondary",
            " standby 1 preempt delay minimum 42",
            " standby 1 track 20 decrement 50",
            "end"])

        configuring_interface_vlan(t, "2999", do="no standby 1 ip 2.2.2.3")
        configuring_interface_vlan(t, "2999", do="no standby 1 preempt delay")
        configuring_interface_vlan(t, "2999", do="no standby 1 track 20")
        configuring_interface_vlan(t, "2999", do="")
        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " description hey ho",
            " ip address 2.2.2.2 255.255.255.0",
            " standby 1 ip 2.2.2.1",
            " standby 1 preempt",
            "end"])

        configuring_interface_vlan(t, "2999", do="no standby 1 ip 2.2.2.1")
        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " description hey ho",
            " ip address 2.2.2.2 255.255.255.0",
            " standby 1 preempt",
            "end"])

        configuring_interface_vlan(t, "2999", do="no standby 1")
        configuring_interface_vlan(t, "2999", do="no description")
        configuring_interface_vlan(t, "2999", do="")
        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " ip address 2.2.2.2 255.255.255.0",
            "end"])

        configuring(t, do="no interface vlan 2999")

        t.write("show run int vlan 2999")
        t.readln("\s*\^", regex=True)
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_creating_a_port_channel(self, t):
        enable(t)

        create_port_channel_interface(t, '1')
        configuring_port_channel(t, '1', 'description HELLO')
        configuring_port_channel(t, '1', 'switchport trunk encapsulation dot1q')
        configuring_port_channel(t, '1', 'switchport trunk native vlan 998')
        configuring_port_channel(t, '1', 'switchport trunk allowed vlan 6,4087-4089,4091,4093')
        configuring_port_channel(t, '1', 'switchport mode trunk')

        assert_interface_configuration(t, 'Port-channel1', [
            "interface Port-channel1",
            " description HELLO",
            " switchport trunk encapsulation dot1q",
            " switchport trunk native vlan 998",
            " switchport trunk allowed vlan 6,4087-4089,4091,4093",
            " switchport mode trunk",
            "end"
        ])

        configuring(t, do="no interface port-channel 1")

        t.write("show run int po1")
        t.readln("\s*\^", regex=True)
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_port_channel_is_automatically_created_when_adding_a_port_to_it(self, t):
        enable(t)

        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("interface FastEthernet0/1")
        t.read("my_switch(config-if)#")
        t.write("channel-group 2 mode active")
        t.readln("Creating a port-channel interface Port-channel 2")
        t.read("my_switch(config-if)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        assert_interface_configuration(t, 'fa0/1', [
            "interface FastEthernet0/1",
            " channel-group 2 mode active",
            "end"
        ])

        assert_interface_configuration(t, 'po2', [
            "interface Port-channel2",
            "end"
        ])

        configuring(t, do="no interface port-channel 2")

        configuring_interface(t, interface="fa0/1", do="no channel-group 2 mode on")

        assert_interface_configuration(t, "fa0/1", [
            "interface FastEthernet0/1",
            "end"
        ])

    @with_protocol
    def test_port_channel_is_not_automatically_created_when_adding_a_port_to_it_if_its_already_created(self, t):
        enable(t)

        create_port_channel_interface(t, '4')

        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("interface FastEthernet0/1")
        t.read("my_switch(config-if)#")
        t.write("channel-group 4 mode active")
        t.read("my_switch(config-if)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        assert_interface_configuration(t, "fa0/1", [
            "interface FastEthernet0/1",
            " channel-group 4 mode active",
            "end"
        ])

        configuring_interface(t, interface="fa0/1", do="no channel-group 4 mode on")

        assert_interface_configuration(t, "fa0/1", [
            "interface FastEthernet0/1",
            "end"
        ])

        configuring(t, do="no interface port-channel 4")

    @with_protocol
    def test_setting_secondary_ips(self, t):
        enable(t)

        create_interface_vlan(t, "2999")
        configuring_interface_vlan(t, "2999", do="description hey ho")
        configuring_interface_vlan(t, "2999", do="no ip redirects")
        configuring_interface_vlan(t, "2999", do="ip address 1.1.1.1 255.255.255.0")
        configuring_interface_vlan(t, "2999", do="ip address 2.2.2.1 255.255.255.0 secondary")
        configuring_interface_vlan(t, "2999", do="ip address 4.4.4.1 255.255.255.0 secondary")
        configuring_interface_vlan(t, "2999", do="ip address 3.3.3.1 255.255.255.0 secondary")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " description hey ho",
            " ip address 2.2.2.1 255.255.255.0 secondary",
            " ip address 4.4.4.1 255.255.255.0 secondary",
            " ip address 3.3.3.1 255.255.255.0 secondary",
            " ip address 1.1.1.1 255.255.255.0",
            " no ip redirects",
            "end"])

        configuring_interface_vlan(t, "2999", do="no ip address")
        configuring_interface_vlan(t, "2999", do="ip redirects")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " description hey ho",
            " no ip address",
            "end"])

        configuring(t, do="no interface vlan 2999")

    @with_protocol
    def test_setting_access_group(self, t):
        enable(t)

        create_interface_vlan(t, "2999")
        configuring_interface_vlan(t, "2999", do="ip access-group SHNITZLE in")
        configuring_interface_vlan(t, "2999", do="ip access-group WHIZZLE out")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " no ip address",
            " ip access-group SHNITZLE in",
            " ip access-group WHIZZLE out",
            "end"])

        configuring_interface_vlan(t, "2999", do="no ip access-group in")
        configuring_interface_vlan(t, "2999", do="no ip access-group WHIZZLE out")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " no ip address",
            "end"])

        configuring(t, do="no interface vlan 2999")

    @with_protocol
    def test_removing_ip_address(self, t):
        enable(t)

        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("interface vlan2999")
        t.read("my_switch(config-if)#")
        t.write("ip address 1.1.1.1 255.255.255.0")
        t.read("my_switch(config-if)#")
        t.write("ip address 2.2.2.2 255.255.255.0 secondary")
        t.read("my_switch(config-if)#")
        t.write("no ip address 1.1.1.1 255.255.255.0")
        t.readln("Must delete secondary before deleting primary")
        t.read("my_switch(config-if)#")
        t.write("no ip address 2.2.2.2 255.255.255.0 secondary")
        t.read("my_switch(config-if)#")
        t.write("no ip address 1.1.1.1 255.255.255.0")
        t.read("my_switch(config-if)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        assert_interface_configuration(t, "Vlan2999", [
            "interface Vlan2999",
            " no ip address",
            "end"])

        configuring(t, do="no interface vlan 2999")

    @with_protocol
    def test_show_ip_interfaces(self, t):
        enable(t)

        create_vlan(t, "1000")
        create_interface_vlan(t, "1000")
        create_vlan(t, "2000")
        create_vlan(t, "3000")
        create_interface_vlan(t, "3000")
        configuring_interface_vlan(t, "3000", do="ip address 1.1.1.1 255.255.255.0")

        create_interface_vlan(t, "4000")
        configuring_interface_vlan(t, "4000", do="ip vrf forwarding DEFAULT-LAN")
        configuring_interface_vlan(t, "4000", do="ip address 2.2.2.2 255.255.255.0")
        configuring_interface_vlan(t, "4000", do="ip address 4.2.2.2 255.255.255.0 secondary")
        configuring_interface_vlan(t, "4000", do="ip address 3.2.2.2 255.255.255.0 secondary")
        configuring_interface_vlan(t, "4000", do="ip address 3.2.2.2 255.255.255.128 secondary")
        configuring_interface_vlan(t, "4000", do="ip access-group shizzle in")
        configuring_interface_vlan(t, "4000", do="ip access-group whizzle out")

        t.write("show ip interface")
        t.readln("Vlan1000 is down, line protocol is down")
        t.readln("  Internet protocol processing disabled")
        t.readln("Vlan3000 is down, line protocol is down")
        t.readln("  Internet address is 1.1.1.1/24")
        t.readln("  Outgoing access list is not set")
        t.readln("  Inbound  access list is not set")
        t.readln("Vlan4000 is down, line protocol is down")
        t.readln("  Internet address is 2.2.2.2/24")
        t.readln("  Secondary address 4.2.2.2/24")
        t.readln("  Secondary address 3.2.2.2/25")
        t.readln("  Outgoing access list is whizzle")
        t.readln("  Inbound  access list is shizzle")
        t.readln("  VPN Routing/Forwarding \"DEFAULT-LAN\"")
        t.readln("FastEthernet0/1 is down, line protocol is down")
        t.readln("  Internet protocol processing disabled")
        t.readln("FastEthernet0/2 is down, line protocol is down")
        t.readln("  Internet protocol processing disabled")
        t.readln("FastEthernet0/3 is down, line protocol is down")
        t.readln("  Internet protocol processing disabled")
        t.readln("FastEthernet0/4 is down, line protocol is down")
        t.readln("  Internet protocol processing disabled")
        t.read("my_switch#")

        t.write("show ip interface vlan 4000")
        t.readln("Vlan4000 is down, line protocol is down")
        t.readln("  Internet address is 2.2.2.2/24")
        t.readln("  Secondary address 4.2.2.2/24")
        t.readln("  Secondary address 3.2.2.2/25")
        t.readln("  Outgoing access list is whizzle")
        t.readln("  Inbound  access list is shizzle")
        t.readln("  VPN Routing/Forwarding \"DEFAULT-LAN\"")
        t.read("my_switch#")

        t.write("show ip interface vlan1000")
        t.readln("Vlan1000 is down, line protocol is down")
        t.readln("  Internet protocol processing disabled")
        t.read("my_switch#")

        configuring(t, do="no interface vlan 1000")
        configuring(t, do="no interface vlan 3000")
        configuring(t, do="no interface vlan 4000")

        remove_vlan(t, "1000")
        remove_vlan(t, "2000")
        remove_vlan(t, "3000")

    @with_protocol
    def test_assigning_a_secondary_ip_as_the_primary_removes_it_from_secondary_and_removes_the_primary(self, t):
        enable(t)

        create_interface_vlan(t, "4000")
        configuring_interface_vlan(t, "4000", do="ip address 2.2.2.2 255.255.255.0")
        configuring_interface_vlan(t, "4000", do="ip address 4.2.2.2 255.255.255.0 secondary")
        configuring_interface_vlan(t, "4000", do="ip address 3.2.2.2 255.255.255.0 secondary")
        configuring_interface_vlan(t, "4000", do="ip address 3.2.2.2 255.255.255.128")

        assert_interface_configuration(t, "Vlan4000", [
            "interface Vlan4000",
            " ip address 4.2.2.2 255.255.255.0 secondary",
            " ip address 3.2.2.2 255.255.255.128",
            "end"])

        configuring(t, do="no interface vlan 4000")

    @with_protocol
    def test_overlapping_ips(self, t):
        enable(t)

        create_vlan(t, "1000")
        create_interface_vlan(t, "1000")
        create_vlan(t, "2000")
        create_interface_vlan(t, "2000")

        configuring_interface_vlan(t, "1000", do="ip address 2.2.2.2 255.255.255.0")
        configuring_interface_vlan(t, "1000", do="ip address 3.3.3.3 255.255.255.0 secondary")

        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("interface vlan2000")
        t.read("my_switch(config-if)#")

        t.write("ip address 2.2.2.75 255.255.255.128")
        t.readln("% 2.2.2.0 overlaps with secondary address on Vlan1000")
        t.read("my_switch(config-if)#")

        t.write("ip address 3.3.3.4 255.255.255.128")
        t.readln("% 3.3.3.0 is assigned as a secondary address on Vlan1000")
        t.read("my_switch(config-if)#")

        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        configuring(t, do="no interface vlan 2000")
        remove_vlan(t, "2000")
        configuring(t, do="no interface vlan 1000")
        remove_vlan(t, "1000")

    @with_protocol
    def test_unknown_ip_interface(self, t):
        enable(t)

        t.write("show ip interface Vlan2345")
        t.readln("                                 ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch#")

    @with_protocol
    def test_removing_ip_needs_to_compare_objects_better(self, t):
        enable(t)

        create_vlan(t, "1000")
        create_interface_vlan(t, "1000")

        configuring_interface_vlan(t, "1000", do="ip address 1.1.1.1 255.255.255.0")
        configuring_interface_vlan(t, "1000", do="ip address 1.1.1.2 255.255.255.0 secondary")
        configuring_interface_vlan(t, "1000", do="ip address 1.1.1.3 255.255.255.0 secondary")

        configuring_interface_vlan(t, "1000", do="no ip address 1.1.1.3 255.255.255.0 secondary")

        t.write("show ip interface vlan 1000")
        t.readln("Vlan1000 is down, line protocol is down")
        t.readln("  Internet address is 1.1.1.1/24")
        t.readln("  Secondary address 1.1.1.2/24")
        t.readln("  Outgoing access list is not set")
        t.readln("  Inbound  access list is not set")
        t.read("my_switch#")

        configuring(t, do="no interface vlan 1000")
        remove_vlan(t, "1000")

    @with_protocol
    def test_extreme_vlan_range(self, t):
        enable(t)

        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")

        t.write("vlan -1")
        t.readln("Command rejected: Bad VLAN list - character #1 ('-') delimits a VLAN number")
        t.readln(" which is out of the range 1..4094.")
        t.read("my_switch(config)#")

        t.write("vlan 0")
        t.readln("Command rejected: Bad VLAN list - character #X (EOL) delimits a VLAN")
        t.readln("number which is out of the range 1..4094.")
        t.read("my_switch(config)#")

        t.write("vlan 1")
        t.read("my_switch(config-vlan)#")
        t.write("exit")
        t.read("my_switch(config)#")

        t.write("vlan 4094")
        t.read("my_switch(config-vlan)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("no vlan 4094")
        t.read("my_switch(config)#")

        t.write("vlan 4095")
        t.readln("Command rejected: Bad VLAN list - character #X (EOL) delimits a VLAN")
        t.readln("number which is out of the range 1..4094.")
        t.read("my_switch(config)#")

        t.write("exit")
        t.read("my_switch#")

    @with_protocol
    def test_full_running_config_and_pipe_begin_support(self, t):
        enable(t)

        create_vlan(t, "1000", name="hello")
        create_interface_vlan(t, "1000")
        configuring_interface(t, "Fa0/2", do="switchport mode trunk")
        configuring_interface(t, "Fa0/2", do="switchport trunk allowed vlan 125")

        t.write("show running | beg vlan")
        t.readln("vlan 1")
        t.readln("!")
        t.readln("vlan 1000")
        t.readln(" name hello")
        t.readln("!")
        t.readln("interface FastEthernet0/1")
        t.readln("!")
        t.readln("interface FastEthernet0/2")
        t.readln(" switchport trunk allowed vlan 125")
        t.readln(" switchport mode trunk")
        t.readln("!")
        t.readln("interface FastEthernet0/3")
        t.readln("!")
        t.readln("interface FastEthernet0/4")
        t.readln("!")
        t.readln("interface Vlan1000")
        t.readln(" no ip address")
        t.readln("!")
        t.readln("end")
        t.readln("")
        t.read("my_switch#")

        configuring_interface(t, "Fa0/2", do="no switchport mode trunk")
        configuring_interface(t, "Fa0/2", do="no switchport trunk allowed vlan")
        configuring(t, do="no interface vlan 1000")
        remove_vlan(t, "1000")

    @with_protocol
    def test_pipe_inc_support(self, t):
        enable(t)

        create_vlan(t, "1000", name="hello")

        t.write("show running | inc vlan")
        t.readln("vlan 1")
        t.readln("vlan 1000")
        t.read("my_switch#")

        remove_vlan(t, "1000")

    @with_protocol
    def test_ip_vrf(self, t):
        enable(t)

        t.write("conf t")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("ip vrf SOME-LAN")
        t.read("my_switch(config-vrf)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("no ip vrf SOME-LAN")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

    @with_protocol
    def test_ip_vrf_forwarding(self, t):
        enable(t)

        t.write("conf t")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("ip vrf SOME-LAN")
        t.read("my_switch(config-vrf)#")
        t.write("exit")
        t.read("my_switch(config)#")

        t.write("interface Fa0/2")
        t.read("my_switch(config-if)#")
        t.write("ip vrf forwarding NOT-DEFAULT-LAN")
        t.readln("% VRF NOT-DEFAULT-LAN not configured.")
        t.read("my_switch(config-if)#")

        t.write("ip vrf forwarding SOME-LAN")
        t.read("my_switch(config-if)#")
        t.write("exit")
        t.read("my_switch(config)#")

        t.write("exit")
        t.read("my_switch#")

        assert_interface_configuration(t, "Fa0/2", [
            "interface FastEthernet0/2",
            " ip vrf forwarding SOME-LAN",
            "end"])

        t.write("conf t")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("no ip vrf SOME-LAN")
        t.read("my_switch(config)#")

        t.write("exit")
        t.read("my_switch#")

        assert_interface_configuration(t, "Fa0/2", [
            "interface FastEthernet0/2",
            "end"])

    @with_protocol
    def test_ip_vrf_default_lan(self, t):
        enable(t)

        t.write("conf t")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")

        t.write("interface Fa0/2")
        t.read("my_switch(config-if)#")
        t.write("ip vrf forwarding DEFAULT-LAN")
        t.read("my_switch(config-if)#")

        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        assert_interface_configuration(t, "Fa0/2", [
            "interface FastEthernet0/2",
            " ip vrf forwarding DEFAULT-LAN",
            "end"])

        t.write("conf t")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("interface Fa0/2")
        t.read("my_switch(config-if)#")
        t.write("no ip vrf forwarding")
        t.read("my_switch(config-if)#")

        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        assert_interface_configuration(t, "Fa0/2", [
            "interface FastEthernet0/2",
            "end"])

    @with_protocol
    def test_ip_setting_vrf_forwarding_wipes_ip_addresses(self, t):
        enable(t)

        create_vlan(t, "4000")
        create_interface_vlan(t, "4000")
        configuring_interface_vlan(t, "4000", do="ip address 10.10.0.10 255.255.255.0")
        configuring_interface_vlan(t, "4000", do="ip address 10.10.1.10 255.255.255.0 secondary")

        assert_interface_configuration(t, "Vlan4000", [
            "interface Vlan4000",
            " ip address 10.10.1.10 255.255.255.0 secondary",
            " ip address 10.10.0.10 255.255.255.0",
            "end"])

        configuring_interface_vlan(t, "4000", do="ip vrf forwarding DEFAULT-LAN")

        assert_interface_configuration(t, "Vlan4000", [
            "interface Vlan4000",
            " ip vrf forwarding DEFAULT-LAN",
            " no ip address",
            "end"])

        configuring(t, do="no interface vlan 4000")
        remove_vlan(t, "4000")

    @with_protocol
    def test_ip_helper(self, t):
        enable(t)

        create_interface_vlan(t, "4000")

        assert_interface_configuration(t, "Vlan4000", [
            "interface Vlan4000",
            " no ip address",
            "end"])

        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("interface vlan 4000")
        t.read("my_switch(config-if)#")
        t.write("ip helper-address")
        t.readln("% Incomplete command.")
        t.readln("")
        t.read("my_switch(config-if)#")

        t.write("ip helper-address 10.10.0.1 EXTRA INFO")
        t.readln(" ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        configuring_interface_vlan(t, "4000", do="ip helper-address 10.10.10.1")

        assert_interface_configuration(t, "Vlan4000", [
            "interface Vlan4000",
            " no ip address",
            " ip helper-address 10.10.10.1",
            "end"])

        configuring_interface_vlan(t, "4000", do="ip helper-address 10.10.10.1")
        configuring_interface_vlan(t, "4000", do="ip helper-address 10.10.10.2")
        configuring_interface_vlan(t, "4000", do="ip helper-address 10.10.10.3")

        assert_interface_configuration(t, "Vlan4000", [
            "interface Vlan4000",
            " no ip address",
            " ip helper-address 10.10.10.1",
            " ip helper-address 10.10.10.2",
            " ip helper-address 10.10.10.3",
            "end"])

        configuring_interface_vlan(t, "4000", do="no ip helper-address 10.10.10.1")

        assert_interface_configuration(t, "Vlan4000", [
            "interface Vlan4000",
            " no ip address",
            " ip helper-address 10.10.10.2",
            " ip helper-address 10.10.10.3",
            "end"])

        configuring_interface_vlan(t, "4000", do="no ip helper-address 10.10.10.1")

        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("interface vlan 4000")
        t.read("my_switch(config-if)#")
        t.write("no ip helper-address 10.10.0.1 EXTRA INFO")
        t.readln(" ^")
        t.readln("% Invalid input detected at '^' marker.")
        t.readln("")
        t.read("my_switch(config-if)#")
        t.write("exit")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

        configuring_interface_vlan(t, "4000", do="no ip helper-address")

        assert_interface_configuration(t, "Vlan4000", [
            "interface Vlan4000",
            " no ip address",
            "end"])

        configuring(t, do="no interface vlan 4000")

    @with_protocol
    def test_ip_route(self, t):
        enable(t)
        configuring(t, do="ip route 1.1.1.0 255.255.255.0 2.2.2.2")

        t.write("show ip route static | inc 2.2.2.2")
        t.readln("S        1.1.1.0 [x/y] via 2.2.2.2")
        t.read("my_switch#")

        t.write("show running | inc 2.2.2.2")
        t.readln("ip route 1.1.1.0 255.255.255.0 2.2.2.2")
        t.read("my_switch#")

        configuring(t, do="no ip route 1.1.1.0 255.255.255.0 2.2.2.2")

        t.write("show ip route static")
        t.readln("")
        t.read("my_switch#")
        t.write("exit")

    @with_protocol
    def test_write_memory(self, t):
        enable(t)

        t.write("write memory")
        t.read("my_switch#")


def enable(t):
    t.write("enable")
    t.read("Password: ")
    t.write_invisible(cisco_privileged_password)
    t.read("my_switch#")


def create_vlan(t, vlan, name=None):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("vlan %s" % vlan)
    t.read("my_switch(config-vlan)#")
    if name:
        t.write("name %s" % name)
        t.read("my_switch(config-vlan)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def create_interface_vlan(t, vlan):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface vlan %s" % vlan)
    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def create_port_channel_interface(t, po_id):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface port-channel %s" % po_id)
    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def remove_vlan(t, vlan):
    configuring(t, do="no vlan %s" % vlan)


def set_interface_on_vlan(t, interface, vlan):
    configuring_interface(t, interface, do="switchport mode access")
    configuring_interface(t, interface, do="switchport access vlan %s" % vlan)


def revert_switchport_mode_access(t, interface):
    configuring_interface(t, interface, do="no switchport access vlan")
    configuring_interface(t, interface, do="no switchport mode access")


def configuring(t, do):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")

    t.write(do)

    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def configuring_interface(t, interface, do):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface %s" % interface)
    t.read("my_switch(config-if)#")

    t.write(do)

    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def configuring_interface_vlan(t, interface, do):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface vlan %s" % interface)
    t.read("my_switch(config-if)#")

    t.write(do)

    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def configuring_port_channel(t, number, do):
    t.write("configure terminal")
    t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
    t.read("my_switch(config)#")
    t.write("interface port-channel %s" % number)
    t.read("my_switch(config-if)#")

    t.write(do)

    t.read("my_switch(config-if)#")
    t.write("exit")
    t.read("my_switch(config)#")
    t.write("exit")
    t.read("my_switch#")


def assert_interface_configuration(t, interface, config):
    t.write("show running-config interface %s " % interface)
    t.readln("Building configuration...")
    t.readln("")
    t.readln("Current configuration : \d+ bytes", regex=True)
    t.readln("!")
    for line in config:
        t.readln(line)
    t.readln("")
    t.read("my_switch#")


class TestCiscoSwitchProtocolSSH(TestCiscoSwitchProtocol):
    __test__ = True

    def create_client(self):
        return SshTester("ssh", cisco_switch_ip, cisco_switch_ssh_port, 'root', 'root')


class TestCiscoSwitchProtocolTelnet(TestCiscoSwitchProtocol):
    __test__ = True

    def create_client(self):
        return TelnetTester("telnet", cisco_switch_ip, cisco_switch_telnet_port, 'root', 'root')
