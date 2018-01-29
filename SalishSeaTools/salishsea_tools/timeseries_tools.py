# Copyright 2013-2017 The Salish Sea MEOPAR contributors
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

"""A library of Python functions for loading SalishSeaCast timeseries while
conserving memory.
"""

from salishsea_tools import viz_tools, utilities
from dateutil.parser import parse
from datetime import timedelta
import xarray as xr
import numpy as np
import os


def load_NEMO_timeseries(
        filenames, mask, field, dim, index=0, spacing=1,
        shape='grid', unstagger_dim=None
):
    """
    """

    # Reshape mask, grid, and depth
    tmask, coords, ngrid, ngrid_water = reshape_coords(
        mask, dim, index=index, spacing=spacing)

    # Initialize output array
    date = np.empty(0, dtype='datetime64[ns]')
    data = np.empty((0, ngrid_water))

    # Loop through filenames
    bar = utilities.statusbar(
        'Loading {}, {}={}'.format(field, dim, index), width=90
    )
    for findex, filename in enumerate(bar(filenames)):
        # Open NEMO results and flatten (depth averages added here)
        data_grid = xr.open_dataset(filename)[field].isel(**{dim: index})

        # Unstagger if velocity field
        if unstagger_dim is not None:
            data_grid = viz_tools.unstagger_xarray(data_grid, unstagger_dim)

        # Reshape field
        data_trim = reshape_to_ts(
            data_grid.values, tmask, ngrid, ngrid_water, spacing=spacing)

        # Store trimmed arrays
        date = np.concatenate([date, data_grid.time_counter.values])
        data = np.concatenate([data, data_trim], axis=0)

    # Reshape to grid
    if shape is 'grid':

        # Correct for depth dimension name
        if dim.find('depth') is not -1:
            dim1, dim2, dimslice = 'gridY', 'gridX', 'z'
        elif dim.find('y') is not -1:
            dim1, dim2, dimslice = 'gridZ', 'gridX', 'y'
        elif dim.find('x') is not -1:
            dim1, dim2, dimslice = 'gridZ', 'gridY', 'x'

        # Reshape data to grid
        data = reshape_to_grid(
            data, [coords[dim1], coords[dim2]],
            mask.gdept_0.isel(**{'t': 0, dimslice: 0}).shape
        )

        # Redefine coords for grid
        coords = {
            'depth': mask.gdept_1d.isel(t=0).values,
            'gridZ': mask.z.values,
            'gridY': mask.y.values,
            'gridX': mask.x.values
        }

    # Coords dict
    coords['date'] = date

    return data, coords


def make_filename_list(
        timerange, qty, model='nowcast', resolution='h',
        path='/results/SalishSea'
):
    """Return a sequential list of Nowcast results filenames to be passed into
    `xarray.open_mfdataset` or `timeseries_tools.load_NEMO_timeseries`.

    :arg timerange: list or tuple of date strings
        (e.g., ['2017 Jan 1 00:00', '2017 Jan 31 23:00'])
    :type timerange: list or tuple of str

    :arg qty: quantity type
        ('U' for zonal velocity, 'V' for meridional velocity,
        'W' for vertical velocity, 'T' for tracers)
    :type qty: str

    :arg model: forecast type
        (e.g., 'nowcast', 'nowcast-green', 'forecast')
    :type model: str

    :arg resolution: time resolution ('h' for hourly, 'd', for daily)
    :type resolution: str

    :arg path: path to results archive
    :type path: str

    :returns: Sequential list of Nowcast results filenames
    :rtype: list of str
    """

    date, enddate = map(parse, timerange)

    filenames = []

    while date < enddate:
        datestr1 = date.strftime('%d%b%y').lower()
        datestr2 = date.strftime('%Y%m%d')
        filename = 'SalishSea_1{}_{}_{}_grid_{}.nc'.format(
            resolution, datestr2, datestr2, qty)
        filenames.append(os.path.join(path, model, datestr1, filename))
        date = date + timedelta(days=1)

    return filenames


