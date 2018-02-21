# Copyright 2016 Internap.
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

from time import time

from fake_switches.netconf import dict_2_etree, XML_ATTRIBUTES
from hamcrest import assert_that, has_length, greater_than
from tests.juniper import BaseJuniper
from tests.util.global_reactor import COMMIT_DELAY


class JuniperBaseProtocolWithCommitDelayTest(BaseJuniper):
    test_switch = "commit-delayed-juniper"

    def test_lock_edit_candidate_add_vlan_and_commit_with_commit_delay(self):
        with self.nc.locked(target='candidate'):
            result = self.nc.edit_config(target='candidate', config=dict_2_etree({
                "config": {
                    "configuration": {
                        "vlans": {
                            "vlan": {
                                "name": "VLAN2999",
                                }
                        }
                    }
                }}))
            assert_that(result.xpath("//rpc-reply/ok"), has_length(1))

            result = self.nc.commit()
            assert_that(result.xpath("//rpc-reply/ok"), has_length(1))

        result = self.nc.get_config(source="running")

        assert_that(result.xpath("data/configuration/vlans/vlan"), has_length(1))

        self.edit({
            "vlans": {
                "vlan": {
                    XML_ATTRIBUTES: {"operation": "delete"},
                    "name": "VLAN2999"
                }
            }
        })

        start_time = time()
        self.nc.commit()
        end_time = time()

        result = self.nc.get_config(source="running")

        assert_that(result.xpath("data/configuration/vlans/vlan"), has_length(0))
        assert_that((end_time - start_time), greater_than(COMMIT_DELAY))

    def edit(self, config):
        result = self.nc.edit_config(target="candidate", config=dict_2_etree({
            "config": {
                "configuration": config
            }
        }))

        assert_that(result.xpath("//rpc-reply/ok"), has_length(1))
