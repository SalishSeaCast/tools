# Copyright 2013-2015 The Salish Sea MEOPAR contributors
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


"""A collection of Python functions to produce comparisons between with the
VENUS nodes and the model results with visualization figures for analysis
of daily nowcast/forecast runs.
"""
from cStringIO import StringIO
import datetime

from dateutil import tz
import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import netCDF4 as nc

from salishsea_tools import (
    nc_tools,
    tidetools as tt,
    viz_tools
)
from salishsea_tools.nowcast import (figures, analyze)

# Plotting colors
model_c = 'MediumBlue'
observations_c = 'DarkGreen'
predictions_c = 'MediumVioletRed'
stations_c = cm.rainbow(np.linspace(0, 1, 7))

# Time shift for plotting in PST
time_shift = datetime.timedelta(hours=-8)
hfmt = mdates.DateFormatter('%m/%d %H:%M')

# Font format
title_font = {
    'fontname': 'Bitstream Vera Sans', 'size': '15', 'color': 'white',
    'weight': 'medium'
}
axis_font = {'fontname': 'Bitstream Vera Sans', 'size': '13', 'color': 'white'}

# Constants defined for the VENUS nodes
# Lat/lon/depth from the VENUS website. Depth is in meters.
# i,j are python grid coordinates as returned from
# tidetools.find_closest_model_point()
SITES = {
    'Vancouver': {
        'lat': 49.2827,
        'lon': -123.1207},
    'VENUS': {
        'East': {
            'lat': 49.0419,
            'lon': -123.3176,
            'depth': 170,
            'i': 283,
            'j': 416},
        'Central': {
            'lat': 49.0401,
            'lon': -123.4261,
            'depth': 300,
            'i': 266,
            'j': 424}
        }
    }


def dateparse(s):
    """Parse the dates from the VENUS files."""

    unaware = datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
    aware = unaware.replace(tzinfo=tz.tzutc())

    return aware


def load_VENUS(station):
    """Loads the most recent State of the Ocean data from the VENUS node
    indicated by station.

    This data set includes pressure, temperature, and salinity among
    other things.
    See: http://venus.uvic.ca/research/state-of-the-ocean/

    :arg station: The name of the station, either "East" or "Central".
    :type station: string

    :returns: DataFrame (data) with the VENUS data
    """

    # Define location
    filename = 'SG-{0}-VIP/VSG-{0}-VIP-State_of_Ocean.txt'.format(station)

    # Access website
    url = 'http://venus.uvic.ca/scripts/log_download.php'
    params = {
        'userid': 'nsoontie@eos.ubc.ca',
        'filename': filename,
    }
    response = requests.get(url, params=params)

    # Parse data
    fakefile = StringIO(response.content)
    data = pd.read_csv(
        fakefile, delimiter=' ,', skiprows=17,
        names=[
            'date', 'pressure', 'pflag', 'temp', 'tflag', 'sal', 'sflag',
            'sigmaT', 'stflag', 'oxygen', 'oflag',
        ],
        parse_dates=['date'], date_parser=dateparse, engine='python')

    return data


def plot_VENUS(ax_sal, ax_temp, station, start, end):
    """Plots a time series of the VENUS data over a date range.

    :arg ax_sal: The axis in which the salinity is displayed.
    :type ax_sal: axis object

    :arg ax_temp: The axis in which the temperature is displayed.
    :type ax_temp: axis object

    :arg station: The name of the station, either "East" or "Central".
    :type station: string

    :arg start: The start date of the plot.
    :type start: datetime object

    :arg end: The end date of the plot.
    :type end: datetime object

    """

    data = load_VENUS(station)
    ax_sal.plot(data.date[:], data.sal, 'r-', label='Observations')
    ax_sal.set_xlim([start, end])
    ax_temp.plot(data.date[:], data.temp, 'r-', label='Observations')
    ax_temp.set_xlim([start, end])


