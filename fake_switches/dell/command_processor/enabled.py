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

from fake_switches import group_sequences

from fake_switches.command_processing.base_command_processor import \
    BaseCommandProcessor
from fake_switches.dell.command_processor.config import \
    DellConfigCommandProcessor
from fake_switches.switch_configuration import VlanPort, AggregatedPort


class EnabledCommandProcessor(BaseCommandProcessor):
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
            self.write_line("Configuration Saved!")
        else:
            self.write_line("Configuration Not Saved!")
        self.show_prompt()

    def do_configure(self, *_):
        self.move_to(DellConfigCommandProcessor)

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
            vlan_lines = []
            for vlan in self.switch_configuration.vlans:
                vlan_lines.append("%-5s  %-32s %-13s  %-8s  %-13s" % (
                    vlan.number, vlan_name(vlan), "",
                    "Default" if vlan.number == 1 else "Static", "Required"))

            self.show_vlan_page(vlan_lines)
        elif "interfaces".startswith(args[0]) and "status".startswith(args[1]):
            self.show_page(self.get_interfaces_status_output())

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

    def show_vlan_page(self, lines):
        lines_per_pages = 18
        self.write_line("")
        self.write_line("VLAN       Name                         Ports          Type      Authorization")
        self.write_line("-----  ---------------                  -------------  -----     -------------")

        line = 0
        while len(lines) > 0 and line < lines_per_pages:
            self.write_line(lines.pop(0))
            line += 1

        self.write_line("")

        if len(lines) > 0:
            self.write("--More-- or (q)uit")
            self.on_keystroke(self.continue_vlan_pages, lines)

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

