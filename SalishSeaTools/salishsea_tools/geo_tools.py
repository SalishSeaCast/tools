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

    :returns: Cumulative point-by-point distance along track in km.
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


def _spiral_search_for_closest_water_point(
    j, i, land_mask, lon, lat, model_lons, model_lats
):
    # Searches in a spiral pattern around grid element (j,i)
    # for the closest water point to the the coordinate (lat,lon)

    jmax, imax = land_mask.shape
    # Limit on size of grid search
    max_search_dist = max(50, int(model_lats.shape[1]/4))
    closest_point = None
    j_s, i_s = j, i  # starting point is j, i
    dj, di = 0, -1
    # move j_s, i_s in a square spiral centred at j, i
    while (i_s-i) <= max_search_dist:
        if any([(j_s-j) == (i_s-i),
               ((j_s-j) < 0 and (j_s-j) == -(i_s-i)),
               ((j_s-j) > 0 and (j_s-j) == 1-(i_s-i))]):
            # Hit the corner of the spiral- change direction
            dj, di = -di, dj
        i_s, j_s = i_s+di, j_s+dj  # Take a step to next square
        if (i_s >= 0
            and i_s < imax
            and j_s >= 0
            and j_s < jmax
            and not land_mask[j_s, i_s]
        ):
            # Found a water point, how close is it?
            actual_dist = haversine(
                lon, lat, model_lons[j_s, i_s], model_lats[j_s, i_s])
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
    if closest_point is not None:
        return closest_point
    else:
        raise ValueError('lat/lon on land and no nearby water point found')


def find_closest_model_point(
    lon, lat, model_lons, model_lats, grid='NEMO', land_mask=None,
    tols={
        'NEMO': {'tol_lon': 0.0104, 'tol_lat': 0.00388},
        'GEM2.5': {'tol_lon': 0.016, 'tol_lat': 0.012},
        },
    checkTol=False
):
    """Returns the grid coordinates of the closest model point
    to a specified lon/lat. If land_mask is provided, returns the closest
    water point.

    Example:

    .. code-block:: python

        j, i = find_closest_model_point(
                   -125.5,49.2,model_lons,model_lats,land_mask=bathy.mask)

    where bathy, model_lons and model_lats are returned from
    :py:func:`salishsea_tools.tidetools.get_bathy_data`.

    j is the y-index(latitude), i is the x-index(longitude)

    :arg float lon: longitude to find closest grid point to

    :arg float lat: latitude to find closest grid point to

    :arg model_lons: specified model longitude grid
    :type model_lons: :py:obj:`numpy.ndarray`

    :arg model_lats: specified model latitude grid
    :type model_lats: :py:obj:`numpy.ndarray`

    :arg grid: specify which default lon/lat tolerances
    :type grid: string

    :arg land_mask: describes which grid coordinates are land
    :type land_mask: numpy array

    :arg tols: stored default tols for different grid types
    :type tols: dict

    :arg checkTol: optionally check that nearest ocean point is not
        outside specified tolerances in case that spiral search is called

    :returns: yind, xind
    """

    if grid not in tols:
        raise KeyError(
            'The provided grid type is not in tols. '
            'Use another grid type or add your grid type to tols.')

    # Search for a grid point with longitude and latitude within
    # tolerance of measured location
    j_list, i_list = np.where(
        np.logical_and(
            (np.logical_and(model_lons > lon - tols[grid]['tol_lon'],
                            model_lons < lon + tols[grid]['tol_lon'])),
            (np.logical_and(model_lats > lat - tols[grid]['tol_lat'],
                            model_lats < lat + tols[grid]['tol_lat']))
        )
    )

    if len(j_list) == 0:
        # Added by BMM March 2017
        # If including points outside of domain:
        return np.nan, np.nan
        # raise ValueError(
        #    'No model point found. tol_lon/tol_lat too small or '
        #    'lon/lat outside of domain.')
    try:
        j, i = map(np.asscalar, (j_list, i_list))
    except ValueError:
        # Several points within tolerance
        # Calculate distances for all and choose the closest

        # Avoiding array indexing because some functions
        # pass in model_lons and model_lats as netcdf4 objects
        # (which treat 'model_lons[j_list, i_list]' differently)
        lons = [model_lons[j_list[n], i_list[n]] for n in range(len(j_list))]
        lats = [model_lats[j_list[n], i_list[n]] for n in range(len(j_list))]
        dists = haversine(
            np.array([lon] * i_list.size), np.array([lat] * j_list.size),
            lons, lats)
        n = dists.argmin()
        j, i = map(np.asscalar, (j_list[n], i_list[n]))

    # If point is on land and land mask is provided
    # try to find closest water point
    if land_mask is None or not land_mask[j, i]:
        return j, i
    try:
        if checkTol:
            j2,i2=_spiral_search_for_closest_water_point(
                j, i, land_mask, lon, lat, model_lons, model_lats)
            if (np.abs(model_lons[j2,i2]-lon)>tols[grid]['tol_lon']) or \
                (np.abs(model_lats[j2,i2]-lat)>tols[grid]['tol_lat']):
                return np.nan,np.nan
            else: 
                return j2, i2
        else:
            return _spiral_search_for_closest_water_point(
                j, i, land_mask, lon, lat, model_lons, model_lats)
    except ValueError:
        raise ValueError(
            'lat/lon on land and no nearby water point found')


