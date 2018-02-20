import logging
import re
import unittest

import pexpect
from flexmock import flexmock_teardown
from hamcrest import assert_that, equal_to
from tests.util.global_reactor import TEST_SWITCHES


def with_protocol(test):
    def wrapper(self):
        try:
            logging.info(">>>> CONNECTING [%s]" % self.protocol.name)
            self.protocol.connect()
            logging.info(">>>> START")
            test(self, self.protocol)
            logging.info(">>>> SUCCESS")
        finally:
            self.protocol.disconnect()

    wrapper.__name__ = test.__name__
    return wrapper


class LoggingFileInterface(object):
    def __init__(self, prefix):
        self.prefix = prefix

    def write(self, data):
        for line in data.rstrip(b'\r\n').split(b'\r\n'):
            logging.info(self.prefix + repr(line))

    def flush(self):
        pass


class ProtocolTester(object):
    def __init__(self, name, host, port, username, password, conf=None):
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.conf = conf

        self.child = None

    def connect(self):
        self.child = pexpect.spawn(self.get_ssh_connect_command())
        self.child.delaybeforesend = 0.0005
        self.child.logfile = None
        self.child.logfile_read = LoggingFileInterface(prefix="[%s] " % self.name)
        self.child.timeout = 1
        self.login()

    def disconnect(self):
        self.child.close()

    def get_ssh_connect_command(self):
        pass

    def login(self):
        pass

    def read(self, expected, regex=False):
        self.wait_for(expected, regex)
        assert_that(self.child.before, equal_to(b""))

    def readln(self, expected, regex=False):
        self.read(expected + "\r\n", regex=regex)

    def read_lines_until(self, expected):
        self.wait_for(expected)
        lines = self.child.before.decode().split('\r\n')
        return lines

    def read_eof(self):
        self.child.expect(pexpect.EOF)

    def wait_for(self, expected, regex=False):
        pattern = re.escape(expected) if not regex else expected
        self.child.expect(pattern)

    def write(self, data):
        self.child.sendline(data.encode())
        self.read(data + "\r\n")

    def write_invisible(self, data):
        self.child.sendline(data.encode())
        self.read("\r\n")

    def write_stars(self, data):
        self.child.sendline(data.encode())
        self.read(len(data) * "*" + "\r\n")

    def write_raw(self, data):
        self.child.send(data.encode())


class SshTester(ProtocolTester):
    CONF_KEY = "ssh"

    def get_ssh_connect_command(self):
        return 'ssh %s@%s -p %s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null' \
               % (self.username, self.host, self.port)

    def login(self):
        self.wait_for('[pP]assword: ', regex=True)
        self.write_invisible(self.password)
        self.wait_for('[>#]$', regex=True)


class TelnetTester(ProtocolTester):
    CONF_KEY = "telnet"

    def get_ssh_connect_command(self):
        return 'telnet %s %s' \
               % (self.host, self.port)

    def login(self):
        self.wait_for("Username: ")
        self.write(self.username)
        self.wait_for("[pP]assword: ", True)
        self.write_invisible(self.password)
        self.wait_for('[>#]$', regex=True)


class ProtocolTest(unittest.TestCase):
    tester_class = SshTester
    test_switch = None

    def setUp(self):
        conf = TEST_SWITCHES[self.test_switch]
        self.protocol = self.tester_class(self.tester_class.CONF_KEY,
                                          "127.0.0.1",
                                          conf[self.tester_class.CONF_KEY],
                                          u'root',
                                          u'root',
                                          conf)

    def tearDown(self):
        flexmock_teardown()
