# Copyright 2013-2016 The Salish Sea NEMO Project and
# The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for geo_tools module.
"""
import numpy as np
import pytest


@pytest.fixture(scope='module')
def geo_tools_module():
    from salishsea_tools import geo_tools
    return geo_tools


class TestDistanceAlongCurve:
    """Unit tests for distance_along_curve() function.
    """
    KM_PER_NM = 1.852
    # The distance_along_curve() function uses the haversine formula which
    # has a typical error of up to 0.3% due to the Earth not being a perfect
    # sphere.
    # See http://www.movable-type.co.uk/scripts/latlong.html
    HAVERSINE_RTOL = 0.003

    @pytest.mark.parametrize('lons, lats, expected', [
        (np.array([0, 0]), np.array([0, 1]),
         np.array([0, 60*KM_PER_NM])),
        (np.array([-123, -123, -123.5]), np.array([49, 50, 50.5]),
         np.array([0, 60*KM_PER_NM, 60*KM_PER_NM + 65.99])),
    ])
    def test_distance_along_curve(self, lons, lats, expected, geo_tools_module):
        result = geo_tools_module.distance_along_curve(lons, lats)
        np.testing.assert_allclose(result, expected, rtol=self.HAVERSINE_RTOL)


class TestHaversine:
    """Unit tests for haversine() function.
    """
    KM_PER_NM = 1.852
    # The haversine formula which has a typical error of up to 0.3% due to the
    # Earth not being a perfect sphere.
    # See http://www.movable-type.co.uk/scripts/latlong.html
    HAVERSINE_RTOL = 0.003

    @pytest.mark.parametrize('lon1, lat1, lon2, lat2, expected', [
        (0, 0, 0, 1, 60*KM_PER_NM),
        (-123, 50, -123.5, 50.5, 65.99),
    ])
    def test_haversine(
        self, lon1, lat1, lon2, lat2, expected, geo_tools_module,
    ):
        result = geo_tools_module.haversine(lon1, lat1, lon2, lat2)
        np.testing.assert_allclose(result, expected, rtol=self.HAVERSINE_RTOL)
