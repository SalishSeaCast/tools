# Copyright 2013-2018 The Salish Sea NEMO Project and
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

# A module to interpolate Live Ocean results onto Salish Sea NEMO grid and
# save boundary forcing files.

import datetime
#import glob
import logging
import os
#import re
#import subprocess as sp
#import sys

import mpl_toolkits.basemap as Basemap
#import netCDF4 as nc
import numpy as np
import xarray as xr
from salishsea_tools import LiveOcean_grid as grid
from salishsea_tools import gsw_calls
from scipy import interpolate

#import math
#import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ---------------------- Interpolation functions ------------------------
def load_SalishSea_boundary_grid(
    fname='/data/nsoontie/MEOPAR/NEMO-forcing/open_boundaries/west/SalishSea_west_TEOS10.nc',
):
    """Load the Salish Sea NEMO model boundary depth, latitudes and longitudes.

    :arg fname str: name of boundary file

    :returns: numpy arrays depth, lon, lat and a tuple shape
    """

    f = nc.Dataset(fname)
    depth = f.variables['deptht'][:]
    lon = f.variables['nav_lon'][:]
    lat = f.variables['nav_lat'][:]
    shape = lon.shape

    return depth, lon, lat, shape


def load_LiveOcean(date, LO_dir='/results/forcing/LiveOcean/downloaded/', LO_file='low_passed_UBC.nc'):

    """Load a time series of Live Ocean results represented by a date, location and filename

    :arg date: date as yyyy-mm-dd
    :type date: string

    :arg LO_dir: directory of Live Ocean file
    :type LO_dir: string

    :arg LO_file: Live Ocean filename
    :type LO_file: string

    :returns: xarray dataset of Live Ocean results
    """
    # Choose file and load
    sdt = datetime.datetime.strptime(date, '%Y-%m-%d')
    file = os.path.join(LO_dir, sdt.strftime('%Y%m%d'), LO_file)

    G, S, T = grid.get_basic_info(file)  # note: grid.py is from Parker
    d = xr.open_dataset(file)

    # Determine z-rho (depth)
    zeta = d.zeta.values[0]
    z_rho = grid.get_z(G['h'], zeta, S)
    # Add z_rho to dataset
    zrho_DA = xr.DataArray(
        np.expand_dims(z_rho, 0),
        dims=['ocean_time', 's_rho', 'eta_rho', 'xi_rho'],
        coords={'ocean_time': d.ocean_time.values[:],
                's_rho': d.s_rho.values[:],
                'eta_rho': d.eta_rho.values[:],
                'xi_rho': d.xi_rho.values[:]},
        attrs={'units': 'metres',
               'positive': 'up',
               'long_name': 'Depth at s-levels',
               'field': 'z_rho ,scalar'})
    d = d.assign(z_rho=zrho_DA)

    return d


def interpolate_to_NEMO_depths(dataset, depBC,
                               var_names = ['salt', 'temp', 'NO3']):
    """ Interpolate variables in var_names from a Live Ocean dataset to NEMO
    depths. LiveOcean land points (including points lower than bathymetry) are
    set to np.nan and then masked.

    :arg dataset: Live Ocean dataset
    :type dataset: xarray Dataset

    :arg depBC: NEMO model depths
    :type depBC: 1D numpy array

    :arg var_names: list of Live Ocean variable names to be interpolated,
                    e.g ['salt', 'temp']
    :type var_names: list of str

    :returns: dictionary containing interpolated numpy arrays for each variable
    """
    interps = {}
    for var_name in var_names:
        var_interp = np.zeros(dataset[var_name][0].shape)
        for j in range(var_interp.shape[1]):
            for i in range(var_interp.shape[2]):
                LO_depths = dataset.z_rho.values[0, :, j, i]
                var = dataset[var_name].values[0, :, j, i]
                var_interp[:, j, i] = np.interp(
                        -depBC, LO_depths, var, left=np.nan)
                    # NEMO depths are positive, LiveOcean are negative
        interps[var_name] = np.ma.masked_invalid(var_interp)

    return interps

