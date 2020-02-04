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
import datetime

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches
from salishsea_tools import geo_tools, nc_tools


def contour_thalweg(
    axes, var, bathy, mesh_mask, clevels=None,
    mesh_mask_depth_var='gdept_0', cmap='hsv', land_colour='burlywood',
    xcoord_distance=True,
    thalweg_file='/home/sallen/MEOPAR/Tools/bathymetry/thalweg_working.txt',
    cbar_args=None,
    mesh_args=None,
    method='contourf'
):
    """Contour the data stored in var along the domain thalweg.

    :arg axes: Axes instance to plot thalweg contour on.
    :type axes: :py:class:`matplotlib.axes.Axes`

    :arg var: Salish Sea NEMO model results variable to be contoured
    :type var: :py:class:`numpy.ndarray`

    :arg bathy: Salish Sea NEMO model bathymetry dataset
    :type bathy: :py:class:`netCDF4.Dataset`

    :arg mesh_mask: Salish Sea NEMO model mesh_mask dataset
    :type mesh_mask: :py:class:`netCDF4.Dataset`

    :arg clevels: argument for determining contour levels. Choices are
                  1. 'salinity' or 'temperature' for pre-determined levels
                  used in nowcast.
                  2. an integer N, for N automatically determined levels.
                  3. a sequence V of contour levels, which must be in
                  increasing order.
    :type clevels: str or int or iterable

    :arg str mesh_mask_depth_var: name of depth variable in :kbd:`mesh_mask`
                                  that is appropriate for :kbd:`var`;
                                  defaults to :kbd:`gdept_0` for NEMO-3.6
                                  tracer variables.

    :arg str cmap: matplotlib colormap

    :arg str land_colour: matplotlib colour for land

    :arg xcoord_distance: plot along thalweg distance (True) or index (False)
    :type xcoord_distance: boolean

    :arg thalweg_file: Path and file name to read the array of
                       thalweg grid points from.
    :type thalweg_file: str

    :arg dict cbar_args: Additional arguments to be passed to the cbar
                         function (fraction, pad, etc.)

    :arg dict mesh_args: Additional arguments to be passed to the contourf
                         or pcolormesh function

    : arg string method: method to use for data display: defaults to
                         'contourf' but 'pcolormesh' is also accepted

    :returns: matplotlib colorbar object
    """
    thalweg_pts = np.loadtxt(thalweg_file, delimiter=' ', dtype=int)
    depth = mesh_mask.variables[mesh_mask_depth_var][:]
    dep_thal, distance, var_thal = load_thalweg(
        depth[0, ...], var, bathy['nav_lon'][:], bathy['nav_lat'][:],
        thalweg_pts)
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

    if method == 'pcolormesh':
        if mesh_args is None:
            mesh = axes.pcolormesh(xx_thal, dep_thal, var_plot, cmap=cmap)
        else:
            mesh = axes.pcolormesh(xx_thal, dep_thal, var_plot, cmap=cmap, **mesh_args)
        axes.set_xlim((np.min(xx_thal),np.max(xx_thal)))
    else:
        if mesh_args is None:
            mesh = axes.contourf(xx_thal, dep_thal, var_plot, clevels, cmap=cmap,
                         extend='both')
        else:
            mesh = axes.contourf(xx_thal, dep_thal, var_plot, clevels, cmap=cmap,
                         extend='both', **mesh_args)
    _add_bathy_patch(
        xx_thal, bathy['Bathymetry'][:], thalweg_pts, axes, color=land_colour)
    if cbar_args is None:
        cbar = plt.colorbar(mesh, ax=axes)
    else:
        cbar = plt.colorbar(mesh, ax=axes, **cbar_args)
    axes.invert_yaxis()
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
    """Returns depths, cumulative distance and variable along thalweg.

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

    xx_thal = geo_tools.distance_along_curve(lons_thal, lats_thal)
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

def contour_layer_grid(axes,data,mask,clevels=10,lat=None,lon=None,cmap=None,var_name=None,
                       land_colour='burlywood',is_depth_avg=False,is_pcolmesh=False,title='',cbar_args=None,
):
    """Contour 2d data at an arbitrary klevel on the model grid

    :arg axes: Axes instance to plot thalweg contour on.
    :type axes: :py:class:`matplotlib.axes.Axes`

    :arg data: 2D array to be contoured at level k
    :type data: :py:class:`numpy.ndarray`

    :arg klev: Index of k-level along which to contour
    :type klev: int

    :arg mask: Mask array with same dimensions as data
    :type mask: :py:class:`numpy.ndarray`

    :arg clevels: argument for determining contour levels. Choices are
                  1. an integer N, for N automatically determined levels.
                  2. a sequence V of contour levels, which must be in
                  increasing order.
    :type clevels: str or int or iterable

    :arg lon: Array of longitudes with same length as x dimension of data.
    :type lon: :py:class:`numpy.ndarray`

    :arg lat: Array of longitudes with same length as x dimension of data.
    :type lat: :py:class:`numpy.ndarray`

    :arg str cmap: matplotlib colormap

    :arg str var_name: Name of variable to plot. Necesssary if cmap=None.

    :arg str land_colour: matplotlib colour for land

    :arg is_depth_avg: True if data is a depth averaged field (default is False).
    :type is_depth_avg: boolean

    :arg is_pcolmesh: plot a pcolormesh (True) instead of a contourf (default).
    :type is_pcolmesh: boolean

    :arg str title: Title string

    :arg dict cbar_args: Additional arguments to be passed to the cbar
                         function (fraction, pad, etc.)

    :returns: matplotlib colorbar object
    """
    mdata = np.ma.masked_where(mask==0,data)

    viz_tools.set_aspect(axes)

    if cmap == None:
        cbMIN, cbMAX, cmap = visualisations.retrieve_cmap(var_name,is_depth_avg)
        cmap = plt.get_cmap(cmocean.cm.algae)

    if is_pcolmesh:
        mesh = axes.pcolormesh(mdata, cmap=cmap)
    else:
        mesh= axes.contourf(mdata,clevels,cmap=cmap)

    axes.set_xlabel('X index')
    axes.set_ylabel('Y index')
    axes.set_title(title)

    axes.set_axis_bgcolor(land_colour)


    if cbar_args is None:
        cbar = plt.colorbar(mesh, ax=axes)
    else:
        cbar = plt.colorbar(mesh, ax=axes, **cbar_args)

    return cbar


def plot_drifters(ax, DATA, DRIFT_OBJS=None, color='red', cutoff=24, zorder=15):
    """Plot a drifter track from ODL Drifter observations.

    :arg time_ind: Time index (current drifter position, track will be visible
        up until this point, ex. 'YYYY-mmm-dd HH:MM:SS', format is flexible)
    :type time_ind: str or :py:class:`datetime.datetime`

    :arg ax: Axis object
    :type ax: :py:class:`matplotlib.pyplot.axes`

    :arg DATA: Drifter track dataset
    :type DATA: :py:class:`xarray.Dataset`

    :arg color: Drifter track color
    :type color: str

    :arg cutoff: Time threshold for color plotting (hours)
    :type cutoff: integer

    :arg zorder: Plotting layer specifier
    :type zorder: integer

    :returns: Dictionary of line objects
    :rtype: dict > :py:class:`matplotlib.lines.Line2D`
    """

    if DATA.time.shape[0] > 0:

        # Convert time boundaries to datetime.datetime to allow operations/slicing
        starttime = nc_tools.xarraytime_to_datetime(DATA.time[ 0])
        endtime   = nc_tools.xarraytime_to_datetime(DATA.time[-1])

        # Color plot cutoff
        time_cutoff = endtime - datetime.timedelta(hours=cutoff)

        if DRIFT_OBJS is not None: # --- Update line objects only

            # Plot drifter track (gray)
            DRIFT_OBJS['L_old'][0].set_data(
                DATA.lon.sel(time=slice(starttime, time_cutoff)),
                DATA.lat.sel(time=slice(starttime, time_cutoff)))

            # Plot drifter track (color)
            DRIFT_OBJS['L_new'][0].set_data(
                DATA.lon.sel(time=slice(time_cutoff, endtime)),
                DATA.lat.sel(time=slice(time_cutoff, endtime)))

            # Plot drifter position
            DRIFT_OBJS['P'][0].set_data(
                DATA.lon.sel(time=endtime, method='nearest'),
                DATA.lat.sel(time=endtime, method='nearest'))

        else: # ------------------------ Plot new line objects instances

            # Define drifter objects dict
            DRIFT_OBJS = {}

            # Plot drifter track (gray)
            DRIFT_OBJS['L_old'] = ax.plot(
                DATA.lon.sel(time=slice(starttime, time_cutoff)),
                DATA.lat.sel(time=slice(starttime, time_cutoff)),
                '-', linewidth=2, color='gray', zorder=zorder)

            # Plot drifter track (color)
            DRIFT_OBJS['L_new'] = ax.plot(
                DATA.lon.sel(time=slice(time_cutoff, endtime)),
                DATA.lat.sel(time=slice(time_cutoff, endtime)),
                '-', linewidth=2, color=color, zorder=zorder+1)

            # Plot drifter position
            DRIFT_OBJS['P'] = ax.plot(
                DATA.lon.sel(time=endtime, method='nearest'),
                DATA.lat.sel(time=endtime, method='nearest'),
                'o', color=color, zorder=zorder+2)

    else:

        if DRIFT_OBJS is not None: # --- Update line objects only

            # Update drifter tracks
            DRIFT_OBJS['L_old'][0].set_data([], []) # gray
            DRIFT_OBJS['L_new'][0].set_data([], []) # color
            DRIFT_OBJS['P'    ][0].set_data([], []) # position

        else:

            DRIFT_OBJS = {}
            DRIFT_OBJS['L_old'] = ax.plot([], [], '-',
                linewidth=2, color='gray', zorder=zorder)

            # Plot drifter track (color)
            DRIFT_OBJS['L_new'] = ax.plot([], [], '-',
                linewidth=2, color=color, zorder=zorder+1)

            # Plot drifter position
            DRIFT_OBJS['P'] = ax.plot([], [], 'o', color=color, zorder=zorder+2)

    return DRIFT_OBJS


def create_figure(ax, DATA, coords='map', window=[-125, -122.5, 48, 50]):
    """ Boilerplate figure code like coastline, aspect ratio, axis lims, etc.

    .. note::

        This function is deprecated.
        Call plot formatting functions individually instead.
    """

    raise DeprecationWarning(
        'create_figure has been deprecated. Call plot formatting functions '
        'individually instead.')


def plot_tracers(
    ax, qty, DATA, C=None, coords='map', clim=[0, 35, 1], cmap='jet', zorder=0
):
    """Plot a horizontal slice of NEMO tracers as filled contours.

    .. note::

        This function is deprecated.
        Plot NEMO results directly using `matplotlib.pyplot.contourf` or
        equivalent instead.
    """

    raise DeprecationWarning(
        'plot_tracers has been deprecated. Plot NEMO results directly using '
        'matplotlib.pyplot.contourf or equivalent instead.')



def plot_velocity(
    ax, model, DATA, Q=None, coords='map', processed=False, spacing=5,
    mask=True, color='black', scale=20, headwidth=3, linewidth=0, zorder=5
):
    """Plot a horizontal slice of NEMO or GEM velocities as quiver objects.
    Accepts subsampled u and v fields via the **processed** keyword
    argument.

    .. note::

        This function is deprecated.
        Plot NEMO results directly using `matplotlib.pyplot.quiver` or
        equivalent instead.
    """

    raise DeprecationWarning(
        'plot_velocity has been deprecated. Plot NEMO results directly using '
        'matplotlib.pyplot.quiver or equivalent instead.')


def retrieve_cmap(varname,deep_bool):
    """takes 2 args:
    string varname - name of a variable from nowcast-green output
    boolean deep_bool - indicates whether the variable is depth-integrated or not
    returns 2 ints(min and max value of range), and string identifying cmap"""

    var_namemap ={'Fraser_tracer': {'varname':'Fraser_tracer'},
              'ammonium': {'varname':'NH4'},
              'NH4': {'varname':'NH4'},
             'biogenic_silicon': {'varname':'bSi'},
              'bSi': {'varname':'bSi'},
             'ciliates': {'varname':'MYRI'},
             'MYRI': {'varname':'MYRI'},
              'diatoms': {'varname':'PHY2'},
              'PHY2': {'varname':'PHY2'},
             'dissolved_organic_nitrogen': {'varname':'dissolved_organic_nitrogen'},
              'flagellates': {'varname':'PHY'},
              'PHY': {'varname':'PHY'},
             'mesozooplankton': {'varname':'MESZ'},
              'MESZ': {'varname':'MESZ'},
              'microzooplankton': {'varname':'MICZ'},
             'MICZ': {'varname':'MICZ'},
              'nitrate': {'varname':'NO3'},
              'NO3': {'varname':'NO3'},
             'particulate_organic_nitrogen': {'varname':'PON'},
              'POC': {'varname':'PON'},
              'PON': {'varname':'PON'},
              'dissolved_organic_nitrogen': {'varname':'DON'},
              'DOC': {'varname':'DON'},
              'DON': {'varname':'DON'},

              'silicon': {'varname':'Si'},
             'Si': {'varname':'Si'}}

    #dictionary of colour ranges
    var_colour_ranges = {

    'Fraser_tracer':{'colorBarMinimum': 0.0, 'colorBarMaximum': 140.0,'cmap': 'turbid'},
    'MESZ': {'colorBarMinimum': 0.0, 'colorBarMaximum': 3.0,'cmap': 'algae'},
    'MICZ': {'colorBarMinimum': 0.0, 'colorBarMaximum': 4.0,'cmap': 'algae'},
    'MYRI': {'colorBarMinimum': 0.0, 'colorBarMaximum': 5.0,'cmap': 'algae'},
    'NH4': {'colorBarMinimum': 0.0, 'colorBarMaximum': 10.0,'cmap': 'matter'},
    'NO3': {'colorBarMinimum': 0.0, 'colorBarMaximum': 40.0,'cmap': 'tempo'},
    'PON': {'colorBarMinimum': 0.0, 'colorBarMaximum': 2.0,'cmap': 'amp'},
    'DON': {'colorBarMinimum': 0.0, 'colorBarMaximum': 20.0,'cmap': 'amp'},
    'O2': {'colorBarMinimum': 0.0, 'colorBarMaximum': 140.0,'cmap': 'turbid'},
    'PHY': {'colorBarMinimum': 0.0, 'colorBarMaximum': 6.0, 'cmap': 'algae'},
    'PHY2': {'colorBarMinimum': 0.0, 'colorBarMaximum': 15.0,'cmap': 'algae'},
    'Si': {'colorBarMinimum': 0.0, 'colorBarMaximum': 70.0,'cmap': 'turbid'},
    'bSi': {'colorBarMinimum': 0.0, 'colorBarMaximum': 70.0,'cmap': 'turbid'},

    'Fraser_tracer_int':{'colorBarMinimum': 0.0, 'colorBarMaximum': 6500,'cmap': 'turbid'},
    'MESZ_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 140,'cmap': 'algae'},
    'MICZ_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 350,'cmap': 'algae'},
    'MYRI_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 75,'cmap': 'algae'},
    'NH4_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 1500,'cmap': 'matter'},
    'NO3_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 24000,'cmap': 'tempo'},
    'PON_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 600,'cmap': 'amp'},
    'DON_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 2500,'cmap': 'amp'},
    'O2_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 1000,'cmap': 'turbid'},
    'PHY_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 100,'cmap': 'algae'},
    'PHY2_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 350,'cmap': 'algae'},
    'Si_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 40000,'cmap': 'turbid'},
    'bSi_int': {'colorBarMinimum': 0.0, 'colorBarMaximum': 40000,'cmap': 'turbid'},
}
    dp = var_namemap[varname]
    vn = dp['varname']
    if (deep_bool == True):
        vn = vn + '_int'

    dict_pull = var_colour_ranges[vn]
    cbMIN = dict_pull['colorBarMinimum']
    print()
    cbMAX = dict_pull['colorBarMaximum']
    cmap_name = dict_pull['cmap']

    return cbMIN, cbMAX, cmap_name
