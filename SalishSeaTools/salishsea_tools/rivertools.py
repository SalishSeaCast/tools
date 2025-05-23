# Copyright 2013 – present by the SalishSeaCast contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A collections of functions for working with river flow forcing data
for the SalishSeaCast NEMO model.
"""
import netCDF4 as NC
import numpy as np


def put_watershed_into_runoff(rivertype, area, flux, runoff, run_depth, run_temp, pd):
    """Fill the river file with the rivers of one watershed.

    :arg str rivertype: 'constant' or 'monthly' flows

    :arg area: horizontal area of each grid cell in domain e1t*e2t
    :type area: :py:class:`numpy.ndarray`

    :arg float flux: amount of flow into watershed

    :arg runoff: runoff array we are filling
    :type area: :py:class:`numpy.ndarray`

    :arg run_depth: depth array we are filling
    :type area: :py:class:`numpy.ndarray`

    :arg run_temp: temperature array we are filling
    :type area: :py:class:`numpy.ndarray`

    :arg dict pd: property dictionary for the watershed

    Note: this function now needs pd sent in, it does not go
    and get it as it did previously
    """

    for key in pd:
        river = pd[key]
        if rivertype == "constant":
            fill_runoff_array(
                flux * river["prop"],
                river["i"],
                river["di"],
                river["j"],
                river["dj"],
                river["depth"],
                runoff,
                run_depth,
                area,
            )
        elif rivertype == "monthly":
            fill_runoff_array_monthly(
                flux * river["prop"],
                river["i"],
                river["di"],
                river["j"],
                river["dj"],
                river["depth"],
                runoff,
                run_depth,
                run_temp,
                area,
                numtimes=12,
            )
        elif rivertype == "daily":
            fill_runoff_array_monthly(
                flux * river["prop"],
                river["i"],
                river["di"],
                river["j"],
                river["dj"],
                river["depth"],
                runoff,
                run_depth,
                run_temp,
                area,
                numtimes=365,
            )
    return runoff, run_depth, run_temp


def get_watershed_prop_dict(watershedname, Fraser_River="short"):
    """get the proportion that each river occupies in the watershed."""
    raise DeprecationWarning(
        "get_watershed_prop_dict() depreciated, use the river_** dictionary files"
    )


def get_bathy_cell_size(
    grid="../../../nemo-forcing/grid/" "coordinates_seagrid_SalishSea.nc",
):
    """Get the bathymetry and size of each cell."""
    fc = NC.Dataset(grid)
    e1t = fc.variables["e1t"]
    e2t = fc.variables["e2t"]
    return e1t, e2t


def init_runoff_array(
    bathy="../../../nemo-forcing/grid/" "bathy_meter_SalishSea.nc",
    init_depth=-1,
    init_temp=-99,
):
    """Initialise the runoff array.

    If you want to use a different bathymetry set it in the call;
    e.g.::

      init_runoff_array(
          bathy='/ocean/jieliu/research/meopar/river-treatment/bathy_meter_SalishSea6.nc')
    """
    raise DeprecationWarning(
        "init_runoff_array() deprecated, use runoff = np.zeros_like(area); run_depth = np.ones_like(runoff)"
    )


def init_runoff_array_monthly(
    bathy="../../../nemo-forcing/grid/" "bathy_meter_SalishSea.nc",
    init_depth=-1,
    init_temp=-99,
):
    """Initialise the runoff array for each month."""
    raise DeprecationWarning(
        "init_runoff_array() deprecated, use runoff = np.zeros((12, area.shape[0], area.shape[1])); run_depth = np.ones_like(runoff)"
    )


def fill_runoff_array(
    flux, istart, di, jstart, dj, depth_of_flux, runoff, run_depth, area
):
    """Fill the runoff array."""
    number_cells = di * dj
    total_area = number_cells * area[istart, jstart]
    w = flux / total_area * 1000.0  # w is in kg/s not m/s
    runoff[istart : istart + di, jstart : jstart + dj] = w
    run_depth[istart : istart + di, jstart : jstart + dj] = depth_of_flux
    return runoff, run_depth


def fill_runoff_array_monthly(
    flux,
    istart,
    di,
    jstart,
    dj,
    depth_of_flux,
    runoff,
    run_depth,
    run_temp,
    area,
    numtimes=12,
):
    """Fill the monthly runoff array."""
    number_cells = di * dj
    total_area = number_cells * area[istart, jstart]
    for ntime in range(1, numtimes + 1):
        w = flux[ntime - 1] / total_area * 1000.0  # w is in kg/s not m/s
        runoff[(ntime - 1), istart : istart + di, jstart : jstart + dj] = w
        run_depth[(ntime - 1), istart : istart + di, jstart : jstart + dj] = (
            depth_of_flux
        )
        if numtimes == 12:
            run_temp[(ntime - 1), istart : istart + di, jstart : jstart + dj] = (
                rivertemp(month=ntime)
            )
        else:
            run_temp[(ntime - 1), istart : istart + di, jstart : jstart + dj] = (
                rivertemp_yday(yearday=ntime)
            )
    return runoff, run_depth, run_temp


def check_sum(runoff_orig, runoff_new, flux, area):
    """Check that the runoff adds up to what it should."""
    new_flux = np.sum(runoff_new * area) / 1000.0 - np.sum(runoff_orig * area) / 1000.0
    print(new_flux, flux, new_flux / flux)


def check_sum_monthly(runoff_orig, runoff_new, flux, area, numtimes=12):
    """Check that the runoff adds up per month to what it should."""
    new_flux = np.sum(runoff_new * area) / 1000.0 - np.sum(runoff_orig * area) / 1000.0
    print(new_flux / numtimes, np.sum(flux) / numtimes, new_flux / np.sum(flux))


def rivertemp_yday(yearday):
    """River temperature, based on Fraser River, see Allen and Wolfe (2013).

    Temperature in NEMO is in Celsius.
    """
    if yearday < 52.8 or yearday > 334.4:
        river_temp = 2.5
    elif yearday < 232.9:
        river_temp = 2.5 + (yearday - 52.8) * (19.3 - 2.5) / (232.9 - 52.8)
    else:
        river_temp = 19.3 + (yearday - 232.9) * (2.5 - 19.3) / (334.4 - 232.9)
    return river_temp


def rivertemp(month):
    """River temperature, based on Fraser River, see Allen and Wolfe (2013).

    Temperature in NEMO is in Celsius.
    """
    centerday = [
        15.5,
        31 + 14,
        31 + 28 + 15.5,
        31 + 28 + 31 + 15,
        31 + 28 + 31 + 30 + 15.5,
        31 + 28 + 31 + 30 + 31 + 15,
        31 + 28 + 31 + 30 + 31 + 30 + 15.5,
        31 + 28 + 31 + 30 + 31 + 30 + 31 + 15.5,
        31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 15,
        31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 15.5,
        31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 15,
        31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 15.5,
    ]
    yearday = centerday[month - 1]
    river_temp = rivertemp_yday(yearday)
    return river_temp


def get_watershed_prop_dict_long_fraser(watershedname):
    """get the proportion that each river occupies in the watershed."""
    raise DeprecationWarning(
        "get_watershed_prop_dict_long_fraser() depreciated, use the river_** dictionary files"
    )


def get_watershed_prop_dict_allArms_fraser(watershedname):
    """get the proportion that each river occupies in the watershed."""
    raise DeprecationWarning(
        "get_watershed_prop_dict_allArms_fraser() depreciated, all Arms bathy superceded by 201702"
    )


def init_runoff3_array(
    bathy="/ocean/jieliu/research/meopar/river-treatment/" "bathy_meter_SalishSea3.nc",
):
    """Initialise the runoff array."""
    raise DeprecationWarning(
        "init_runoff3_array() depreciated, just use init_runoff_array"
    )


def put_watershed_into_runoff3(
    rivertype,
    watershedname,
    flux,
    runoff,
    run_depth,
    run_temp,
):
    """Fill the river file with the rivers of one watershed."""
    raise DeprecationWarning(
        "put_watershed_into_runoff3() depreciated, just use put_watershed_into_runoff"
    )


def init_runoff3_array_monthly(
    bathy="/ocean/jieliu/research/meopar/river-treatment/" "bathy_meter_SalishSea3.nc",
):
    """Initialise the runoff array for each month."""
    raise DeprecationWarning(
        "init_runoff3_array_monthly() depreciated, just use init_runoff_array_monthly"
    )


def init_runoff5_array_monthly(
    bathy="/ocean/jieliu/research/meopar/river-treatment/" "bathy_meter_SalishSea5.nc",
):
    """Initialise the runoff array for each month."""
    raise DeprecationWarning(
        "init_runoff5_array_monthly() depreciated, just use init_runoff_array_monthly"
    )


def init_runoff5_array(
    bathy="/ocean/jieliu/research/meopar/river-treatment/" "bathy_meter_SalishSea5.nc",
):
    """Initialise the runoff array."""
    raise DeprecationWarning(
        "init_runoff5_array() depreciated, just use init_runoff_array"
    )
