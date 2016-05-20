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

"""Functions for working with geographical data and model results.
"""
import numpy as np


def distance_along_curve(lons, lats):
    """Calculate cumulative distance in km between points in lons, lats

    :arg lons: 1D array of longitude points.
    :type lons: :py:class:`numpy.ndarray`

    :arg lats: 1D array of latitude points.
    :type lats: :py:class:`numpy.ndarray`

    :returns: Cummulative point-by-point distance along track in km.
    :rtype: :py:class:`numpy.ndarray`
    """
    dist = np.cumsum(haversine(lons[1:], lats[1:], lons[:-1], lats[:-1]))
    return np.insert(dist, 0, 0)


def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great-circle distance in kilometers between two points
    on a sphere from their longitudes and latitudes.

    Reference: http://www.movable-type.co.uk/scripts/latlong.html

    :arg lon1: Longitude of point 1.
    :type lon1: float or :py:class:`numpy.ndarray`

    :arg lat1: Latitude of point 1.
    :type lat1: float or :py:class:`numpy.ndarray`

    :arg lon2: Longitude of point 2.
    :type lon2: float or :py:class:`numpy.ndarray`

    :arg lat2: Latitude of point 2.
    :type lat2: float or :py:class:`numpy.ndarray`

    :returns: Great-circle distance between two points in km
    :rtype: float or :py:class:`numpy.ndarray`
    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km


def find_closest_model_point(
    lon, lat, model_lons, model_lats, grid='NEMO', land_mask=None,
    tols={
        'NEMO': {'tol_lon': 0.0104, 'tol_lat': 0.00388},
        'GEM2.5': {'tol_lon': 0.016, 'tol_lat': 0.011},
        }):
    """Returns the grid coordinates of the closest model point
    to a specified lon/lat. If land_mask is provided, returns the closest
    water point.

    e.g.
    j, i = find_closest_model_point(-125.5,49.2,model_lons,model_lats,bathy)
    where bathy, model_lons and model_lats are returned from get_bathy_data(grid).
    j is the y-index(latitude), i is the x-index(longitude)

    :arg lon: specified longitude
    :type lon: float

    :arg lat: specified latitude
    :type lat: float

    :arg model_lons: specified model longitude
    :type model_lons: numpy array

    :arg model_lats: specified model latitude
    :type model_lats: numpy array

    :arg grid: specify which default lon/lat tolerances
    :type grid: string

    :arg land_mask: describes which grid co-ordinates are land
    :type land_mask: numpy array

    :arg tols: stored default tols for different grid types
    :type tols: dict

    :returns: yind, xind
    """

    # Search for a grid point with longitude or latitude within
    # tolerance of measured location
    j_list, i_list = np.where(
        np.logical_and(
            (np.logical_and(model_lons > lon - tols[grid]['tol_lon'], model_lons < lon + tols[grid]['tol_lon'])),
            (np.logical_and(model_lats > lat - tols[grid]['tol_lat'], model_lats < lat + tols[grid]['tol_lat']))))
    if j_list.size > 1 or i_list.size > 1:
        # several points within tol, calculate distance for all of them and pick closest
        min_dist = float('Inf')
        for n in range(len(i_list)):
            dist = haversine(lon, lat, model_lons[j_list[n], i_list[n]], model_lats[j_list[n], i_list[n]])
            if dist < min_dist:
                closest_point = (j_list[n], i_list[n])
                min_dist = dist
        j, i = closest_point
    elif not j_list or not i_list:
        raise ValueError(
            'No model point found. tol_lon/tol_lat too small or '
            'lon/lat outside of domain.'
        )
    else:
        i = i_list
        j = j_list

    # If point is on land and land mask is provided, try to find closest water point
    if land_mask is not None and land_mask[j, i]:
        jmax, imax = land_mask.shape
        max_search_dist = int(model_lats.shape[1]/4)  # Limit on size of grid search
        closest_point = None
        j_s, i_s = j, i  # starting points is j, i
        dj, di = 0, -1
        # move j_s, i_s in a square spiral centred at j, i
        while (i_s-i) <= max_search_dist:
            if ((j_s-j) == (i_s-i)
                or ((j_s-j) < 0 and (j_s-j) == -(i_s-i))
                or ((j_s-j) > 0 and (j_s-j) == 1-(i_s-i))
            ):
                # Hit the corner of the spiral- change direction
                dj, di = -di, dj
            i_s, j_s = i_s+di, j_s+dj  # Take a step to next square
            if i_s >= 0 and i_s < imax and j_s >= 0 and j_s < jmax and not land_mask[j_s, i_s]:
                # Found a water point, how close is it?
                actual_dist = haversine(lon, lat, model_lons[j_s, i_s], model_lats[j_s, i_s])
                if closest_point is None:
                    min_dist = actual_dist
                    closest_point = (j_s, i_s)
                elif actual_dist < min_dist:
                    # Keep record of closest point
                    min_dist = actual_dist
                    closest_point = (j_s, i_s)
                # Assumes grids are square- reduces search radius to only
                # check grids that could potentially be closer than this
                grid_dist = int(((i_s-i)**2 + (j_s-j)**2)**0.5)
                if (grid_dist + 1) < max_search_dist:
                    # Reduce stopping distance for spiral-
                    # just need to check that no points closer than this one
                    max_search_dist = grid_dist + 1

        if closest_point is None:
            raise ValueError(
                "Only found land points near that coordinate. If land points are OK don't pass in a land_mask."
            )
        else:
            j, i = closest_point
    return j, i
