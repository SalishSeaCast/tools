# Copyright 2013-2015 The Salish Sea MEOPAR contributors
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

from salishsea_tools.teos_tools import (
    PSU_TEOS,
    TEOS_PSU,
    psu_teos,
    teos_psu,
)


#: Conversion factor from m/s to km/hr
M_PER_S__KM_PER_HR = 3600 / 1000
#: Conversion factor from m/s to knots
M_PER_S__KNOTS = 3600 / 1852


def mps_kph(m_per_s):
    """Convert speed from m/s to km/hr.

    :arg m_per_s: Speed in m/s to convert.

    :returns: Speed in km/hr.
    """
    return m_per_s * M_PER_S__KM_PER_HR


def mps_knots(m_per_s):
    """Convert speed from m/s to knots.

    :arg m_per_s: Speed in m/s to convert.

    :returns: Speed in knots.
    """
    return m_per_s * M_PER_S__KNOTS


def wind_to_from(wind_to):
    """Convert wind bearing from "physics" compass "to" direction to
    "human"compass "from" direction.

    "Physics" compass has zero at the east and bearing angles increase
    in the counter-clockwise direction.

    "Human" compass has zero at the north and bearing angles increase in
    the clockwise direction.

    Example: 0° on the physics compass indicates air flow to the east
    which is called a west (270°) wind on the human compass.

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
