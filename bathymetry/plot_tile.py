#  Copyright 2013 – present by the SalishSeaCast Project contributors
#  and The University of British Columbia
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# SPDX-License-Identifier: Apache-2.0

"""
Plots tile-wise comparisons of single and double resolution bathymetry maps.

This function generates subplots for visualizing single resolution bathymetry,
double resolution base bathymetry, and optional final double resolution
bathymetry in both grid index coordinates and geographical coordinates.

:param x_min_max: Minimum and maximum x-coordinates for slicing.
:type x_min_max: numpy.ndarray

:param y_slices: Dictionary defining slicing in the y-dimension.
:type y_slices: dict

:param bathy: The dataset containing single resolution bathymetry data.
:type bathy: xarray.DataArray

:param dbl_bathy_base: Dataset containing double resolution base bathymetry data.
:type dbl_bathy_base: xarray.DataArray

:param dbl_bathy: Optional dataset for final double resolution bathymetry data.
:type dbl_bathy: xarray.DataArray or None

:param vmax: Maximum value for color scale in visualizations, default is 15.
:type vmax: int

:returns: A tuple with the figure and axes of the plotted bathymetry maps.
:rtype: tuple
"""
from cmap import Colormap
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from matplotlib import pyplot as plt
import matplotlib.cm

from salishsea_tools import viz_tools


# Colour map for plotly traces
colorscale = Colormap("nipy_spectral").to_plotly()

# Hover text template for plotly traces
hover_tmpl = (
    "Lon: %{x:.3f}<br>"
    "Lat: %{y:.3f}<br>"
    "Depth: %{z:.2f} m<br>"
    "x, y: %{customdata}"
    "<extra></extra>"
)


def _add_plotly_panel(
    fig,
    x_slices,
    y_slices,
    bathy_ds,
    rez,
    colorscale=colorscale,
    zmin=4,
    zmax=15,
    hover_tmpl=hover_tmpl,
    row=1,
    col=1,
):
    """
    Adds a Plotly heatmap panel to an existing figure using bathymetry dataset information.

    This function extracts slices of bathymetric data, longitude, and latitude from the
    provided dataset and adds them as a heatmap to the specified subplot of the given figure.

    :param fig: The Plotly figure object to which the heatmap panel will be added.
    :type fig: plotly.graph_objects.Figure

    :param x_slices: Indices for longitude slices at different resolutions.
    :type x_slices: dict

    :param y_slices: Indices for latitude slices at different resolutions.
    :type y_slices: dict

    :param bathy_ds: The Xarray dataset containing bathymetry data. It must include
                     'Bathymetry', 'nav_lon', and 'nav_lat' variables.
    :type bathy_ds: xarray.Dataset

    :param rez: Key specifying the resolution level for slicing the data.
    :type rez: str

    :param colorscale: Colour scale to be used for the heatmap. Defaults to the
                       value provided in the module scope.
    :type colorscale: list

    :param zmin: Minimum z-value for the colour scale to normalize the heatmap values.
                 Defaults to 4.
    :type zmin: float

    :param zmax: Maximum z-value for the colour scale to normalize the heatmap values.
                 Defaults to 15.
    :type zmax: float

    :param hover_tmpl: Custom hover text template for displaying data on hover. Defaults
                       to the value provided in the module scope.
    :type hover_tmpl: str

    :param row: The row index of the subplot in the figure where the heatmap is added.
                Defaults to 1.
    :type row: int

    :param col: The column index of the subplot in the figure where the heatmap is
                added. Defaults to 1.
    :type col: int

    :return: None
    """
    tile_bathy = bathy_ds.Bathymetry.isel(y=y_slices[rez], x=x_slices[rez])
    tile_lons = bathy_ds.nav_lon.isel(y=y_slices[rez], x=x_slices[rez])[0]
    tile_lats = bathy_ds.nav_lat.isel(y=y_slices[rez], x=x_slices[rez])[0]
    fig.add_trace(
        go.Heatmap(
            z=tile_bathy,
            y=tile_lats,
            x=tile_lons,
            customdata=[[(i, j) for i in tile_bathy.x] for j in tile_bathy.y],
            zmin=zmin,
            zmax=zmax,
            colorscale=colorscale,
            hovertemplate=hover_tmpl,
        ),
        row=row,
        col=col,
    )


