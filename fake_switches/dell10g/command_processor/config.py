# Copyright 2015 Internap.
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

from fake_switches.dell.command_processor.config import DellConfigCommandProcessor
from fake_switches.dell10g.command_processor.config_interface import \
    Dell10GConfigInterfaceCommandProcessor
from fake_switches.dell10g.command_processor.config_vlan import \
    Dell10GConfigureVlanCommandProcessor


class Dell10GConfigCommandProcessor(DellConfigCommandProcessor):
    config_interface_processor = Dell10GConfigInterfaceCommandProcessor

    def do_vlan(self, raw_number, *_):
        number = int(raw_number)
        vlan = self.switch_configuration.get_vlan(number)
        if not vlan:
            vlan = self.switch_configuration.new("Vlan", number)
            self.switch_configuration.add_vlan(vlan)
        self.move_to(Dell10GConfigureVlanCommandProcessor, vlan)