def compare_VENUS(station, grid_T, grid_B, figsize=(6, 10)):
    """Compares the model's temperature and salinity with observations from
    VENUS station.

    :arg station: Name of the station ('East' or 'Central')
    :type station: string

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Time range
    t_orig, t_end, t = figures.get_model_time_variables(grid_T)

    # Bathymetry
    bathy, X, Y = tt.get_bathy_data(grid_B)

    # VENUS data
    fig, (ax_sal, ax_temp) = plt.subplots(2, 1, figsize=figsize, sharex=True)
    fig.patch.set_facecolor('#2B3E50')
    fig.autofmt_xdate()
    lon = SITES['VENUS'][station]['lon']
    lat = SITES['VENUS'][station]['lat']
    depth = SITES['VENUS'][station]['depth']

    # Plotting observations
    plot_VENUS(ax_sal, ax_temp, station, t_orig, t_end)

    # Grid point of VENUS station
    [j, i] = tt.find_closest_model_point(
        lon, lat, X, Y, bathy, allow_land=True)

    # Model data
    sal = grid_T.variables['vosaline'][:, :, j, i]
    temp = grid_T.variables['votemper'][:, :, j, i]
    ds = grid_T.variables['deptht']

    # Interpolating data
    salc = []
    tempc = []
    for ind in np.arange(0, sal.shape[0]):
        salc.append(figures.interpolate_depth(sal[ind, :], ds, depth))
        tempc.append(figures.interpolate_depth(temp[ind, :], ds, depth))

    # Plot model data
    ax_sal.plot(t, salc, '-b', label='Model')
    ax_temp.plot(t, tempc, '-b', label='Model')

    # Axis
    ax_sal.set_title('VENUS {} - {}'.format(station, t[0].strftime('%d-%b-%Y'),
                                            **title_font))
    ax_sal.set_ylim([29, 32])
    ax_sal.set_ylabel('Practical Salinity [psu]', **axis_font)
    ax_sal.legend(loc=0)
    ax_temp.set_ylim([7, 11])
    ax_temp.set_xlabel('Time [UTC]', **axis_font)
    ax_temp.set_ylabel('Temperature [deg C]', **axis_font)
    figures.axis_colors(ax_sal, 'gray')
    figures.axis_colors(ax_temp, 'gray')

    # Text box
    ax_temp.text(0.25, -0.3, 'Observations from Ocean Networks Canada',
                 transform=ax_temp.transAxes, color='white')

    return fig


def unstag_rot(ugrid, vgrid, i, j):
    """Interpolate u and v component values to values at grid cell centre.
    Then rotates the grid cells to align with N/E orientation.

    :arg ugrid: u velocity component values with axes (..., y, x)
    :type ugrid: :py:class:`numpy.ndarray`

    :arg vgrid: v velocity component values with axes (..., y, x)
    :type vgrid: :py:class:`numpy.ndarray`

    :arg station: Name of the station ('East' or 'Central')
    :type station: string

    :returns u_E, v_N, depths: u_E and v_N velocties is the North and East
     directions at the cell center,
    and the depth of the station
    """

    # We need to access the u velocity that is between i and i-1
    u_t = (ugrid[:, :, j, i-1] + ugrid[:, :, j, i]) / 2
    v_t = (vgrid[:, :, j, i] + vgrid[:, :, j-1, i]) / 2
    theta = 29
    theta_rad = theta * np.pi / 180

    u_E = u_t * np.cos(theta_rad) - v_t * np.sin(theta_rad)
    v_N = u_t * np.sin(theta_rad) + v_t * np.cos(theta_rad)

    return u_E, v_N


def unstag_rot_gridded(ugrid, vgrid, station):
    """Interpolate u and v component values to values at grid cell centre.
    Then rotates the grid cells to align with N/E orientation.

    :arg ugrid: u velocity component values with axes (..., y, x)
    :type ugrid: :py:class:`numpy.ndarray`

    :arg vgrid: v velocity component values with axes (..., y, x)
    :type vgrid: :py:class:`numpy.ndarray`

    :arg station: Name of the station ('East' or 'Central')
    :type station: string

    :returns u_E, v_N, depths: u_E and v_N velocties is the North and East
     directions at the cell center,
    and the depth of the station
    """

    # We need to access the u velocity that is between i and i-1
    u_t = (ugrid[:, :, 1, 0] + ugrid[:, :, 1, 1]) / 2
    v_t = (vgrid[:, :, 1, 1] + vgrid[:, :, 0, 1]) / 2
    theta = 29
    theta_rad = theta * np.pi / 180

    u_E = u_t * np.cos(theta_rad) - v_t * np.sin(theta_rad)
    v_N = u_t * np.sin(theta_rad) + v_t * np.cos(theta_rad)

    return u_E, v_N


def plot_vel_NE_gridded(station, grid, figsize=(14, 10)):
    """Plots the hourly averaged North/South and East/West velocities at a chosen
    VENUS node station using data that is calculated every 15 minutes.

    :arg station: Name of the station ('East' or 'Central')
    :type station: string

    :arg grid: Quarter-hourly velocity and tracer results dataset from NEMO.
    :type grid: :class:`netCDF4.Dataset`

    :arg figsize: Figure size (width, height) in inches or 'default'.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """
    u_u = grid.variables['vozocrtx']
    v_v = grid.variables['vomecrty']
    w_w = grid.variables['vovecrtz']
    dep_t = grid.variables['depthv']
    dep_w = grid.variables['depthw']

    u_E, v_N = unstag_rot_gridded(u_u, v_v, station)

    fig, (axu, axv, axw) = plt.subplots(3, 1, figsize=figsize, sharex=True)
    fig.patch.set_facecolor('#2B3E50')

    max_array = np.maximum(abs(v_N), abs(u_E))
    max_speed = np.amax(max_array)
    vmax = max_speed
    vmin = - max_speed
    step = 0.03

    # viz_tools.set_aspect(axu)
    timestamp = nc_tools.timestamp(grid, 0)
    cmap = plt.get_cmap('jet')
    dep_s = SITES['VENUS'][station]['depth']

    axu.invert_yaxis()
    mesh = axu.contourf(
        np.arange(0, 24, 0.25),
        dep_t[:],
        u_E.transpose(),
        np.arange(vmin, vmax, step), cmap=cmap)
    cbar = fig.colorbar(mesh, ax=axu)
    axu.set_ylim([dep_s, 0])
    axu.set_xlim([0, 23])
    axu.set_ylabel('Depth [m]', **axis_font)
    figures.axis_colors(axu, 'white')
    axu.set_title('East/West Velocities at VENUS {node} on {date}'.format(
        node=station, date=timestamp.format('DD-MMM-YYYY')), **title_font)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')
    cbar.set_label('[m/s]', **axis_font)

    axv.invert_yaxis()
    mesh = axv.contourf(
        np.arange(0, 24, 0.25),
        dep_t[:],
        v_N.transpose(),
        np.arange(vmin, vmax, step),
        cmap=cmap)
    cbar = fig.colorbar(mesh, ax=axv)
    axv.set_ylim([dep_s, 0])
    axv.set_xlim([0, 23])
    axv.set_ylabel('Depth [m]', **axis_font)
    figures.axis_colors(axv, 'white')
    axv.set_title('North/South Velocities at VENUS {node} on {date}'.format(
        node=station, date=timestamp.format('DD-MMM-YYYY')), **title_font)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')
    cbar.set_label('[m/s]', **axis_font)

    axw.invert_yaxis()
    mesh = axw.contourf(
        np.arange(0, 24, 0.25), dep_w[:],
        w_w[:, :, 1, 1].transpose(),
        np.arange(vmin/70, vmax/70, step/80),
        cmap=cmap)
    cbar = fig.colorbar(mesh, ax=axw)
    axw.set_ylim([dep_s, 0])
    axw.set_xlim([0, 23])
    axw.set_xlabel('Time [h]', **axis_font)
    axw.set_ylabel('Depth [m]', **axis_font)
    figures.axis_colors(axw, 'white')
    axw.set_title('Vertical Velocities at VENUS {node} on {date}'.format(
        node=station, date=timestamp.format('DD-MMM-YYYY')), **title_font)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')
    cbar.set_label('[m/s]', **axis_font)

    return fig


def VENUS_location(grid_B, figsize=(10, 10)):
    """Plots the location of the VENUS Central and East nodes as well as
    Vancouver as a reference on a bathymetry map.

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    lats = grid_B.variables['nav_lat'][:]
    lons = grid_B.variables['nav_lon'][:]
    bathy = grid_B.variables['Bathymetry'][:]
    levels = np.arange(0, 470, 50)

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    fig.patch.set_facecolor('#2B3E50')
    cmap = plt.get_cmap('winter_r')
    cmap.set_bad('burlywood')
    mesh = ax.contourf(lons, lats, bathy, levels, cmap=cmap, extend='both')
    cbar = fig.colorbar(mesh)
    viz_tools.plot_land_mask(ax, grid_B, coords='map', color='burlywood')
    viz_tools.plot_coastline(ax, grid_B, coords='map')
    viz_tools.set_aspect(ax)

    lon_c = SITES['VENUS']['Central']['lon']
    lat_c = SITES['VENUS']['Central']['lat']
    lon_e = SITES['VENUS']['East']['lon']
    lat_e = SITES['VENUS']['East']['lat']
    lon_v = SITES['Vancouver']['lon']
    lat_v = SITES['Vancouver']['lat']

    ax.plot(
        lon_c,
        lat_c,
        marker='D',
        color='Black',
        markersize=10,
        markeredgewidth=2)
    bbox_args = dict(boxstyle='square', facecolor='white', alpha=0.8)
    ax.annotate(
        'Central',
        (lon_c - 0.15, lat_c + 0.08),
        fontsize=15,
        color='black',
        bbox=bbox_args)

    ax.plot(
        lon_e,
        lat_e,
        marker='D',
        color='Black',
        markersize=10,
        markeredgewidth=2)
    bbox_args = dict(boxstyle='square', facecolor='white', alpha=0.8)
    ax.annotate(
        'East',
        (lon_e + 0.05, lat_e + 0.08),
        fontsize=15,
        color='black',
        bbox=bbox_args)

    ax.plot(
        lon_v,
        lat_v,
        marker='D',
        color='DarkMagenta',
        markersize=10,
        markeredgewidth=2)
    bbox_args = dict(boxstyle='square', facecolor='white', alpha=0.8)
    ax.annotate(
        'Vancouver',
        (lon_v - 0.15, lat_v + 0.08),
        fontsize=15,
        color='black',
        bbox=bbox_args)

    ax.set_xlim([-124.02, -123.02])
    ax.set_ylim([48.5, 49.6])
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')
    figures.axis_colors(ax, 'white')
    ax.set_xlabel('Longitude', **axis_font)
    ax.set_ylabel('Latitude', **axis_font)
    ax.set_title('VENUS Node Locations', **title_font)
    cbar.set_label('Depth [m]', **axis_font)

    return fig


