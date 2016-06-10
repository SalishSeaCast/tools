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

"""A library of Python functions for working with netCDF files.

Included are functions for:

* exploring the attributes of netCDF files
* managing those attributes during netCDF file creation and updating
* obtaining variable values from netCDF files
* creation of special purpose netCDF files
* combining per-processor sub-domain output files fron NEMO into a single
  netCDF file
"""
from __future__ import division

from collections import namedtuple
from datetime import (
    datetime,
    timedelta,
)
import os

import arrow
import netCDF4 as nc
import numpy as np

from salishsea_tools import hg_commands as hg


__all__ = [
    'check_dataset_attrs',
    'combine_subdomain',
    'dataset_from_path',
    'generate_pressure_file',
    'generate_pressure_file_ops',
    'init_dataset_attrs',
    'show_dataset_attrs',
    'show_dimensions',
    'show_variables',
    'show_variable_attrs',
    'ssh_timeseries_at_point',
    'time_origin',
    'timestamp',
    'uv_wind_timeseries_at_point',
]


def dataset_from_path(path, *args, **kwargs):
    """Return a dataset constructed from the file given by :kbd:`path`.

    This is a shim that facilitates constructing a
    :py:class:`netCDF4.Dataset` instance from a file that is identified
    by path/filename that is either a string or a :py:class:`pathlib.Path`
    instance.
    The :py:class:`netCDF4.Dataset` constructor cannot handle
    :py:class:`pathlib.Path` instances.

    :arg path: Path/filename to construct the dataset from.
    :type path: :py:class:`pathlib.Path` or :py:class`str`

    :arg list args: Positional arguments to pass through to the
                    :py:class:`netCDF4.Dataset` constructor.

    :arg dict kwargs: Keyword arguments to pass through to the
                      :py:class:`netCDF4.Dataset` constructor.

    :returns: Dataset from file at :kbd:`path`.
    :rtype: :py:class:`netCDF4.Dataset`

    :raises: :py:exc:`IOError` if there the :py:class:`netCDF4.Dataset`
             constructor raises a :py:exc:`RuntimeError` that indicates
             that the file or directory at path is not found.
    """
    try:
        return nc.Dataset(str(path), *args, **kwargs)
    except RuntimeError as e:
        if str(e) == 'No such file or directory':
            raise IOError('No such file or directory')
        else:
            raise


def show_dataset_attrs(dataset):
    """Print the global attributes of the netCDF dataset.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    print('file format: {}'.format(dataset.file_format))
    for attr in dataset.ncattrs():
        print('{}: {}'.format(attr, dataset.getncattr(attr)))


def show_dimensions(dataset):
    """Print the dimensions of the netCDF dataset.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    for dim in dataset.dimensions.values():
        print(dim)