def reshape_coords(mask_in, dim_in, index=0, spacing=1):
    """Prepare the mask and grid for the selected timeseries slice, and reshape
    into 1 spatial dimension
    """

    # Correct for depth dimension name
    if dim_in.find('depth') is not -1:
        dim = 'deptht'
    else:
        dim = dim_in

    # Create full gridded mask, grid and depth Numpy ndarrays
    gridZ, gridY, gridX = np.meshgrid(
        mask_in.z, mask_in.y, mask_in.x, indexing='ij')
    gridmask = xr.Dataset({
        'tmask': (
            ['deptht', 'y', 'x'],
            mask_in.tmask.isel(t=0).values.astype(bool),
        ),
        'depth': (['deptht', 'y', 'x'], mask_in.gdept_0.isel(t=0).values),
        'gridZ': (['deptht', 'y', 'x'], gridZ),
        'gridY': (['deptht', 'y', 'x'], gridY),
        'gridX': (['deptht', 'y', 'x'], gridX)},
        coords={'deptht': mask_in.gdept_1d.isel(t=0).values,
                'y': mask_in.y, 'x': mask_in.x})

    # Slice and subsample mask
    mask = gridmask.tmask.isel(**{dim: index}).values[::spacing, ::spacing]

    # Slice and subsample grid and depth into dict
    coords = {
        'depth':
            gridmask.depth.isel(**{dim: index}).values[::spacing, ::spacing],
        'gridZ':
            gridmask.gridZ.isel(**{dim: index}).values[::spacing, ::spacing],
        'gridY':
            gridmask.gridY.isel(**{dim: index}).values[::spacing, ::spacing],
        'gridX':
            gridmask.gridX.isel(**{dim: index}).values[::spacing, ::spacing],
    }

    # Number of grid points
    ngrid = mask.shape[0] * mask.shape[1]
    ngrid_water = mask.sum()

    # Reshape mask, grid, and depth
    mask = mask.reshape(ngrid)
    coords['depth'] = coords['depth'].reshape(ngrid)[mask]
    coords['gridZ'] = coords['gridZ'].reshape(ngrid)[mask]
    coords['gridY'] = coords['gridY'].reshape(ngrid)[mask]
    coords['gridX'] = coords['gridX'].reshape(ngrid)[mask]

    return mask, coords, ngrid, ngrid_water


def reshape_coords_GEM(grid, mask_in):
    """
    """

    coords = {}

    # Create full gridded mask, grid and depth Numpy ndarrays
    coords['gridY'], coords['gridX'] = np.meshgrid(
        grid.y, grid.x, indexing='ij')

    # Number of grid points
    ngrid = mask_in.shape[0] * mask_in.shape[1]
    ngrid_water = mask_in.sum()

    # Reshape mask, grid, and depth
    mask = mask_in.reshape(ngrid)
    coords['gridY'] = coords['gridY'].reshape(ngrid)[mask.astype(bool)]
    coords['gridX'] = coords['gridX'].reshape(ngrid)[mask.astype(bool)]

    return mask, coords, ngrid, ngrid_water


def reshape_to_ts(data_grid, mask, ngrid, ngrid_water, spacing=1):
    """
    """

    # Convert to Numpy ndarray, subsample, and reshape
    data_flat = data_grid[:, ::spacing, ::spacing].reshape((-1, ngrid))

    # Preallocate trimmed array
    data_trim = np.zeros((data_flat.shape[0], ngrid_water))

    # Trim land points
    for tindex, data_t in enumerate(data_flat):
        data_trim[tindex, :] = data_t[mask]

    return data_trim


def reshape_to_grid(data_flat, coords, shape):
    """Given a flattened array of data with the corresponding Y and X coordinates and the desired grid shape, return the grid of desired shape with the data given. Assumes flattened array has a time dimension as first dimension.

    :arg data_flat: 2d array of data. First dimension is assumed to be time.

    :arg coords: List of form [Ycoords, Xcoords] for each data point given.

    :arg shape: 2d tuple corresponding to desired grid shape. For Salish Sea model, shape would be (898,398). 

    :returns: Array of with dimensions corresponding to shape given with data in coordinates given.  
    """

    # Preallocate gridded array
    data_grid = np.zeros((data_flat.shape[0],) + shape)

    # Reshape flattened data to grid
    for coord1, coord2, data_xyz in zip(*(coords + [data_flat.T])):
        data_grid[:, coord1, coord2] = data_xyz

    return data_grid
