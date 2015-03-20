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


"""A collection of Python functions to produce model results visualization
figures for analysis and model evaluation of nowcast, forecast, and
forecast2 runs.
"""

from __future__ import division

import datetime
import glob
import os

from dateutil import tz
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import pandas as pd

from salishsea_tools import (
    nc_tools,
    tidetools,
)

from salishsea_tools.nowcast import figures


# Paths for model results
paths = {'nowcast': '/data/dlatorne/MEOPAR/SalishSea/nowcast/',
         'forecast': '/ocean/sallen/allen/research/MEOPAR/SalishSea/forecast/',
         'forecast2': '/ocean/sallen/allen/research/MEOPAR/SalishSea/forecast2/'}

# Colours for plots
colours = {'nowcast': 'DodgerBlue',
           'forecast': 'ForestGreen',
           'forecast2': 'MediumVioletRed',
           'observed': 'Indigo',
           'predicted': 'ForestGreen',
           'model': 'blue',
           'residual': 'DimGray'}

def get_filenames(t_orig, t_final, period, grid, model_path):
    """Returns a list with the filenames for all files over the
    defined period of time and sorted in chronological order.

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :arg t_final: The end of the date range of interest.
    :type t_final: datetime object

    :arg period: Time interval of model results (eg. 1h or 1d).
    :type period: string

    :arg grid: Type of model results (eg. grid_T, grid_U, etc).
    :type grid: string

    :arg model_path: Defines the path used (eg. nowcast)
    :type model_path: string

    :returns: files, a list of filenames
    """

    numdays = (t_final-t_orig).days
    dates = [t_orig + datetime.timedelta(days=num)
             for num in range(0, numdays+1)]
    dates.sort()

    allfiles = glob.glob(model_path+'*/SalishSea_'+period+'*_'+grid+'.nc')
    sdt = dates[0].strftime('%Y%m%d')
    edt = dates[-1].strftime('%Y%m%d')
    sstr = 'SalishSea_{}_{}_{}_{}.nc'.format(period, sdt, sdt, grid)
    estr = 'SalishSea_{}_{}_{}_{}.nc'.format(period, edt, edt, grid)

    files = []
    for filename in allfiles:
        if os.path.basename(filename) >= sstr:
            if os.path.basename(filename) <= estr:
                files.append(filename)

    files.sort(key=os.path.basename)

    return files


def combine_files(files, var, depth, j, i):
    """Returns the value of the variable entered over
    multiple files covering a certain period of time.

    :arg files: Multiple result files in chronological order.
    :type files: list

    :arg var: Name of variable (sossheig = sea surface height,
                      vosaline = salinity, votemper = temperature,
                      vozocrtx = Velocity U-component,
                      vomecrty = Velocity V-component).
    :type var: string

    :arg depth: Depth of model results ('None' if var=sossheig).
    :type depth: integer or string

    :arg j: Latitude (y) index of location (<=897).
    :type j: integer

    :arg i: Longitude (x) index of location (<=397).
    :type i: integer

    :returns: var_ary, time - array of model results and time.
    """

    time = np.array([])
    var_ary = np.array([])

    for f in files:
        G = nc.Dataset(f)
        if depth == 'None':
            var_tmp = G.variables[var][:, j, i]
        else:
            var_tmp = G.variables[var][:, depth, j, i]

        var_ary = np.append(var_ary, var_tmp, axis=0)
        t = nc_tools.timestamp(G, np.arange(var_tmp.shape[0]))
        for ind in range(len(t)):
            t[ind] = t[ind].datetime
        time = np.append(time, t)

    return var_ary, time


