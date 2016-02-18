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
