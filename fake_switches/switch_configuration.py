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
from time import sleep

from netaddr import IPNetwork, IPAddress


class SwitchConfiguration(object):
    def __init__(self, ip, name="", auto_enabled=False, privileged_passwords=None, ports=None, vlans=None, objects_overrides=None, commit_delay=0):
        self.ip = ip
        self.name = name
        self.privileged_passwords = privileged_passwords or []
        self.auto_enabled = auto_enabled
        self.vlans = []
        self.ports = []
        self.static_routes = []
        self.vrfs = [VRF('DEFAULT-LAN')]
        self.locked = False
        self.objects_factory = {
            "Route": Route,
            "VRF": VRF,
            "Vlan": Vlan,
            "Port": Port,
            "VRRP": VRRP,
            "VlanPort": VlanPort,
            "AggregatedPort": AggregatedPort,
        }
        self.commit_delay = commit_delay

        if vlans:
            [self.add_vlan(v) for v in vlans]
        if ports:
            [self.add_port(p) for p in ports]
        if objects_overrides:
            self.objects_factory.update(objects_overrides)

    def new(self, class_name, *args, **kwargs):
        return self.objects_factory[class_name](*args, **kwargs)

    def add_static_route(self, route):
        self.static_routes.append(route)

    def remove_static_route(self, destination, mask):
        subnet = IPNetwork("{}/{}".format(destination, mask))
        route = next(route for route in self.static_routes if route.dest == subnet)
        self.static_routes.remove(route)

    def get_vlan(self, number):
        return next((vlan for vlan in self.vlans if vlan.number == number), None)

    def get_vlan_by_name(self, name):
        return next((vlan for vlan in self.vlans if vlan.name == name), None)

    def add_vlan(self, vlan):
        self.vlans.append(vlan)
        vlan.switch_configuration = self

    def remove_vlan(self, vlan):
        vlan.switch_configuration = None
        self.vlans.remove(vlan)

    def get_port(self, name):
        return next((port for port in self.ports if port.name == name), None)

    def add_port(self, port):
        self.ports.append(port)
        port.switch_configuration = self

    def remove_port(self, port):
        port.switch_configuration = None
        self.ports.remove(port)

    def get_port_by_partial_name(self, name):
        partial_name, number = split_port_name(name.lower())

        return next((port for port in self.ports if port.name.lower().startswith(partial_name.strip()) and port.name.lower().endswith(number.strip())), None)

    def get_port_and_ip_by_ip(self, ip_string):
        for port in [e for e in self.ports if isinstance(e, VlanPort)]:
            for ip in port.ips:
                if ip_string in ip:
                    return port, ip
        return None, None

    def add_vrf(self, vrf):
        if not self.get_vrf(vrf.name):
            self.vrfs.append(vrf)

    def get_vrf(self, name):
        return next((vrf for vrf in self.vrfs if vrf.name == name), None)

    def remove_vrf(self, name):
        vrf = self.get_vrf(name)
        if vrf:
            self.vrfs.remove(vrf)
            for port in self.ports:
                if port.vrf and port.vrf.name == name:
                    port.vrf = None

    def get_physical_ports(self):
        return [p for p in self.ports if not (isinstance(p, VlanPort) or isinstance(p, AggregatedPort))]

    def get_vlan_ports(self):
        return [p for p in self.ports if isinstance(p, VlanPort)]

    def commit(self):
        sleep(self.commit_delay)


class VRF(object):
    def __init__(self, name):
        self.name = name


class Route(object):
    def __init__(self, destination, mask, next_hop):
        self.dest = IPNetwork("{}/{}".format(destination, mask))
        self.next_hop = IPAddress(next_hop)

    @property
    def destination(self):
        return self.dest.ip

    @property
    def mask(self):
        return self.dest.netmask


class Vlan(object):
    def __init__(self, number=None, name=None, description=None, switch_configuration=None):
        self.number = number
        self.name = name
        self.description = description
        self.switch_configuration = switch_configuration
        self.vendor_specific = {}


class Port(object):
    def __init__(self, name):
        self.name = name
        self.switch_configuration = None
        self.reset()

    def reset(self):
        self.description = None
        self.mode = None
        self.access_vlan = None
        self.trunk_vlans = None
        self.trunk_native_vlan = None
        self.trunk_encapsulation_mode = None
        self.shutdown = None
        self.vrf = None
        self.speed = None
        self.auto_negotiation = None
        self.aggregation_membership = None
        self.mtu = None
        self.vendor_specific = {}
        self.ip_helpers = []
        self.lldp_transmit = None
        self.lldp_receive = None
        self.lldp_med = None
        self.lldp_med_transmit_capabilities = None
        self.lldp_med_transmit_network_policy = None
        self.spanning_tree = None
        self.spanning_tree_portfast = None
        self.ntp = None

    def get_subname(self, length):
        name, number = split_port_name(self.name)
        return name[:length] + number


class VRRP(object):
    def __init__(self, group_id):
        self.group_id = group_id
        self.ip_addresses = None
        self.description = None
        self.authentication = None
        self.timers_hello = None
        self.timers_hold = False
        self.priority = None
        self.track = {}
        self.preempt = None
        self.preempt_delay_minimum = None
        self.activated = None
        self.advertising = None
        self.related_ip_network = None
        self.vendor_specific = {}


class VlanPort(Port):
    def __init__(self, vlan_id, *args, **kwargs):
        super(VlanPort, self).__init__(*args, **kwargs)

        self.vlan_id = vlan_id
        self.access_group_in = None
        self.access_group_out = None
        self.ips = []
        self.secondary_ips = []
        self.vrrp_common_authentication = None
        self.vrrp_version = None
        self.vrrps = []
        self.varp_addresses = []
        self.ip_redirect = True
        self.ip_proxy_arp = True
        self.unicast_reverse_path_forwarding = False
        self.load_interval = None
        self.mpls_ip = True

    def get_vrrp_group(self, group):
        return next((vrrp for vrrp in self.vrrps if vrrp.group_id == group), None)

    def add_ip(self, ip_network):
        existing_ip = next((ip for ip in self.ips if ip.ip == ip_network.ip), None)
        if existing_ip:
            self.ips[self.ips.index(existing_ip)] = ip_network
        else:
            self.ips.append(ip_network)

    def add_secondary_ip(self, ip_network):
        self.secondary_ips.append(ip_network)

    def remove_ip(self, ip_network):
        for i, ip in enumerate(self.ips):
            if ip.ip == ip_network.ip:
                self.ips.pop(i)
                break

    def remove_secondary_ip(self, deleting_ip):
        ip = next((ip for ip in self.secondary_ips if ip.ip == deleting_ip.ip), None)
        if ip:
            self.secondary_ips.remove(ip)


class AggregatedPort(Port):
    def reset(self):
        self.lacp_active = False
        self.lacp_periodic = None

        super(AggregatedPort, self).reset()

    def get_child_ports_linked_to_a_machine(self):
        return [p for p in self.switch_configuration.ports if p.aggregation_membership == self.name and p.link_name is not None]


def split_port_name(name):
    number_start, number_len = re.compile('\d').search(name).span()
    return name[0:number_start], name[number_start:]
