# coding=utf-8

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

"""Salish Sea NEMO model unit conversion functions and constants.
"""
from __future__ import division

import numpy as np

# For convenience we import the TEOS-10 salinity conversion factors
# and functions so that they can be used from either here or the
# :py:mod:`salishsea_tools.teos_tools` module
from salishsea_tools.teos_tools import (
    PSU_TEOS,
    TEOS_PSU,
    psu_teos,
    teos_psu,
)


__all__ = [
    'PSU_TEOS', 'TEOS_PSU', 'psu_teos', 'teos_psu',
    'M_PER_S__KM_PER_HR', 'M_PER_S__KNOTS', 'mps_kph', 'mps_knots',
    'wind_to_from', 'bearing_heading',
    'humanize_time_of_day',
]


#: Conversion factor from m/s to km/hr
M_PER_S__KM_PER_HR = 3600 / 1000
#: Conversion factor from m/s to knots
M_PER_S__KNOTS = 3600 / 1852
#: Conversion factor from knots to m/s
KNOTS__M_PER_S = 1852 / 3600


def mps_kph(m_per_s):
    """Convert speed from m/s to km/hr.

    :kbd:`m_per_s` may be either a scalar number or a
    :py:class:`numpy.ndarray` object,
    and the return value will be of the same type.

    :arg m_per_s: Speed in m/s to convert.

    :returns: Speed in km/hr.
    """
    return m_per_s * M_PER_S__KM_PER_HR


def mps_knots(m_per_s):
    """Convert speed from m/s to knots.

    :kbd:`m_per_s` may be either a scalar number or a
    :py:class:`numpy.ndarray` object,
    and the return value will be of the same type.

    :arg m_per_s: Speed in m/s to convert.

    :returns: Speed in knots.
    """
    return m_per_s * M_PER_S__KNOTS


def knots_mps(knots):
    """Convert speed from knots to m/s.

    :kbd:`knots` may be either a scalar number or a
    :py:class:`numpy.ndarray` object,
    and the return value will be of the same type.

    :arg knots: Speed in knots to convert.

    :returns: Speed in m/s.
    """
    return knots * KNOTS__M_PER_S


def wind_to_from(wind_to):
    """Convert wind bearing from "physics" compass "to" direction to
    "human"compass "from" direction.

    "Physics" compass has zero at the east and bearing angles increase
    in the counter-clockwise direction.

    "Human" compass has zero at the north and bearing angles increase in
    the clockwise direction.

    Example: 0° on the physics compass indicates air flow to the east
    which is called a west (270°) wind on the human compass.

    :kbd:`wind_to` may be either a scalar number or a
    :py:class:`numpy.ndarray` object,
    and the return value will be of the same type.

    :arg wind_to: Bearing on physics (to) compass to convert.

    :returns: Bearing on human (from) compass.
    """
    try:
        # Scalar value case
        return 270 - wind_to if wind_to <= 270 else 270 - wind_to + 360
    except ValueError:
        # N-dimensional array case
        mask_le_270, mask_gt_270 = wind_to <= 270, wind_to > 270
        wind_from = np.array(wind_to, copy=True)
        wind_from[mask_le_270] = 270 - wind_to[mask_le_270]
        wind_from[mask_gt_270] = 270 - wind_to[mask_gt_270] + 360
        return wind_from


def bearing_heading(
    bearing,
    headings=(
        'N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S',
        'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N'),
):
    """Convert a compass bearing to a heading.

    :arg float bearing: The compass bearing to convert.

    :arg sequence headings: A sequence of headings to convert the bearing
                            to.
                            The default is the 16 compass points that
                            divide the compass into 22.5° segments.

    :returns: Compass heading.
    :rtype: str
    """
    return headings[int(round(bearing * (len(headings) - 1) / 360, 0))]


def humanize_time_of_day(date_time):
    """Return a "humanized" time of day string like "early Monday afternoon"
    that corresponds to :kbd:`date_time`.

    We use the same terminology as is used in the Environment Canada
    weather forecasts:
    https://www.ec.gc.ca/meteo-weather/default.asp?lang=En&n=10220A6B-1#c4

    :arg date_time: Date/time to humanize.
    :type date_time: :py:class:`arrow.Arrow`

    :returns: Humanized time of day and day name;
              e.g. early Monday afternoon
    :rtype: str
    """
    day_of_week = date_time.format('dddd')
    if date_time.hour < 6:
        part_of_day = ''
        early_late = 'overnight'
    elif date_time.hour < 12:
        part_of_day = 'morning'
        early_late = 'early' if date_time.hour < 9 else 'late'
    elif 12 <= date_time.hour < 18:
        part_of_day = 'afternoon'
        early_late = 'early' if date_time.hour < 15 else 'late'
    else:
        part_of_day = 'evening'
        early_late = 'early' if date_time.hour < 21 else 'late'
    return ' '.join((early_late, day_of_week, part_of_day)).rstrip()
