# Copyright 2015-2018 Internap.
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
from fake_switches.netconf import dict_2_etree, XML_ATTRIBUTES, XML_TEXT
from hamcrest import assert_that, has_length, has_items, equal_to, is_, contains_string
from lxml import etree
from ncclient.operations import RPCError
from tests import contains_regex
from tests.juniper import BaseJuniper
from tests.juniper.assertion_tools import has_xpath
from tests.juniper_qfx_copper.juniper_qfx_copper_protocol_test import reset_interface
from tests.netconf.netconf_protocol_test import xml_equals_to
from tests.util.global_reactor import ThreadedReactor


class JuniperMXProtocolTest(BaseJuniper):
    test_switch = "juniper_mx"

    def test_capabilities(self):
        assert_that(list(self.nc.server_capabilities), has_items(
            "urn:ietf:params:xml:ns:netconf:base:1.0",
            "urn:ietf:params:xml:ns:netconf:capability:candidate:1.0",
            "urn:ietf:params:xml:ns:netconf:capability:confirmed-commit:1.0",
            "urn:ietf:params:xml:ns:netconf:capability:validate:1.0",
            "urn:ietf:params:xml:ns:netconf:capability:url:1.0?protocol=http,ftp,file",
            "urn:ietf:params:netconf:capability:validate:1.0",
            "urn:ietf:params:netconf:capability:candidate:1.0",
            "urn:ietf:params:netconf:capability:confirmed-commit:1.0",
            "urn:ietf:params:netconf:capability:url:1.0?scheme=http,ftp,file",
            "http://xml.juniper.net/netconf/junos/1.0",
            "http://xml.juniper.net/dmi/system/1.0"
        ))

    def test_get_running_config_shows_nothing_by_default(self):
        result = self.nc.get_config(source="running")

        conf = result._NCElement__result.xml
        assert_that(conf, contains_regex(
            '<configuration xmlns="http://xml.juniper.net/xnm/1.1/xnm" junos:commit-localtime="[^"]*" junos:commit-seconds="[^"]*" junos:commit-user="[^"]*"'))

        assert_that(result.xpath("data/configuration/*"), has_length(0))

    def test_only_configured_interfaces_are_returned(self):
        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"description": "I see what you did there!"}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running")

        assert_that(result.xpath("data/configuration/interfaces/*"), has_length(1))

        self.cleanup(reset_interface("xe-0/0/3"))

    def test_lock_edit_candidate_add_vlan_and_commit(self):
        with self.nc.locked(target='candidate'):
            result = self.nc.edit_config(target='candidate', config=dict_2_etree({
                "config": {
                    "configuration": {
                        "bridge-domains": {
                            "domain": {
                                "name": "VLAN2999",
                                "vlan-id": "2999",
                            }
                        }
                    }
                }}))
            assert_that(result.xpath("//rpc-reply/ok"), has_length(1))

            result = self.nc.commit()
            assert_that(result.xpath("//rpc-reply/ok"), has_length(1))

        result = self.nc.get_config(source="running")

        assert_that(result.xpath("data/configuration/bridge-domains/domain"), has_length(1))

        self.edit({
            "bridge-domains": {
                "domain": {
                    XML_ATTRIBUTES: {"operation": "delete"},
                    "name": "VLAN2999"
                }
            }
        })

        self.nc.commit()

        result = self.nc.get_config(source="running")
        assert_that(result.xpath("data/configuration/bridge-domains/domain"), has_length(0))

    def test_locking_fails_if_changes_are_being_made(self):
        nc2 = self.create_client()

        try:
            self.nc.edit_config(target='candidate', config=dict_2_etree({
                "config": {
                    "configuration": {
                        "bridge-domains": {
                            "domain": [
                                {"name": "VLAN2999"},
                                {"description": "WHAAT"}
                            ]
                        }
                    }
                }}))

            with self.assertRaises(RPCError):
                with nc2.locked(target='candidate'):
                    self.fail('Should not be able to lock an edited configuration')

        finally:
            self.nc.discard_changes()
            nc2.close_session()

    def test_double_locking_with_two_sessions(self):
        nc2 = self.create_client()

        try:
            with self.nc.locked(target='candidate'):
                with self.assertRaises(RPCError):
                    with nc2.locked(target='candidate'):
                        self.fail("The second lock should not have worked.")

        finally:
            nc2.close_session()

    def test_bad_configuration_element(self):
        with self.assertRaises(RPCError):
            self.nc.edit_config(target='candidate', config=dict_2_etree({
                "config": {
                    "configuration": {
                        "vbleh": "shizzle"
                    }
                }}))

    def test_create_vlan(self):
        self.nc.edit_config(target='candidate', config=dict_2_etree({"config": {"configuration": {
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN2999"},
                    {"description": "WHAAT"},
                    {"vlan-id": "2995"}
                ]
            }
        }}}))

        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"bridge-domains": {}}}
        }))

        assert_that(result.xpath("data/*"), has_length(1))
        assert_that(result.xpath("data/configuration/*"), has_length(1))
        assert_that(result.xpath("data/configuration/bridge-domains/*"), has_length(1))
        assert_that(result.xpath("data/configuration/bridge-domains/domain/*"), has_length(3))

        vlan2995 = result.xpath("data/configuration/bridge-domains/domain")[0]

        assert_that(vlan2995.xpath("name")[0].text, equal_to("VLAN2999"))
        assert_that(vlan2995.xpath("description")[0].text, equal_to("WHAAT"))
        assert_that(vlan2995.xpath("vlan-id")[0].text, equal_to("2995"))

        self.cleanup(vlan("VLAN2999"))

    def test_vlan_configuration_merging(self):
        self.edit({
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN2999"},
                    {"vlan-id": "2995"}
                ]}})
        self.edit({
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN2999"},
                    {"description": "shizzle"}
                ]}})
        self.nc.commit()

        self.edit({
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN2999"},
                    {"vlan-id": "2996"},
                    {"description": {XML_ATTRIBUTES: {"operation": "delete"}}}
                ]}})

        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"bridge-domains": {}}}
        }))

        assert_that(result.xpath("data/configuration/bridge-domains/domain"), has_length(1))

        vlan2995 = result.xpath("data/configuration/bridge-domains/domain")[0]

        assert_that(vlan2995.xpath("name")[0].text, equal_to("VLAN2999"))
        assert_that(vlan2995.xpath("description"), has_length(0))
        assert_that(vlan2995.xpath("vlan-id")[0].text, equal_to("2996"))

        self.cleanup(vlan("VLAN2999"))

    def test_deletion_errors(self):
        self.edit({
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN2999"},
                    {"vlan-id": "2995"}]}})

        with self.assertRaises(RPCError):
            self.edit({
                "bridge-domains": {
                    "domain": {
                        "name": "VLAN3000",
                        XML_ATTRIBUTES: {"operation": "delete"}}}})

        with self.assertRaises(RPCError):
            self.edit({
                "bridge-domains": {
                    "domain": [
                        {"name": "VLAN2999"},
                        {"description": {XML_ATTRIBUTES: {"operation": "delete"}}}
                    ]}})

        self.nc.commit()

        with self.assertRaises(RPCError):
            self.edit({
                "bridge-domains": {
                    "domain": {
                        "name": "VLAN3000",
                        XML_ATTRIBUTES: {"operation": "delete"}}}})

        with self.assertRaises(RPCError):
            self.edit({
                "bridge-domains": {
                    "domain": [
                        {"name": "VLAN2999"},
                        {"description": {XML_ATTRIBUTES: {"operation": "delete"}}}
                    ]}})

        self.cleanup(vlan("VLAN2999"))

    def test_access_mode(self):
        self.edit({
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "access",
                                "vlan-id": "2995"}}}]}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int003 = result.xpath("data/configuration/interfaces/interface")[0]

        assert_that(int003.xpath("name")[0].text, equal_to("xe-0/0/3"))
        assert_that(int003.xpath("unit/family/bridge/*"), has_length(2))
        assert_that(int003.xpath("unit/family/bridge/interface-mode")[0].text,
                    equal_to("access"))
        assert_that(int003.xpath("unit/family/bridge/vlan-id")[0].text, equal_to("2995"))

        self.cleanup(vlan("VLAN2995"), reset_interface("xe-0/0/3"))

    def test_set_trunk_mode_access_mode_vlan_removal(self):
        self.edit({
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "access",
                                "vlan-id": "2995"}}}]}]}})
        self.nc.commit()

        self.edit({
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "trunk",
                                "vlan-id": {XML_ATTRIBUTES: {"operation": "delete"}},
                                "vlan-id-list": "2997"}
                        }}]}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))

        int003 = result.xpath("data/configuration/interfaces/interface")[0]

        assert_that(int003.xpath("unit/family/bridge/*"), has_length(2))
        assert_that(int003.xpath("unit/family/bridge/vlan-id"), has_length(0))
        assert_that(int003.xpath("unit/family/bridge/interface-mode")[0].text, equal_to("trunk"))
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list")[0].text, equal_to("2997"))

        self.cleanup(vlan("VLAN2995"), reset_interface("xe-0/0/3"))

    def test_trunk_mode_does_not_allow_no_vlan_members(self):
        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
                {"domain": [
                    {"name": "VLAN2996"},
                    {"vlan-id": "2996"}]},
                {"domain": [
                    {"name": "VLAN2997"},
                    {"vlan-id": "2997"}]},
            ],
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"native-vlan-id": "2996"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "trunk"
                            }}}]}]}})
        with self.assertRaises(RPCError) as context:
            self.nc.commit()

        assert_that(etree.tostring(context.exception._raw.xpath('/*/*')[0]), xml_equals_to(
            """<?xml version="1.0" encoding="UTF-8"?><commit-results xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns:junos="http://xml.juniper.net/junos/11.4R1/junos">
                <routing-engine junos:style="show-name">
                <name>re0</name>
                <rpc-error>
                <error-type>application</error-type>
                <error-tag>invalid-value</error-tag>
                <error-severity>error</error-severity>
                <error-path>[edit interfaces xe-0/0/3 unit 0 family bridge interface-mode]</error-path>
                <error-message>mgd: 'interface-mode trunk' must be defined with either 'vlan-id-list','isid-list', 'inner-vlan-id-list' or the interface must be configured for 'protocols mvrp'</error-message>
                <error-info>
                <bad-element>interface-mode trunk</bad-element>
                </error-info>
                </rpc-error>
                <rpc-error>
                <error-type>protocol</error-type>
                <error-tag>operation-failed</error-tag>
                <error-severity>error</error-severity>
                <error-message>
                commit failed: (statements constraint check failed)
                </error-message>
                </rpc-error>
                </routing-engine>
                </commit-results>"""))

        self.cleanup(vlan("VLAN2995"), vlan("VLAN2996"), vlan("VLAN2997"),
                     reset_interface("xe-0/0/3"))
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"bridge-domains": {}}}
        }))
        assert_that(result.xpath("data/configuration/bridge-domains/domain"), has_length(0))

    def test_trunk_mode(self):
        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
                {"domain": [
                    {"name": "VLAN2996"},
                    {"vlan-id": "2996"}]},
                {"domain": [
                    {"name": "VLAN2997"},
                    {"vlan-id": "2997"}]},
            ],
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"native-vlan-id": "2996"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": [
                                {"interface-mode": "trunk"},
                                {"vlan-id-list": "2995"},
                                {"vlan-id-list": "2997"}
                            ]}}]}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int003 = result.xpath("data/configuration/interfaces/interface")[0]

        assert_that(int003.xpath("name")[0].text, equal_to("xe-0/0/3"))
        assert_that(int003.xpath("native-vlan-id")[0].text, equal_to("2996"))
        assert_that(int003.xpath("unit/family/bridge/*"), has_length(3))
        assert_that(int003.xpath("unit/family/bridge/interface-mode")[0].text, equal_to("trunk"))
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list")[0].text, equal_to("2995"))
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list")[1].text, equal_to("2997"))

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "vlan-id-list": {XML_TEXT: "2995", XML_ATTRIBUTES: {"operation": "delete"}}},
                                }}]}]}})
        self.nc.commit()
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))
        int003 = result.xpath("data/configuration/interfaces/interface")[0]
        assert_that(int003.xpath("unit/family/bridge/*"), has_length(2))
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list")[0].text, equal_to("2997"))

        self.cleanup(vlan("VLAN2995"), vlan("VLAN2996"), vlan("VLAN2997"),
                     reset_interface("xe-0/0/3"))
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"bridge-domains": {}}}
        }))
        assert_that(result.xpath("data/configuration/bridge-domains/domain"), has_length(0))

    def test_trunk_mode_delete_all_vlan(self):
        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
                {"domain": [
                    {"name": "VLAN2996"},
                    {"vlan-id": "2996"}]},
                {"domain": [
                    {"name": "VLAN2997"},
                    {"vlan-id": "2997"}]},
            ],
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"native-vlan-id": "2996"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": [
                                {"interface-mode": "trunk"},
                                {"vlan-id-list": "2995"},
                                {"vlan-id-list": "2997"}
                            ]}}]}]}})
        self.nc.commit()

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": [{
                                "vlan-id-list": {XML_ATTRIBUTES: {"operation": "delete"}}},
                                {"vlan-id-list": "2996"}]
                                }}]}]}})
        self.nc.commit()
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))
        int003 = result.xpath("data/configuration/interfaces/interface")[0]
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list"), has_length(1))
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list")[0].text, equal_to("2996"))

        self.cleanup(vlan("VLAN2995"), vlan("VLAN2996"), vlan("VLAN2997"),
                     reset_interface("xe-0/0/3"))

    def test_interface_trunk_native_vlan_merge(self):
        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
                {"domain": [
                    {"name": "VLAN2996"},
                    {"vlan-id": "2996"}]},
                {"domain": [
                    {"name": "VLAN2997"},
                    {"vlan-id": "2997"}]},
            ],
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"native-vlan-id": "2995"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "trunk",
                                "vlan-id-list": "2997"}}}]}]}})
        self.nc.commit()

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"native-vlan-id": "2996"},
                ]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int003 = result.xpath("data/configuration/interfaces/interface")[0]
        assert_that(int003.xpath("native-vlan-id")[0].text, equal_to("2996"))

        self.cleanup(vlan("VLAN2995"), vlan("VLAN2996"), vlan("VLAN2997"),
                     reset_interface("xe-0/0/3"))
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"bridge-domains": {}}}
        }))
        assert_that(result.xpath("data/configuration/bridge-domains/domain"), has_length(0))

    def test_interface_set_trunk_native_vlan_then_set_members_after(self):
        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
                {"domain": [
                    {"name": "VLAN2996"},
                    {"vlan-id": "2996"}]},
                {"domain": [
                    {"name": "VLAN2997"},
                    {"vlan-id": "2997"}]},
            ],
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "trunk",
                                "vlan-id-list": "2996"
                            }}}]}]}})
        self.nc.commit()

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"native-vlan-id": "2995"}
                ]}})
        self.nc.commit()

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "vlan-id-list": "2997"}}}]}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int003 = result.xpath("data/configuration/interfaces/interface")[0]
        assert_that(int003.xpath("native-vlan-id")[0].text, equal_to("2995"))
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list"), has_length(2))
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list")[0].text, equal_to("2996"))
        assert_that(int003.xpath("unit/family/bridge/vlan-id-list")[1].text, equal_to("2997"))

        self.cleanup(vlan("VLAN2995"), vlan("VLAN2996"), vlan("VLAN2997"),
                     reset_interface("xe-0/0/3"))
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"bridge-domains": {}}}
        }))
        assert_that(result.xpath("data/configuration/bridge-domains/domain"), has_length(0))

    def test_display_interface_with_description_and_trunk_native_vlan(self):
        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
                {"domain": [
                    {"name": "VLAN2996"},
                    {"vlan-id": "2996"}]},
                {"domain": [
                    {"name": "VLAN2997"},
                    {"vlan-id": "2997"}]},
            ],
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"description": "I see what you did there!"},
                    {"native-vlan-id": "2996"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": [
                                {"interface-mode": "trunk"},
                                {"vlan-id-list": "2995"},
                                {"vlan-id-list": "2997"}
                            ]}}]}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int003 = result.xpath("data/configuration/interfaces/interface")[0]
        assert_that(int003.xpath("name")[0].text, equal_to("xe-0/0/3"))
        assert_that(int003.xpath("native-vlan-id")[0].text, equal_to("2996"))
        assert_that(int003.xpath("description")[0].text, equal_to("I see what you did there!"))

        assert_that(int003.xpath("unit/family/bridge/vlan-id-list")), has_length(2)

        members = int003.xpath("unit/family/bridge/vlan-id-list")
        assert_that(members[0].text, equal_to("2995"))
        assert_that(members[1].text, equal_to("2997"))

        self.cleanup(vlan("VLAN2995"), vlan("VLAN2996"), vlan("VLAN2997"),
                     reset_interface("xe-0/0/3"))
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"bridge-domains": {}}}
        }))
        assert_that(result.xpath("data/configuration/bridge-domains/domain"), has_length(0))

    def test_display_interface_trunk_native_vlan_and_no_ethernet_switching(self):
        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/3"},
                    {"native-vlan-id": "2996"}
                ]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/3"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int003 = result.xpath("data/configuration/interfaces/interface")[0]
        assert_that(int003.xpath("name")[0].text, equal_to("xe-0/0/3"))
        assert_that(int003.xpath("native-vlan-id")[0].text, equal_to("2996"))

        self.cleanup(reset_interface("xe-0/0/3"))

    def test_set_interface_description(self):
        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/2"},
                    {"description": "Hey there beautiful"}]}})

        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/2"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int002 = result.xpath("data/configuration/interfaces/interface")[0]

        assert_that(int002.xpath("name")[0].text, equal_to("xe-0/0/2"))
        assert_that(int002.xpath("description")[0].text, equal_to("Hey there beautiful"))

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/2"},
                    {"description": {XML_ATTRIBUTES: {"operation": "delete"}}}]}})

        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/2"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(0))

    def test_set_interface_disabling(self):
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/2"}}}}}))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(0))

        self.edit({"interfaces": {"interface": [{"name": "xe-0/0/2"}, {"disable": ""}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/2"}}}}}))

        int002 = result.xpath("data/configuration/interfaces/interface")[0]
        assert_that(int002.xpath("disable"), has_length(1))

        self.edit({"interfaces": {
            "interface": [{"name": "xe-0/0/2"}, {"disable": {XML_ATTRIBUTES: {"operation": "delete"}}}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/2"}}}}}))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(0))

    def test_set_interface_trunk_native_vlan_id(self):
        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/2"},
                    {"native-vlan-id": "2996"}]}})

        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/2"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int002 = result.xpath("data/configuration/interfaces/interface")[0]

        assert_that(int002.xpath("name")[0].text, equal_to("xe-0/0/2"))
        assert_that(int002.xpath("native-vlan-id")[0].text, equal_to("2996"))

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "xe-0/0/2"},
                    {"native-vlan-id": {XML_ATTRIBUTES: {"operation": "delete"}}}]}})

        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "xe-0/0/2"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(0))

        self.cleanup(reset_interface("xe-0/0/2"))

    def test_set_interface_raises_on_aggregated_out_of_range_port(self):
        with self.assertRaises(RPCError) as exc:
            self.edit({
                "interfaces": {
                    "interface": [
                        {"name": "ae9000"},
                        {"aggregated-ether-options": {
                            "link-speed": "10g"}}
                    ]}})
        assert_that(str(exc.exception), contains_string("device value outside range 0..4091 for '9000' in 'ae9000'"))

    def test_create_aggregated_port(self):
        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "ae1"},
                    {"description": "This is a Greg hated"}]}})
        self.nc.commit()

        ae1 = self.get_interface("ae1")
        assert_that(ae1.xpath("*"), has_length(2))
        assert_that(ae1.xpath("description")[0].text, is_("This is a Greg hated"))

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "ae1"},
                    {"description": {XML_ATTRIBUTES: {"operation": "delete"}}},
                    {"aggregated-ether-options": {
                        "link-speed": "10g",
                        "lacp": {
                            "active": {},
                            "periodic": "slow"}}}]}})
        self.nc.commit()

        ae1 = self.get_interface("ae1")
        assert_that(ae1.xpath("*"), has_length(2))
        assert_that(ae1.xpath("aggregated-ether-options/*"), has_length(2))
        assert_that(ae1.xpath("aggregated-ether-options/link-speed")[0].text, is_("10g"))
        assert_that(ae1.xpath("aggregated-ether-options/lacp/*"), has_length(2))
        assert_that(ae1.xpath("aggregated-ether-options/lacp/active"), has_length(1))
        assert_that(ae1.xpath("aggregated-ether-options/lacp/periodic")[0].text, is_("slow"))

        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
                {"domain": [
                    {"name": "VLAN2997"},
                    {"vlan-id": "2997"}]},
            ],
            "interfaces": {
                "interface": [
                    {"name": "ae1"},
                    {"aggregated-ether-options": {
                        "link-speed": {XML_ATTRIBUTES: {"operation": "delete"}},
                        "lacp": {
                            "active": {XML_ATTRIBUTES: {"operation": "delete"}},
                            "periodic": "slow"}}},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": [
                                {"interface-mode": "trunk"},
                                {"vlan-id-list": "2995"},
                                {"vlan-id-list": "2997"}
                            ]}}]}]}})
        self.nc.commit()

        ae1 = self.get_interface("ae1")
        assert_that(ae1.xpath("*"), has_length(3))
        assert_that(ae1.xpath("aggregated-ether-options/*"), has_length(1))
        assert_that(ae1.xpath("aggregated-ether-options/lacp/periodic")[0].text, is_("slow"))
        assert_that(ae1.xpath("unit/family/bridge/vlan-id-list"), has_length(2))

        self.cleanup(vlan("VLAN2995"), vlan("VLAN2997"), reset_interface("ae1"))

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "ae1"}}}}}))

        assert_that(result.xpath("configuration/interfaces"), has_length(0))

    def test_assign_port_to_aggregated_interface(self):
        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
            ],
            "interfaces": [
                {"interface": [
                    {"name": "xe-0/0/1"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "access",
                                "vlan-id": "2995"
                            }}}]}]},
                {"interface": [
                    {"name": "xe-0/0/2"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "access",
                                "vlan-id": "2995"}}}]}]},
            ]})
        self.nc.commit()

        self.edit({
            "interfaces": [
                {"interface": [
                    {"name": "ae1"},
                    {"aggregated-ether-options": {
                        "link-speed": "10g",
                        "lacp": {
                            "active": {},
                            "periodic": "slow"}}},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "trunk",
                                "vlan-id-list": "2995"}}}]}]},
                {"interface": [
                    {"name": "xe-0/0/1"},
                    {"gigether-options": {
                        "auto-negotiation": {},
                        "ieee-802.3ad": {"bundle": "ae1"}}},
                    {"unit": {XML_ATTRIBUTES: {"operation": "delete"}}}]},
                {"interface": [{XML_ATTRIBUTES: {"operation": "replace"}},
                               {"name": "xe-0/0/2"},
                               {"gigether-options": {
                                   "ieee-802.3ad": {"bundle": "ae1"}}}]},
            ]})
        self.nc.commit()

        ge001 = self.get_interface("xe-0/0/1")
        assert_that(ge001.xpath("*"), has_length(2))
        assert_that(ge001.xpath("unit"), has_length(0))
        assert_that(ge001.xpath("gigether-options/*"), has_length(2))
        assert_that(ge001.xpath("gigether-options/auto-negotiation"), has_length(1))
        assert_that(ge001.xpath("gigether-options/ieee-802.3ad/bundle")[0].text, is_("ae1"))

        ge002 = self.get_interface("xe-0/0/2")
        assert_that(ge002.xpath("*"), has_length(2))
        assert_that(ge002.xpath("unit"), has_length(0))
        assert_that(ge002.xpath("gigether-options/*"), has_length(1))
        assert_that(ge002.xpath("gigether-options/ieee-802.3ad/bundle")[0].text, is_("ae1"))

        self.edit({
            "interfaces": [
                {"interface": [
                    {"name": "xe-0/0/1"},
                    {"gigether-options": {
                        "auto-negotiation": {XML_ATTRIBUTES: {"operation": "delete"}},
                        "ieee-802.3ad": {XML_ATTRIBUTES: {"operation": "delete"}}}}]},
                {"interface": [
                    {"name": "xe-0/0/2"},
                    {"gigether-options": {XML_ATTRIBUTES: {"operation": "delete"}}}]},
            ]})
        self.nc.commit()

        ge001 = self.get_interface("xe-0/0/1")
        assert_that(ge001, is_(None))

        ge002 = self.get_interface("xe-0/0/2", )
        assert_that(ge002, is_(None))

        self.cleanup(vlan("VLAN2995"), reset_interface("ae1"), reset_interface("xe-0/0/1"), reset_interface("xe-0/0/2"))

    def test_auto_negotiation_and_no_auto_negotiation_are_mutually_exclusive(self):
        self.edit({
            "interfaces": [
                {"interface": [
                    {"name": "xe-0/0/1"},
                    {"gigether-options": {
                        "auto-negotiation": {}}}]}]})
        self.nc.commit()

        ge001 = self.get_interface("xe-0/0/1")
        assert_that(ge001.xpath("gigether-options/auto-negotiation"), has_length(1))
        assert_that(ge001.xpath("gigether-options/no-auto-negotiation"), has_length(0))

        self.edit({
            "interfaces": [
                {"interface": [
                    {"name": "xe-0/0/1"},
                    {"gigether-options": {
                        "no-auto-negotiation": {}}}]}]})
        self.nc.commit()

        ge001 = self.get_interface("xe-0/0/1")
        assert_that(ge001.xpath("gigether-options/auto-negotiation"), has_length(0))
        assert_that(ge001.xpath("gigether-options/no-auto-negotiation"), has_length(1))

        self.edit({
            "interfaces": [
                {"interface": [
                    {"name": "xe-0/0/1"},
                    {"gigether-options": {
                        "no-auto-negotiation": {XML_ATTRIBUTES: {"operation": "delete"}}}}]}]})
        self.nc.commit()

        assert_that(self.get_interface("xe-0/0/1"), is_(None))

    def test_operational_request_get_interface_information_terse(self):
        self.edit({
            "bridge-domains": [
                {"domain": [
                    {"name": "VLAN1999"},
                    {"vlan-id": "1999"}]},
            ],
            "interfaces": [
                {"interface": [
                    {XML_ATTRIBUTES: {"operation": "delete"}},
                    {"name": "xe-0/0/1"}]},
                {"interface": [
                    {"name": "xe-0/0/2"},
                    {"description": "my crib"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "access",
                                "vlan-id": "1999"}}}]}]},
                {"interface": [
                    {"name": "xe-0/0/3"},
                    {"description": "bond member"},
                    {"gigether-options": {
                        "ieee-802.3ad": {"bundle": "ae1"}}},
                    {"unit": {XML_ATTRIBUTES: {"operation": "delete"}}}]},
                {"interface": [
                    {"name": "xe-0/0/4"},
                    {"disable": ""}]},
                {"interface": [
                    {"name": "ae3"},
                    {"aggregated-ether-options": {
                        "lacp": {
                            "active": {},
                            "periodic": "slow"}}},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "bridge": {
                                "interface-mode": "trunk",
                                "vlan-id-list": "1999"}}}]}]},
            ]})
        self.nc.commit()

        terse = self.nc.rpc(dict_2_etree({
            "get-interface-information": {
                "terse": {}}}))

        assert_that(terse.xpath("interface-information/physical-interface"), has_length(5)) # 4 physical 1 bonds

        deleted_interface = terse.xpath("interface-information/physical-interface/name[contains(text(),'\nxe-0/0/1\n')]/..")[0]
        assert_that(deleted_interface.xpath("*"), has_length(4))
        assert_that(deleted_interface.xpath("admin-status")[0].text, is_("\nup\n"))
        assert_that(deleted_interface.xpath("oper-status")[0].text, is_("\ndown\n"))
        assert_that(deleted_interface.xpath("logical-interface/*"), has_length(4))
        assert_that(deleted_interface.xpath("logical-interface/name")[0].text, is_("\nxe-0/0/1.16386\n"))
        assert_that(deleted_interface.xpath("logical-interface/admin-status")[0].text, is_("\nup\n"))
        assert_that(deleted_interface.xpath("logical-interface/oper-status")[0].text, is_("\ndown\n"))
        assert_that(deleted_interface.xpath("logical-interface/filter-information"), has_length(1))
        assert_that(deleted_interface.xpath("logical-interface/filter-information/*"), has_length(0))

        access_mode_interface = terse.xpath("interface-information/physical-interface/name[contains(text(),'\nxe-0/0/2\n')]/..")[0]
        assert_that(access_mode_interface.xpath("*"), has_length(5))
        assert_that(access_mode_interface.xpath("admin-status")[0].text, is_("\nup\n"))
        assert_that(access_mode_interface.xpath("oper-status")[0].text, is_("\ndown\n"))
        assert_that(access_mode_interface.xpath("description")[0].text, is_("\nmy crib\n"))
        assert_that(access_mode_interface.xpath("logical-interface/*"), has_length(5))
        assert_that(access_mode_interface.xpath("logical-interface/name")[0].text, is_("\nxe-0/0/2.0\n"))
        assert_that(access_mode_interface.xpath("logical-interface/admin-status")[0].text, is_("\nup\n"))
        assert_that(access_mode_interface.xpath("logical-interface/oper-status")[0].text, is_("\ndown\n"))
        assert_that(access_mode_interface.xpath("logical-interface/filter-information"), has_length(1))
        assert_that(access_mode_interface.xpath("logical-interface/filter-information/*"), has_length(0))
        assert_that(access_mode_interface.xpath("logical-interface/address-family/*"), has_length(1))
        assert_that(access_mode_interface.xpath("logical-interface/address-family/address-family-name")[0].text, is_("\neth-switch\n"))

        bond_member_interface = terse.xpath("interface-information/physical-interface/name[contains(text(),'\nxe-0/0/3\n')]/..")[0]
        assert_that(bond_member_interface.xpath("*"), has_length(4))
        assert_that(bond_member_interface.xpath("admin-status")[0].text, is_("\nup\n"))
        assert_that(bond_member_interface.xpath("oper-status")[0].text, is_("\ndown\n"))
        assert_that(bond_member_interface.xpath("description")[0].text, is_("\nbond member\n"))

        disabled_interface = terse.xpath("interface-information/physical-interface/name[contains(text(),'\nxe-0/0/4\n')]/..")[0]
        assert_that(disabled_interface.xpath("admin-status")[0].text, is_("\ndown\n"))

        active_bond = terse.xpath("interface-information/physical-interface/name[contains(text(),'\nae3\n')]/..")[0]
        assert_that(active_bond.xpath("*"), has_length(4))
        assert_that(active_bond.xpath("admin-status")[0].text, is_("\nup\n"))
        assert_that(active_bond.xpath("oper-status")[0].text, is_("\ndown\n"))
        assert_that(active_bond.xpath("logical-interface/*"), has_length(5))
        assert_that(active_bond.xpath("logical-interface/name")[0].text, is_("\nae3.0\n"))
        assert_that(active_bond.xpath("logical-interface/admin-status")[0].text, is_("\nup\n"))
        assert_that(active_bond.xpath("logical-interface/oper-status")[0].text, is_("\ndown\n"))
        assert_that(active_bond.xpath("logical-interface/filter-information"), has_length(1))
        assert_that(active_bond.xpath("logical-interface/filter-information/*"), has_length(0))
        assert_that(active_bond.xpath("logical-interface/address-family/*"), has_length(1))
        assert_that(active_bond.xpath("logical-interface/address-family/address-family-name")[0].text, is_("\neth-switch\n"))

        self.cleanup(vlan("VLAN1999"),
                     reset_interface("ae1"),
                     reset_interface("ae3"),
                     reset_interface("xe-0/0/1"),
                     reset_interface("xe-0/0/2"),
                     reset_interface("xe-0/0/3"),
                     reset_interface("xe-0/0/4"))

    def test_set_interface_raises_on_physical_interface_with_bad_trailing_input(self):
        with self.assertRaises(RPCError) as exc:
            self.edit({
                "interfaces": {
                    "interface": [
                        {"name": "xe-0/0/43foobar"},
                        {"ether-options": {
                            "auto-negotiation": {}}}
                    ]}})

        assert_that(str(exc.exception), contains_string("invalid trailing input 'foobar' in 'xe-0/0/43foobar'"))

    def test_set_interface_raises_for_physical_interface_for_out_of_range_port(self):
        with self.assertRaises(RPCError) as exc:
            self.edit({
                "interfaces": {
                    "interface": [
                        {"name": "xe-0/0/128"},
                        {"ether-options": {
                            "auto-negotiation": {}}}
                    ]}})

        assert_that(str(exc.exception), contains_string("port value outside range 1..63 for '128' in 'xe-0/0/128'"))

    def test_set_interface_raises_on_aggregated_invalid_interface_type(self):
        with self.assertRaises(RPCError) as exc:
            self.edit({
                "interfaces": {
                    "interface": [
                        {"name": "ae34foobar345"},
                        {"ether-options": {
                            "auto-negotiation": {}}}
                    ]}})

        assert_that(str(exc.exception), contains_string("invalid interface type in 'ae34foobar345'"))

    def test_set_interface_mtu(self):
        self.edit({
            "interfaces": [
                {"interface": [
                    {"name": "xe-0/0/2"},
                    {"mtu": "1000"}]},
                {"interface": [
                    {"name": "ae2"},
                    {"mtu": "1500"}]},
            ]})

        self.nc.commit()

        assert_that(self._interface("xe-0/0/2"), has_xpath("mtu", equal_to("1000")))
        assert_that(self._interface("ae2"), has_xpath("mtu", equal_to("1500")))

        self.edit({
            "interfaces": [
                {"interface": [
                    {"name": "xe-0/0/2"},
                    {"mtu": {XML_ATTRIBUTES: {"operation": "delete"}}}]},
                {"interface": [
                    {"name": "ae2"},
                    {"mtu": {XML_ATTRIBUTES: {"operation": "delete"}}}]}
            ]})

        self.nc.commit()

        assert_that(self._interface("xe-0/0/2"), is_(None))
        assert_that(self._interface("ae2"), is_(None))

    def test_set_interface_mtu_error_messages(self):
        with self.assertRaises(RPCError) as exc:
            self.edit({
                "interfaces": {
                    "interface": [
                        {"name": "xe-0/0/2"},
                        {"mtu": "wat"}]}})

        assert_that(str(exc.exception), contains_string("Invalid numeric value: 'wat'"))

        with self.assertRaises(RPCError) as exc:
            self.edit({
                "interfaces": {
                    "interface": [
                        {"name": "ae2"},
                        {"mtu": "0"}]}})

        assert_that(str(exc.exception), contains_string("Value 0 is not within range (256..16360)"))

    def test_add_a_routing_interface_to_vlan(self):
        self.edit({
            "bridge-domains": {
                "domain": {
                    "name": "VLAN123",
                    "vlan-id": "123",
                    "routing-interface": "irb.123"}}})
        self.nc.commit()

        vlan123 = self._get_vlan("VLAN123")

        assert_that(vlan123.xpath("routing-interface")[0].text, is_("irb.123"))

        self.edit({
            "bridge-domains": {
                "domain": [
                    {"name": "VLAN123"},
                    {"routing-interface": {XML_ATTRIBUTES: {"operation": "delete"}}}]}})
        self.nc.commit()

        vlan123 = self._get_vlan("VLAN123")

        assert_that(vlan123.xpath("routing-interface"), has_length(0))

        self.cleanup(vlan("VLAN123"))

    def test_adding_a_full_interface_vlan_shows_the_vlan_number_on_the_vlan_port(self):
        self.edit({
            "bridge-domains": {
                "domain": {
                    "name": "VLAN100",
                    "vlan-id": "200",
                    "routing-interface": "irb.300"}},
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": {
                                    "name": "3.3.3.2/27"}}}}}}})
        self.nc.commit()

        switch = ThreadedReactor.get_switch("juniper_mx")

        assert_that(switch.switch_configuration.get_port("irb.300").vlan_id, is_(200))

        irb = self._interface("irb")

        assert_that(irb.xpath("unit"), has_length(1))
        assert_that(irb.xpath("unit/name")[0].text, is_("300"))
        assert_that(irb.xpath("unit/family/inet/address/name")[0].text, is_("3.3.3.2/27"))

        self.cleanup(vlan("VLAN100"), reset_interface("irb"))

    def test_adding_the_vlan_after_the_routing_interface_should_still_link_the_vlan_number(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": {
                                    "name": "3.3.3.2/27"}}}}}}})
        self.edit({
            "bridge-domains": {
                "domain": {
                    "name": "VLAN100",
                    "vlan-id": "200",
                    "routing-interface": "irb.300"}}
        })
        self.nc.commit()

        switch = ThreadedReactor.get_switch("juniper_mx")

        assert_that(switch.switch_configuration.get_port("irb.300").vlan_id, is_(200))

        self.cleanup(vlan("VLAN100"), reset_interface("irb"))

    def test_multiple_ip_support(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": [
                                {"address": {"name": "3.3.3.2/27"}},
                                {"address": {"name": "4.4.4.2/27"}},
                            ]}}}}})
        self.nc.commit()

        int_vlan = self._interface_vlan("300")

        assert_that(int_vlan.xpath("family/inet/address"), has_length(2))
        assert_that(int_vlan.xpath("family/inet/address/name")[0].text, is_("3.3.3.2/27"))
        assert_that(int_vlan.xpath("family/inet/address/name")[1].text, is_("4.4.4.2/27"))

        self.cleanup(reset_interface("irb"))

    def test_add_same_ip_in_2_vlans_reports_error(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": [
                                {"address": {"name": "3.3.3.2/27"}},
                            ]}}}}})
        self.nc.commit()
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "400",
                        "family": {
                            "inet": [
                                {"address": {"name": "3.3.3.2/27"}},
                            ]}}}}})
        with self.assertRaises(RPCError) as context:
            self.nc.commit()

        assert_that(context.exception._message, is_("Overlapping subnet is configured"))

        self.cleanup(reset_interface("irb"))

    def test_ip_removal(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": [
                                {"address": {"name": "3.3.3.2/27"}},
                                {"address": {"name": "4.4.4.2/27"}},
                            ]}}}}})
        self.nc.commit()

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": [
                                {"address": {"name": "4.4.4.2/27", XML_ATTRIBUTES: {"operation": "delete"}}},
                            ]}}}}})
        self.nc.commit()

        int_vlan = self._interface_vlan("300")

        assert_that(int_vlan.xpath("family/inet/address"), has_length(1))
        assert_that(int_vlan.xpath("family/inet/address/name")[0].text, is_("3.3.3.2/27"))

        self.cleanup(reset_interface("irb"))

    def test_vrrp_virtual_address(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": [
                                        {"name": "0"},
                                        {"virtual-address": "3.3.3.1"},
                                        {"virtual-address": "3.3.3.3"},
                                    ]},
                                    {"vrrp-group": [
                                        {"name": "1"},
                                        {"virtual-address": "3.3.3.4"},
                                    ]}]}}}}}})
        self.nc.commit()

        int_vlan = self._interface_vlan("300")

        assert_that(int_vlan.xpath("family/inet/address/vrrp-group"), has_length(2))

        vrrp0, vrrp1 = int_vlan.xpath("family/inet/address/vrrp-group")

        assert_that(vrrp0.xpath("name")[0].text, is_("0"))
        assert_that(vrrp0.xpath("virtual-address"), has_length(2))
        assert_that(vrrp0.xpath("virtual-address")[0].text, is_("3.3.3.1"))
        assert_that(vrrp0.xpath("virtual-address")[1].text, is_("3.3.3.3"))

        assert_that(vrrp1.xpath("name")[0].text, is_("1"))
        assert_that(vrrp1.xpath("virtual-address"), has_length(1))
        assert_that(vrrp1.xpath("virtual-address")[0].text, is_("3.3.3.4"))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": {
                                    "name": "3.3.3.2/27",
                                    "vrrp-group": [
                                        {"name": "0"},
                                        {"virtual-address": "3.3.3.1"},
                                        {"virtual-address": {XML_ATTRIBUTES: {"operation": "delete"}}},
                                    ]}}}}}}})
        self.nc.commit()

        int_vlan = self._interface_vlan("300")

        vrrp0 = int_vlan.xpath("family/inet/address/vrrp-group")[0]

        assert_that(vrrp0.xpath("virtual-address"), has_length(1))
        assert_that(vrrp0.xpath("virtual-address")[0].text, is_("3.3.3.1"))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": {
                                    "name": "3.3.3.2/27",
                                    "vrrp-group": {
                                        XML_ATTRIBUTES: {"operation": "delete"},
                                        "name": "0"}}}}}}}})
        self.nc.commit()

        int_vlan = self._interface_vlan("300")

        assert_that(int_vlan.xpath("family/inet/address/vrrp-group"), has_length(1))

        self.cleanup(reset_interface("irb"))

    def test_vrrp_priority(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "priority": "90",
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("priority")[0].text, is_("90"))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "priority": {XML_ATTRIBUTES: {"operation": "delete"}},
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("priority"), has_length(0))

        self.cleanup(reset_interface("irb"))

    def test_vrrp_preempt_hold_time(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "preempt": {"hold-time": "60"},
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("preempt/hold-time")[0].text, is_("60"))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "preempt": {XML_ATTRIBUTES: {"operation": "delete"}},
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("preempt/hold-time"), has_length(0))

        self.cleanup(reset_interface("irb"))

    def test_vrrp_accept_data(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "accept-data": "",
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("accept-data"), has_length(1))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "accept-data": {XML_ATTRIBUTES: {"operation": "delete"}},
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("accept-data"), has_length(0))

        self.cleanup(reset_interface("irb"))

    def test_vrrp_authentication_type(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "authentication-type": "simple",
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("authentication-type")[0].text, is_("simple"))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "authentication-type": {XML_ATTRIBUTES: {"operation": "delete"}},
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("authentication-type"), has_length(0))

        self.cleanup(reset_interface("irb"))

    def test_vrrp_authentication_key(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "authentication-key": "VLAN300",
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("authentication-key")[0].text, is_("this is VLAN300 but hashed"))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "authentication-key": {XML_ATTRIBUTES: {"operation": "delete"}},
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("authentication-key"), has_length(0))

        self.cleanup(reset_interface("irb"))

    def test_track_route(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "track": {
                                            "route": {
                                                "route_address": "0.0.0.0/0",
                                                "routing-instance": "default",
                                                "priority-cost": "50"}},
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("track/route/*"), has_length(3))
        assert_that(vrrp.xpath("track/route/route_address")[0].text, is_("0.0.0.0/0"))
        assert_that(vrrp.xpath("track/route/routing-instance")[0].text, is_("default"))
        assert_that(vrrp.xpath("track/route/priority-cost")[0].text, is_("50"))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "address": [
                                    {"name": "3.3.3.2/27"},
                                    {"vrrp-group": {
                                        "name": "0",
                                        "virtual-address": "3.3.3.1",
                                        "track": {XML_ATTRIBUTES: {"operation": "delete"}},
                                    }}]}}}}}})
        self.nc.commit()

        vrrp = self._vrrp("300", "3.3.3.2/27", "0")

        assert_that(vrrp.xpath("track"), has_length(0))

        self.cleanup(reset_interface("irb"))

    def test_icmp_redirects(self):
        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "no-redirects": {}}}}}}})
        self.nc.commit()

        interface_vlan = self._interface_vlan("300")

        assert_that(interface_vlan.xpath("family/inet/no-redirects"), has_length(1))

        self.edit({
            "interfaces": {
                "interface": {
                    "name": "irb",
                    "unit": {
                        "name": "300",
                        "family": {
                            "inet": {
                                "no-redirects": {XML_ATTRIBUTES: {"operation": "delete"}}}}}}}})
        self.nc.commit()

        interface_vlan = self._interface_vlan("300")

        assert_that(interface_vlan.xpath("family/inet/no-redirects"), has_length(0))

        self.cleanup(reset_interface("irb"))

    def _interface(self, name):
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": name}}}}
        }))

        try:
            return result.xpath("data/configuration/interfaces/interface")[0]
        except IndexError:
            return None

    def _interface_vlan(self, unit):
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {
                "interfaces": {
                    "interface": {
                        "name": "irb",
                        "unit": {"name": unit}}}}}
        }))

        try:
            return result.xpath("data/configuration/interfaces/interface/unit")[0]
        except IndexError:
            return None

    def _vrrp(self, unit, address, group):
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {
                "interfaces": {
                    "interface": {
                        "name": "irb",
                        "unit": {
                            "name": unit,
                            "family": {
                                "inet": {
                                    "address": {
                                        "name": address,
                                        "vrrp-group": {"name": group}}}}}}}}}}))

        try:
            return result.xpath("data/configuration/interfaces/interface/unit/family/inet/address/vrrp-group")[0]
        except IndexError:
            return None

    def _get_vlan(self, name):
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"bridge-domains": {"domain": {"name": name}}}}}))
        return result.xpath("data/configuration/bridge-domains/domain")[0]


def vlan(vlan_name):
    def m(edit):
        edit({"bridge-domains": {
            "domain": {"name": vlan_name, XML_ATTRIBUTES: {"operation": "delete"}}
        }})

    return m