def closestPointArray(lons,lats,
    model_lons, model_lats, tol2=1, grid='NEMO', land_mask=None,
    tols={
        'NEMO': {'tol_lon': 0.0104, 'tol_lat': 0.00388},
        'GEM2.5': {'tol_lon': 0.016, 'tol_lat': 0.012},
        }
):
    """Wrapper on find_closest_model_point that is faster if you have many points to locate AND
    you expect the points to be ordered such that each point is likely close to the point ahead
    (eg ship track). 
    Returns the grid coordinates of the closest model points as numpy arrays of lons and lats.
    See find_closest_model_point for more details.
    For a list of 5000 points on ONC ferry path, speed up was ~95%.

    Additional/changed input:
    :arg float lons: numpy array of longitudes to find closest grid point to

    :arg float lats: numpy array of latitudes to find closest grid point to

    :arg int tol2:: expected distance in grid cells between one point and the next

    :returns: yinds, xinds: numpy arrays of same shape as input lons
    """
    tol2=int(tol2) # ensure integer indices
    mj,mi=np.shape(model_lons)
    outi=np.nan*np.ones(np.shape(lons))
    outj=np.nan*np.ones(np.shape(lons))
    ilast=np.nan
    jlast=np.nan
    for kk in range(0,len(lons)):
        if not np.isnan(ilast):
            jjs=max(0,jlast-tol2-1)
            jje=min(mj,jlast+1+tol2+1)
            iis=max(0,ilast-tol2-1)
            iie=min(mi,ilast+1+tol2+1)
            jj,ii=find_closest_model_point(lons[kk],lats[kk],
                    model_lons[jjs:jje,iis:iie],
                    model_lats[jjs:jje,iis:iie],
                    land_mask=land_mask if land_mask is None else land_mask[jjs:jje,iis:iie])
            if np.isnan(jj) or jj==0 or jj==(jje-1) or ii==0 or ii==(iie-1): # if not found in expected grid swath or on edge
                jj,ii=find_closest_model_point(lons[kk],lats[kk],model_lons,model_lats,land_mask=land_mask)
            else:
                jj=jj+jjs
                ii=ii+iis
        else:
            jj,ii=find_closest_model_point(lons[kk],lats[kk],model_lons,model_lats,land_mask=land_mask)
        jlast=np.nan if np.isnan(jj) else int(jj)
        ilast=np.nan if np.isnan(ii) else int(ii)
        outj[kk]=jlast
        outi[kk]=ilast
    return outj, outi
