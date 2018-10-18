# Copyright 2018 Inap.
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
from fake_switches.arista.command_processor import vlan_display_name
from fake_switches.arista.command_processor.default import DefaultCommandProcessor


class EnabledCommandProcessor(DefaultCommandProcessor):
    def __init__(self, display_class, config):
        super(EnabledCommandProcessor, self).__init__(display_class, enabled=None)
        self.config_processor = config

    def get_prompt(self):
        return self.switch_configuration.name + "#"

    def do_enable(self, *args):
        pass

    def do_configure(self, *_):
        self.move_to(self.config_processor)

    def do_show(self, *args):
        if "running-config".startswith(args[0]):
            self._show_running_config()
        else:
            super(EnabledCommandProcessor, self).do_show(*args)

    def do_terminal(self, *_):
        self.write("Pagination disabled.")

    def _show_running_config(self):
        self._show_header()
        self._show_vlans(sorted(self.switch_configuration.vlans, key=lambda v: v.number))
        self.write_line("end")

    def _show_header(self):
        self.write_line("! Command: show running-config all")
        self.write_line("! device: {} (vEOS, EOS-4.20.8M)".format(self.switch_configuration.name))
        self.write_line("!")
        self.write_line("! boot system flash:/vEOS-lab.swi")
        self.write_line("!")

    def _show_vlans(self, vlans):
        for vlan in vlans:
            self.write_line("vlan {}".format(vlan.number))
            self.write_line("   name {}".format(vlan_display_name(vlan)))
            self.write_line("   mac address learning")
            self.write_line("   state active")
            self.write_line("!")
