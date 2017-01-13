
class SwitchCore(object):
    def __init__(self, switch_configuration):
        self.switch_configuration = switch_configuration

    def launch(self, protocol, terminal_controller):
        raise NotImplementedError()

    @staticmethod
    def get_default_ports():
        raise NotImplementedError()
