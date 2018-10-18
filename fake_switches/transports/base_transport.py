
class BaseTransport(object):
    def __init__(self, ip=None, port=None, switch_core=None, users=None):
        self.ip = ip
        self.port = port
        self.switch_core = switch_core
        self.users = users

    def hook_to_reactor(self, reactor):
        raise NotImplementedError()
