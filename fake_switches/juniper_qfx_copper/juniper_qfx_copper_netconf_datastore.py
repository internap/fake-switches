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
from fake_switches.netconf import NetconfError


class JuniperQfxCopperNetconfDatastore(JuniperNetconfDatastore):
    PORT_MODE_TAG = "interface-mode"
    MAX_AGGREGATED_ETHERNET_INTERFACES = 999
    SYSTEM_INTERFACES = ["irb"]

    def __init__(self, configuration):
        super(JuniperQfxCopperNetconfDatastore, self).__init__(configuration)

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
                raise self.member_list_trunk_vlan_error(port)
        return super(JuniperQfxCopperNetconfDatastore, self)._validate(configuration)

    def member_list_trunk_vlan_error(self, port):
        return FailingCommitResults([TrunkShouldHaveVlanMembers(interface=port.name),
                                     ConfigurationCheckOutFailed()])

    def _assert_no_garbage(self, port):
        pass

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

    def _format_protocol_port_name(self, port):
        return port.name


class TrunkShouldHaveVlanMembers(NetconfError):
    def __init__(self, interface):
        super(TrunkShouldHaveVlanMembers, self).__init__(msg='\nFor trunk interface, please ensure either vlan members is configured or inner-vlan-id-list is configured\n',
                                                         severity='error',
                                                         err_type='protocol',
                                                         tag='operation-failed',
                                                         info={'bad-element': 'ethernet-switching'},
                                                         path='\n[edit interfaces {} unit 0 family]\n'.format(interface))


class ConfigurationCheckOutFailed(NetconfError):
    def __init__(self):
        super(ConfigurationCheckOutFailed, self).__init__(msg='\nconfiguration check-out failed\n',
                                                          severity='error',
                                                          err_type='protocol',
                                                          tag='operation-failed',
                                                          info=None)


class FailingCommitResults(NetconfError):
    def __init__(self, netconf_errors):
        self.netconf_errors = netconf_errors

    def to_dict(self):
        return {'commit-results': [e.to_dict() for e in self.netconf_errors]}
