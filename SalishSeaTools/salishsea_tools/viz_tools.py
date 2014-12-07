# Copyright 2013-2014 The Salish Sea MEOPAR contributors
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

"""A collection of Python functions to do routine tasks associated with
plotting and visualization.
"""
from __future__ import division

import netCDF4 as nc
import numpy as np


__all__ = ['calc_abs_max', 'plot_coastline', 'set_aspect']


def calc_abs_max(array):
    """Return the maximum absolute value in the array.

    :arg array: Array to find the maximum absolute value of.
    :type array: :py:class:`numpy.ndarray` or :py:class:`netCDF4.Dataset`

    :returns: Maximum absolute value
    :rtype: :py:class:`numpy.float32`
    """
    return np.absolute(array.flatten()[np.absolute(array).argmax()])


def plot_coastline(
    axes,
    bathymetry,
    coords='grid',
    isobath=0,
    xslice=None,
    yslice=None,
    color='black',
):
    """Plot the coastline contour line from bathymetry on the axes.

    The bathymetry data may be specified either as a file path/name,
    or as a :py:class:`netCDF4.Dataset` instance.
    If a file path/name is given it is opened and read into a
    :py:class:`netCDF4.Dataset` so,
    if this function is being called in a loop,
    it is best to provide it with a bathymetry dataset to avoid
    the overhead of repeated file reads.

    :arg axes: Axes instance to plot the coastline contour line on.
    :type axes: :py:class:`matplotlib.axes.Axes`

    :arg bathymetry: File path/name of a netCDF bathymetry data file
                     or a dataset object containing the bathymetry data.
    :type bathymetry: str or :py:class:`netCDF4.Dataset`

    :arg coords: Type of plot coordinates to set the aspect ratio for;
                 either :kbd:`grid` (the default) or :kbd:`map`.
    :type coords: str

    :arg isobath: Depth to plot the contour at; defaults to 0.
    :type isobath: float

    :arg xslice: X dimension slice to defined the region for which the
                 contour is to be calculated;
                 defaults to :kbd:`None` which means the whole domain.
                 If an xslice is given,
                 a yslice value is also required.
    :type xslice: :py:class:`numpy.ndarray`

    :arg yslice: Y dimension slice to defined the region for which the
                 contour is to be calculated;
                 defaults to :kbd:`None` which means the whole domain.
                 If a yslice is given,
                 an xslice value is also required.
    :type yslice: :py:class:`numpy.ndarray`

    :arg color: Matplotlib colour argument
    :type color: str, float, rgb or rgba tuple

    :returns: Contour line set
    :rtype: :py:class:`matplotlib.contour.QuadContourSet`
    """
    if any((
        xslice is None and yslice is not None,
        xslice is not None and yslice is None,
    )):
        raise ValueError('Both xslice and yslice must be specified')
    if not hasattr(bathymetry, 'variables'):
        bathy = nc.Dataset(bathymetry)
    else:
        bathy = bathymetry
    depths = bathy.variables['Bathymetry']
    if coords == 'map':
        lats = bathy.variables['nav_lat']
        lons = bathy.variables['nav_lon']
        if xslice is None and yslice is None:
            contour_lines = axes.contour(
                np.array(lons), np.array(lats), np.array(depths), 
                [isobath], colors=color)
        else:
            contour_lines = axes.contour(
                lons[yslice, xslice], lats[yslice, xslice],
                depths[yslice, xslice].data, [isobath], colors=color)
    else:
        if xslice is None and yslice is None:
            contour_lines = axes.contour(
                np.array(depths), [isobath], colors=color)
        else:
            contour_lines = axes.contour(
                xslice, yslice, depths[yslice, xslice].data,
                [isobath], colors=color)
    if not hasattr(bathymetry, 'variables'):
        bathy.close()
    return contour_lines