def remove_south_of_Tatoosh(interps, imask=6, jmask=17):
    """Removes points south of Tatoosh point because the water masses there
    are different"

    :arg interps: dictionary of 3D numpy arrays.
                     Key represents the variable name.
    :type var_arrrays: dictionary

    :arg imask: longitude points to be removed
    :type imask: int

    :arg jmask: latitude points to be removed
    :type jmask: int

    :returns: interps with values south-west of Tatoosh set to Nan.
    """

    for var in interps.keys():
        for i in range(6):
            for j in range(17):
                interps[var][:, i, j] = np.nan

    interps[var] = np.ma.masked_invalid(interps[var][:])

    return interps


def fill_box(interps, maxk=35):
    """Fill all NaN in the LiveOcean with nearest points (constant depth),
    go as far down as maxk

    :arg interps: dictionary of 3D numpy arrays.
                     Key represents the variable name.
    :type interps: dictionary

    :arg maxk: maximum Live Ocean depth with data
    :type maxk: int

    :returns interps with filled values
    """

    for var in interps.keys():
        for k in range(maxk):
            array = np.ma.masked_invalid(interps[var][k])
            xx, yy = np.meshgrid(range(interps[var].shape[2]),
                                 range(interps[var].shape[1]))
            x1 = xx[~array.mask]
            y1 = yy[~array.mask]
            newarr = array[~array.mask]
            interps[var][k] = interpolate.griddata((x1, y1), newarr.ravel(),
                         (xx, yy), method='nearest')
    return interps

def convect(sigma, interps):
    """Convect interps based on density (sigma).  Ignores variations in cell depths and convects
    vertically

    :arg interps: dictionary of 3D numpy arrays.
                     Key represents the variable name.
    :type interps: dictionary

    :arg sigma: sigma-t, density, 3D array
    :type sigma: numpy array

    :returns sigma, interps stabilized
    """

    var_names = interps.keys()
    kmax, imax, jmax = sigma.shape
    good = False
    while not good:
        good = True
        for k in range(kmax - 1):
            for i in range(imax):
                for j in range(jmax):
                    if sigma[k, i, j] > sigma[k + 1, i, j]:
                        good = False
                        for var in var_names:
                            interps[var][k, i, j], interps[var][
                                k + 1, i, j] = interps[var][
                                    k + 1, i, j], interps[var][k, i, j]
                        sigma[k, i, j], sigma[k + 1, i, j] = sigma[
                            k + 1, i, j], sigma[k, i, j]
    return sigma, interps


def extend_to_depth(interps, maxk=35):
    """Fill all values below level with LiveOcean data with data from above
    start at maxk

    :arg interps: dictionary of 3D numpy arrays.
                     Key represents the variable name.
    :type interps: dictionary

    :arg maxk: maximum Live Ocean depth with data
    :type maxk: int

    :returns interps extended to depth
    """

    for var in interps.keys():
        interps[var][maxk:] = interps[var][maxk-1]

    return interps

def interpolate_to_NEMO_lateral(interps, dataset, NEMOlon, NEMOlat, shape):
    """Interpolates arrays in interps laterally to NEMO grid.
    Assumes these arrays have already been interpolated vertically.
    Note that by this point interps should be a full array

    :arg interps: dictionary of 4D numpy arrays.
                     Key represents the variable name.
    :type interps: dictionary

    :arg dataset: LiveOcean results. Used to look up lateral grid.
    :type dataset: xarray Dataset

    :arg NEMOlon: array of NEMO boundary longitudes
    :type NEMOlon: 1D numpy array

    :arg NEMOlat: array of NEMO boundary longitudes
    :type NEMOlat: 1D numpy array

    :arg shape: the lateral shape of NEMO boundary area.
    :type shape: 2-tuple

    :returns: a dictionary, like var_arrays, but with arrays replaced with
              interpolated values
    """
    # LiveOcean grid
    lonsLO = dataset.lon_rho.values[0, :]
    latsLO = dataset.lat_rho.values[:, 0]
    # interpolate each variable
    interpl = {}
    for var in interps.keys():
        var_new = np.zeros((interps[var].shape[0], shape[0], shape[1]))
        for k in range(var_new.shape[0]):
            var_grid = interps[var][k, :, :]
            var_new[k, ...] = Basemap.interp(
                var_grid, lonsLO, latsLO, NEMOlon, NEMOlat)
        interpl[var] = var_new
    return interpl






