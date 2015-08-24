import unittest

from flexmock import flexmock_teardown
from tests.util.global_reactor import cisco_switch_ip, \
    cisco_auto_enabled_switch_ssh_port, cisco_auto_enabled_switch_telnet_port
from tests.util.protocol_util import SshTester, TelnetTester, with_protocol


class TestCiscoAutoEnabledSwitchProtocol(unittest.TestCase):
    __test__ = False

    def setUp(self):
        self.protocol = self.create_client()

    def tearDown(self):
        flexmock_teardown()

    @with_protocol
    def test_enable_command_requires_a_password(self, t):
        t.write("enable")
        t.read("my_switch#")
        t.write("terminal length 0")
        t.read("my_switch#")
        t.write("terminal width 0")
        t.read("my_switch#")
        t.write("configure terminal")
        t.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        t.read("my_switch(config)#")
        t.write("exit")
        t.read("my_switch#")

    def create_client(self):
        raise NotImplemented()


class TestCiscoSwitchProtocolSSH(TestCiscoAutoEnabledSwitchProtocol):
    __test__ = True

    def create_client(self):
        return SshTester("ssh", cisco_switch_ip, cisco_auto_enabled_switch_ssh_port, 'root', 'root')


class TestCiscoSwitchProtocolTelnet(TestCiscoAutoEnabledSwitchProtocol):
    __test__ = True

    def create_client(self):
        return TelnetTester("telnet", cisco_switch_ip, cisco_auto_enabled_switch_telnet_port, 'root', 'root')
