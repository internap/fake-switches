import logging
import unittest

from hamcrest.core.base_matcher import BaseMatcher
import re
from hamcrest import assert_that, ends_with, equal_to, has_length, has_key
from mock import Mock
from ncclient.xml_ import to_ele, to_xml
from fake_switches.netconf import RUNNING, dict_2_etree
from fake_switches.netconf.capabilities import filter_content
from fake_switches.netconf.netconf_protocol import NetconfProtocol


class NetconfProtocolTest(unittest.TestCase):
    def setUp(self):
        self.netconf = NetconfProtocol(logger=logging.getLogger())
        self.netconf.transport = Mock()

    def test_says_hello_upon_connection_and_receive_an_hello(self):
        self.netconf.connectionMade()

        self.assert_xml_response("""
            <hello>
              <session-id>1</session-id>
              <capabilities>
                <capability>urn:ietf:params:xml:ns:netconf:base:1.0</capability>
              </capabilities>
            </hello>
            """)

    def test_close_session_support(self):
        self.netconf.connectionMade()
        self.say_hello()

        self.netconf.dataReceived('<nc:rpc xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="12345">\n')
        self.netconf.dataReceived('  <nc:close-session/>\n')
        self.netconf.dataReceived('</nc:rpc>\n')
        self.netconf.dataReceived(']]>]]>\n')

        self.assert_xml_response("""
            <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="12345">
                <ok/>
            </rpc-reply>
            """)
        self.netconf.transport.loseConnection.assert_called_with()

    def test_get_config_support(self):
        self.netconf.datastore.set_data(RUNNING, {"configuration": {"stuff": "is cool!"}})
        self.netconf.connectionMade()
        self.say_hello()

        self.netconf.dataReceived("""
            <rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="67890">
              <get-config>
                <source><running /></source>
              </get-config>
            </rpc>
            ]]>]]>""")

        self.assert_xml_response("""
            <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="67890">
                <data>
                  <configuration>
                    <stuff>is cool!</stuff>
                  </configuration>
                </data>
            </rpc-reply>
            """)

        assert_that(self.netconf.transport.loseConnection.called, equal_to(False))

    def test_request_with_namespace(self):
        self.netconf.datastore.set_data(RUNNING, {"configuration": {"stuff": "is cool!"}})
        self.netconf.connectionMade()
        self.say_hello()

        self.netconf.dataReceived("""
            <nc:rpc xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="67890">
              <nc:get-config>
                <nc:source><nc:running/></nc:source>
              </nc:get-config>
            </nc:rpc>
            ]]>]]>""")

        self.assert_xml_response("""
            <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="67890">
                <data>
                  <configuration>
                    <stuff>is cool!</stuff>
                  </configuration>
                </data>
            </rpc-reply>
            """)

    def test_edit_config(self):
        self.netconf.datastore.set_data(RUNNING, {"configuration": {"stuff": {"substuff": "is cool!"}}})
        self.netconf.connectionMade()
        self.say_hello()

        self.netconf.dataReceived("""<?xml version="1.0" encoding="UTF-8"?>
            <nc:rpc xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:346c9f18-c420-11e4-8e4c-fa163ecd3b0a">
                <nc:edit-config>
                    <nc:target>
                        <nc:candidate/>
                    </nc:target>
                    <nc:config>
                        <nc:configuration><nc:stuff><substuff>is hot!</substuff></nc:stuff></nc:configuration>
                    </nc:config>
                </nc:edit-config>
            </nc:rpc>]]>]]>""")

        self.assert_xml_response("""
            <rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:346c9f18-c420-11e4-8e4c-fa163ecd3b0a">
                <ok/>
            </rpc-reply>
            """)

    def test_reply_includes_additional_namespaces(self):
        self.netconf.additionnal_namespaces = {
            "junos": "http://xml.juniper.net/junos/11.4R1/junos",
            "nc": "urn:ietf:params:xml:ns:netconf:base:1.0",
        }
        self.netconf.connectionMade()
        self.say_hello()

        self.netconf.dataReceived("""
            <nc:rpc xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="67890">
              <nc:get-config>
                <nc:source><nc:running/></nc:source>
              </nc:get-config>
            </nc:rpc>
            ]]>]]>""")

        assert_that(self.netconf.transport.write.call_args[0][0], xml_equals_to("""
            <rpc-reply xmlns:junos="http://xml.juniper.net/junos/11.4R1/junos" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="67890">
              <data/>
            </rpc-reply>
            ]]>]]>
            """
                                                                                ))

    def test_filtering(self):
        content = dict_2_etree({
            "data": {
                "configuration": [
                    {"shizzle": {
                        "whizzle": {}
                    }},
                    {"shizzle": {
                        "whizzle": {
                            "howdy": {}
                        },
                        "not-whizzle": {
                            "not-howdy": {}
                        }
                    }},
                    {"zizzle": {
                        "nothing": {}
                    }},
                    {"outzzle": {
                        "nothing": {}
                    }}
                ]
            }
        })

        content_filter = dict_2_etree({
            "filter": {
                "configuration": {
                    "shizzle": {"whizzle": {}},
                    "zizzle": {},
                }
            }
        })

        filter_content(content, content_filter)

        assert_that(content.xpath("//data/configuration/shizzle"), has_length(2))
        assert_that(content.xpath("//data/configuration/shizzle/*"), has_length(2))
        assert_that(content.xpath("//data/configuration/shizzle/whizzle/howdy"), has_length(1))
        assert_that(content.xpath("//data/configuration/zizzle"), has_length(1))
        assert_that(content.xpath("//data/configuration/outzzle"), has_length(0))

    def test_filtering_with_a_value(self):
        content = dict_2_etree({
            "data": {
                "configuration": [
                    {"element": {
                        "element-key": "MY-KEY",
                        "attribute": {"sub-attribute": {}}
                    }},
                    {"element": {
                        "element-key": "MY-OTHER-KEY",
                        "other-attribute": {"sub-attribute": {}}
                    }},
                ]
            }
        })

        content_filter = dict_2_etree({
            "filter": {
                "configuration": {
                    "element": {
                        "element-key": "MY-KEY"
                    },
                }
            }
        })

        filter_content(content, content_filter)

        assert_that(content.xpath("//data/configuration/element"), has_length(1))
        assert_that(content.xpath("//data/configuration/element/*"), has_length(2))
        assert_that(content.xpath("//data/configuration/element/attribute/*"), has_length(1))

    def say_hello(self):
        self.netconf.dataReceived(
            '<hello xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"><capabilities><capability>urn:ietf:params:xml:ns:netconf:base:1.0</capability></capabilities></hello>]]>]]>')

    def assert_xml_response(self, expected):
        data = self.netconf.transport.write.call_args[0][0]
        assert_that(data, ends_with("]]>]]>\n"))
        data = data.replace("]]>]]>", "")
        assert_that(data, xml_equals_to(expected))