# ------------------ Creation of files ------------------------------


def create_LiveOcean_TS_BCs(
    start, end, avg_period, file_frequency,
    nowcast=False, teos_10=True, basename='LO',
    single_nowcast=False,
    bc_dir='/results/forcing/LiveOcean/boundary_condtions/',
    LO_dir='/results/forcing/LiveOcean/downloaded/',
    NEMO_BC='/data/nsoontie/MEOPAR/NEMO-forcing/open_boundaries/west/SalishSea_west_TEOS10.nc'
):
    """Create a series of Live Ocean boundary condition files in date range
    [start, end] for use in the NEMO model.

    :arg str start: start date in format 'yyyy-mm-dd'

    :arg str end: end date in format 'yyyy-mm-dd

    :arg str avg_period: The averaging period for the forcing files.
                         options are '1H' for hourly, '1D' for daily,
                         '7D' for weekly', '1M' for monthly

    :arg str file_frequency: The frequency by which the files will be saved.
                             Options are:

                             * 'yearly' files that contain a year of data and
                               look like :file:`*_yYYYY.nc`
                             * 'monthly' for files that contain a month of
                               data and look like :file:`*_yYYYYmMM.nc`
                             * 'daily' for files that contain a day of data and
                               look like :file:`*_yYYYYmMMdDD.nc`

                             where :kbd:`*` is the basename.

    :arg nowcast: Specifies that the boundary data is to be generated for the
                  nowcast framework. If true, the files are from a single
                  72 hour run beginning on start, in which case, the argument
                  end is ignored. If both this and single_nowcst are false,
                  a set of time series files is produced.
    :type nowcast: boolean

    :arg single_nowcast: Specifies that the boundary data is to be generated for the
                  nowcast framework. If true, the files are from a single tidally
                  averaged value centered at 12 noon on day specified by start,
                  in this case, the argument end is ignored. If both this and nowcast
                  are false, a set of time series files is produced.
    :type nowcast: boolean

    :arg teos_10: specifies that temperature and salinity are saved in
                  teos-10 variables if true. If false, temperature is Potential
                  Temperature and Salinity is Practical Salinity
    :type teos_10: boolean

    :arg str basename: the base name of the saved files.
                       Eg. basename='LO', file_frequency='daily' saves files as
                       'LO_yYYYYmMMdDD.nc'

    :arg str bc_dir: the directory in which to save the results.

    :arg str LO_dir: the directory in which Live Ocean results are stored.

    :arg str NEMO_BC: path to an example NEMO boundary condition file for
                      loading boundary info.

    :returns: Boundary conditions files that were created.
    :rtype: list
    """
    # Check for incoming consistency
    if (nowcast and single_nowcast):
        raise ValueError ('Choose either nowcast or single_nowcast, not both')
    # Create metadeta for temperature and salinity
    var_meta = {'vosaline': {'grid': 'SalishSea2',
                             'long_name': 'Practical Salinity',
                             'units': 'psu'},
                'votemper': {'grid': 'SalishSea2',
                             'long_name': 'Potential Temperature',
                             'units': 'deg C'}
                }

    # Mapping from LiveOcean TS names to NEMO TS names
    LO_to_NEMO_var_map = {'salt': 'vosaline',
                          'temp': 'votemper'}

    # Initialize var_arrays dict
    NEMO_var_arrays = {key: [] for key in LO_to_NEMO_var_map.values()}

    # Load BC information
    depBC, lonBC, latBC, shape = load_SalishSea_boundary_grid(fname=NEMO_BC)

    # Load and interpolate Live Ocean
    if nowcast:
        logger.info(
            'Preparing 48 hours of Live Ocean results. '
            'Argument end={} is ignored'.format(end))
        files = _list_LO_files_for_nowcast(start, LO_dir)
        save_dir = os.path.join(bc_dir, start)
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
    elif single_nowcast:
        logger.info(
            'Preparing one daily average Live Ocean result. '
            'Argument end={} is ignored'.format(end))
        sdt = datetime.datetime.strptime(start, '%Y-%m-%d')
        files = [os.path.join(LO_dir, sdt.strftime('%Y%m%d'), 'low_passed_UBC.nc')]
        save_dir = os.path.join(bc_dir, start)
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)
    else:
        files = _list_LO_time_series_files(start, end, LO_dir)
        save_dir = bc_dir

    LO_dataset = load_LiveOcean(files, resample_interval=avg_period)
    depth_interps = interpolate_to_NEMO_depths(LO_dataset, depBC,
                                               ['salt', 'temp'])
    lateral_interps = interpolate_to_NEMO_lateral(depth_interps, LO_dataset,
                                                  lonBC, latBC, shape)
    lateral_interps['ocean_time'] = LO_dataset.ocean_time

    # convert to TEOS-10 if necessary
    if teos_10:
        var_meta, lateral_interps['salt'], lateral_interps['temp'] = \
            _convert_TS_to_TEOS10(
                var_meta, lateral_interps['salt'], lateral_interps['temp'])

    # divide up data and save into separate files
    _separate_and_save_files(
        lateral_interps, avg_period, file_frequency, basename, save_dir,
        LO_to_NEMO_var_map, var_meta, NEMO_var_arrays, NEMO_BC)
    # make time_counter the record dimension using ncks and compress
    files = glob.glob(os.path.join(save_dir, '*.nc'))
    for f in files:
        cmd = ['ncks', '--mk_rec_dmn=time_counter', '-O', f, f]
        sp.call(cmd)
        cmd = ['ncks', '-4', '-L4', '-O', f, f]
        sp.call(cmd)
    # move files around
    if nowcast:
        filepaths = _relocate_files_for_nowcast(
            start, save_dir, basename, bc_dir)
    elif single_nowcast:
        filepaths = []
        d_file = os.path.join(
            save_dir, '{}_{}.nc'.format(
                basename, sdt.strftime('y%Ym%md%d')))
        filepath = os.path.join(
            bc_dir, '{}_{}.nc'.format(
                basename, sdt.strftime('y%Ym%md%d')))
        os.rename(d_file, filepath)
        filepaths.append(filepath)
        if not os.listdir(save_dir):
            os.rmdir(save_dir)
    else:
        filepaths = files
    return filepaths


