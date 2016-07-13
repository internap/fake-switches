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
from fake_switches.switch_configuration import AggregatedPort

from fake_switches.juniper.juniper_netconf_datastore import JuniperNetconfDatastore, resolve_new_value, port_is_in_trunk_mode
from fake_switches.netconf import FailingCommitResults, TrunkShouldHaveVlanMembers, ConfigurationCheckOutFailed


class JuniperQfxCopperNetconfDatastore(JuniperNetconfDatastore):
    def __init__(self, configuration):
        super(JuniperQfxCopperNetconfDatastore, self).__init__(configuration)

        self.PORT_MODE_TAG = "interface-mode"
        self.MAX_AGGREGATED_ETHERNET_INTERFACES = 999

    def apply_trunk_native_vlan(self, interface_data, port):
        if port.trunk_native_vlan is not None:
            interface_data.append({"native-vlan-id": str(port.trunk_native_vlan)})

    def parse_trunk_native_vlan(self, interface_node, port):
        native_vlan_id_node = interface_node.xpath("native-vlan-id")
        if len(native_vlan_id_node) == 1 and native_vlan_id_node[0].text is not None:
            return resolve_new_value(interface_node, "native-vlan-id", port.trunk_native_vlan,
                                 transformer=int)
        return port.trunk_native_vlan

    def get_trunk_native_vlan_node(self, interface_node):
        return interface_node.xpath("native-vlan-id")

    def _validate(self, configuration):
        for port in configuration.ports:
            if port_is_in_trunk_mode(port) and \
                    (port.trunk_vlans is None or len(port.trunk_vlans) == 0):
                raise FailingCommitResults([TrunkShouldHaveVlanMembers(interface=port.name),
                                            ConfigurationCheckOutFailed()])
        return super(JuniperQfxCopperNetconfDatastore, self)._validate(configuration)

    def _to_terse(self, port):
        interface = [
            {"name": "\n{}\n".format(port.name)},
            {"admin-status": "\ndown\n" if port.shutdown else "\nup\n"},
            {"oper-status": "\ndown\n"}
        ]

        if port.description is not None:
            interface.append({"description": "\n{}\n".format(port.description)})

        if port.vendor_specific.get("has-ethernet-switching"):
            interface.extend([
                {"logical-interface": [
                    {"name": "\n{}.0\n".format(port.name)},
                    {"admin-status": "\ndown\n" if port.shutdown else "\nup\n"},
                    {"oper-status": "\ndown\n"},
                    {"filter-information": {}},
                    {"address-family": {
                        "address-family-name": "\neth-switch\n"
                    }}
                ]}
            ])
        elif port.aggregation_membership is None and not isinstance(port, AggregatedPort):
            interface.extend([
                {"logical-interface": [
                    {"name": "\n{}.16386\n".format(port.name)},
                    {"admin-status": "\ndown\n" if port.shutdown else "\nup\n"},
                    {"oper-status": "\ndown\n"},
                    {"filter-information": {}}
                ]}
            ])

        return {"physical-interface": interface}
