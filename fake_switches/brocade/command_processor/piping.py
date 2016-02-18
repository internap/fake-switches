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

from fake_switches.command_processing.piping_processor_base import PipingProcessorBase, StartOutputAt, Grep


class PipingProcessor(PipingProcessorBase):

    def do_begin(self, *args):
        return StartOutputAt(" ".join(args))

    def do_include(self, *args):
        return Grep(" ".join(args))

