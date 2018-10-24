# Copyright 2018 Inap.
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
from functools import wraps

import pyeapi


def with_eapi(test):
    @wraps(test)
    def wrapper(self, protocol):
        api = pyeapi.connect(transport="http", host=protocol.host, port=protocol.conf["http"],
                             username=protocol.username, password=protocol.password, return_node=True)
        test(self, protocol, api)

    return wrapper


def enable(t):
    t.write("enable")
    t.read("my_arista#")


def create_vlan(t, vlan, name=None):
    t.write("configure terminal")
    t.read("my_arista(config)#")
    t.write("vlan {}".format(vlan))
    t.read("my_arista(config-vlan-{})#".format(vlan))
    if name:
        t.write("name {}".format(name))
        t.read("my_arista(config-vlan-{})#".format(vlan))
    t.write("exit")
    t.read("my_arista(config)#")
    t.write("exit")
    t.read("my_arista#")


def create_interface_vlan(t, vlan):
    t.write("configure terminal")
    t.read("my_arista(config)#")
    t.write("interface vlan {}".format(vlan))
    t.read("my_arista(config-if-Vl{})#".format(vlan))
    t.write("exit")
    t.read("my_arista(config)#")
    t.write("exit")
    t.read("my_arista#")


def configuring_interface_vlan(t, vlan, do):
    t.write("configure terminal")
    t.read("my_arista(config)#")
    t.write("interface vlan {}".format(vlan))
    t.read("my_arista(config-if-Vl{})#".format(vlan))

    t.write(do)

    t.read("my_arista(config-if-Vl{})#".format(vlan))
    t.write("exit")
    t.read("my_arista(config)#")
    t.write("exit")
    t.read("my_arista#")


def remove_vlan(t, vlan):
    configuring(t, do="no vlan {}".format(vlan))


def remove_interface_vlan(t, vlan):
    configuring(t, do="no interface vlan {}".format(vlan))


def configuring(t, do):
    t.write("configure terminal")
    t.read("my_arista(config)#")

    t.write(do)

    t.read("my_arista(config)#")
    t.write("exit")
    t.read("my_arista#")
