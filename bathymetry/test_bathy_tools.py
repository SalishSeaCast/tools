"""Unit tests for bathy_tools.
"""
"""
Copyright 2013 The Salish Sea MEOPAR contributors
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
import netCDF4 as nc
import numpy as np
import pytest
import bathy_tools


@pytest.fixture
def depths(request):
    bathy = nc.Dataset('foo', 'w')
    bathy.createDimension('x', 3)
    bathy.createDimension('y', 5)
    depths = bathy.createVariable('Bathymetry', float, ('y', 'x'))
    request.addfinalizer(bathy.close)
    return depths


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
