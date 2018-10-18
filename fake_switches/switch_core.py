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


class SwitchCore(object):
    def __init__(self, switch_configuration):
        self.switch_configuration = switch_configuration

    def launch(self, protocol, terminal_controller):
        raise NotImplementedError()

    @staticmethod
    def get_default_ports():
        raise NotImplementedError()

    def get_netconf_protocol(self):
        raise NotImplementedError()

    def get_http_resource(self):
        raise NotImplementedError()