def loadparam(to, tf, path, freq='h', depav='None'):
    """ This function loads all the data between the start and the end date
    that contains gridded quarter-hourly velocity netCDF4 files. Then it mask,
    unstaggers and rotates the velocities by component about the VENUS nodes.
    Lastly it fits the velcities and caculates the tidal ellipse parameters for
    that date range.**(Important not to have a to < 2015-05-09 because the
    files do not exist before this date).**

    :arg to: The beginning of the date range of interest
    :type to: datetime object

    :arg tf: The end of the date range of interest
    :type tf: datetime object

    :arg path: Defines the path used(eg. nowcast)
    :type path: string

    :arg freq: determines the type of data used (quarter-hourly or hourly).
        Default set to hourly.
    :type freq: string

    :arg depav: Values overwhich the velocities will be depth averaged to
        output depth averaged ellipse parameters.
        [min Central, max Central, min East, max, East]. (default is 'None').
    :type depav: array

    :returns: depth, maj, mino, thet, pha,mjk, mnk, thk, phak- the M2 and K1
        ellipse parameters at various depths.
    """
    if freq == 'h':
        filesu = analyze.get_filenames(to, tf, '1h', 'grid_U', path)
        filesv = analyze.get_filenames(to, tf, '1h', 'grid_V', path)

        i_c = SITES['VENUS']['Central']['i']
        i_e = SITES['VENUS']['East']['i']
        j_c = SITES['VENUS']['Central']['j']
        j_e = SITES['VENUS']['East']['j']

        a = filesu
        b = filesv
        c = filesu
        d = filesv

    else:
        files_Central = analyze.get_filenames_15(to, tf, 'central', path)
        files_East = analyze.get_filenames_15(to, tf, 'east', path)

        i_c = 1
        i_e = 1
        j_c = 1
        j_e = 1

        a = files_Central
        b = files_Central
        c = files_East
        d = files_East

    u_u_c, time = analyze.combine_files(
        a, 'vozocrtx', 'None', [j_c-1, j_c], [i_c-1, i_c])
    v_v_c, timec = analyze.combine_files(
        b, 'vomecrty', 'None', [j_c-1, j_c], [i_c-1, i_c])
    time_c = tt.convert_to_seconds(timec)
    dep_t_c = nc.Dataset(b[-1]).variables['depthv']

    u_u_e, time = analyze.combine_files(
        c, 'vozocrtx', 'None', [j_e-1, j_e], [i_e-1, i_e])
    v_v_e, timee = analyze.combine_files(
        d, 'vomecrty', 'None', [j_e-1, j_e], [i_e-1, i_e])
    time_e = tt.convert_to_seconds(timee)
    dep_t_e = nc.Dataset(d[-1]).variables['depthv']

    depth = [dep_t_c[:], dep_t_e[:]]

    u_u_0 = np.ma.masked_values(u_u_e, 0)
    v_v_0 = np.ma.masked_values(v_v_e, 0)
    u_u_0c = np.ma.masked_values(u_u_c, 0)
    v_v_0c = np.ma.masked_values(v_v_c, 0)

    u_c, v_c = unstag_rot_gridded(u_u_0c, v_v_0c, 'Central')
    u_e, v_e = unstag_rot_gridded(u_u_0, v_v_0, 'East')

    if depav == 'None':
        us = [u_c, u_e]
        vs = [v_c, v_e]
        thesize = (40, 2)

    else:
        jc = np.where(np.logical_and(depth[0] > depav[0], depth[0] < depav[1]))
        je = np.where(np.logical_and(depth[1] > depav[2], depth[1] < depav[3]))

        u_c_slice = u_c[:, jc[0]]
        v_c_slice = v_c[:, jc[0]]
        u_e_slice = u_e[:, je[0]]
        v_e_slice = v_e[:, je[0]]

        uc_av = analyze.depth_average(u_c_slice, depth[0][jc], 1)
        vc_av = analyze.depth_average(v_c_slice, depth[0][jc], 1)
        ue_av = analyze.depth_average(u_e_slice, depth[1][je], 1)
        ve_av = analyze.depth_average(v_e_slice, depth[1][je], 1)

        thesize = (1, 2)
        us = [uc_av, ue_av]
        vs = [vc_av, ve_av]

    times = [time_c, time_e]
    i = np.arange(0, 2)

    vM2amp = np.zeros(thesize)
    vM2pha = np.zeros(thesize)
    vK1amp = np.zeros(thesize)
    vK1pha = np.zeros(thesize)
    uM2amp = np.zeros(thesize)
    uM2pha = np.zeros(thesize)
    uK1amp = np.zeros(thesize)
    uK1pha = np.zeros(thesize)

    for i, u, time, v in zip(i, us, times, vs):
        uM2amp[:, i], uM2pha[:, i], uK1amp[:, i], uK1pha[
            :, i] = tt.fittit(u, time)
        vM2amp[:, i], vM2pha[:, i], vK1amp[:, i], vK1pha[
            :, i] = tt.fittit(v, time)

    CX, SX, CY, SY, ap, am, ep, em, maj, mino, thet, pha = tt.ellipse_params(
        uM2amp, uM2pha, vM2amp, vM2pha)

    CXk, SXk, CYk, SYk, apk, amk, epk, emk, mjk, mnk, thk, phak = tt.ellipse_params(
        uK1amp, uK1pha, vK1amp, vK1pha)

    return depth, maj, mino, pha, thet, mjk, mnk, thk, phak


