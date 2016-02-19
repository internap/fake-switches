from fake_switches.netconf import dict_2_etree, XML_TEXT, XML_ATTRIBUTES
from hamcrest import assert_that, has_length, equal_to
from ncclient import manager
from ncclient.operations import RPCError
from tests.juniper.juniper_base_protocol_test import JuniperBaseProtocolTest, vlan, interface

from tests.util.global_reactor import juniper_qfx_copper_switch_ip, \
    juniper_qfx_copper_switch_netconf_port


class JuniperQfxCopperProtocolTest(JuniperBaseProtocolTest):

    def setUp(self):
        super(JuniperQfxCopperProtocolTest, self).setUp()

        self.PORT_MODE_TAG = "interface-mode"

    def create_client(self):
        return manager.connect(
            host=juniper_qfx_copper_switch_ip,
            port=juniper_qfx_copper_switch_netconf_port,
            username="root",
            password="root",
            hostkey_verify=False,
            device_params={'name': 'junos'}
        )

    def test_trunk_mode(self):
        self.edit({
            "vlans": [
                {"vlan": [
                    {"name": "VLAN2995"},
                    {"vlan-id": "2995"}]},
                {"vlan": [
                    {"name": "VLAN2996"},
                    {"vlan-id": "2996"}]},
                {"vlan": [
                    {"name": "VLAN2997"},
                    {"vlan-id": "2997"}]},
            ],
            "interfaces": {
                "interface": [
                    {"name": "ge-0/0/3"},
                    {"native-vlan-id": "2996"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "ethernet-switching": {
                                self.PORT_MODE_TAG: "trunk",
                                "vlan": [
                                    {"members": "2995"},
                                    {"members": "2997"},
                                ]}}}]}]}})
        self.nc.commit()

        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "ge-0/0/3"}}}}
        }))

        assert_that(result.xpath("data/configuration/interfaces/interface"), has_length(1))

        int003 = result.xpath("data/configuration/interfaces/interface")[0]

        assert_that(int003.xpath("name")[0].text, equal_to("ge-0/0/3"))
        assert_that(int003.xpath("native-vlan-id")[0].text, equal_to("2996"))
        assert_that(int003.xpath("unit/family/ethernet-switching/*"), has_length(2))
        assert_that(int003.xpath("unit/family/ethernet-switching/{}".format(self.PORT_MODE_TAG))[0].text,
                    equal_to("trunk"))
        assert_that(int003.xpath("unit/family/ethernet-switching/vlan/members"), has_length(2))
        assert_that(int003.xpath("unit/family/ethernet-switching/vlan/members")[0].text, equal_to("2995"))
        assert_that(int003.xpath("unit/family/ethernet-switching/vlan/members")[1].text, equal_to("2997"))

        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "ge-0/0/3"},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "ethernet-switching": {
                                "vlan": [
                                    {"members": {XML_TEXT: "2995", XML_ATTRIBUTES: {"operation": "delete"}}},
                                ]}}}]}]}})
        self.nc.commit()
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": "ge-0/0/3"}}}}
        }))
        int003 = result.xpath("data/configuration/interfaces/interface")[0]
        assert_that(int003.xpath("unit/family/ethernet-switching/vlan/members"), has_length(1))
        assert_that(int003.xpath("unit/family/ethernet-switching/vlan/members")[0].text, equal_to("2997"))

        self.cleanup(vlan("VLAN2995"), vlan("VLAN2996"), vlan("VLAN2997"),
                     interface("ge-0/0/3", [self.PORT_MODE_TAG, "vlan"]))
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"vlans": {}}}
        }))
        assert_that(result.xpath("data/configuration/vlans/vlan"), has_length(0))

    def test_assigning_unknown_native_vlan_raises(self):
        self.edit({
            "interfaces": {
                "interface": [
                    {"name": "ge-0/0/3"},
                    {"native-vlan-id": "2000"},
                    ]}})

        with self.assertRaises(RPCError):
            self.nc.commit()


def interface(interface_name, fields=None):
    if fields is not None:
        def m(edit):
            edit({"interfaces": {
                "interface": [
                    {"name": interface_name},
                    {"native-vlan-id": {XML_ATTRIBUTES: {"operation": "delete"}}},
                    {"unit": [
                        {"name": "0"},
                        {"family": {
                            "ethernet-switching": {field: {XML_ATTRIBUTES: {"operation": "delete"}} for field in fields}
                        }}]}]}})
    else:
        def m(edit):
            edit({"interfaces": {
                "interface": {
                    "name": interface_name,
                    XML_ATTRIBUTES: {"operation": "delete"}}}})

    return m


def reset_interface(interface_name):
    def m(edit):
        edit({"interfaces": {
            "interface": [{XML_ATTRIBUTES: {"operation": "replace"}},
                          {"name": interface_name},
                          {"native-vlan-id": ""},
                          {"unit": [
                              {"name": "0"},
                              {"family": {
                                  "ethernet-switching": {}}}]}]}})

    return m
