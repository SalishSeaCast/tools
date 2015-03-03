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

from cStringIO import StringIO
import datetime
import glob
import os

import arrow
from dateutil import tz
import matplotlib
from matplotlib.backends import backend_agg as backend
import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import pandas as pd
import requests
from scipy import interpolate as interp

from salishsea_tools import (
    nc_tools,
    viz_tools,
    stormtools,
    tidetools,
)

from salishsea_tools.nowcast import figures


# Average mean sea level calculated over 1983-2001
# (To be used to centre model output about mean sea level)
MSL_DATUMS = {
    'Point Atkinson': 3.10, 'Victoria': 1.90,
    'Campbell River': 2.89, 'Patricia Bay': 2.30}


def model_paths():
    """ A dictionary of paths containing model results for
    nowcasts, forecasts and forecasts 2.

    :returns: paths (dictionary)
    """

    paths = {'nowcast': '/data/dlatorne/MEOPAR/SalishSea/nowcast/',
             'forecast': '/ocean/sallen/allen/research/MEOPAR/SalishSea/forecast/',
             'forecast2': '/ocean/sallen/allen/research/MEOPAR/SalishSea/forecast2/'}

    return paths


def feet_to_metres(feet):
    """ Converts feet to metres.

    :returns: metres
    """

    metres = feet*0.3048
    return metres


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
    ax.plot(time, var_ary, label=label, color=colour, linewidth=2)

    # Figure format
    ax_start = t_orig
    ax_end = t_final + datetime.timedelta(days=1)
    ax.set_xlim(ax_start, ax_end)
    hfmt = mdates.DateFormatter('%m/%d %H:%M')
    ax.xaxis.set_major_formatter(hfmt)

    return ax


def compare_ssh_tides(grid_B, files, t_orig, t_final, name, PST=0, MSL=0,
                      figsize=(20, 5)):
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
                    t_orig, t_final, name, 'Model', 'DodgerBlue')
    # Tides
    figures.plot_tides(ax, name, PST, MSL, color='green')

    # Figure format
    fig.autofmt_xdate()
    ax.set_title('Modelled Sea Surface Height versus Predicted Tides:{t_start:%d-%b-%Y} to {t_end:%d-%b-%Y}'.format(t_start=t_orig, t_end=t_final))
    ax.legend(loc=3, ncol=2)

    return fig


def calculate_wlev_residual(name, t_orig):
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


