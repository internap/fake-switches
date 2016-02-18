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

from fake_switches.juniper.juniper_core import JuniperSwitchCore
from fake_switches.juniper.juniper_qfx_copper_netconf_datastore import JuniperQfxCopperNetconfDatastore


class JuniperQfxCopperSwitchCore(JuniperSwitchCore):
    def __init__(self, switch_configuration):
        super(JuniperQfxCopperSwitchCore, self).__init__(
            switch_configuration,
            datastore_class=JuniperQfxCopperNetconfDatastore)