def _relocate_files_for_nowcast(start_date, save_dir, basename, bc_dir):
    """Organize the files for use in the nowcast framework.
    Originally, files are save in bc_dir/start/basename_y...nc
    For the nowcast system we want file start_date+1 in bc_dir and
    start_date+2 in bc_dir/fcst

    :arg str start_date: the start_date of the LO simulation in format %Y-%m-%d

    :arg str save_dir: the directory where the boundary files are orginally
    saved. Should be bc_dir/start_date/..

    :arg str basename: The basename of the boundary files,  e.g. LO

    :arg str bc_dir: The directory to save the bc files.

    :returns: Final file paths.
    :rtype: list
    """
    filepaths = []
    rundate = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    for d, subdir in zip([1, 2], ['', 'fcst']):
        next_date = rundate + datetime.timedelta(days=d)
        d_file = os.path.join(
            save_dir, '{}_{}.nc'.format(
                basename, next_date.strftime('y%Ym%md%d')))
        if os.path.isfile(d_file):
            filepath = os.path.join(bc_dir, subdir, os.path.basename(d_file))
            os.rename(d_file, filepath)
            filepaths.append(filepath)
    if not os.listdir(save_dir):
        os.rmdir(save_dir)
    return filepaths


def _list_LO_time_series_files(start, end, LO_dir):
    """ List the Live Ocean files in a given date range [start, end].
    LO nowcast files that form a time series are used.
    Note: If start='2016-06-01' and end= '2016-06-02' results will be a
    list starting with LO_dir/2016-05-31/ocean_his_0025_UBC.nc and ending with
    LO_dir/2016-06-02/ocean_his_0024_UBC.nc.
    The times in these files represent 2016-06-01 00:00:00 to
    2016-06-02 23:00:00.

    :arg str start: start date in format 'yyyy-mm-dd'

    :arg str end: end date in format 'yyyy-mm-dd

    :arg str LO_dir: the file path where Live Ocean results are stored

    :returns: list of Live Ocean file names
    """

    sdt = (datetime.datetime.strptime(start, '%Y-%m-%d')
           - datetime.timedelta(days=1))
    edt = datetime.datetime.strptime(end, '%Y-%m-%d')
    sstr = os.path.join(
        LO_dir, '{}/ocean_his_0025_UBC.nc'.format(sdt.strftime('%Y%m%d')))
    estr = os.path.join(
        LO_dir, '{}/ocean_his_0024_UBC.nc'.format(edt.strftime('%Y%m%d')))

    allfiles = glob.glob(os.path.join(LO_dir, '*/*UBC.nc'))

    files = []
    for filename in allfiles:
        if sstr <= filename <= estr:
            files.append(filename)

    # remove files outside of first 24hours for each day
    regex = re.compile(r'_00[3-7][0-9]|_002[6-9]')
    keeps = [x for x in files if not regex.search(x)]

    keeps.sort()

    return keeps


