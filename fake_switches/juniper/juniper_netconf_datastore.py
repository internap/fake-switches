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

from copy import deepcopy
import re

from lxml import etree

from fake_switches.netconf import XML_NS, XML_ATTRIBUTES, CANDIDATE, RUNNING, AlreadyLocked, NetconfError, CannotLockUncleanCandidate, first, \
    UnknownVlan
from fake_switches.netconf.netconf_protocol import dict_2_etree
from fake_switches.switch_configuration import AggregatedPort


NS_JUNOS = "http://xml.juniper.net/junos/11.4R1/junos"


class JuniperNetconfDatastore(object):
    def __init__(self, configuration):
        self.original_configuration = configuration
        self.configurations = {}
        self.reset()

        self.PORT_MODE_TAG = "port-mode"

    def reset(self):
        self.configurations = {
            CANDIDATE: deepcopy(self.original_configuration),
            RUNNING: self.original_configuration,
        }

        self.configurations[CANDIDATE].routing_engine = None

    def to_etree(self, source):
        etree.register_namespace("junos", NS_JUNOS)

        return dict_2_etree({
            "data": {
                "configuration": {
                    XML_NS: 'http://xml.juniper.net/xnm/1.1/xnm',
                    XML_ATTRIBUTES: {
                        "xmlns":"http://xml.juniper.net/xnm/1.1/xnm",
                        "{" + NS_JUNOS + "}commit-seconds": "1411928899",
                        "{" + NS_JUNOS + "}commit-localtime": "2014-09-28 14:28:19 EDT",
                        "{" + NS_JUNOS + "}commit-user": "admin"
                    },
                    "interfaces": [{"interface": self.interface_to_etree(port)} for port in self.configurations[source].ports],
                    "protocols": extract_protocols(self.configurations[source]),
                    "vlans": [{"vlan": vlan_to_etree(vlan)} for vlan in self.configurations[source].vlans]
                }
            }
        })

    def edit(self, target, etree_conf):
        conf = self.configurations[target]
        handled_elements = []

        handled_elements += self.parse_vlans(conf, etree_conf)
        handled_elements += self.parse_interfaces(conf, etree_conf)
        handled_elements += parse_protocols(conf, etree_conf)

        raise_for_unused_nodes(etree_conf, handled_elements)

    def commit_candidate(self):
        validate(self.configurations[CANDIDATE])
        for updated_vlan in self.configurations[CANDIDATE].vlans:
            actual_vlan = self.configurations[RUNNING].get_vlan_by_name(updated_vlan.name)
            if not actual_vlan:
                self.configurations[RUNNING].add_vlan(deepcopy(updated_vlan))
            else:
                actual_vlan.number = updated_vlan.number
                actual_vlan.description = updated_vlan.description

        for p in self.configurations[RUNNING].vlans[:]:
            if self.configurations[CANDIDATE].get_vlan_by_name(p.name) is None:
                self.configurations[RUNNING].remove_vlan(p)

        for updated_port in self.configurations[CANDIDATE].ports:
            actual_port = self.configurations[RUNNING].get_port_by_partial_name(updated_port.name)

            if actual_port is None:
                actual_port = deepcopy(updated_port)
                self.configurations[RUNNING].add_port(actual_port)
            else:
                actual_port.mode = updated_port.mode
                actual_port.shutdown = updated_port.shutdown
                actual_port.description = updated_port.description
                actual_port.access_vlan = updated_port.access_vlan
                actual_port.trunk_vlans = updated_port.trunk_vlans
                actual_port.trunk_native_vlan = updated_port.trunk_native_vlan
                actual_port.speed = updated_port.speed
                actual_port.auto_negotiation = updated_port.auto_negotiation
                actual_port.aggregation_membership = updated_port.aggregation_membership
                actual_port.lldp_transmit = updated_port.lldp_transmit
                actual_port.lldp_receive = updated_port.lldp_receive
                actual_port.vendor_specific = updated_port.vendor_specific

                if isinstance(actual_port, AggregatedPort):
                    actual_port.lacp_active = updated_port.lacp_active
                    actual_port.lacp_periodic = updated_port.lacp_periodic

        for p in self.configurations[RUNNING].ports[:]:
            if self.configurations[CANDIDATE].get_port_by_partial_name(p.name) is None:
                self.configurations[RUNNING].remove_port(p)


    def lock(self, target):
        if etree.tostring(self.to_etree(RUNNING)) != etree.tostring(self.to_etree(CANDIDATE)):
            raise CannotLockUncleanCandidate()
        if self.configurations[target].locked:
            raise AlreadyLocked()
        self.configurations[target].locked = True

    def unlock(self, target):
        self.configurations[target].locked = False

    def interface_to_etree(self, port):
        interface_data = [
            {"name": port.name}
        ]

        if port.description is not None:
            interface_data.append({"description": port.description})

        if port.shutdown is not None:
            interface_data.append({("disable" if port.shutdown else "enable"): ""})

        if isinstance(port, AggregatedPort):
            aggregated_ether_options = {}
            if port.speed is not None:
                aggregated_ether_options["link-speed"] = port.speed

            if port.auto_negotiation is True:
                aggregated_ether_options["auto-negotiation"] = {}

            lacp_options = {}
            if port.lacp_active is True:
                lacp_options["active"] = {}

            if port.lacp_periodic is not None:
                lacp_options["periodic"] = port.lacp_periodic

            if len(lacp_options.items()) > 0:
                aggregated_ether_options["lacp"] = lacp_options

            if len(aggregated_ether_options.items()) > 0:
                interface_data.append({"aggregated-ether-options": aggregated_ether_options})
        else:
            ether_options = {}
            if port.speed is not None:
                ether_options["speed"] = {"ethernet-{0}".format(port.speed): {}}

            if port.auto_negotiation is True:
                ether_options["auto-negotiation"] = {}

            if port.aggregation_membership is not None:
                ether_options["ieee-802.3ad"] = {"bundle": port.aggregation_membership}

            if len(ether_options.items()) > 0:
                interface_data.append({"ether-options": ether_options})

        if port.vendor_specific["has-ethernet-switching"]:
            ethernet_switching = {}
            if port.mode is not None:
                ethernet_switching[self.PORT_MODE_TAG] = port.mode

            if port.trunk_native_vlan is not None:
                ethernet_switching["native-vlan-id"] = str(port.trunk_native_vlan)

            vlans = port.trunk_vlans or []
            if port.access_vlan: vlans.append(port.access_vlan)

            if len(vlans) > 0:
                ethernet_switching["vlan"] = [{"members": str(v)} for v in vlans]

            if len(ethernet_switching.items()) > 0 or not isinstance(port, AggregatedPort):
                interface_data.append({"unit": {
                    "name": "0",
                    "family": {
                        "ethernet-switching": ethernet_switching
                    }
                }})

        return interface_data

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

            operation = resolve_operation(interface_node)
            if operation == "delete" and isinstance(port, AggregatedPort):
                conf.remove_port(port)
            else:
                if operation == "replace":
                    port.reset()
                    port.vendor_specific["has-ethernet-switching"] = False
                self.apply_interface_data(interface_node, port)

        return handled_elements

    def apply_interface_data(self, interface_node, port):
        port.description = resolve_new_value(interface_node, "description", port.description)

        if first(interface_node.xpath("enable")) is not None:
            port.shutdown = False if resolve_operation(first(interface_node.xpath("enable"))) != "delete" else None
        elif first(interface_node.xpath("disable")) is not None:
            port.shutdown = True if resolve_operation(first(interface_node.xpath("disable"))) != "delete" else None

        ether_options_attributes = first(interface_node.xpath("ether-options"))
        if ether_options_attributes is not None:
            if resolve_operation(ether_options_attributes) != "delete":
                speed_node = first(ether_options_attributes.xpath("speed/*"))
                if speed_node is not None:
                    port.speed = speed_node.tag.split("-")[-1]

                port.auto_negotiation = resolve_new_value(ether_options_attributes, "auto-negotiation", port.auto_negotiation, transformer=lambda _: True)

                if resolve_operation(first(ether_options_attributes.xpath("ieee-802.3ad"))) == "delete":
                    port.aggregation_membership = None
                else:
                    port.aggregation_membership = resolve_new_value(ether_options_attributes, "ieee-802.3ad/bundle", port.aggregation_membership)
            else:
                port.speed = None
                port.aggregation_membership = None

        if "delete" in [resolve_operation(first(interface_node.xpath("unit"))), resolve_operation(first(interface_node.xpath("unit/family")))]:
            port.mode = None
            port.trunk_native_vlan = None
            port.access_vlan = None
            port.trunk_vlans = None
            port.trunk_vlans = None
            port.vendor_specific["has-ethernet-switching"] = False
        else:
            port_attributes = first(interface_node.xpath("unit/family/ethernet-switching"))
            if port_attributes is not None:
                port.vendor_specific["has-ethernet-switching"] = True

                port.mode = resolve_new_value(port_attributes, self.PORT_MODE_TAG, port.mode)
                port.trunk_native_vlan = resolve_new_value(port_attributes, "native-vlan-id", port.trunk_native_vlan,
                                                           transformer=int)

                if resolve_operation(first(port_attributes.xpath("vlan"))) == "delete":
                    port.access_vlan = None
                    port.trunk_vlans = None
                else:
                    for member in port_attributes.xpath("vlan/members"):
                        if resolve_operation(member) == "delete":
                            if port.mode is None or port.mode == "access":
                                port.access_vlan = None
                            else:
                                port.trunk_vlans.remove(int(member.text))
                                if len(port.trunk_vlans) == 0:
                                    port.trunk_vlans = None
                        else:
                            if port.mode is None or port.mode == "access":
                                port.access_vlan = parse_range(member.text)[0]
                            else:
                                if port.trunk_vlans is None:
                                    port.trunk_vlans = []
                                port.trunk_vlans += parse_range(member.text)

        if isinstance(port, AggregatedPort):
            port.speed = resolve_new_value(interface_node, "aggregated-ether-options/link-speed", port.speed)
            port.auto_negotiation = resolve_new_value(interface_node, "aggregated-ether-options/auto-negotiation", port.auto_negotiation, transformer=lambda _: True)
            port.lacp_active = first(interface_node.xpath("aggregated-ether-options/lacp/active")) is not None
            port.lacp_periodic = resolve_new_value(interface_node, "aggregated-ether-options/lacp/periodic", port.lacp_periodic)

    def parse_vlans(self, conf, etree_conf):
        handled_elements = []
        for vlan_node in etree_conf.xpath("vlans/vlan/name/.."):
            handled_elements.append(vlan_node)

            vlan = conf.get_vlan_by_name(val(vlan_node, "name"))

            if resolve_operation(vlan_node) == "delete":
                if vlan is None:
                    raise NotFound(val(vlan_node, "name"))
                else:
                    conf.remove_vlan(vlan)
            else:
                if vlan is None:
                    vlan = self.original_configuration.new("Vlan", name=val(vlan_node, "name"))
                    conf.add_vlan(vlan)

                vlan.number = resolve_new_value(vlan_node, "vlan-id", vlan.number, transformer=int)
                vlan.description = resolve_new_value(vlan_node, "description", vlan.description)

        return handled_elements

