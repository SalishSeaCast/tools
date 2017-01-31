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
import datetime
import glob
import os
import netCDF4 as nc

from salishsea_tools import nc_tools
from salishsea_tools import geo_tools

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
    'wind_speed_dir', 'get_weather_filenames', 'get_model_winds',
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

    :arg 2-tuple windji: Indices of weather datasset grid point to
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

def get_weather_filenames(t_orig, t_final, weather_path):
    """Gathers a list of "Operational" atmospheric model filenames in a
    specifed date range.

    :arg datetime t_orig: The beginning of the date range of interest.

    :arg datetime t_final: The end of the date range of interest.

    :arg str weather_path: The directory where the weather forcing files
                           are stored.

    :returns: list of files names (files) from the Operational model.
    """
    numdays = (t_final - t_orig).days
    dates = [
        t_orig + datetime.timedelta(days=num)
        for num in range(0, numdays + 1)]
    dates.sort()

    allfiles = glob.glob(os.path.join(weather_path, 'ops_y*'))
    sstr = os.path.join(weather_path, dates[0].strftime('ops_y%Ym%md%d.nc'))
    estr = os.path.join(weather_path, dates[-1].strftime('ops_y%Ym%md%d.nc'))
    files = []
    for filename in allfiles:
        if filename >= sstr:
            if filename <= estr:
                files.append(filename)
    files.sort(key=os.path.basename)

    return files


def get_model_winds(lon, lat, t_orig, t_final, weather_path):
    """Returns meteorological fields for the "Operational" model at a given
    longitude and latitude over a date range.

    :arg float lon: The specified longitude.

    :arg float lat: The specified latitude.

    :arg datetime t_orig: The beginning of the date range of interest.

    :arg datetime t_final: The end of the date range of interest.

    :arg str weather_path: The directory where the weather forcing files
                           are stored.

    :returns: wind speed (wind), wind direction (direc), time (t),
              pressure (pr), temperature (tem), solar radiation (sol),
              thermal radiation (the),humidity (qr), precipitation (pre).
              wind speed: m/s (confirm this)
              wind direction: direction wind is GOING, RELATIVE TO EAST,
              WITH POSITIVE DIRECTION CCW
    """

    # Weather file names
    files = get_weather_filenames(t_orig, t_final, weather_path)
    weather = nc.Dataset(files[0])
    Y = weather.variables['nav_lat'][:]
    X = weather.variables['nav_lon'][:] - 360

    [j, i] = geo_tools.find_closest_model_point(lon, lat, X, Y, grid="GEM2.5")

    wind = np.array([])
    direc = np.array([], 'double')
    t = np.array([])
    pr = np.array([])
    sol = np.array([])
    the = np.array([])
    pre = np.array([])
    tem = np.array([])
    qr = np.array([])
    for f in files:
        G = nc.Dataset(f)
        u = G.variables['u_wind'][:, j, i]
        v = G.variables['v_wind'][:, j, i]
        pr = np.append(pr, G.variables['atmpres'][:, j, i])
        sol = np.append(sol, G.variables['solar'][:, j, i])
        qr = np.append(qr, G.variables['qair'][:, j, i])
        the = np.append(the, G.variables['therm_rad'][:, j, i])
        pre = np.append(pre, G.variables['precip'][:, j, i])
        tem = np.append(tem, G.variables['tair'][:, j, i])
        speed = np.sqrt(u ** 2 + v ** 2)
        wind = np.append(wind, speed)

        d = np.arctan2(v, u)
        d = np.rad2deg(d + (d < 0) * 2 * np.pi)
        direc = np.append(direc, d)

        ts = G.variables['time_counter']
        # There is no time_origin attribute in OP files; this is hard coded.
        torig = datetime.datetime(1970, 1, 1)
        for ind in np.arange(ts.shape[0]):
            t = np.append(t, torig + datetime.timedelta(seconds=ts[ind]))
    return wind, direc, t, pr, tem, sol, the, qr, pre

