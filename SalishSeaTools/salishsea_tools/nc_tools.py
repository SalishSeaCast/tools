"""A library of Python functions for exploring and managing
the attributes of netCDF files.
"""
from __future__ import (
    absolute_import,
    division,
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
from datetime import datetime
import os
from salishsea_tools import hg_commands as hg


__all__ = [
    'check_dataset_attrs',
    'init_dataset_attrs',
    'show_dataset_attrs',
    'show_dimensions',
    'show_variables',
    'show_variable_attrs',
]


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
    for dim in dataset.dimensions.itervalues():
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
        for var in dataset.variables.itervalues():
            print(var)


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
                        or update the dataset
    :type notebook_name: str

    :arg nc_filepath: Relative path and filename of the netCDF file being
                      created or updated.
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
        if name in dataset.ncattrs() and not quiet:
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
    repo_path = nc_filepath.split(rel_path)[1]
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
    for var_name, var in dataset.variables.iteritems():
        for attr in reqd_variable_attrs:
            if attr not in var.ncattrs():
                print('Missing required variable attribute for {}: {}'
                      .format(var_name, attr))
                continue
            value = var.getncattr(attr)
            if not value:
                print('Missing value for variable attribute for {}: {}'
                      .format(var_name, attr))
