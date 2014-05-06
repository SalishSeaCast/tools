# Copyright 2013-2014 The Salish Sea MEOPAR contributors
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

"""Unit tests for the viz_tools module.
"""
from __future__ import division

from collections import defaultdict

from mock import (
    MagicMock,
    Mock,
    patch,
)
import netCDF4 as nc
import numpy as np
import pytest


@pytest.fixture()
def viz_tools_module():
    from salishsea_tools import viz_tools
    return viz_tools


@pytest.mark.usefixtures('viz_tools_module', 'nc_dataset')
class TestCalcAbsMax(object):
    @pytest.mark.parametrize(
        ('array', 'expected'),
        [
            (np.arange(-5, 10, 0.1), 9.9),
            (np.arange(-10, 5, 0.5), 10),
            (np.array([42]), 42),
        ]
    )
    def test_calc_abs_max_array(self, array, expected, viz_tools_module):
        abs_max = viz_tools_module.calc_abs_max(array)
        np.testing.assert_almost_equal(abs_max, expected)

    @pytest.mark.parametrize(
        ('array', 'expected'),
        [
            (np.arange(-5, 10, 0.1), 9.9),
            (np.arange(-10, 5, 0.5), 10),
            (np.array([42]), 42),
        ]
    )
    def test_calc_abs_max_dataset(
        self, array, expected, viz_tools_module, nc_dataset,
    ):
        nc_dataset.createDimension('x', len(array))
        foo = nc_dataset.createVariable('foo', float, ('x',))
        foo[:] = array
        abs_max = viz_tools_module.calc_abs_max(array)
        np.testing.assert_almost_equal(abs_max, expected)


