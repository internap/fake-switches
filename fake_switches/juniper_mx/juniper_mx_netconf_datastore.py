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
from copy import deepcopy

from fake_switches.juniper.juniper_netconf_datastore import resolve_new_value, NS_JUNOS, resolve_operation, parse_range, \
    val, _restore_protocols_specific_data
from fake_switches.juniper_qfx_copper.juniper_qfx_copper_netconf_datastore import JuniperQfxCopperNetconfDatastore
from fake_switches.netconf import NetconfError, XML_ATTRIBUTES, first
from fake_switches.switch_configuration import AggregatedPort, VlanPort
from netaddr import IPNetwork


class JuniperMxNetconfDatastore(JuniperQfxCopperNetconfDatastore):
    VLANS_COLLECTION = "bridge-domains"
    VLANS_COLLECTION_OBJ = "domain"
    ETHERNET_SWITCHING_TAG = "bridge"
    MAX_AGGREGATED_ETHERNET_INTERFACES = 4091
    ETHER_OPTIONS_TAG = "gigether-options"
    MAX_PHYSICAL_PORT_NUMBER = 63
    MAX_MTU = 16360

    def parse_vlan_members(self, port, port_attributes):
        vlan_node = first(port_attributes.xpath("vlan-id"))
        if vlan_node is not None:
            if resolve_operation(vlan_node) == "delete":
                port.access_vlan = None
            else:
                port.access_vlan = vlan_node.text

        for member in port_attributes.xpath("vlan-id-list"):
            if resolve_operation(member) == "delete":
                if member.text:
                    port.trunk_vlans.remove(int(member.text))
                    if len(port.trunk_vlans) == 0:
                        port.trunk_vlans = None
                else:
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

    def parse_interface(self, conf, interface_node):
        port_name = val(interface_node, "name")

        if port_name == "irb":
            operation = resolve_operation(interface_node)
            if operation == "delete":
                for port in conf.get_vlan_ports():
                    conf.remove_port(port)
            else:
                self.parse_vlan_interfaces(conf, interface_node)
        else:
            super(JuniperMxNetconfDatastore, self).parse_interface(conf, interface_node)

    def parse_vlan_interfaces(self, conf, interface_node):
        for unit_node in interface_node.xpath("unit/name/.."):
            unit_id = val(unit_node, "name")

            port_name = "irb.{}".format(unit_id)

            port = conf.get_port(port_name)
            if port is None:
                linked_vlan = find_vlan_with_routing_interface(conf, port_name)
                port = self.original_configuration.new("VlanPort",
                                                       vlan_id=linked_vlan.number if linked_vlan else None,
                                                       name=port_name)
                port.vendor_specific["irb-unit"] = unit_id
                conf.add_port(port)

            inet = first(unit_node.xpath("family/inet".format(self.ETHERNET_SWITCHING_TAG)))
            if inet is not None:
                if first(inet.xpath("no-redirects")) is not None:
                    if resolve_operation(first(inet.xpath("no-redirects"))) == "delete":
                        port.ip_redirect = True
                    else:
                        port.ip_redirect = False

                for address in inet.xpath("address/name/.."):
                    ip = IPNetwork(val(address, "name"))
                    if resolve_operation(address) == "delete":
                        port.remove_ip(ip)
                    else:
                        port.add_ip(ip)

                        for vrrp_node in address.xpath("vrrp-group/name/.."):
                            group_id = val(vrrp_node, "name")
                            vrrp_group = port.get_vrrp_group(group_id)

                            if vrrp_group is not None and resolve_operation(vrrp_node) == "delete":
                                port.vrrps.remove(vrrp_group)
                            else:
                                if vrrp_group is None:
                                    vrrp_group = self.original_configuration.new("VRRP", group_id=group_id)
                                    port.vrrps.append(vrrp_group)

                                vrrp_group.related_ip_network = ip
                                vrrp_group.ip_addresses = [vip.text for vip in vrrp_node.xpath("virtual-address")
                                                           if resolve_operation(vip) != "delete"]
                                vrrp_group.priority = resolve_new_value(vrrp_node, "priority", vrrp_group.priority)

                                vrrp_group.preempt_delay_minimum = resolve_new_value(vrrp_node, "preempt/hold-time", vrrp_group.preempt_delay_minimum)
                                if resolve_operation(first(vrrp_node.xpath("preempt"))) == "delete":
                                    vrrp_group.preempt_delay_minimum = None

                                if first(vrrp_node.xpath("accept-data")) is not None:
                                    if resolve_operation(first(vrrp_node.xpath("accept-data"))) == "delete":
                                        vrrp_group.vendor_specific.pop("accept-data")
                                    else:
                                        vrrp_group.vendor_specific["accept-data"] = True
                                elif "accept-data" in vrrp_group.vendor_specific:
                                    vrrp_group.vendor_specific.pop("accept-data")

                                vrrp_group.vendor_specific["authentication-type"] = resolve_new_value(vrrp_node, "authentication-type", vrrp_group.vendor_specific.get("authentication-type"))
                                if vrrp_group.vendor_specific["authentication-type"] is None:
                                    vrrp_group.vendor_specific.pop("authentication-type")

                                vrrp_group.authentication = resolve_new_value(vrrp_node, "authentication-key", vrrp_group.authentication)

                                track = first(vrrp_node.xpath("track"))
                                if track is not None:
                                    if resolve_operation(track) == "delete":
                                        vrrp_group.track = {}
                                    else:
                                        vrrp_group.track = {val(track, "route/route_address"): val(track, "route/priority-cost")}

    def _validate(self, conf):
        ips = []
        for p in conf.ports:
            if hasattr(p, "ips"):
                ips = ips + p.ips
        if not len(ips) == len(set(ips)):
            raise IpAlreadyInUse("Overlapping subnet is configured")
        return super(JuniperMxNetconfDatastore, self)._validate(conf)

    def handle_interface_operation(self, conf, operation, port):
        if operation == 'delete' and isinstance(port, AggregatedPort):
            conf.remove_port(port)
        elif operation in ("delete", "replace"):
            backup = deepcopy(vars(port))

            port.reset()

            _restore_protocols_specific_data(backup, port)

    def parse_vlan_attributes(self, conf, vlan, vlan_node):
        vlan.number = resolve_new_value(vlan_node, "vlan-id", vlan.number, transformer=int)
        vlan.description = resolve_new_value(vlan_node, "description", vlan.description)

        vlan.vendor_specific["linked-port-vlan"] = resolve_new_value(vlan_node, "routing-interface",
                                                                     vlan.vendor_specific.get("linked-port-vlan"))

        if vlan.vendor_specific["linked-port-vlan"]:
            for port in conf.get_vlan_ports():
                if port.name == vlan.vendor_specific["linked-port-vlan"]:
                    port.vlan_id = vlan.number

    def _extract_interfaces(self, source):
        interfaces = []
        vlan_ports = []
        for port in source.ports:
            if isinstance(port, VlanPort):
                vlan_ports.append(port)
            else:
                interface_node = self.interface_to_etree(port)
                if interface_node:
                    interfaces.append({"interface": interface_node})

        interface_node = self.to_irb_interfaces(vlan_ports)
        if interface_node:
            interfaces.append({"interface": interface_node})
        return interfaces

    def to_irb_interfaces(self, vlan_ports):
        units = []
        for vlan_port in vlan_ports:
            unit = {
                "name": vlan_port.vendor_specific["irb-unit"]
            }

            inet = []
            if vlan_port.ips:
                inet.extend([{"address": self._address_etree(ip, vlan_port)} for ip in vlan_port.ips])

            if vlan_port.ip_redirect is False:
                inet.append({"no-redirects": {}})

            if inet:
                unit["family"] = {
                    "inet": inet
                }

            units.append({"unit": unit})

        if units:
            units.insert(0, {"name": "irb"})
            return units
        else:
            return None

    def _address_etree(self, ip, port):
        out = [{"name": str(ip)}]

        for vrrp in port.vrrps:
            if vrrp.related_ip_network == ip:
                vrrp_etree = [{"name": vrrp.group_id}]
                for ip_address in vrrp.ip_addresses:
                    vrrp_etree.append({"virtual-address": ip_address})

                    if vrrp.priority is not None:
                        vrrp_etree.append({"priority": vrrp.priority})

                    if vrrp.preempt_delay_minimum is not None:
                        vrrp_etree.append({"preempt": {"hold-time": vrrp.preempt_delay_minimum}})

                    if vrrp.vendor_specific.get("accept-data") is not None:
                        vrrp_etree.append({"accept-data": ""})

                    if vrrp.vendor_specific.get("authentication-type") is not None:
                        vrrp_etree.append({"authentication-type": vrrp.vendor_specific.get("authentication-type")})

                    if vrrp.authentication is not None:
                        vrrp_etree.append({"authentication-key": "this is {} but hashed".format(vrrp.authentication)})

                    for address, decrement in vrrp.track.items():
                        vrrp_etree.append({
                            "track": {
                                "route": {
                                    "route_address": address,
                                    "routing-instance": 'default',
                                    "priority-cost": decrement,
                                }}})

                out.append({"vrrp-group": vrrp_etree})

        return out

    def vlan_to_etree(self, vlan):
        etree = super(JuniperMxNetconfDatastore, self).vlan_to_etree(vlan)

        if vlan.vendor_specific.get("linked-port-vlan"):
            etree.append({"routing-interface": vlan.vendor_specific.get("linked-port-vlan")})

        return etree


def find_vlan_with_routing_interface(conf, interface_name):
    for vlan in conf.vlans:
        if vlan.vendor_specific.get("linked-port-vlan") == interface_name:
            return vlan

    return None


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

class IpAlreadyInUse(NetconfError):
    def __init__(self, message):
        super(IpAlreadyInUse, self).__init__(message,
                                             severity="error",
                                             err_type="protocol",
                                             tag="operation-not-supported")
