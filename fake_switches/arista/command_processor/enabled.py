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
from fake_switches.dell.command_processor.enabled import to_vlan_ranges
from fake_switches.switch_configuration import VlanPort


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
            self._show_running_config(*args[1:])
        else:
            super(EnabledCommandProcessor, self).do_show(*args)

    def do_terminal(self, *_):
        self.write("Pagination disabled.")

    def do_write(self, *_):
        self.switch_configuration.commit()
        self.write_line("Copy completed successfully.")

    def _show_running_config(self, *args):
        if "interfaces".startswith(args[0]):
            names = self.read_multiple_interfaces_name(args[1:])
            if names is not None:
                self._show_run_interfaces(sorted(filter(lambda e: e, (self.switch_configuration.get_port_by_partial_name(p) for p in names)), key=lambda e: e.name))
        else:
            self._show_header()
            self._show_run_vlans(sorted(self.switch_configuration.vlans, key=lambda v: v.number))
            self.write_line("end")

    def _show_header(self):
        self.write_line("! Command: show running-config all")
        self.write_line("! device: {} (vEOS, EOS-4.20.8M)".format(self.switch_configuration.name))
        self.write_line("!")
        self.write_line("! boot system flash:/vEOS-lab.swi")
        self.write_line("!")

    def _show_run_vlans(self, vlans):
        for vlan in vlans:
            self.write_line("vlan {}".format(vlan.number))
            self.write_line("   name {}".format(vlan_display_name(vlan)))
            self.write_line("   mac address learning")
            self.write_line("   state active")
            self.write_line("!")

    def _show_run_interfaces(self, ports):
        for port in ports:
            self.write_line("interface {}".format(port.name))
            if port.trunk_vlans is not None:
                self.write_line("   switchport trunk allowed vlan {}".format(to_vlan_ranges(port.trunk_vlans)))
            if port.mode is not None:
                self.write_line("   switchport mode {}".format(port.mode))
            if isinstance(port, VlanPort):
                if port.load_interval is not None:
                    self.write_line("   load-interval {}".format(port.load_interval))
                for ip in port.ips[:1]:
                    self.write_line("   ip address {}".format(ip))
                for ip in port.ips[1:]:
                    self.write_line("   ip address {} secondary".format(ip))
                if port.mpls_ip is False:
                    self.write_line("   no mpls ip")
                for ip_helper in port.ip_helpers:
                    self.write_line("   ip helper-address {}".format(ip_helper))
                for varp_address in sorted(port.varp_addresses):
                    self.write_line("   ip virtual-router address {}"
                                    .format(varp_address if varp_address.prefixlen < 32 else varp_address.ip))
