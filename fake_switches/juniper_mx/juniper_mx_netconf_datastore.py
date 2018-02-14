# Copyright 2015-2018 Internap.
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
from copy import deepcopy

from fake_switches.juniper.juniper_netconf_datastore import resolve_new_value, NS_JUNOS, resolve_operation, parse_range, \
    val, _restore_protocols_specific_data
from fake_switches.juniper_qfx_copper.juniper_qfx_copper_netconf_datastore import JuniperQfxCopperNetconfDatastore
from fake_switches.netconf import NetconfError, XML_ATTRIBUTES
from fake_switches.switch_configuration import AggregatedPort


class JuniperMxNetconfDatastore(JuniperQfxCopperNetconfDatastore):
    VLANS_COLLECTION = "bridge-domains"
    VLANS_COLLECTION_OBJ = "domain"
    ETHERNET_SWITCHING_TAG = "bridge"
    MAX_AGGREGATED_ETHERNET_INTERFACES = 4091
    ETHER_OPTIONS_TAG = "gigether-options"
    MAX_PHYSICAL_PORT_NUMBER = 63
    MAX_MTU = 16360

    def parse_vlan_members(self, port, port_attributes):
        port.access_vlan = resolve_new_value(port_attributes, "vlan-id", port.access_vlan, transformer=int)

        for member in port_attributes.xpath("vlan-id-list"):
            if resolve_operation(member) == "delete":
                port.trunk_vlans.remove(int(member.text))
                if len(port.trunk_vlans) == 0:
                    port.trunk_vlans = None
            else:
                if port.trunk_vlans is None:
                    port.trunk_vlans = []
                port.trunk_vlans += parse_range(member.text)

    def ethernet_switching_to_etree(self, port, interface_data):
        ethernet_switching = []
        if port.mode is not None:
            ethernet_switching.append({self.PORT_MODE_TAG: port.mode})
        if port.access_vlan:
            ethernet_switching.append({"vlan-id": str(port.access_vlan)})

        if port.trunk_vlans:
            ethernet_switching += [{"vlan-id-list": str(v)} for v in port.trunk_vlans]

        if ethernet_switching:
            interface_data.append({"unit": {
                "name": "0",
                "family": {
                    self.ETHERNET_SWITCHING_TAG: ethernet_switching
                }
            }})

    def member_list_trunk_vlan_error(self, port):
        return FailingCommitResults([TrunkShouldHaveVlanMembers(interface=port.name),
                                     ConfigurationCheckOutFailed()])

    def validate_vlan_config(self, port, vlan_list):
        pass

    def parse_interfaces(self, conf, etree_conf):
        handled_elements = []
        for interface_node in etree_conf.xpath("interfaces/interface/name/.."):
            handled_elements.append(interface_node)

            port_name = val(interface_node, "name")

            port = conf.get_port_by_partial_name(port_name)
            if port is None and re.match("^ae\d+$",port_name):
                port = self.original_configuration.new("AggregatedPort", port_name)
                port.vendor_specific["has-ethernet-switching"] = True
                conf.add_port(port)

            self.raise_for_invalid_interface(port_name, self.MAX_AGGREGATED_ETHERNET_INTERFACES)

            operation = resolve_operation(interface_node)
            if operation == 'delete' and isinstance(port, AggregatedPort):
                conf.remove_port(port)
            elif operation in ("delete", "replace"):
                backup = deepcopy(vars(port))

                port.reset()

                _restore_protocols_specific_data(backup, port)

            if operation != "delete":
                self.apply_interface_data(interface_node, port)

        return handled_elements

class TrunkShouldHaveVlanMembers(NetconfError):
    def __init__(self, interface):
        super(TrunkShouldHaveVlanMembers, self).__init__(msg="mgd: 'interface-mode trunk' must be defined with either "
                                                             "'vlan-id-list','isid-list', 'inner-vlan-id-list' or the "
                                                             "interface must be configured for 'protocols mvrp'",
                                                         severity='error',
                                                         err_type='application',
                                                         tag='invalid-value',
                                                         info={'bad-element': 'interface-mode trunk'},
                                                         path='[edit interfaces {} unit 0 family bridge interface-mode]'.format(
                                                             interface))


class ConfigurationCheckOutFailed(NetconfError):
    def __init__(self):
        super(ConfigurationCheckOutFailed, self).__init__(msg='commit failed: (statements constraint check failed)',
                                                          severity='error',
                                                          err_type='protocol',
                                                          tag='operation-failed',
                                                          info=None)


class FailingCommitResults(NetconfError):
    def __init__(self, netconf_errors):
        self.netconf_errors = netconf_errors

    def to_dict(self):
        return {
            'commit-results': {
                'routing-engine': [
                  {XML_ATTRIBUTES: {"{" + NS_JUNOS + "}style": "show-name"}},
                  {'name': "re0"},
              ] + [e.to_dict() for e in self.netconf_errors]
            }
        }
