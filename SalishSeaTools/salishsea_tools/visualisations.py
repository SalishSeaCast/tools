# Copyright 2016 The Salish Sea NEMO Project and
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

"""Functions for common model visualisations
"""

import matplotlib.pyplot as plt
from matplotlib import patches
import numpy as np

from salishsea_tools import tidetools


def contour_thalweg(
    axes, var, bathy, lons, lats, mesh_mask, mesh_mask_depth_var, clevels,
    cmap='hsv', land_colour='burlywood', xcoord_distance=True,
    thalweg_file='/data/nsoontie/MEOPAR/tools/bathymetry/thalweg_working.txt'
):
    """Contour the data stored in var along the domain thalweg.

    :arg axes: Axes instance to plot thalweg contour on.
    :type axes: :py:class:`matplotlib.axes.Axes`

    :arg var: Salish Sea NEMO model results variable to be contoured
    :type var: :py:class:`numpy.ndarray`

    :arg bathy: Salish Sea NEMO model bathymetry data
    :type bathy: :py:class:`numpy.ndarray`

    :arg lons: Salish Sea NEMO model longitude grid data
    :type lons: :py:class:`numpy.ndarray`

    :arg lats: Salish Sea NEMO model latitude grid data
    :type lats: :py:class:`numpy.ndarray`

    :arg mesh_mask: Salish Sea NEMO model mesh_mask data
    :type mesh_mask: :py:class:`netCDF4.Dataset`

    :arg str mesh_mask_depth_var: name of depth variable in :kbd:`mesh_mask`
                                  that is appropriate for :kbd:`var`.

    :arg clevels: argument for determining contour levels. Choices are
                  1. 'salinity' or 'temperature' for pre-determined levels
                  used in nowcast.
                  2. an integer N, for N automatically determined levels.
                  3. a sequence V of contour levels, which must be in
                  increasing order.
    :type clevels: str or int or iterable

    :arg str cmap: matplotlib colormap

    :arg str land_colour: matplotlib colour for land

    :arg xcoord_distance: plot along thalweg distance (True) or index (False)
    :type xcoord_distance: boolean

    :arg thalweg_pts_file: Path and file name to read the array of
                           thalweg grid points from.
    :type thalweg_pts_file: str

    :returns: matplotlib colorbar object
    """
    thalweg_pts = np.loadtxt(thalweg_file, delimiter=' ', dtype=int)
    depth = mesh_mask.variables[mesh_mask_depth_var][:]
    dep_thal, distance, var_thal = load_thalweg(
        depth[0, ...], var, lons, lats, thalweg_pts)
    if xcoord_distance:
        xx_thal = distance
        axes.set_xlabel('Distance along thalweg [km]')
    else:
        xx_thal, _ = np.meshgrid(np.arange(var_thal.shape[-1]), dep_thal[:, 0])
        axes.set_xlabel('Thalweg index')
    # Determine contour levels
    clevels_default = {
        'salinity': [
            26, 27, 28, 29, 30, 30.2, 30.4, 30.6, 30.8, 31, 32, 33, 34
        ],
        'temperature': [
            6.9, 7, 7.5, 8, 8.5, 9, 9.8, 9.9, 10.3, 10.5, 11, 11.5, 12,
            13, 14, 15, 16, 17, 18, 19
        ]
    }
    if isinstance(clevels, str):
        try:
            clevels = clevels_default[clevels]
        except KeyError:
            raise KeyError('no default clevels defined for {}'.format(clevels))
    # Prepare for plotting by filling in grid points just above bathymetry
    var_plot = _fill_in_bathy(var_thal, mesh_mask, thalweg_pts)
    mesh = axes.contourf(xx_thal, dep_thal, var_plot, clevels, cmap=cmap,
                         extend='both')
    _add_bathy_patch(xx_thal, bathy, thalweg_pts, axes, color=land_colour)
    cbar = plt.colorbar(mesh, ax=axes)
    axes.set_ylabel('Depth [m]')
    return cbar