def plotly_tile(
    x_min_max,
    y_slices,
    bathy_ds,
    dbl_bathy_base_ds,
    dbl_bathy_ds=None,
    colorscale=colorscale,
    zmin=4,
    zmax=15,
    hover_tmpl=hover_tmpl,
):
    """
    Generates a Plotly figure to visualize bathymetric data. The
    resulting figure includes either two or three tiled plots based on whether the adjusted double
    bathymetry dataset is provided. The single resolution bathymetry and base double resolution bathymetry
    are always included as the first two panels.

    :param x_min_max: Array containing the minimum and maximum x-coordinates of the single resolution
                      bathymetry for the tile.
    :type x_min_max: numpy.ndarray

    :param y_slices: Dictionary containing y-coordinate slices for both single and double
                     bathymetry data, keyed by ``"sgl"`` and ``"dbl"`` respectively.
    :type y_slices: dict[str, slice]

    :param bathy_ds: Dataset containing the single resolution bathymetry data.
    :type bathy_ds: xarray.Dataset

    :param dbl_bathy_base_ds: Dataset containing the base double resolution bathymetry data.
    :type dbl_bathy_base_ds: xarray.Dataset

    :param dbl_bathy_ds: Dataset containing the adjusted double resolution bathymetry data. Defaults
                         to None.
    :type dbl_bathy_ds: xarray.Dataset, optional

    :param colorscale: Colour scale to be used for the heatmap. Defaults to the
                       value provided in the module scope.
    :type colorscale: list

    :param zmin: Minimum z-value for the colour scale to normalize the heatmap values.
                 Defaults to 4.
    :type zmin: float

    :param zmax: Maximum z-value for the colour scale to normalize the heatmap values.
                 Defaults to 15.
    :type zmax: float

    :param hover_tmpl: Custom hover text template for displaying data on hover. Defaults
                       to the value provided in the module scope.
    :type hover_tmpl: str

    :return: A Plotly ``Figure`` object containing the configured subplots for bathymetric
             data visualization.
    :rtype: plotly.graph_objects.Figure
    """
    x_slices = {
        "sgl": slice(*x_min_max),
        "dbl": slice(*x_min_max * 2),
    }
    subplot_titles = [
        "bathymetry_202405",
        "bathymetry_double_202405_base",
    ]
    if dbl_bathy_ds is None:
        cols = 2
        width = 1600
    else:
        cols = 3
        subplot_titles.append("bathymetry_double_202405")
        width = 2400
    fig = make_subplots(rows=1, cols=cols, subplot_titles=subplot_titles)
    _add_plotly_panel(
        fig,
        x_slices,
        y_slices,
        bathy_ds,
        "sgl",
        col=1,
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        hover_tmpl=hover_tmpl,
    )
    _add_plotly_panel(
        fig,
        x_slices,
        y_slices,
        dbl_bathy_base_ds,
        "dbl",
        col=2,
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        hover_tmpl=hover_tmpl,
    )
    if dbl_bathy_ds is not None:
        _add_plotly_panel(
            fig,
            x_slices,
            y_slices,
            dbl_bathy_ds,
            "dbl",
            col=3,
            colorscale=colorscale,
            zmin=zmin,
            zmax=zmax,
            hover_tmpl=hover_tmpl,
        )
    fig.update_xaxes(tickformat=".3f")
    fig.update_yaxes(tickformat=".3f")
    fig.update_layout(height=800, width=width)
    return fig


def plot_tile(
    x_min_max,
    y_slices,
    bathy,
    lons_e,
    lats_e,
    dbl_bathy_base,
    lons_dbl_e,
    lats_dbl_e,
    dbl_bathy=None,
    vmax=15,
):
    x_slices = {
        "sgl": slice(*x_min_max),
        "dbl": slice(*x_min_max * 2),
    }
    if dbl_bathy is None:
        fig, axs = plt.subplots(2, 2, figsize=(24, 12))
        ((ax_sgl, ax_dbl_base), (ax_sgl_map, ax_dbl_base_map)) = axs
    else:
        fig, axs = plt.subplots(2, 3, figsize=(36, 18))
        ((ax_sgl, ax_dbl_base, ax_dbl), (ax_sgl_map, ax_dbl_base_map, ax_dbl_map)) = axs

    # use spectral colour map to provide lots of contrast between grid cells
    cmap = matplotlib.cm.get_cmap("nipy_spectral").copy()
    cmap.set_bad(color="burlywood")

    # single resolution bathymetry
    # grid index coordinates
    bathy.isel(y=y_slices["sgl"], x=x_slices["sgl"]).plot(
        ax=ax_sgl, cmap=cmap, vmax=vmax
    )
    viz_tools.set_aspect(ax_sgl)
    ax_sgl.set_title("bathymetry_202405")
    # lon/lat coordinates
    tile_lons = lons_e[y_slices["sgl"], x_slices["sgl"]]
    tile_lats = lats_e[y_slices["sgl"], x_slices["sgl"]]
    ax_sgl_map.pcolormesh(
        tile_lons,
        tile_lats,
        bathy.isel(y=y_slices["sgl"], x=x_slices["sgl"]),
        cmap=cmap,
        vmax=vmax,
    )
    viz_tools.set_aspect(ax_sgl_map, coords="map")

    # double resolution base bathymetry
    # grid index coordinates
    dbl_bathy_base.isel(y=y_slices["dbl"], x=x_slices["dbl"]).plot(
        ax=ax_dbl_base, cmap=cmap, vmax=vmax
    )
    viz_tools.set_aspect(ax_dbl_base)
    ax_dbl_base.set_title("bathymetry_double_202405_base")
    # lon/lat coordinates
    tile_lons = lons_dbl_e[y_slices["dbl"], x_slices["dbl"]]
    tile_lats = lats_dbl_e[y_slices["dbl"], x_slices["dbl"]]
    ax_dbl_base_map.pcolormesh(
        tile_lons,
        tile_lats,
        dbl_bathy_base.isel(y=y_slices["dbl"], x=x_slices["dbl"]),
        cmap=cmap,
        vmax=vmax,
    )
    viz_tools.set_aspect(ax_dbl_base_map, coords="map")
    ax_dbl_base_map.grid(True)

    if dbl_bathy is not None:
        # final double resolution bathymetry
        # useful to show the effect of adjustments made in the Process202405-2xrezBathymetnry.ipynb notebook as we iterate
        # grid index coordintes
        dbl_bathy.isel(y=y_slices["dbl"], x=x_slices["dbl"]).plot(
            ax=ax_dbl, cmap=cmap, vmax=vmax
        )
        viz_tools.set_aspect(ax_dbl)
        ax_dbl.set_title("bathymetry_double_202405")
        # lon/lat coordinates
        ax_dbl_map.pcolormesh(
            tile_lons,
            tile_lats,
            dbl_bathy.isel(y=y_slices["dbl"], x=x_slices["dbl"]),
            cmap=cmap,
            vmax=vmax,
        )
        viz_tools.set_aspect(ax_dbl_map, coords="map")
    fig.tight_layout()
    return fig, axs
