# Copyright 2013-2016 The Salish Sea MEOPAR contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for SalishSeaTools stormtools module.
"""
from unittest.mock import Mock

import pytest

from salishsea_tools import stormtools


class TestStormSurgeRiskLevel(object):
    """Unit tests for storm_surge_risk_level() function.
    """
    def test_places_key_error(self):
        m_ttide = Mock(name='ttide', pred_all=[42])
        with pytest.raises(KeyError):
            stormtools.storm_surge_risk_level('foo', 42.24, m_ttide)

    @pytest.mark.parametrize('max_ssh, expected', [
        (4.9, None),
        (5.1, 'moderate risk'),
        (5.4, 'extreme risk'),
    ])
    def test_risk_level(self, max_ssh, expected):
        m_ttide = Mock(name='ttide', pred_all=[2])
        risk_level = stormtools.storm_surge_risk_level(
            'Point Atkinson', max_ssh, m_ttide)
        assert risk_level == expected
