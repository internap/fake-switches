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

import re
from copy import deepcopy

from lxml import etree

from fake_switches.netconf import XML_NS, XML_ATTRIBUTES, CANDIDATE, RUNNING, AlreadyLocked, NetconfError, \
    CannotLockUncleanCandidate, first,UnknownVlan, InvalidInterfaceType, InvalidTrailingInput, \
    AggregatePortOutOfRange, PhysicalPortOutOfRange,  MultipleNetconfErrors, InvalidNumericValue, InvalidMTUValue
from fake_switches.netconf.netconf_protocol import dict_2_etree
from fake_switches.switch_configuration import AggregatedPort, VlanPort

NS_JUNOS = "http://xml.juniper.net/junos/11.4R1/junos"


class JuniperNetconfDatastore(object):
    VLANS_COLLECTION = "vlans"
    VLANS_COLLECTION_OBJ = "vlan"
    PORT_MODE_TAG = "port-mode"
    ETHERNET_SWITCHING_TAG = "ethernet-switching"
    MAX_AGGREGATED_ETHERNET_INTERFACES = 127
    ETHER_OPTIONS_TAG = "ether-options"
    MAX_PHYSICAL_PORT_NUMBER = 127
    MAX_MTU = 9216
    SYSTEM_INTERFACES = []

    def __init__(self, configuration):
        self.original_configuration = configuration
        self.configurations = {}
        self.reset()
        self.edit_errors = []

    def reset(self):
        self.configurations = {
            CANDIDATE: deepcopy(self.original_configuration),
            RUNNING: self.original_configuration,
        }

        self.configurations[CANDIDATE].routing_engine = None

    def to_etree(self, source):
        etree.register_namespace("junos", NS_JUNOS)

        configuration = {
            XML_NS: 'http://xml.juniper.net/xnm/1.1/xnm',
            XML_ATTRIBUTES: {
                "xmlns":"http://xml.juniper.net/xnm/1.1/xnm",
                "{" + NS_JUNOS + "}commit-seconds": "1411928899",
                "{" + NS_JUNOS + "}commit-localtime": "2014-09-28 14:28:19 EDT",
                "{" + NS_JUNOS + "}commit-user": "admin"
            }
        }

        _add_if_not_empty(configuration, "interfaces", self._extract_interfaces(self.configurations[source]))

        _add_if_not_empty(configuration, "protocols", self._extract_protocols(self.configurations[source]))

        _add_if_not_empty(configuration, self.VLANS_COLLECTION,
                         [{self.VLANS_COLLECTION_OBJ: self.vlan_to_etree(vlan)} for vlan in self.configurations[source].vlans])

        return dict_2_etree({"data": {"configuration": configuration}})

    def edit(self, target, etree_conf):
        self.edit_errors = []
        conf = self.configurations[target]
        handled_elements = []

        handled_elements += self.parse_vlans(conf, etree_conf)
        handled_elements += self.parse_interfaces(conf, etree_conf)
        handled_elements += parse_protocols(conf, etree_conf)

        self.edit_errors.extend(_get_errors_for_unused_nodes(etree_conf, handled_elements))

        if len(self.edit_errors) > 0:
            raise MultipleNetconfErrors(self.edit_errors)

    def commit_candidate(self):
        self._validate(self.configurations[CANDIDATE])
        for updated_vlan in self.configurations[CANDIDATE].vlans:
            actual_vlan = self.configurations[RUNNING].get_vlan_by_name(updated_vlan.name)
            if not actual_vlan:
                self.configurations[RUNNING].add_vlan(deepcopy(updated_vlan))
            else:
                actual_vlan.number = updated_vlan.number
                actual_vlan.description = updated_vlan.description
                actual_vlan.vendor_specific = updated_vlan.vendor_specific

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
                actual_port.mtu = updated_port.mtu
                actual_port.access_vlan = updated_port.access_vlan
                actual_port.trunk_vlans = deepcopy(updated_port.trunk_vlans)
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

                if isinstance(actual_port, VlanPort):
                    actual_port.vlan_id = updated_port.vlan_id
                    actual_port.access_group_in = updated_port.access_group_in
                    actual_port.access_group_out = updated_port.access_group_out
                    for ip in actual_port.ips:
                        if ip not in updated_port.ips:
                            actual_port.remove_ip(ip)
                    for ip in updated_port.ips:
                        if ip not in actual_port.ips:
                            actual_port.add_ip(ip)
                    actual_port.secondary_ips = deepcopy(updated_port.secondary_ips)
                    actual_port.vrrp_common_authentication = updated_port.vrrp_common_authentication
                    actual_port.vrrp_version = updated_port.vrrp_version
                    actual_port.vrrps = deepcopy(updated_port.vrrps)
                    actual_port.ip_redirect = updated_port.ip_redirect
                    actual_port.ip_proxy_arp = updated_port.ip_proxy_arp
                    actual_port.unicast_reverse_path_forwarding = updated_port.unicast_reverse_path_forwarding

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

    def get_interface_information_terse(self):
        return dict_2_etree({
            "interface-information":
                [{XML_ATTRIBUTES: {"style": "terse"}}]
                + self._port_terse(self.configurations[RUNNING])
                + self._aggregated_port_terse(self.configurations[RUNNING])})

    def interface_to_etree(self, port):
        interface_data = []

        if port.description is not None:
            interface_data.append({"description": port.description})

        if port.mtu is not None:
            interface_data.append({"mtu": port.mtu})

        if port.shutdown:
            interface_data.append({"disable": ""})

        if isinstance(port, AggregatedPort):
            aggregated_ether_options = {}
            if port.speed is not None:
                aggregated_ether_options["link-speed"] = port.speed

            lacp_options = {}
            if port.lacp_active is True:
                lacp_options["active"] = {}

            if port.lacp_periodic is not None:
                lacp_options["periodic"] = port.lacp_periodic

            if len(lacp_options) > 0:
                aggregated_ether_options["lacp"] = lacp_options

            if len(aggregated_ether_options) > 0:
                interface_data.append({"aggregated-ether-options": aggregated_ether_options})
        else:
            ether_options = {}
            if port.speed is not None:
                ether_options["speed"] = {"ethernet-{0}".format(port.speed): {}}

            if port.auto_negotiation is True:
                ether_options["auto-negotiation"] = {}
            elif port.auto_negotiation is False:
                ether_options["no-auto-negotiation"] = {}

            if port.aggregation_membership is not None:
                ether_options["ieee-802.3ad"] = {"bundle": port.aggregation_membership}

            if len(ether_options) > 0:
                interface_data.append({self.ETHER_OPTIONS_TAG: ether_options})

        if port.vendor_specific.get("has-ethernet-switching"):
            self.ethernet_switching_to_etree(port, interface_data)

        self.apply_trunk_native_vlan(interface_data, port)

        if len(interface_data) > 0:
            interface_data.insert(0, {"name": port.name})
            return interface_data

        return None

    def ethernet_switching_to_etree(self, port, interface_data):
        ethernet_switching = {}
        if port.mode is not None:
            ethernet_switching[self.PORT_MODE_TAG] = port.mode
        vlans = port.trunk_vlans or []
        if port.access_vlan: vlans.append(port.access_vlan)
        if len(vlans) > 0:
            ethernet_switching["vlan"] = [{"members": str(v)} for v in vlans]
        if ethernet_switching or not isinstance(port, AggregatedPort):
            interface_data.append({"unit": {
                "name": "0",
                "family": {
                    self.ETHERNET_SWITCHING_TAG: ethernet_switching
                }
            }})

    def parse_interfaces(self, conf, etree_conf):
        handled_elements = []
        for interface_node in etree_conf.xpath("interfaces/interface/name/.."):
            handled_elements.append(interface_node)

            self.parse_interface(conf, interface_node)

        return handled_elements

    def parse_interface(self, conf, interface_node):
        port_name = val(interface_node, "name")
        self.raise_for_invalid_interface(port_name, self.MAX_AGGREGATED_ETHERNET_INTERFACES)

        port = conf.get_port_by_partial_name(port_name)
        if port is None and re.match("^ae\d+$", port_name):
            port = self.original_configuration.new("AggregatedPort", port_name)
            port.vendor_specific["has-ethernet-switching"] = True
            conf.add_port(port)

        operation = resolve_operation(interface_node)
        self.handle_interface_operation(conf, operation, port)

        if operation != "delete":
            self.apply_interface_data(interface_node, port)

    def handle_interface_operation(self, conf, operation, port):
        if operation in ("delete", "replace"):
            backup = deepcopy(vars(port))

            port.reset()

            _restore_protocols_specific_data(backup, port)

    def apply_interface_data(self, interface_node, port):
        port.description = resolve_new_value(interface_node, "description", port.description)
        port.mtu = resolve_new_value(interface_node, "mtu", port.mtu, transformer=self._validate_mtu)

        shutdown_node = first(interface_node.xpath("disable"))
        if shutdown_node is not None:
            if port.shutdown is False and resolve_operation(shutdown_node) == "delete":
                raise NotFound('')
            port.shutdown = resolve_operation(shutdown_node) != "delete"

        ether_options_attributes = first(interface_node.xpath(self.ETHER_OPTIONS_TAG))
        if ether_options_attributes is not None:
            if resolve_operation(ether_options_attributes) != "delete":
                speed_node = first(ether_options_attributes.xpath("speed/*"))
                if speed_node is not None:
                    port.speed = speed_node.tag.split("-")[-1]

                self.edit_errors.extend(assign_auto_negotiation_state(ether_options_attributes, port))

                if resolve_operation(first(ether_options_attributes.xpath("ieee-802.3ad"))) == "delete":
                    if port.aggregation_membership is None:
                        raise NotFound("802.3ad")
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
            port_attributes = first(interface_node.xpath("unit/family/{}".format(self.ETHERNET_SWITCHING_TAG)))
            if port_attributes is not None:
                port.vendor_specific["has-ethernet-switching"] = True

                port.mode = resolve_new_value(port_attributes, self.PORT_MODE_TAG, port.mode)
                if port.mode == "access":
                    port.trunk_vlans = None
                    port.trunk_native_vlan = None
                else:
                    port.access_vlan = None

                if resolve_operation(first(port_attributes.xpath("vlan"))) == "delete":
                    port.access_vlan = None
                    port.trunk_vlans = None
                else:
                    self.parse_vlan_members(port, port_attributes)

            if resolve_operation(first(self.get_trunk_native_vlan_node(interface_node))) == "delete":
                port.trunk_native_vlan = None
            else:
                port.trunk_native_vlan = self.parse_trunk_native_vlan(interface_node, port)

        if isinstance(port, AggregatedPort):
            port.speed = resolve_new_value(interface_node, "aggregated-ether-options/link-speed", port.speed)
            port.auto_negotiation = resolve_new_value(interface_node, "aggregated-ether-options/auto-negotiation", port.auto_negotiation, transformer=lambda _: True)
            port.lacp_active = first(interface_node.xpath("aggregated-ether-options/lacp/active")) is not None
            port.lacp_periodic = resolve_new_value(interface_node, "aggregated-ether-options/lacp/periodic", port.lacp_periodic)

    def parse_vlan_members(self, port, port_attributes):
        for member in port_attributes.xpath("vlan/members"):
            if resolve_operation(member) == "delete":
                if port_is_in_access_mode(port):
                    port.access_vlan = None
                else:
                    port.trunk_vlans.remove(int(member.text))
                    if len(port.trunk_vlans) == 0:
                        port.trunk_vlans = None
            else:
                if port_is_in_access_mode(port):
                    port.access_vlan = parse_range(member.text)[0]
                else:
                    if port.trunk_vlans is None:
                        port.trunk_vlans = []
                    port.trunk_vlans += parse_range(member.text)

    def parse_vlans(self, conf, etree_conf):
        handled_elements = []
        for vlan_node in etree_conf.xpath("{}/{}/name/..".format(self.VLANS_COLLECTION, self.VLANS_COLLECTION_OBJ)):
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

                self.parse_vlan_attributes(conf, vlan, vlan_node)

        return handled_elements

    def parse_vlan_attributes(self, conf, vlan, vlan_node):
        vlan.number = resolve_new_value(vlan_node, "vlan-id", vlan.number, transformer=int)
        vlan.description = resolve_new_value(vlan_node, "description", vlan.description)

    def parse_trunk_native_vlan(self, interface_node, port):
        if len(interface_node.xpath("unit/family/{}/native-vlan-id".format(self.ETHERNET_SWITCHING_TAG))) == 1 and interface_node.xpath("unit/family/{}/native-vlan-id".format(self.ETHERNET_SWITCHING_TAG))[0].text is not None:
            port_attributes = first(interface_node.xpath("unit/family/{}".format(self.ETHERNET_SWITCHING_TAG)))
            return resolve_new_value(port_attributes, "native-vlan-id", port.trunk_native_vlan,
                              transformer=int)
        return port.trunk_native_vlan

    def apply_trunk_native_vlan(self, interface_data, port):
        if port.vendor_specific.get("has-ethernet-switching"):
            if port.trunk_native_vlan is not None:
                if not "unit" in interface_data[-1]:
                    interface_data.append({"unit": {
                        "family":{
                            self.ETHERNET_SWITCHING_TAG: {
                                "native-vlan-id": str(port.trunk_native_vlan)
                            }
                        }}})
                else:
                    interface_data[-1]['unit']['family'][self.ETHERNET_SWITCHING_TAG]['native-vlan-id'] = str(port.trunk_native_vlan)

    def get_trunk_native_vlan_node(self, interface_node):
        return interface_node.xpath("unit/family/{}/native-vlan-id".format(self.ETHERNET_SWITCHING_TAG))

    def vlan_to_etree(self, vlan):
        vlan_data = [{"name": vlan.name}]

        if vlan.description is not None:
            vlan_data.append({"description": vlan.description})

        if vlan.number is not None:
            vlan_data.append({"vlan-id": str(vlan.number)})

        return vlan_data

    def _validate(self, configuration):
        vlan_list = [vlan.number for vlan in configuration.vlans]

        for port in configuration.ports:
            self.validate_vlan_config(port, vlan_list)
            self._assert_no_garbage(port)

    def validate_vlan_config(self, port, vlan_list):
        if port.access_vlan is not None and port.access_vlan not in vlan_list:
            raise UnknownVlan(port.access_vlan, port.name, 0)
        if port.trunk_native_vlan is not None and port.trunk_native_vlan not in vlan_list:
            raise UnknownVlan(port.trunk_native_vlan, port.name, 0)
        if port.trunk_vlans is not None:
            for trunk_vlan in port.trunk_vlans:
                if trunk_vlan not in vlan_list:
                    raise UnknownVlan(trunk_vlan, port.name, 0)


    def _assert_no_garbage(self, port):
        if not port.vendor_specific.get("has-ethernet-switching"):
            if port.vendor_specific.get("rstp-edge") or port.vendor_specific.get("rstp-no-root-port"):
                raise RSTPActiveWithoutEthernetSwitching(self._format_protocol_port_name(port))

    def _port_terse(self, conf):
        return [self._to_terse(p) for p in conf.get_physical_ports()]

    def _aggregated_port_terse(self, conf):
        return [self._to_terse(p) for p in conf.ports if isinstance(p, AggregatedPort)]

    def _to_terse(self, port):
        interface = [
            {"name": "\n{}\n".format(port.name)},
            {"admin-status": "\ndown\n" if port.shutdown else "\nup\n"},
            {"oper-status": "\ndown\n"}
        ]

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

        return {"physical-interface": interface}

    def _extract_interfaces(self, source):
        interfaces = []
        for port in source.ports:
            interface_node = self.interface_to_etree(port)
            if interface_node:
                interfaces.append({"interface": interface_node})
        return interfaces

    def _extract_protocols(self, configuration):
        protocols = {}
        for port in configuration.ports:
            if port.vendor_specific.get("rstp-edge"):
                if "rstp" not in protocols:
                    protocols["rstp"] = []
                interface = self._get_or_create_interface(protocols["rstp"], port)
                interface["interface"].append({"edge": ""})

            if port.vendor_specific.get("rstp-no-root-port"):
                if "rstp" not in protocols:
                    protocols["rstp"] = []
                interface = self._get_or_create_interface(protocols["rstp"], port)
                interface["interface"].append({"no-root-port": ""})

            if port.vendor_specific.get("lldp"):
                if "lldp" not in protocols:
                    protocols["lldp"] = []
                interface = self._get_or_create_interface(protocols["lldp"], port)
                if port.lldp_receive is False and port.lldp_transmit is False:
                    interface["interface"].append({"disable": ""})

        return protocols

    def _get_or_create_interface(self, if_list, port):
        port_name = self._format_protocol_port_name(port)
        existing = next((v for v in if_list if v["interface"][0]["name"] == port_name), None)
        if existing is None:
            existing = {"interface": [
                {"name": port_name},
            ]}
            if_list.append(existing)

        return existing

    def _format_protocol_port_name(self, port):
        return "{}.0".format(port.name)

    def raise_for_invalid_interface(self, interface, max_aggregated_interfaces):
        if interface in self.SYSTEM_INTERFACES:
            return

        interface_match = re.match(r'^(\w+)-\d/\d/(\d+)(\S*)', interface)
        if interface_match and interface_match.group(2):
            if interface_match and interface_match.group(3):
                raise InvalidTrailingInput(interface_match.group(3), interface)

            if interface_match and int(interface_match.group(2)) > self.MAX_PHYSICAL_PORT_NUMBER:
                raise PhysicalPortOutOfRange(interface_match.group(2), interface, self.MAX_PHYSICAL_PORT_NUMBER)
        else:
            interface_match = re.match(r'^[a-z]+(\S+)', interface)
            if interface_match and any(c.isalpha() for c in interface_match.group(1)):
                raise InvalidInterfaceType(interface)

            if interface_match and int(interface_match.group(1)) > max_aggregated_interfaces:
                raise AggregatePortOutOfRange(interface_match.group(1), interface, max_range=max_aggregated_interfaces)

    def _validate_mtu(self, value):
        try:
            int_val = int(value)
        except ValueError:
            raise InvalidNumericValue(value)

        if 256 <= int_val <= self.MAX_MTU:
            return value

        raise InvalidMTUValue(value, self.MAX_MTU)


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

        if resolve_operation(lldp_interface_node) == "delete":
            port.vendor_specific["lldp"] = False
            port.lldp_transmit = None
            port.lldp_receive = None
        else:
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


