# Copyright 2013-2016 The Salish Sea MEOPAR Contributors
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

"""Unit tests for the unit_conversions module.
"""
from __future__ import division

import arrow
import numpy as np
import pytest

from salishsea_tools import unit_conversions


def test_M_PER_S__KM_PER_HR_constant_value():
    expected = 3600 / 1000
    np.testing.assert_allclose(unit_conversions.M_PER_S__KM_PER_HR, expected)


def test_M_PER_S__KNOTS_constant_value():
    expected = 3600 / 1852
    np.testing.assert_allclose(unit_conversions.M_PER_S__KNOTS, expected)


def test_KNOTS__M_PER_S_constant_value():
    expected = 1852 / 3600
    np.testing.assert_allclose(unit_conversions.KNOTS__M_PER_S, expected)


@pytest.mark.parametrize('m_per_s, expected', [
    (0, 0),
    (1, 3.6),
])
def test_mps_kph(m_per_s, expected):
    np.testing.assert_allclose(
        unit_conversions.mps_kph(m_per_s), expected)


def test_mps_kph_ndarray():
    kph = unit_conversions.mps_kph(np.array([0, 1]))
    np.testing.assert_allclose(kph, np.array([0, 3.6]))


@pytest.mark.parametrize('m_per_s, expected', [
    (0, 0),
    (1, 1.94384),
])
def test_mps_knots(m_per_s, expected):
    np.testing.assert_allclose(
        unit_conversions.mps_knots(m_per_s), expected, rtol=1e-05)


def test_mps_knots_ndarray():
    knots = unit_conversions.mps_knots(np.array([0, 1]))
    np.testing.assert_allclose(knots, np.array([0, 1.94384]), rtol=1e-05)


@pytest.mark.parametrize('knots, expected', [
    (0, 0),
    (1, 0.514444),
])
def test_knots_mps(knots, expected):
    np.testing.assert_allclose(
        unit_conversions.knots_mps(knots), expected, rtol=1e-05)


def test_knots_mps_ndarray():
    knots = unit_conversions.knots_mps(np.array([0, 1]))
    np.testing.assert_allclose(knots, np.array([0, 0.514444]), rtol=1e-05)


@pytest.mark.parametrize('wind_to, expected', [
    (0, 270),
    (90, 180),
    (180, 90),
    (270, 0),
    (359, 271),
])
def test_wind_to_from(wind_to, expected):
    np.testing.assert_allclose(
        unit_conversions.wind_to_from(wind_to), expected)


def test_wind_to_from_ndarray():
    wind_from = unit_conversions.wind_to_from(
        np.array([0, 90, 180, 270, 359]))
    np.testing.assert_allclose(wind_from, np.array([270, 180, 90, 0, 271]))


class TestBearingHeading(object):
    """Unit tests for bearing_heading() function.
    """
    @pytest.mark.parametrize('bearing, expected', [
        (0, 'N'),
        (27, 'NNE'),
        (359, 'N'),
    ])
    def test_default_16_points(self, bearing, expected):
        heading = unit_conversions.bearing_heading(bearing)
        assert heading == expected

    @pytest.mark.parametrize('bearing, expected', [
        (0, 'N'),
        (27, 'NE'),
        (359, 'N'),
    ])
    def test_8_points(self, bearing, expected):
        heading = unit_conversions.bearing_heading(
            bearing,
            headings=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'])
        assert heading == expected


class TestHumanizeTimeOfDay(object):
    """Unit tests for humanize_time_of_day() function.
    """
    @pytest.mark.parametrize('date_time, expected', [
        (arrow.get('2015-12-26 00:00:00'), 'overnight Saturday'),
        (arrow.get('2015-12-26 02:15:42'), 'overnight Saturday'),
        (arrow.get('2015-12-26 05:59:59'), 'overnight Saturday'),
        (arrow.get('2015-12-26 06:00:00'), 'early Saturday morning'),
        (arrow.get('2015-12-26 07:22:51'), 'early Saturday morning'),
        (arrow.get('2015-12-26 08:59:59'), 'early Saturday morning'),
        (arrow.get('2015-12-26 09:00:00'), 'late Saturday morning'),
        (arrow.get('2015-12-26 09:52:43'), 'late Saturday morning'),
        (arrow.get('2015-12-26 11:59:59'), 'late Saturday morning'),
        (arrow.get('2015-12-25 12:00:00'), 'early Friday afternoon'),
        (arrow.get('2015-12-25 13:36:11'), 'early Friday afternoon'),
        (arrow.get('2015-12-25 14:59:59'), 'early Friday afternoon'),
        (arrow.get('2015-12-25 15:00:00'), 'late Friday afternoon'),
        (arrow.get('2015-12-25 16:09:21'), 'late Friday afternoon'),
        (arrow.get('2015-12-25 17:59:59'), 'late Friday afternoon'),
        (arrow.get('2015-12-27 18:00:00'), 'early Sunday evening'),
        (arrow.get('2015-12-27 18:01:56'), 'early Sunday evening'),
        (arrow.get('2015-12-27 20:59:59'), 'early Sunday evening'),
        (arrow.get('2015-12-27 21:00:00'), 'late Sunday evening'),
        (arrow.get('2015-12-27 23:43:43'), 'late Sunday evening'),
        (arrow.get('2015-12-27 23:59:59'), 'late Sunday evening'),
    ])
    def test_humanize_time_of_day(self, date_time, expected):
        result = unit_conversions.humanize_time_of_day(date_time)
        assert result == expected
