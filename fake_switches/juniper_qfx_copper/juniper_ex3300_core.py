from fake_switches.juniper.juniper_core import JuniperSwitchCore


class JuniperEx3300SwitchCore(JuniperSwitchCore):
    def __init__(self, switch_configuration, aggregated_port_count=24):
        super(JuniperEx3300SwitchCore, self).__init__(
            switch_configuration,
            datastore_class=JuniperEx3300SwitchCore,
            aggregated_port_count=aggregated_port_count)
