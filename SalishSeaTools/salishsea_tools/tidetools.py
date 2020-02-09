
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

"""A collection of tools for dealing with tidal results from the
Salish Sea NEMO model
"""
from __future__ import division

import cmath
import collections
import csv
import datetime
import os
from math import radians, cos, sqrt, pi

import angles
import matplotlib.pyplot as plt
import netCDF4 as NC
import numpy as np
import pandas as pd
import pytz
import requests
from dateutil import tz
from scipy.optimize import curve_fit

from salishsea_tools import (
    namelist,
    viz_tools,
    geo_tools,
)

# Tide correction for amplitude and phase set to September 10th 2014 by nowcast
# Values for there and other constituents can be found in:
# /data/dlatorne/MEOPAR/SalishSea/nowcast/08jul15/ocean.output
# The freq parameter it the frequency of the tidal consituent in degrees/hour.
CorrTides = {
    'reftime': datetime.datetime(2014, 9, 10, tzinfo=tz.tzutc()),
    'K1': {
        'freq': 15.041069000,
        'ft': 0.891751,
        'uvt': 262.636797},
    'O1': {
        'freq': 13.943036,
        'ft': 0.822543,
        'uvt': 81.472430},
    'Q1': {
        'freq': 13.398661,
        'ft': 0.822543,
        'uvt': 46.278236},
    'P1': {
        'freq': 14.958932,
        'ft': 1.0000000,
        'uvt': 101.042160},
    'M2': {
        'freq': 28.984106,
        'ft': 1.035390,
        'uvt': 346.114490},
    'N2': {
        'freq': 28.439730,
        'ft': 1.035390,
        'uvt': 310.920296},
    'S2': {
        'freq': 30.000002,
        'ft': 1.0000000,
        'uvt': 0.000000},
    'K2': {
        'freq': 30.082138,
        'ft': 0.763545,
        'uvt': 344.740346}
    }


def get_all_perm_dfo_wlev(start_date, end_date):
    """Get water level data for all permanent DFO water level sites
    for specified period.

    :arg start_date: Start date; e.g. '01-JAN-2010'.
    :type start_date: str

    :arg end_date: End date; e.g. '31-JAN-2010'
    :type end_date: str

    :returns: Saves text files with water level data at each site
    """
    stations = {
        'Point Atkinson': 7795,
        'Vancouver': 7735,
        'Patricia Bay': 7277,
        'Victoria Harbour': 7120,
        'Bamfield': 8545,
        'Tofino': 8615,
        'Winter Harbour': 8735,
        'Port Hardy': 8408,
        'Campbell River': 8074,
        'New Westminster': 7654,
    }
    for ttt in stations:
        get_dfo_wlev(stations[ttt], start_date, end_date)


def get_dfo_wlev(station_no, start_date, end_date):
    """Download water level data from DFO site for one DFO station
    for specified period.

    :arg station_no: Station number e.g. 7795.
    :type station_no: int

    :arg start_date: Start date; e.g. '01-JAN-2010'.
    :type start_date: str

    :arg end_date: End date; e.g. '31-JAN-2010'
    :type end_date: str

    :returns: Saves text file with water level data at one station
    """
    # Name the output file
    outfile = 'wlev_'+str(station_no)+'_'+start_date+'_'+end_date+'.csv'
    # Form urls and html information
    base_url = 'http://www.meds-sdmm.dfo-mpo.gc.ca/isdm-gdsi/twl-mne/inventory-inventaire/'
    form_handler = (
        'data-donnees-eng.asp?user=isdm-gdsi&region=PAC&tst=1&no='
        + str(station_no))
    sitedata = {
        'start_period': start_date,
        'end_period': end_date,
        'resolution': 'h',
        'time_zone': 'l',
    }
    data_provider = (
        'download-telecharger.asp'
        '?File=E:%5Ciusr_tmpfiles%5CTWL%5C'
        + str(station_no) + '-'+start_date + '_slev.csv'
        '&Name=' + str(station_no) + '-'+start_date+'_slev.csv')
    # Go get the data from the DFO site
    with requests.Session() as s:
        s.post(base_url + form_handler, data=sitedata)
        r = s.get(base_url + data_provider)
    # Write the data to a text file
    with open(outfile, 'w') as f:
        f.write(r.text)


def dateParserMeasured(s):
    """Function to make datetime object aware of time zone
    e.g. date_parser=dateParserMeasured('2014/05/31 11:42')

    :arg s: string of date and time
    :type s: str

    :returns: datetime object that is timezone aware
    """
    # Convert the string to a datetime object
    unaware = datetime.datetime.strptime(s, "%Y/%m/%d %H:%M")
    # Add in the local time zone (Canada/Pacific)
    aware = unaware.replace(tzinfo=pytz.timezone('Canada/Pacific'))
    # Convert to UTC
    return aware.astimezone(pytz.timezone('UTC'))


def read_dfo_wlev_file(filename):
    """Read in the data in the csv file downloaded from DFO website

    :arg filename: Filename to read.
    :type filename: str

    :returns: measured time, measured water level, station name,
              station number, station lat, station long
    """
    info = pd.read_csv(filename, nrows=4, index_col=0, header=None)
    wlev_meas = pd.read_csv(
        filename, skiprows=7, parse_dates=[0], date_parser=dateParserMeasured)
    wlev_meas = wlev_meas.rename(
        columns={'Obs_date': 'time', 'SLEV(metres)': 'slev'})
    # Allocate the variables to nice names
    stat_name = info[1][0]
    stat_num = info[1][1]
    stat_lat = info[1][2]
    stat_lon = info[1][3]
    # Measured times are in PTZ - first make dates aware of this,
    # then convert dates to UTC
    for x in np.arange(0, len(wlev_meas.time)):
        wlev_meas.time[x] = wlev_meas.time[x].replace(
            tzinfo=pytz.timezone('Canada/Pacific'))
        print(wlev_meas.time[x])
        wlev_meas.time[x] = wlev_meas.time[x].astimezone(pytz.timezone('UTC'))
        print(wlev_meas.time[x])
    return (
        wlev_meas.time, wlev_meas.slev,
        stat_name, stat_num, stat_lat, stat_lon)


def get_amp_phase_data(runname, loc):
    """Get the amplitude and phase data for one or more model runs.

    :arg runname: Name of the model run to process;
                  e.g. runname = '50s_15Sep-21Sep',
                  or if you'd like the harmonics of more than one run
                  to be combined into one picture,
                  give a tuple of names;
                  e.g. ('40d', '41d50d', '51d60d').
    :type runname: str or tuple

    :arg loc: Location of results folder;
              e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :returns: mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha
    """
    if runname == 'concepts110':
        mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_concepts110(
            loc + runname)
        mod_K1_amp = 0.0
        mod_K1_pha = 0.0
    elif runname == 'jpp72':
        mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_jpp72(loc + runname)
        mod_K1_amp = 0.0
        mod_K1_pha = 0.0
    elif runname == 'composite':
        # 'composite' was the first set of runs where the harmonics were
        # combined manually
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_composite_harms2()
    elif type(runname) is not str and len(runname) > 1:
        # Combine the harmonics from a set of runs
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_composite_harms(
            runname, loc)
    else:
        # Get the harmonics for a specific run
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = \
            get_netcdf_amp_phase_data(loc + runname)
    return mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha


def plot_amp_phase_maps(runname, loc, grid):
    """Plot the amplitude and phase results for a model run
    e.g. plot_amp_phase_maps('50s_15Sep-21Sep')

    :arg runname: name of the model run to process;
                  e.g. runname = '50s_15Sep-21Sep',
                  or if you'd like the harmonics of more than one run
                  to be combined into one picture, give a list of names;
                  e.g. '40d','41d50d','51d60d'
    :type runname: str

    :arg loc: location of results folder;
              e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :arg grid: netcdf file of grid data
    :type grid: netcdf dataset

    :returns: plots the amplitude and phase
    """
    mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_amp_phase_data(
        runname, loc)
    bathy, X, Y = get_bathy_data(grid)
    plot_amp_map(X, Y, grid, mod_M2_amp, 'M2')
    plot_pha_map(X, Y, grid, mod_M2_pha, 'M2')
    if runname != 'concepts110' and runname != 'jpp72':
        plot_amp_map(X, Y, grid, mod_K1_amp, 'K1')
        plot_pha_map(X, Y, grid, mod_K1_pha, 'K1')