def validate(configuration):
    vlan_list = [vlan.number for vlan in configuration.vlans]

    for port in configuration.ports:
        if port.access_vlan is not None and port.access_vlan not in vlan_list:
            raise UnknownVlan(port.access_vlan, port.name, 0)
        if port.trunk_native_vlan is not None and port.trunk_native_vlan not in vlan_list:
            raise UnknownVlan(port.trunk_native_vlan, port.name, 0)
        if port.trunk_vlans is not None:
            for trunk_vlan in port.trunk_vlans:
                if trunk_vlan not in vlan_list:
                    raise UnknownVlan(trunk_vlan, port.name, 0)


def vlan_to_etree(vlan):
    vlan_data = [{"name": vlan.name}]

    if vlan.description is not None:
        vlan_data.append({"description": vlan.description})

    if vlan.number is not None:
        vlan_data.append({"vlan-id": str(vlan.number)})

    return vlan_data


def parse_protocols(conf, etree_conf):
    handled_elements = []
    for rstp_interface_node in etree_conf.xpath("protocols/rstp/interface/name/.."):
        handled_elements.append(rstp_interface_node)

        port = conf.get_port_by_partial_name(val(rstp_interface_node, "name"))

        if first(rstp_interface_node.xpath("edge")) is not None:
            if resolve_operation(first(rstp_interface_node.xpath("edge"))) == "delete":
                port.vendor_specific.pop("rstp-edge")
            else:
                port.vendor_specific["rstp-edge"] = True
        elif "rstp-edge" in port.vendor_specific:
            port.vendor_specific.pop("rstp-edge")

        if first(rstp_interface_node.xpath("no-root-port")) is not None:
            if resolve_operation(first(rstp_interface_node.xpath("no-root-port"))) == "delete":
                port.vendor_specific.pop("rstp-no-root-port")
            else:
                port.vendor_specific["rstp-no-root-port"] = True
        elif "rstp-no-root-port" in port.vendor_specific:
            port.vendor_specific.pop("rstp-no-root-port")

    for lldp_interface_node in etree_conf.xpath("protocols/lldp/interface/name/.."):
        handled_elements.append(lldp_interface_node)

        port = conf.get_port_by_partial_name(val(lldp_interface_node, "name"))

        port.vendor_specific["lldp"] = True

        disable_node = first(lldp_interface_node.xpath("disable"))
        if disable_node is not None:
            if resolve_operation(disable_node) == "delete":
                port.lldp_transmit = None
                port.lldp_receive = None
            else:
                port.lldp_transmit = False
                port.lldp_receive = False

    return handled_elements


