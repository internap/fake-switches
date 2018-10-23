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


class TerminalDisplay(object):
    def invalid_command(self, processor, message, json_data=None):
        self._error(processor, message)

    def invalid_result(self, processor, message, json_data=None):
        self._error(processor, message)

    def _error(self, processor, message):
        processor.write_line("% {}".format(message))

    def show_vlans(self, processor, vlans_json):
        processor.write_line("VLAN  Name                             Status    Ports")
        processor.write_line("----- -------------------------------- --------- -------------------------------")

        for vlan_number in sorted(vlans_json["vlans"].keys(), key=lambda e: int(e)):
            processor.write_line("{: <5} {: <32} active"
                                      .format(vlan_number, vlans_json["vlans"][vlan_number]["name"]))

        processor.write_line("")
