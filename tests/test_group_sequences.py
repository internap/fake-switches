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