def get_netcdf_amp_phase_data(loc):
    """Calculate amplitude and phase from the results of a
    particular run of the Salish Sea model

    :arg runname: name of the model run to process e.g. '50s_15Sep-21Sep'
    :type runname: str

    :returns: model M2 amplitude, model K1 amplitude, model M2 phase,
              model K1 phase
    """
    harmT = NC.Dataset(loc+'/Tidal_Harmonics_eta.nc', 'r')
    # Get imaginary and real components
    mod_M2_eta_real = harmT.variables['M2_eta_real'][0, :, :]
    mod_M2_eta_imag = harmT.variables['M2_eta_imag'][0, :, :]
    mod_K1_eta_real = harmT.variables['K1_eta_real'][0, :, :]
    mod_K1_eta_imag = harmT.variables['K1_eta_imag'][0, :, :]
    # Convert to amplitude and phase
    mod_M2_amp = np.sqrt(mod_M2_eta_real**2+mod_M2_eta_imag**2)
    mod_M2_pha = -np.degrees(np.arctan2(mod_M2_eta_imag, mod_M2_eta_real))
    mod_K1_amp = np.sqrt(mod_K1_eta_real**2+mod_K1_eta_imag**2)
    mod_K1_pha = -np.degrees(np.arctan2(mod_K1_eta_imag, mod_K1_eta_real))
    return mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha


def get_netcdf_amp_phase_data_jpp72(loc):
    """Calculate amplitude and phase from the results of the JPP72 model
    e.g. mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_jpp72()

    :returns: model M2 amplitude, model M2 phase
    """
    harmT = NC.Dataset(loc+'/JPP_1d_20020102_20020104_grid_T.nc', 'r')
    # Get amplitude and phase
    mod_M2_x_elev = harmT.variables['M2_x_elev'][0, :, :]  # Cj
    mod_M2_y_elev = harmT.variables['M2_y_elev'][0, :, :]  # Sj
    # See section 11.6 of NEMO manual (p223/367)
    mod_M2_amp = np.sqrt(mod_M2_x_elev**2+mod_M2_y_elev**2)
    mod_M2_pha = -np.degrees(np.arctan2(mod_M2_y_elev, mod_M2_x_elev))
    return mod_M2_amp, mod_M2_pha


def get_netcdf_amp_phase_data_concepts110(loc):
    """Calculate amplitude and phase from the results of the CONCEPTS110 model
    e.g. mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_concepts110()

    :returns: model M2 amplitude, model M2 phase
    """
    harmT = NC.Dataset(loc+'/WC3_Harmonics_gridT_TIDE2D.nc', 'r')
    mod_M2_amp = harmT.variables['M2_amp'][0, :, :]
    mod_M2_pha = harmT.variables['M2_pha'][0, :, :]
    return mod_M2_amp, mod_M2_pha


def get_bathy_data(grid):
    """Get the Salish Sea bathymetry from specified grid NC.Dataset
    e.g. bathy, X, Y = get_bathy_data(grid)

    :arg grid: netcdf object of model grid
    :type grid: netcdf dataset

    :returns: bathy, X, Y
    """
    bathy = grid.variables['Bathymetry'][:, :]
    X = grid.variables['nav_lon'][:, :]
    Y = grid.variables['nav_lat'][:, :]
    return bathy, X, Y


def get_SS_bathy_data():
    """Get the Salish Sea bathymetry and grid data
    e.g. bathy, X, Y = get_SS_bathy_data()

    .. note::

        This function is deprecated due to hard-coding of
        :file:`/ocean/klesouef/` path.
        Use :py:func:`tidetools.get_bathy_data` instead.

    :returns: bathy, X, Y
    """
    grid = NC.Dataset(
        '/ocean/klesouef/meopar/nemo-forcing/grid/bathy_meter_SalishSea.nc',
        'r')
    bathy = grid.variables['Bathymetry'][:, :]
    X = grid.variables['nav_lon'][:, :]
    Y = grid.variables['nav_lat'][:, :]
    return bathy, X, Y


def get_SS2_bathy_data():
    """Get the Salish Sea 2 bathymetry and grid data
    e.g. bathy, X, Y = get_SS2_bathy_data()

    .. note::

        This function is deprecated due to hard-coding of
        :file:`/ocean/klesouef/` path.
        Use :py:func:`tidetools.get_bathy_data` instead.

    :returns: bathy, X, Y
    """
    grid = NC.Dataset(
        '/ocean/jieliu/research/meopar/nemo-forcing/grid/bathy_meter_SalishSea2.nc', 'r')
    bathy = grid.variables['Bathymetry'][:, :]
    X = grid.variables['nav_lon'][:, :]
    Y = grid.variables['nav_lat'][:, :]
    return bathy, X, Y


def get_subdomain_bathy_data():
    """Get the subdomain bathymetry and grid data
    e.g. bathy, X, Y = get_subdomain_bathy_data()

    .. note::

        This function is deprecated due to hard-coding of
        :file:`/ocean/klesouef/` path.
        Use :py:func:`tidetools.get_bathy_data` instead.

    :returns: bathy, X, Y
    """
    grid = NC.Dataset(
        '/ocean/klesouef/meopar/nemo-forcing/grid/SubDom_bathy_meter_NOBCchancomp.nc',
        'r')
    bathy = grid.variables['Bathymetry'][:, :]
    X = grid.variables['nav_lon'][:, :]
    Y = grid.variables['nav_lat'][:, :]
    return bathy, X, Y


def find_model_level(depth, model_depths, fractional=False):
    """ Returns the index of the model level closest to a specified depth.
    The model level can be fractional (ie between two grid points).
    If depth is between 0 and first model level the result is negative.
    If depth is greater than the max depth the lowest level is returned.
    A python index is returned (count starting at 0). Add 1 for Fortran.

    :arg depth: The specified depth
    :type depth: float > 0

    :arg model_depths: array of model depths
    :type model_depths: numpy array (one dimensional)

    :arg fractional: a flag that specifies if a fractional model level
                     is desired
    :type fractional: boolean

    :returns: idx, the model level index
    """

    # index for closest value
    idx = (np.abs(depth-model_depths)).argmin()

    # If a fractional index is requried...
    if fractional:
        sign = np.sign(depth-model_depths[idx])
        idxpm = idx + sign*1
        # Check not to go out of bounds
        if idxpm < model_depths.shape[0] and idxpm >= 0:
            m = (idx-idxpm)/(model_depths[idx] -
                             model_depths[idxpm])*(depth-model_depths[idx])
            idx = m + idx
        # If idxpm < 0 then we are between z=0 and depth of first gridcell
        if idxpm < 0:
            # assume z=0 correspons to idx = -model_depths[0]
            idxpm = -model_depths[0]
            m = (idx-idxpm)/(model_depths[idx]-0)*(depth-model_depths[idx])
            idx = m+idx
    return idx


def find_closest_model_point(lon, lat, X, Y, bathy, lon_tol=0.0052,
                             lat_tol=0.00189, allow_land=False):
    """Returns the grid co-ordinates of the closest non-land model point
    to a specified lon/lat.

    .. note::

        This function is deprecated.
        Use :py:func:`geo_tools.find_closest_model_point` instead.
    """
    raise DeprecationWarning(
        'tidetools.find_closest_model_point() has been replaced by '
        'geo_tools.find_closest_model_point()')



def plot_amp_map(X, Y, grid, amp, constituent_name, figsize=(9, 9)):
    """Plot the amplitude of one constituent throughout the whole domain.

    :arg X: specified model longitude
    :type X: numpy array

    :arg Y: specified model latitude
    :type Y: numpy array

    :arg grid: model grid netcdf
    :type grid: netcdf dataset

    :arg amp: amplitude
    :type amp: numpy array

    :arg constituent_name: Name of tidal constituent. Used as subplot title.
    :type constituent_name: str

    :arg figsize: Figure size, (width, height).
    :type figsize: 2-tuple

    :returns: Figure containing plots of observed vs. modelled
              amplitude and phase of the tidal constituent.
    :rtype: Matplotlib figure
    """
    # Make 0 values NaNs so they plot blank
    amp = np.ma.masked_equal(amp, 0)
    # Range of amplitudes to plot
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    viz_tools.set_aspect(ax, coords='map', lats=Y)
    # Plot the coastline and amplitude contours
    viz_tools.plot_coastline(ax, grid, coords='map')
    v2 = np.arange(0, 1.80, 0.10)
    CS = ax.contourf(X, Y, amp, v2)
    CS2 = ax.contour(X, Y, amp, v2, colors='black')
    # Add a colour bar
    cbar = fig.colorbar(CS)
    cbar.add_lines(CS2)
    cbar.set_label('amplitude [m]')
    # Set axes labels and title
    ax.set_label('longitude (deg)')
    ax.set_label('latitude (deg)')
    ax.set_title(
        '{constituent} amplitude (m) for model'
        .format(constituent=constituent_name))
    return fig