def _get_errors_for_unused_nodes(root, handled_elements):
    errors = []
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
                errors.append(BadElement(element.tag))
        else:
            errors.extend(_get_errors_for_unused_nodes(element, handled_elements))
    return errors


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


class SyntaxError(NetconfError):
    def __init__(self):
        super(SyntaxError, self).__init__("syntax error")


def parse_range(r):
    m = re.match("(\d+)-(\d+)", r)
    if m:
        return list(range(int(m.groups()[0]), int(m.groups()[1]) + 1))
    else:
        return [int(r)]


def port_is_in_access_mode(port):
    return port.mode is None or port.mode == "access"


def port_is_in_trunk_mode(port):
    return not port_is_in_access_mode(port)


def _add_if_not_empty(target_dict, key, value):
    if value:
        target_dict[key] = value


def _restore_protocols_specific_data(backup, port):
    port.vendor_specific["rstp-edge"] = backup.get("vendor_specific", {}).get("rstp-edge")
    port.vendor_specific["rstp-no-root-port"] = backup.get("vendor_specific", {}).get("rstp-no-root-port")
    port.vendor_specific["lldp"] = backup.get("vendor_specific", {}).get("lldp")
    port.lldp_transmit = backup.get("lldp_transmit")
    port.lldp_receive = backup.get("lldp_receive")


def assign_auto_negotiation_state(ether_options_attributes, port):
    errors = []

    auto_negotion_present = resolve_new_value(ether_options_attributes, "auto-negotiation", False, transformer=lambda _: True)
    no_auto_negotion_present = resolve_new_value(ether_options_attributes, "no-auto-negotiation", False, transformer=lambda _: True)

    if auto_negotion_present is not False and no_auto_negotion_present is not False:
        errors.append(SyntaxError())
    if auto_negotion_present is None and port.auto_negotiation is not True:
        errors.append(NotFound("auto-negotiation"))
    if no_auto_negotion_present is None and port.auto_negotiation is not False:
        errors.append(NotFound("no-auto-negotiation"))

    if auto_negotion_present is True:
        port.auto_negotiation = True
    elif no_auto_negotion_present is True:
        port.auto_negotiation = False
    else:
        port.auto_negotiation = None

    return errors


class RSTPActiveWithoutEthernetSwitching(NetconfError):
    def __init__(self, interface_name):
        super(RSTPActiveWithoutEthernetSwitching, self).__init__(
            "XSTP : Interface {} is not enabled for Ethernet Switching".format(interface_name))
