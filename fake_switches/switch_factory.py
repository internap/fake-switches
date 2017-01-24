from fake_switches.brocade import brocade_core
from fake_switches.cisco import cisco_core
from fake_switches import switch_configuration
from fake_switches.dell import dell_core
from fake_switches.dell10g import dell_core as dell10g_core
from fake_switches.juniper import juniper_core
from fake_switches.juniper_qfx_copper import juniper_qfx_copper_core

DEFAULT_MAPPING = {
    'brocade_generic': brocade_core.BrocadeSwitchCore,
    'cisco_generic': cisco_core.CiscoSwitchCore,
    'cisco_2960_24TT_L': cisco_core.Cisco2960_24TT_L_SwitchCore,
    'cisco_2960_48TT_L': cisco_core.Cisco2960_48TT_L_SwitchCore,
    'dell_generic': dell_core.DellSwitchCore,
    'dell10g_generic': dell10g_core.DellSwitchCore,
    'juniper_generic': juniper_core.JuniperSwitchCore,
    'juniper_qfx_copper_generic': juniper_qfx_copper_core.JuniperQfxCopperSwitchCore,
}


class SwitchFactory(object):
    def __init__(self, mapping=None):
        if mapping is None:
            mapping = DEFAULT_MAPPING
        self.mapping = mapping

    def get(self, switch_model, hostname='switch_hostname', password='root'):
        try:
            core = self.mapping[switch_model]
        except KeyError:
            raise InvalidSwitchModel(switch_model)

        return core(
            switch_configuration.SwitchConfiguration(
                '127.0.0.1',
                name=hostname,
                privileged_passwords=[password],
                ports=core.get_default_ports())
        )


class SwitchFactoryException(Exception):
    pass


class InvalidSwitchModel(SwitchFactoryException):
    pass