def plot_pha_map(X, Y, grid, pha, constituent_name, figsize=(9, 9)):
    """Plot the phase of one constituent throughout the whole domain.

    :arg X: specified model longitude
    :type X: numpy array

    :arg Y: specified model latitude
    :type Y: numpy array

    :arg pha: phase
    :type pha: numpy array

    :arg constituent_name: Name of tidal constituent. Used as subplot title.
    :type constituent_name: str

    :arg figsize: Figure size, (width, height).
    :type figsize: 2-tuple

    :returns: Figure containing plots of observed vs. modelled
              amplitude and phase of the tidal constituent.
    :rtype: Matplotlib figure
    """
    # Make 0 values NaNs so they plot blank
    pha = np.ma.masked_equal(pha, 0)
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    viz_tools.set_aspect(ax, coords='map', lats=Y)
    # Plot the coastline and the phase contours
    viz_tools.plot_coastline(ax, grid, coords='map')
    v2 = np.arange(-180, 202.5, 22.5)
    CS = ax.contourf(X, Y, pha, v2, cmap='gist_rainbow')
    CS2 = ax.contour(X, Y, pha, v2, colors='black', linestyles='solid')
    # Add a colour bar
    cbar = fig.colorbar(CS)
    cbar.add_lines(CS2)
    cbar.set_label('phase [deg]')
    # Set axes labels and title
    ax.set_label('longitude (deg)')
    ax.set_label('latitude (deg)')
    ax.set_title(
        '{constituent} phase (deg) for model'
        .format(constituent=constituent_name))
    return fig


def plot_scatter_pha_amp(Am, Ao, gm, go, constituent_name, figsize=(12, 6),
                         split1=0, split2=0, labels=['', '', '']):
    """Plot scatter plot of observed vs. modelled phase and amplitude

    :arg Am: Modelled amplitude.
    :type Am: Numpy array

    :arg Ao: Observed amplitude.
    :type Ao: NumPy array

    :arg gm: Modelled phase.
    :type gm: NumPy array

    :arg go: Observed phase.
    :type go: NumPy array

    :arg constituent_name: Name of tidal constituent. Used as subplot title.
    :type constituent_name: str

    :arg figsize: Figure size, (width, height).
    :type figsize: 2-tuple

    :arg split1: Change colors at this point in array, if > 0
    :type split1: int

    :arg split2: Change colors at this point in array, if > 0
    :type split2: int

    :arg labels: Labels for three different splits
    :type labels: list of strings

    :returns: Figure containing plots of observed vs. modelled
              amplitude and phase of the tidal constituent.
    :rtype: Matplotlib figure
    """
    fig, (ax_amp, ax_pha) = plt.subplots(1, 2, figsize=figsize)
    ax_amp.set_aspect('equal')
    if split1 == 0:
        ax_amp.scatter(Ao, Am, color='blue', edgecolors='blue')
    else:
        ax_amp.scatter(Ao[:split1], Am[:split1], color='green',
                       edgecolors = 'green', label=labels[0])
        ax_amp.scatter(Ao[split1:split2], Am[split1:split2], color='blue',
                       edgecolors = 'blue', label=labels[1])
        ax_amp.scatter(Ao[split2:], Am[split2:], color='black',
                       edgecolors = 'black', label=labels[2])
    min_value, max_value = ax_amp.set_xlim(0, 1.2)
    ax_amp.set_ylim(min_value, max_value)
    ax_amp.legend(loc='upper left')
    # Equality line
    ax_amp.plot([min_value, max_value], [min_value, max_value], color='red')
    ax_amp.set_xlabel('Observed Amplitude [m]')
    ax_amp.set_ylabel('Modelled Amplitude [m]')
    ax_amp.set_title(
        '{constituent} Amplitude'.format(constituent=constituent_name))
    # Phase plot
    ax_pha.set_aspect('equal')
    if split1 == 0:
        ax_pha.scatter(go, gm, color='blue', edgecolors='blue')
    else:
        ax_pha.scatter(go[:split1], gm[:split1], color='green',
                       edgecolors='green', label=labels[0])
        ax_pha.scatter(go[split1:split2], gm[split1:split2], color='blue',
                       edgecolors='blue', label=labels[1])
        ax_pha.scatter(go[split2:], gm[split2:], color='black',
                       edgecolors='black', label=labels[2])
    min_value, max_value = ax_pha.set_xlim(0, 360)
    ax_pha.set_ylim(min_value, max_value)
    ax_pha.legend(loc='upper left')
    # Equality line
    ax_pha.plot([min_value, max_value], [min_value, max_value], color='red')
    ticks = range(0, 420, 60)
    ax_pha.set_xticks(ticks)
    ax_pha.set_yticks(ticks)
    ax_pha.set_xlabel('Observed Phase [deg]')
    ax_pha.set_ylabel('Modelled Phase [deg]')
    ax_pha.set_title(
        '{constituent} Phase'.format(constituent=constituent_name))
    return fig


def plot_diffs_on_domain(
    diffs, meas_wl_harm, calc_method, constituent_name, grid,
    scale_fac=100,
    legend_scale=0.1,
    figsize=(9, 9),
):
    """Plot differences as circles of varying radius on a map of the
    model domain.

    :arg diffs: Differences calculated between measured and modelled
                values [m].
    :type diffs: numpy array

    :arg meas_wl_harm: Measured water level harmonics read in from csv.
    :type meas_wl_harm: numpy array

    :arg calc_method: Method for calculating differences ('F95' or 'M04')
    :type calc_method: str

    :arg constituent_name: Name of tidal constituent. Used as subplot title.
    :type constituent_name: str

    :arg grid: Netcdf file of grid data.
    :type grid: Netcdf dataset

    :arg scale_fac: Scale factor to make difference dots visible on map.
    :type scale_fac: float

    :arg legend_scale: Size of legend sot; [cm].

    :arg figsize: Figure size, (width, height).
    :type figsize: 2-tuple

    :returns: Figure containing plots of observed vs. modelled
              amplitude and phase of the tidal constituent.
    :rtype: Matplotlib figure
    """
    # Plot the bathy underneath
    bathy, X, Y = get_bathy_data(grid)
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    mesh = ax.contourf(X, Y, bathy, cmap='spring')
    cbar = fig.colorbar(mesh)
    cbar.set_label('depth [m]')
    # Plot the differences as dots of varying radii
    # Multiply the differences by something big to see the results
    # on a map (D is in [m])
    ax.scatter(
        -meas_wl_harm.Lon, meas_wl_harm.Lat,
        s=np.array(diffs) * scale_fac, marker='o',
        c='blue', edgecolors='blue')
    # Legend and labels
    ax.text(
        -124.4, 47.875, 'Diff = {}cm'.format(legend_scale * scale_fac))
    ax.scatter(
        -124.5, 47.9,
        s=legend_scale * scale_fac, marker='o',
        c='blue', edgecolors='blue')
    ax.set_xlabel('Longitude [deg E]')
    ax.set_ylabel('Latitude [deg N]')
    ref = (
        'Foreman et al' if calc_method == 'F95' else 'Masson & Cummins')
    ax.set_title(
        '{constituent} Differences ({ref})'
        .format(constituent=constituent_name, ref=ref))
    return fig


