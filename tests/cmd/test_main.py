import socket
import subprocess
import sys
import time
import unittest
import random

import os
from hamcrest import assert_that, is_not, starts_with

TEST_BIND_HOST = '127.0.0.1'
TEST_BIND_PORT = str(random.randint(20000, 22000))


class FakeSwitchesTest(unittest.TestCase):
    def test_fake_switches_entrypoint_cisco_generic(self):
        p = subprocess.Popen(get_base_args() + ['cisco_generic', TEST_BIND_HOST, TEST_BIND_PORT])

        handshake = connect_and_read_bytes(TEST_BIND_HOST, TEST_BIND_PORT,
                                           byte_count=8, retry_count=10)

        p.terminate()

        assert_that(handshake, starts_with('SSH-2.0'))

    def test_fake_switches_entrypoint_invalid_model(self):
        p = subprocess.Popen(get_base_args() + ['invalid_model', TEST_BIND_HOST, TEST_BIND_PORT])

        returncode = p.wait()

        assert_that(returncode, is_not(0))


def get_base_args():
    entry_point_path = os.path.join(os.path.dirname(sys.executable), 'fake-switches')
    return [sys.executable, entry_point_path]


def connect_and_read_bytes(host, port, byte_count, retry_count, sleep_time=0.1):
    last_socket_error = None

    for _ in xrange(retry_count):
        try:
            s = socket.create_connection((host, port))
        except socket.error as e:
            last_socket_error = e
            time.sleep(sleep_time)
            continue
        data = s.recv(byte_count)
        s.close()

        return data
    raise last_socket_error