def plot_land_mask(
    axes,
    bathymetry,
    coords='grid',
    isobath=0,
    xslice=None,
    yslice=None,
    color='black',
):
    """Plot land areas from bathymetry as solid colour ploygons on the axes.

    The bathymetry data may be specified either as a file path/name,
    or as a :py:class:`netCDF4.Dataset` instance.
    If a file path/name is given it is opened and read into a
    :py:class:`netCDF4.Dataset` so,
    if this function is being called in a loop,
    it is best to provide it with a bathymetry dataset to avoid
    the overhead of repeated file reads.

    :arg axes: Axes instance to plot the land mask ploygons on.
    :type axes: :py:class:`matplotlib.axes.Axes`

    :arg bathymetry: File path/name of a netCDF bathymetry data file
                     or a dataset object containing the bathymetry data.
    :type bathymetry: str or :py:class:`netCDF4.Dataset`

    :arg coords: Type of plot coordinates to set the aspect ratio for;
                 either :kbd:`grid` (the default) or :kbd:`map`.
    :type coords: str

    :arg isobath: Depth to plot the land mask at; defaults to 0.
    :type isobath: float

    :arg xslice: X dimension slice to defined the region for which the
                 land mask is to be calculated;
                 defaults to :kbd:`None` which means the whole domain.
                 If an xslice is given,
                 a yslice value is also required.
    :type xslice: :py:class:`numpy.ndarray`

    :arg yslice: Y dimension slice to defined the region for which the
                 land maks is to be calculated;
                 defaults to :kbd:`None` which means the whole domain.
                 If a yslice is given,
                 an xslice value is also required.
    :type yslice: :py:class:`numpy.ndarray`

    :arg color: Matplotlib colour argument
    :type color: str, float, rgb or rgba tuple

    :returns: Contour ploygon set
    :rtype: :py:class:`matplotlib.contour.QuadContourSet`
    """
    if any((
        xslice is None and yslice is not None,
        xslice is not None and yslice is None,
    )):
        raise ValueError('Both xslice and yslice must be specified')
    if not hasattr(bathymetry, 'variables'):
        bathy = nc.Dataset(bathymetry)
    else:
        bathy = bathymetry
    depths = bathy.variables['Bathymetry']
    contour_interval = [-0.01, isobath + 0.01]
    if coords == 'map':
        lats = bathy.variables['nav_lat']
        lons = bathy.variables['nav_lon']
        if xslice is None and yslice is None:
            contour_fills = axes.contourf(
                np.array(lons), np.array(lats), np.array(depths), 
                contour_interval, colors=color)
        else:
            contour_fills = axes.contourf(
                lons[yslice, xslice], lats[yslice, xslice],
                depths[yslice, xslice].data, contour_interval, colors=color)
    else:
        if xslice is None and yslice is None:
            contour_fills = axes.contourf(np.array(depths), 
                                          contour_interval, colors=color)
        else:
            contour_fills = axes.contourf(
                xslice, yslice, depths[yslice, xslice].data,
                contour_interval, colors=color)
    if not hasattr(bathymetry, 'variables'):
        bathy.close()
    return contour_fills


def set_aspect(
    axes,
    aspect=5/4.4,
    coords='grid',
    lats=None,
    adjustable='box-forced',
):
    """Set the aspect ratio for the axes.

    This is a thin wrapper on the :py:meth:`matplotlib.axes.Axes.set_aspect`
    method.
    Its primary purpose is to free the user from needing to remember the
    5/4.4 nominal aspect ratio for the Salish Sea NEMO model grid,
    and the formula for the aspect ratio based on latitude for map
    coordinates.
    It also sets the axes aspect ratio with :py:attr:`adjustable='box-forced'`
    so that the axes can be shared if desired.

    :arg axes: Axes instance to set the aspect ratio of.
    :type axes: :py:class:`matplotlib.axes.Axes`

    :arg aspect: Aspect ratio.
    :type aspect: float

    :arg coords: Type of plot coordinates to set the aspect ratio for;
                 either :kbd:`grid` (the default) or :kbd:`map`.
    :type coords: str

    :arg lats: Array of latitude values to calculate the aspect ratio
                    from; only required when :kbd:`coordinates='map'`.
    :type lats: :py:class:`numpy.ndarray`

    :arg adjustable: How to adjust the axes box.
    :type adjustable: str

    :returns: Aspect ratio.
    :rtype: float

    .. note::

        To explicitly set the aspect ratio for map coordinates
        (instead of calculating it from latitudes)
        set :kbd:`aspect` to the aspect ratio,
        :kbd:`coords='map'`,
        and use the default :kbd:`lats=None`.
    """
    if coords == 'map' and lats is not None:
        aspect = 1 / np.cos(np.median(lats) * np.pi / 180)
    axes.set_aspect(aspect, adjustable=adjustable)
    return aspect


def unstagger(ugrid, vgrid):
    """Interpolate u and v component values to values at grid cell centres.

    The shapes are the returned arrays are 1 less than those of
    the input arrays in the y and x dimensions.

    :arg ugrid: u velocity component values with axes (..., y, x)
    :type ugrid: :py:class:`numpy.ndarray`

    :arg vgrid: v velocity component values with axes (..., y, x)
    :type vgrid: :py:class:`numpy.ndarray`

    :returns u, v: u and v component values at grid cell centres
    :rtype: 2-tuple of :py:class:`numpy.ndarray`
    """
    u = np.add(ugrid[..., :-1], ugrid[..., 1:]) / 2
    v = np.add(vgrid[..., :-1, :], vgrid[..., 1:, :]) / 2
    return u[..., 1:, :], v[..., 1:]
