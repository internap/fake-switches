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

from fake_switches.dell.command_processor.enabled import DellEnabledCommandProcessor, to_vlan_ranges
from fake_switches.dell10g.command_processor.config import \
    Dell10GConfigCommandProcessor
from fake_switches.switch_configuration import VlanPort, AggregatedPort


class Dell10GEnabledCommandProcessor(DellEnabledCommandProcessor):
    configure_command_processor = Dell10GConfigCommandProcessor

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
            self.show_vlans()
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

    def show_vlans(self):

        self.write_line("")
        self.write_line("VLAN   Name                             Ports          Type")
        self.write_line("-----  ---------------                  -------------  --------------")

        for vlan in self.switch_configuration.vlans:
            self.write_line("{number: <5}  {name: <32} {ports: <13}  {type}".format(
                number=vlan.number, name=vlan_name(vlan), ports="",
                type="Default" if vlan.number == 1 else "Static"))

        self.write_line("")

    def do_terminal(self, *args):
        self.write_line("")

def vlan_name(vlan):
    if vlan.number == 1:
        return "default"
    elif vlan.name is not None:
        return vlan.name
    else:
        return "VLAN{}".format(vlan.number)