def raise_for_unused_nodes(root, handled_elements):
    for element in root:
        if len(element) == 0:
            current = element
            handled = False
            while current is not None:
                if current in handled_elements:
                    handled = True
                    break
                current = current.getparent()

            if not handled:
                raise BadElement(element.tag)
        else:
            raise_for_unused_nodes(element, handled_elements)


def resolve_new_value(node, value_name, actual_value, transformer=None):
    value_node = first(node.xpath(value_name))
    if value_node is not None:
        operation = resolve_operation(value_node)

        if operation == "delete":
            if actual_value is None:
                raise NotFound(value_name)
            else:
                return None
        else:
            return value_node.text if transformer is None else transformer(value_node.text)
    else:
        return actual_value


def resolve_operation(node):
    operation = "merge"
    if node is not None and "operation" in node.attrib:
        operation = node.attrib["operation"]

    return operation


def val(node, xpath):
    return first(node.xpath(xpath)).text


class BadElement(NetconfError):
    def __init__(self, name):
        super(BadElement, self).__init__("syntax error", info={"bad-element": name})


class NotFound(NetconfError):
    def __init__(self, name):
        super(NotFound, self).__init__("statement not found: %s" % name, severity="warning")


def parse_range(r):
    m = re.match("(\d+)-(\d+)", r)
    if m:
        return range(int(m.groups()[0]), int(m.groups()[1]) + 1)
    else:
        return [int(r)]


def extract_protocols(configuration):
    protocols = {}
    for port in configuration.ports:
        if port.vendor_specific.get("rstp-edge"):
            if "rstp" not in protocols:
                protocols["rstp"] = []
            interface = get_or_create_interface(protocols["rstp"], port)
            interface["interface"].append({"edge": ""})

        if port.vendor_specific.get("rstp-no-root-port"):
            if "rstp" not in protocols:
                protocols["rstp"] = []
            interface = get_or_create_interface(protocols["rstp"], port)
            interface["interface"].append({"no-root-port": ""})

        if port.vendor_specific.get("lldp"):
            if "lldp" not in protocols:
                protocols["lldp"] = []
            interface = get_or_create_interface(protocols["lldp"], port)
            if port.lldp_receive is False and port.lldp_transmit is False:
                interface["interface"].append({"disable": ""})


    return protocols


def get_or_create_interface(if_list, port):
    existing = next((v for v in if_list if v["interface"][0]["name"] == port.name), None)
    if existing is None:
        existing = {"interface": [
            {"name": port.name},
            ]}
        if_list.append(existing)

    return existing

