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

from fake_switches import group_sequences
from fake_switches.brocade.command_processor import explain_missing_port
from fake_switches.command_processing.base_command_processor import BaseCommandProcessor
from fake_switches.command_processing.switch_tftp_parser import SwitchTftpParser
from fake_switches.switch_configuration import split_port_name, VlanPort


class EnabledCommandProcessor(BaseCommandProcessor):
    def __init__(self, config):
        super(EnabledCommandProcessor, self).__init__()
        self.config_processor = config

    def get_prompt(self):
        return "SSH@%s#" % self.switch_configuration.name

    def do_configure(self, *_):
        self.move_to(self.config_processor)

    def do_show(self, *args):
        if "running-config".startswith(args[0]):
            if "vlan".startswith(args[1]):
                self.show_run_vlan()
            if "interface".startswith(args[1]):
                self.show_run_int(args)
        elif "interfaces".startswith(args[0]):
            self.show_int(args)
        elif "vlan".startswith(args[0]):
            if args[1].isdigit():
                self._show_vlan(int(args[1]))
            elif "brief".startswith(args[1]):
                self.show_vlan_brief()
            elif "ethernet".startswith(args[1]):
                self.show_vlan_int(args)
            else:
                self.write_line("Invalid input -> %s" % args[1])
                self.write_line("Type ? for a list")
        elif "ip".startswith(args[0]) and "route".startswith(args[1]) and "static".startswith(args[2]):
            routes = self.switch_configuration.static_routes
            if routes:
                self.write_line("        Destination        Gateway        Port          Cost          Type Uptime src-vrf")
            for n, route in enumerate(routes):
                self.write_line("{index:<8}{destination:<18} {next_hop:}".format(index=n+1, destination=str(route.dest), next_hop=str(route.next_hop)))
            self.write_line("")
        elif "version".startswith(args[0]):
            self.show_version()

    def do_ncopy(self, protocol, url, filename, target):
        try:
            SwitchTftpParser(self.switch_configuration).parse(url, filename, self.config_processor)
            self.write_line("done")
        except Exception as e:
            self.logger.warning("tftp parsing went wrong : %s" % str(e))
            self.write_line("%s: Download to %s failed - Session timed out" % (protocol.upper(), target))

    def do_skip_page_display(self, *args):
        pass

    def do_write(self, *args):
        self.switch_configuration.commit()

    def do_exit(self):
        self.is_done = True

    def show_run_vlan(self):
        self.write_line("spanning-tree")
        self.write_line("!")
        self.write_line("!")
        for vlan in sorted(self.switch_configuration.vlans, key=lambda v: v.number):
            if vlan_name(vlan):
                self.write_line("vlan %d name %s" % (vlan.number, vlan_name(vlan)))
            else:
                self.write_line("vlan %d" % vlan.number)

            untagged_ports = []
            for port in self.switch_configuration.ports:
                if not isinstance(port, VlanPort):
                    if vlan.number == 1 and port.access_vlan is None and port.trunk_native_vlan is None:
                        untagged_ports.append(port)
                    elif port.access_vlan == vlan.number or port.trunk_native_vlan == vlan.number:
                        untagged_ports.append(port)

            if len(untagged_ports) > 0:
                if vlan.number == 1:
                    self.write_line(" no untagged %s" % to_port_ranges(untagged_ports))
                else:
                    self.write_line(" untagged %s" % to_port_ranges(untagged_ports))

            tagged_ports = [p for p in self.switch_configuration.ports if
                            p.trunk_vlans and vlan.number in p.trunk_vlans]
            if tagged_ports:
                self.write_line(" tagged %s" % to_port_ranges(tagged_ports))

            vif = self.get_interface_vlan_for(vlan)
            if vif is not None:
                self.write_line(" router-interface %s" % vif.name)

            self.write_line("!")
        self.write_line("!")
        self.write_line("")

    def show_run_int(self, args):
        port_list = []
        if len(args) < 3:
            port_list = sorted(self.switch_configuration.ports, key=lambda e: ("a" if not isinstance(e, VlanPort) else "b") + e.name)
        else:
            if "ve".startswith(args[2]):
                port = self.switch_configuration.get_port_by_partial_name(" ".join(args[2:]))
                if not port:
                    self.write_line("Error - %s was not configured" % " ".join(args[2:]))
                else:
                    port_list = [port]
            else:
                port_type, port_number = split_port_name("".join(args[2:]))
                port = self.switch_configuration.get_port_by_partial_name(port_number)
                if not port:
                    self.write_line("")
                else:
                    port_list = [port]
        if len(port_list) > 0:
            for port in port_list:
                attributes = get_port_attributes(port)
                if len(attributes) > 0 or isinstance(port, VlanPort):
                    self.write_line("interface %s" % port.name)
                    for a in attributes:
                        self.write_line(" " + a)
                    self.write_line("!")

            self.write_line("")

    def show_int(self, args):
        ports = []
        port_name = " ".join(args[1:])
        if len(args) > 1:
            port = self.switch_configuration.get_port_by_partial_name(port_name)
            if port:
                ports.append(port)
        else:
            ports = self.switch_configuration.ports
        if not ports:
            [self.write_line(l) for l in explain_missing_port(port_name)]
        for port in ports:
            if isinstance(port, VlanPort):
                _, port_id = split_port_name(port.name)
                self.write_line("Ve%s is down, line protocol is down" % port_id)
                self.write_line("  Hardware is Virtual Ethernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
                if port.description:
                    self.write_line("  Port name is %s" % port.description)
                else:
                    self.write_line("  No port name")

                self.write_line("  Vlan id: %s" % port.vlan_id)
                self.write_line("  Internet address is %s, IP MTU 1500 bytes, encapsulation ethernet" % (
                    port.ips[0] if port.ips else "0.0.0.0/0"))
            else:
                _, port_id = split_port_name(port.name)
                self.write_line("GigabitEthernet%s is %s, line protocol is down" % (
                    port_id, "down" if port.shutdown is False else "disabled"))
                self.write_line("  Hardware is GigabitEthernet, address is 0000.0000.0000 (bia 0000.0000.0000)")
                self.write_line("  " + ", ".join([vlan_membership(port), port_mode(port), port_state(port)]))
                if port.description:
                    self.write_line("  Port name is %s" % port.description)
                else:
                    self.write_line("  No port name")

    def show_vlan_brief(self):
        self.write_line("")
        self.write_line("VLAN     Name       Encap ESI                              Ve    Pri Ports")
        self.write_line("----     ----       ----- ---                              ----- --- -----")
        for vlan in sorted(self.switch_configuration.vlans, key=lambda v: v.number):
            ports = [port for port in self.switch_configuration.ports
                     if port.access_vlan == vlan.number or (port.access_vlan is None and vlan.number == 1)]
            self.write_line("%-4s     %-10s                                        -     -%s" % (
                vlan.number,
                vlan_name(vlan)[:10] if vlan_name(vlan) else "[None]",
                ("   Untagged Ports : %s" % to_port_ranges(ports)) if ports else ""
            ))

    def show_vlan_int(self, args):
        port = self.switch_configuration.get_port_by_partial_name(" ".join(args[1:]))
        if port:
            untagged_vlan = port.access_vlan or (port.trunk_native_vlan if port.trunk_native_vlan != 1 else None)
            if untagged_vlan is None and port.trunk_vlans is None:
                self.write_line("VLAN: 1  Untagged")
            else:
                for vlan in sorted(port.trunk_vlans or []):
                    if untagged_vlan is not None and untagged_vlan < vlan:
                        self.write_line("VLAN: %s  Untagged" % untagged_vlan)
                        untagged_vlan = None
                    self.write_line("VLAN: %s  Tagged" % vlan)

                if untagged_vlan is not None:
                    self.write_line("VLAN: %s  Untagged" % untagged_vlan)
        else:
            self.write_line("Invalid input -> %s" % args[2])
            self.write_line("Type ? for a list")

    def _show_vlan(self, vlan_id):
        vlan = self.switch_configuration.get_vlan(vlan_id)
        if vlan is None:
            self.write_line("Error: vlan {} is not configured".format(vlan_id))
        else:
            vif = self.get_interface_vlan_for(vlan)
            ports = self.get_interface_ports_for(vlan)

            self.write_line("")
            self.write_line("PORT-VLAN {}, Name {}, Priority Level -, Priority Force 0, Creation Type STATIC".format(
                vlan_id, vlan.name if vlan.name is not None else "[None]"))
            self.write_line("Topo HW idx    : 81    Topo SW idx: 257    Topo next vlan: 0")
            self.write_line("L2 protocols   : STP")
            if len(ports["tagged"]) > 0:
                self.write_line("Statically tagged Ports    : {}".format(to_port_ranges(ports["tagged"])))
            if len(ports["untagged"]) > 0:
                self.write_line("Untagged Ports : {}".format(to_port_ranges(ports["untagged"])))
            self.write_line("Associated Virtual Interface Id: {}".format(
                "NONE" if vif is None else vif.name.split(" ")[-1]))
            self.write_line("----------------------------------------------------------")
            if len(ports["untagged"]) == 0 and len(ports["tagged"]) == 0:
                self.write_line("No ports associated with VLAN")
            else:
                self.write_line("Port  Type      Tag-Mode  Protocol  State")
                for port in ports["untagged"]:
                    self.write_line("{}   PHYSICAL  UNTAGGED  STP       DISABLED".format(split_port_name(port.name)[1]))
                for port in ports["tagged"]:
                    self.write_line("{}   PHYSICAL  TAGGED    STP       DISABLED".format(split_port_name(port.name)[1]))

            self.write_line("Arp Inspection: 0")
            self.write_line("DHCP Snooping: 0")
            self.write_line("IPv4 Multicast Snooping: Disabled")
            self.write_line("IPv6 Multicast Snooping: Disabled")
            self.write_line("")

            if vif is None:
                self.write_line("No Virtual Interfaces configured for this vlan")
            else:
                self.write_line("Ve{} is down, line protocol is down".format(vif.name.split(" ")[-1]))
                self.write_line("  Type is Vlan (Vlan Id: {})".format(vlan_id))
                self.write_line("  Hardware is Virtual Ethernet, address is 748e.f8a7.1b01 (bia 748e.f8a7.1b01)")
                self.write_line("  No port name")
                self.write_line("  Vlan id: {}".format(vlan_id))
                self.write_line("  Internet address is 0.0.0.0/0, IP MTU 1500 bytes, encapsulation ethernet")
                self.write_line("  Configured BW 0 kbps")

    def get_interface_vlan_for(self, vlan):
        return next((p for p in self.switch_configuration.ports
                     if isinstance(p, VlanPort) and p.vlan_id == vlan.number),
                    None)

    def show_version(self):
        self.write_line("System: NetIron CER (Serial #: 1P2539K036,  Part #: 40-1000617-02)")
        self.write_line("License: RT_SCALE, ADV_SVCS_PREM (LID: XXXXXXXXXX)")
        self.write_line("Boot     : Version 5.8.0T185 Copyright (c) 1996-2014 Brocade Communications Systems, Inc.")
        self.write_line("Compiled on May 18 2015 at 13:03:00 labeled as ceb05800")
        self.write_line(" (463847 bytes) from boot flash")
        self.write_line("Monitor  : Version 5.8.0T185 Copyright (c) 1996-2014 Brocade Communications Systems, Inc.")
        self.write_line("Compiled on May 18 2015 at 13:03:00 labeled as ceb05800")
        self.write_line(" (463847 bytes) from code flash")
        self.write_line("IronWare : Version 5.8.0bT183 Copyright (c) 1996-2014 Brocade Communications Systems, Inc.")
        self.write_line("Compiled on May 21 2015 at 09:20:22 labeled as ce05800b")
        self.write_line(" (17563175 bytes) from Primary")
        self.write_line("CPLD Version: 0x00000010")
        self.write_line("Micro-Controller Version: 0x0000000d")
        self.write_line("Extended route scalability")
        self.write_line("PBIF Version: 0x0162")
        self.write_line("800 MHz Power PC processor 8544 (version 8021/0023) 400 MHz bus")
        self.write_line("512 KB Boot Flash (MX29LV040C), 64 MB Code Flash (MT28F256J3)")
        self.write_line("2048 MB DRAM")
        self.write_line("System uptime is 109 days 4 hours 39 minutes 4 seconds")

    def get_interface_ports_for(self, vlan):
        vlan_ports = {"tagged": [], "untagged": []}
        for port in self.switch_configuration.ports:
            if not isinstance(port, VlanPort):
                if port.access_vlan == vlan.number or port.trunk_native_vlan == vlan.number:
                    vlan_ports["untagged"].append(port)
                elif port.trunk_vlans and vlan.number in port.trunk_vlans:
                    vlan_ports["tagged"].append(port)
        return vlan_ports


def port_index(port):
    return int(re.match(".*(\d)$", port.name).groups()[0])


def to_port_ranges(ports):
    port_range_list = group_sequences(ports, are_in_sequence=lambda a, b: port_index(a) + 1 == port_index(b))

    out = []
    for port_range in port_range_list:
        if len(port_range) == 1:
            out.append("ethe %s" % split_port_name(port_range[0].name)[1])
        else:
            out.append("ethe %s to %s" %
                       (split_port_name(port_range[0].name)[1], split_port_name(port_range[-1].name)[1]))

    out_str = " ".join(out)
    return out_str


def vlan_name(vlan):
    return vlan.name or ("DEFAULT-VLAN" if vlan.number == 1 else None)


def get_port_attributes(port):
    attributes = []
    if port.description:
        attributes.append("port-name %s" % port.description)
    if port.shutdown is False:
        attributes.append("enable")
    if port.vrf is not None:
        attributes.append("vrf forwarding {}".format(port.vrf.name))
    if isinstance(port, VlanPort):
        for ip in sorted(port.ips, key=lambda e: e.ip):
            attributes.append("ip address %s" % ip)
        for ip in sorted(port.secondary_ips, key=lambda e: e.ip):
            attributes.append("ip address %s secondary" % ip)
        if port.access_group_in:
            attributes.append("ip access-group %s in" % port.access_group_in)
        if port.access_group_out:
            attributes.append("ip access-group %s out" % port.access_group_out)
        if port.vrrp_common_authentication:
            attributes.append("ip vrrp-extended auth-type simple-text-auth ********")
        for vrrp in port.vrrps:
            attributes.append("ip vrrp-extended vrid %s" % vrrp.group_id)
            if vrrp.priority and len(vrrp.track) > 0:
                attributes.append(" backup priority %s track-priority %s" % (vrrp.priority, list(vrrp.track.values())[0]))
            if vrrp.ip_addresses:
                for ip_address in vrrp.ip_addresses:
                    attributes.append(" ip-address %s" % ip_address)
            if vrrp.advertising:
                attributes.append(" advertise backup")
            if vrrp.timers_hold:
                attributes.append(" dead-interval %s" % vrrp.timers_hold)
            if vrrp.timers_hello:
                attributes.append(" hello-interval %s" % vrrp.timers_hello)
            if len(vrrp.track) > 0 and list(vrrp.track.keys())[0] is not None:
                attributes.append(" track-port %s" % list(vrrp.track.keys())[0])
            if vrrp.activated:
                attributes.append(" activate")
            else:
                attributes.append(" exit")
        for ip_address in port.ip_helpers:
            attributes.append("ip helper-address %s" % ip_address)
        if port.ip_redirect is False:
            attributes.append("no ip redirect")

    return attributes


def vlan_membership(port):
    if port.access_vlan:
        return "Member of VLAN %s (untagged)" % port.access_vlan
    elif port.trunk_vlans and port.trunk_native_vlan:
        return "Member of VLAN %s (untagged), %d L2 VLANS (tagged)" % (port.trunk_native_vlan, len(port.trunk_vlans))
    elif port.trunk_vlans and not port.trunk_native_vlan:
        return "Member of %d L2 VLAN(S) (tagged)" % len(port.trunk_vlans)
    else:
        return "Member of VLAN 1 (untagged)"


def port_mode(port):
    if port.trunk_vlans and port.trunk_native_vlan == 1:
        return "port is in dual mode (default vlan)"
    elif port.trunk_vlans and port.trunk_native_vlan:
        return "port is in dual mode"
    elif port.access_vlan or port.trunk_vlans is None:
        return "port is in untagged mode"
    else:
        return "port is in tagged mode"


def port_state(_):
    return "port state is Disabled"
