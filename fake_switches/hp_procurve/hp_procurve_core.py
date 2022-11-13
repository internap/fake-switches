import logging
from fake_switches.command_processing.shell_session import ShellSession
from fake_switches.hp_procurve.command_processing.default import DefaultCommandProcessor
from fake_switches.hp_procurve.command_processing.enabled import EnabledCommandProcessor
from fake_switches.hp_procurve.command_processing.nopage import NoPageCommandProcessor
from fake_switches.hp_procurve.command_processing.piping import PipingProcessor

from fake_switches.switch_core import SwitchCore
from fake_switches.switch_configuration import Port
from fake_switches.terminal import LoggingTerminalController


class HpProcurveCore(SwitchCore):
       def __init__(self, switch_configuration):
              super(HpProcurveCore, self).__init__(switch_configuration)
              self.switch_configuration.add_vlan(self.switch_configuration.new("Vlan", 1))

              self.logger = None
              self.last_connection_id = 0

       def launch(self, protocol, terminal_controller):
              self.last_connection_id += 1
              self.logger = logging.getLogger("fake_switches.hp_procurve.{}.{}.{}"
                                        .format(self.switch_configuration.name, self.last_connection_id, protocol))

              command_processor = DefaultCommandProcessor(
                     no_page=NoPageCommandProcessor(
                            enabled=EnabledCommandProcessor()))
                     
              command_processor.init(switch_configuration=self.switch_configuration,
                               terminal_controller=LoggingTerminalController(self.logger, terminal_controller),
                               piping_processor=PipingProcessor(self.logger),
                               logger=self.logger)
              return HpProcurveShellSession(command_processor)

       def get_default_ports():
              return [
                     Port("Ethernet1"),
                     Port("Ethernet2")
              ]

       def get_netconf_protocol(self):
              return None

       def get_http_resource(self):
              raise NotImplementedError()

class HpProcurveShellSession(ShellSession):
    def handle_unknown_command(self, line):
        self.command_processor.terminal_controller.write("Invalid input -> %s\nType ? for a list\n" % line)
