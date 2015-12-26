# Copyright 2013-2015 The Salish Sea MEOPAR Contributors
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

import numpy as np
import pytest


@pytest.fixture
def unit_conversions_module():
    from salishsea_tools import unit_conversions
    return unit_conversions


def equal_enough(value, expected, abs_diff=0.00001):
    return abs(value - expected) < abs_diff


def test_M_PER_S__KM_PER_HR_constant_value(unit_conversions_module):
    expected = 3600 / 1000
    assert equal_enough(unit_conversions_module.M_PER_S__KM_PER_HR, expected)


def test_M_PER_S__KNOTS_constant_value(unit_conversions_module):
    expected = 3600 / 1852
    assert equal_enough(unit_conversions_module.M_PER_S__KNOTS, expected)


@pytest.mark.parametrize('m_per_s, expected', [
    (0, 0),
    (1, 3.6),
])
def test_mps_kph(m_per_s, expected, unit_conversions_module):
    assert equal_enough(unit_conversions_module.mps_kph(m_per_s), expected)


def test_mps_kph_ndarray(unit_conversions_module):
    kph = unit_conversions_module.mps_kph(np.array([0, 1]))
    np.testing.assert_allclose(kph, np.array([0, 3.6]))


@pytest.mark.parametrize('m_per_s, expected', [
    (0, 0),
    (1, 1.94384449),
])
def test_mps_knots(m_per_s, expected, unit_conversions_module):
    assert equal_enough(unit_conversions_module.mps_knots(m_per_s), expected)


def test_mps_knots_ndarray(unit_conversions_module):
    knots = unit_conversions_module.mps_knots(np.array([0, 1]))
    np.testing.assert_allclose(knots, np.array([0, 1.94384449]))


@pytest.mark.parametrize('wind_to, expected', [
    (0, 270),
    (90, 180),
    (180, 90),
    (270, 0),
    (359, 271),
])
def test_wind_to_from(wind_to, expected, unit_conversions_module):
    assert equal_enough(
        unit_conversions_module.wind_to_from(wind_to), expected)


def test_wind_to_from_ndarray(unit_conversions_module):
    wind_from = unit_conversions_module.wind_to_from(
        np.array([0, 90, 180, 270, 359]))
    np.testing.assert_allclose
    (wind_from, np.array([270, 180, 90, 0, 271]))


class TestBearingHEading(object):
    """Unit tests for bearing_heading() function.
    """
    @pytest.mark.parametrize('bearing, expected', [
        (0, 'N'),
        (27, 'NNE'),
        (359, 'N'),
    ])
    def test_default_16_points(
        self, bearing, expected, unit_conversions_module,
    ):
        heading = unit_conversions_module.bearing_heading(bearing)
        assert heading == expected

    @pytest.mark.parametrize('bearing, expected', [
        (0, 'N'),
        (27, 'NE'),
        (359, 'N'),
    ])
    def test_8_points(
        self, bearing, expected, unit_conversions_module,
    ):
        heading = unit_conversions_module.bearing_heading(
            bearing,
            headings=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N'])
        assert heading == expected