def show_variables(dataset):
    """Print the variable names in the netCDF dataset as a list.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    print(dataset.variables.keys())


def show_variable_attrs(dataset, *vars):
    """Print the variable attributes of the netCDF dataset.

    If variable instances are given as optional arguments,
    only those variable's attributes are printed.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`

    :arg vars: Variables to print attributes for
    :type vars: :py:class:`netCDF4.Variable1`
    """
    if vars:
        for var in vars:
            print(dataset.variables[var])
    else:
        for var in dataset.variables.values():
            print(var)


def time_origin(dataset, time_var='time_counter'):
    """Return the time_var.time_origin value.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`

    :arg time_var: name of time variable
    :type time_var: str

    :returns: Value of the time_origin attribute of the time_counter
              variable.
    :rtype: :py:class:`Arrow` instance
    """
    try:
        time_counter = dataset.variables[time_var]
    except KeyError:
        raise KeyError('dataset does not have time_counter variable')
    try:
        time_origin = time_counter.time_origin.title()
    except AttributeError:
        raise AttributeError(
            'NetCDF: '
            'time_counter variable does not have time_origin attribute')
    value = arrow.get(
        time_origin,
        ['YYYY-MMM-DD HH:mm:ss',
         'YYYY-MM-DD HH:mm:ss'])
    return value


def timestamp(dataset, tindex, time_var='time_counter'):
    """Return the time stamp of the tindex time_counter value(s) in dataset.

    The time stamp is calculated by adding the time_counter[tindex] value
    (in seconds) to the dataset's time_counter.time_origin value.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`

    :arg tindex: time_counter variable index.
    :type tindex: int or list

    :arg time_var: name of the time variable
    :type time_var: str

    :returns: Time stamp value(s) at tindex in the dataset.
    :rtype: :py:class:`Arrow` instance or list of instances
    """
    time_orig = time_origin(dataset, time_var=time_var)
    time_counter = dataset.variables[time_var]
    try:
        iter(tindex)
    except TypeError:
        tindex = [tindex]
    results = []
    for i in tindex:
        try:
            results.append(time_orig + timedelta(seconds=time_counter[i]))
        except IndexError:
            raise IndexError(
                'time_counter variable has no tindex={}'.format(tindex))
    if len(results) > 1:
        return results
    else:
        return results[0]


def ssh_timeseries_at_point(grid_T, j, i, datetimes=False):
    """Return the sea surface height and time counter values
    at a single grid point from a NEMO tracer results dataset.

    :arg grid_T: Tracer results dataset from NEMO.
    :type grid_T: :py:class:`netCDF4.Dataset`

    :arg int j: j-direction (longitude) index of grid point to get sea surface
                height at.

    :arg int i: i-direction (latitude) index of grid point to get sea surface
                height at.

    :arg boolean datetimes: Return time counter values as
                            :py:class:`datetime.datetime` objects if
                            :py:obj:`True`, otherwise return them as
                            :py:class:`arrow.Arrow` objects (the default).

    :returns: 2-tuple of 1-dimensional :py:class:`numpy.ndarray` objects.
              The :py:attr:`ssh` attribute holds the sea surface heights,
              and the :py:attr:`time` attribute holds the time counter
              values.
    :rtype: :py:class:`collections.namedtuple`
    """
    ssh = grid_T.variables['sossheig'][:, j, i]
    time = timestamp(grid_T, range(len(ssh)))
    if datetimes:
        time = np.array([a.datetime for a in time])
    ssh_ts = namedtuple('ssh_ts', 'ssh, time')
    return ssh_ts(ssh, np.array(time))


def uv_wind_timeseries_at_point(grid_weather, j, i, datetimes=False):
    """Return the u and v wind components and time counter values
    at a single grid point from a weather forcing dataset.

    :arg grid_weather: Weather forcing dataset, typically from an
                       :file:`ops_yYYYYmMMdDD.nc` file produced by the
                       :py:mod:`nowcast.workers.grid_to_netcdf` worker.
    :type grid_weather: :py:class:`netCDF4.Dataset`

    :arg int j: j-direction (longitude) index of grid point to get wind
                components at.

    :arg int i: i-direction (latitude) index of grid point to get wind
                components at.

    :arg boolean datetimes: Return time counter values as
                            :py:class:`datetime.datetime` objects if
                            :py:obj:`True`, otherwise return them as
                            :py:class:`arrow.Arrow` objects (the default).

    :returns: 2-tuple of 1-dimensional :py:class:`numpy.ndarray` objects,
              The :py:attr:`u` attribute holds the u-direction wind
              component,
              The :py:attr:`v` attribute holds the v-direction wind
              component,
              and the :py:attr:`time` attribute holds the time counter
              values.
    :rtype: :py:class:`collections.namedtuple`
    """
    u_wind = grid_weather.variables['u_wind'][:, j, i]
    v_wind = grid_weather.variables['v_wind'][:, j, i]
    time = timestamp(grid_weather, range(len(u_wind)))
    if datetimes:
        time = np.array([a.datetime for a in time])
    wind_ts = namedtuple('wind_ts', 'u, v, time')
    return wind_ts(u_wind, v_wind, np.array(time))


def init_dataset_attrs(
    dataset,
    title,
    notebook_name,
    nc_filepath,
    comment='',
    quiet=False,
):
    """Initialize the required global attributes of the netCDF dataset.

    If an attribute with one of the required attribute names is already
    set on the dataset it will not be overwritten,
    instead a warning will be printed,
    unless quiet==True.

    With quiet==False
    (the default)
    the dataset attributes and their values are printed.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`

    :arg title: Title for the dataset
    :type title: str

    :arg notebook_name: Name of the IPython Notebook being used to create
                        or update the dataset.
                        If empty the source attribute value will be set
                        to REQUIRED and must therefore be handled in a
                        subsequent operation.
    :type notebook_name: str

    :arg nc_filepath: Relative path and filename of the netCDF file being
                      created or updated.
                      If empty the references attribute value will be set
                      to REQUIRED and must therefore be handled in a
                      subsequent operation.
    :type nc_filepath: str

    :arg comment: Comment(s) for the dataset
    :type comment: str

    :arg quiet: Suppress printed output when True; defaults to False
    :type quiet: Boolean
    """
    reqd_attrs = (
        ('Conventions', 'CF-1.6'),
        ('title', title),
        ('institution', ('Dept of Earth, Ocean & Atmospheric Sciences, '
                         'University of British Columbia')),
        ('source', _notebook_hg_url(notebook_name)),
        ('references', _nc_file_hg_url(nc_filepath)),
        ('history', (
            '[{:%Y-%m-%d %H:%M:%S}] Created netCDF4 zlib=True dataset.'
            .format(datetime.now()))),
        ('comment', comment),
    )
    for name, value in reqd_attrs:
        if name in dataset.ncattrs():
            if not quiet:
                print('Existing attribute value found, not overwriting: {}'
                      .format(name))
        else:
            dataset.setncattr(name, value)
    if not quiet:
        show_dataset_attrs(dataset)


def _notebook_hg_url(notebook_name):
    """Calculate a Bitbucket URL for an IPython Notebook.

    It is assumed that this function is being called from a file that
    resides in a Mercurial repository with a default path that points
    to Bitbucket.org.

    The URL is based on repo's default path,
    the current working directory path,
    and notebook_name.

    :arg notebook_name: Name of the IPython Notebook to calculate the
                        Bitbucket URL for
    :type notebook_name: str

    :returns: The Bitbucket URL for notebook_name
    :rtype: str
    """
    if not notebook_name:
        return 'REQUIRED'
    default_url = hg.default_url()
    try:
        bitbucket, repo_path = default_url.partition('bitbucket.org')[1:]
    except AttributeError:
        return 'REQUIRED'
    repo = os.path.split(repo_path)[-1]
    local_path = os.getcwd().partition(repo)[-1]
    if not notebook_name.endswith('.ipynb'):
        notebook_name += '.ipynb'
    url = os.path.join(
        'https://', bitbucket, repo_path[1:], 'src', 'tip',
        local_path[1:], notebook_name)
    return url


def _nc_file_hg_url(nc_filepath):
    """Calculate a Bitbucket URL for nc_filepath.

    It is assumed that nc_filepath is a relative path to a netCDF file
    that resides in a Mercurial repositorywith a default path that points
    to Bitbucket.org.

    :arg nc_filepath: Relative path and filename of the netCDF file
                        to calculate the Bitbucket URL for
    :type nc_filepath: str

    :returns: The Bitbucket URL for the nc_filepath netCDF file
    :rtype: str
    """
    rel_path = ''.join(nc_filepath.rpartition('../')[:2])
    try:
        repo_path = nc_filepath.split(rel_path)[1]
    except ValueError:
        return 'REQUIRED'
    repo, filepath = repo_path.split('/', 1)
    default_url = hg.default_url(os.path.join(rel_path, repo))
    try:
        bitbucket, repo_path = default_url.partition('bitbucket.org')[1:]
    except AttributeError:
        return 'REQUIRED'
    url = os.path.join(
        'https://', bitbucket, repo_path[1:], 'src', 'tip', filepath)
    return url


def check_dataset_attrs(dataset):
    """Check that required dataset and variable attributes are present
    and that they are not empty.

    :arg dataset: netcdf dataset object
    :type dataset: :py:class:`netCDF4.Dataset`
    """
    reqd_dataset_attrs = (
        'Conventions', 'title', 'institution', 'source', 'references',
        'history', 'comment')
    reqd_variable_attrs = ('units', 'long_name')
    for attr in reqd_dataset_attrs:
        if attr not in dataset.ncattrs():
            print('Missing required dataset attribute: {}'.format(attr))
            continue
        if attr != 'comment':
            value = dataset.getncattr(attr)
            if value in ('', 'REQUIRED'):
                print('Missing value for dataset attribute: {}'.format(attr))
    for var_name, var in dataset.variables.items():
        for attr in reqd_variable_attrs:
            if attr not in var.ncattrs():
                print('Missing required variable attribute for {}: {}'
                      .format(var_name, attr))
                continue
            value = var.getncattr(attr)
            if not value:
                print('Missing value for variable attribute for {}: {}'
                      .format(var_name, attr))


def generate_pressure_file(filename, p_file, t_file, alt_file, day):
    """ Generates a file with CGRF pressure corrected to sea level.

    :arg filename: full path name where the corrected pressure should be saved
    :type filename: string

    :arg p_file: full path name of the uncorrected CGRF pressure
    :type p_file: string

    :arg t_file: full path name of the corresponding CGRF temperature
    :type t_file: string

    :arg alt_file: full path name of the altitude of CGRF cells
    :type alt_file: string

    :arg day: the date
    :type day: arrow
    """
    # load data
    f = nc.Dataset(p_file)
    press = f.variables['atmpres']
    f = nc.Dataset(t_file)
    temp = f.variables['tair']
    time = f.variables['time_counter']
    lon = f.variables['nav_lon']
    lat = f.variables['nav_lat']
    f = nc.Dataset(alt_file)
    alt = f.variables['alt']

    # correct pressure
    press_corr = np.zeros(press.shape)
    for k in range(press.shape[0]):
        press_corr[k, :, :] = _slp(alt, press[k, :, :], temp[k, :, :])

    # Create netcdf
    slp_file = nc.Dataset(filename, 'w', zlib=True)
    description = 'corrected sea level pressure'
    # dataset attributes
    init_dataset_attrs(
        slp_file,
        title=(
            'CGRF {} forcing dataset for {}'
            .format(description, day.format('YYYY-MM-DD'))),
        notebook_name='',
        nc_filepath='',
        comment=(
            'Processed and adjusted from '
            'goapp.ocean.dal.ca::canadian_GDPS_reforecasts_v1 files.'),
        quiet=True,
    )
    # dimensions
    slp_file.createDimension('time_counter', 0)
    slp_file.createDimension('y', press_corr.shape[1])
    slp_file.createDimension('x', press_corr.shape[2])
    # time
    time_counter = slp_file.createVariable(
        'time_counter', 'double', ('time_counter',))
    time_counter.calendar = time.calendar
    time_counter.long_name = time.long_name
    time_counter.title = time.title
    time_counter.units = time.units
    time_counter[:] = time[:]
    time_counter.valid_range = time.valid_range
    # lat/lon variables
    nav_lat = slp_file.createVariable('nav_lat', 'float32', ('y', 'x'))
    nav_lat.long_name = lat.long_name
    nav_lat.units = lat.units
    nav_lat.valid_max = lat.valid_max
    nav_lat.valid_min = lat.valid_min
    nav_lat.nav_model = lat.nav_model
    nav_lat[:] = lat
    nav_lon = slp_file.createVariable('nav_lon', 'float32', ('y', 'x'))
    nav_lon.long_name = lon.long_name
    nav_lon.units = lon.units
    nav_lon.valid_max = lon.valid_max
    nav_lon.valid_min = lon.valid_min
    nav_lon.nav_model = lon.nav_model
    nav_lon[:] = lon
    # Pressure
    atmpres = slp_file.createVariable(
        'atmpres', 'float32', ('time_counter', 'y', 'x'))
    atmpres.long_name = 'Sea Level Pressure'
    atmpres.units = press.units
    atmpres.valid_min = press.valid_min
    atmpres.valid_max = press.valid_max
    atmpres.missing_value = press.missing_value
    atmpres.axis = press.axis
    atmpres[:] = press_corr[:]

    slp_file.close()


def generate_pressure_file_ops(filename, p_file, t_file, alt_file, day):
    """ Generates a file with CGRF pressure corrected to sea level.

    :arg filename: full path name where the corrected pressure should be saved
    :type filename: string

    :arg p_file: full path name of the uncorrected CGRF pressure
    :type p_file: string

    :arg t_file: full path name of the corresponding CGRF temperature
    :type t_file: string

    :arg alt_file: full path name of the altitude of CGRF cells
    :type alt_file: string

    :arg day: the date
    :type day: arrow
    """
    # load data
    f = nc.Dataset(p_file)
    press = f.variables['atmpres']
    f = nc.Dataset(t_file)
    temp = f.variables['tair']
    time = f.variables['time_counter']
    lon = f.variables['nav_lon']
    lat = f.variables['nav_lat']
    f = nc.Dataset(alt_file)
    alt = f.variables['HGT_surface']
    lat_a = f.variables['latitude']
    lon_a = f.variables['longitude']

    alt, lon_a, lat_a = _truncate_height(alt, lon_a, lat_a, lon, lat)

    # correct pressure
    press_corr = np.zeros(press.shape)
    for k in range(press.shape[0]):
        press_corr[k, :, :] = _slp(alt, press[k, :, :], temp[k, :, :])

    # Create netcdf
    slp_file = nc.Dataset(filename, 'w', zlib=True)
    description = 'corrected sea level pressure'
    # dataset attributes
    init_dataset_attrs(
        slp_file,
        title=(
            'GRIB2 {} forcing dataset for {}'
            .format(description, day.format('YYYY-MM-DD'))),
        notebook_name='',
        nc_filepath='',
        comment=(
            'Processed and adjusted from '
            'GEM 2.5km operational model'),
        quiet=True,
    )
    # dimensions
    slp_file.createDimension('time_counter', 0)
    slp_file.createDimension('y', press_corr.shape[1])
    slp_file.createDimension('x', press_corr.shape[2])
    # time
    time_counter = slp_file.createVariable(
        'time_counter', 'double', ('time_counter',))
    time_counter.long_name = time.long_name
    time_counter.units = time.units
    time_counter[:] = time[:]
    # lat/lon variables
    nav_lat = slp_file.createVariable('nav_lat', 'float32', ('y', 'x'))
    nav_lat.long_name = lat.long_name
    nav_lat.units = lat.units
    nav_lat[:] = lat
    nav_lon = slp_file.createVariable('nav_lon', 'float32', ('y', 'x'))
    nav_lon.long_name = lon.long_name
    nav_lon.units = lon.units
    nav_lon[:] = lon
    # Pressure
    atmpres = slp_file.createVariable(
        'atmpres', 'float32', ('time_counter', 'y', 'x'))
    atmpres.long_name = 'Sea Level Pressure'
    atmpres.units = press.units
    atmpres[:] = press_corr[:]

    slp_file.close()


def _slp(Z, P, T):
    R = 287  # ideal gas constant
    g = 9.81  # gravity
    gam = 0.0098  # lapse rate(deg/m)
    p0 = 101000  # average sea surface heigh in Pa

    ps = P * (gam * (Z / T) + 1)**(g / gam / R)
    return ps


def _truncate_height(alt1, lon1, lat1, lon2, lat2):
    """ Truncates the height file over our smaller domain.
    alt1, lon1, lat1, are the height, longitude and latitude of the larger domain.
    lon2, lat2 are the longitude and latitude of the smaller domain.
    returns h,lons,lats, the height, longiutde and latitude over the smaller domain. """

    # bottom left (i,j)
    i = np.where(np.logical_and(np.abs(lon1 - lon2[0, 0]) < 10**(-5),
                                np.abs(lat1 - lat2[0, 0]) < 10**(-5)))
    i_st = i[1]
    j_st = i[0]

    # top right
    i = np.where(np.logical_and(np.abs(lon1 - lon2[-1, -1]) < 10**(-5),
                                np.abs(lat1 - lat2[-1, -1]) < 10**(-5)))

    i_ed = i[1]
    j_ed = i[0]

    h_small = alt1[0, j_st:j_ed + 1, i_st:i_ed + 1]
    lat_small = lat1[j_st:j_ed + 1, i_st:i_ed + 1]
    lon_small = lon1[j_st:j_ed + 1, i_st:i_ed + 1]
    return h_small, lon_small, lat_small


def combine_subdomain(filenames, outfilename):
    """Recombine per-processor subdomain files into one single file.

    Note: filenames must be an array of files organized to reflect the
    subdomain decompsition. filenames[0,0] is bottom left, filenames[0,-1] is
    bottom right, filenames[-1,0] is top left, filenames[-1,-1] is top right.
    For example,
    filenames =  [[sub_00.nc, sub_01.nc], [sub_02.nc, sub_03.nc]].
    This can be improved. At some point it would be worthwhile to autmotically
    build the filenames array.
    Also, we might want to add netcdf attributes like history, units, etc.

    :arg filenames: An array containing the names of the files to be
                    recombined.
    :type filenames: numpy array (2D)

    :arg outfilename: The name of the file for saving output
    :type outfilename: string
    """
    # Determine shape of each subdomain
    shapes = _define_shapes(filenames)

    # Initialize
    new = nc.Dataset(outfilename, 'w')
    _initialize_dimensions(new, nc.Dataset(filenames[0, 0]))
    newvars = _initialize_variables(new, nc.Dataset(filenames[0, 0]))

    # Build full array
    _concatentate_variables(filenames, shapes, newvars)

    new.close()


def _define_shapes(filenames):
    """Creates a dictionary object that stores the beginning and ending i, j
    coordinate for each subdomain file stored in names.
    filenames should be orgnaized in a way that corresponds to the shape of the
    region you are compiling.
    The first axis (rows) of names is along y, second axis (columns) is along x
    filenames[0,0] is the bottom left subdomain
    filenames[-1,0] is the top left subdomain
    filenames[0,-1] is the bottom right subdomain
    filenames[-1,-1] is the top right subdomain

    Beginning/ending i = iss/iee, beginning/ending j = jss/jee

    Used for recombining per-processor subdomain files

    :arg filenames: Filenames in the domain decomposition, organized into an
    an array grid
    :type filenames: numpy array

    :returns: a dictionary of dictionarys. First level keys are the filenames,
    second level are iss,iee,jss,jee
    """
    shapes = {}
    jss = 0
    for j in np.arange(filenames.shape[0]):
        iss = 0
        for i in np.arange(filenames.shape[1]):
            name = filenames[j, i]
            f = nc.Dataset(name)
            x = f.dimensions['x'].__len__()
            y = f.dimensions['y'].__len__()
            shapes[name] = {}
            shapes[name]['iss'] = iss
            shapes[name]['iee'] = iss+x
            shapes[name]['jss'] = jss
            shapes[name]['jee'] = jss+y
            iss = iss+x
        jss = jss + y
    return shapes


def _initialize_dimensions(newfile, oldfile):
    """Initialize new file to have the same dimension names as oldfile
    Dimensions that are not associated with the horizontal grid are also given
    the same size as oldfile
    Used for recombining per-processor subdomain files

    :arg newfile: the new netCDF file
    :type newfile: netCDF4 file handle

    :arg oldfile: the file from which dimensions are copied
    :type oldfile: netCDF4 file handle
    """
    for dimname in oldfile.dimensions:
        dim = oldfile.dimensions[dimname]
        if dimname == 'x' or dimname == 'y':
            newdim = newfile.createDimension(dimname)
        else:
            newdim = newfile.createDimension(dimname, size=dim.__len__())


def _initialize_variables(newfile, oldfile):
    """Initialize new file to have the same variables as oldfile.
    Used for recombining per-processor subdomain files

    :arg newfile: the new netCDF file
    :type newfile: netCDF4 file handle

    :arg oldfile: the file from which dimensions are copied
    :type oldfile: netCDF4 file handle

    :returns: newvars, a dictionary object with key variable name, value netcdf
    variable
    """
    newvars = {}
    for varname in oldfile.variables:
        var = oldfile.variables[varname]
        dims = var.dimensions
        newvar = newfile.createVariable(varname, var.datatype, dims)
        newvar[:] = var[:]
        newvars[varname] = newvar

    return newvars


def _concatentate_variables(filenames, shapes, variables):
    """Concatentate netcdf variables listed in dictionary variables for all of
    the files stored in filenames. Concatentation on horizontal grid.
    Used for recombining per-processor subdomain files

    :arg filenames: array of filenames for each piece of subdomain
    :type filenames: numpy array

    :arg shapes: conatiner for shapes of each subdomain
    :type shapes: dictionary

    :arg variables: conatiner for the new variables
    :type variables: dictionary with variable name key and netcdf array value
    """
    for name in filenames.flatten():
        for varname in variables.keys():
            newvar = variables[varname]
            f = nc.Dataset(name)
            oldvar = f.variables[varname]
            x1 = shapes[name]['iss']
            x2 = shapes[name]['iee']
            y1 = shapes[name]['jss']
            y2 = shapes[name]['jee']
            if 'x' in newvar.dimensions:
                newvar[..., y1:y2, x1:x2] = oldvar[..., :, :]
