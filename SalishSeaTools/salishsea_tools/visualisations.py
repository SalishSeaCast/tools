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

import numpy as np
import matplotlib.patches as patches

from salishsea_tools import (tidetools)


def contour_thalweg(
    axes, var, grid_B, mesh_mask, depthname, clevels,
    cmap='hsv', land_colour='burlywood', xcoord='distance',
    thalweg_file='/data/nsoontie/MEOPAR/tools/bathymetry/thalweg_working.txt'
):
    """Contour the data stored in var along the domain thalweg.

    :arg axes: Axes instance to plot thalweg contour on.
    :type axes: :py:class:`matplotlib.axes.Axes`

    :arg var: variable to be contoured
    :type var: numpy array, shape (40,898,398)

    :arg grid_B: model bathymetry data
    :type lons: netCDF handle

    :arg mesh_mask: model mesh_mask data
    :type mesh_mask: netCDF handle

    :arg depthname: name of appropriate depth variable in mesh_mask
    :type depthname: str

    :arg clevels: levels for contouring
    :type clevels: list of numbers

    :arg cmap: colormap
    :type cmap: str representing a matplotlib colormap

    :arg land_colour: colour for land
    :type land_colour: str

    :arg xcoord: plot along thalweg distance or index
    :type xcoord: str, 'distance' or 'index'

    :arg thalweg_pts_file: Path and file name to read the array of
                           thalweg grid point from.
    :type thalweg_pts_file: str

    :returns: mesh, the matplotlib contour mesh object
    """
    # Load thalweg points, bathymetry, depths and variable along thalweg
    thalweg_pts = np.loadtxt(thalweg_file, delimiter=' ', dtype=int)
    bathy, X, Y = tidetools.get_bathy_data(grid_B)
    depth = mesh_mask.variables[depthname][:]
    dep_thal, distance, var_thal = _load_thalweg(depth[0, ...], var, X, Y,
                                                 thalweg_pts)
    if xcoord == 'distance':
        xx_thal = distance
    elif xcoord == 'index':
        xx_thal, _ = np.meshgrid(np.arange(var_thal.shape[-1]), dep_thal[:, 0])
    # Prepare for plotting by filling in grids above bathymetry
    var_plot = _fill_in_bathy(var_thal, mesh_mask, thalweg_pts)
    mesh = axes.contourf(xx_thal, dep_thal, var_plot, clevels, cmap=cmap,
                         extend='both')
    _add_bathy_patch(xx_thal, bathy, thalweg_pts, axes, color=land_colour)

    return mesh


def _add_bathy_patch(xcoord, bathy, thalweg_pts,  ax, color,
                     zmin=450):
    """Add a polygon shaped as the land in the thalweg section

    :arg xcoord: x grid along thalweg
    :type xcoord: 2D numpy array

    :arg bathy: bathymetry array, shape (898, 398)
    :type bathy: numpy array

    :arg lines: indices for the thalweg
    :type lines: 2D numpy array

    :arg ax: axis to plot in
    :type ax: axis handle

    :arg color: color of bathymetry patch
    :type color: string

    :arg zmin: minimum depth for plot in meters
    :type zmin: float
    """
    # Look up bottom bathymetry along thalweg
    thalweg_bottom = bathy[thalweg_pts[:, 0], thalweg_pts[:, 1]]
    # Construct bathy polygon
    poly = np.zeros((thalweg_bottom.shape[0]+2, 2))
    poly[0, 0] = 0
    poly[0, 1] = zmin
    poly[1:-1, 0] = xcoord[0, :]
    poly[1:-1, 1] = thalweg_bottom
    poly[-1, 0] = xcoord[0, -1]
    poly[-1, 1] = zmin
    # Add polygon patch to plot
    ax.add_patch(patches.Polygon(poly, facecolor=color, edgecolor=color))


def _load_thalweg(depths, var, lons, lats, thalweg_points):
    """Returns depths, cummulative distance and variable along thalweg.

    :arg depths: depth array for variable. Can be 1D or 3D.
    :type depths: numpy array

    :arg var: 3D variable
    :type var: numpy array, shape (40, 898, 398)

    :arg lons: full NEMO longitude
    :type lons: numpy array, shape (898, 398)

    :arg lons: full NEMO latitude
    :type lats: numpy array, shape (898, 398)

    :arg thalweg_points: indices for the thalweg
    :type thalweg_points: 2D numpy array

    :returns: dep_thal, xx_thal, var_thal, all the same shape
    (depth, thalweg length)
    """

    lons_thal = lons[thalweg_points[:, 0], thalweg_points[:, 1]]
    lats_thal = lats[thalweg_points[:, 0], thalweg_points[:, 1]]
    var_thal = var[:, thalweg_points[:, 0], thalweg_points[:, 1]]

    xx_thal = distance_along_curve(lons_thal, lats_thal)
    xx_thal = xx_thal + np.zeros(var_thal.shape)

    if depths.ndim > 1:
        dep_thal = depths[:, thalweg_points[:, 0], thalweg_points[:, 1]]
    else:
        dep_thal, _ = np.meshgrid(depths, xx_thal[0, :])
        dep_thal = dep_thal.T
    return dep_thal, xx_thal, var_thal


def _fill_in_bathy(variable, mesh_mask, thalweg_pts):
    """For each horizontal point in variable, fill in first vertically masked
    point with the value just above.
    Use mbathy in mesh_mask file to determine level of vertical masking

    :arg variable: the variable to be filled
    :type variable: 2D numpy array

    :arg mesh_mask: NEMO mesh_mask file
    :type mesh_mask: netCDF handle

    :arg thalweg_pts: indices for the thalweg
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
    :type lons: numpy array

    :arg lats: latitude points
    :type lats: numpy array

    :returns: dist, a numpy array with distance along track in km
    """
    dist = [0]
    for i in np.arange(1, lons.shape[0]):
        newdist = dist[i-1] + tidetools.haversine(lons[i], lats[i],
                                                  lons[i-1], lats[i-1])
        dist.append(newdist)
    dist = np.array(dist)
    return dist
