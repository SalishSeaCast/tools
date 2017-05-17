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

    land_mask = np.array([
            [False, False, False,  True,  True],
            [False,  True,  True,  True,  True],
            [True,  True,  True,  True,  True],
            [True,  True,  True,  True,  True]
    ])

    model_lons = np.array([
        [-124.5007019, -124.49552155, -124.49034119, -124.4851532,
         -124.47997284],
        [-124.50404358, -124.49885559, -124.49367523, -124.48848724,
         -124.48330688],
        [-124.50737762, -124.50219727, -124.49700928, -124.49182892,
         -124.48664093],
        [-124.5107193, -124.50553131, -124.50035095, -124.49516296,
         -124.4899826]
    ])

    model_lats = np.array([
        [48.53593826, 48.53788376, 48.53982544, 48.54176712, 48.5437088],
        [48.53991318, 48.54185486, 48.54379654, 48.54573822, 48.5476799],
        [48.54388428, 48.54582596, 48.54776764, 48.54970932, 48.551651],
        [48.54785919, 48.54980087, 48.55174255, 48.55368423, 48.55562592]
    ])

    def test_raises_value_error(self):
        with pytest.raises(ValueError):
            # lat and lon values that aren't on this grid (0, 0)
            geo_tools.find_closest_model_point(0, 0, self.model_lons, self.model_lats)

    @pytest.mark.parametrize('lon, lat, expected', [
        (-124.488, 48.54, (0, 2)),
        (-124.5, 48.54, (1, 0)),
        (-124.5, 48.555, (1, 0))
    ])
    def test_find_water_point(self, lon, lat, expected):
        j, i = geo_tools.find_closest_model_point(
            lon, lat, self.model_lons, self.model_lats, land_mask=self.land_mask)
        assert (j, i) == expected

    def test_no_land_mask_closest_grid_pt_found(self):
        lon = -124.5
        lat = 48.555
        expected = (3, 2)
        j, i = geo_tools.find_closest_model_point(
            lon, lat, self.model_lons, self.model_lats)
        assert (j, i) == expected

    def test_bad_tol_grid_key(self):
        with pytest.raises(KeyError):
            # Should raise a key error because the value
            # for grid is not a key in 'tols'
            geo_tools.find_closest_model_point(
                -124.5, 48.5, self.model_lons, self.model_lats, grid="NotAKey")

    def test_no_land_mask_1_grid_pt_found(self):
        lon, lat = -124.49885559, 48.54185486
        expected = (1, 1)
        j, i = geo_tools.find_closest_model_point(
            lon, lat, self.model_lons, self.model_lats, grid='test',
            tols={'test': {'tol_lon': 0.000001, 'tol_lat': 0.000001}})
        assert (j, i) == expected

    def test_no_water_pt_found(self):
        lon, lat = -124.5, 48.555
        all_land_land_mask = np.full(self.land_mask.shape, True, dtype=bool)
        with pytest.raises(ValueError):
            geo_tools.find_closest_model_point(
                lon, lat, self.model_lons, self.model_lats,
                land_mask=all_land_land_mask)
