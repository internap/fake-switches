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

from fake_switches.brocade.brocade_core import BrocadeSwitchCore
from fake_switches.cisco.cisco_core import CiscoSwitchCore
from fake_switches.cisco6500.cisco_core import Cisco6500SwitchCore
from fake_switches.dell.dell_core import DellSwitchCore
from fake_switches.dell10g.dell_core import Dell10GSwitchCore
from fake_switches.juniper.juniper_core import JuniperSwitchCore
from fake_switches.juniper_qfx_copper.juniper_qfx_copper_core import JuniperQfxCopperSwitchCore
from fake_switches.ssh_service import SwitchSshService
from fake_switches.switch_configuration import SwitchConfiguration
from fake_switches.telnet_service import SwitchTelnetService

COMMIT_DELAY = 1

cisco_switch_ip = "127.0.0.1"
cisco_switch_telnet_port = 11001
cisco_switch_ssh_port = 11002
cisco_switch_ssh_with_commit_delay_port = 12002
cisco_privileged_password = "CiSc000"
cisco_auto_enabled_switch_telnet_port = 11004
cisco_auto_enabled_switch_ssh_port = 11005
cisco6500_switch_ip = "127.0.0.1"
cisco6500_switch_telnet_port = 11013
cisco6500_switch_ssh_port = 11014
brocade_switch_ip = "127.0.0.1"
brocade_switch_ssh_port = 11006
brocade_privileged_password = 'Br0cad3'
brocade_switch_with_commit_delay_ssh_port = 12006
juniper_switch_ip = "127.0.0.1"
juniper_switch_netconf_port = 11007
juniper_switch_netconf_with_commit_delay_port = 12007
juniper_qfx_copper_switch_ip = "127.0.0.1"
juniper_qfx_copper_switch_netconf_port = 11008
dell_switch_ip = "127.0.0.1"
dell_switch_telnet_port = 11010
dell_switch_ssh_port = 11009
dell_switch_with_commit_delay_ssh_port = 12009
dell_privileged_password = 'DeLL'
dell10g_switch_ip = "127.0.0.1"
dell10g_switch_telnet_port = 11011
dell10g_switch_ssh_port = 11012
dell10g_switch_with_commit_delay_ssh_port = 12012
dell10g_privileged_password = 'DeLL10G'


