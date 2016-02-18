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

import unittest
from hamcrest import equal_to, assert_that
from fake_switches import group_sequences


class StuffTest(unittest.TestCase):
    def test_group_sequences_empty(self):
        assert_that(group_sequences([], are_in_sequence=int_sequence),
                    equal_to([]))

    def test_group_sequences_1_value(self):
        assert_that(group_sequences([10], are_in_sequence=int_sequence),
                    equal_to([[10]]))

    def test_group_sequences_2_values_not_consecutive(self):
        assert_that(group_sequences([10, 15], are_in_sequence=int_sequence),
                    equal_to([[10], [15]]))

    def test_group_sequences_2_consecutive_values(self):
        assert_that(group_sequences([10, 11], are_in_sequence=int_sequence),
                    equal_to([[10, 11]]))

    def test_group_sequences_some_values(self):
        assert_that(group_sequences([10, 11, 13, 14, 15, 22], are_in_sequence=int_sequence),
                    equal_to([[10, 11], [13, 14, 15], [22]]))


def int_sequence(a, b):
    return (a + 1) == b
