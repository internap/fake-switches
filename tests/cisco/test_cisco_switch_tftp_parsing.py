# Copyright 2016 Internap.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from hamcrest import assert_that, equal_to
import mock
from fake_switches.command_processing.switch_tftp_parser import SwitchTftpParser
from fake_switches.cisco.command_processor.config import ConfigCommandProcessor
from fake_switches.switch_configuration import SwitchConfiguration, Port


class TestCiscoSwitchTftpParsing(unittest.TestCase):
    @mock.patch("fake_switches.adapters.tftp_reader.read_tftp")
    def test_basic_parsing(self, tftp_reader_mock):
        tftp_reader_mock.return_value = """
!
vlan 1000
name VLAN_1_0_0_0
!
!
vlan 2000
name VLAN_2_0_0_0
!
"""
        config = SwitchConfiguration("127.0.0.1", name="my_switch", ports=[
            Port("GigabitEthernet0/1")
        ])

        parser = SwitchTftpParser(config)

        parser.parse("hostname", "filename", ConfigCommandProcessor)

        tftp_reader_mock.assert_called_with("hostname", "filename")

        vlan1000 = config.get_vlan(1000)
        assert_that(vlan1000.name, equal_to("VLAN_1_0_0_0"))

        vlan2000 = config.get_vlan(2000)
        assert_that(vlan2000.name, equal_to("VLAN_2_0_0_0"))

    @mock.patch("fake_switches.adapters.tftp_reader.read_tftp")
    def test_longer_parsing(self, tftp_reader_mock):
        tftp_reader_mock.return_value = """
!
vlan 1000
name VLAN_1_0_0_0
!
!
interface GigabitEthernet0/1
no switchport access vlan 1
switchport access vlan 1000
!
!
interface GigabitEthernet0/1
description "Gigabit Ethernet 1 desc"
switchport
load-interval 30
switchport mode access
switchport access vlan 1000
switchport nonegotiate
spanning-tree portfast
spanning-tree bpdufilter enable
spanning-tree bpduguard enable
no loopback
no keepalive
!
"""

        config = SwitchConfiguration("127.0.0.1", name="my_switch", ports=[
            Port("GigabitEthernet0/1")
        ])

        parser = SwitchTftpParser(config)

        parser.parse("hostname", "filename", ConfigCommandProcessor)

        vlan1000 = config.get_vlan(1000)
        assert_that(vlan1000.name, equal_to("VLAN_1_0_0_0"))

        eth01 = config.get_port("GigabitEthernet0/1")
        assert_that(eth01.description, equal_to("Gigabit Ethernet 1 desc"))
        assert_that(eth01.mode, equal_to("access"))
        assert_that(eth01.access_vlan, equal_to(1000))
