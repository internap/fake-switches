from fake_switches.cisco.cisco_core import BaseCiscoSwitchCore
from fake_switches.cisco.command_processor.config import ConfigCommandProcessor
from fake_switches.cisco.command_processor.config_interface import ConfigInterfaceCommandProcessor
from fake_switches.cisco.command_processor.config_vlan import ConfigVlanCommandProcessor
from fake_switches.cisco.command_processor.config_vrf import ConfigVRFCommandProcessor
from fake_switches.cisco.command_processor.enabled import EnabledCommandProcessor


class Cisco6500SwitchCore(BaseCiscoSwitchCore):
    def new_command_processor(self):
        return EnabledCommandProcessor(
            config=ConfigCommandProcessor(
                config_vlan=ConfigVlanCommandProcessor(),
                config_vrf=ConfigVRFCommandProcessor(),
                config_interface=Cisco6500ConfigInterfaceCommandProcessor()
            )
        )


class Cisco6500ConfigInterfaceCommandProcessor(ConfigInterfaceCommandProcessor):
    def _handle_ip_verify_unicast(self):
        self.port.unicast_reverse_path_forwarding = True