def calc_diffs_meas_mod(runname, loc, grid):
    """Calculate differences between measured and modelled water level
    e.g. (meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all, D_M04_M2_all,Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all = calc_diffs_meas_mod('50s_13Sep-20Sep')

    :arg runname: name of model run
    :type runname: str

    :returns: meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all,
              D_F95_M2_all, D_M04_M2_all,Am_K1_all, Ao_K1_all, gm_K1_all,
              go_K1_all, D_F95_K1_all, D_M04_K1_all
    """
    # Read in the measured data from Foreman et al (1995) and US sites
    meas_wl_harm = pd.read_csv('obs_tidal_wlev_const_all.csv', sep=';')
    meas_wl_harm = meas_wl_harm.rename(
        columns={
            'M2 amp': 'M2_amp',
            'M2 phase (deg UT)': 'M2_pha',
            'K1 amp': 'K1_amp',
            'K1 phase (deg UT)': 'K1_pha',
        })
    # Make an appropriately named csv file for results
    outfile = 'wlev_harm_diffs_'+''.join(runname)+'.csv'
    D_F95_M2_all = []
    D_M04_M2_all = []
    Am_M2_all = []
    Ao_M2_all = []
    gm_M2_all = []
    go_M2_all = []

    D_F95_K1_all = []
    D_M04_K1_all = []
    Am_K1_all = []
    Ao_K1_all = []
    gm_K1_all = []
    go_K1_all = []
    # Get harmonics data
    mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_amp_phase_data(
        runname, loc)
    # Get bathy data
    bathy, X, Y = get_bathy_data(grid)
    with open(outfile, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow([
            'Station Number', 'Station Name', 'Longitude', 'Latitude',
            'Modelled M2 amp', 'Observed M2 amp',
            'Modelled M2 phase', 'Observed M2 phase',
            'M2 Difference Foreman', 'M2 Difference Masson',
            'Modelled K1 amp', 'Observed K1 amp',
            'Modelled K1 phase', 'Observed K1 phase',
            'K1 Difference Foreman', 'K1 Difference Masson',
        ])
        for t in np.arange(0, len(meas_wl_harm.Lat)):
            x1, y1 = geo_tools.find_closest_model_point(
                -meas_wl_harm.Lon[t], meas_wl_harm.Lat[t],
                X, Y, land_mask=bathy.mask)
            if x1:
                # Observed constituents
                Ao_M2 = meas_wl_harm.M2_amp[t]/100  # [m]
                go_M2 = meas_wl_harm.M2_pha[t]   # [degrees UTC]
                Ao_K1 = meas_wl_harm.K1_amp[t]/100  # [m]
                go_K1 = meas_wl_harm.K1_pha[t]   # [degrees UTC]
                # Modelled constituents
                Am_M2 = mod_M2_amp[x1, y1]  # [m]
                gm_M2 = angles.normalize(
                    mod_M2_pha[x1, y1], 0, 360)  # [degrees ????]
                Am_K1 = mod_K1_amp[x1, y1]  # [m]
                gm_K1 = angles.normalize(
                    mod_K1_pha[x1, y1], 0, 360)  # [degrees ????]
                # Calculate differences two ways
                D_F95_M2 = sqrt(
                    (Ao_M2*np.cos(radians(go_M2))
                     - Am_M2*np.cos(radians(gm_M2)))**2
                    + (Ao_M2*np.sin(radians(go_M2))
                       - Am_M2*np.sin(radians(gm_M2)))**2)
                D_M04_M2 = sqrt(
                    0.5 * (Am_M2**2 + Ao_M2**2)
                    - Am_M2*Ao_M2*cos(radians(gm_M2-go_M2)))
                D_F95_K1 = sqrt(
                    (Ao_K1*np.cos(radians(go_K1))
                     - Am_K1*np.cos(radians(gm_K1)))**2
                    + (Ao_K1*np.sin(radians(go_K1))
                       - Am_K1*np.sin(radians(gm_K1)))**2)
                D_M04_K1 = sqrt(
                    0.5 * (Am_K1**2 + Ao_K1**2)
                    - Am_K1*Ao_K1*cos(radians(gm_K1-go_K1)))
                # Write results to csv
                writer.writerow([
                    str(t+1), meas_wl_harm.Site[t],
                    -meas_wl_harm.Lon[t], meas_wl_harm.Lat[t],
                    Am_M2, Ao_M2, gm_M2, go_M2, D_F95_M2, D_M04_M2,
                    Am_K1, Ao_K1, gm_K1, go_K1, D_F95_K1, D_M04_K1])
                # Append the latest result
                Am_M2_all.append(float(Am_M2))
                Ao_M2_all.append(float(Ao_M2))
                gm_M2_all.append(float(gm_M2))
                go_M2_all.append(float(go_M2))
                D_F95_M2_all.append(float(D_F95_M2))
                D_M04_M2_all.append(float(D_M04_M2))
                Am_K1_all.append(float(Am_K1))
                Ao_K1_all.append(float(Ao_K1))
                gm_K1_all.append(float(gm_K1))
                go_K1_all.append(float(go_K1))
                D_F95_K1_all.append(float(D_F95_K1))
                D_M04_K1_all.append(float(D_M04_K1))
            else:
                # If no point found, fill difference fields with 9999
                print(
                    'No point found in current domain for station '
                    + str(t+1)+' :(')
                writer.writerow([
                    str(t+1), meas_wl_harm.Site[t],
                    -meas_wl_harm.Lon[t], meas_wl_harm.Lat[t],
                    9999, 9999])
    return (
        meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all,
        D_F95_M2_all, D_M04_M2_all, Am_K1_all, Ao_K1_all,
        gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all,
    )


def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great-circle distance between two points on a sphere
    from their longitudes and latitudes.

    .. note::

        This function is deprecated.
        Use :py:func:`geo_tools.haversine` instead.
    """
    raise DeprecationWarning(
        'tidetools.haversine() has been replaced by geo_tools.haversine()')


def plot_meas_mod_locations(measlon, measlat, modlon, modlat, X, Y, bathy):
    """Plot two locations on a contour map of bathymetry,
    where bathy, X and Y are returned from get_bathy_data(grid);
    e.g. plot_meas_mod_locations(-124.0, 48.4, -124.2, 48.1,X,Y,bathy)

    :arg measlon: longitude of point 1
    :type measlon: float

    :arg measlat: latitude of point 1
    :type measlat: float

    :arg modlon: longitude of point 2
    :type modlon: float

    :arg modlat: latitude of point 2
    :type modlat: float

    :arg X: specified model longitude
    :type X: numpy array

    :arg Y: specified model latitude
    :type Y: numpy array

    :arg bathy: model bathymetry
    :type bathy: numpy array

    :returns: plots contour plot with 2 points
    """
    plt.contourf(X, Y, bathy)
    plt.colorbar()
    plt.title('Domain of model (depths in m)')
    plt.plot(modlon, modlat, 'g.', markersize=10, label='model')
    plt.plot(measlon, measlat, 'm.', markersize=10, label='measured')
    plt.xlim([modlon-0.1, modlon+0.1])
    plt.ylim([modlat-0.1, modlat+0.1])
    plt.legend(numpoints=1)


def plot_wlev_const_transect(savename, statnums, runname, loc, grid, *args):
    """Plot water level of the modelled M2 and K1 constituents
    and measured M2 and K1 constituents in a transect at specified stations
    e.g. plot_wlev_const_transect('40d','/ocean/klesouef/meopar/)

    :arg savename: tag for saving the pdf pics
    :type savename: str

    :arg statnums: array of station numbers
    :type statnums: numpy array

    :arg runname: unique name of run
    :type runname: str

    :arg loc: location of model results
    :type loc: str

    :arg grid: netcdf dataset of model grid
    :type grid: netcdf dataset

    :arg args: other runname and results location strings,
               in case you want to plot more than set of model results
               on the same figure
    :type args: str

    :returns: plots transect of M2 and K1 water level constituent
    """
    # runname1, loc1, runname2, loc2
    fig1 = plt.figure(figsize=(15, 5))
    ax1 = fig1.add_subplot(111)
    ax1.set_xlabel('Station number [-]')
    ax1.set_ylabel('M2 amplitude [m]')
    fig2 = plt.figure(figsize=(15, 5))
    ax2 = fig2.add_subplot(111)
    ax2.set_xlabel('Station number [-]')
    ax2.set_ylabel('K1 amplitude [m]')
    fig3 = plt.figure(figsize=(15, 5))
    ax3 = fig3.add_subplot(111)
    ax3.set_xlabel('Station number[-]')
    ax3.set_ylabel('M2 phase [degrees]')
    fig4 = plt.figure(figsize=(15, 5))
    ax4 = fig4.add_subplot(111)
    ax4.set_xlabel('Station number[-]')
    ax4.set_ylabel('K1 phase [degrees]')

    # Get the modelled data
    (meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all,
     D_M04_M2_all, Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all,
     D_M04_K1_all) = calc_diffs_meas_mod(runname, loc, grid)
    Am_M2_all = np.array(Am_M2_all)
    Ao_M2_all = np.array(Ao_M2_all)
    gm_M2_all = np.array(gm_M2_all)
    go_M2_all = np.array(go_M2_all)
    Am_K1_all = np.array(Am_K1_all)
    Ao_K1_all = np.array(Ao_K1_all)
    gm_K1_all = np.array(gm_K1_all)
    go_K1_all = np.array(go_K1_all)
    # Just take the model values at the statnums we want
    some_model_amps_M2 = np.array([Am_M2_all[statnums]])
    some_model_amps_K1 = np.array([Am_K1_all[statnums]])
    some_model_phas_M2 = np.array([gm_M2_all[statnums]])
    some_model_phas_K1 = np.array([gm_K1_all[statnums]])
    x = np.array(range(0, len(statnums)))
    # Plot the M2 model data
    ax1.plot(x, some_model_amps_M2[0, :], 'b-o', label='single model')
    # Plot the K1 model data
    ax2.plot(x, some_model_amps_K1[0, :], 'b--o', label='single model')
    ax3.plot(x, some_model_phas_M2[0, :], 'b-o', label='single model')
    ax4.plot(x, some_model_phas_K1[0, :], 'b--o', label='single model')

    if len(args) > 0:
        # Assuming we will only be adding an additional 3 lines,
        # define 3 colours
        colours = ['g', 'm', 'k', 'r', 'y']
        for r in range(0, int(len(args)/2)):
            runname = args[2*r]
            loc = args[2*r+1]
            (meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all,
             D_F95_M2_all, D_M04_M2_all, Am_K1_all, Ao_K1_all, gm_K1_all,
             go_K1_all, D_F95_K1_all, D_M04_K1_all) = calc_diffs_meas_mod(
                runname, loc, grid)
            Am_M2_all = np.array(Am_M2_all)
            Ao_M2_all = np.array(Ao_M2_all)
            gm_M2_all = np.array(gm_M2_all)
            go_M2_all = np.array(go_M2_all)
            Am_K1_all = np.array(Am_K1_all)
            Ao_K1_all = np.array(Ao_K1_all)
            gm_K1_all = np.array(gm_K1_all)
            go_K1_all = np.array(go_K1_all)
            some_model_amps_M2 = np.array([Am_M2_all[statnums]])
            some_model_amps_K1 = np.array([Am_K1_all[statnums]])
            some_model_phas_M2 = np.array([gm_M2_all[statnums]])
            some_model_phas_K1 = np.array([gm_K1_all[statnums]])
            x = np.array(range(0, len(statnums)))
            ax1.plot(
                x, some_model_amps_M2[0, :],
                '-o', color=colours[r], label='model')
            ax2.plot(
                x, some_model_amps_K1[0, :],
                '--o', color=colours[r], label='model')
            ax3.plot(
                x, some_model_phas_M2[0, :],
                '-o', color=colours[r], label='model')
            ax4.plot(
                x, some_model_phas_K1[0, :],
                '--o', color=colours[r], label='model')
    some_meas_amps_M2 = np.array([Ao_M2_all[statnums]])
    some_meas_amps_K1 = np.array([Ao_K1_all[statnums]])
    some_meas_phas_M2 = np.array([go_M2_all[statnums]])
    some_meas_phas_K1 = np.array([go_K1_all[statnums]])
    # M2
    ax1.plot(x, some_meas_amps_M2[0, :], 'r-o', label='measured')
    ax1.set_xticks(x)
    ax1.set_xticklabels(statnums+1)
    ax1.legend(loc='lower right')
    ax1.set_title('Line through stations '+str(statnums))
    fig1.savefig(
        'meas_mod_wlev_transect_M2_'+''.join(runname)+'_'+savename+'.pdf')
    # K1
    ax2.plot(x, some_meas_amps_K1[0, :], 'r--o', label='measured')
    ax2.set_xticks(x)
    ax2.set_xticklabels(statnums+1)
    ax2.legend(loc='lower right')
    ax2.set_title('Line through stations '+str(statnums))
    fig2.savefig(
        'meas_mod_wlev_transect_K1_'+''.join(runname)+'_'+savename+'.pdf')
    # M2
    ax3.plot(x, some_meas_phas_M2[0, :], 'r-o', label='measured')
    ax3.set_xticks(x)
    ax3.set_xticklabels(statnums+1)
    ax3.legend(loc='lower right')
    ax3.set_title('Line through stations '+str(statnums))
    fig3.savefig(
        'meas_mod_wlev_transect_M2_phas'+''.join(runname)+'_'+savename+'.pdf')
    # K1
    ax4.plot(x, some_meas_phas_K1[0, :], 'r--o', label='measured')
    ax4.set_xticks(x)
    ax4.set_xticklabels(statnums+1)
    ax4.legend(loc='lower right')
    ax4.set_title('Line through stations '+str(statnums))
    fig2.savefig(
        'meas_mod_wlev_transect_K1_phas'+''.join(runname)+'_'+savename+'.pdf')


def plot_wlev_transect_map(
    grid, stn_nums,
    stn_file='obs_tidal_wlev_const_all.csv',
    figsize=(9, 9)
):
    """Plot a map of the coastline and the transect of water level stations,
    which are plotted in :py:func:`plot_wlev_M2_const_transect`.

    :arg grid: Bathymetry file.
    :type grid: netcdf dataset

    :arg stn_nums: Station numbers to plot.
    :type stn_nums: numpy array

    :arg stn_file: Name of file containing tidal observation station
                   names, lats/lons, and tidal component amplitudes
                   and phases.
    :type stn_file: str

    :arg figsize: Figure size, (width, height).
    :type figsize: 2-tuple

    :returns: Figure containing plots of observed vs. modelled
              amplitude and phase of the tidal constituent.
    :rtype: Matplotlib figure
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    # Add a coastline
    viz_tools.plot_coastline(ax, grid, coords='map')
    # Get the measured data
    meas_wl_harm = pd.read_csv(stn_file, sep=';')
    sitelats = np.array(meas_wl_harm.Lat[stn_nums])
    sitelons = np.array(-meas_wl_harm.Lon[stn_nums])
    # Plot the transect line
    ax.plot(sitelons, sitelats, 'm-o')
    ax.set_title('Location of Select Stations')
    return fig


def plot_coastline(grid):
    """Plots a map of the coastline.

    .. note::

        This function is deprecated.
        Use :py:func:`viz_tools.plot_coastline` instead.

    :arg grid: netcdf file of bathymetry
    :type grid: netcdf dataset

    :returns: coastline map
    """
    viz_tools.plot_coastline(plt.gc(), grid, coords='map', color='black')


def get_composite_harms2():
    """Take the results of the following runs
    (which are all the same model setup)
    and combine the harmonics into one 'composite' run.

    50s_15-21Sep
    50s_22-25Sep
    50s_26-29Sep
    50s_30Sep-6Oct
    50s_7-13Oct

    :returns: mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha
    """

    runnames = [
        '50s_15-21Sep', '50s_22-25Sep', '50s_26-29Sep', '50s_30Sep-6Oct',
        '50s_7-13Oct']
    runlength = np.array([7.0, 4.0, 4.0, 7.0, 7.0])

    mod_M2_eta_real1 = 0.0
    mod_M2_eta_imag1 = 0.0
    mod_K1_eta_real1 = 0.0
    mod_K1_eta_imag1 = 0.0

    for runnum in range(0, len(runnames)):
        harmT = NC.Dataset(
            '/data/dlatorne/MEOPAR/SalishSea/results/'
            + runnames[runnum]+'/Tidal_Harmonics_eta.nc', 'r')
        # Get imaginary and real components
        mod_M2_eta_real1 += (
            harmT.variables['M2_eta_real'][0, :, :]*runlength[runnum])
        mod_M2_eta_imag1 += (
            harmT.variables['M2_eta_imag'][0, :, :]*runlength[runnum])
        mod_K1_eta_real1 += (
            harmT.variables['K1_eta_real'][0, :, :]*runlength[runnum])
        mod_K1_eta_imag1 += (
            harmT.variables['K1_eta_imag'][0, :, :]*runlength[runnum])
    totaldays = sum(runlength)
    mod_M2_eta_real = mod_M2_eta_real1/totaldays
    mod_M2_eta_imag = mod_M2_eta_imag1/totaldays
    mod_K1_eta_real = mod_K1_eta_real1/totaldays
    mod_K1_eta_imag = mod_K1_eta_imag1/totaldays
    mod_M2_amp = np.sqrt(mod_M2_eta_real**2+mod_M2_eta_imag**2)
    mod_M2_pha = -np.degrees(np.arctan2(mod_M2_eta_imag, mod_M2_eta_real))
    mod_K1_amp = np.sqrt(mod_K1_eta_real**2+mod_K1_eta_imag**2)
    mod_K1_pha = -np.degrees(np.arctan2(mod_K1_eta_imag, mod_K1_eta_real))
    return mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha


def get_composite_harms(runnames, loc):
    """Combine the harmonics from the specified runs into a 'composite' run.

    The runs to be 'composed' must all have the same model setup.

    :arg runnames: Names of the model runs to process;
                   e.g. ('40d', '41d50d', '51d60d').
    :type runnames: tuple

    :arg loc: Location of results folder;
              e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :returns: mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha
    :rtypes: 4-tuple of numpy.ndarray instances
    """
    results = {}
    vars = 'M2_eta_real M2_eta_imag K1_eta_real K1_eta_imag'.split()
    runlengths = {
        runname: get_run_length(runname, loc) for runname in runnames}
    for k, runname in enumerate(runnames):
        filename = os.path.join(loc, runnames[k], 'Tidal_Harmonics_eta.nc')
        harmT = NC.Dataset(filename)
        for var in vars:
            try:
                results[var] += (
                    harmT.variables[var][0, ...] * runlengths[runname])
            except KeyError:
                results[var] = (
                    harmT.variables[var][0, ...] * runlengths[runname])
    totaldays = sum(runlengths.itervalues())
    for var in vars:
        results[var] /= totaldays
    mod_M2_amp = np.sqrt(
        results['M2_eta_real']**2 + results['M2_eta_imag']**2)
    mod_M2_pha = -np.degrees(
        np.arctan2(results['M2_eta_imag'], results['M2_eta_real']))
    mod_K1_amp = np.sqrt(
        results['K1_eta_real']**2 + results['K1_eta_imag']**2)
    mod_K1_pha = -np.degrees(
        np.arctan2(results['K1_eta_imag'], results['K1_eta_real']))
    return mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha


def get_composite_harms_uv(runname, loc):
    """Take the results of the specified runs
    (which must all have the same model setup)
    and combine the harmonics into one 'composite' run.

    :arg runname: name of the model run to process;
                  e.g. runname = '50s_15Sep-21Sep',
                  or if you'd like the harmonics of more than one run
                  to be combined into one picture,
                  give a list of names e.g. '40d','41d50d','51d60d'
    :type runname: str

    :arg loc: location of results folder;
              e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :returns: mod_M2_u_amp, mod_M2_u_pha, mod_M2_v_amp, mod_M2_v_pha,
              mod_K1_u_amp, mod_K1_u_pha, mod_K1_v_amp, mod_K1_v_pha
    """
    runlength = np.zeros((len(runname), 1))
    for k in range(0, len(runname)):
        runlength[k, 0] = get_run_length(runname[k], loc)

    mod_M2_u_real1 = 0.0
    mod_M2_u_imag1 = 0.0
    mod_M2_v_real1 = 0.0
    mod_M2_v_imag1 = 0.0
    mod_K1_u_real1 = 0.0
    mod_K1_u_imag1 = 0.0
    mod_K1_v_real1 = 0.0
    mod_K1_v_imag1 = 0.0

    for runnum in range(0, len(runname)):
        harmU = NC.Dataset(loc+runname[runnum]+'/Tidal_Harmonics_U.nc', 'r')
        # Get imaginary and real components
        mod_M2_u_real1 += (
            harmU.variables['M2_u_real'][0, :, :]*runlength[runnum])
        mod_M2_u_imag1 += (
            harmU.variables['M2_u_imag'][0, :, :]*runlength[runnum])
        mod_K1_u_real1 += (
            harmU.variables['K1_u_real'][0, :, :]*runlength[runnum])
        mod_K1_u_imag1 += (
            harmU.variables['K1_u_imag'][0, :, :]*runlength[runnum])

    for runnum in range(0, len(runname)):
        harmV = NC.Dataset(loc+runname[runnum]+'/Tidal_Harmonics_V.nc', 'r')
        # Get imaginary and real components
        mod_M2_v_real1 += (
            harmV.variables['M2_v_real'][0, :, :]*runlength[runnum])
        mod_M2_v_imag1 += (
            harmV.variables['M2_v_imag'][0, :, :]*runlength[runnum])
        mod_K1_v_real1 += (
            harmV.variables['K1_v_real'][0, :, :]*runlength[runnum])
        mod_K1_v_imag1 += (
            harmV.variables['K1_v_imag'][0, :, :]*runlength[runnum])

    totaldays = sum(runlength)
    mod_M2_u_real = mod_M2_u_real1/totaldays
    mod_M2_u_imag = mod_M2_u_imag1/totaldays
    mod_K1_u_real = mod_K1_u_real1/totaldays
    mod_K1_u_imag = mod_K1_u_imag1/totaldays
    mod_M2_v_real = mod_M2_v_real1/totaldays
    mod_M2_v_imag = mod_M2_v_imag1/totaldays
    mod_K1_v_real = mod_K1_v_real1/totaldays
    mod_K1_v_imag = mod_K1_v_imag1/totaldays

    mod_M2_u_amp = np.sqrt(mod_M2_u_real**2+mod_M2_u_imag**2)
    mod_M2_u_pha = -np.degrees(np.arctan2(mod_M2_u_imag, mod_M2_u_real))
    mod_K1_u_amp = np.sqrt(mod_K1_u_real**2+mod_K1_u_imag**2)
    mod_K1_u_pha = -np.degrees(np.arctan2(mod_K1_u_imag, mod_K1_u_real))
    mod_M2_v_amp = np.sqrt(mod_M2_v_real**2+mod_M2_v_imag**2)
    mod_M2_v_pha = -np.degrees(np.arctan2(mod_M2_v_imag, mod_M2_v_real))
    mod_K1_v_amp = np.sqrt(mod_K1_v_real**2+mod_K1_v_imag**2)
    mod_K1_v_pha = -np.degrees(np.arctan2(mod_K1_v_imag, mod_K1_v_real))

    return (
        mod_M2_u_amp, mod_M2_u_pha, mod_M2_v_amp, mod_M2_v_pha, mod_K1_u_amp,
        mod_K1_u_pha, mod_K1_v_amp, mod_K1_v_pha,
    )


def get_current_harms(runname, loc):
    """Get harmonics of current at a specified lon, lat and depth.

    :arg runname: name of the model run to process;
                  e.g. runname = '50s_15Sep-21Sep'
                  (doesn't deal with multiple runs)
    :type runname: str

    :arg loc: location of results folder;
              e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :returns: mod_M2_u_amp, mod_M2_u_pha, mod_M2_v_amp, mod_M2_v_pha
    """
    # u
    harmu = NC.Dataset(loc+runname+'/Tidal_Harmonics_U.nc', 'r')
    mod_M2_u_real = harmu.variables['M2_u_real'][0, :, :]
    mod_M2_u_imag = harmu.variables['M2_u_imag'][0, :, :]
    # Convert to amplitude and phase
    mod_M2_u_amp = np.sqrt(mod_M2_u_real**2+mod_M2_u_imag**2)
    mod_M2_u_pha = -np.degrees(np.arctan2(mod_M2_u_imag, mod_M2_u_real))
    # v
    harmv = NC.Dataset(loc+runname+'/Tidal_Harmonics_V.nc', 'r')
    mod_M2_v_real = harmv.variables['M2_v_real'][0, :, :]
    mod_M2_v_imag = harmv.variables['M2_v_imag'][0, :, :]
    # Convert to amplitude and phase
    mod_M2_v_amp = np.sqrt(mod_M2_v_real**2+mod_M2_v_imag**2)
    mod_M2_v_pha = -np.degrees(np.arctan2(mod_M2_v_imag, mod_M2_v_real))
    return mod_M2_u_amp, mod_M2_u_pha, mod_M2_v_amp, mod_M2_v_pha


def get_run_length(runname, loc):
    """Get the length of the run in days from the namelist file

    :arg runname: name of the model run to process; e.g. '50s_15Sep-21Sep'
    :type runname: str

    :arg loc: location of results folder;
              e.g. '/ocean/dlatorne/MEOPAR/SalishSea/results'
    :type loc: str

    :returns: length of run in days
    """
    resfile = os.path.join(loc, runname, 'namelist')
    nl = namelist.namelist2dict(resfile)
    timestep = nl['namdom'][0]['rn_rdt']
    start_time = nl['nam_diaharm'][0]['nit000_han']
    end_time = nl['nam_diaharm'][0]['nitend_han']
    run_length = (end_time - start_time + 1) * timestep / 60 / 60 / 24  # days
    return run_length


def ap2ep(Au, PHIu, Av, PHIv):
    """Convert amplitude and phase to ellipse parameters.

    Based on MATLAB script by Zhigang Xu, available at
    http://woodshole.er.usgs.gov/operations/sea-mat/tidal_ellipse-html/ap2ep.m
    """

    # Convert tidal amplitude and phase lag (ap-) parameters into tidal ellipse
    # (ep-) parameters. Please refer to ep2app for its inverse function.
    #
    # Usage:
    #
    # [SEMA,  ECC, INC, PHA]=ap2ep(Au, PHIu, Av, PHIv)
    #
    # where:
    #
    #     Au, PHIu, Av, PHIv are the amplitudes and phase lags (in degrees) of
    #     u- and v- tidal current components. They can be vectors or
    #     matrices or multidimensional arrays.
    #
    #     SEMA: Semi-major axes, or the maximum speed;
    #     ECC:  Eccentricity, the ratio of semi-minor axis over
    #           the semi-major axis; its negative value indicates that the ellipse
    #           is traversed in clockwise direction.
    #     INC:  Inclination, the angles (in degrees) between the semi-major
    #           axes and u-axis.
    #     PHA:  Phase angles, the time (in angles and in degrees) when the
    #           tidal currents reach their maximum speeds,  (i.e.
    #           PHA=omega*tmax).
    #
    #           These four ep-parameters will have the same dimensionality
    #           (i.e., vectors, or matrices) as the input ap-parameters.
    #
    #     w:    Optional. If it is requested, it will be output as matrices
    #           whose rows allow for plotting ellipses and whose columns are
    #           for different ellipses corresponding columnwise to SEMA. For
    #           example, plot(real(w(1,:)), imag(w(1,:))) will let you see
    #           the first ellipse. You may need to use squeeze function when
    #           w is a more than two dimensional array. See example.m.
    #
    # Document:   tidal_ellipse.ps
    #
    # Revisions: May  2002, by Zhigang Xu,  --- adopting Foreman's northern
    # semi major axis convention.
    #
    # For a given ellipse, its semi-major axis is undetermined by 180. If we borrow
    # Foreman's terminology to call a semi major axis whose direction lies in a range of
    # [0, 180) as the northern semi-major axis and otherwise as a southern semi major
    # axis, one has freedom to pick up either northern or southern one as the semi major
    # axis without affecting anything else. Foreman (1977) resolves the ambiguity by
    # always taking the northern one as the semi-major axis. This revision is made to
    # adopt Foreman's convention. Note the definition of the phase, PHA, is still
    # defined as the angle between the initial current vector, but when converted into
    # the maximum current time, it may not give the time when the maximum current first
    # happens; it may give the second time that the current reaches the maximum
    # (obviously, the 1st and 2nd maximum current times are half tidal period apart)
    # depending on where the initial current vector happen to be and its rotating sense.
    #
    # Version 2, May 2002

    # Assume the input phase lags are in degrees and convert them in radians.
    PHIu = PHIu/180*pi
    PHIv = PHIv/180*pi

    # Make complex amplitudes for u and v
    i = cmath.sqrt(-1)
    u = Au*cmath.exp(-i*PHIu)
    v = Av*cmath.exp(-i*PHIv)

    # Calculate complex radius of anticlockwise and clockwise circles:
    wp = (u+i*v)/2      # for anticlockwise circles
    wm = ((u-i*v)/2).conjugate()  # for clockwise circles
    # and their amplitudes and angles
    Wp = abs(wp)
    Wm = abs(wm)
    THETAp = cmath.phase(wp)
    THETAm = cmath.phase(wm)

    # calculate ep-parameters (ellipse parameters)
    SEMA = Wp+Wm             # Semi  Major Axis, or maximum speed
    SEMI = Wp-Wm               # Semin Minor Axis, or minimum speed
    ECC = SEMI/SEMA          # Eccentricity
    # Phase angle, the time (in angle) when the velocity reaches the maximum
    PHA = (THETAm-THETAp)/2
    # Inclination, the angle between the semi major axis and x-axis (or u-axis)
    INC = (THETAm+THETAp)/2

    # convert to degrees for output
    PHA = PHA/pi*180
    INC = INC/pi*180
    THETAp = THETAp/pi*180
    THETAm = THETAm/pi*180

    # Map the resultant angles to the range of [0, 360].
    # PHA=mod(PHA+360, 360)
    PHA = (PHA+360) % 360
    # INC=mod(INC+360, 360)
    INC = (INC+360) % 360

    # Mar. 2, 2002 Revision by Zhigang Xu    (REVISION_1)
    # Change the southern major axes to northern major axes to conform the tidal
    # analysis convention  (cf. Foreman, 1977, p. 13, Manual For Tidal Currents
    # Analysis Prediction, available in www.ios.bc.ca/ios/osap/people/foreman.htm)
    k = float(INC)/180
    INC = INC-k*180
    PHA = PHA+k*180
    PHA = PHA % 360
    return SEMA,  ECC, INC, PHA
    # Authorship Copyright:
    #
    #    The author retains the copyright of this program, while  you are welcome
    # to use and distribute it as long as you credit the author properly and respect
    # the program name itself. Particularly, you are expected to retain the original
    # author's name in this original version or any of its modified version that
    # you might make. You are also expected not to essentially change the name of
    # the programs except for adding possible extension for your own version you
    # might create, e.g. ap2ep_xx is acceptable.  Any suggestions are welcome and
    # enjoy my program(s)!
    #
    #
    # Author Info:
    # _______________________________________________________________________
    #  Zhigang Xu, Ph.D.
    #  (pronounced as Tsi Gahng Hsu)
    #  Research Scientist
    #  Coastal Circulation
    #  Bedford Institute of Oceanography
    #  1 Challenge Dr.
    #  P.O. Box 1006                    Phone  (902) 426-2307 (o)
    #  Dartmouth, Nova Scotia           Fax    (902) 426-7827
    #  CANADA B2Y 4A2                   email xuz@dfo-mpo.gc.ca
    # _______________________________________________________________________
    #
    # Release Date: Nov. 2000,
    # Revised on May. 2002 to adopt Foreman's northern semi-major axis
    # convention.


def convert_to_hours(time_model, reftime='None'):
    """ Interpolates the datetime values into an array of hours from a
        determined starting point

    :arg time_model: array of model output time as datetime objects
    :type time_model: array with datetimes

    :arg reftime: Epoc value. Default 'None', uses time_model[0] as the epoc.
                  **Note:** must add tzinfo = tzutc() in datetime.datetime
                  object.
    :type reftime: date time object

    :returns tp_wrt_epoch, times with respect to the
        beginning of the input in seconds
    """
    if reftime == 'None':
        epoc = time_model[0]
    else:
        epoc = reftime
    tp_wrt_epoc = []
    for t in time_model:
        tp_wrt_epoc.append((t-epoc).total_seconds()/3600)
    return tp_wrt_epoc


def double(x, M2amp, M2pha, K1amp, K1pha, mean):
    """Function for the fit, assuming only M2 and K2 tidal constituents.

    :arg x:
    :type x:

    :arg M2amp: Tidal amplitude of the M2 constituent
    :type M2amp:

    :arg M2pha: Phase lag of M2 constituent
    :type M2pha:

    :arg K1amp: Tidal amplitude of the K1 constituent
    :type K1amp:

    :arg K1pha: Phase lag of K1 constituent
    :type K1pha:

    :returns:(mean + M2amp*np.cos(M2FREQ*x-M2pha*np.pi/180.)
        +K1amp*np.cos(K1FREQ*x-K1pha*np.pi/180.))
    """
    return(
        mean +
        M2amp * np.cos((CorrTides['M2']['freq'] * x - M2pha) * np.pi / 180.) +
        K1amp * np.cos((CorrTides['K1']['freq'] * x - K1pha) * np.pi / 180))


def quadruple(x, M2amp, M2pha, K1amp, K1pha, S2amp, S2pha, O1amp, O1pha, mean):
    """Function for the fit, assuming only 4 constituents of importance are:
        M2, K2, S1 and O1.

    :arg x: Independent variable, time.
    :type x:

    :arg \*amp: Tidal amplitude of the a constituent
    :type \*amp: float

    :arg \*pha: Phase lag of a constituent
    :type \*pha: float

    :returns: function for fitting 4 frequencies
    """
    return(
        mean +
        M2amp * np.cos((CorrTides['M2']['freq'] * x - M2pha) * np.pi / 180) +
        K1amp * np.cos((CorrTides['K1']['freq'] * x - K1pha) * np.pi / 180) +
        S2amp * np.cos((CorrTides['S2']['freq'] * x - S2pha) * np.pi / 180) +
        O1amp * np.cos((CorrTides['O1']['freq'] * x - O1pha) * np.pi / 180))


def sextuple(
        x, M2amp, M2pha, K1amp, K1pha,
        S2amp, S2pha, O1amp, O1pha,
        N2amp, N2pha, P1amp, P1pha, mean):
    """Function for the fit, assuming 6 constituents of importance are:
    M2, K2, S1, O1, N2 and P1.

    :arg x: Independent variable, time.
    :type x:

    :arg \*amp: Tidal amplitude of the a constituent
    :type \*amp: float

    :arg \*pha: Phase lag of a constituent
    :type \*pha: float

    :returns: function for fitting 6 frequencies
    """
    return(
        mean +
        M2amp * np.cos((CorrTides['M2']['freq'] * x - M2pha) * np.pi / 180) +
        K1amp * np.cos((CorrTides['K1']['freq'] * x - K1pha) * np.pi / 180) +
        S2amp * np.cos((CorrTides['S2']['freq'] * x - S2pha) * np.pi / 180) +
        O1amp * np.cos((CorrTides['O1']['freq'] * x - O1pha) * np.pi / 180) +
        N2amp * np.cos((CorrTides['N2']['freq'] * x - N2pha) * np.pi / 180) +
        P1amp * np.cos((CorrTides['P1']['freq'] * x - P1pha) * np.pi / 180))


def octuple(
        x, M2amp, M2pha, K1amp, K1pha,
        S2amp, S2pha, O1amp, O1pha,
        N2amp, N2pha, P1amp, P1pha,
        K2amp, K2pha, Q1amp, Q1pha, mean):
    """Function for the fit, for all the constituents: M2, K2, S1, O1, N2, P1,
    K2 and Q1.

    :arg x: Independent variable, time.
    :type x:

    :arg \*amp: Tidal amplitude of the a constituent
    :type \*amp: float

    :arg \*pha: Phase lag of a constituent
    :type \*pha: float

    :returns: function for fitting 8 frequencies
    """
    return(
        mean +
        M2amp * np.cos((CorrTides['M2']['freq'] * x - M2pha) * np.pi / 180) +
        K1amp * np.cos((CorrTides['K1']['freq'] * x - K1pha) * np.pi / 180) +
        S2amp * np.cos((CorrTides['S2']['freq'] * x - S2pha) * np.pi / 180) +
        O1amp * np.cos((CorrTides['O1']['freq'] * x - O1pha) * np.pi / 180) +
        N2amp * np.cos((CorrTides['N2']['freq'] * x - N2pha) * np.pi / 180) +
        P1amp * np.cos((CorrTides['P1']['freq'] * x - P1pha) * np.pi / 180) +
        K2amp * np.cos((CorrTides['K2']['freq'] * x - K2pha) * np.pi / 180) +
        Q1amp * np.cos((CorrTides['Q1']['freq'] * x - Q1pha) * np.pi / 180))


def convention_pha_amp(fitted_amp, fitted_pha):
    """ This function takes the fitted parameters given for phase and
         amplitude of the tidal analysis and returns them following the
         tidal parameter convention; amplitude is positive and phase
         is between -180 and +180 degrees.

    :arg fitted_amp: The amplitude given by the fitting function.
    :type fitted_amp: float

    :arg fitted_pha: The phase given by the fitting function.
    :type fitted_pha: float

    :return fitted_amp, fitted_pha: The fitted parameters following the
        conventions.
    """

    if fitted_amp < 0:
        fitted_amp = -fitted_amp
        fitted_pha = fitted_pha + 180
    fitted_pha = angles.normalize(fitted_pha, -180, 180)

    return fitted_amp, fitted_pha


def fittit(uaus, time, nconst):
    """Function to find tidal components of a time series over the whole
    area given.

    Can be done over depth, or an area.
    Time must be in axis one, depth in axis two if applicable then the
    y, x if an area.
    In order to calculate the tidal components of an area at a single
    depth the time series must only have 3 dimensions. For a depth
    profile it must only have 2 dimensions

    :arg uaus: The time series to be analyzed.
    :type uaus:  :py:class:'np.ndarray' or float

    :arg time: Time over which the time series is taken in hours.
    :type time: :py:class:'np.ndarray'

    :arg nconst: The amount of tidal constituents used for the analysis.
                 They added in pairs and by order of importance,
                 M2, K1, S2, O1, N2, P1, K2, Q1.
    :type nconst: int

    :returns: a dictionary object containing a phase an amplitude for each
              harmonic constituent, for each orthogonal velocity
    """
    # Setting up the dictionary space for the ap-parameters to be stored
    apparam = collections.OrderedDict()

    # The function with which we do the fit is based on the amount of
    # constituents
    fitfunction = double

    # The first two harmonic parameters are always M2 and K1
    apparam['M2'] = {'amp': [], 'phase': []}
    apparam['K1'] = {'amp': [], 'phase': []}

    if nconst > 2:
        fitfunction = quadruple
        apparam['S2'] = {'amp': [], 'phase': []}
        apparam['O1'] = {'amp': [], 'phase': []}

    if nconst > 4:
        fitfunction = sextuple
        apparam['N2'] = {'amp': [], 'phase': []}
        apparam['P1'] = {'amp': [], 'phase': []}

    if nconst > 6:
        fitfunction = octuple
        apparam['K2'] = {'amp': [], 'phase': []}
        apparam['Q1'] = {'amp': [], 'phase': []}

    # CASE 1: a time series of velocities with depth at a single location.
    if uaus.ndim == 2:
        # The parameters are the same shape as the velocities without the time
        # dimension.
        thesize = uaus.shape[1]
        # creating the right shape of space for each amplitude and phase for
        # every constituent.
        for const, ap in apparam.items():
            for key2 in ap:
                ap[key2] = np.zeros(thesize)

        # Calculates the parameters for one depth and one location at a time
        # from its time series
        for dep in np.arange(0, len(uaus[1])):
            if uaus[:, dep].any() != 0:

                # performs fit of velocity over time using function that is
                # chosen by the amount of constituents
                fitted, cov = curve_fit(fitfunction, time[:], uaus[:, dep])

                # Rotating to have a positive amplitude and a phase between
                # [-180, 180]
                for k in np.arange(nconst):
                    fitted[2*k], fitted[2*k+1] = convention_pha_amp(
                        fitted[2*k], fitted[2*k+1])
                # Putting the amplitude and phase of each constituent of this
                # particlar depth in the right location within the dictionary.
                for const, k in zip(apparam, np.arange(0, nconst)):
                    apparam[const]['amp'][dep] = fitted[2*k]
                    apparam[const]['phase'][dep] = fitted[2*k+1]

    # CASE 2 : a time series of an area of velocities at a single depth
    elif uaus.ndim == 3:
        thesize = (uaus.shape[1], uaus.shape[2])
        for const, ap in apparam.items():
            for key2 in ap:
                ap[key2] = np.zeros(thesize)

        for i in np.arange(0, uaus.shape[1]):
            for j in np.arange(0, uaus.shape[2]):
                if uaus[:, i, j].any() != 0.:
                    fitted, cov = curve_fit(
                        fitfunction, time[:], uaus[:, i, j])
                    for k in np.arange(nconst):
                        fitted[2*k], fitted[2*k+1] = convention_pha_amp(
                            fitted[2*k], fitted[2*k+1])

                    for const, k in zip(apparam, np.arange(0, nconst)):
                        apparam[const]['amp'][i, j] = fitted[2*k]
                        apparam[const]['phase'][i, j] = fitted[2*k+1]

    # CASE 3: a time series of an area of velocities with depth
    elif uaus.ndim == 4:
        thesize = (uaus.shape[1], uaus.shape[2], uaus.shape[3])
        for const, ap in apparam.items():
            for key2 in ap:
                ap[key2] = np.zeros(thesize)

        for dep in np.arange(0, uaus.shape[1]):
            for i in np.arange(0, uaus.shape[2]):
                for j in np.arange(0, uaus.shape[3]):
                    if uaus[:, dep, i, j].any() != 0.:
                        fitted, cov = curve_fit(
                            fitfunction, time[:], uaus[:, dep, i, j])

                        for k in np.arange(nconst):
                            fitted[2*k], fitted[2*k+1] = convention_pha_amp(
                                fitted[2*k], fitted[2*k+1])

                        for const, k in zip(apparam, np.arange(0, nconst)):
                            apparam[const]['amp'][dep, i, j] = fitted[2*k]
                            apparam[const]['phase'][dep, i, j] = fitted[2*k+1]

    # Case 4: a time series of a single location with a single depth.
    else:
        thesize = (0)
        for const, ap in apparam.items():
            for key2 in ap:
                ap[key2] = np.zeros(thesize)

        if uaus[:].any() != 0.:
            fitted, cov = curve_fit(fitfunction, time[:], uaus[:])
            for k in np.arange(nconst):
                fitted[2*k], fitted[2*k+1] = convention_pha_amp(
                    fitted[2*k], fitted[2*k+1])
            for const, k in zip(apparam, np.arange(0, nconst)):
                apparam[const]['amp'] = fitted[2*k]
                apparam[const]['phase'] = fitted[2*k+1]

    # Mask the zero values
    for const, ap in apparam.items():
        for key in ap.keys():
            ap[key] = np.ma.masked_values(ap[key], 0)

    return apparam


def filter_timeseries(record, winlen=39, method='box'):
    """Filter a timeseries.
    
    Developed for wind and tidal filtering, but can be modified for use
    with a variety of timeseries data. The data record should be at least
    half a window length longer at either end than the period of interest
    to accommodate window length shrinking near the array edges.

    *This function can only operate along the 0 axis. Please modify to include
    an axis argument in the future.*
    
    Types of filters (*please add to these*):
    * **box**: simple running mean
    * **doodson**: Doodson bandpass filter (39 winlen required)
    
    :arg record: timeseries record to be filtered
    :type record: :py:class:`numpy.ndarray`, :py:class:`xarray.DataArray`,
                  or :py:class:`netCDF4.Variable`
    
    :arg winlen: window length
    :type winlen: integer
    
    :arg method: type of filter (ex. 'box', 'doodson', etc.)
    :type method: string
    
    :returns filtered: filtered timeseries
    :rtype: same as record
    """
    
    # Preallocate filtered record
    filtered = record.copy()
    
    # Length along time axis
    record_length = record.shape[0]

    # Window length
    w = (winlen - 1) // 2
    
    # Construct weight vector
    weight = np.zeros(w, dtype=int)
    
    # Select filter method
    if method == 'doodson':
        # Doodson bandpass filter (winlen must be 39)
        weight[[1, 2, 5, 6, 10, 11, 13, 16, 18]] = 1
        weight[[0, 3, 8]] = 2
        centerval = 0
    elif method == 'box':
        # Box filter
        weight[:] = 1
        centerval = 1
    else:
        raise ValueError('Invalid filter method: {}'.format(method))
    
    # Loop through record
    for i in range(record_length):
        
        # Adjust window length for end cases
        W = min(i, w, record_length-i-1)
        Weight = weight[:W]
        Weight = np.append(Weight[::-1], np.append(centerval, Weight))
        if sum(Weight) != 0:
            Weight = (Weight/sum(Weight))
        
        # Expand weight dims so it can operate on record window
        for dim in range(record.ndim - 1):
            Weight = Weight[:, np.newaxis]
        
        # Apply mean over window length
        if W > 0:
            filtered[i, ...] = np.sum(record[i-W:i+W+1, ...] * Weight, axis=0)
        else:
            filtered[i, ...] = record[i, ...]
    
    return filtered
