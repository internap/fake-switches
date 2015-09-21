# Copyright 2015 Internap.
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

from fake_switches.brocade.brocade_core import BrocadeSwitchCore
from fake_switches.cisco.cisco_core import CiscoSwitchCore
from fake_switches.dell.dell_core import DellSwitchCore
from fake_switches.juniper.juniper_core import JuniperSwitchCore
from fake_switches.juniper.juniper_qfx_copper_core import JuniperQfxCopperSwitchCore
from fake_switches.ssh_service import SwitchSshService
from fake_switches.switch_configuration import SwitchConfiguration, Port
from fake_switches.telnet_service import SwitchTelnetService

cisco_switch_ip = "127.0.0.1"
cisco_switch_telnet_port = 11001
cisco_switch_ssh_port = 11002
cisco_privileged_password = "CiSc000"
cisco_auto_enabled_switch_telnet_port = 11004
cisco_auto_enabled_switch_ssh_port = 11005
brocade_switch_ip = "127.0.0.1"
brocade_switch_ssh_port = 11006
brocade_privileged_password = 'Br0cad3'
juniper_switch_ip = "127.0.0.1"
juniper_switch_netconf_port = 11007
juniper_qfx_copper_switch_ip = "127.0.0.1"
juniper_qfx_copper_switch_netconf_port = 11008
dell_switch_ip = "127.0.0.1"
dell_switch_telnet_port = 11010
dell_switch_ssh_port = 11009
dell_privileged_password = 'DeLL'


class ThreadedReactor(threading.Thread):
    _threaded_reactor = None

    @classmethod
    def start_reactor(cls):
        cls._threaded_reactor = ThreadedReactor()

        switch_core = CiscoSwitchCore(
            SwitchConfiguration(cisco_switch_ip, name="my_switch", privileged_passwords=[cisco_privileged_password],
                                ports=[
                                    Port("FastEthernet0/1"),
                                    Port("FastEthernet0/2"),
                                    Port("FastEthernet0/3"),
                                    Port("FastEthernet0/4"),
                                ]))
        SwitchTelnetService(cisco_switch_ip, telnet_port=cisco_switch_telnet_port, switch_core=switch_core,
                            users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)
        SwitchSshService(cisco_switch_ip, ssh_port=cisco_switch_ssh_port, switch_core=switch_core,
                         users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        auto_enabled_switch_core = CiscoSwitchCore(
            SwitchConfiguration(cisco_switch_ip, name="my_switch", auto_enabled=True))
        SwitchTelnetService(cisco_switch_ip, telnet_port=cisco_auto_enabled_switch_telnet_port,
                            switch_core=auto_enabled_switch_core, users={'root': 'root'}).hook_to_reactor(
            cls._threaded_reactor.reactor)
        SwitchSshService(cisco_switch_ip, ssh_port=cisco_auto_enabled_switch_ssh_port,
                         switch_core=auto_enabled_switch_core, users={'root': 'root'}).hook_to_reactor(
            cls._threaded_reactor.reactor)

        switch_core = BrocadeSwitchCore(
            SwitchConfiguration(brocade_switch_ip, name="my_switch", privileged_passwords=[brocade_privileged_password],
                                ports=[
                                    Port("ethernet 1/1"),
                                    Port("ethernet 1/2"),
                                    Port("ethernet 1/3"),
                                    Port("ethernet 1/4")
                                ]))
        SwitchSshService(brocade_switch_ip, ssh_port=brocade_switch_ssh_port, switch_core=switch_core,
                         users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = JuniperSwitchCore(SwitchConfiguration(juniper_switch_ip, name="ju_ju_ju_juniper", ports=[
            Port("ge-0/0/1"),
            Port("ge-0/0/2"),
            Port("ge-0/0/3"),
            Port("ge-0/0/4")
        ]))
        SwitchSshService(juniper_switch_ip, ssh_port=juniper_switch_netconf_port, switch_core=switch_core,
                         users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = JuniperQfxCopperSwitchCore(
            SwitchConfiguration(juniper_qfx_copper_switch_ip, name="ju_ju_ju_juniper_qfx_copper", ports=[
                Port("ge-0/0/1"),
                Port("ge-0/0/2"),
                Port("ge-0/0/3"),
                Port("ge-0/0/4")
            ]))
        SwitchSshService(juniper_qfx_copper_switch_ip, ssh_port=juniper_qfx_copper_switch_netconf_port,
                         switch_core=switch_core, users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = DellSwitchCore(
            SwitchConfiguration(dell_switch_ip, name="my_switch", privileged_passwords=[dell_privileged_password],
                                ports=[
                                    Port("ethernet 1/g1"),
                                    Port("ethernet 1/g2"),
                                    Port("ethernet 2/g1"),
                                    Port("ethernet 2/g2"),
                                    Port("ethernet 1/xg1"),
                                    Port("ethernet 2/xg1")
                                ]))
        SwitchTelnetService(dell_switch_ip, telnet_port=dell_switch_telnet_port, switch_core=switch_core,
                            users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)
        SwitchSshService(dell_switch_ip, ssh_port=dell_switch_ssh_port, switch_core=switch_core,
                         users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        cls._threaded_reactor.start()

    @classmethod
    def stop_reactor(cls):
        cls._threaded_reactor.stop()

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        from twisted.internet import reactor

        self.reactor = reactor

    def run(self):
        self.reactor.run(installSignalHandlers=False)

    def stop(self):
        self.reactor.callFromThread(self.reactor.stop)


if __name__ == '__main__':
    print 'Starting reactor...'
    ThreadedReactor.start_reactor()
