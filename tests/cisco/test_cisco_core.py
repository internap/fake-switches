import unittest

from fake_switches.cisco import cisco_core
from hamcrest import assert_that, has_length, has_property


class CiscoCoreTest(unittest.TestCase):
    def test_cisco_2960_24TT_L_has_right_ports(self):
        ports = cisco_core.Cisco2960_24TT_L_SwitchCore.get_default_ports()

        fast_ethernet_ports = [p for p in ports if p.name.startswith('FastEthernet')]
        gigabit_ethernet_ports = [p for p in ports if p.name.startswith('GigabitEthernet')]

        assert_that(fast_ethernet_ports, has_length(24))
        assert_that(gigabit_ethernet_ports, has_length(2))
        assert_that(fast_ethernet_ports[0], has_property('name', 'FastEthernet0/1'))
        assert_that(gigabit_ethernet_ports[0], has_property('name', 'GigabitEthernet0/1'))

    def test_cisco_2960_48TT_L_has_right_ports(self):
        ports = cisco_core.Cisco2960_48TT_L_SwitchCore.get_default_ports()

        fast_ethernet_ports = [p for p in ports if p.name.startswith('FastEthernet')]
        gigabit_ethernet_ports = [p for p in ports if p.name.startswith('GigabitEthernet')]

        assert_that(fast_ethernet_ports, has_length(48))
        assert_that(gigabit_ethernet_ports, has_length(2))
        assert_that(fast_ethernet_ports[0], has_property('name', 'FastEthernet0/1'))
        assert_that(gigabit_ethernet_ports[0], has_property('name', 'GigabitEthernet0/1'))