class ThreadedReactor(threading.Thread):
    _threaded_reactor = None

    @classmethod
    def start_reactor(cls):
        cls._threaded_reactor = ThreadedReactor()

        switch_core = CiscoSwitchCore(
            SwitchConfiguration(cisco_switch_ip, name="my_switch", privileged_passwords=[cisco_privileged_password],
                                ports=CiscoSwitchCore.get_default_ports()))
        SwitchTelnetService(cisco_switch_ip, telnet_port=cisco_switch_telnet_port, switch_core=switch_core,
                            users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)
        SwitchSshService(cisco_switch_ip, ssh_port=cisco_switch_ssh_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        auto_enabled_switch_core = CiscoSwitchCore(
            SwitchConfiguration(cisco_switch_ip, name="my_switch", auto_enabled=True))
        SwitchTelnetService(cisco_switch_ip, telnet_port=cisco_auto_enabled_switch_telnet_port,
                            switch_core=auto_enabled_switch_core, users={'root': b'root'}).hook_to_reactor(
            cls._threaded_reactor.reactor)
        SwitchSshService(cisco_switch_ip, ssh_port=cisco_auto_enabled_switch_ssh_port,
                         switch_core=auto_enabled_switch_core, users={'root': b'root'}).hook_to_reactor(
            cls._threaded_reactor.reactor)

        switch_core = Cisco6500SwitchCore(
            SwitchConfiguration(cisco6500_switch_ip, name="my_switch", privileged_passwords=[cisco_privileged_password],
                                ports=Cisco6500SwitchCore.get_default_ports()))
        SwitchTelnetService(cisco6500_switch_ip, telnet_port=cisco6500_switch_telnet_port, switch_core=switch_core,
                            users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)
        SwitchSshService(cisco6500_switch_ip, ssh_port=cisco6500_switch_ssh_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = BrocadeSwitchCore(
            SwitchConfiguration(brocade_switch_ip, name="my_switch", privileged_passwords=[brocade_privileged_password],
                                ports=BrocadeSwitchCore.get_default_ports()))
        SwitchSshService(brocade_switch_ip, ssh_port=brocade_switch_ssh_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = JuniperSwitchCore(SwitchConfiguration(juniper_switch_ip, name="ju_ju_ju_juniper",
                                ports=JuniperSwitchCore.get_default_ports()),
            aggregated_port_count=4)
        SwitchSshService(juniper_switch_ip, ssh_port=juniper_switch_netconf_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = JuniperQfxCopperSwitchCore(
            SwitchConfiguration(juniper_qfx_copper_switch_ip, name="ju_ju_ju_juniper_qfx_copper",
                                ports=JuniperQfxCopperSwitchCore.get_default_ports()),
            aggregated_port_count=4)
        SwitchSshService(juniper_qfx_copper_switch_ip, ssh_port=juniper_qfx_copper_switch_netconf_port,
                         switch_core=switch_core, users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = DellSwitchCore(
            SwitchConfiguration(dell_switch_ip, name="my_switch", privileged_passwords=[dell_privileged_password],
                                ports=DellSwitchCore.get_default_ports()))
        SwitchTelnetService(dell_switch_ip, telnet_port=dell_switch_telnet_port, switch_core=switch_core,
                            users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)
        SwitchSshService(dell_switch_ip, ssh_port=dell_switch_ssh_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = Dell10GSwitchCore(
            SwitchConfiguration(dell10g_switch_ip, name="my_switch", privileged_passwords=[dell10g_privileged_password],
                                ports=Dell10GSwitchCore.get_default_ports()))
        SwitchTelnetService(dell10g_switch_ip, telnet_port=dell10g_switch_telnet_port, switch_core=switch_core,
                            users={'root': 'root'}).hook_to_reactor(cls._threaded_reactor.reactor)
        SwitchSshService(dell10g_switch_ip, ssh_port=dell10g_switch_ssh_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        # SWITCHES WITH COMMIT DELAYS

        switch_core = CiscoSwitchCore(
            SwitchConfiguration(cisco_switch_ip, name="my_switch", privileged_passwords=[cisco_privileged_password],
                                ports=CiscoSwitchCore.get_default_ports(), commit_delay=COMMIT_DELAY))
        SwitchSshService(cisco_switch_ip, ssh_port=cisco_switch_ssh_with_commit_delay_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = BrocadeSwitchCore(
            SwitchConfiguration(brocade_switch_ip, name="my_switch", privileged_passwords=[brocade_privileged_password],
                                ports=BrocadeSwitchCore.get_default_ports(), commit_delay=COMMIT_DELAY))
        SwitchSshService(brocade_switch_ip, ssh_port=brocade_switch_with_commit_delay_ssh_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = JuniperSwitchCore(SwitchConfiguration(juniper_switch_ip, name="ju_ju_ju_juniper",
                                ports=JuniperSwitchCore.get_default_ports(),
                                commit_delay=COMMIT_DELAY))
        SwitchSshService(juniper_switch_ip, ssh_port=juniper_switch_netconf_with_commit_delay_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = DellSwitchCore(
            SwitchConfiguration(dell_switch_ip, name="my_switch", privileged_passwords=[dell_privileged_password],
                                ports=DellSwitchCore.get_default_ports(), commit_delay=COMMIT_DELAY))
        SwitchSshService(dell_switch_ip, ssh_port=dell_switch_with_commit_delay_ssh_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

        switch_core = Dell10GSwitchCore(
            SwitchConfiguration(dell10g_switch_ip, name="my_switch", privileged_passwords=[dell10g_privileged_password],
                                ports=Dell10GSwitchCore.get_default_ports(), commit_delay=COMMIT_DELAY))
        SwitchSshService(dell10g_switch_ip, ssh_port=dell10g_switch_with_commit_delay_ssh_port, switch_core=switch_core,
                         users={'root': b'root'}).hook_to_reactor(cls._threaded_reactor.reactor)

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
    print('Starting reactor...')
    ThreadedReactor.start_reactor()
