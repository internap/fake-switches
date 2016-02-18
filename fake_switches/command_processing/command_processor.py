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


class CommandProcessor(object):

    def get_command_func(self, line):
        if line.startswith("!"):
            return (lambda: None), []
        else:
            line_split = line.strip().split()
            command = line_split[0]
            args = line_split[1:]

            if command == "no":
                command += "_" + args.pop(0)

            command = re.sub('[-]', "_", command)

            matching = sorted([c for c in dir(self) if c.startswith('do_' + command)])
            if len(matching) >= 1:
                return getattr(self, matching[0], None), args

        return None, []