@pytest.mark.usefixtures('viz_tools_module')
class TestPlotCoastline(object):
    @patch('salishsea_tools.viz_tools.nc.Dataset')
    def test_plot_coastline_defaults_bathy_file(
        self, m_dataset, viz_tools_module,
    ):
        axes = Mock()
        viz_tools_module.plot_coastline(axes, 'bathyfile')
        m_dataset.assert_called_once_with('bathyfile')
        m_dataset.close.assert_called_once()

    @patch('salishsea_tools.viz_tools.nc.Dataset')
    def test_plot_coastline_defaults_bathy_netCDF_obj(
        self, m_dataset, viz_tools_module,
    ):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        viz_tools_module.plot_coastline(axes, bathy)
        assert not m_dataset.called
        assert not m_dataset.close.called

    def test_plot_coastline_defaults(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        contour_lines = viz_tools_module.plot_coastline(axes, bathy)
        axes.contour.assert_called_once_with(
            bathy.variables['Bathymetry'], [0], colors='black')
        assert contour_lines == axes.contour()

    def test_plot_coastline_map_coords(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {
            'Bathymetry': Mock(),
            'nav_lat': Mock(),
            'nav_lon': Mock(),
        }
        contour_lines = viz_tools_module.plot_coastline(
            axes, bathy, coords='map')
        axes.contour.assert_called_once_with(
            bathy.variables['nav_lon'], bathy.variables['nav_lat'],
            bathy.variables['Bathymetry'], [0], colors='black')
        assert contour_lines == axes.contour()

    def test_plot_coastline_isobath(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        contour_lines = viz_tools_module.plot_coastline(
            axes, bathy, isobath=42.42)
        axes.contour.assert_called_once_with(
            bathy.variables['Bathymetry'], [42.42], colors='black')
        assert contour_lines == axes.contour()

    def test_plot_coastline_no_xslice(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        with pytest.raises(ValueError):
            viz_tools_module.plot_coastline(
                axes, bathy, yslice=np.arange(200, 320))

    def test_plot_coastline_no_yslice(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        with pytest.raises(ValueError):
            viz_tools_module.plot_coastline(
                axes, bathy, xslice=np.arange(250, 370))

    def test_plot_coastline_grid_coords_slice(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': MagicMock(spec=nc.Variable)}
        xslice = np.arange(250, 370)
        yslice = np.arange(200, 320)
        contour_lines = viz_tools_module.plot_coastline(
            axes, bathy, xslice=xslice, yslice=yslice)
        axes.contour.assert_called_once_with(
            xslice, yslice, bathy.variables['Bathymetry'][yslice, xslice].data,
            [0], colors='black')
        assert contour_lines == axes.contour()

    def test_plot_coastline_map_coords_slice(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {
            'Bathymetry': MagicMock(spec=nc.Variable),
            'nav_lon': MagicMock(spec=nc.Variable),
            'nav_lat': MagicMock(spec=nc.Variable),
        }
        xslice = np.arange(250, 370)
        yslice = np.arange(200, 320)
        contour_lines = viz_tools_module.plot_coastline(
            axes, bathy, coords='map', xslice=xslice, yslice=yslice)
        axes.contour.assert_called_once_with(
            bathy.variables['nav_lon'][yslice, xslice],
            bathy.variables['nav_lat'][yslice, xslice],
            bathy.variables['Bathymetry'][yslice, xslice].data,
            [0], colors='black')
        assert contour_lines == axes.contour()

    def test_plot_coastline_color_arg(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        contour_lines = viz_tools_module.plot_coastline(
            axes, bathy, color='red')
        axes.contour.assert_called_once_with(
            bathy.variables['Bathymetry'], [0], colors='red')
        assert contour_lines == axes.contour()


@pytest.mark.usefixtures('viz_tools_module')
class TestPlotLandMask(object):
    @patch('salishsea_tools.viz_tools.nc.Dataset')
    def test_plot_land_mask_defaults_bathy_file(
        self, m_dataset, viz_tools_module,
    ):
        axes = Mock()
        viz_tools_module.plot_land_mask(axes, 'bathyfile')
        m_dataset.assert_called_once_with('bathyfile')
        m_dataset.close.assert_called_once()

    @patch('salishsea_tools.viz_tools.nc.Dataset')
    def test_plot_land_mask_defaults_bathy_netCDF_obj(
        self, m_dataset, viz_tools_module,
    ):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        viz_tools_module.plot_land_mask(axes, bathy)
        assert not m_dataset.called
        assert not m_dataset.close.called

    def test_plot_land_mask_defaults(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        contour_fills = viz_tools_module.plot_land_mask(axes, bathy)
        axes.contourf.assert_called_once_with(
            bathy.variables['Bathymetry'], [-0.01, 0.01], colors='black')
        assert contour_fills == axes.contourf()

    def test_plot_land_mask_map_coords(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {
            'Bathymetry': Mock(),
            'nav_lat': Mock(),
            'nav_lon': Mock(),
        }
        contour_fills = viz_tools_module.plot_land_mask(
            axes, bathy, coords='map')
        axes.contourf.assert_called_once_with(
            bathy.variables['nav_lon'], bathy.variables['nav_lat'],
            bathy.variables['Bathymetry'], [-0.01, 0.01], colors='black')
        assert contour_fills == axes.contourf()

    def test_plot_land_mask_isobath(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        contour_fills = viz_tools_module.plot_land_mask(
            axes, bathy, isobath=42.42)
        args, kwargs = axes.contourf.call_args
        assert args[0] == bathy.variables['Bathymetry']
        np.testing.assert_almost_equal(args[1], [-0.01, 42.43])
        assert kwargs == {'colors': 'black'}
        assert contour_fills == axes.contourf()

    def test_plot_land_mask_no_xslice(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        with pytest.raises(ValueError):
            viz_tools_module.plot_land_mask(
                axes, bathy, yslice=np.arange(200, 320))

    def test_plot_land_mask_no_yslice(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        with pytest.raises(ValueError):
            viz_tools_module.plot_land_mask(
                axes, bathy, xslice=np.arange(250, 370))

    def test_plot_land_mask_grid_coords_slice(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': MagicMock(spec=nc.Variable)}
        xslice = np.arange(250, 370)
        yslice = np.arange(200, 320)
        contour_fills = viz_tools_module.plot_land_mask(
            axes, bathy, xslice=xslice, yslice=yslice)
        axes.contourf.assert_called_once_with(
            xslice, yslice, bathy.variables['Bathymetry'][yslice, xslice].data,
            [-0.01, 0.01], colors='black')
        assert contour_fills == axes.contourf()

    def test_plot_land_mask_map_coords_slice(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {
            'Bathymetry': MagicMock(spec=nc.Variable),
            'nav_lon': MagicMock(spec=nc.Variable),
            'nav_lat': MagicMock(spec=nc.Variable),
        }
        xslice = np.arange(250, 370)
        yslice = np.arange(200, 320)
        contour_fills = viz_tools_module.plot_land_mask(
            axes, bathy, coords='map', xslice=xslice, yslice=yslice)
        axes.contourf.assert_called_once_with(
            bathy.variables['nav_lon'][yslice, xslice],
            bathy.variables['nav_lat'][yslice, xslice],
            bathy.variables['Bathymetry'][yslice, xslice].data,
            [-0.01, 0.01], colors='black')
        assert contour_fills == axes.contourf()

    def test_plot_land_mask_color_arg(self, viz_tools_module):
        axes, bathy = Mock(), Mock()
        bathy.variables = {'Bathymetry': Mock()}
        contour_fills = viz_tools_module.plot_land_mask(
            axes, bathy, color='red')
        axes.contourf.assert_called_once_with(
            bathy.variables['Bathymetry'], [-0.01, 0.01], colors='red')
        assert contour_fills == axes.contourf()


@pytest.mark.usefixtures('viz_tools_module')
class TestSetAspect(object):
    def test_set_aspect_defaults(self, viz_tools_module):
        axes = Mock()
        aspect = viz_tools_module.set_aspect(axes)
        axes.set_aspect.assert_called_once_with(5/4.4, adjustable='box-forced')
        assert aspect == 5/4.4

    def test_set_aspect_args(self, viz_tools_module):
        axes = Mock()
        aspect = viz_tools_module.set_aspect(axes, 3/2, adjustable='foo')
        axes.set_aspect.assert_called_once_with(3/2, adjustable='foo')
        assert aspect == 3/2

    def test_set_aspect_map_lats(self, viz_tools_module):
        axes = Mock()
        lats = np.array([42.0])
        lats_aspect = 1 / np.cos(42 * np.pi / 180)
        aspect = viz_tools_module.set_aspect(axes, coords='map', lats=lats)
        axes.set_aspect.assert_called_once_with(
            lats_aspect, adjustable='box-forced')
        assert aspect == lats_aspect

    def test_set_aspect_map_explicit(self, viz_tools_module):
        axes = Mock()
        aspect = viz_tools_module.set_aspect(axes, 2/3, coords='map')
        axes.set_aspect.assert_called_once_with(2/3, adjustable='box-forced')
        assert aspect == 2/3


def test_unstagger(viz_tools_module):
    ugrid = np.array([1, 2, 3] * 3).reshape(3, 3)
    vgrid = np.array([[4] * 3, [5] * 3, [6] * 3])
    u, v = viz_tools_module.unstagger(ugrid, vgrid)
    np.testing.assert_almost_equal(u, np.array([1.5, 2.5] * 2).reshape(2, 2))
    np.testing.assert_almost_equal(v, np.array([[4.5] * 2, [5.5] * 2]))
