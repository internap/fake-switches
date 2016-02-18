from ncclient import manager
from tests.juniper.juniper_base_protocol_test import JuniperBaseProtocolTest

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
