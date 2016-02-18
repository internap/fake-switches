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

import re
from lxml import etree

RUNNING = "running"
CANDIDATE = "candidate"
NS_BASE_1_0 = "urn:ietf:params:xml:ns:netconf:base:1.0"

XML_ATTRIBUTES = "__xml_attributes__"
XML_TEXT = "__xml_text__"
XML_NS = "__xml_ns__"

class SimpleDatastore(object):
    def __init__(self):
        self.data = {
            RUNNING: {},
            CANDIDATE: {}
        }

    def set_data(self, source, data):
        self.data[source] = data

    def to_etree(self, source):
        return dict_2_etree({"data": self.data[source]})

    def edit(self, target, config):
        pass

    def lock(self):
        pass

    def unlock(self):
        pass

class Response(object):
    def __init__(self, etree_object, require_disconnect=False):
        self.etree = etree_object
        self.require_disconnect = require_disconnect


def dict_2_etree(source_dict):

    def append(root, data):
        if isinstance(data, dict):
            for k, v in data.items():
                if k == XML_ATTRIBUTES:
                    for a, val in sorted(v.items()):
                        root.set(a, val)
                elif k == XML_TEXT:
                    root.text = v
                else:
                    if XML_NS in v:
                        sub = etree.SubElement(root, k, xmlns=v[XML_NS])
                        del v[XML_NS]
                    else:
                        sub = etree.SubElement(root, k)
                    append(sub, v)
        elif isinstance(data, list):
            for e in data:
                append(root, e)
        else:
            root.text = data

    root_element = source_dict.keys()[0]
    root_etree = etree.Element(root_element)
    append(root_etree, source_dict[root_element])
    return root_etree

def resolve_source_name(xml_tag):
    if xml_tag.endswith(RUNNING):
        return RUNNING
    elif xml_tag.endswith(CANDIDATE):
        return CANDIDATE
    else:
        raise Exception("What is this source : %s" % xml_tag)

def first(node):
    return node[0] if node else None


def normalize_operation_name(element):
    tag = unqualify(element)
    return re.sub("-", "_", tag)


def unqualify(lxml_element):
    return re.sub("\{.*\}", "", lxml_element.tag)


class NetconfError(Exception):
    def __init__(self, msg, severity="error", err_type=None, tag=None, info=None):
        super(NetconfError, self).__init__(msg)
        self.severity = severity
        self.type = err_type
        self.tag = tag
        self.info = info


class AlreadyLocked(NetconfError):
    def __init__(self):
        super(AlreadyLocked, self).__init__("Configuration database is already open")


class CannotLockUncleanCandidate(NetconfError):
    def __init__(self):
        super(CannotLockUncleanCandidate, self).__init__("configuration database modified")


class UnknownVlan(NetconfError):
    def __init__(self, vlan, interface, unit):
        super(UnknownVlan, self).__init__("No vlan matches vlan tag %s for interface %s.%s" % (vlan, interface, unit))


class OperationNotSupported(NetconfError):
    def __init__(self, name):
        super(OperationNotSupported, self).__init__(
            "Operation %s not found amongst current capabilities" % name,
            severity="error",
            err_type="protocol",
            tag="operation-not-supported"
        )


def xml_equals(actual_node, node):
    if unqualify(node) != unqualify(actual_node): return False
    if len(node) != len(actual_node): return False
    if node.text is not None:
        if actual_node.text is None: return False
        elif node.text.strip() != actual_node.text.strip(): return False
    elif actual_node.text is not None: return False
    for name, value in node.attrib.items():
        if name not in actual_node.attrib: return False
        if actual_node.attrib[name] != value: return False
    if actual_node.nsmap != node.nsmap: return False
    return _compare_children(node, actual_node)

def _compare_children(expected, actual):
    for i, node in enumerate(expected):
        actual_node = actual[i]
        if not xml_equals(actual_node, node):
            return False

    return True
