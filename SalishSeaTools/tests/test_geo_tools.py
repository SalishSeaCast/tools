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
import netCDF4 as nc

from salishsea_tools import geo_tools
from salishsea_tools import tidetools

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
    def test_distance_along_curve(self, lons, lats, expected):
        result = geo_tools.distance_along_curve(lons, lats)
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
        (np.array([-123, -123]), np.array([49, 50]),
         np.array([-123, -123.5]), np.array([50, 50.5]),
         np.array([60*KM_PER_NM, 65.99])),
    ])
    def test_haversine(self, lon1, lat1, lon2, lat2, expected):
        result = geo_tools.haversine(lon1, lat1, lon2, lat2)
        np.testing.assert_allclose(result, expected, rtol=self.HAVERSINE_RTOL)


class TestFindClosestModelPoint:
    """ Unit tests for find_closest_model_point() function
    """

    grid_B = nc.Dataset('/data/nsoontie/MEOPAR/NEMO-forcing/grid/bathy_meter_SalishSea2.nc')
    bathy, model_lons, model_lats = tidetools.get_bathy_data(grid_B)

    def raises_value_error(self, model_lons, model_lats):
        with pytest.raises(ValueError):
            geo_tools.find_closest_model_point(0, 0, model_lons, model_lats)

    @pytest.mark.parametrize('lon, lat, expected', [
        (-122, 47.6, (69, 248)),
        (-124, 48.9, (437, 205)),
        (-123.515, 48.905, (404, 237)),
        (-123.50, 48.905, (403, 239))
    ])
    def test_find_closest_model_point(self, lon, lat, expected):
        j, i = geo_tools.find_closest_model_point(lon, lat, self.model_lons, self.model_lats, land_mask = self.bathy.mask)
        assert j == expected[0] and i == expected[1]
