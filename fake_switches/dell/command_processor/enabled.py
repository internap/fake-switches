# Copyright 2015-2016 Internap.
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
from fake_switches.command_processing.base_command_processor import \
    BaseCommandProcessor
from fake_switches.switch_configuration import VlanPort, AggregatedPort


class DellEnabledCommandProcessor(BaseCommandProcessor):
    def __init__(self, config):
        super(DellEnabledCommandProcessor, self).__init__()
        self.config_processor = config

    def get_prompt(self):
        return "%s#" % self.switch_configuration.name

    def do_exit(self, *_):
        self.is_done = True

    def do_copy(self, *_):
        self.write_line("")
        self.write_line("This operation may take a few minutes.")
        self.write_line("Management interfaces will not be available during this time.")
        self.write_line("")
        self.write("Are you sure you want to save? (y/n) ")
        self.on_keystroke(self.continue_validate_copy)

    def continue_validate_copy(self, character):
        self.write_line("")
        self.write_line("")
        if character == 'y':
            self.switch_configuration.commit()
            self.write_line("Configuration Saved!")
        else:
            self.write_line("Configuration Not Saved!")
        self.show_prompt()

    def do_configure(self, *_):
        self.move_to(self.config_processor)

    def do_show(self, *args):
        if "running-config".startswith(args[0]):
            if len(args) == 1:
                self.write_line('!Current Configuration:')
                self.write_line('!System Description "PowerConnect 6224P, 3.3.7.3, VxWorks 6.5"')
                self.write_line('!System Software Version 3.3.7.3')
                self.write_line('!Cut-through mode is configured as disabled')
                self.write_line('!')
                self.write_line('configure')
                self.write_line('vlan database')
                if len(self.switch_configuration.vlans) > 0:
                    self.write_line('vlan %s' % ','.join(sorted([str(v.number) for v in self.switch_configuration.vlans])))
                self.write_line('exit')
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
                    self.write_line("\nERROR: Invalid input!\n")
        elif "vlan".startswith(args[0]):
            if len(args) == 1:
                self.show_vlan_page(list(self.switch_configuration.vlans))
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
                        self.show_vlan_page([vlan])


        elif "interfaces".startswith(args[0]) and "status".startswith(args[1]):
            self.show_page(self.get_interfaces_status_output())
        elif "version".startswith(args[0]):
            self.show_version()

    def get_port_configuration(self, port):
        conf = []
        if port.shutdown:
            conf.append('shutdown')
        if port.description:
            conf.append("description '{}'".format(port.description))
        if port.mode and port.mode != "access":
            conf.append('switchport mode {}'.format(port.mode))
        if port.access_vlan:
            conf.append('switchport access vlan {}'.format(port.access_vlan))
        if port.trunk_native_vlan:
            conf.append('switchport general pvid {}'.format(port.trunk_native_vlan))
        if port.trunk_vlans:
            conf.append('switchport {} allowed vlan add {}'.format(port.mode, to_vlan_ranges(port.trunk_vlans)))
        if port.spanning_tree is False:
            conf.append("spanning-tree disable")
        if port.spanning_tree_portfast:
            conf.append("spanning-tree portfast")
        if port.mtu:
            conf.append("mtu {}".format(port.mtu))
        if port.lldp_transmit is False:
            conf.append('no lldp transmit')
        if port.lldp_receive is False:
            conf.append('no lldp receive')
        if port.lldp_med_transmit_capabilities is False:
            conf.append('no lldp med transmit-tlv capabilities')
        if port.lldp_med_transmit_network_policy is False:
            conf.append('no lldp med transmit-tlv network-policy')

        return conf

    def get_vlan_port_configuration(self, port):
        conf = ["interface {}".format(port.name)]
        vlan = self.switch_configuration.get_vlan(port.vlan_id)
        if vlan.name:
            conf.append('name "{}"'.format(vlan.name))
        conf.append('exit')

        return conf

    def get_interfaces_status_output(self):
        output_lines = [
            "",
            "Port   Type                            Duplex  Speed    Neg  Link  Flow Control",
            "                                                             State Status",
            "-----  ------------------------------  ------  -------  ---- --------- ------------",
        ]
        interfaces = []
        bonds = []
        for port in self.switch_configuration.ports:
            if isinstance(port, AggregatedPort):
                bonds.append(port)
            elif not isinstance(port, VlanPort):
                interfaces.append(port)

        for port in sorted(interfaces, key=lambda e: e.name):
            output_lines.append(
                "{name: <5}  {type: <30}  {duplex: <6}  {speed: <7}  {neg: <4} {state: <9} {flow}".format(
                    name=port.name.split(" ")[-1], type="10G - Level" if "x" in port.name else "Gigabit - Level",
                    duplex="Full", speed="Unknown", neg="Auto", state="Down", flow="Inactive"))

        output_lines += [
            "",
            "",
            "Ch   Type                            Link",
            "                                     State",
            "---  ------------------------------  -----",
        ]

        for port in sorted(bonds, key=lambda e: int(e.name.split(" ")[-1])):
            output_lines.append("ch{name: <2} {type: <30}  {state}".format(
                name=port.name.split(" ")[-1], type="Link Aggregate", state="Down", flow="Inactive"))

        output_lines += [
            "",
            "Flow Control:Enabled",
        ]
        return output_lines

    def show_vlan_page(self, vlans):
        lines_per_pages = 18
        self.write_line("")
        self.write_line("VLAN       Name                         Ports          Type      Authorization")
        self.write_line("-----  ---------------                  -------------  -----     -------------")

        line_count = 0
        while len(vlans) > 0 and line_count < lines_per_pages:
            vlan = vlans.pop(0)
            ports_strings = self._build_port_strings(self.get_ports_for_vlan(vlan))

            self.write_line("{number: <5}  {name: <32} {ports: <13}  {type: <8}  {auth: <13}".format(
                number=vlan.number, name=vlan_name(vlan), ports=ports_strings[0],
                type="Default" if vlan.number == 1 else "Static", auth="Required"))
            line_count += 1
            for port_string in ports_strings[1:]:
                self.write_line("{number: <5}  {name: <32} {ports: <13}  {type: <8}  {auth: <13}".format(
                        number="", name="", ports=port_string, type="", auth=""))
                line_count += 1
        self.write_line("")

        if len(vlans) > 0:
            self.write("--More-- or (q)uit")
            self.on_keystroke(self.continue_vlan_pages, vlans)

    def get_ports_for_vlan(self, vlan):
        ports = []
        for port in self.switch_configuration.ports:
            if not isinstance(port, VlanPort):
                if (port.trunk_vlans and vlan.number in port.trunk_vlans) or port.access_vlan == vlan.number:
                    ports.append(port)
        return ports

    def _build_port_strings(self, ports):
        port_range_list = group_sequences(ports, are_in_sequence=self._are_in_sequence)
        port_list = []
        for port_range in port_range_list:
            first_details = self._get_interface_details(port_range[0].name)
            if len(port_range) == 1:
                port_list.append("{}{}".format(first_details.port_prefix, first_details.port))
            else:
                port_list.append("{0}{1}-{0}{2}".format(first_details.port_prefix, first_details.port, self._get_interface_details(port_range[-1].name).port))
        return _assemble_elements_on_lines(port_list, max_line_char=13)

    def _get_interface_details(self, interface_name):
        interface_descriptor = namedtuple('InterfaceDescriptor', "interface port_prefix port")
        re_port_number = re.compile('(\d/[a-zA-Z]+)(\d+)')
        interface, slot_descriptor = interface_name.split(" ")
        port_prefix, port = re_port_number.match(slot_descriptor).groups()
        return interface_descriptor(interface, port_prefix, int(port))

    def _are_in_sequence(self, a, b):
        details_a = self._get_interface_details(a.name)
        details_b = self._get_interface_details(b.name)
        return details_a.port + 1 == details_b.port and details_a.port_prefix == details_b.port_prefix

    def continue_vlan_pages(self, lines, _):
        self.write_line("\r                     ")
        self.write_line("")

        self.show_vlan_page(lines)

        if not self.awaiting_keystroke:
            self.show_prompt()

    def show_page(self, lines):
        lines_per_pages = 23

        line = 0
        while len(lines) > 0 and line < lines_per_pages:
            self.write_line(lines.pop(0))
            line += 1

        if len(lines) > 0:
            self.write("--More-- or (q)uit")
            self.on_keystroke(self.continue_pages, lines)

    def continue_pages(self, lines, _):
        self.write_line("")

        self.show_page(lines)

        if not self.awaiting_keystroke:
            self.write_line("")
            self.show_prompt()

    def show_version(self):
        self.write_line("")
        self.write_line("Image Descriptions")
        self.write_line("")
        self.write_line(" image1 : default image")
        self.write_line(" image2 :")
        self.write_line("")
        self.write_line("")
        self.write_line(" Images currently available on Flash")
        self.write_line("")
        self.write_line("--------------------------------------------------------------------")
        self.write_line(" unit      image1      image2     current-active        next-active")
        self.write_line("--------------------------------------------------------------------")
        self.write_line("")
        self.write_line("    1     3.3.7.3     3.3.7.3             image1             image1")
        self.write_line("    2     3.3.7.3    3.3.13.1             image1             image1")
        self.write_line("")


def vlan_name(vlan):
    if vlan.number == 1:
        return "Default"
    elif vlan.name is not None:
        return vlan.name
    else:
        return ""

def to_vlan_ranges(vlans):
    if len(vlans) == 0:
        return "none"

    ranges = group_sequences(vlans, are_in_sequence=lambda a, b: a + 1 == b)

    return ",".join([to_range_string(r) for r in ranges])


def to_range_string(range_array):
    if len(range_array) < 2:
        return ",".join([str(n) for n in range_array])
    else:
        return "%s-%s" % (range_array[0], range_array[-1])


def _is_vlan_id(text):
    try:
        number = int(text)
    except ValueError:
        return False

    return 1 <= number <= 4093


def _assemble_elements_on_lines(elements, max_line_char, separator=','):
    lines = [""]
    for element in elements:
        if len(lines[-1]) > 1:
            lines[-1] += separator
        new_line_length = len(lines[-1]) + len(element)
        if new_line_length <= max_line_char:
            lines[-1] += element
        else:
            lines.append(element)
    return lines
