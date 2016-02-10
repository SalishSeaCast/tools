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

"""A library of Python functions for viewing and manipulating
netCDF bathymetry files.
"""
from __future__ import (
    division,
    print_function,
)

from matplotlib.colors import BoundaryNorm
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np

from salishsea_tools import nc_tools


def show_global_attrs(dataset):
    """Print the global attributes of the netCDF dataset.

    .. note::

        This function is deprecated.
        Use :py:func:`nc_tools.show_dataset_attrs` instead.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    nc_tools.show_dataset_attrs(dataset)


def show_dimensions(dataset):
    """Print the dimensions of the netCDF dataset.

    .. note::

        This function is deprecated.
        Use :py:func:`nc_tools.show_dimensions` instead.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    nc_tools.show_dimensions(dataset)


def show_variables(dataset):
    """Print the variable names in the netCDF dataset as a list.

    .. note::

        This function is deprecated.
        Use :py:func:`nc_tools.show_variables` instead.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    nc_tools.show_variables(dataset)


def min_mid_max(var):
    """Return the minimum, median, and maximum values of var as a tuple.

    Especially useful when applied to latitude and longitude variables.

    :arg dataset: netcdf variable object
    :type dataset: :py:class:`netCDF4.Variable`
    """
    return np.min(var), np.median(var), np.max(var)


def plot_colourmesh(
    dataset,
    title,
    fig_size=(9, 9),
    axis_limits=None,
    colour_map='winter_r',
    bins=15,
    land_colour='#edc9af',
):
    """Create a colour-mesh plot of a bathymetry dataset
    on a longitude/latitude axis.

    :arg dataset: netcdf dataset object containing the bathymetry
    :type dataset: :py:class:`netCDF4.Dataset`

    :arg title: Title for the plot
    :type title: str

    :arg fig_size: Size of the figure
    :type fig_size: 2-tuple

    :arg axis_limits: Axis limits for the plt (xmin, xmax, ymin, ymax);
                      defaults to those calculated by :py:obj:`matplotlib`
    :type axis_limits: 4-tuple

    :arg colour_map: :py:obj:`matplotlib` colour map name
    :type colour_map: str

    :arg bins: Number of level bins for the colour map
    :type bins: int

    :arg land_colour: Colour to use for land regions;
                      i.e. those which the depth is undefined in the
                      dataset's :py:const:`Bathymetry` variable masked array
    :type land_colour: str

    :returns: Figure object containing the plot
    :rtype: :py:class:`matplotlib.figure.Figure`
    """
    lats = dataset.variables['nav_lat']
    lons = dataset.variables['nav_lon']
    depths = dataset.variables['Bathymetry']
    fig = plt.figure(figsize=fig_size)
    set_aspect_ratio(lats)
    plt.title(title)
    cmap, norm = prep_colour_map(
        depths, limits=(0, np.max(depths)), colour_map=colour_map, bins=bins)
    cmap.set_bad(land_colour)
    plt.pcolormesh(lons[:], lats[:], depths[:], cmap=cmap, norm=norm)
    if axis_limits is not None:
        plt.axis(axis_limits)
    cbar = plt.colorbar(shrink=0.8)
    cbar.set_label('Depth [m]')
    return fig


def plot_colourmesh_zoom(
    dataset,
    centre,
    half_width=5,
    fig_size=(9, 9),
    colour_map='copper_r',
    bins=15,
    land_colour='white',
):
    """Create a colour-mesh plot of a bathymetry dataset
    on a grid point axis.

    The plot extends half_width grid points in each direction from centre.

    :arg dataset: netcdf dataset object containing the bathymetry
    :type dataset: :py:class:`netCDF4.Dataset`

    :arg centre: Grid point to centre the plot at
    :type centre: 2-tuple

    :arg half_width: Number of grid points from centre to the edge
                     of the plot
    :type half_width: int

    :arg fig_size: Size of the figure
    :type fig_size: 2-tuple

    :arg colour_map: :py:obj:`matplotlib` colour map name
    :type colour_map: str

    :arg bins: Number of level bins for the colour map
    :type bins: int

    :arg land_colour: Colour to use for land regions;
                      i.e. those which the depth is undefined in the
                      dataset's :py:const:`Bathymetry` variable masked array
    :type land_colour: str
    """
    lats = dataset.variables['nav_lat']
    depths = dataset.variables['Bathymetry']
    plt.figure(figsize=fig_size)
    set_aspect_ratio(lats)
    ictr, jctr = centre
    region_depths = depths[
        jctr+half_width:jctr-half_width:-1,
        ictr-half_width:ictr+half_width
    ]
    cmap, norm = prep_colour_map(
        depths, limits=(0, np.max(region_depths)), colour_map=colour_map, bins=bins)
    cmap.set_bad(land_colour)
    plt.pcolormesh(depths[:], cmap=cmap, norm=norm)
    cbar = plt.colorbar()
    cbar.set_label('Depth [m]')
    plt.axis((ictr-half_width, ictr+half_width,
             jctr-half_width, jctr+half_width))


def prep_colour_map(
        depths,
        limits=None,
        centre=None,
        half_width=5,
        colour_map='copper_r',
        bins=15,
):
    """Returns cmap and norm elements of a colourmap for the
    netCDF depths variable.

    If limits is None (the default) the limits are set to
    (0, max depth in centre +/- half_width).

    :arg depths: netcdf variable object containing the depths
    :type depths: :py:class:`netCDF4.Variable`

    :arg limits: Minimum and maximum depths for colour map
    :type limits: 2-tuple

    :arg centre: Grid point to centre the plot at
    :type centre: 2-tuple

    :arg half_width: Number of grid points from centre to the edge
                     of the plot
    :type half_width: int

    :arg colour_map: :py:obj:`matplotlib` colour map name
    :type colour_map: str

    :arg bins: Number of level bins for the colour map
    :type bins: int
    """
    if limits is None:
        ictr, jctr = centre
        region = depths[
            jctr+half_width:jctr-half_width:-1,
            ictr-half_width:ictr+half_width
        ]
        limits = (0, np.max(region))
    levels = MaxNLocator(nbins=bins).tick_values(*limits)
    cmap = plt.get_cmap(colour_map)
    norm = BoundaryNorm(levels, ncolors=cmap.N)
    return cmap, norm


def set_aspect_ratio(lats):
    """Set the plot axis aspect ratio based on the median latitude.

    :arg lats: netcdf variable object containing the latitudes
    :type lats: :py:class:`netCDF4.Variable`
    """
    ax = plt.axes()
    ax.set_aspect(1 / np.cos(np.median(lats) * np.pi / 180))


def show_region_depths(depths, centre, half_width=5):
    """Print the depths for a region extending half_width grid points
    from centre.

    :arg depths: netcdf variable object containing the depths
    :type depths: :py:class:`netCDF4.Variable`

    :arg centre: Grid point to centre the plot at
    :type centre: 2-tuple

    :arg half_width: Number of grid points from centre to the edge
                     of the plot
    :type half_width: int
    """
    ictr, jctr = centre
    print(depths[
        jctr+half_width:jctr-half_width:-1,
        ictr-half_width:ictr+half_width])


def smooth(depths, max_norm_depth_diff=0.8, smooth_factor=0.2):
    """Smooth the bathymetry by successively adjusting depths
    that have the greatest normalized difference until all of those
    differences are below a max_norm_depth_diff.

    :arg depths: netcdf variable object containing the depths
    :type depths: :py:class:`netCDF4.Variable`

    :arg max_norm_depth_diff: Threshold normalized depth difference to
                              smooth to.
    :type max_norm_depth_diff: float

    :arg smooth_factor: Fraction of the average depth to change
                        the depths by
    :type smooth_factor: float

    :returns: netcdf variable object containing the depths
    :rtype: :py:class:`netCDF4.Variable`
    """
    diffs_lat, lat_ij, diffs_lon, lon_ij = choose_steepest_cells(depths)
    max_diff = np.maximum(diffs_lat[lat_ij], diffs_lon[lon_ij])
    while max_diff > max_norm_depth_diff:
        if diffs_lat[lat_ij] > diffs_lon[lon_ij]:
            i, j = lat_ij
            depths[lat_ij], depths[i+1, j] = smooth_neighbours(
                smooth_factor, depths[lat_ij], depths[i+1, j])
        else:
            i, j = lon_ij
            depths[lon_ij], depths[i, j+1] = smooth_neighbours(
                smooth_factor, depths[lon_ij], depths[i, j+1])
        diffs_lat, lat_ij, diffs_lon, lon_ij = choose_steepest_cells(depths)
        max_diff = np.maximum(diffs_lat[lat_ij], diffs_lon[lon_ij])
    return depths


def choose_steepest_cells(depths):
    """Choose the grid cells with the greatest normalized depth
    differences in the latitude and longitude directions.

    :arg depths: netcdf variable object containing the depths
    :type depths: :py:class:`netCDF4.Variable`

    :returns: Normalized depth difference field in the latitude direction,
              indices of the grid point with the greatest latitude
              direction difference,
              normalized depth difference field in the longitude direction,
              and indices of the grid point with the greatest longitude
              direction difference.
    :rtype: 4-tuple
    """
    diffs_lat = calc_norm_depth_diffs(depths, delta_lat=1, delta_lon=0)
    lat_ij = argmax(diffs_lat)
    diffs_lon = calc_norm_depth_diffs(depths, delta_lat=0, delta_lon=1)
    lon_ij = argmax(diffs_lon)
    return diffs_lat, lat_ij, diffs_lon, lon_ij


def smooth_neighbours(smooth_factor, depth1, depth2):
    """Adjust a pair of depths by smooth_factor times their average.

    :arg smooth_factor: Fraction of the average depth to change
                        the depths by
    :type smooth_factor: float

    :arg depth1: First depth to adjust
    :type depth1: float

    :arg depth2: Second depth to adjust
    :type depth2: float

    :returns: Adjusted depths
    :rtype: 2-tuple
    """
    avg = (depth1 + depth2) / 2
    change = smooth_factor if depth1 < depth2 else -smooth_factor
    depth1 += change * avg
    depth2 -= change * avg
    return depth1, depth2


def calc_norm_depth_diffs(depths, delta_lat, delta_lon):
    """Calculate normalized depth differences between each depth
    and the depth delta_lat and delta_lon grid points away.

    :arg depths: netcdf variable object containing the depths
    :type depths: :py:class:`netCDF4.Variable`

    :arg delta_lat: Number of grid point in the latitude direction
                    to calculate the difference over
    :type delta_lat: int

    :arg delta_lon: Number of grid point in the longitude direction
                    to calculate the difference over
    :type delta_lon: int

    :returns: Normalized depth difference field for the bathymetry
    :rtype: :py:class:`netCDF4.Variable`
    """
    jmax, imax = depths.shape
    offset_depths = depths[:jmax-delta_lat, :imax-delta_lon]
    avg_depths = (depths[delta_lat:, delta_lon:] + offset_depths) / 2
    delta_depths = depths[delta_lat:, delta_lon:] - offset_depths
    return np.abs(delta_depths / avg_depths)


def argmax(depths):
    """Return the indices of the maximum value in depths.

    :arg depths: netcdf variable object containing the depths
    :type depths: :py:class:`netCDF4.Variable`

    :returns: Indices of the maximum value in depths
    :rtype: 2-tuple
    """
    i, j = np.unravel_index(np.argmax(depths), depths.shape)
    return i, j


def zero_jervis_end(depths):
    """Set the depths to zero in the area at the end of Jervis Inlet
    where the Cascadia bathymetry source data are deficient.

    :arg depths: netcdf variable object containing the depths
    :type depths: :py:class:`netCDF4.Variable`

    :returns: netcdf variable object containing the depths
    :rtype: :py:class:`netCDF4.Variable`
    """
    depths[650:651+1, 310:320] = 0.
    depths[647:649+1, 312:320] = 0.
    return depths


def zero_toba_region(depths):
    """Set the depths to zero in the Toba Inlet region where
    the Cascadia bathymetry source data are deficient.

    :arg depths: netcdf variable object containing the depths
    :type depths: :py:class:`netCDF4.Variable`

    :returns: netcdf variable object containing the depths
    :rtype: :py:class:`netCDF4.Variable`
    """
    depths[746, 243:] = 0.
    depths[747:756+1, 240:] = 0.
    depths[757:763+1, 235:] = 0.
    depths[763:766+1, 220:] = 0.
    depths[766:771, 213:] = 0.
    depths[771, 189:] = 0.
    depths[772, 188:] = 0.
    depths[773:774+1, 189:] = 0.
    depths[775:784+1, 190:] = 0.
    depths[785:788+1, 198:] = 0.
    depths[789:791+1, 199:] = 0.
    return depths
