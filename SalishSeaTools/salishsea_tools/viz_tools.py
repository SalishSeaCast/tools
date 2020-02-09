# Copyright 2013-2016 The Salish Sea MEOPAR contributors
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
from salishsea_tools import geo_tools


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
    server='local',
    zorder=2,
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

    :arg zorder: Plotting layer specifier
    :type zorder: integer

    :returns: Contour line set
    :rtype: :py:class:`matplotlib.contour.QuadContourSet`
    """

    # Index names based on results server
    if server == 'local':
        lon_name = 'nav_lon'
        lat_name = 'nav_lat'
        bathy_name = 'Bathymetry'
    elif server == 'ERDDAP':
        lon_name = 'longitude'
        lat_name = 'latitude'
        bathy_name = 'bathymetry'
    else:
        raise ValueError('Unknown results server name: {}'.format(server))

    if any((
        xslice is None and yslice is not None,
        xslice is not None and yslice is None,
    )):
        raise ValueError('Both xslice and yslice must be specified')
    if not hasattr(bathymetry, 'variables'):
        bathy = nc.Dataset(bathymetry)
    else:
        bathy = bathymetry
    depths = bathy.variables[bathy_name]
    if coords == 'map':
        lats = bathy.variables[lat_name]
        lons = bathy.variables[lon_name]
        if xslice is None and yslice is None:
            contour_lines = axes.contour(
                np.array(lons), np.array(lats), np.array(depths),
                [isobath], colors=color, zorder=zorder)
        else:
            contour_lines = axes.contour(
                lons[yslice, xslice], lats[yslice, xslice],
                depths[yslice, xslice].data, [isobath], colors=color,
                zorder=zorder)
    else:
        if xslice is None and yslice is None:
            contour_lines = axes.contour(
                np.array(depths), [isobath], colors=color, zorder=zorder)
        else:
            contour_lines = axes.contour(
                xslice, yslice, depths[yslice, xslice].data,
                [isobath], colors=color, zorder=zorder)
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
    server='local',
    zorder=1
):
    """Plot land areas from bathymetry as solid colour polygons on the axes.

    The bathymetry data may be specified either as a file path/name,
    or as a :py:class:`netCDF4.Dataset` instance.
    If a file path/name is given it is opened and read into a
    :py:class:`netCDF4.Dataset` so,
    if this function is being called in a loop,
    it is best to provide it with a bathymetry dataset to avoid
    the overhead of repeated file reads.

    :arg axes: Axes instance to plot the land mask polygons on.
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

    :arg zorder: Plotting layer specifier
    :type zorder: integer

    :returns: Contour polygon set
    :rtype: :py:class:`matplotlib.contour.QuadContourSet`
    """

    # Index names based on results server
    if server == 'local':
        lon_name   = 'nav_lon'
        lat_name   = 'nav_lat'
        bathy_name = 'Bathymetry'
    elif server == 'ERDDAP':
        lon_name   = 'longitude'
        lat_name   = 'latitude'
        bathy_name = 'bathymetry'
    else:
        raise ValueError('Unknown results server name: {}'.format(server))

    if any((
        xslice is None and yslice is not None,
        xslice is not None and yslice is None,
    )):
        raise ValueError('Both xslice and yslice must be specified')
    if not hasattr(bathymetry, 'variables'):
        bathy = nc.Dataset(bathymetry)
    else:
        bathy = bathymetry
    depths = bathy.variables[bathy_name]
    contour_interval = [-0.01, isobath + 0.01]
    if coords == 'map':
        lats = bathy.variables[lat_name]
        lons = bathy.variables[lon_name]
        if xslice is None and yslice is None:
            contour_fills = axes.contourf(
                np.array(lons), np.array(lats), np.array(depths), 
                contour_interval, colors=color, zorder=zorder)
        else:
            contour_fills = axes.contourf(
                lons[yslice, xslice], lats[yslice, xslice],
                depths[yslice, xslice].data, contour_interval, colors=color,
                zorder=zorder)
    else:
        if xslice is None and yslice is None:
            contour_fills = axes.contourf(np.array(depths), 
                                          contour_interval, colors=color,
                                          zorder=zorder)
        else:
            contour_fills = axes.contourf(
                xslice, yslice, depths[yslice, xslice].data,
                contour_interval, colors=color, zorder=zorder)
    if not hasattr(bathymetry, 'variables'):
        bathy.close()
    return contour_fills


def plot_boundary(
        ax, grid, mask, dim='depth', index=0, coords='grid',
        color='burlywood', zorder=10
):
    """Plot the land boundary for a given NEMO domain slice.
    
    :arg ax: axes object handle
    :type ax: :py:class:`matplotlib.axes._subplots.AxesSubplot`
    
    :arg grid: NEMO grid variables
    :type grid: :py:class:`xarray.DataSet`
    
    :arg mask: NEMO mask variables
    :type mask: :py:class:`xarray.DataSet`
    
    :arg dim: dimension for slice (one of 'depth', 'x', or 'y')
    :type dim: str
    
    :arg index: slice index (integer for 'x' or 'y', float for 'depth')
    :type index: int or float
    
    :arg coords: 'map' or 'grid'
    :type coords: str
    
    :arg color: land color
    :type color: str
    
    :arg zorder: desired vertical plot layer
    :type zorder: int
    
    :returns: land and coastline contour object handles
    :rtype: :py:class:`matplotlib.contour.QuadContourSet`
    """
    
    # Define depth array and slices
    depth = mask.gdept_1d.isel(t=0)
    dimslice = dim
    indexslice = index
    
    # Determine coordinate system and orientation
    if dim == 'depth':
        dimslice = 'z'
        indexslice = abs(depth.values - index).argmin()
        if coords == 'map':
            dim1, dim2 = grid.nav_lon, grid.nav_lat
        elif coords == 'grid':
            dim1, dim2 = grid.x, grid.y
        else:
            raise ValueError('Unknown coordinate system: {}'.format(coords))
    elif dim == 'y':
        if coords == 'map':
            dim1, dim2 = grid.nav_lon.isel(**{dim: index}), depth
        elif coords == 'grid':
            dim1, dim2 = grid.x, depth
        else:
            raise ValueError('Unknown coordinate system: {}'.format(coords))
    elif dim == 'x':
        if coords == 'map':
            dim1, dim2 = grid.nav_lat.isel(**{dim: index}), depth
        elif coords == 'grid':
            dim1, dim2 = grid.y, depth
        else:
            raise ValueError('Unknown coordinate system: {}'.format(coords))
    else:
        raise ValueError('Unknown dimension: {}'.format(dim))

    # Plot landmask and boundary contour
    patch = ax.contourf(
        dim1, dim2, mask.tmask.isel(**{'t': 0, dimslice: indexslice}),
        [-0.01, 0.01], colors=color, zorder=zorder
    )
    boundary = ax.contour(
        dim1, dim2, mask.tmask.isel(**{'t': 0, dimslice: indexslice}),
        [0], colors='k', zorder=zorder
    )
    
    # Invert depth axis
    if dim == 'x' or dim == 'y':
        ax.invert_yaxis()

    return patch, boundary


def set_aspect(
    axes,
    aspect=5/4.4,
    coords='grid',
    lats=None,
    adjustable='box',
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


def unstagger_xarray(qty, index):
    """Interpolate u, v, or w component values to values at grid cell centres.
    
    Named indexing requires that input arrays are XArray DataArrays.

    :arg qty: u, v, or w component values
    :type qty: :py:class:`xarray.DataArray`
    
    :arg index: index name along which to centre
        (generally one of 'gridX', 'gridY', or 'depth')
    :type index: str

    :returns qty: u, v, or w component values at grid cell centres
    :rtype: :py:class:`xarray.DataArray`
    """
    
    qty = (qty + qty.shift(**{index: 1})) / 2
    
    return qty


def rotate_vel(u_in, v_in, origin='grid'):
    """Rotate u and v component values to either E-N or model grid.

    The origin argument sets the input coordinates ('grid' or 'map')

    :arg u_in: u velocity component values
    :type u_in: :py:class:`numpy.ndarray`

    :arg v_in: v velocity component values
    :type v_in: :py:class:`numpy.ndarray`
    
    :arg origin: Input coordinate system
                 (either 'grid' or 'map', output will be the other)
    :type origin: str

    :returns u_out, v_out: rotated u and v component values
    :rtype: :py:class:`numpy.ndarray`
    """
    
    # Determine rotation direction
    if   origin == 'grid':
        fac =  1
    elif origin == 'map':
        fac = -1
    else:
        raise ValueError('Invalid origin value: {origin}'.format(
            origin=origin))

    # Rotate velocities
    theta_rad = 29 * np.pi / 180
    
    u_out = u_in * np.cos(theta_rad) - fac * v_in * np.sin(theta_rad)
    v_out = u_in * np.sin(theta_rad) * fac + v_in * np.cos(theta_rad)
    
    return u_out, v_out


def rotate_vel2(u_in, v_in, coords, origin="grid"):
    """Rotate u and v component values to either E-N or model grid. The origin
    argument sets the input coordinates ('grid' or 'map').

    This function is an evolution of rotate_vel that uses spherical trig to
    compute the rotation angle at T points rather than assuming 29 degrees
    applies uniformly. For most of the Salish Sea domain the 29 degree
    approximation is reasonable, but it does not work in the compressed Fraser
    River region, hence the need for a per-point angle calculation. The u_in
    and v_in arguments should be unstaggered velocities at T points from
    viz_tools.unstagger() which exclude the first row and column.

    :arg u_in: u velocity component values
    :type u_in: :py:class:`numpy.ndarray`

    :arg v_in: v velocity component values
    :type v_in: :py:class:`numpy.ndarray`

    :arg coords: File path/name to netCDF coordinates file
                 or a dataset object containing the U-point coordinates.
    :type coords: str or :py:class:`netCDF4.Dataset`

    :arg origin: Input coordinate system
                 (either 'grid' or 'map', output will be the other)
    :type origin: str

    :returns u_out, v_out: rotated u and v component values
    :rtype: :py:class:`numpy.ndarray`
    """

    # Determine rotation direction
    if origin == "grid":
        fac = 1
    elif origin == "map":
        fac = -1
    else:
        raise ValueError("Invalid origin value: {origin}".format(origin=origin))

    # Load u-point coordinates
    if hasattr(coords, "variables"):
        cnc = coords
    else:
        cnc = nc.Dataset(coords)
    glamu = cnc["glamu"][0, ...]
    gphiu = cnc["gphiu"][0, ...]

    # Get the value of R that geo_tools.haversine() uses
    R = geo_tools.haversine(0, 0, 0, 1) / np.deg2rad(1)

    # Find angle by spherical trig
    # https://en.wikipedia.org/wiki/Solution_of_triangles#Three_sides_given_.28spherical_SSS.29

    # First point
    xA = glamu[0:-1, 0:-1]
    yA = gphiu[0:-1, 0:-1]
    # Second point
    xB = glamu[0:-1, 1:]
    yB = gphiu[0:-1, 1:]
    # Third point: same longitude as second point, same latitude as first point
    xC = xB
    yC = yA

    # Compute distances, convert to angles
    a = geo_tools.haversine(xB, yB, xC, yC) / R
    b = geo_tools.haversine(xA, yA, xC, yC) / R
    c = geo_tools.haversine(xA, yA, xB, yB) / R

    # A is the angle counterclockwise from due east in radians
    cosA = (np.cos(a) - np.cos(b) * np.cos(c)) / (np.sin(b) * np.sin(c))
    A = np.arccos(cosA)

    # Rotate velocities
    u_out = u_in * np.cos(A) - fac * v_in * np.sin(A)
    v_out = u_in * np.sin(A) * fac + v_in * np.cos(A)

    return u_out, v_out


def rotate_vel_bybearing(u_in, v_in, coords, origin="grid"):
    """Rotate u and v component values to either E-N or model grid. The origin
    argument sets the input coordinates ('grid' or 'map').

    This function is an evolution of rotate_vel that uses a bearing calculation
    based on the coordinates to compute the rotation angle based on
    https://www.movable-type.co.uk/scripts/latlong.html see Bearing
    The u_in and v_in arguments should be on the grid passed in as a dictionary
    in coords

    :arg u_in: u velocity component values
    :type u_in: :py:class:`numpy.ndarray`

    :arg v_in: v velocity component values
    :type v_in: :py:class:`numpy.ndarray`

    :arg coords: dict of latitudes and longitudes
    :type coords: dict

    :arg origin: Input coordinate system
                 (either 'grid' or 'map', output will be the other)
    :type origin: str

    :returns u_out, v_out: rotated u and v component values
    :rtype: :py:class:`numpy.ndarray`
    """

    # Determine rotation direction
    if origin == "grid":
        fac = 1
    elif origin == "map":
        fac = -1
    else:
        raise ValueError("Invalid origin value: {origin}".format(origin=origin))

    longitude = np.array(coords["lon"])
    latitude = np.array(coords["lat"])

    # First point
    xA = np.deg2rad(longitude[:, 0:-1])
    yA = np.deg2rad(latitude[:, 0:-1])
    # Second point
    xB = np.deg2rad(longitude[:, 1:])
    yB = np.deg2rad(latitude[:, 1:])

    # A is the angle counterclockwise from due east in radians
    A = np.empty_like(longitude)

    A[:, 0:-1] = np.arctan2(np.cos(yA) * np.sin(yB) - np.sin(yA) * np.cos(yB) * np.cos(xB-xA), np.sin(xB-xA) * np.cos(yB))
    A[:, -1] = A[:, -2]

    # Rotate velocities
    u_out = u_in * np.cos(A) - fac * v_in * np.sin(A)
    v_out = u_in * np.sin(A) * fac + v_in * np.cos(A)

    return u_out, v_out


def clear_contours(C):
    """Clear contours from an existing plot.
    
    :arg C: contour object handle
    :type C: :py:class:`matplotlib.contour.QuadContourSet`
    """
    
    # Clear previous contours
    for C_obj in C.collections:
        C_obj.remove()
    
    return
