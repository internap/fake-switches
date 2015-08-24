import re
from hamcrest.library.text.substringmatcher import SubstringMatcher
from tests.util.global_reactor import ThreadedReactor


def setup():
    ThreadedReactor.start_reactor()


def tearDown():
    ThreadedReactor.stop_reactor()


class RegexStringContains(SubstringMatcher):

    def __init__(self, regex_substring):
        super(RegexStringContains, self).__init__(regex_substring)

    def _matches(self, item):
        return re.search(self.substring, item) is not None

    def relationship(self):
        return 'containing regex'


def contains_regex(substring):
    """Matches if object is a string containing a given string.

    :param substring: The regex string to search for.
    """
    return RegexStringContains(substring)
