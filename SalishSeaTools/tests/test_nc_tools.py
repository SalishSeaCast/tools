# Copyright 2013-2016 The Salish Sea MEOPAR contributors
# and The University of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for nc_tools.
"""
from __future__ import division

import datetime
from pathlib import Path
from unittest.mock import patch

import arrow
import dateutil
import numpy as np
import pytest

from salishsea_tools import nc_tools


@pytest.mark.parametrize('path, args, kwargs, expected', [
    ('foo/bar.nc', [], {}, 'foo/bar.nc'),
    ('foo/bar.nc', ['w'], {}, 'foo/bar.nc'),
    ('foo/bar.nc', ['w'], {'format': 'NETCDF4_CLASSIC'}, 'foo/bar.nc'),
    (Path('foo/bar.nc'), [], {}, 'foo/bar.nc'),
    (Path('foo/bar.nc'), ['w'], {}, 'foo/bar.nc'),
    (Path('foo/bar.nc'), ['w'], {'format': 'NETCDF4_CLASSIC'}, 'foo/bar.nc'),
])
def test_dataset_from_path(path, args, kwargs, expected):
    """dataset_from_path calls netCDF4.Dataset w/ path as str, args & kwargs
    """
    with patch.object(nc_tools.nc, 'Dataset') as m_Dataset:
        dataset = nc_tools.dataset_from_path(path, *args, **kwargs)
    assert dataset == m_Dataset(expected, *args, **kwargs)


def test_show_dataset_attrs_file_format(capsys, nc_dataset):
    """show_dataset_attrs prints file_format attr
    """
    nc_tools.show_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    assert out.splitlines()[0] == 'file format: NETCDF4'


def test_show_dataset_attrs_1_attr(capsys, nc_dataset):
    """show_dataset_attrs prints attr name and value
    """
    nc_dataset.Conventions = 'CF-1.6'
    nc_tools.show_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    assert out.splitlines()[1] == 'Conventions: CF-1.6'


def test_show_dataset_attrs_order(capsys, nc_dataset):
    """show_dataset_attrs prints attr names & values in order they were set
    """
    nc_dataset.Conventions = 'CF-1.6'
    nc_dataset.title = 'Test Dataset'
    nc_tools.show_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    assert out.splitlines()[2] == 'title: Test Dataset'


def test_show_dimensions(capsys, nc_dataset):
    """show_dimensions prints dimension string representation
    """
    nc_dataset.createDimension('foo', 42)
    nc_tools.show_dimensions(nc_dataset)
    out, err = capsys.readouterr()
    assert out.splitlines()[0] == (
        "<class 'netCDF4._netCDF4.Dimension'>: name = 'foo', size = 42")


def test_show_dimensions_order(capsys, nc_dataset):
    """show_dimensions prints dimension in order they were defined
    """
    nc_dataset.createDimension('foo', 42)
    nc_dataset.createDimension('bar', 24)
    nc_tools.show_dimensions(nc_dataset)
    out, err = capsys.readouterr()
    assert out.splitlines()[2] == (
        "<class 'netCDF4._netCDF4.Dimension'>: name = 'bar', size = 24")


def test_show_variables(capsys, nc_dataset):
    """show_variables prints list of variable names
    """
    nc_dataset.createDimension('x', 42)
    nc_dataset.createVariable('foo', float, ('x',))
    nc_tools.show_variables(nc_dataset)
    out, err = capsys.readouterr()
    assert out.splitlines()[0] == "odict_keys(['foo'])"


def test_show_variables_order(capsys, nc_dataset):
    """show_variables prints list of variable names in order they were defined
    """
    nc_dataset.createDimension('x', 42)
    nc_dataset.createVariable('foo', float, ('x',))
    nc_dataset.createVariable('bar', float, ('x',))
    nc_tools.show_variables(nc_dataset)
    out, err = capsys.readouterr()
    assert out.splitlines()[0] == "odict_keys(['foo', 'bar'])"


def test_show_variable_attrs(capsys, nc_dataset):
    """show_variable_attrs prints variable string representation
    """
    nc_dataset.createDimension('x', 42)
    foo = nc_dataset.createVariable('foo', float, ('x',))
    foo.units = 'm'
    nc_tools.show_variable_attrs(nc_dataset)
    out, err = capsys.readouterr()
    assert out == (
        "<class 'netCDF4._netCDF4.Variable'>\n"
        "float64 foo(x)\n"
        "    units: m\n"
        "unlimited dimensions: \n"
        "current shape = (42,)\n"
        "filling on, default _FillValue of 9.969209968386869e+36 used\n\n"
    )


def test_show_variable_attrs_order(capsys, nc_dataset):
    """show_variable_attrs prints variables in order they were defined
    """
    nc_dataset.createDimension('x', 42)
    nc_dataset.createVariable('foo', float, ('x',))
    nc_dataset.createVariable('bar', float, ('x',))
    nc_tools.show_variable_attrs(nc_dataset)
    out, err = capsys.readouterr()
    assert out.splitlines()[7] == 'float64 bar(x)'


def test_show_variable_attrs_spec_var(capsys, nc_dataset):
    """show_variable_attrs prints string repr of specified variable
    """
    nc_dataset.createDimension('x', 42)
    foo = nc_dataset.createVariable('foo', float, ('x',))
    foo.units = 'm'
    nc_dataset.createVariable('bar', float, ('x',))
    nc_tools.show_variable_attrs(nc_dataset, 'foo')
    out, err = capsys.readouterr()
    assert out == (
        "<class 'netCDF4._netCDF4.Variable'>\n"
        "float64 foo(x)\n"
        "    units: m\n"
        "unlimited dimensions: \n"
        "current shape = (42,)\n"
        "filling on, default _FillValue of 9.969209968386869e+36 used\n\n"
    )


def test_show_variable_attrs_spec_var_order(capsys, nc_dataset):
    """show_variable_attrs prints specified vars in order they were defined
    """
    nc_dataset.createDimension('x', 42)
    nc_dataset.createVariable('foo', float, ('x',))
    nc_dataset.createVariable('bar', float, ('x',))
    nc_tools.show_variable_attrs(nc_dataset, 'foo', 'bar')
    out, err = capsys.readouterr()
    assert out.splitlines()[7] == 'float64 bar(x)'


def test_time_origin_value(nc_dataset):
    """time_origin returns expected Arrow instance
    """
    nc_dataset.createDimension('time_counter')
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2002-OCT-26 00:00:00'
    time_origin = nc_tools.time_origin(nc_dataset)
    assert time_origin == arrow.get(2002, 10, 26, 0, 0, 0)


def test_time_origin_value_format2(nc_dataset):
    """time_origin returns expected Arrow instance.
    time_origin format is 'YYYY-MM-DD HH:mm:ss'
    """
    nc_dataset.createDimension('time_counter')
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2002-10-26 00:00:00'
    time_origin = nc_tools.time_origin(nc_dataset)
    assert time_origin == arrow.get(2002, 10, 26, 0, 0, 0)


def test_time_origin_UTC_timezone(nc_dataset):
    """time_origin return value has UTC timezone
    """
    nc_dataset.createDimension('time_counter')
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2002-OCT-26 00:00:00'
    time_origin = nc_tools.time_origin(nc_dataset)
    assert time_origin.tzinfo == dateutil.tz.tzutc()


def test_time_origin_missing(nc_dataset):
    """time_origin raises AttributeError if dataset lacks time_origin attr
    """
    with pytest.raises(AttributeError):
        nc_dataset.createDimension('time_counter')
        nc_dataset.createVariable(
            'time_counter', float, ('time_counter',))
        nc_tools.time_origin(nc_dataset)


def test_time_counter_missing(nc_dataset):
    """time_origin raises KeyError if dataset lacks time_counter variable
    """
    with pytest.raises(KeyError):
        nc_tools.time_origin(nc_dataset)


def test_timestamp_value(nc_dataset):
    """timestamp returns expected Arrow instance
    """
    nc_dataset.createDimension('time_counter')
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2002-OCT-26 00:00:00'
    time_counter[:] = np.array([8.5 * 60*60])
    timestamp = nc_tools.timestamp(nc_dataset, 0)
    assert timestamp == arrow.get(2002, 10, 26, 8, 30, 0)


def test_timestamp_value_list(nc_dataset):
    """timestamp returns expected list of Arrow instances
    """
    nc_dataset.createDimension('time_counter')
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2002-OCT-26 00:00:00'
    time_counter[:] = np.array([0.5, 1.5]) * 60*60
    timestamp = nc_tools.timestamp(nc_dataset, (0, 1))
    expected = [
        arrow.get(2002, 10, 26, 0, 30, 0),
        arrow.get(2002, 10, 26, 1, 30, 0),
    ]
    assert timestamp == expected


def test_timestamp_index_error(nc_dataset):
    """timestamp returns expected Arrow instance
    """
    nc_dataset.createDimension('time_counter')
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2002-OCT-26 00:00:00'
    time_counter[:] = np.array([8.5 * 60*60])
    with pytest.raises(IndexError):
        nc_tools.timestamp(nc_dataset, 1)


@pytest.mark.parametrize('datetimes, expected', [
    (False, arrow.Arrow),
    (True, datetime.datetime),
])
def test_ssh_timeseries_at_point_time_counter_type(
    datetimes, expected, nc_dataset,
):
    """Sea surface height timeseries time counter values have expected type
    """
    nc_dataset.createDimension('time_counter')
    nc_dataset.createDimension('y', 1)
    nc_dataset.createDimension('x', 1)
    ssh = nc_dataset.createVariable(
        'sossheig', float, ('time_counter', 'y', 'x'))
    ssh[:] = np.array([5.0, 5.3])
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2002-OCT-26 00:00:00'
    time_counter[:] = np.array([0.5, 1.5]) * 60*60
    ssh_ts = nc_tools.ssh_timeseries_at_point(nc_dataset, 0, 0, datetimes)
    np.testing.assert_array_equal(ssh_ts.ssh, np.array([5.0, 5.3]))
    assert isinstance(ssh_ts.time[0], expected)


@pytest.mark.parametrize('datetimes, expected', [
    (False, arrow.Arrow),
    (True, datetime.datetime),
])
def test_uv_wind_timeseries_at_point_time_counter_type(
    datetimes, expected, nc_dataset,
):
    """u and v wind components timeseries time counter values have expected type
    """
    nc_dataset.createDimension('time_counter')
    nc_dataset.createDimension('y', 1)
    nc_dataset.createDimension('x', 1)
    u_wind = nc_dataset.createVariable(
        'u_wind', float, ('time_counter', 'y', 'x'))
    u_wind[:] = np.array([-8.75, -4.41])
    v_wind = nc_dataset.createVariable(
        'v_wind', float, ('time_counter', 'y', 'x'))
    v_wind[:] = np.array([0.43, -0.37])
    time_counter = nc_dataset.createVariable(
        'time_counter', float, ('time_counter',))
    time_counter.time_origin = '2002-OCT-26 00:00:00'
    time_counter[:] = np.array([0.5, 1.5]) * 60*60
    wind_ts = nc_tools.uv_wind_timeseries_at_point(nc_dataset, 0, 0, datetimes)
    np.testing.assert_array_equal(wind_ts.u, np.array([-8.75, -4.41]))
    np.testing.assert_array_equal(wind_ts.v, np.array([0.43, -0.37]))
    assert isinstance(wind_ts.time[0], expected)


@patch('salishsea_tools.nc_tools._notebook_hg_url')
@patch('salishsea_tools.nc_tools._nc_file_hg_url')
def test_init_dataset_attrs(mock_nhu, mock_nfhu, nc_dataset):
    """init_dataset_attrs initializes dataset global attrs
    """
    nc_tools.init_dataset_attrs(
        nc_dataset, 'Test Dataset', 'TestDatasetNotebook', 'test_dataset.nc')
    assert nc_dataset.Conventions == 'CF-1.6'


@patch('salishsea_tools.nc_tools._notebook_hg_url')
@patch('salishsea_tools.nc_tools._nc_file_hg_url')
def test_init_dataset_attrs_quiet(mock_nhu, mock_nfhu, capsys, nc_dataset):
    """init_dataset_attrs prints no output when quiet=True
    """
    nc_tools.init_dataset_attrs(
        nc_dataset, 'Test Dataset', 'TestDatasetNotebook', 'test_dataset.nc',
        quiet=True)
    out, err = capsys.readouterr()
    assert out == ''


@patch('salishsea_tools.nc_tools._notebook_hg_url')
@patch('salishsea_tools.nc_tools._nc_file_hg_url')
def test_init_dataset_attrs_no_oversrite(
    mock_nhu, mock_nfhu, capsys, nc_dataset,
):
    """init_dataset_attrs does not overwrite existing attrs
    """
    nc_dataset.Conventions = 'CF-1.6'
    nc_tools.init_dataset_attrs(
        nc_dataset, 'Test Dataset', 'TestDatasetNotebook', 'test_dataset.nc')
    out, err = capsys.readouterr()
    assert out.splitlines()[0] == (
        'Existing attribute value found, not overwriting: Conventions')


@patch('salishsea_tools.nc_tools._notebook_hg_url')
@patch('salishsea_tools.nc_tools._nc_file_hg_url')
def test_init_dataset_attrs_no_oversrite_quiet(
    mock_nhu, mock_nfhu, capsys, nc_dataset,
):
    """init_dataset_attrs suppresses no-overwrite notice when quiet=True
    """
    nc_dataset.Conventions = 'CF-1.6'
    nc_dataset.history = 'foo'
    nc_tools.init_dataset_attrs(
        nc_dataset, 'Test Dataset', 'TestDatasetNotebook', 'test_dataset.nc',
        quiet=True)
    out, err = capsys.readouterr()
    assert out == ''
    assert nc_dataset.history == 'foo'


@patch(
    'salishsea_tools.nc_tools.hg.default_url',
    return_value='ssh://hg@bitbucket.org/salishsea/foo')
def test_notebook_hg_url(mock_dflt_url):
    """_notebook_hg_url returns expected URL
    """
    url = nc_tools._notebook_hg_url('bar.ipynb')
    assert url == 'https://bitbucket.org/salishsea/foo/src/tip/bar.ipynb'


def test_notebook_hg_url_no_notebook_name():
    """_notebook_hg_url returns REQUIRED if notebook name arg is empty
    """
    url = nc_tools._notebook_hg_url('')
    assert url == 'REQUIRED'


@patch('salishsea_tools.nc_tools.hg.default_url', return_value=None)
def test_notebook_hg_url_REQUIRED(mock_dflt_url):
    """_notebook_hg_url returns REQUIRED if bitbucket not in repo URL
    """
    url = nc_tools._notebook_hg_url('foo')
    assert url == 'REQUIRED'


@patch(
    'salishsea_tools.nc_tools.hg.default_url',
    return_value='ssh://hg@bitbucket.org/salishsea/foo')
def test_notebook_hg_url_adds_ipynb(mock_dflt_url):
    """_notebook_hg_url adds .ipynb extension if notebook name lacks it
    """
    url = nc_tools._notebook_hg_url('bar')
    assert url == 'https://bitbucket.org/salishsea/foo/src/tip/bar.ipynb'


@patch(
    'salishsea_tools.nc_tools.hg.default_url',
    return_value='ssh://hg@bitbucket.org/salishsea/foo')
def test_nc_file_hg_url(mock_dflt_url):
    """_nc_file_hg_url returns expected URL
    """
    url = nc_tools._nc_file_hg_url('../bar/baz.nc')
    assert url == 'https://bitbucket.org/salishsea/foo/src/tip/baz.nc'


def test_nc_file_hg_url_no_nc_filepath():
    """_nc_file_hg_url returns REQUIRED if nc_filepath arg is empty
    """
    url = nc_tools._nc_file_hg_url('')
    assert url == 'REQUIRED'


@patch('salishsea_tools.nc_tools.hg.default_url', return_value=None)
def test_nc_file_hg_url_REQUIRED(mock_dflt_url):
    """_nc_file_hg_url returns REQUIRED if bitbucket not in repo URL
    """
    url = nc_tools._nc_file_hg_url('../bar/baz.nc')
    assert url == 'REQUIRED'


def test_check_dataset_attrs_reqd_dataset_attrs(capsys, nc_dataset):
    """check_dataset_attrs warns of missing required dataset attributes
    """
    nc_tools.check_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    reqd_attrs = (
        'Conventions',
        'title',
        'institution',
        'source',
        'references',
        'history',
        'comment',
    )
    for line, expected in enumerate(reqd_attrs):
        assert out.splitlines()[line] == (
            'Missing required dataset attribute: {}'.format(expected))


def test_check_dataset_attrs_reqd_dataset_attr_values(capsys, nc_dataset):
    """check_dataset_attrs warns of missing reqd dataset attr values
    """
    reqd_attrs = (
        'Conventions',
        'title',
        'institution',
        'source',
        'references',
        'history',
    )
    for attr in reqd_attrs:
        nc_dataset.setncattr(attr, '')
    nc_tools.check_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    for line, attr in enumerate(reqd_attrs):
        assert out.splitlines()[line] == (
            'Missing value for dataset attribute: {}'.format(attr))


def test_check_dataset_attrs_url_reqd(capsys, nc_dataset):
    """check_dataset_attrs warns of source or references set to REQUIRED
    """
    empty_reqd_attrs = (
        'Conventions',
        'title',
        'institution',
        'references',
    )
    for attr in empty_reqd_attrs:
        nc_dataset.setncattr(attr, 'foo')
    REQUIRED_reqd_attrs = (
        'source',
        'references',
    )
    for attr in REQUIRED_reqd_attrs:
        nc_dataset.setncattr(attr, 'REQUIRED')
    nc_tools.check_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    for line, attr in enumerate(REQUIRED_reqd_attrs):
        assert out.splitlines()[line] == (
            'Missing value for dataset attribute: {}'.format(attr))


def test_check_dataset_attrs_good(capsys, nc_dataset):
    """check_dataset_attrs prints nothing when all reqd attts present w/ value
    """
    dataset_attrs = (
        ('Conventions', 'CF-1.6'),
        ('title', 'Test Dataset'),
        ('institution', 'Unit Tests'),
        ('source', 'foo'),
        ('references', 'bar'),
        ('history', 'was'),
        ('comment', ''),
    )
    for attr, value in dataset_attrs:
        nc_dataset.setncattr(attr, value)
    nc_tools.check_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    assert out == ''


def test_check_dataset_attrs_reqd_var_attrs(capsys, nc_dataset):
    """check_dataset_attrs warns of missing required variable attributes
    """
    dataset_attrs = (
        ('Conventions', 'CF-1.6'),
        ('title', 'Test Dataset'),
        ('institution', 'Unit Tests'),
        ('source', 'foo'),
        ('references', 'bar'),
        ('history', 'was'),
        ('comment', ''),
    )
    for attr, value in dataset_attrs:
        nc_dataset.setncattr(attr, value)
    nc_dataset.createDimension('x', 42)
    nc_dataset.createVariable('foo', float, ('x',))
    nc_tools.check_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    reqd_attrs = (
        'units',
        'long_name',
    )
    for line, expected in enumerate(reqd_attrs):
        assert out.splitlines()[line] == (
            'Missing required variable attribute for foo: {}'.format(expected))


def test_check_dataset_attrs_reqd_var_attr_values(capsys, nc_dataset):
    """check_dataset_attrs warns of missing reqd variable attr values
    """
    dataset_attrs = (
        ('Conventions', 'CF-1.6'),
        ('title', 'Test Dataset'),
        ('institution', 'Unit Tests'),
        ('source', 'foo'),
        ('references', 'bar'),
        ('history', 'was'),
        ('comment', ''),
    )
    for attr, value in dataset_attrs:
        nc_dataset.setncattr(attr, value)
    nc_dataset.createDimension('x', 42)
    foo = nc_dataset.createVariable('foo', float, ('x',))
    reqd_attrs = (
        'units',
        'long_name',
    )
    for attr in reqd_attrs:
        foo.setncattr(attr, '')
    nc_tools.check_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    for line, expected in enumerate(reqd_attrs):
        assert out.splitlines()[line] == (
            'Missing value for variable attribute for foo: {}'
            .format(expected))


def test_check_dataset_attrs_car_attrs_good(capsys, nc_dataset):
    """check_dataset_attrs prints nothing when reqd var attrs present w/ values
    """
    dataset_attrs = (
        ('Conventions', 'CF-1.6'),
        ('title', 'Test Dataset'),
        ('institution', 'Unit Tests'),
        ('source', 'foo'),
        ('references', 'bar'),
        ('history', 'was'),
        ('comment', ''),
    )
    for attr, value in dataset_attrs:
        nc_dataset.setncattr(attr, value)
    nc_dataset.createDimension('x', 42)
    foo = nc_dataset.createVariable('foo', float, ('x',))
    reqd_attrs = (
        ('units', 'foo'),
        ('long_name', 'bar'),
    )
    for attr, value in reqd_attrs:
        foo.setncattr(attr, value)
    nc_tools.check_dataset_attrs(nc_dataset)
    out, err = capsys.readouterr()
    assert out == ''