def plot_files(ax, grid_B, files, var, depth, t_orig, t_final,
               name, label, colour):
    """Plots values of  variable over multiple files covering
    a certain period of time.

    :arg ax: The axis where the variable is plotted.
    :type ax: axis object

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg files: Multiple result files in chronological order.
    :type files: list

    :arg var: Name of variable (sossheig = sea surface height,
                      vosaline = salinity, votemper = temperature,
                      vozocrtx = Velocity U-component,
                      vomecrty = Velocity V-component).
    :type var: string

    :arg depth: Depth of model results ('None' if var=sossheig).
    :type depth: integer or string

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :arg t_final: The end of the date range of interest.
    :type t_final: datetime object

    :arg name: The name of the station.
    :type name: string

    :arg label: Label for plot line.
    :type label: string

    :arg colour: Colour of plot lines.
    :type colour: string

    :returns: matplotlib figure object instance (fig) and axis object (ax).
    """

    # Stations information
    [lats, lons] = figures.station_coords()

    # Bathymetry
    bathy, X, Y = tidetools.get_bathy_data(grid_B)

    # Get index
    [j, i] = tidetools.find_closest_model_point(lons[name], lats[name], X, Y,
                                                bathy, allow_land=False)

    # Call function
    var_ary, time = combine_files(files, var, depth, j, i)

    # Plot
    ax.plot(time, var_ary, label=label, color=colour, linewidth=2.5)

    # Figure format
    ax_start = t_orig
    ax_end = t_final + datetime.timedelta(days=1)
    ax.set_xlim(ax_start, ax_end)
    hfmt = mdates.DateFormatter('%m/%d %H:%M')
    ax.xaxis.set_major_formatter(hfmt)

    return ax


