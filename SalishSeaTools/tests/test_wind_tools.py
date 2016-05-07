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

"""Unit tests for Salish Sea NEMO nowcast make_feeds worker.
"""
from __future__ import division

import os
from unittest.mock import patch

import arrow
import netCDF4 as nc
import numpy as np
import pytest

from salishsea_tools import wind_tools


@pytest.fixture
def wind_dataset(nc_dataset):
    nc_dataset.createDimension('time_counter')
    nc_dataset.createDimension('y', 1)
    nc_dataset.createDimension('x', 1)
    u_wind = nc_dataset.createVariable(
        'u_wind', float, ('time_counter', 'y', 'x'))
    u_wind[:] = np.arange(5)
    v_wind = nc_dataset.createVariable(
        'v_wind', float, ('time_counter', 'y', 'x'))
    v_wind[:] = np.arange(0, -5, -1)
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2016-FEB-02 00:00:00'
    time_counter[:] = np.arange(5) * 60*60
    return nc_dataset


class TestWindSpeedDir(object):
    """Unit tests for the wind_speed_dir() function.
    """
    @pytest.mark.parametrize('u_wind, v_wind, exp_speed, exp_dir', [
        (0, 0, 0, 0),
        (1, 0, 1, 0),
        (1, 1, 1.414214, 45),
        (3, 4, 5, 53.130102),
        (0, 1, 1, 90),
        (-1, 1, 1.414214, 135),
        (-1, 0, 1, 180),
        (-1, -1, 1.414214, 225),
        (0, -1, 1, 270),
        (1, -1, 1.414214, 315),
        (1, -0.001, 1, 359.942704),
    ])
    def test_scalar_uv_values(
        self, u_wind, v_wind, exp_speed, exp_dir,
    ):
        wind = wind_tools.wind_speed_dir(u_wind, v_wind)
        np.testing.assert_allclose(wind.speed, exp_speed, rtol=1e-05)
        np.testing.assert_allclose(wind.dir, exp_dir, rtol=1e-05)

    def test_ndarray_uv_values(self):
        u_wind = np.array([0, 1, 1, 3, 0, -1, -1, -1, 0, 1, 1])
        v_wind = np.array([0, 0, 1, 4, 1, 1, 0, -1, -1, -1, -0.001])
        wind = wind_tools.wind_speed_dir(u_wind, v_wind)
        exp_speed = np.array([
            0, 1, 1.414214, 5, 1, 1.414214, 1, 1.414214, 1, 1.414214, 1])
        np.testing.assert_allclose(wind.speed, exp_speed, rtol=1e-05)
        exp_dir = np.array([
            0, 0, 45, 53.130102, 90, 135, 180, 225, 270, 315, 359.942704])
        np.testing.assert_allclose(wind.dir, exp_dir)


class TestCalcWindAvgAtPoint(object):
    """Unit tests for calc_wind_avg_at_point() function.
    """
    @patch.object(wind_tools.nc_tools, 'dataset_from_path')
    def test_ops_wind(self, m_dfp, wind_dataset, tmpdir):
        tmp_weather_path = tmpdir.ensure_dir('operational')
        m_dfp.side_effect = (wind_dataset,)
        wind_avg = wind_tools.calc_wind_avg_at_point(
            arrow.get('2016-02-02 04:25'), str(tmp_weather_path), (0, 0))
        np.testing.assert_allclose(wind_avg.u, 2.5)
        np.testing.assert_allclose(wind_avg.v, -2.5)

    @patch.object(wind_tools.nc_tools, 'dataset_from_path')
    def test_2h_avg(self, m_dfp, wind_dataset, tmpdir):
        tmp_weather_path = tmpdir.ensure_dir('operational')
        m_dfp.side_effect = (wind_dataset,)
        wind_avg = wind_tools.calc_wind_avg_at_point(
            arrow.get('2016-02-02 04:25'), str(tmp_weather_path), (0, 0),
            avg_hrs=-2)
        np.testing.assert_allclose(wind_avg.u, 3.5)
        np.testing.assert_allclose(wind_avg.v, -3.5)

    @patch.object(wind_tools.nc_tools, 'dataset_from_path')
    def test_fcst_wind(self, m_dfp, wind_dataset, tmpdir):
        tmp_weather_path = tmpdir.ensure_dir('operational')
        m_dfp.side_effect = (IOError, wind_dataset)
        wind_avg = wind_tools.calc_wind_avg_at_point(
            arrow.get('2016-02-02 04:25'), str(tmp_weather_path), (0, 0))
        np.testing.assert_allclose(wind_avg.u, 2.5)
        np.testing.assert_allclose(wind_avg.v, -2.5)

    @patch.object(wind_tools.nc_tools, 'dataset_from_path')
    def test_prepend_previous_day(
        self, m_dfp, wind_dataset, tmpdir,
    ):
        tmp_weather_path = tmpdir.ensure_dir('operational')
        wind_prev_day = nc.Dataset('wind_prev_day', 'w')
        wind_prev_day.createDimension('time_counter')
        wind_prev_day.createDimension('y', 1)
        wind_prev_day.createDimension('x', 1)
        u_wind = wind_prev_day.createVariable(
            'u_wind', float, ('time_counter', 'y', 'x'))
        u_wind[:] = np.arange(5)
        v_wind = wind_prev_day.createVariable(
            'v_wind', float, ('time_counter', 'y', 'x'))
        v_wind[:] = np.arange(0, -5, -1)
        time_counter = wind_prev_day.createVariable(
            'time_counter', float, ('time_counter',))
        time_counter.time_origin = '2016-FEB-01 00:00:00'
        time_counter[:] = np.arange(19, 24) * 60*60
        m_dfp.side_effect = (wind_dataset, wind_prev_day)
        wind_avg = wind_tools.calc_wind_avg_at_point(
            arrow.get('2016-02-02 01:25'), str(tmp_weather_path), (0, 0))
        wind_prev_day.close()
        os.remove('wind_prev_day')
        np.testing.assert_allclose(wind_avg.u, 2)
        np.testing.assert_allclose(wind_avg.v, -2)
