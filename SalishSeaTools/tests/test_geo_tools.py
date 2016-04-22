# Copyright 2013-2016 The Salish Sea NEMO Project and
# The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for geo_tools module.
"""

import pytest


@pytest.fixture(scope='module')
def geo_tools_module():
    from salishsea_tools import geo_tools
    return geo_tools


class TestSomeFunction:
    def test_some_function(self, geo_tools_module):
        result = geo_tools_module.some_function()
        assert result == expected

