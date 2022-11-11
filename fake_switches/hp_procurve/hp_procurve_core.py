from fake_switches.switch_core import SwitchCore
from fake_switches.switch_configuration import Port

class HpProcurveCore(SwitchCore):
       def __init__(self, switch_configuration):
              super(HpProcurveCore, self).__init__(switch_configuration)
              self.switch_configuration.add_vlan(self.switch_configuration.new("Vlan", 1))

              self.logger = None
              self.last_connection_id = 0

       def launch(self, protocol, terminal_controller):
              raise NotImplementedError()

       def get_default_ports():
              return [
                     Port("Ethernet1"),
                     Port("Ethernet2")
              ]

       def get_netconf_protocol(self):
              raise NotImplementedError()

       def get_http_resource(self):
              raise NotImplementedError()