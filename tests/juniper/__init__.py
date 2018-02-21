import unittest

from fake_switches.netconf import dict_2_etree, XML_ATTRIBUTES
from hamcrest import assert_that, has_length
from ncclient import manager
from tests.util.global_reactor import TEST_SWITCHES


class BaseJuniper(unittest.TestCase):
    test_switch = None

    def setUp(self):
        self.conf = TEST_SWITCHES[self.test_switch]
        self.nc = self.create_client()

    def create_client(self):
        return manager.connect(
            host="127.0.0.1",
            port=self.conf["ssh"],
            username="root",
            password="root",
            hostkey_verify=False,
            device_params={'name': 'junos'}
        )

    def tearDown(self):
        assert_that(self.nc.get_config(source="running").xpath("data/configuration/*"), has_length(0))
        try:
            self.nc.discard_changes()
        finally:
            self.nc.close_session()

    def edit(self, config):
        result = self.nc.edit_config(target="candidate", config=dict_2_etree({
            "config": {
                "configuration": config
            }
        }))
        assert_that(result.xpath("//rpc-reply/ok"), has_length(1))

    def cleanup(self, *args):
        for clean_it in args:
            clean_it(self.edit)
        self.nc.commit()

    def get_interface(self, name):
        result = self.nc.get_config(source="running", filter=dict_2_etree({"filter": {
            "configuration": {"interfaces": {"interface": {"name": name}}}}}))
        if len(result.xpath("data/configuration")) == 0:
            return None
        return result.xpath("data/configuration/interfaces/interface")[0]


def vlan(vlan_name):
    def m(edit):
        edit({"vlans": {
            "vlan": {"name": vlan_name, XML_ATTRIBUTES: {"operation": "delete"}}
        }})

    return m

