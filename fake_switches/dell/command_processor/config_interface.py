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

from fake_switches.cisco.command_processor.config_interface import \
    ConfigInterfaceCommandProcessor


class DellConfigInterfaceCommandProcessor(ConfigInterfaceCommandProcessor):

    def __init__(self, switch_configuration, terminal_controller, logger,
                 piping_processor, port):
        super(DellConfigInterfaceCommandProcessor, self).__init__(
            switch_configuration, terminal_controller, logger, piping_processor,
            port)
        self.description_strip_chars = "\"'"

    def get_prompt(self):
        if self.port.name.startswith("ethernet"):
            short_name = self.port.name.split(' ')[1]
        elif self.port.name.startswith("port-channel"):
            short_name = "ch{}".format(self.port.name.split(' ')[1])
        else:
            short_name = self.port.name.replace(' ', '').lower()
        return self.switch_configuration.name + "(config-if-%s)#" % short_name

    def do_description(self, *args):
        super(DellConfigInterfaceCommandProcessor, self).do_description(*args)
        self.write_line("")

    def do_no_description(self, *_):
        super(DellConfigInterfaceCommandProcessor, self).do_no_description(*_)
        self.write_line("")

    def do_no_shutdown(self, *_):
        super(DellConfigInterfaceCommandProcessor, self).do_no_shutdown(*_)
        self.write_line("")

    def do_shutdown(self, *_):
        super(DellConfigInterfaceCommandProcessor, self).do_shutdown(*_)
        self.write_line("")

    def do_spanning_tree(self, *args):
        if "disable".startswith(args[0]):
            self.port.spanning_tree = False
        if "portfast".startswith(args[0]):
            self.port.spanning_tree_portfast = True
        self.write_line("")

    def do_no_spanning_tree(self, *args):
        if "disable".startswith(args[0]):
            self.port.spanning_tree = None
        if "portfast".startswith(args[0]):
            self.port.spanning_tree_portfast = None
        self.write_line("")

    def do_lldp(self, *args):
        self.configure_lldp_port(args, target_value=True)
        self.write_line("")

    def do_no_lldp(self, *args):
        self.configure_lldp_port(args, target_value=False)
        self.write_line("")

    def configure_lldp_port(self, args, target_value):
        if "transmit".startswith(args[0]):
            self.port.lldp_transmit = target_value
        elif "receive".startswith(args[0]):
            self.port.lldp_receive = target_value
        elif "med".startswith(args[0]) and "transmit-tlv".startswith(args[1]):
            if "capabilities".startswith(args[2]):
                self.port.lldp_med_transmit_capabilities = target_value
            elif "network-policy".startswith(args[2]):
                self.port.lldp_med_transmit_network_policy = target_value

    def do_name(self, *args):
        if len(args) == 0:
            self.write_line("")
            self.write_line("Command not found / Incomplete command. Use ? to list commands.")
        elif len(args) > 1:
            self.write_line("                                     ^")
            self.write_line("% Invalid input detected at '^' marker.")
        elif len(args[0]) > 32:
            self.write_line("Name must be 32 characters or less.")
        else:
            vlan = self.switch_configuration.get_vlan(self.port.vlan_id)
            vlan.name = args[0]

        self.write_line("")

    def do_switchport(self, *args):
        if "access".startswith(args[0]) and "vlan".startswith(args[1]):
            self.set_access_vlan(int(args[2]))
        elif "mode".startswith(args[0]):
            self.set_switchport_mode(args[1])
        elif ("general".startswith(args[0]) or "trunk".startswith(args[0])) and "allowed".startswith(args[1]):
            if "general".startswith(args[0]) and self.port.mode != "general":
                self.write_line("Interface not in General Mode.")
            elif "trunk".startswith(args[0]) and self.port.mode != "trunk":
                self.write_line("Interface not in Trunk Mode.")
            elif "vlan".startswith(args[2]):
                if len(args) > 5:
                    self.write_line("                                                                 ^")
                    self.write_line("% Invalid input detected at '^' marker.")
                else:
                    operation = args[3]
                    vlan_range = args[4]
                    self.update_trunk_vlans(operation, vlan_range)
                    return
        elif "general".startswith(args[0]) and "pvid".startswith(args[1]):
            self.set_trunk_native_vlan(int(args[2]))

        self.write_line("")

    def do_no_switchport(self, *args):
        if "access".startswith(args[0]):
            if "vlan".startswith(args[1]):
                self.print_vlan_warning()
                self.port.access_vlan = None
        elif "general".startswith(args[0]):
            if "pvid".startswith(args[1]):
                self.port.trunk_native_vlan = None

        self.write_line("")

    def set_switchport_mode(self, mode):
        if mode not in ("access", "trunk", "general"):
            self.write_line("                                         ^")
            self.write_line("% Invalid input detected at '^' marker.")
        else:
            if self.port.mode != mode:
                self.port.mode = mode
                self.port.access_vlan = None
                self.port.trunk_native_vlan = None
                self.port.trunk_vlans = None

    def set_access_vlan(self, vlan_id):
        self.print_vlan_warning()
        vlan = self.switch_configuration.get_vlan(int(vlan_id))
        if vlan:
            self.port.access_vlan = vlan.number
        else:
            self.write_line("")
            self.write_line("VLAN ID not found.")

    def set_trunk_native_vlan(self, native_vlan):
        if self.port.mode != "general":
            self.write_line("")
            self.write_line("Port is not general port.")
        else:
            vlan = self.switch_configuration.get_vlan(native_vlan)
            if vlan is None:
                self.write_line("Could not configure pvid.")
            else:
                self.port.trunk_native_vlan = vlan.number

    def update_trunk_vlans(self, operation, vlan_range):
        try:
            vlans = parse_vlan_list(vlan_range)
        except ValueError:
            self.write_line("VLAN range - separate non-consecutive IDs with ',' and no spaces.  Use '-' for range.")
            self.write_line("")
            return

        self.print_vlan_warning()

        vlans_not_found = [v for v in vlans if self.switch_configuration.get_vlan(v) is None]
        if len(vlans_not_found) > 0:
            self.write_line("")
            self.write_line("          Failure Information")
            self.write_line("---------------------------------------")
            self.write_line("   VLANs failed to be configured : {}".format(len(vlans_not_found)))
            self.write_line("---------------------------------------")
            self.write_line("   VLAN             Error")
            self.write_line("---------------------------------------")
            for vlan in vlans_not_found:
                self.write_line("VLAN      {: >4} ERROR: This VLAN does not exist.".format(vlan))
            return

        if "add".startswith(operation):
            if self.port.trunk_vlans is None:
                self.port.trunk_vlans = []
            self.port.trunk_vlans = list(set(self.port.trunk_vlans + vlans))
        if "remove".startswith(operation):
            for v in vlans:
                if v in self.port.trunk_vlans:
                    self.port.trunk_vlans.remove(v)
            if len(self.port.trunk_vlans) == 0:
                self.port.trunk_vlans = None

        self.write_line("")

    def print_vlan_warning(self):
        self.write_line("Warning: The use of large numbers of VLANs or interfaces may cause significant")
        self.write_line("delays in applying the configuration.")
        self.write_line("")


def parse_vlan_list(param):
    ranges = param.split(",")
    vlans = []
    for r in ranges:
        if "-" in r:
            start, stop = r.split("-")
            if stop < start:
                raise ValueError
            vlans += [v for v in range(int(start), int(stop) + 1)]
        else:
            vlans.append(int(r))

    return vlans
