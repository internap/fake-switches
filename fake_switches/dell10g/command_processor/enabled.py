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
import re
from collections import namedtuple

from fake_switches import group_sequences
from fake_switches.dell.command_processor.enabled import DellEnabledCommandProcessor, to_vlan_ranges, _is_vlan_id, \
    _assemble_elements_on_lines
from fake_switches.switch_configuration import VlanPort, AggregatedPort


class Dell10GEnabledCommandProcessor(DellEnabledCommandProcessor):
    def __init__(self, config):
        super(Dell10GEnabledCommandProcessor, self).__init__(config)

    def get_port_configuration(self, port):
        conf = []
        if port.shutdown:
            conf.append('shutdown')
        if port.description:
            conf.append("description \"{}\"".format(port.description))
        if port.mode and port.mode != "access":
            conf.append('switchport mode {}'.format(port.mode))
        if port.access_vlan:
            conf.append('switchport access vlan {}'.format(port.access_vlan))
        if port.trunk_native_vlan:
            conf.append('switchport general pvid {}'.format(port.trunk_native_vlan))
        if port.trunk_vlans:
            if port.mode == "general":
                conf.append('switchport {} allowed vlan add {}'.format(port.mode, to_vlan_ranges(port.trunk_vlans)))
            else:
                conf.append('switchport trunk allowed vlan {}'.format(to_vlan_ranges(port.trunk_vlans)))

        if port.spanning_tree is False:
            conf.append("spanning-tree disable")
        if port.spanning_tree_portfast:
            conf.append("spanning-tree portfast")
        if port.lldp_transmit is False:
            conf.append('no lldp transmit')
        if port.lldp_receive is False:
            conf.append('no lldp receive')
        if port.lldp_med is False:
            conf.append('no lldp med')
        if port.lldp_med_transmit_capabilities is False:
            conf.append('no lldp med transmit-tlv capabilities')
        if port.lldp_med_transmit_network_policy is False:
            conf.append('no lldp med transmit-tlv network-policy')

        return conf

    def do_show(self, *args):
        if "running-config".startswith(args[0]):
            if len(args) == 1:
                self.write_line('!Current Configuration:')
                self.write_line('!System Description "............."')
                self.write_line('!System Software Version 3.3.7.3')
                self.write_line('!Cut-through mode is configured as disabled')
                self.write_line('!')
                self.write_line('configure')
                self.write_vlans()
                for port in self.switch_configuration.ports:
                    port_config = self.get_port_configuration(port)

                    if len(port_config) > 0:
                        self.write_line('interface %s' % port.name)
                        for item in port_config:
                            self.write_line(item)
                        self.write_line('exit')
                        self.write_line('!')
                self.write_line('exit')
            elif "interface".startswith(args[1]):
                interface_name = ' '.join(args[2:])

                port = self.switch_configuration.get_port_by_partial_name(interface_name)
                if port:
                    if isinstance(port, VlanPort):
                        config = self.get_vlan_port_configuration(port)
                    else:
                        config = self.get_port_configuration(port)
                    if len(config) > 0:
                        for line in config:
                            self.write_line(line)
                    else:
                        self.write_line("")
                    self.write_line("")
                else:
                    self.write_line("")
                    self.write_line("An invalid interface has been used for this function")

        elif "vlan".startswith(args[0]):
            if len(args) == 1:
                self.show_vlans(self.switch_configuration.vlans)
            elif args[1] == "id":
                if len(args) < 3:
                    self.write_line("")
                    self.write_line("Command not found / Incomplete command. Use ? to list commands.")
                    self.write_line("")
                elif not _is_vlan_id(args[2]):
                    self.write_line("                     ^")
                    self.write_line("Invalid input. Please specify an integer in the range 1 to 4093.")
                    self.write_line("")
                else:
                    vlan = self.switch_configuration.get_vlan(int(args[2]))
                    if vlan is None:
                        self.write_line("")
                        self.write_line("ERROR: This VLAN does not exist.")
                        self.write_line("")
                    else:
                        self.show_vlans([vlan])

        elif "interfaces".startswith(args[0]) and "status".startswith(args[1]):
            self.show_interfaces_status()

    def write_vlans(self):
        named_vlans = []
        other_vlans = []
        for v in self.switch_configuration.vlans:
            if v.name is not None:
                named_vlans.append(v)
            else:
                other_vlans.append(v)

        for vlan in named_vlans:
            self.write_line('vlan {}'.format(vlan.number))
            if vlan.name is not None:
                self.write_line('name {}'.format(vlan.name))
            self.write_line('exit')

        self.write_line('vlan {}'.format(to_vlan_ranges([v.number for v in other_vlans])))
        self.write_line('exit')

    def show_interfaces_status(self):

        self.write_line("")
        self.write_line("Port      Description               Vlan  Duplex Speed   Neg  Link   Flow Ctrl")
        self.write_line("                                                              State  Status")
        self.write_line("--------- ------------------------- ----- ------ ------- ---- ------ ---------")

        for port in self.switch_configuration.ports:
            if not isinstance(port, AggregatedPort):
                self.write_line(
                    "Te{name: <7} {desc: <25} {vlan: <5} {duplex: <6} {speed: <7} {neg: <4} {state: <6} {flow}".format(
                        name=port.name.split(" ")[-1], desc=port.description[:25] if port.description else "", vlan="",
                        duplex="Full", speed="10000", neg="Auto", state="Up", flow="Active"))

        self.write_line("")
        self.write_line("")

        self.write_line("Port    Description                    Vlan  Link")
        self.write_line("Channel                                      State")
        self.write_line("------- ------------------------------ ----- -------")

        for port in self.switch_configuration.ports:
            if isinstance(port, AggregatedPort):
                self.write_line(
                    "Po{name: <7} {desc: <28} {vlan: <5} {state}".format(
                        name=port.name.split(" ")[-1], desc=port.description[:28] if port.description else "",
                        vlan="trnk", state="Up"))

        self.write_line("")

    def show_vlans(self, vlans):

        self.write_line("")
        self.write_line("VLAN   Name                             Ports          Type")
        self.write_line("-----  ---------------                  -------------  --------------")

        for vlan in vlans:
            ports_strings = self._build_port_strings(self.get_ports_for_vlan(vlan))
            self.write_line("{number: <5}  {name: <32} {ports: <13}  {type}".format(
                number=vlan.number, name=vlan_name(vlan), ports=ports_strings[0],
                type="Default" if vlan.number == 1 else "Static"))
            for port_string in ports_strings[1:]:
                self.write_line("{number: <5}  {name: <32} {ports: <13}  {type}".format(
                        number="", name="", ports=port_string, type=""))
        self.write_line("")

    def _build_port_strings(self, ports):
        port_range_list = group_sequences(ports, are_in_sequence=self._are_in_sequence)
        port_list = []
        for port_range in port_range_list:
            first_details = self._get_interface_details(port_range[0].name)
            if len(port_range) == 1:
                port_list.append("Te{}{}".format(first_details.port_prefix, first_details.port))
            else:
                port_list.append("Te{0}{1}-{2}".format(first_details.port_prefix, first_details.port, self._get_interface_details(port_range[-1].name).port))
        return _assemble_elements_on_lines(port_list, max_line_char=13)

    def _get_interface_details(self, interface_name):
        interface_descriptor = namedtuple('InterfaceDescriptor', "interface port_prefix port")
        re_port_number = re.compile('(\d/\d/)(\d+)')
        interface, slot_descriptor = interface_name.split(" ")
        port_prefix, port = re_port_number.match(slot_descriptor).groups()
        return interface_descriptor(interface, port_prefix, int(port))

    def do_terminal(self, *args):
        self.write_line("")

def vlan_name(vlan):
    if vlan.number == 1:
        return "default"
    elif vlan.name is not None:
        return vlan.name
    else:
        return "VLAN{}".format(vlan.number)
