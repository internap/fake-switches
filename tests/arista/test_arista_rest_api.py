# Copyright 2018 Inap.
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
import unittest

import pyeapi
from hamcrest import assert_that, is_

from tests.util.global_reactor import TEST_SWITCHES


class TestAristaRestApi(unittest.TestCase):
    def test_get_vlan(self):

        conf = TEST_SWITCHES["arista"]
        node = pyeapi.connect(transport="http", host="127.0.0.1", port=conf["http"],
                              username="root", password="root", return_node=True)

        result = node.api('vlans').get(1)

        assert_that(result, is_({
            "name": "default",
            "state": "active",
            "trunk_groups": [],
            "vlan_id": 1
        }))
