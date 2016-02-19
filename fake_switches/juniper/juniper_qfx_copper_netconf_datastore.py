# Copyright 2016 Internap.
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

from fake_switches.juniper.juniper_netconf_datastore import JuniperNetconfDatastore, resolve_new_value, \
    resolve_operation, parse_range
from fake_switches.netconf import first
from fake_switches.switch_configuration import AggregatedPort


class JuniperQfxCopperNetconfDatastore(JuniperNetconfDatastore):
    def __init__(self, configuration):
        super(JuniperQfxCopperNetconfDatastore, self).__init__(configuration)

        self.PORT_MODE_TAG = "interface-mode"

    def interface_to_etree(self, port):
        interface_data = [
            {"name": port.name}
        ]

        if port.description is not None:
            interface_data.append({"description": port.description})

        if port.shutdown is not None:
            interface_data.append({("disable" if port.shutdown else "enable"): ""})

        if port.trunk_native_vlan is not None:
            interface_data.append({"native-vlan-id" : str(port.trunk_native_vlan)})

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

    def apply_interface_data(self, interface_node, port):
        port.description = resolve_new_value(interface_node, "description", port.description)
        port.trunk_native_vlan = resolve_new_value(interface_node, "native-vlan-id", port.trunk_native_vlan,
                                                   transformer=int)

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
