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

import logging
import textwrap

from fake_switches import switch_core
from fake_switches.juniper.juniper_netconf_datastore import JuniperNetconfDatastore, NS_JUNOS
from fake_switches.netconf import OperationNotSupported, RUNNING, CANDIDATE, Response, xml_equals, NetconfError
from fake_switches.netconf.capabilities import Candidate1_0, ConfirmedCommit1_0, Validate1_0, Url1_0, \
    Capability
from fake_switches.netconf.netconf_protocol import NetconfProtocol
from fake_switches.switch_configuration import Port, AggregatedPort
from lxml import etree


class BaseJuniperSwitchCore(switch_core.SwitchCore):
    def __init__(self, switch_configuration, datastore_class):
        super(BaseJuniperSwitchCore, self).__init__(switch_configuration)

        self.last_connection_id = 0
        self.datastore = datastore_class(self.switch_configuration)

    def launch(self, protocol, terminal_controller):
        raise NotImplemented()

    def process_command(self, line):
        raise NotImplemented()

    def get_netconf_protocol(self):
        self.last_connection_id += 1

        return NetconfProtocol(
            datastore=self.datastore,
            capabilities=self.capabilities(),
            additionnal_namespaces={"junos": NS_JUNOS},
            logger=logging.getLogger(
                "fake_switches.juniper.%s.%s.netconf" % (self.switch_configuration.name, self.last_connection_id))
        )

    def capabilities(self):
        return [
            Candidate1_0,
            ConfirmedCommit1_0,
            Validate1_0,
            Url1_0,
            NetconfJunos1_0,
            DmiSystem1_0
        ]

    @staticmethod
    def get_default_ports():
        return [Port("ge-0/0/{}".format(i)) for i in range(1, 5)] + \
               [AggregatedPort("ae{}".format(i)) for i in range(1, 24)]


class JuniperSwitchCore(BaseJuniperSwitchCore):
    def __init__(self, switch_configuration):
        super(JuniperSwitchCore, self).__init__(switch_configuration, datastore_class=JuniperNetconfDatastore)


class NetconfJunos1_0(Capability):
    def get_url(self):
        return "http://xml.juniper.net/netconf/junos/1.0"

    def get_configuration(self, request):
        if "compare" not in request.attrib:
            raise OperationNotSupported("get_configuration without a compare")

        running = self.datastore.to_etree(RUNNING)
        candidate = self.datastore.to_etree(CANDIDATE)

        # NOTE(lindycoder): Not actually computing the diff, not needed so far, just show that there's a change
        data_string = textwrap.dedent(
            """
            <configuration-information>
                <configuration-output>{0}</configuration-output>
            </configuration-information>
            """).format("There were some changes" if not xml_equals(running, candidate) else "")
        data = etree.fromstring(data_string, parser=etree.XMLParser(recover=True))

        return Response(data)

    def get_interface_information(self, request):
        if len(request) == 1 and request[0].tag == "terse":
            return Response(self.datastore.get_interface_information_terse())

        raise NetconfError("syntax error", err_type="protocol", tag="operation-failed")


class DmiSystem1_0(Capability):
    def get_url(self):
        return "http://xml.juniper.net/dmi/system/1.0"
