from tests.util.protocol_util import SshTester, TelnetTester, with_protocol, ProtocolTest


class TestCiscoAutoEnabledSwitchProtocol(ProtocolTest):
    __test__ = False
    test_switch = "cisco-auto-enabled"

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


class TestCiscoSwitchProtocolSSH(TestCiscoAutoEnabledSwitchProtocol):
    __test__ = True
    tester_class = SshTester


class TestCiscoSwitchProtocolTelnet(TestCiscoAutoEnabledSwitchProtocol):
    __test__ = True
    tester_class = TelnetTester
