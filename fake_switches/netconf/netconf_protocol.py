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

import logging
import re

from lxml import etree
from twisted.internet.protocol import Protocol

from fake_switches.netconf import dict_2_etree, NS_BASE_1_0, normalize_operation_name, SimpleDatastore, \
    Response, OperationNotSupported, NetconfError
from fake_switches.netconf.capabilities import Base1_0


class NetconfProtocol(Protocol):
    def __init__(self, datastore=None, capabilities=None, additionnal_namespaces=None, logger=None):
        self.logger = logger or logging.getLogger("fake_switches.netconf")

        self.input_buffer = ""
        self.session_count = 0
        self.been_greeted = False

        self.datastore = datastore or SimpleDatastore()
        caps_class_list = capabilities or []
        caps_class_list.insert(0, Base1_0)
        self.capabilities = [cap(self.datastore) for cap in caps_class_list]
        self.additionnal_namespaces = additionnal_namespaces or {}

    def __call__(self, *args, **kwargs):
        return self

    def connectionMade(self):
        self.logger.info("Connected, sending <hello>")

        self.session_count += 1

        self.say(dict_2_etree({
            "hello": [
                {"session-id": str(self.session_count)},
                {"capabilities": [{"capability": cap.get_url()} for cap in self.capabilities]}
            ]
        }))

    def dataReceived(self, data):
        data = data.decode()
        self.logger.info("Received : %s" % repr(data))
        self.input_buffer += data
        if self.input_buffer.rstrip().endswith("]]>]]>"):
            self.process(self.input_buffer.rstrip()[0:-6])
            self.input_buffer = ""

    def process(self, data):
        if not self.been_greeted:
            self.logger.info("Client's greeting received")
            self.been_greeted = True
            return

        xml_request_root = remove_namespaces(etree.fromstring(data.encode()))
        message_id = xml_request_root.get("message-id")
        operation = xml_request_root[0]
        self.logger.info("Operation requested %s" % repr(operation.tag))

        handled = False
        operation_name = normalize_operation_name(operation)
        for capability in self.capabilities:
            if hasattr(capability, operation_name):
                try:
                    self.reply(message_id, getattr(capability, operation_name)(operation))
                except NetconfError as e:
                    self.reply(message_id, Response(e.to_etree()))

                handled = True

        if not handled:
            self.reply(message_id, Response(OperationNotSupported(operation_name).to_etree()))

    def reply(self, message_id, response):
        reply = etree.Element("rpc-reply", xmlns=NS_BASE_1_0, nsmap=self.additionnal_namespaces)
        reply.attrib["message-id"] = message_id
        for ele in response.elements:
            reply.append(ele)

        self.say(reply)

        if response.require_disconnect:
            self.logger.info("Disconnecting")
            self.transport.loseConnection()

    def say(self, etree_root):
        self.logger.info("Saying : %s" % repr(etree.tostring(etree_root)))
        self.transport.write(etree.tostring(etree_root, pretty_print=True) + b"]]>]]>\n")


def remove_namespaces(xml_root):
    xml_root.tag = unqualify(xml_root.tag)
    for child in xml_root:
        remove_namespaces(child)
    return xml_root

def unqualify(tag):
    return re.sub("\{[^\}]*\}", "", tag)
