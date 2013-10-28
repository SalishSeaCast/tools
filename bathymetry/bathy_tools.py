"""A collection of functions for viewing and manipulating
netCDF bathymetry files.
"""
from __future__ import (
    division,
    print_function,
)
"""
Copyright 2013 The Salish Sea MEOPAR contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from matplotlib.colors import BoundaryNorm
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np


def show_dimensions(dataset):
    """Print the dimensions of the netCDF dataset.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    for dim in dataset.dimensions.itervalues():
        print(dim)


def show_variables(dataset):
    """Print the variable names in the netCDF dataset as a list.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    print(dataset.variables.keys())


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
    print(depths[jctr+5:jctr-5:-1, ictr-5:ictr+5])
