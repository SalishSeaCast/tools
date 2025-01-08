# Copyright 2013 – present The Salish Sea MEOPAR contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

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
from datetime import datetime
import os

import numpy as np
import pandas as pd
from salishsea_tools import nc_tools, stormtools

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
    "calc_wind_avg_at_point",
    "M_PER_S__KM_PER_HR",
    "M_PER_S__KNOTS",
    "mps_kph",
    "mps_knots",
    "wind_to_from",
    "bearing_heading",
    "wind_speed_dir",
]


def get_EC_observations(station, start_day, end_day):
    """Gather hourly Environment Canada (EC) weather observations for the
    station and dates indicated.

    This function is a wrapper for stormtools.get_EC_observations, which
    should be migrated to this module at some point

    The hourly EC data is stored in monthly files, so only a single month can
    be downloaded at a time.

    :arg station: Station name (no spaces). e.g. 'PointAtkinson'
    :type station: str

    :arg start_day: Start date in the format '01-Dec-2006'.
    :type start_day: str

    :arg end_day: End date in the format '01-Dec-2006'.
    :type end_day: str

    :returns: wind_speed, wind_dir, temperature, times, lat and lon:
              wind speed is in m/s
              wind_dir is direction wind is blowing to in degrees measured
              counterclockwise from East
              temperature is in Kelvin
              time is UTC
              Also returns latitude and longitude of the station.
    """

    # Call get_EC_observations from stormtools
    wind_spd, wind_dir, temp, times, lat, lon = stormtools.get_EC_observations(
        station,
        start_day,
        end_day,
    )

    return wind_spd, wind_dir, temp, times, lat, lon


def parse_DFO_buoy_date(line):
    """Parse the DFO buoy date from a list of data block header strings

    :arg line: list of data block header strings (containing datetime info)

    :returns: parsed datetime object

    :rtype: :py:class:`datetime.datetime`
    """

    # The date format changes throughout the record
    # -- thus the multiple cases
    if (int(line[3]) > 2020) & (int(line[3]) < 202020):
        year, month, day = int(line[3][:4]), int(line[3][4:]), int(line[4])
        HHMM = f"{int(line[5]):04d}"
    elif int(line[3]) > 202020:
        year, month, day = int(line[3][:4]), int(line[3][4:6]), int(line[3][6:])
        HHMM = f"{int(line[4]):04d}"
    elif int(line[4]) > 12:
        year = int(line[3])
        MMDD, HHMM = [f"{int(l):04d}" for l in line[4:6]]
        month, day = int(MMDD[:2]), int(MMDD[2:])
    else:
        year = int(line[3])
        HHMM = f"{int(line[6]):04d}"
        month, day = int(line[4]), int(line[5])
    hour, minute = int(HHMM[:2]), int(HHMM[2:])
    date = datetime(year, month, day, hour, minute, 0)

    return date


def read_DFO_buoy(station, year):
    """Reads the data from a DFO *.fb buoy data file and appends to a timeseries dict

    :arg station: station name string

    :arg year: integer year requested

    :returns: wsp, wdir and time arrays

    :rtype: :py:class:`numpy.ndarray`
    """

    # Station ID dict
    station_ids = {
        "Halibut Bank": 46146,
        "Sentry Shoal": 46131,
    }

    # Data url
    url = "https://www.meds-sdmm.dfo-mpo.gc.ca/alphapro/wave/waveshare/fbyears"

    # Open the *.zip file from url using Pandas
    ID = f"C{station_ids[station]}"
    file = os.path.join(url, ID, f"{ID.lower()}_{year}.zip")
    csv = pd.read_csv(file, header=None)

    # Initialize parsing booleans
    gotdate, gotwind = True, True

    # Initialize storage dict
    wspd, wdir, time = [], [], []

    # Read file line by line
    for line in csv.values:

        # Parse line to list of strings
        line_parsed = line[0].strip().split()

        # Ignore lines shorter than 4
        if len(line_parsed) > 3:

            # Begin new entry
            if line_parsed[3] == ID:
                gotdate = False

            # Parse date
            elif gotdate == False:
                gotdate, gotwind = True, False
                time.append(parse_DFO_buoy_date(line_parsed))

            # Read wind data
            elif gotwind == False:
                gotwind = True
                wdir.append(float(line_parsed[0].split("W")[0]))
                wspd.append(float(line_parsed[1].split("W")[0]))

    # Transform angle to deg CCW from east
    wdir = 270 - np.array(wdir)
    wdir[wdir < 0] += 360

    return np.array(wspd), wdir, np.array(time)


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
    speed_dir = namedtuple("speed_dir", "speed, dir")
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
    weather_filename_tmpl = "hrdps_y{0.year:4d}m{0.month:02d}d{0.day:02d}.nc"
    try:
        weather_file = Path(weather_path, weather_filename_tmpl.format(date_time))
        grid_weather = nc_tools.dataset_from_path(weather_file)
    except IOError:
        weather_file = Path(
            weather_path, "fcst", weather_filename_tmpl.format(date_time)
        )
        grid_weather = nc_tools.dataset_from_path(weather_file)
    wind_u, wind_v, wind_t = nc_tools.uv_wind_timeseries_at_point(grid_weather, *windji)
    if date_time.hour < abs(avg_hrs):
        grid_weather = nc_tools.dataset_from_path(
            weather_file.with_name(
                weather_filename_tmpl.format(date_time.shift(days=-1))
            )
        )
        wind_prev_day = nc_tools.uv_wind_timeseries_at_point(grid_weather, *windji)
        wind_u = np.concatenate((wind_prev_day.u, wind_u))
        wind_v = np.concatenate((wind_prev_day.v, wind_v))
        wind_t = np.concatenate((wind_prev_day.time, wind_t))
    i_date_time = np.where(wind_t == date_time.floor("hour"))[0].item()
    i_date_time_p1 = i_date_time + 1
    u_avg = np.mean(wind_u[(i_date_time_p1 + avg_hrs) : i_date_time_p1])
    v_avg = np.mean(wind_v[(i_date_time_p1 + avg_hrs) : i_date_time_p1])
    wind_avg = namedtuple("wind_avg", "u, v")
    return wind_avg(u_avg, v_avg)
