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

from lxml import etree
from fake_switches.netconf import resolve_source_name, Response, NS_BASE_1_0, first


class Capability(object):
    def __init__(self, datastore):
        self.datastore = datastore

    def get_url(self):
        pass


class Base1_0(Capability):
    def get_url(self):
        return NS_BASE_1_0

    def get_config(self, request):
        source = first(request.xpath("source"))
        content = self.datastore.to_etree(resolve_source_name(source[0].tag))
        filtering = first(request.xpath("filter"))
        if filtering is not None:
            filter_content(content, filtering)
        return Response(content)

    def close_session(self, _):
        return Response(etree.Element("ok"), require_disconnect=True)

    def lock(self, request):
        target = first(request.xpath("target"))
        self.datastore.lock(resolve_source_name(target[0].tag))
        return Response(etree.Element("ok"))

    def unlock(self, request):
        target = first(request.xpath("target"))
        self.datastore.unlock(resolve_source_name(target[0].tag))
        return Response(etree.Element("ok"))

    def discard_changes(self, _):
        self.datastore.reset()
        return Response(etree.Element("ok"))

    def edit_config(self, request):
        target = first(request.xpath("target"))
        config = first(request.xpath("config"))
        self.datastore.edit(resolve_source_name(target[0].tag), config[0])

        return Response(etree.Element("ok"))

    def commit(self, _):
        self.datastore.commit_candidate()
        return Response(etree.Element("ok"))


def filter_content(content, filtering):
    valid_xpaths = list(crawl_for_leaves(filtering, base="//data"))
    valid_endpoints = []
    valid_endpoints_parents = []
    for xpath in valid_xpaths:
        for node in content.xpath(xpath):
            valid_endpoints.append(node)
            n = node.getparent()
            while n is not None:
                valid_endpoints_parents.append(n)
                n = n.getparent()

    filter_by_valid_nodes(content, valid_endpoints, valid_endpoints_parents)


def crawl_for_leaves(root, base):
    for e in root:
        new_base = "%s/%s" % (base, e.tag)
        if len(e) == 0:
            if e.text:
                yield new_base + "[text()=\"%s\"]/.." % e.text
            else:
                yield new_base
        else:
            for leaf in crawl_for_leaves(e, new_base):
                yield leaf


def filter_by_valid_nodes(content, valid_endpoints, valid_endpoints_parents):
    for e in content:
        if e in valid_endpoints_parents:
            filter_by_valid_nodes(e, valid_endpoints, valid_endpoints_parents)
        elif e not in valid_endpoints:
            content.remove(e)



class Candidate1_0(Capability):
    def get_url(self):
        return "urn:ietf:params:xml:ns:netconf:capability:candidate:1.0"


class ConfirmedCommit1_0(Capability):
    def get_url(self):
        return "urn:ietf:params:xml:ns:netconf:capability:confirmed-commit:1.0"


class Validate1_0(Capability):
    def get_url(self):
        return "urn:ietf:params:xml:ns:netconf:capability:validate:1.0"


class Url1_0(Capability):
    def get_url(self):
        return "urn:ietf:params:xml:ns:netconf:capability:url:1.0?protocol=http,ftp,file"


