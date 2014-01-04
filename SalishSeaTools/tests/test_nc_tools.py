"""Unit tests for nc_tools.
"""
from __future__ import division
"""
Copyright 2013-2014 The Salish Sea MEOPAR contributors
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
import os
from mock import patch
import netCDF4 as nc
import pytest
from salishsea_tools import nc_tools


@pytest.fixture()
def dataset(request):
    dataset = nc.Dataset('foo', 'w')

    def teardown():
        dataset.close()
        os.remove('foo')
    request.addfinalizer(teardown)
    return dataset


def test_show_dataset_attrs_file_format(capsys, dataset):
    """show_dataset_attrs prints file_format attr
    """
    nc_tools.show_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    assert out.split('\n')[0] == 'file format: NETCDF4'


def test_show_dataset_attrs_1_attr(capsys, dataset):
    """show_dataset_attrs prints attr name and value
    """
    dataset.Conventions = 'CF-1.6'
    nc_tools.show_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    assert out.split('\n')[1] == 'Conventions: CF-1.6'


def test_show_dataset_attrs_order(capsys, dataset):
    """show_dataset_attrs prints attr names & values in order they were set
    """
    dataset.Conventions = 'CF-1.6'
    dataset.title = 'Test Dataset'
    nc_tools.show_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    assert out.split('\n')[2] == 'title: Test Dataset'


def test_show_dimensions(capsys, dataset):
    """show_dimensions prints dimension string representation
    """
    dataset.createDimension('foo', 42)
    nc_tools.show_dimensions(dataset)
    out, err = capsys.readouterr()
    assert out.split('\n')[0] == (
        "<type 'netCDF4.Dimension'>: name = 'foo', size = 42")


def test_show_dimensions_order(capsys, dataset):
    """show_dimensions prints dimension in order they were defined
    """
    dataset.createDimension('foo', 42)
    dataset.createDimension('bar', 24)
    nc_tools.show_dimensions(dataset)
    out, err = capsys.readouterr()
    assert out.split('\n')[2] == (
        "<type 'netCDF4.Dimension'>: name = 'bar', size = 24")


def test_show_variables(capsys, dataset):
    """show_variables prints list of variable names
    """
    dataset.createDimension('x', 42)
    dataset.createVariable('foo', float, ('x',))
    nc_tools.show_variables(dataset)
    out, err = capsys.readouterr()
    assert out.split('\n')[0] == "['foo']"


def test_show_variables_order(capsys, dataset):
    """show_variables prints list of variable names in order they were defined
    """
    dataset.createDimension('x', 42)
    dataset.createVariable('foo', float, ('x',))
    dataset.createVariable('bar', float, ('x',))
    nc_tools.show_variables(dataset)
    out, err = capsys.readouterr()
    assert out.split('\n')[0] == "['foo', 'bar']"


def test_show_variable_attrs(capsys, dataset):
    """show_variable_attrs prints variable string representation
    """
    dataset.createDimension('x', 42)
    foo = dataset.createVariable('foo', float, ('x',))
    foo.units = 'm'
    nc_tools.show_variable_attrs(dataset)
    out, err = capsys.readouterr()
    assert out == (
        "<type 'netCDF4.Variable'>\n"
        "float64 foo(x)\n"
        "    units: m\n"
        "unlimited dimensions: \n"
        "current shape = (42,)\n\n"
    )


def test_show_variable_attrs_order(capsys, dataset):
    """show_variable_attrs prints variables in order they were defined
    """
    dataset.createDimension('x', 42)
    dataset.createVariable('foo', float, ('x',))
    dataset.createVariable('bar', float, ('x',))
    nc_tools.show_variable_attrs(dataset)
    out, err = capsys.readouterr()
    assert out.split('\n')[6] == 'float64 bar(x)'


def test_show_variable_attrs_spec_var(capsys, dataset):
    """show_variable_attrs prints string repr of specified variable
    """
    dataset.createDimension('x', 42)
    foo = dataset.createVariable('foo', float, ('x',))
    foo.units = 'm'
    dataset.createVariable('bar', float, ('x',))
    nc_tools.show_variable_attrs(dataset, 'foo')
    out, err = capsys.readouterr()
    assert out == (
        "<type 'netCDF4.Variable'>\n"
        "float64 foo(x)\n"
        "    units: m\n"
        "unlimited dimensions: \n"
        "current shape = (42,)\n\n"
    )


def test_show_variable_attrs_spec_var_order(capsys, dataset):
    """show_variable_attrs prints specified vars in order they were defined
    """
    dataset.createDimension('x', 42)
    dataset.createVariable('foo', float, ('x',))
    dataset.createVariable('bar', float, ('x',))
    nc_tools.show_variable_attrs(dataset, 'foo', 'bar')
    out, err = capsys.readouterr()
    assert out.split('\n')[6] == 'float64 bar(x)'


@patch('salishsea_tools.nc_tools._notebook_hg_url')
@patch('salishsea_tools.nc_tools._nc_file_hg_url')
def test_init_dataset_attrs(mock_nhu, mock_nfhu, dataset):
    """init_dataset_attrs initializes dataset global attrs
    """
    nc_tools.init_dataset_attrs(
        dataset, 'Test Dataset', 'TestDatasetNotebook', 'test_dataset.nc')
    assert dataset.Conventions == 'CF-1.6'


@patch('salishsea_tools.nc_tools._notebook_hg_url')
@patch('salishsea_tools.nc_tools._nc_file_hg_url')
def test_init_dataset_attrs_quiet(mock_nhu, mock_nfhu, capsys, dataset):
    """init_dataset_attrs prints no output when quiet=True
    """
    nc_tools.init_dataset_attrs(
        dataset, 'Test Dataset', 'TestDatasetNotebook', 'test_dataset.nc',
        quiet=True)
    out, err = capsys.readouterr()
    assert out == ''


@patch('salishsea_tools.nc_tools._notebook_hg_url')
@patch('salishsea_tools.nc_tools._nc_file_hg_url')
def test_init_dataset_attrs_no_oversrite(mock_nhu, mock_nfhu, capsys, dataset):
    """init_dataset_attrs does not overwrite existing attrs
    """
    dataset.Conventions = 'CF-1.6'
    nc_tools.init_dataset_attrs(
        dataset, 'Test Dataset', 'TestDatasetNotebook', 'test_dataset.nc')
    out, err = capsys.readouterr()
    assert out.split('\n')[0] == (
        'Existing attribute value found, not overwriting: Conventions')


@patch('salishsea_tools.nc_tools._notebook_hg_url')
@patch('salishsea_tools.nc_tools._nc_file_hg_url')
def test_init_dataset_attrs_no_oversrite_quiet(
    mock_nhu, mock_nfhu, capsys, dataset,
):
    """init_dataset_attrs suppresses no-overwrite notice when quiet=True
    """
    dataset.Conventions = 'CF-1.6'
    dataset.history = 'foo'
    nc_tools.init_dataset_attrs(
        dataset, 'Test Dataset', 'TestDatasetNotebook', 'test_dataset.nc',
        quiet=True)
    out, err = capsys.readouterr()
    assert out == ''
    assert dataset.history == 'foo'


@patch(
    'salishsea_tools.nc_tools.hg.default_url',
    return_value='ssh://hg@bitbucket.org/salishsea/foo')
def test_notebook_hg_url(mock_dflt_url):
    """_notebook_hg_url returns expected URL
    """
    url = nc_tools._notebook_hg_url('bar.ipynb')
    assert url == 'https://bitbucket.org/salishsea/foo/src/tip/bar.ipynb'


def test_notebook_hg_url_no_notebook_name():
    """_notebook_hg_url returns REQUIRED if notebook name is empty
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


