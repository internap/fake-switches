from fake_switches.cisco.cisco_core import BaseCiscoSwitchCore
from fake_switches.cisco.command_processor.config import ConfigCommandProcessor
from fake_switches.cisco.command_processor.config_interface import ConfigInterfaceCommandProcessor
from fake_switches.cisco.command_processor.config_vlan import ConfigVlanCommandProcessor
from fake_switches.cisco.command_processor.config_vrf import ConfigVRFCommandProcessor
from fake_switches.cisco.command_processor.enabled import EnabledCommandProcessor
import fake_switches.switch_configuration as switch_configuration
from fake_switches.switch_configuration import Port


class CiscoN5kSwitchCore(BaseCiscoSwitchCore):
    def __init__(self, switch_configuration):
        """
        @type switch_configuration: switch_configuration.SwitchConfiguration
        @param switch_configuration:
        """
        super(CiscoN5kSwitchCore, self).__init__(switch_configuration)
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "Flexlink", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "amt", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "bgp", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "cts", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "dhcp", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "dot1x", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "eigrp", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "eigrp", "2", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "eigrp", "3", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "eigrp", "4", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "eth_port_sec", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "fcoe", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "fcoe-npv", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "fex", "1", "enabled "))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "glbp", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "hsrp_engine", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "http-server", "1", "enabled "))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "interface-vlan", "1", "enabled "))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "lacp", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "ldap", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "lldp", "1", "enabled "))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "msdp", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "ospf", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "ospf", "2", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "ospf", "3", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "ospf", "4", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "pim", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "poe", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "private-vlan", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "privilege", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "ptp", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "rip", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "rip", "2", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "rip", "3", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "rip", "4", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "sshServer", "1", "enabled "))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "tacacs", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "telnetServer", "1", "enabled "))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "udld", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "vem", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "vmfex", "1", "disabled"))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "vpc", "1", "enabled "))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "vrrp", "1", "enabled "))
        switch_configuration.add_switch_feature(switch_configuration.new("Feature", "vtp", "1", "disabled"))

    @staticmethod
    def get_default_ports():
        port_list = [Port("Eth1/{}".format(x)) for x in xrange(1, 33)]
        return port_list

    def new_command_processor(self):
        return EnabledCommandProcessor(
            config=ConfigCommandProcessor(
                config_vlan=ConfigVlanCommandProcessor(),
                config_vrf=ConfigVRFCommandProcessor(),
                config_interface=ConfigInterfaceCommandProcessor()
            )
        )