def _list_LO_files_for_nowcast(rundate, LO_dir):
    """ List 48 hours of Live Ocean files that began on rundate.
    Used for creation of nowcast system boundary conditions.
    Each Live Ocean run date contains 72 hours. This funtcion returns the files
    that represent hours 23 through 71.
    Example: if rundate='2016-06-01'  the listed files will be
    LO_dir/20160601/ocean_his_0025_UBC.nc to
    LO_dir/20160601/ocean_his_0072_UBC.nc
    The times in these files represent 2016-06-02 00:00:00 to
    2016-06-03 23:00:00.

    :arg str rundate: The Live Ocean rundate in format 'yyyy-mm-dd'

    :arg str LO_dir: the file path where Live Ocean results are stored

    :returns: list of Live Ocean file names
    """

    sdt = datetime.datetime.strptime(rundate, '%Y-%m-%d')
    allfiles = glob.glob(os.path.join(LO_dir, sdt.strftime('%Y%m%d'), '*.nc'))
    start_str = 'ocean_his_0025_UBC.nc'
    end_str = 'ocean_his_0072_UBC.nc'
    files_return = []
    for filename in allfiles:
        if os.path.basename(filename) >= start_str:
            if os.path.basename(filename) <= end_str:
                files_return.append(filename)

    files_return.sort(key=os.path.basename)

    return files_return


