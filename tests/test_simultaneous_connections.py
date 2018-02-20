import unittest

from tests.util.global_reactor import TEST_SWITCHES
from tests.util.protocol_util import SshTester, TelnetTester


class RoutingEngineTest(unittest.TestCase):
    def test_2_ssh(self):
        conf = TEST_SWITCHES["brocade"]
        tester1 = SshTester("ssh-1", "127.0.0.1", conf["ssh"], u'root', u'root')
        tester2 = SshTester("ssh-2", "127.0.0.1", conf["ssh"], u'root', u'root')

        tester1.connect()
        tester1.write("enable")
        tester1.read("Password:")
        tester1.write_invisible(conf["extra"]["password"])
        tester1.read("SSH@my_switch#")
        tester1.write("skip-page-display")
        tester1.read("SSH@my_switch#")

        tester2.connect()

        tester1.write("skip-page-display")
        tester1.read("SSH@my_switch#")

        tester2.write("enable")
        tester2.read("Password:")
        tester2.write_invisible(conf["extra"]["password"])
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
        conf = TEST_SWITCHES["cisco"]
        tester1 = TelnetTester("telnet-1", "127.0.0.1", conf["telnet"], 'root', 'root')
        tester2 = TelnetTester("telnet-2", "127.0.0.1", conf["telnet"], 'root', 'root')

        tester1.connect()
        tester1.write("enable")
        tester1.read("Password: ")
        tester1.write_invisible(conf["extra"]["password"])
        tester1.read("my_switch#")
        tester1.write("terminal length 0")
        tester1.read("my_switch#")

        tester2.connect()

        tester1.write("terminal length 0")
        tester1.read("my_switch#")

        tester2.write("enable")
        tester2.read("Password: ")
        tester2.write_invisible(conf["extra"]["password"])
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
