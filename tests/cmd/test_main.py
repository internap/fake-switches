import os
import socket
import subprocess
import sys
import time
import unittest

from hamcrest import assert_that, is_not, starts_with
from tests.util import _unique_port
from tests.util.protocol_util import SshTester

TEST_BIND_HOST = '127.0.0.1'
TEST_BIND_PORT = str(_unique_port())
TEST_HOSTNAME = 'root'
TEST_PASSWORD = 'root'


class FakeSwitchesTest(unittest.TestCase):
    def test_fake_switches_password_encoding(self):
        p = subprocess.Popen(get_base_args() + ["--listen-host", TEST_BIND_HOST,
                                                "--listen-port", TEST_BIND_PORT,
                                                "--hostname", TEST_HOSTNAME,
                                                "--password", TEST_PASSWORD])
        time.sleep(1)

        ssh = SshTester("ssh-2", TEST_BIND_HOST, TEST_BIND_PORT, TEST_HOSTNAME, TEST_PASSWORD)
        ssh.connect()
        ssh.disconnect()

        p.terminate()

    def test_fake_switches_entrypoint_cisco_generic(self):
        p = subprocess.Popen(get_base_args() + ["--listen-host", TEST_BIND_HOST,
                                                "--listen-port", TEST_BIND_PORT])
        time.sleep(1)
        handshake = connect_and_read_bytes(TEST_BIND_HOST, TEST_BIND_PORT,
                                           byte_count=8, retry_count=10)

        p.terminate()

        assert_that(handshake, starts_with('SSH-2.0'))

    def test_fake_switches_entrypoint_invalid_model(self):
        p = subprocess.Popen(get_base_args() + ["--listen-host", TEST_BIND_HOST,
                                                "--listen-port", TEST_BIND_PORT,
                                                "--model", "invalid_model"])

        returncode = p.wait()

        assert_that(returncode, is_not(0))


def get_base_args():
    entry_point_path = os.path.join(os.path.dirname(sys.executable), 'fake-switches')
    return [sys.executable, entry_point_path]


def connect_and_read_bytes(host, port, byte_count, retry_count, sleep_time=0.1):
    last_socket_error = None

    for _ in range(retry_count):
        try:
            s = socket.create_connection((host, port))
        except socket.error as e:
            last_socket_error = e
            time.sleep(sleep_time)
            continue
        data = s.recv(byte_count)
        s.close()

        return data.decode()
    raise last_socket_error
