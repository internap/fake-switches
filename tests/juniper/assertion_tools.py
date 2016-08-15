from hamcrest import assert_that, not_, is_
from hamcrest import has_length
from hamcrest.core.base_matcher import BaseMatcher


def has_xpath(xpath, matcher):
    return XPathMatcher(xpath, matcher)


class XPathMatcher(BaseMatcher):
    def __init__(self, xpath, matcher):
        self.xpath = xpath
        self.matcher = matcher

    def _matches(self, other):
        assert_that(other, is_(not_(None)), "Lookup node doesn't exist")
        nodes = other.xpath(self.xpath)
        assert_that(nodes, has_length(1), "Nodes length should be 1 element")
        assert_that(nodes[0].text, self.matcher)
        return True

    def describe_to(self, description):
        pass
