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

import pprint

from hamcrest import assert_that, is_


def enable(t):
    t.write("enable")
    t.read("Password:")
    t.write_stars(t.conf["extra"].get("password", "root"))
    t.readln("")
    t.read("my_switch#")


def configuring(t, do):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")

    t.write(do)

    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def add_vlan(t, vlan_id):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("vlan {}".format(vlan_id))
    t.readln("")
    t.read("my_switch(config-vlan{})#".format(vlan_id))
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def configuring_vlan(t, vlan_id, do):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")

    t.write("vlan {}".format(vlan_id))
    t.readln("")

    t.read("my_switch(config-vlan{})#".format(vlan_id))

    t.write(do)
    t.readln("")

    t.read("my_switch(config-vlan{})#".format(vlan_id))
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def configuring_interface(t, interface, do):
    interface_short_name = interface.split(' ')[1]
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("interface {}".format(interface))
    t.readln("")
    t.read("my_switch(config-if-Te{})#".format(interface_short_name))

    t.write(do)

    t.readln("")
    t.read("my_switch(config-if-Te{})#".format(interface_short_name))
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def create_bond(t, bond_id):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("interface port-channel {}".format(bond_id))
    t.readln("")
    t.read("my_switch(config-if-Po{})#".format(bond_id))
    t.write("exit")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def remove_bond(t, bond_id):
    t.write("configure")
    t.readln("")
    t.read("my_switch(config)#")
    t.write("no interface port-channel {}".format(bond_id))
    t.readln("")
    t.read("my_switch(config)#")
    t.write("exit")
    t.readln("")
    t.read("my_switch#")


def assert_interface_configuration(t, interface, config):
    t.write("show running-config interface {}".format(interface))
    for line in config:
        t.readln(line)
    t.readln("")
    t.read("my_switch#")


def assert_running_config_contains_in_order(t, lines):
    config = get_running_config(t)

    assert_lines_order(config, lines)


def get_running_config(t):
    t.write("show running-config")
    config = t.read_lines_until('my_switch#')
    return config


def assert_lines_order(config, lines):
    begin = config.index(lines[0])

    for (i, line) in enumerate(lines):
        expected_content = line
        expected_line_number = i + begin
        actual_content = config[expected_line_number]

        assert_that(actual_content, is_(expected_content),
                    "Item <%s> was expected to be found at line {} but found {} instead.\nWas looking for {} in {}".format(
                        line, expected_line_number, actual_content, pprint.pformat(lines), pprint.pformat(config)))