def xml_equals_to(string):
    return XmlEqualsToMatcher(string)


class XmlEqualsToMatcher(BaseMatcher):
    def __init__(self, expected):
        self.expected = to_ele(expected)
        self.last_error = None

    def _matches(self, other):
        otherxml = other if not isinstance(other, basestring) else to_ele(other)
        try:
            self.compare_nodes(self.expected, otherxml)
            return True
        except AssertionError as e:
            self.last_error = e
            return False

    def describe_to(self, description):
        description.append_text(to_xml(self.expected, pretty_print=True))

    def describe_mismatch(self, item, mismatch_description):
        itemxml = item if not isinstance(item, basestring) else to_ele(item)
        mismatch_description.append_text("WAS : \n" + to_xml(itemxml, pretty_print=True) + "\n\n")
        mismatch_description.append_text("IN WHICH : " + str(self.last_error))

    def compare_nodes(self, actual_node, node):
        assert_that(unqualify(node.tag), equal_to(unqualify(actual_node.tag)))
        assert_that(node, has_length(len(actual_node)))
        if node.text is not None:
            if node.text.strip() == "":
                assert_that(actual_node.text is None or actual_node.text.strip() == "")
            else:
                assert_that(node.text.strip(), equal_to(actual_node.text.strip()))
        for name, value in node.attrib.items():
            assert_that(actual_node.attrib, has_key(name))
            assert_that(actual_node.attrib[name], equal_to(value))
        assert_that(actual_node.nsmap, equal_to(node.nsmap))
        self.compare_children(node, actual_node)

    def compare_children(self, expected, actual):
        for i, node in enumerate(expected):
            actual_node = actual[i]
            self.compare_nodes(actual_node, node)


def unqualify(tag):
    return re.sub("\{[^\}]*\}", "", tag)
