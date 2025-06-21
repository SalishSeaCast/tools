# Copyright 2013 – present by the SalishSeaCast contributors
# and The University of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for evaltools module."""


import datetime

import numpy
import pandas
import pytest

from salishsea_tools.evaltools import datetimeToYD


class TestDatetimeToYD:
    """Unit tests for the datetimeToYD() function."""

    def test_single_datetime_object(self):
        result = datetimeToYD(datetime.datetime(2025, 1, 1))
        assert result == 1

    @pytest.mark.parametrize(
        "input_date, expected_yd",
        [
            (datetime.datetime(2025, 1, 1), 1),
            (datetime.datetime(2025, 12, 31), 365),
            (datetime.datetime(2024, 2, 29), 60),  # Leap year
        ],
    )
    def test_parametrized_datetime_cases(self, input_date, expected_yd):
        result = datetimeToYD(input_date)
        assert result == expected_yd

    def test_pandas_datetime_series(self):
        dates = pandas.Series(
            [
                datetime.datetime(2025, 1, 1),
                datetime.datetime(2025, 6, 1),
                datetime.datetime(2025, 12, 31),
            ]
        )
        result = datetimeToYD(dates)
        assert result == [1, 152, 365]

    def test_datetime_array(self):
        dates = numpy.array(
            [
                datetime.datetime(2025, 1, 1),
                datetime.datetime(2025, 6, 1),
                datetime.datetime(2025, 12, 31),
            ]
        )
        result = datetimeToYD(dates)
        assert result == [1, 152, 365]
