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

"""Uni tests for salishsea_tools.data_tools module.
"""
from datetime import datetime

import arrow
import pytest

from salishsea_tools import data_tools


class TestOncDatetime(object):
    """Unit tests for onc_datetime function.
    """
    @pytest.mark.parametrize('date_time', [
        '2016-06-27 16:49:42',
        datetime(2016, 6, 27, 16, 49, 42),
        arrow.get('2016-06-27 16:49:42'),
    ])
    def test_onc_datetime_str(self, date_time):
        result = data_tools.onc_datetime(date_time)
        assert result == '2016-06-27T23:49:42.000Z'

    @pytest.mark.parametrize('date_time, timezone', [
        ('2016-06-27 23:49:42', 'utc'),
        (datetime(2016, 6, 27, 23, 49, 42), 'utc'),
        (arrow.get('2016-06-27 23:49:42'), 'utc'),
        ('2016-06-27 19:49:42', 'Canada/Eastern'),
        (datetime(2016, 6, 28, 11, 49, 42), 'Pacific/Auckland'),
        (arrow.get('2016-06-27 21:19:42'), 'Canada/Newfoundland'),
    ])
    def test_onc_datetime_timzone(self, date_time, timezone):
        result = data_tools.onc_datetime(date_time, timezone)
        assert result == '2016-06-27T23:49:42.000Z'
