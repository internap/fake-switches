import unittest
import time

from flexmock import flexmock_teardown
from hamcrest import assert_that, greater_than
from tests.util.global_reactor import brocade_switch_ip, brocade_privileged_password, brocade_switch_with_commit_delay_ssh_port, \
    COMMIT_DELAY
from tests.util.protocol_util import SshTester, with_protocol


class TestBrocadeSwitchProtocolWithCommitDelay(unittest.TestCase):
    def setUp(self):
        self.protocol = SshTester("ssh", brocade_switch_ip, brocade_switch_with_commit_delay_ssh_port, 'root', 'root')

    def tearDown(self):
        flexmock_teardown()

    @with_protocol
    def test_write_memory(self, t):
        enable(t)
        t.child.timeout = 10

        start_time = time.time()

        t.write("write memory")
        t.read("SSH@my_switch#")

        end_time = time.time()

        assert_that((end_time - start_time), greater_than(COMMIT_DELAY))


def enable(t):
    t.write("enable")
    t.read("Password:")
    t.write_invisible(brocade_privileged_password)
    t.read("SSH@my_switch#")
