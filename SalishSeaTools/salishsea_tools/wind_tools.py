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

"""Functions for working with wind model results and wind observations
data.
"""
from __future__ import division

from collections import namedtuple

import numpy as np

# For convenience we import the wind speed conversion factors
# and functions and wind direction manipulation functions so that they
# can be used from either here or the
# :py:mod:`salishsea_tools.unit_conversions` module
from salishsea_tools.unit_conversions import (
    M_PER_S__KM_PER_HR,
    M_PER_S__KNOTS,
    mps_kph,
    mps_knots,
    wind_to_from,
    bearing_heading,
)


__all__ = [
    'M_PER_S__KM_PER_HR', 'M_PER_S__KNOTS', 'mps_kph', 'mps_knots',
    'wind_to_from', 'bearing_heading',
    'wind_speed_dir',
]


def wind_speed_dir(u_wind, v_wind):
    """Calculate wind speed and direction from u and v wind components.

    :kbd:`u_wind` and :kbd:`v_wind` may be either scalar numbers or
    :py:class:`numpy.ndarray` objects,
    and the elements of the return value will be of the same type.

    :arg u_wind: u-direction component of wind vector.

    :arg v_wind: v-direction component of wind vector.

    :returns: 2-tuple containing the wind speed and direction.
              The :py:attr:`speed` attribute holds the wind speed(s),
              and the :py:attr:`dir` attribute holds the wind
              direction(s).
    :rtype: :py:class:`collections.namedtuple`
    """
    speed = np.sqrt(u_wind**2 + v_wind**2)
    dir = np.arctan2(v_wind, u_wind)
    dir = np.rad2deg(dir + (dir < 0) * 2 * np.pi)
    speed_dir = namedtuple('speed_dir', 'speed, dir')
    return speed_dir(speed, dir)
