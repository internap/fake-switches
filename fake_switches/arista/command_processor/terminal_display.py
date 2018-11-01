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
from fake_switches.arista.command_processor import short_port_name
from fake_switches.switch_configuration import split_port_name


class TerminalDisplay(object):
    def invalid_command(self, processor, message, json_data=None):
        self._error(processor, message)

    def invalid_result(self, processor, message, json_data=None):
        self._error(processor, message)

    def _error(self, processor, message):
        processor.write_line("% {}".format(message))

    def warning(self, processor, message, json_data=None):
        processor.write_line("! {}".format(message))

    def show_vlans(self, processor, vlans_json):
        processor.write_line("VLAN  Name                             Status    Ports")
        processor.write_line("----- -------------------------------- --------- -------------------------------")

        for vlan_number in sorted(vlans_json["vlans"].keys(), key=lambda e: int(e)):
            processor.write_line("{: <5} {: <32} active"
                                 .format(vlan_number, vlans_json["vlans"][vlan_number]["name"]))

        processor.write_line("")

    def show_interface(self, processor, interfaces_json):
        for interface in sorted(interfaces_json["interfaces"].values(), key=lambda e: int(split_port_name(e["name"])[1])):
            if interface["name"].startswith("Vlan"):
                self._show_vlan_port(processor, interface)
            else:
                self._show_phys_port(processor, interface)

    def _show_vlan_port(self, processor, interface):
        processor.write_line("{} is up, line protocol is up (connected)".format(interface["name"]))
        processor.write_line("  Hardware is Vlan, address is {} (bia {})"
                             .format(_mac6to3(interface["physicalAddress"]),
                                     _mac6to3(interface["burnedInAddress"])))
        int_address = next(iter(interface["interfaceAddress"]), None)
        if int_address is not None:
            primary = _to_cidr(int_address["primaryIp"])
            if primary == "0.0.0.0/0":
                processor.write_line("  No Internet protocol address assigned")
            else:
                processor.write_line("  Internet address is {}".format(primary))
                for secondary_ip in int_address["secondaryIpsOrderedList"]:
                    processor.write_line("  Secondary address is {}".format(_to_cidr(secondary_ip)))
                processor.write_line("  Broadcast address is 255.255.255.255")
        processor.write_line("  IP MTU 1500 bytes")
        processor.write_line("  Up 0 minutes, 0 seconds")

    def _show_phys_port(self, processor, interface):
        processor.write_line("{} is up, line protocol is up (connected)".format(interface["name"]))
        processor.write_line("  Hardware is Ethernet, address is {} (bia {})"
                             .format(_mac6to3(interface["physicalAddress"]),
                                     _mac6to3(interface["burnedInAddress"])))
        processor.write_line("  Ethernet MTU 9214 bytes")
        processor.write_line("  Full-duplex, Unconfigured, auto negotiation: off, uni-link: n/a")
        processor.write_line("  Up 0 minutes, 0 seconds")
        processor.write_line("  Loopback Mode : None")
        processor.write_line("  0 link status changes since last clear")
        processor.write_line("  Last clearing of \"show interface\" counters never")
        processor.write_line("  0 minutes input rate 0 bps (- with framing overhead), 0 packets/sec")
        processor.write_line("  0 minutes output rate 0 bps (- with framing overhead), 0 packets/sec")
        processor.write_line("     0 packets input, 0 bytes")
        processor.write_line("     Received 0 broadcasts, 0 multicast")
        processor.write_line("     0 runts, 0 giants")
        processor.write_line("     0 input errors, 0 CRC, 0 alignment, 0 symbol, 0 input discards")
        processor.write_line("     0 PAUSE input")
        processor.write_line("     0 packets output, 0 bytes")
        processor.write_line("     Sent 0 broadcasts, 0 multicast")
        processor.write_line("     0 output errors, 0 collisions")
        processor.write_line("     0 late collision, 0 deferred, 0 output discards")
        processor.write_line("     0 PAUSE output")

    def show_interface_switchport(self, processor, switchport_json):
        ports = switchport_json["switchports"].items()
        if len(ports) > 1:
            processor.write_line("Default switchport mode: access")
            processor.write_line("")

        for name, properties in sorted(iter(ports), key=lambda item: int(split_port_name(item[0])[1])):
            switchport = properties["switchportInfo"]
            processor.write_line("Name: {}"
                                 .format(short_port_name(name)))

            processor.write_line("Switchport: {}"
                                 .format("Enabled" if properties["enabled"] else "Disabled"))

            processor.write_line("Administrative Mode: {}"
                                 .format("static access" if switchport["mode"] == "access" else switchport["mode"]))

            processor.write_line("Operational Mode: {}"
                                 .format("static access" if switchport["mode"] == "access" else switchport["mode"]))

            processor.write_line("MAC Address Learning: {}"
                                 .format("enabled" if switchport["macLearning"] else "disabled"))

            processor.write_line("Dot1q ethertype/TPID: {} ({})"
                                 .format(switchport["tpid"], "active" if switchport["tpidStatus"] else "inactive"))

            processor.write_line("Dot1q Vlan Tag Required (Administrative/Operational): {}"
                                 .format("Yes/Yes" if switchport["dot1qVlanTagRequiredStatus"] else "No/No"))

            processor.write_line("Access Mode VLAN: {} ({})"
                                 .format(switchport["accessVlanId"], switchport["accessVlanName"]))

            processor.write_line("Trunking Native Mode VLAN: {} ({})"
                                 .format(switchport["trunkingNativeVlanId"], switchport["trunkingNativeVlanName"]))

            processor.write_line("Administrative Native VLAN tagging: disabled")

            processor.write_line("Trunking VLANs Enabled: {}"
                                 .format(switchport["trunkAllowedVlans"]))

            processor.write_line("Static Trunk Groups:")

            processor.write_line("Dynamic Trunk Groups:")

            processor.write_line("Source interface filtering: {}"
                                 .format(switchport["sourceportFilterMode"]))

            processor.write_line("")


def _to_cidr(ip):
    return "{}/{}".format(ip["address"], ip["maskLen"])


def _mac6to3(mac6):
    parts = mac6.split(":")
    return ".".join(parts[part_id] + parts[part_id + 1] for part_id in range(0, 3))
