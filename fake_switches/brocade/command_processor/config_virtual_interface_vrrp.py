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

from fake_switches.command_processing.base_command_processor import BaseCommandProcessor


class ConfigVirtualInterfaceVrrpCommandProcessor(BaseCommandProcessor):
    def init(self, switch_configuration, terminal_controller, logger, piping_processor, *args):
        super(ConfigVirtualInterfaceVrrpCommandProcessor, self).init(switch_configuration, terminal_controller, logger, piping_processor)
        self.port, self.vrrp = args

    def get_prompt(self):
        return "SSH@%s(config-vif-%s-vrid-%s)#" % (
            self.switch_configuration.name, self.port.vlan_id, self.vrrp.group_id)

    def do_backup(self, *args):
        if "priority".startswith(args[0]) and "track-priority".startswith(args[2]):
            self.vrrp.priority = args[1]
            if len(self.vrrp.track) > 0:
                track_port = list(self.vrrp.track.keys())[0]
            else:
                track_port = None
            self.vrrp.track.update({track_port: args[3]})

    def do_no_backup(self, *_):
        self.vrrp.priority = None
        if len(self.vrrp.track) > 0:
            track_port = list(self.vrrp.track.keys())[0]
        else:
            track_port = None
        self.vrrp.track.update({track_port: None})

    def do_ip_address(self, *args):
        if self.vrrp.ip_addresses is not None:
            self.vrrp.ip_addresses.append(args[0])
        else:
            self.vrrp.ip_addresses = [args[0]]

    def do_no_ip_address(self, *args):
        if args[0] in self.vrrp.ip_addresses:
            self.vrrp.ip_addresses.remove(args[0])

    def do_hello_interval(self, *args):
        self.vrrp.timers_hello = args[0]

    def do_no_hello_interval(self, *_):
        self.vrrp.timers_hello = None

    def do_dead_interval(self, *args):
        self.vrrp.timers_hold = args[0]

    def do_no_dead_interval(self, *_):
        self.vrrp.timers_hold = None

    def do_advertise(self, *_):
        self.vrrp.advertising = True

    def do_no_advertise(self, *_):
        self.vrrp.advertising = False

    def do_track_port(self, *args):
        old_value = None

        if len(self.vrrp.track) > 0:
            old_value = list(self.vrrp.track.values())[0]

        self.vrrp.track = {' '.join(args[0:2]): old_value}

    def do_no_track_port(self, *_):
        old_value = None

        if len(self.vrrp.track) > 0:
            old_value = list(self.vrrp.track.values())[0]

        self.vrrp.track = {None: old_value}

    def do_activate(self, *_):
        self.vrrp.activated = True
        self.is_done = True

    def do_no_activate(self, *_):
        self.vrrp.activated = False

    def do_exit(self):
        self.is_done = True
