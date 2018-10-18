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

import logging

from twisted.web.server import Site

from fake_switches.transports.base_transport import BaseTransport


class SwitchHttpService(BaseTransport):
    def __init__(self, ip=None, port=80, switch_core=None, users=None):
        super(SwitchHttpService, self).__init__(ip, port, switch_core, users)

    def hook_to_reactor(self, reactor):
        site = Site(self.switch_core.get_http_resource())

        lport = reactor.listenTCP(port=self.port, factory=site, interface=self.ip)
        logging.info(lport)
        logging.info("{} (HTTP): Registered on {} tcp/{}"
                     .format(self.switch_core.switch_configuration.name, self.ip, self.port))
