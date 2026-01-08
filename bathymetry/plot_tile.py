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
from matplotlib import pyplot as plt

from salishsea_tools import viz_tools


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
    cmap = "nipy_spectral"

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
