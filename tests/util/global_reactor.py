# Copyright 2015-2016 Internap.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading

from fake_switches.switch_factory import SwitchFactory
from fake_switches.transports.http_service import SwitchHttpService
from fake_switches.transports.ssh_service import SwitchSshService
from fake_switches.transports.telnet_service import SwitchTelnetService
from tests.util import _juniper_ports_with_less_ae, _unique_port

COMMIT_DELAY = 1

TEST_SWITCHES = {
    "arista": {
        "model": "arista_generic",
        "hostname": "my_arista",
        "ssh": _unique_port(),
        "http": _unique_port(),
        "extra": {},
    },
    "brocade": {
        "model": "brocade_generic",
        "hostname": "my_switch",
        "ssh": _unique_port(),
        "extra": {
            "password": "Br0cad3"
        },
    },
    "cisco": {
        "model": "cisco_generic",
        "hostname": "my_switch",
        "telnet": _unique_port(),
        "ssh": _unique_port(),
        "extra": {
            "password": "CiSc000"
        },
    },
    "cisco-auto-enabled": {
        "model": "cisco_generic",
        "hostname": "my_switch",
        "telnet": _unique_port(),
        "ssh": _unique_port(),
        "extra": {
            "auto_enabled": True
        },
    },
    "cisco6500": {
        "model": "cisco_6500",
        "hostname": "my_switch",
        "telnet": _unique_port(),
        "ssh": _unique_port(),
        "extra": {},
    },
    "dell": {
        "model": "dell_generic",
        "hostname": "my_switch",
        "telnet": _unique_port(),
        "ssh": _unique_port(),
        "extra": {
            "password": "DeLL10G"
        },
    },
    "dell10g": {
        "model": "dell10g_generic",
        "hostname": "my_switch",
        "telnet": _unique_port(),
        "ssh": _unique_port(),
        "extra": {
            "password": "DeLL"
        },
    },
    "juniper": {
        "model": "juniper_generic",
        "hostname": "ju_ju_ju_juniper",
        "ssh": _unique_port(),
        "extra": {
            "ports": _juniper_ports_with_less_ae()
        },
    },
    "juniper_qfx": {
        "model": "juniper_qfx_copper_generic",
        "hostname": "ju_ju_ju_juniper_qfx_copper",
        "ssh": _unique_port(),
        "extra": {
            "ports": _juniper_ports_with_less_ae()
        },
    },
    "juniper_mx": {
        "model": "juniper_mx_generic",
        "hostname": "super_juniper_mx",
        "ssh": _unique_port(),
        "extra": {},
    },
    "commit-delayed-brocade": {
        "model": "brocade_generic",
        "hostname": "my_switch",
        "ssh": _unique_port(),
        "extra": {
            "commit_delay": COMMIT_DELAY
        },
    },
    "commit-delayed-cisco": {
        "model": "cisco_generic",
        "hostname": "my_switch",
        "ssh": _unique_port(),
        "extra": {
            "commit_delay": COMMIT_DELAY
        },
    },
    "commit-delayed-dell": {
        "model": "dell_generic",
        "hostname": "my_switch",
        "ssh": _unique_port(),
        "extra": {
            "commit_delay": COMMIT_DELAY
        },
    },
    "commit-delayed-dell10g": {
        "model": "dell10g_generic",
        "hostname": "my_switch",
        "ssh": _unique_port(),
        "extra": {
            "commit_delay": COMMIT_DELAY
        },
    },
    "commit-delayed-juniper": {
        "model": "juniper_generic",
        "hostname": "ju_ju_ju_juniper",
        "ssh": _unique_port(),
        "extra": {
            "commit_delay": COMMIT_DELAY
        },
    }
}


class ThreadedReactor(threading.Thread):
    _threaded_reactor = None

    @classmethod
    def start_reactor(cls):
        cls._threaded_reactor = ThreadedReactor()
        cls._threaded_reactor.switches = {}

        switch_factory = SwitchFactory()

        for name, conf in TEST_SWITCHES.items():
            switch_core = switch_factory.get(conf["model"], hostname=conf["hostname"], **conf["extra"] or {})
            if "telnet" in conf:
                SwitchTelnetService("127.0.0.1",
                                    port=conf["telnet"],
                                    switch_core=switch_core,
                                    users={'root': b'root'}
                                    ).hook_to_reactor(cls._threaded_reactor.reactor)
            if "ssh" in conf:
                SwitchSshService("127.0.0.1",
                                 port=conf["ssh"],
                                 switch_core=switch_core,
                                 users={'root': b'root'}
                                 ).hook_to_reactor(cls._threaded_reactor.reactor)
            if "http" in conf:
                SwitchHttpService("127.0.0.1",
                                  port=conf["http"],
                                  switch_core=switch_core,
                                  users={'root': b'root'}
                                  ).hook_to_reactor(cls._threaded_reactor.reactor)

            cls._threaded_reactor.switches[name] = switch_core

        cls._threaded_reactor.start()

    @classmethod
    def stop_reactor(cls):
        cls._threaded_reactor.stop()

    @classmethod
    def get_switch(cls, name):
        return cls._threaded_reactor.switches[name]

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        from twisted.internet import reactor

        self.reactor = reactor

    def run(self):
        self.reactor.run(installSignalHandlers=False)

    def stop(self):
        self.reactor.callFromThread(self.reactor.stop)


if __name__ == '__main__':
    print('Starting reactor...')
    ThreadedReactor.start_reactor()