def _separate_and_save_files(
    interpolated_data, avg_period, file_frequency, basename, save_dir,
    LO_to_NEMO_var_map, var_meta, NEMO_var_arrays, NEMO_BC_file,
):
    """Separates and saves variables in interpolated_data into netCDF files
    given a desired file frequency.

    :arg interpolated_data: a dictionary containing variable arrays and time.
                            Keys are LO variable names.
    :type interpolated_data: dictionary of numpy arrays for varables and an
                             xarray dataarray for time.

    :arg str avg_period: The averaging period for the forcing files.
                         options are '1H' for hourly, '1D' for daily,
                         '7D' for weekly, '1M' for monthly

    :arg str file_frequency: The frequency by which the files will be saved.
                             Options are:
                             * 'yearly' files that contain a year of data and
                               look like *_yYYYY.nc
                             * 'monthly' for files that contain a month of
                               data and look like *_yYYYYmMM.nc
                             * 'daily' for files that contain a day of data and
                               look like *_yYYYYmMMdDD.nc
                             where * is the basename.

    :arg str basename: the base name of the saved files.
                       Eg. basename='LO', file_frequency='daily' saves files as
                       'LO_yYYYYmMMdDD.nc'

    :arg str save_dir: the directory in which to save the results

    :arg LO_to_NEMO_var_map: a dictionary mapping between LO variable names
                            (keys) and NEMO variable names (values)
    :type LO_to_NEMO_var_map: a dictionary with string key-value pairs

    :arg var_meta: metadata for each variable in var_arrays.
                   Keys are NEMO variable names.
    :type var_meta: a dictionary of dictionaries with key-value pairs of
                    metadata

    :arg NEMO_var_arrays: a dictionary containing the boundary data to be
                          saved.
    :type NEMO_var_arrays: dictionary of numpy arrays

    :arg str NEMO_BC_file: path to an example NEMO boundary condition file for
                           loading boundary info.
    """
    time_units = {'1H': 'hours', '1D': 'days', '7D': 'weeks', '1M': 'months'}
    index = 0
    first = datetime.datetime.strptime(
        str(interpolated_data['ocean_time'].values[0])[0:-3],
        '%Y-%m-%dT%H:%M:%S.%f'
    )
    # I don't really like method of retrieving the date from LO results.
    # Is it necessary? .
    first = first.replace(second=0, microsecond=0)
    for counter, t in enumerate(interpolated_data['ocean_time']):
        date = datetime.datetime.strptime(str(t.values)[0:-3],
                                          '%Y-%m-%dT%H:%M:%S.%f')
        conditions = {
            'yearly': date.year != first.year,
            'monthly': date.month != first.month,
            # above doesn't work if same months, different year...
            'daily': date.date() != first.date()
        }
        filenames = {
            'yearly': os.path.join(save_dir,
                                   '{}_y{}.nc'.format(basename, first.year)
                                   ),
            'monthly': os.path.join(save_dir,
                                    '{}_y{}m{:02d}.nc'.format(basename,
                                                              first.year,
                                                              first.month)
                                    ),
            'daily': os.path.join(save_dir,
                                  '{}_y{}m{:02d}d{:02d}.nc'.format(basename,
                                                                   first.year,
                                                                   first.month,
                                                                   first.day)
                                  )
        }
        if conditions[file_frequency]:
            for LO_name, NEMO_name in LO_to_NEMO_var_map.items():
                NEMO_var_arrays[NEMO_name] = \
                    interpolated_data[LO_name][index:counter, :, :, :]
            _create_sub_file(
                first, time_units[avg_period], NEMO_var_arrays, var_meta,
                NEMO_BC_file, filenames[file_frequency])
            first = date
            index = counter
        elif counter == interpolated_data['ocean_time'].values.shape[0] - 1:
            for LO_name, NEMO_name in LO_to_NEMO_var_map.items():
                NEMO_var_arrays[NEMO_name] = \
                    interpolated_data[LO_name][index:, :, :, :]
            _create_sub_file(first, time_units[avg_period], NEMO_var_arrays,
                             var_meta, NEMO_BC_file, filenames[file_frequency])