@patch('salishsea_tools.nc_tools.hg.default_url', return_value=None)
def test_nc_file_hg_url_REQUIRED(mock_dflt_url):
    """_nc_file_hg_url returns REQUIRED if bitbucket not in repo URL
    """
    url = nc_tools._nc_file_hg_url('../bar/baz.nc')
    assert url == 'REQUIRED'


def test_check_dataset_attrs_reqd_dataset_attrs(capsys, dataset):
    """check_dataset_attrs warns of missing required dataset attributes
    """
    nc_tools.check_dataset_attrs(dataset)
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
        assert out.split('\n')[line] == (
            'Missing required dataset attribute: {}'.format(expected))


def test_check_dataset_attrs_reqd_dataset_attr_values(capsys, dataset):
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
        dataset.setncattr(attr, '')
    nc_tools.check_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    for line, attr in enumerate(reqd_attrs):
        assert out.split('\n')[line] == (
            'Missing value for dataset attribute: {}'.format(attr))


def test_check_dataset_attrs_url_reqd(capsys, dataset):
    """check_dataset_attrs warns of source or references set to REQUIRED
    """
    empty_reqd_attrs = (
        'Conventions',
        'title',
        'institution',
        'references',
    )
    for attr in empty_reqd_attrs:
        dataset.setncattr(attr, 'foo')
    REQUIRED_reqd_attrs = (
        'source',
        'references',
    )
    for attr in REQUIRED_reqd_attrs:
        dataset.setncattr(attr, 'REQUIRED')
    nc_tools.check_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    for line, attr in enumerate(REQUIRED_reqd_attrs):
        assert out.split('\n')[line] == (
            'Missing value for dataset attribute: {}'.format(attr))


def test_check_dataset_attrs_good(capsys, dataset):
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
        dataset.setncattr(attr, value)
    nc_tools.check_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    assert out == ''


def test_check_dataset_attrs_reqd_var_attrs(capsys, dataset):
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
        dataset.setncattr(attr, value)
    dataset.createDimension('x', 42)
    dataset.createVariable('foo', float, ('x',))
    nc_tools.check_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    reqd_attrs = (
        'units',
        'long_name',
    )
    for line, expected in enumerate(reqd_attrs):
        assert out.split('\n')[line] == (
            'Missing required variable attribute for foo: {}'.format(expected))


def test_check_dataset_attrs_reqd_var_attr_values(capsys, dataset):
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
        dataset.setncattr(attr, value)
    dataset.createDimension('x', 42)
    foo = dataset.createVariable('foo', float, ('x',))
    reqd_attrs = (
        'units',
        'long_name',
    )
    for attr in reqd_attrs:
        foo.setncattr(attr, '')
    nc_tools.check_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    for line, expected in enumerate(reqd_attrs):
        assert out.split('\n')[line] == (
            'Missing value for variable attribute for foo: {}'
            .format(expected))


def test_check_dataset_attrs_car_attrs_good(capsys, dataset):
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
        dataset.setncattr(attr, value)
    dataset.createDimension('x', 42)
    foo = dataset.createVariable('foo', float, ('x',))
    reqd_attrs = (
        ('units', 'foo'),
        ('long_name', 'bar'),
    )
    for attr, value in reqd_attrs:
        foo.setncattr(attr, value)
    nc_tools.check_dataset_attrs(dataset)
    out, err = capsys.readouterr()
    assert out == ''
