import unittest

from hamcrest import assert_that, equal_to

from fake_switches.transports import SwitchSshService, SwitchTelnetService, SwitchHttpService


class TransportsTests(unittest.TestCase):
    def test_http_service_has_default_port(self):
        http_service = SwitchHttpService()

        assert_that(http_service.port, equal_to(80))

    def test_ssh_service_has_default_port(self):
        ssh_service = SwitchSshService()

        assert_that(ssh_service.port, equal_to(22))

    def test_telnet_service_has_default_port(self):
        telnet_service = SwitchTelnetService()

        assert_that(telnet_service.port, equal_to(23))