def _add_bathy_patch(xcoord, bathy, thalweg_pts, ax, color, zmin=450):
    """Add a polygon shaped as the land in the thalweg section

    :arg xcoord: x grid along thalweg
    :type xcoord: 2D numpy array

    :arg bathy: Salish Sea NEMO model bathymetry data
    :type bathy: :py:class:`numpy.ndarray`

    :arg thalweg_pts: Salish Sea NEMO model grid indices along thalweg
    :type thalweg_pts: 2D numpy array

    :arg ax:  Axes instance to plot thalweg contour on.
    :type ax: :py:class:`matplotlib.axes.Axes`

    :arg str color: color of bathymetry patch

    :arg zmin: minimum depth for plot in meters
    :type zmin: float
    """
    # Look up bottom bathymetry along thalweg
    thalweg_bottom = bathy[thalweg_pts[:, 0], thalweg_pts[:, 1]]
    # Construct bathy polygon
    poly = np.zeros((thalweg_bottom.shape[0]+2, 2))
    poly[0, :] = 0, zmin
    poly[1:-1, 0] = xcoord[0, :]
    poly[1:-1:, 1] = thalweg_bottom
    poly[-1, :] = xcoord[0, -1], zmin
    ax.add_patch(patches.Polygon(poly, facecolor=color, edgecolor=color))


def load_thalweg(depths, var, lons, lats, thalweg_pts):
    """Returns depths, cummulative distance and variable along thalweg.

    :arg depths: depth array for variable. Can be 1D or 3D.
    :type depths: :py:class:`numpy.ndarray`

    :arg var: 3D Salish Sea NEMO model results variable
    :type var: :py:class:`numpy.ndarray`

    :arg lons: Salish Sea NEMO model longitude grid data
    :type lons: :py:class:`numpy.ndarray`

    :arg lats: Salish Sea NEMO model latitude grid data
    :type lats: :py:class:`numpy.ndarray`

    :arg thalweg_pts: Salish Sea NEMO model grid indices along thalweg
    :type thalweg_pts: 2D numpy array

    :returns: dep_thal, xx_thal, var_thal, all the same shape
              (depth, thalweg length)
    """

    lons_thal = lons[thalweg_pts[:, 0], thalweg_pts[:, 1]]
    lats_thal = lats[thalweg_pts[:, 0], thalweg_pts[:, 1]]
    var_thal = var[:, thalweg_pts[:, 0], thalweg_pts[:, 1]]

    xx_thal = distance_along_curve(lons_thal, lats_thal)
    xx_thal = xx_thal + np.zeros(var_thal.shape)

    if depths.ndim > 1:
        dep_thal = depths[:, thalweg_pts[:, 0], thalweg_pts[:, 1]]
    else:
        _, dep_thal = np.meshgrid(xx_thal[0, :], depths)
    return dep_thal, xx_thal, var_thal


def _fill_in_bathy(variable, mesh_mask, thalweg_pts):
    """For each horizontal point in variable, fill in first vertically masked
    point with the value just above.
    Use mbathy in mesh_mask file to determine level of vertical masking

    :arg variable: the variable to be filled
    :type variable: 2D numpy array

    :arg mesh_mask: Salish Sea NEMO model mesh_mask data
    :type mesh_mask: :py:class:`netCDF4.Dataset`

    :arg thalweg_pts: Salish Sea NEMO model grid indices along thalweg
    :type thalweg_pts: 2D numpy array

    :returns: newvar, the filled numpy array
    """
    mbathy = mesh_mask.variables['mbathy'][0, :, :]
    newvar = np.copy(variable)

    mbathy = mbathy[thalweg_pts[:, 0], thalweg_pts[:, 1]]
    for i, level in enumerate(mbathy):
        newvar[level, i] = variable[level-1, i]
    return newvar


def distance_along_curve(lons, lats):
    """Calculate cumulative distance in km between points in lons, lats

    :arg lons: longitude points
    :type lons: 1D numpy array

    :arg lats: latitude points
    :type lats: 1D numpy array

    :returns: numpy array with distance along track in km
    """
    dist = [0]
    for i in np.arange(1, lons.shape[0]):
        newdist = dist[i-1] + tidetools.haversine(lons[i], lats[i],
                                                  lons[i-1], lats[i-1])
        dist.append(newdist)
    dist = np.array(dist)
    return dist
