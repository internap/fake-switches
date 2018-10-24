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
            processor.write_line("  Up 00 minutes, 00 seconds")


def _to_cidr(ip):
    return "{}/{}".format(ip["address"], ip["maskLen"])


def _mac6to3(mac6):
    parts = mac6.split(":")
    return ".".join(parts[part_id] + parts[part_id + 1] for part_id in range(0, 3))