def compare_ssh_tides(grid_B, files, t_orig, t_final, name, PST=0, MSL=0,
                      figsize=(20, 6)):
    """
    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg files: Multiple result files in chronological order.
    :type files: list

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :arg t_final: The end of the date range of interest.
    :type t_final: datetime object

    :arg name: Name of station.
    :type name: string

    :arg PST: Specifies if plot should be presented in PST.
              1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg MSL: Specifies if the plot should be centred about mean sea level.
              1=centre about MSL, 0=centre about 0.
    :type MSL: 0 or 1

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Model
    ax = plot_files(ax, grid_B, files, 'sossheig', 'None',
                    t_orig, t_final, name, 'Model', colours['model'])
    # Tides
    figures.plot_tides(ax, name, PST, MSL, color=colours['predicted'])

    # Figure format
    ax.set_title('Modelled Sea Surface Height versus Predicted Tides at {station}: {t_start:%d-%b-%Y} to {t_end:%d-%b-%Y}'.format(station=name, t_start=t_orig, t_end=t_final))
    ax.set_ylim([-3.0, 3.0])
    ax.set_xlabel('[hrs]')
    ax.legend(loc=2, ncol=2)
    ax.grid()

    return fig


def calculate_wlev_residual_NOAA(name, t_orig):
    """ Calculates the residual of the observed water levels with respect
    to the predicted tides at a specific station and for a specific date.

    :arg name: Name of station.
    :type name: string

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :returns: residual (calculated residual), obs (observed water levels),
              tides (predicted tides)
    """
    stations = {'Cherry Point': 9449424,
                'Neah Bay': 9443090,
                'Friday Harbor': 9449880}
    start_date = t_orig.strftime('%d-%b-%Y')
    end_date = start_date
    obs = figures.get_NOAA_wlevels(stations[name], start_date, end_date)
    tides = figures.get_NOAA_tides(stations[name], start_date, end_date)

    # Prepare to find residual
    residual = np.zeros(len(obs.time))

    # Residual and time check
    for i in np.arange(0, len(obs.time)):
        if any(tides.time == obs.time[i]):
            residual[i] = obs.wlev[i] - tides.pred[tides.time == obs.time[i]]
        else:
            residual[i] = float('Nan')

    return residual, obs, tides


def plot_wlev_residual_NOAA(t_orig, elements, figsize=(20, 6)):
    """ Plots the water level residual as calculated by the function
    calculate_wlev_residual_NOAA and has the option to also plot the
    observed water levels and predicted tides over the course of one day.

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :arg elements: Elements included in figure.
                   'residual' for residual only and 'all' for residual,
                   observed water level, and predicted tides.
    :type elements: string

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: fig
    """

    residual, obs, tides = calculate_wlev_residual_NOAA('Neah Bay', t_orig)

    # Figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot
    ax.plot(obs.time, residual, colours['residual'], label='Observed Residual',
            linewidth=2.5)
    if elements == 'all':
        ax.plot(obs.time, obs.wlev,
                colours['observed'], label='Observed Water Level', linewidth=2.5)
        ax.plot(tides.time, tides.pred[tides.time == obs.time],
                colours['predicted'], label='Tidal Predictions', linewidth=2.5)
    if elements == 'residual':
        pass
    ax.set_title('Residual of the observed water levels at Neah Bay: {t:%d-%b-%Y}'.format(t=t_orig))
    ax.set_ylim([-3.0, 3.0])
    ax.set_xlabel('[hrs]')
    hfmt = mdates.DateFormatter('%m/%d %H:%M')
    ax.xaxis.set_major_formatter(hfmt)
    ax.legend(loc=2, ncol=3)
    ax.grid()

    return fig


def create_path(mode, t_orig, file_part):
    """ Creates a path to a file associated with a simulation for date t_orig.
    E.g.
    create_path('nowcast',datatime.datetime(2015,1,1),'SalishSea_1h*grid_T.nc')
    gives
    /data/dlatorne/MEOPAR/SalishSea/nowcast/01jan15/SalishSea_1h_20150101_20150101_grid_T.nc

    :arg mode: Mode of results - nowcast, forecast, forecast2.
    :type mode: string

    :arg t_orig: The simulation start date.
    :type t_orig: datetime object


    :arg file_part: Identifier for type of file.
    E.g. SalishSea_1h*grid_T.nc or ssh*.txt
    :type grid: string

    :returns: filename, run_date
    filename is the path of the file or empty list if the file does not exist.
    run_date is a datetime object that represents the date the simulation ran
    """

    run_date = t_orig

    if mode == 'nowcast':
        results_home = paths['nowcast']
    elif mode == 'forecast':
        results_home = paths['forecast']
        run_date = run_date + datetime.timedelta(days=-1)
    elif mode == 'forecast2':
        results_home = paths['forecast2']
        run_date = run_date + datetime.timedelta(days=-2)

    results_dir = os.path.join(results_home,
                               run_date.strftime('%d%b%y').lower())

    filename = glob.glob(os.path.join(results_dir, file_part))

    try:
        filename = filename[-1]
    except IndexError:
        pass

    return filename, run_date


def truncate_data(data, time, sdt, edt):
    """ Truncates data for a desired time range: sdt <= time <= edt
    data and time must be numpy arrays.
    sdt, edt, and times in time must all have a timezone or all be naive.

    :arg data: the data to be truncated
    :type data: numpy array

    :arg time: array of times associated with data
    :type time: numpy array

    :arg sdt: the start time of the tuncation
    :type sdt: datetime object

    :arg edt: the end time of the truncation
    :type edt: datetime object

    :returns: data_trun, time_trun, the truncated data and time arrays
    """

    inds = np.where(np.logical_and(time <= edt, time >= sdt))

    return data[inds], time[inds]


def verified_runs(t_orig):
    """ Compiles a list of run types (nowcast, forecast, and/or forecast 2)
    that have been verified as complete by checking if their corresponding
    .nc files for that day (generated by create_path) exist.

    :arg t_orig:
    :type t_orig: datetime object

    :returns: runs_list, list strings representing the runs that completed
    """

    runs_list = []
    for mode in ['nowcast', 'forecast', 'forecast2']:
        files, run_date = create_path(mode, t_orig, 'SalishSea*grid_T.nc')
        if files:
            runs_list.append(mode)

    return runs_list


def calculate_error(res_mod, time_mod, res_obs, time_obs):
    """ Calculates the model or forcing residual error.

    :arg res_mod: Residual for model ssh or NB surge data.
    :type res_mod: numpy array

    :arg time_mod: Time of model output.
    :type time_mod: numpy array

    :arg res_obs: Observed residual (archived or at Neah Bay)
    :type res_obs: numpy array

    :arg time_obs: Time corresponding to observed residual.
    :type time_obs: numpy array

    :return: error
    """

    res_obs_interp = figures.interp_to_model_time(time_mod, res_obs, time_obs)
    error = res_mod - res_obs_interp

    return error