def plot_wlev_residual(t_orig, elements, figsize=(20, 5)):
    """ Plots the water level residual as calculated by the function
    calculate_wlev_residual and has the option to also plot the observed
    water levels and predicted tides over the course of one day.

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

    residual, obs, tides = calculate_wlev_residual('Neah Bay', t_orig)

    # Figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot
    ax.plot(obs.time, residual, 'Gray', label='Obs Residual', linewidth=2)
    if elements == 'all':
        ax.plot(obs.time, obs.wlev,
                'DodgerBlue', label='Obs Water Level', linewidth=2)
        ax.plot(tides.time, tides.pred[tides.time == obs.time],
                'ForestGreen', label='Pred Tides', linewidth=2)
    if elements == 'residual':
        pass
    ax.legend(loc=2, ncol=3)
    hfmt = mdates.DateFormatter('%m/%d %H:%M')
    ax.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate()

    return fig


def create_path_sshNB(mode, t_orig):
    """ Creates a complete path to the .txt file containing
    predicted water levels at Neah Bay for the specified date
    and for the mode chosen.

    :arg mode: Mode of results - nowcast, forecast, forecast2.
    :type mode: string

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :returns: filename_NB (path including filename)
              and run_date, a datetime object of the simulation run date
    """

    # All paths
    paths = model_paths()

    run_date = t_orig

    # Directory housing all daily nowcast or forecast folders
    if mode == 'nowcast':
        results_home = paths['nowcast']
    elif mode == 'forecast':
        results_home = paths['forecast']
        run_date = run_date + datetime.timedelta(days=-1)
    elif mode == 'forecast2':
        results_home = paths['forecast2']
        run_date = run_date + datetime.timedelta(days=-2)

    # Directory housing all result files for one day
    results_dir = os.path.join(results_home,
                               run_date.strftime('%d%b%y').lower())

    # Directory and filename
    filename_NB = glob.glob(results_dir+'/ssh*')
    filename_NB = filename_NB[0]

    return filename_NB, run_date


def create_path_results(mode, t_orig):
    """ Compiles a list of complete paths to the various
    model result .nc files (both 1d and 1h and grid U, V, W and T)
    for the specified mode and date.

    :arg mode: Mode of results - nowcast, forecast, forecast2.
    :type mode: string

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :returns: filenames (list of paths including filenames)
    """

    # All paths
    paths = model_paths()

    run_date = t_orig

    # Directory housing all daily nowcast or forecast folders
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
    filenames = glob.glob(results_dir+'/SalishSea_*_grid_*.nc')

    return filenames


def verified_runs(t_orig):
    """ Compiles a list of run types (nowcast, forecast, and/or forecast 2)
    that have been verified as complete by checking if their corresponding
    .nc files for that day (generated by create_path_results) exist.

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :returns: runs_list (list of strings)
    """

    runs_list = []
    for mode in ['nowcast', 'forecast', 'forecast2']:
        files = create_path_results(mode, t_orig)
        if files:
            runs_list.append(mode)

    return runs_list


def load_surge_data(filename_NB):
    """Loads the textfile with surge predictions for Neah Bay.

    :arg filename_NB: Path to file of predicted water levels at Neah Bay.
    :type filename_NB: string

    :returns: data (data structure)
    """

    # Loading the data from that text file.
    data = pd.read_csv(filename_NB, skiprows=3,
                       names=['date', 'surge', 'tide', 'obs',
                              'fcst', 'anom', 'comment'], comment='#')
    # Drop rows with all Nans
    data = data.dropna(how='all')

    return data


def to_datetime(datestr, year, isDec, isJan):
    """ Converts the string given by datestr to a datetime object.
    The year is an argument because the datestr in the NOAA data
    doesn't have a year. Times are in UTC/GMT.

    :arg datestr: Date of data.
    :type datestr: datetime object

    :arg year: Year of data.
    :type year: datetime object

    :arg isDec: True if run date was December.
    :type isDec: Boolean

    :arg isJan: True if run date was January.
    :type isJan: Boolean

    :returns: dt (datetime representation of datestr)
    """

    dt = datetime.datetime.strptime(datestr, '%m/%d %HZ')
    # Dealing with year changes.
    if isDec and dt.month == 1:
        dt = dt.replace(year=year+1)
    elif isJan and dt.month == 12:
        dt = dt.replace(year=year-1)
    else:
        dt = dt.replace(year=year)
    dt = dt.replace(tzinfo=tz.tzutc())

    return dt


def retrieve_surge(data, run_date):
    """ Gathers the surge information a forcing file from on run_date.

    :arg data: Surge predictions data.
    :type data: data structure

    :arg run_date: Simulation run date.
    :type run_date: datetime object

    :returns: surges (meteres), times (array with time_counter)
    """

    surge = []
    times = []
    isDec, isJan = False, False
    if run_date.month == 1:
        isJan = True
    if run_date.month == 12:
        isDec = True
    # Convert datetime to string for comparing with times in data
    for d in data.date:

        dt = to_datetime(d, run_date.year, isDec, isJan)
        times.append(dt)
        daystr = dt.strftime('%m/%d %HZ')
        tide = data.tide[data.date == daystr].item()
        obs = data.obs[data.date == daystr].item()
        fcst = data.fcst[data.date == daystr].item()
        if obs == 99.90:
            # Fall daylight savings
            if fcst == 99.90:
                # If surge is empty, just append 0
                if not surge:
                    surge.append(0)
                else:
                    # Otherwise append previous value
                    surge.append(surge[-1])
            else:
                surge.append(feet_to_metres(fcst-tide))
        else:
            surge.append(feet_to_metres(obs-tide))

    return surge, times


def plot_forced_residual(modes_all, t_orig, figsize):
    """ Plots observed water level residual (calculate_wlev_residual)
    at Neah Bay against forced residuals using surge data (retrieve_surge)
    from existing .txt files for Neah Bay. Function may produce none, any,
    or all (nowcast, forecast, forecast 2) forced residuals depending on
    availability for specified date.

    :arg mode: Any or all modes of results - nowcast, forecast, forecast2.
    :type mode: string

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: figure
    """

    t_forcing_start = t_orig
    t_forcing_end = t_forcing_start + datetime.timedelta(days=1)

    colours = {'observed': 'DimGray', 'nowcast': 'DodgerBlue',
               'forecast': 'ForestGreen', 'forecast2': 'MediumVioletRed'}

    # Figure
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Residual
    residual, obs, tides = calculate_wlev_residual('Neah Bay', t_forcing_start)
    ax.plot(obs.time, residual, colours['observed'], label='observed',
            linewidth=2.5)

    # Nowcast and Forecasts
    for mode in modes_all:
        try:
            filename_NB, run_date = create_path_sshNB(mode, t_orig)
            data = load_surge_data(filename_NB)
            surge, dates = retrieve_surge(data, run_date)
            ax.plot(dates, surge, label=mode, linewidth=2.5,
                    color=colours[mode])
        except IndexError:
            pass

    # Figure format
    ax.set_xlim([t_forcing_start, t_forcing_end])
    ax.set_ylim([-0.4, 0.2])
    ax.set_xlabel('[hrs]')
    ax.set_ylabel('[m]')
    ax.set_title('Comparison of observed and forced sea surface height residuals: {t_forcing:%d-%b-%Y}'.format(t_forcing=t_forcing_start))
    ax.legend(loc=2, ncol=4)
    ax.grid()

    return fig


def plot_forced_residual_all(t_orig, figsize=(20, 7)):

    """Similar to the function plot_forced_residual, except this is designed
    to execute the plot function for all forced residuals as long as their
    respective runs have been verified to exist.

    :arg t_orig: The beginning of the date range of interest.
    :type t_orig: datetime object

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: figure
    """

    runs_list = verified_runs(t_orig)

    fig = plot_forced_residual(runs_list, t_orig, figsize=figsize)

    return fig
