# Copyright 2015-2018 Internap.
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

from fake_switches.juniper.juniper_core import BaseJuniperSwitchCore, NetconfJunos1_0, DmiSystem1_0
from fake_switches.juniper_mx.juniper_mx_netconf_datastore import JuniperMxNetconfDatastore
from fake_switches.netconf.capabilities import Candidate1_0, ConfirmedCommit1_0, Validate1_0, Url1_0, \
    NSLessCandidate1_0, NSLessConfirmedCommit1_0, NSLessValidate1_0, NSLessUrl1_0
from fake_switches.switch_configuration import Port


class JuniperMXSwitchCore(BaseJuniperSwitchCore):
    def __init__(self, switch_configuration):
        super(JuniperMXSwitchCore, self).__init__(
            switch_configuration,
            datastore_class=JuniperMxNetconfDatastore)

    def capabilities(self):
        return [
            Candidate1_0,
            ConfirmedCommit1_0,
            Validate1_0,
            Url1_0,
            NSLessCandidate1_0,
            NSLessConfirmedCommit1_0,
            NSLessValidate1_0,
            NSLessUrl1_0,
            NetconfJunos1_0,
            DmiSystem1_0
        ]

    @staticmethod
    def get_default_ports():
        return [
            Port("xe-0/0/1"),
            Port("xe-0/0/2"),
            Port("xe-0/0/3"),
            Port("xe-0/0/4")
        ]
