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

"""Functions for working with wind model results and wind observations
data.
"""
from __future__ import division

from collections import namedtuple
from pathlib import Path

import numpy as np
from salishsea_tools import nc_tools

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
    'calc_wind_avg_at_point',
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


def calc_wind_avg_at_point(date_time, weather_path, windji, avg_hrs=-4):
    """Calculate the average wind components for a time period at
    a single weather dataset grid point.

    .. note::

        The present implementation only supports averaging over a time
        period ending at:kbd:`date_time` and values for :kbd:`avg_hrs`
        in the range :kbd:`[-24, 0]`.

    :arg date_time: Date and time to use as base for the calculation.
    :type date_time: :py:class:`arrow.arrow.Arrow`

    :arg str weather_path: The directory where weather dataset files
                           are stored.

    :arg 2-tuple windji: Indices of weather dataset grid point to
                         calculate the average at as
                         :kbd:`(lon_index, lat_index)`.

    :arg float avg_hrs: Number of hours to calculate

    :returns: 2-tuple containing the averaged wind components.
              The :py:attr:`u` attribute holds the u-direction component,
              and the :py:attr:`v` attribute holds the v-direction
              component.
    :rtype: :py:class:`collections.namedtuple`

    :raises: :py:exc:`IndexError` if :kbd:`avg_hrs` is outside the range
             :kbd:`[-24, 0]`.
    """
    weather_filename_tmpl = 'ops_y{0.year:4d}m{0.month:02d}d{0.day:02d}.nc'
    try:
        weather_file = Path(
            weather_path, weather_filename_tmpl.format(date_time))
        grid_weather = nc_tools.dataset_from_path(weather_file)
    except IOError:
        weather_file = Path(
            weather_path, 'fcst', weather_filename_tmpl.format(date_time))
        grid_weather = nc_tools.dataset_from_path(weather_file)
    wind_u, wind_v, wind_t = nc_tools.uv_wind_timeseries_at_point(
        grid_weather, *windji)
    if date_time.hour < abs(avg_hrs):
        grid_weather = nc_tools.dataset_from_path(
            weather_file.with_name(
                weather_filename_tmpl.format(date_time.replace(days=-1))))
        wind_prev_day = nc_tools.uv_wind_timeseries_at_point(
            grid_weather, *windji)
        wind_u = np.concatenate((wind_prev_day.u, wind_u))
        wind_v = np.concatenate((wind_prev_day.v, wind_v))
        wind_t = np.concatenate((wind_prev_day.time, wind_t))
    i_date_time = np.asscalar(
        np.where(wind_t == date_time.floor('hour'))[0])
    i_date_time_p1 = i_date_time + 1
    u_avg = np.mean(wind_u[(i_date_time_p1 + avg_hrs):i_date_time_p1])
    v_avg = np.mean(wind_v[(i_date_time_p1 + avg_hrs):i_date_time_p1])
    wind_avg = namedtuple('wind_avg', 'u, v')
    return wind_avg(u_avg, v_avg)



    