def loadparam_all(to, tf, path, i, j, depav='None'):

    """ This function loads all the data between the start and the end date
    that contains hourly velocity netCDF4 files. Then it mask, unstaggers and
    rotates the velocities by component about the grid point described by the i
    and j. Lastly it fits the velcities and caculates the tidal ellipse
    parameters for that date range.

    :arg to: The beginning of the date range of interest
    :type to: datetime object

    :arg tf: The end of the date range of interest
    :type tf: datetime object

    :arg path: Defines the path used(eg. nowcast)
    :type path: string

    :arg depav: Values overwhich the velocities will be depth averaged to
        output depth averaged ellipse parameters.
        [min, max]. (default is 'None').
    :type depav: array

    :returns: depth, maj, mino, thet, pha,mjk, mnk, thk, phak- the M2 and K1
        ellipse parameters at various depths.
         """

    filesu = analyze.get_filenames(to, tf, '1h', 'grid_U', path)
    filesv = analyze.get_filenames(to, tf, '1h', 'grid_V', path)

    u_u, timer = analyze.combine_files(
        filesu, 'vozocrtx', 'None', [j-1, j], [i-1, i])
    v_v, timee = analyze.combine_files(
        filesv, 'vomecrty', 'None', [j-1, j], [i-1, i])

    time = tt.convert_to_seconds(timer)
    dep_t = nc.Dataset(filesu[-1]).variables['depthu']

    u_u_0 = np.ma.masked_values(u_u, 0)
    v_v_0 = np.ma.masked_values(v_v, 0)

    u, v = unstag_rot(u_u_0, v_v_0, 1, 1)

    if depav == 'None':
        thesize = (40)
    else:
        j = np.where(np.logical_and(dep_t[0] > depav[0], dep_t[0] < depav[1]))
        u_slice = u[:, j[0]]
        v_slice = v[:, j[0]]

        u = analyze.depth_average(u_slice, dep_t[0][j], 1)
        v = analyze.depth_average(v_slice, dep_t[0][j], 1)
        thesize = (1)

    vM2amp = np.zeros(thesize)
    vM2pha = np.zeros(thesize)
    vK1amp = np.zeros(thesize)
    vK1pha = np.zeros(thesize)
    uM2amp = np.zeros(thesize)
    uM2pha = np.zeros(thesize)
    uK1amp = np.zeros(thesize)
    uK1pha = np.zeros(thesize)
    uM2amp[:], uM2pha[:], uK1amp[:], uK1pha[:] = tt.fittit(u, time)
    vM2amp[:], vM2pha[:], vK1amp[:], vK1pha[:] = tt.fittit(v, time)

    CX, SX, CY, SY, ap, am, ep, em, maj, mi, the, pha = tt.ellipse_params(uM2amp, uM2pha, vM2amp, vM2pha)

    CXk, SXk, CYk, SYk, apk, amk, epk, emk, majk, mik, thek, phak = tt.ellipse_params(uK1amp, uK1pha, vK1amp, vK1pha)

    return dep_t, maj, mi, the, pha, majk, mik, thek, phak