def _create_sub_file(date, time_unit, var_arrays, var_meta, NEMO_BC, filename):
    """Save a netCDF file for boundary data stored in var_arrays.

    :arg date: Date from which time in var_arrays is measured.
    :type date: datetime object

    :arg str time_unit: Units that time in var_arrays is measured in.
                        e.g 'days' or 'weeks' or 'hours'

    :arg var_arrays: a dictionary containing the boundary data to be saved.
    :type var_arrays: dictionary of numpy arrays

    :arg var_meta: metadata for each variable in var_arrays
    :type var_meta: a dictionary of dictionaries with key-value pairs of
                    metadata

    :arg str NEMO_BC: path to a current NEMO boundary file.
                      Used for looking up boundary indices etc.

    :arg str filename: The name of the file to be saved.
    """
    # Set up xarray Dataset
    ds = xr.Dataset()

    # Load BC information
    f = nc.Dataset(NEMO_BC)
    depBC = f.variables['deptht']

    # Copy variables and attributes of non-time dependent variables
    # from a previous BC file
    keys = list(f.variables.keys())
    for var_name in var_arrays:
        if var_name in keys:  # check that var_name can be removed
            keys.remove(var_name)
    keys.remove('time_counter')  # Allow xarray to build these arrays
    keys.remove('deptht')
    # Now iterate through remaining variables in old BC file and add to dataset
    for key in keys:
        var = f.variables[key]
        temp_array = xr.DataArray(
            var,
            name=key,
            dims=list(var.dimensions),
            attrs={att: var.getncattr(att) for att in var.ncattrs()})
        ds = xr.merge([ds, temp_array])
    # Add better units information nbidta etc
    # for varname in ['nbidta', 'nbjdta', 'nbrdta']:
    #    ds[varname].attrs['units'] = 'index'
    # Now add the time-dependent model variables
    for var_name, var_array in var_arrays.items():
        data_array = xr.DataArray(
            var_array,
            name=var_name,
            dims=['time_counter', 'deptht', 'yb', 'xbT'],
            coords={
                'deptht': (['deptht'], depBC[:]),
                'time_counter': np.arange(var_array.shape[0])
            },
            attrs=var_meta[var_name])
        ds = xr.merge([ds, data_array])
    # Fix metadata on time_counter
    ds['time_counter'].attrs['units'] = \
        '{} since {}'.format(time_unit, date.strftime('%Y-%m-%d %H:%M:%S'))
    ds['time_counter'].attrs['time_origin'] = \
        date.strftime('%Y-%m-%d %H:%M:%S')
    ds['time_counter'].attrs['long_name'] = 'Time axis'
    # Add metadata for deptht
    ds['deptht'].attrs = {att: depBC.getncattr(att) for att in depBC.ncattrs()}
    # Add some global attributes
    ds.attrs = {
        'acknowledgements':
            'Live Ocean http://faculty.washington.edu/pmacc/LO/LiveOcean.html',
        'creator_email': 'nsoontie@eos.ubc.ca',
        'creator_name': 'Salish Sea MEOPAR Project Contributors',
        'creator_url': 'https://salishsea-meopar-docs.readthedocs.org/',
        'institution': 'UBC EOAS',
        'institution_fullname': ('Earth, Ocean & Atmospheric Sciences,'
                                 ' University of British Columbia'),
        'summary': ('Temperature and Salinity from the Live Ocean model'
                    ' interpolated in space onto the Salish Sea NEMO Model'
                    ' western open boundary.'),
        'source': ('http://nbviewer.jupyter.org/urls/bitbucket.org/'
                   'salishsea/analysis-nancy/raw/tip/notebooks/'
                   'LiveOcean/Interpolating%20Live%20Ocean%20to%20'
                   'our%20boundary.ipynb'),
        'history':
            ('[{}] File creation.'
             .format(datetime.datetime.today().strftime('%Y-%m-%d')))
    }
    ds.to_netcdf(filename)
    logger.debug('Saved {}'.format(filename))


def _convert_TS_to_TEOS10(var_meta, sal, temp):
    """Convert Practical Salinity and potential temperature to Reference
       Salinity and Conservative Temperature using gsw matlab functions.

    :arg var_meta: dictionary of metadata for salinity and temperature.
                   Must have keys vosaline and votemper, each with a sub
                   dictionary with keys long_name and units
    :type var_meta: dictionary of dictionaries

    :arg sal: salinity data
    :type sal: numpy array

    :arg temp: temperature daya
    :type temp: numpy array

    :returns: updated meta data, salinity and temperature"""
    # modify metadata
    new_meta = var_meta.copy()
    new_meta['vosaline']['long_name'] = 'Reference Salinity'
    new_meta['vosaline']['units'] = 'g/kg'
    new_meta['votemper']['long_name'] = 'Conservative Temperature'
    # Convert salinity from practical to reference salinity
    sal_ref = gsw_calls.generic_gsw_caller('gsw_SR_from_SP.m',
                                           [sal[:], ])
    # Conver temperature from potential to consvervative
    temp_cons = gsw_calls.generic_gsw_caller('gsw_CT_from_pt.m',
                                             [sal_ref[:], temp[:], ])
    return new_meta, sal_ref, temp_cons


# Command-line interface to create boundary files from Live Ocean results
# for use in nowcast, forecast and forecast2
#
# See the SalishSeaNowcast.nowcast.workers.make_live_ocean_files worker for
# the nowcast automation code that does this job
if __name__ == '__main__':
    # Configure logging so that information messages appear on stderr
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    create_files_for_nowcast(sys.argv[1])
