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

"""Unit tests for Salish Sea NEMO nowcast make_feeds worker.
"""
from __future__ import division

import numpy as np
import pytest


@pytest.fixture
def wind_tools_module():
    from salishsea_tools import wind_tools
    return wind_tools


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
        self, u_wind, v_wind, exp_speed, exp_dir, wind_tools_module,
    ):
        wind = wind_tools_module.wind_speed_dir(u_wind, v_wind)
        np.testing.assert_allclose(wind.speed, exp_speed, rtol=1e-05)
        np.testing.assert_allclose(wind.dir, exp_dir, rtol=1e-05)

    def test_ndarray_uv_values(self, wind_tools_module):
        u_wind = np.array([0, 1, 1, 3, 0, -1, -1, -1, 0, 1, 1])
        v_wind = np.array([0, 0, 1, 4, 1, 1, 0, -1, -1, -1, -0.001])
        wind = wind_tools_module.wind_speed_dir(u_wind, v_wind)
        exp_speed = np.array([
            0, 1, 1.414214, 5, 1, 1.414214, 1, 1.414214, 1, 1.414214, 1])
        np.testing.assert_allclose(wind.speed, exp_speed, rtol=1e-05)
        exp_dir = np.array([
            0, 0, 45, 53.130102, 90, 135, 180, 225, 270, 315, 359.942704])
        np.testing.assert_allclose(wind.dir, exp_dir)
