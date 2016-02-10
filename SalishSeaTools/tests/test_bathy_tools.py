"""Unit tests for bathy_tools.
"""
from __future__ import division
"""
Copyright 2013-2016 The Salish Sea MEOPAR contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import netCDF4 as nc
import numpy as np
import pytest
from salishsea_tools import bathy_tools


@pytest.fixture
def depths(request):
    bathy = nc.Dataset('foo', 'w')
    bathy.createDimension('x', 3)
    bathy.createDimension('y', 5)
    depths = bathy.createVariable('Bathymetry', float, ('y', 'x'))

    def teardown():
        bathy.close()
        os.remove('foo')
    request.addfinalizer(teardown)
    return depths


def test_smooth_neighbours_d1_lt_d2():
    """smooth_neighbours returns expected value for depth1 < depth2
    """
    d1, d2 = bathy_tools.smooth_neighbours(0.2, 1, 2)
    assert d1, d2 == (1.3, 1.7)


def test_smooth_neighbours_d1_gt_d2():
    """smooth_neighbours returns expected value for depth1 > depth2
    """
    d1, d2 = bathy_tools.smooth_neighbours(0.2, 2, 1)
    assert d1, d2 == (1.7, 1.3)


def test_calc_norm_depth_diffs_degenerate(depths):
    """calc_norm_depth_diffs returns zeros for delta_lat=delta_lon=0
    """
    depths = np.ones((5, 3))
    diffs = bathy_tools.calc_norm_depth_diffs(depths, 0, 0)
    np.testing.assert_array_equal(diffs, np.zeros_like(depths))


def test_calc_norm_depth_diffs_1_lat_step(depths):
    """calc_norm_depth_diffs returns expected diffs for delta_lat=1
    """
    depths = np.ones((5, 3))
    depths[1, 1] = 2
    diffs = bathy_tools.calc_norm_depth_diffs(depths, 1, 0)
    expected = np.zeros((4, 3))
    expected[0:2, 1] = 2 / 3
    np.testing.assert_array_equal(diffs, expected)


def test_calc_norm_depth_diffs_1_lon_step(depths):
    """calc_norm_depth_diffs returns expected diffs for delta_lon=1
    """
    depths = np.ones((5, 3))
    depths[1, 1] = 2
    diffs = bathy_tools.calc_norm_depth_diffs(depths, 0, 1)
    expected = np.zeros((5, 2))
    expected[1, 0:2] = 2 / 3
    np.testing.assert_array_equal(diffs, expected)


def test_argmax_single_max(depths):
    """argmax return expected indices for single max value
    """
    depths = np.zeros((5, 3))
    depths[1, 2] = 42
    result = bathy_tools.argmax(depths)
    assert result == (1, 2)


def test_argmax_2_max(depths):
    """argmax return expected indices for single max value
    """
    depths = np.zeros((5, 3))
    depths[1, 2] = 42
    depths[2, 1] = 42
    result = bathy_tools.argmax(depths)
    assert result == (1, 2)


def test_argmax_all_equal(depths):
    """argmax return expected indices for single max value
    """
    depths = np.ones((5, 3))
    result = bathy_tools.argmax(depths)
    assert result == (0, 0)
