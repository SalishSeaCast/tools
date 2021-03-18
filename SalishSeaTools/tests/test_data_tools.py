# Copyright 2013-2021 The Salish Sea NEMO Project and
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
import logging

import arrow
import pytest

from salishsea_tools import data_tools


class TestOncDatetime:
    """Unit tests for onc_datetime function."""

    @pytest.mark.parametrize(
        "date_time",
        [
            "2016-06-27 16:49:42",
            datetime(2016, 6, 27, 16, 49, 42),
            arrow.get("2016-06-27 16:49:42"),
        ],
    )
    def test_onc_datetime_str(self, date_time):
        result = data_tools.onc_datetime(date_time)
        assert result == "2016-06-27T23:49:42.000Z"

    @pytest.mark.parametrize(
        "date_time, timezone",
        [
            ("2016-06-27 23:49:42", "utc"),
            (datetime(2016, 6, 27, 23, 49, 42), "utc"),
            (arrow.get("2016-06-27 23:49:42"), "utc"),
            ("2016-06-27 19:49:42", "Canada/Eastern"),
            (datetime(2016, 6, 28, 11, 49, 42), "Pacific/Auckland"),
            (arrow.get("2016-06-27 21:19:42"), "Canada/Newfoundland"),
        ],
    )
    def test_onc_datetime_timzone(self, date_time, timezone):
        result = data_tools.onc_datetime(date_time, timezone)
        assert result == "2016-06-27T23:49:42.000Z"


class TestResolveCHSTideStn:
    """Unit tests for resolve_chs_tide_stn() function."""

    def test_stn_number(self):
        stn_code = data_tools.resolve_chs_tide_stn(8074)

        assert stn_code == "08074"

    def test_stn_name(self):
        stn_code = data_tools.resolve_chs_tide_stn("Campbell River")

        assert stn_code == "08074"

    def test_stn_name_not_found(self, caplog):
        caplog.set_level(logging.DEBUG)

        stn_code = data_tools.resolve_chs_tide_stn("Rimouski")

        assert caplog.records[0].levelname == "ERROR"
        expected = "station name not found in places.PLACES: Rimouski; maybe try an integer station number?"
        assert caplog.messages[0] == expected
        assert stn_code is None


class TestGetCHSTideStnId:
    """Unit tests for get_chs_tide_stn_id() function."""

    def test_stn_name_not_found(self, caplog):
        caplog.set_level(logging.DEBUG)

        stn_id = data_tools.get_chs_tide_stn_id("Rimouski")

        assert caplog.records[0].levelname == "ERROR"
        expected = "station name not found in places.PLACES: Rimouski; maybe try an integer station number?"
        assert caplog.messages[0] == expected
        assert stn_id is None

    def test_get_chs_tide_stn_id(self):
        stn_id = data_tools.get_chs_tide_stn_id(8074)

        assert stn_id == "5cebf1de3d0f4a073c4bb996"
