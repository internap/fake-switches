# Copyright 2017 Internap.
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
from ncclient import manager

from tests.juniper import BaseJuniper
from tests.util.global_reactor import juniper_ex3300_switch_ip, juniper_ex3300_switch_netconf_port


class JuniperEx3300ProtocolTest(BaseJuniper):

    def create_client(self):
        return manager.connect(
            host=juniper_ex3300_switch_ip,
            port=juniper_ex3300_switch_netconf_port,
            username="root",
            password="root",
            hostkey_verify=False,
            device_params={'name': 'junos'}
        )

    def test_