import unittest

from tests.util.global_reactor import brocade_privileged_password, cisco_privileged_password
from tests.util.global_reactor import brocade_switch_ip, brocade_switch_ssh_port, cisco_switch_ip, \
    cisco_switch_telnet_port
from tests.util.protocol_util import SshTester, TelnetTester


class RoutingEngineTest(unittest.TestCase):
    def test_2_ssh(self):
        tester1 = SshTester("ssh-1", brocade_switch_ip, brocade_switch_ssh_port, 'root', 'root')
        tester2 = SshTester("ssh-2", brocade_switch_ip, brocade_switch_ssh_port, 'root', 'root')

        tester1.connect()
        tester1.write("enable")
        tester1.read("Password:")
        tester1.write_invisible(brocade_privileged_password)
        tester1.read("SSH@my_switch#")
        tester1.write("skip-page-display")
        tester1.read("SSH@my_switch#")

        tester2.connect()

        tester1.write("skip-page-display")
        tester1.read("SSH@my_switch#")

        tester2.write("enable")
        tester2.read("Password:")
        tester2.write_invisible(brocade_privileged_password)
        tester2.read("SSH@my_switch#")
        tester2.write("configure terminal")
        tester2.read("SSH@my_switch(config)#")

        tester1.write("skip-page-display")
        tester1.read("SSH@my_switch#")

        tester2.write("exit")
        tester2.read("SSH@my_switch#")

        tester1.write("exit")
        tester1.read_eof()
        tester1.disconnect()

        tester2.write("exit")
        tester2.read_eof()
        tester2.disconnect()

    def test_2_telnet(self):
        tester1 = TelnetTester("telnet-1", cisco_switch_ip, cisco_switch_telnet_port, 'root', 'root')
        tester2 = TelnetTester("telnet-2", cisco_switch_ip, cisco_switch_telnet_port, 'root', 'root')

        tester1.connect()
        tester1.write("enable")
        tester1.read("Password: ")
        tester1.write_invisible(cisco_privileged_password)
        tester1.read("my_switch#")
        tester1.write("terminal length 0")
        tester1.read("my_switch#")

        tester2.connect()

        tester1.write("terminal length 0")
        tester1.read("my_switch#")

        tester2.write("enable")
        tester2.read("Password: ")
        tester2.write_invisible(cisco_privileged_password)
        tester2.read("my_switch#")
        tester2.write("configure terminal")
        tester2.readln("Enter configuration commands, one per line.  End with CNTL/Z.")
        tester2.read("my_switch(config)#")

        tester1.write("terminal length 0")
        tester1.read("my_switch#")

        tester2.write("exit")
        tester2.read("my_switch#")

        tester1.write("exit")
        tester1.read_eof()
        tester1.disconnect()

        tester2.write("exit")
        tester2.read_eof()
        tester2.disconnect()
