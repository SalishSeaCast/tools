# A module to interpolate Live Ocean results onto Salish Sea NEMO grid and
# save boundary forcing files.

# Nancy Soontiens, August 2016
# nsoontie@eos.ubc.ca
import datetime
import glob
import logging
import os
import re
import subprocess as sp
import sys

import mpl_toolkits.basemap as Basemap
import netCDF4 as nc
import numpy as np
import xarray as xr
from salishsea_tools import LiveOcean_grid as grid
from salishsea_tools import gsw_calls
from scipy import interpolate

import math
import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# -------Main function to generate boundary files from command line--------
# Example: python LiveOcean_BCs '2016-08-30'
def create_files_for_nowcast(date, teos_10=True):
    """Create boundary files from Live Ocean results for use in nowcast,
    forecast and forecast2.

    :arg str date: the LiveOcean rundate in format yyyy-mm-dd

    :arg teos_10: specifies that temperature and salinity are saved in
                  teos-10 variables if true. If true, temperature is saved as
                  Conservative Temperature and salinity is Reference Salinity.
                  If false, temperature is saved as Potential Temperature and
                  salinity is Practical Salinity
    :type teos_10: boolean
    """
    save_dir = '/results/forcing/LiveOcean/boundary_conditions/'
    LO_dir = '/results/forcing/LiveOcean/downloaded/'

    create_LiveOcean_TS_BCs(
        date, date, '1H', 'daily', nowcast=True, teos_10=teos_10,
        bc_dir=save_dir, LO_dir=LO_dir)


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


def load_LiveOcean(files, resample_interval='1H'):
    """Load a time series of Live Ocean results represented by a list of files.
    Time series is resampled by averaging over resample_interval.
    Default is 1 hour.

    :arg files: Live Ocean filenames
    :type files: list of strings

    :arg str resample_interval: interval for resampling based on pandas values.
                                e.g. 1H is one hour, 7D is seven days, etc

    :returns: xarray dataset of Live Ocean results
    """
    # Loop through files and load
    d = xr.open_dataset(files[0])
    for f in files[1:]:
        with xr.open_dataset(f) as d1:
            # drop uncommon variables - subfunction?
            d, d1 = _remove_uncommon_variables_or_coords(d, d1)
            d = xr.concat([d, d1], dim='ocean_time', data_vars='minimal')
    # Determine z-rho (depth)
    G, S, T = grid.get_basic_info(files[0])  # note: grid.py is from Parker
    z_rho = np.zeros(d.salt.shape)
    for t in range(z_rho.shape[0]):
        zeta = d.zeta.values[t, :, :]
        z_rho[t, :, :, :] = grid.get_z(G['h'], zeta, S)
    # Add z_rho to dataset
    zrho_DA = xr.DataArray(
        z_rho,
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
    # Resample
    d = d.resample(resample_interval, 'ocean_time')

    return d


def _remove_uncommon_variables_or_coords(d, d1, remove_type='variables'):
    """Removes uncommon variables or coordinates between two xarray datasets

    :arg d: First dataset
    :type d: xarray dataset

    :arg d1: Second dataset
    :type d1: xarray dataset

    :arg str remove_type: the type to be removed. Either 'variables'
                          or 'coordinates'.

    :returns: two new datasets with uncommon variables/coordinates removed
    """
    if remove_type == 'variables':
        d1list = d1.data_vars
        dlist = d.data_vars
    elif remove_type == 'coords':
        d1list = d1.coords
        dlist = d.coords
    diff = set(dlist) ^ set(d1list)
    rm_d1 = set(d1list) & diff
    rm_d = set(dlist) & diff
    return d.drop(list(rm_d)), d1.drop(list(rm_d1))


def interpolate_to_NEMO_depths(dataset, NEMO_depths, var_names):
    """ Interpolate variables in var_names from a Live Ocean dataset to NEMO
    depths. LiveOcean land points (including points lower than bathymetry) are
    set to np.nan and then masked.

    :arg dataset: Live Ocean dataset
    :type dataset: xarray Dataset

    :arg NEMO_depths: NEMO model depths
    :type NEMO_depths: 1D numpy array

    :arg var_names: list of Live Ocean variable names to be interpolated,
                    e.g ['salt', 'temp']
    :type var_names: list of str

    :returns: dictionary containing interpolated numpy arrays for each variable
    """
    interps = {}
    for var_name in var_names:
        var_interp = np.zeros(dataset[var_name].shape)
        for t in range(var_interp.shape[0]):
            for j in range(var_interp.shape[2]):
                for i in range(var_interp.shape[3]):
                    LO_depths = dataset.z_rho.values[t, :, j, i]
                    var = dataset[var_name].values[t, :, j, i]
                    var_interp[t, :, j, i] = np.interp(
                        -NEMO_depths, LO_depths, var, left=np.nan)
                    # NEMO depths are positive, LiveOcean are negative
        interps[var_name] = np.ma.masked_invalid(var_interp)

    return interps


def fill_NaNs_with_nearest_neighbour(data, lons, lats):
    """At each depth level and time, fill in NaN values with nearest lateral
    neighbour. If the entire depth level is NaN, fill with values from level
    above. The last two dimensions of data are the lateral dimensions.
    lons.shape and lats.shape = (data.shape[-2], data.shape[-1])

    :arg data: the data to be filled
    :type data: 4D numpy array

    :arg lons: longitude points
    :type lons: 2D numpy array

    :arg lats: latitude points
    :type lats: 2D numpy array

    :returns: a 4D numpy array
    """
    filled = data.copy()
    for t in range(data.shape[0]):
        for k in range(data.shape[1]):
            subdata = data[t, k, :, :]
            mask = np.isnan(subdata)
            points = np.array([lons[~mask], lats[~mask]]).T
            valid_data = subdata[~mask]
            try:
                filled[t, k, mask] = interpolate.griddata(
                    points, valid_data, (lons[mask], lats[mask]),
                    method='nearest'
                )
            except ValueError:
                # if the whole depth level is NaN,
                # set it equal to the level above
                filled[t, k, :, :] = filled[t, k - 1, :, :]
    return filled


def interpolate_to_NEMO_lateral(var_arrays, dataset, NEMOlon, NEMOlat, shape):
    """Interpolates arrays in var_arrays laterally to NEMO grid.
    Assumes these arrays have already been interpolated vertically.
    NaN values are set to nearest lateral neighbour.
    If a vertical level is entirely NaNs, it is set equal to the level above.

    :arg var_arrays: dictionary of 4D numpy arrays.
                     Key represents the variable name.
    :type var_arrrays: dictionary

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
    interps = {}
    for var_name, var in var_arrays.items():
        var_new = np.zeros((var.shape[0], var.shape[1], shape[0], shape[1]))
        mask = var_new.copy()
        interp_nearest = var_new.copy()
        for t in range(var_new.shape[0]):
            for k in range(var_new.shape[1]):
                var_grid = var[t, k, :, :]
                # First, interpolate with bilinear. The result is masked near
                # and at grid points where var_grid is masked.
                var_interp = Basemap.interp(
                    var_grid, lonsLO, latsLO, NEMOlon, NEMOlat)
                # Keep track of mask
                mask[t, k, ...] = var_interp.mask
                # Next, interpolate using nearest neighbour so that masked
                # areas can be filled later.
                interp_nearest[t, k, ...] = Basemap.interp(
                    var_grid, lonsLO, latsLO, NEMOlon, NEMOlat, order=0)
                # ave bilinear intepr in var_new
                var_new[t, k, ...] = var_interp
        # Fill in masked values with nearest neighbour interpolant
        inds_of_mask = np.where(mask == 1)
        var_new[inds_of_mask] = interp_nearest[inds_of_mask]
        # There are still some nans over pure land areas.
        # Fill those with nearest lateral neighbour or level above
        interps[var_name] = fill_NaNs_with_nearest_neighbour(
            var_new, NEMOlon, NEMOlat)
    # Make sure salinity is strictly increasing with depth
    for k in range(1, var_new.shape[1]):
        interps['salt'][:, k] = np.fmax(interps['salt'][:, k], interps['salt'][:, k-1])
    # Make sure density is strictly increasing with depth
    interps = _increasing_density(interps)
    return interps


def _increasing_density(filled):
    # use approximate alpha and beta
    beta = 7.4e-4
    alpha = 2.1e-4
    stable = False

    while not stable:
        for t in np.arange(filled['salt'].shape[0]):
            approx_rho_stable = (
                beta * (filled['salt'][t, 1:] - filled['salt'][t, :-1]) - alpha *
                (filled['temp'][t, 1:] - filled['temp'][t, :-1]))
            if (np.min(approx_rho_stable) >= 0):
                stable = True
            else:
                inds_of_mask = np.where(approx_rho_stable < 0)
                for i, j in zip(inds_of_mask[1], inds_of_mask[2]):
                    ks = np.where(approx_rho_stable[:, i, j] < 0)
                    kmax = max(ks[0]) + 2
                    kmin = min(ks[0])
                    for var_name in ['salt', 'temp']:
                        average = np.mean(filled[var_name][t, kmin:kmax, i, j])
                        filled[var_name][t, kmin:kmax, i, j] = average
    return filled


def _bioFileSetup(TS, new):
    for dname, the_dim in TS.dimensions.items():
        new.createDimension(dname, len(the_dim) if not the_dim.isunlimited() else None)
    deptht=new.createVariable('deptht','float32',('deptht',))
    deptht.long_name = 'Vertical T Levels'
    deptht.units = 'm'
    deptht.positive = 'down'
    deptht.valid_range = np.array((4., 428.))
    deptht[:] = TS.variables['deptht'][:]

    #nav_lat
    nav_lat = new.createVariable('nav_lat','float32',('yb','xbT'))
    nav_lat.long_name = TS.variables['nav_lat'].long_name
    nav_lat.units = TS.variables['nav_lat'].units
    nav_lat[:] = TS.variables['nav_lat'][:]

    #nav_lon
    nav_lon = new.createVariable('nav_lon','float32',('yb','xbT'))
    nav_lon.long_name = TS.variables['nav_lon'].long_name
    nav_lon.units = TS.variables['nav_lon'].units
    nav_lon[:]=TS.variables['nav_lon'][:]

    # time_counter
    time_counter = new.createVariable('time_counter', 'float32', ('time_counter'))
    time_counter.long_name = 'Time axis'
    time_counter.axis = 'T'
    time_counter.units = 'weeks since beginning of year'
    time_counter[:] = TS.variables['time_counter'][:]

    # NO3
    voNO3 = new.createVariable('NO3', 'float32',
                                   ('time_counter','deptht','yb','xbT'))
    voNO3.grid = TS.variables['votemper'].grid
    voNO3.units = 'muM'
    voNO3.long_name = 'Nitrate'
    # don't yet set values

    #Si
    voSi = new.createVariable('Si', 'float32',
                                   ('time_counter','deptht','yb','xbT'))
    voSi.grid = TS.variables['votemper'].grid
    voSi.units = 'muM'
    voSi.long_name = 'Silica'
    # don't yet set values

    return(new)

def _ginterp(xval,xPeriod,yval,L,xlocs):
    # if not periodic, xPeriod=0
    fil=np.empty(np.size(xlocs))
    s=L/2.355
    for ii in range(0,xlocs.size):
        t=xlocs[ii]
        diff=[min(abs(x-t),abs(x-t+xPeriod), abs(x-t-xPeriod)) for x in xval]
        weight=[np.exp(-.5*x**2/s**2) if sum(diff<x)<2 or x < 5 else 0.0 for x in diff]
        weight=np.array(weight)
        if np.sum(weight)!=0:
            fil[ii]=np.sum(weight*yval)/np.sum(weight)
        else:
            fil[ii]=np.nan
    return(fil)

def _ginterp2d(xval,xPeriod,yval,yPeriod,zval,L,M,zlocs_x,zlocs_y):
    # if not periodic, xPeriod=0
    s=L/2.355
    n=M/2.355
    sdict={}
    mat=np.empty((np.size(zlocs_x),np.size(zlocs_y)))
    for ii in range(0,zlocs_x.size):
        for jj in range(0,zlocs_y.size):
            tx=zlocs_x[ii]
            ty=zlocs_y[jj]
            diffx=[min(abs(x-tx),abs(x-tx+xPeriod), abs(x-tx-xPeriod)) for x in xval]
            diffy=[min(abs(y-ty),abs(y-ty+yPeriod), abs(y-ty-yPeriod)) for y in yval]
            weight=[np.exp(-.5*(x**2+y**2)/(s**2+n**2)) if \
                    (sum(diffx<x)<3 or x < L) and (sum(diffy<y)<3 or y < M) \
                    else 0.0 for x, y in zip(diffx, diffy)]
            weight=np.array(weight)
            if np.sum(weight)!=0:
                sdict[(tx,ty)]=np.sum(weight*zval)/np.sum(weight)
                mat[ii,jj]=np.sum(weight*zval)/np.sum(weight)
            else:
                sdict[(tx,ty)]=np.nan
                mat[ii,jj]=np.nan
    return(sdict,mat)

# calculations
def recalcBioTSFits(TSfile,
    TSdir = '/results/forcing/LiveOcean/boundary_conditions',
    nFitFilePath = '/results/forcing/LiveOcean/boundary_conditions/bio/fits/bioOBCfit_NTS.csv',
    siFitFilePath = '/results/forcing/LiveOcean/boundary_conditions/bio/fits/bioOBCfit_SiTS.csv',
    nClimFilePath = '/results/forcing/LiveOcean/boundary_conditions/bio/fits/nmat.csv',
    siClimFilePath = '/results/forcing/LiveOcean/boundary_conditions/bio/fits/simat.csv',
    constFile='/ocean/eolson/MEOPAR/NEMO-3.6-inputs/boundary_conditions/bioOBC_constTest.nc'):
    """Recalculate TS fits and also create new boundary file for constant variables.

    :arg str TSfile: the name of a TS boundary file to use as a template for dimensions

    :arg str TSdir: path to the specified TSfile

    :arg str nFitFilePath: path and filename where N to T,S fit coefficients will be saved 
    
    :arg str siFitFilePath: path and filename where Si to T,S fit coefficients will be saved
 
    :arg str nClimFilePath: path and filename where N upper water column climatology will be saved 

    :arg str siClimFilePath: path and filename where Si upper water column climatology will be saved 

    :arg str constFile: path and filename where constant BC variables will be stored
    """
    try:
        import sqlalchemy
        from sqlalchemy import create_engine, case
        from sqlalchemy.orm import create_session
        from sqlalchemy.ext.automap import automap_base
        from sqlalchemy.sql import and_, or_, not_, func
    except ImportError:
        raise ImportError('You need to install sqlalchemy in your environment to run recalcBioTSFits.')
    # Load 3D T+S
    # define constant values, not yet based on data:
    val_bSi=7.74709546875e-06
    val_DIA=1e-8
    val_CRY=1e-8
    val_MYRI=1e-8
    val_MICZ=1e-8
    val_Oxy = 160.0
    val_Tur = 0.0

    TSfile='LO_y2016m10d25.nc'
    TSFilePath=os.path.join(TSdir,TSfile)
    TS = nc.Dataset(TSFilePath)

    newConst = nc.Dataset(constFile, 'w', zlib=True)
    #Copy dimensions
    for dname, the_dim in TS.dimensions.items():
        newConst.createDimension(dname, len(the_dim) if not the_dim.isunlimited() else None)

    # create dimension variables:
    # deptht
    new =newConst
    deptht=new.createVariable('deptht','float32',('deptht',))
    deptht.long_name = 'Vertical T Levels'
    deptht.units = 'm'
    deptht.positive = 'down'
    deptht.valid_range = np.array((4., 428.))
    deptht[:]=TS.variables['deptht']
    #nav_lat
    nav_lat = new.createVariable('nav_lat','float32',('yb','xbT'))
    nav_lat.long_name = TS.variables['nav_lat'].long_name
    nav_lat.units = TS.variables['nav_lat'].units
    nav_lat[:] = TS.variables['nav_lat']
    #nav_lon
    nav_lon = new.createVariable('nav_lon','float32',('yb','xbT'))
    nav_lon.long_name = TS.variables['nav_lon'].long_name
    nav_lon.units = TS.variables['nav_lon'].units
    nav_lon[:]=TS.variables['nav_lon']
    # variables below no longer included
    ## nbidta
    #nbidta=new.createVariable('nbidta','int32',('yb','xbT'))
    #nbidta.long_name = TS.variables['nbidta'].long_name
    #nbidta.units = TS.variables['nbidta'].units
    #nbidta[:]=TS.variables['nbidta']
    ## nbjdta
    #nbjdta=new.createVariable('nbjdta','int32',('yb','xbT'))
    #nbjdta.long_name = TS.variables['nbjdta'].long_name
    #nbjdta.units = TS.variables['nbjdta'].units
    #nbjdta[:]=TS.variables['nbjdta']
    ## nbrdta
    #nbrdta=new.createVariable('nbrdta','int32',('yb','xbT'))
    #nbrdta.long_name = TS.variables['nbrdta'].long_name
    #nbrdta.units = TS.variables['nbrdta'].units
    #nbrdta[:]=TS.variables['nbrdta']
    # time_counter
    time_counter = new.createVariable('time_counter', 'float32', ('time_counter'))
    time_counter.long_name = 'Time axis'
    time_counter.axis = 'T'
    time_counter.units = 'weeks since beginning of year'
    time_counter[:]=[0.0]
    # variables: NO3, Si, NH4, PHY, PHY2, MYRI, MICZ, POC, DOC, bSi
    #NH4
    voNH4 = newConst.createVariable('NH4', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    voNH4.grid = TS.variables['votemper'].grid
    voNH4.units = 'muM'
    voNH4.long_name = 'Ammonia' 
    # don't yet set values
    #DIA
    voDIA = newConst.createVariable('DIA', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    voDIA.units = 'muM N'
    voDIA.long_name = 'Diatoms'
    voDIA.grid = TS.variables['votemper'].grid
    voDIA[:]=val_DIA
    #CRY
    voCRY = newConst.createVariable('CRY', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    voCRY.units = 'muM N'
    voCRY.long_name = 'Cryptophytes'
    voCRY.grid = TS.variables['votemper'].grid
    voCRY[:]=val_CRY
    #MYRI
    voMYRI = newConst.createVariable('MYRI', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    voMYRI.units = 'muM N'
    voMYRI.long_name = 'M. rubra' 
    voMYRI.grid = TS.variables['votemper'].grid
    voMYRI[:]=val_MYRI
    #MICZ
    voMICZ = newConst.createVariable('MICZ', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    voMICZ.units = 'muM N'
    voMICZ.long_name = 'Microzooplankton' 
    voMICZ.grid = TS.variables['votemper'].grid
    voMICZ[:]=val_MICZ
    #PON
    voPON = newConst.createVariable('PON', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    voPON.units = 'muM N'
    voPON.long_name = 'Particulate Organic Nitrogen'
    voPON.grid = TS.variables['votemper'].grid
    #voPON[:] = val_PON
    #DON
    voDON = newConst.createVariable('DON', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    voDON.units = 'muM N'
    voDON.long_name = 'Dissolved Organic Nitrogen'
    voDON.grid = TS.variables['votemper'].grid
    #voDON[:]=DON_val
    #bSi
    vobSi = newConst.createVariable('bSi', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    vobSi.units = 'muM N'
    vobSi.long_name = 'Biogenic Silica'
    vobSi.grid = TS.variables['votemper'].grid
    vobSi[:]=val_bSi
    #O2
    voO2 = newConst.createVariable('O2', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    #voO2.units = ''
    voO2.long_name = 'oxygen'
    voO2.grid = TS.variables['votemper'].grid
    voO2[:]=val_Oxy
    #turbidity
    votu = newConst.createVariable('tur', 'float32', 
                                   ('time_counter','deptht','yb','xbT'))
    #voO2.units = ''
    votu.long_name = 'turbidity'
    votu.grid = TS.variables['votemper'].grid
    votu[:]=0.0

    # load database for data-based conditions
    basepath='/ocean/eolson/MEOPAR/obs/'
    basedir=basepath + 'DFOOPDB/'
    dbname='DFO_OcProfDB'

    # engine and reflection
    Base = automap_base()
    engine = create_engine('sqlite:///' + basedir + dbname + '.sqlite', echo = False)
    Base.prepare(engine, reflect=True)
    Station=Base.classes.StationTBL
    Obs=Base.classes.ObsTBL
    JDFLocs=Base.classes.JDFLocsTBL
    Calcs=Base.classes.CalcsTBL
    session = create_session(bind = engine, autocommit = False, autoflush = True)

    # definitions
    SA=case([(Calcs.Salinity_Bottle_SA!=None, Calcs.Salinity_Bottle_SA)], else_=
             case([(Calcs.Salinity_T0_C0_SA!=None, Calcs.Salinity_T0_C0_SA)], else_=
             case([(Calcs.Salinity_T1_C1_SA!=None, Calcs.Salinity_T1_C1_SA)], else_=
             case([(Calcs.Salinity_SA!=None, Calcs.Salinity_SA)], else_=
             case([(Calcs.Salinity__Unknown_SA!=None, Calcs.Salinity__Unknown_SA)], else_=Calcs.Salinity__Pre1978_SA)
            ))))
    NO=case([(Obs.Nitrate_plus_Nitrite!=None, Obs.Nitrate_plus_Nitrite)], else_=Obs.Nitrate)
    NOUnits=case([(Obs.Nitrate_plus_Nitrite!=None, Obs.Nitrate_plus_Nitrite_units)], else_=Obs.Nitrate_units)
    NOFlag=case([(Obs.Nitrate_plus_Nitrite!=None, Obs.Flag_Nitrate_plus_Nitrite)], else_=Obs.Flag_Nitrate)
    # Obs.Quality_Flag_Nitr does not match any nitrate obs
    # ISUS not included in this NO
    Tem=case([(Obs.Temperature!=None, Obs.Temperature)], else_=
             case([(Obs.Temperature_Primary!=None, Obs.Temperature_Primary)], else_=
             case([(Obs.Temperature_Secondary!=None, Obs.Temperature_Secondary)], else_=Obs.Temperature_Reversing)))
    TemUnits=case([(Obs.Temperature!=None, Obs.Temperature_units)], else_=
             case([(Obs.Temperature_Primary!=None, Obs.Temperature_Primary_units)], else_=
             case([(Obs.Temperature_Secondary!=None, Obs.Temperature_Secondary_units)], 
                  else_=Obs.Temperature_Reversing_units)))
    TemFlag=Obs.Quality_Flag_Temp
    Ox=case([(Calcs.Oxygen_umolL!=None, Calcs.Oxygen_umolL)], else_=Calcs.Oxygen_Dissolved_umolL)
    OxFlag=case([(Calcs.Oxygen_umolL!=None, Obs.Quality_Flag_Oxyg)], else_=Obs.Flag_Oxygen_Dissolved)
    Press=case([(Obs.Pressure!=None, Obs.Pressure)], else_=Obs.Pressure_Reversing)

    # Ammonium:

    q=session.query(JDFLocs.ObsID, Station.StartYear,Station.StartMonth,Press,
                    Obs.Ammonium,Obs.Ammonium_units,Tem,SA).select_from(Obs).\
            join(JDFLocs,JDFLocs.ObsID==Obs.ID).join(Station,Station.ID==Obs.StationTBLID).\
            join(Calcs,Calcs.ObsID==Obs.ID).filter(Obs.Ammonium!=None).\
            all()
    qP=[]
    qNH=[]
    remP=[]
    remNH=[]
    for OID, Yr, Mn, P, NH, un, T, S_A in q:
        # throw out 1 data point that seems unusually high
        if not (P>75 and NH >.2):
            qP.append(P)
            qNH.append(NH)
        else:
            remP.append(P)
            remNH.append(NH)
    qP=np.array(qP)
    qNH=np.array(qNH)
    remP=np.array(remP)
    remNH=np.array(remNH)

    # create depth-weighted mean profile using gaussian filter
    zs=np.array(TS.variables['deptht'])
    AmmProf=_ginterp(qP,0.0,qNH,10,zs)
    AmmProf[AmmProf!=AmmProf]=0.0


    for ii in range(0,zs.size):
        voNH4[:,ii,0,:]=AmmProf[ii]

    # DON

    # take nearest available data to SJDF
    q=session.query(Station.StartYear,Station.StartMonth,Press, Station.Lat, Station.Lon,Obs.Depth,
                    Obs.Nitrogen_Dissolved_Organic,Obs.Nitrogen_Dissolved_Organic_units,Tem).\
            select_from(Obs).join(Station,Station.ID==Obs.StationTBLID).\
            filter(Obs.Nitrogen_Dissolved_Organic!=None).filter(Obs.Nitrogen_Dissolved_Organic>=0).\
            filter(Station.Lat!=None).filter(Station.Lon!=None).\
            filter(Station.Lat<48.8).filter(Station.Lon<-125).all()

    qDON=[]
    for row in q:
        qDON.append(row.Nitrogen_Dissolved_Organic)
    val_DON=np.mean(qDON)

    voDON[:,:,:,:]=val_DON

    # PON

    # take nearest available data to SJDF
    q=session.query(Station.StartYear,Station.StartMonth,Press, Station.Lat, Station.Lon,Obs.Depth,
                    Obs.Nitrogen_Particulate_Organic,Obs.Nitrogen_Particulate_Organic_units,Tem).\
            select_from(Obs).join(Station,Station.ID==Obs.StationTBLID).\
            filter(Obs.Nitrogen_Particulate_Organic!=None).filter(Obs.Nitrogen_Particulate_Organic>=0).\
            filter(Station.Lat!=None).filter(Station.Lon!=None).\
            filter(Station.Lat<48.8).filter(Station.Lon<-125).all()

    qPON=[]
    for row in q:
        qPON.append(row.Nitrogen_Particulate_Organic)
    val_PON=np.mean(qPON)

    voPON[:,:,:,:]=val_PON

    newConst.close()
    TS.close()

    # set up NO3 and save climatology:
    # umol/L=mmol/m**3, so all NO units the same
    q=session.query(JDFLocs.ObsID, Station.StartYear,Station.StartMonth,Press,NO,
                    Tem,SA,Station.StartDay).select_from(Obs).\
            join(JDFLocs,JDFLocs.ObsID==Obs.ID).join(Station,Station.ID==Obs.StationTBLID).\
            join(Calcs,Calcs.ObsID==Obs.ID).filter(SA<38).filter(SA>0).filter(NO!=None).\
            filter(Tem!=None).filter(SA!=None).filter(Press!=None).\
            all()
    qNO50=[]
    qSA50=[]
    qP50=[]
    qT50=[]
    for OID, Yr, Mn, P, NO3, T, S_A, dy in q:
        if P>80:
            qNO50.append(NO3)
            qT50.append(T)
            qSA50.append(S_A)
            qP50.append(P)
    qNO50=np.array(qNO50)
    qSA50=np.array(qSA50)
    qT50=np.array(qT50)
    qP50=np.array(qP50)
    qTC50=gsw_calls.generic_gsw_caller('gsw_CT_from_t.m',
                                                 [qSA50, qT50, qP50, ])
    qNO50=np.array(qNO50)

    a=np.vstack([qTC50,qSA50,np.ones(len(qTC50))]).T
    #a2=np.vstack([qTC,qSA,np.ones(len(qTC))]).T
    m = np.linalg.lstsq(a,qNO50)[0]
    mT, mS, mC = m
    df=pd.DataFrame({'mC':[mC],'mT':[mT],'mS':[mS]})
    df.to_csv(nFitFilePath)

    zupper=np.extract(zs<100, zs)
    ydays=np.arange(0,365,365/52)

    # umol/L=mmol/m**3, so all NO units the same
    q=session.query(JDFLocs.ObsID, Station.StartYear,Station.StartMonth,Press,NO,
                    Tem,SA,Station.StartDay).select_from(Obs).\
            join(JDFLocs,JDFLocs.ObsID==Obs.ID).join(Station,Station.ID==Obs.StationTBLID).\
            join(Calcs,Calcs.ObsID==Obs.ID).filter(SA<38).filter(SA>0).filter(NO!=None).\
            filter(Tem!=None).filter(SA!=None).filter(Press<120).filter(Press!=None).\
            all()
    #for row in q:
    #    print(row)

    qYr=[]
    qMn=[]
    qDy=[]
    qP=[]
    qNO=[]
    date=[]
    for OID, Yr, Mn, P, NO3, T, S_A, dy in q:
        qYr.append(Yr)
        qMn.append(Mn)
        qDy.append(dy)
        qP.append(P)
        qNO.append(NO3)
        date.append(datetime.date(int(Yr),int(Mn),int(dy)))

    qP=np.array(qP)
    qNO=np.array(qNO)
    date=np.array(date)
    YD=0.0*qNO
    for i in range(0,len(YD)):
        YD[i]=date[i].timetuple().tm_yday

    ndict,nmat=_ginterp2d(YD,365,qP,0,qNO,30,10,ydays,zupper)
    np.savetxt(nClimFilePath,nmat,delimiter=',')

    # set up Si and save climatology:
    # umol/L=mmol/m**3, so all NO units the same
    q=session.query(JDFLocs.ObsID, Station.StartYear,Station.StartMonth,Press,
                    Obs.Silicate,Tem,SA,Station.StartDay).select_from(Obs).\
            join(JDFLocs,JDFLocs.ObsID==Obs.ID).join(Station,Station.ID==Obs.StationTBLID).\
            join(Calcs,Calcs.ObsID==Obs.ID).filter(SA<38).filter(SA>0).filter(Obs.Silicate!=None).\
            filter(Tem!=None).filter(SA!=None).filter(Press!=None).\
            all()
    qP50=[]
    qNO50=[]
    qSA50=[]
    qT50=[]
    for OID, Yr, Mn, P, NO3, T, S_A, dy in q:
        if P>80:
            qP50.append(P)
            qNO50.append(NO3)
            qT50.append(T)
            qSA50.append(S_A)

    qP50 =np.array(qP50)
    qSA50=np.array(qSA50)
    qT50 =np.array(qT50)
    qTC50=gsw_calls.generic_gsw_caller('gsw_CT_from_t.m',[qSA50, qT50, qP50, ])
    qNO50=np.array(qNO50)

    a=np.vstack([qTC50,qSA50,np.ones(len(qTC50))]).T
    m = np.linalg.lstsq(a,qNO50)[0]
    mT, mS, mC = m
    df=pd.DataFrame({'mC':[mC],'mT':[mT],'mS':[mS]})
    df.to_csv(siFitFilePath)

    # umol/L=mmol/m**3, so all NO units the same
    q=session.query(JDFLocs.ObsID, Station.StartYear,Station.StartMonth,Press,Obs.Silicate,
                    Tem,SA,Station.StartDay).select_from(Obs).\
            join(JDFLocs,JDFLocs.ObsID==Obs.ID).join(Station,Station.ID==Obs.StationTBLID).\
            join(Calcs,Calcs.ObsID==Obs.ID).filter(SA<38).filter(SA>0).filter(Obs.Silicate!=None).\
            filter(Tem!=None).filter(SA!=None).filter(Press<120).filter(Press!=None).\
            all()
    qYr=[]
    qMn=[]
    qDy=[]
    qP=[]
    qNO=[]
    date=[]
    for OID, Yr, Mn, P, NO3, T, S_A, dy in q:
        qYr.append(Yr)
        qMn.append(Mn)
        qDy.append(dy)
        qP.append(P)
        qNO.append(NO3)
        date.append(datetime.date(int(Yr),int(Mn),int(dy)))
    qP=np.array(qP)
    qNO=np.array(qNO)
    date=np.array(date)
    YD=0.0*qP
    for i in range(0,len(YD)):
        YD[i]=date[i].timetuple().tm_yday
    sidict,simat=_ginterp2d(YD,365,qP,0,qNO,30,10,ydays,zupper)
    np.savetxt(siClimFilePath,simat,delimiter=',')

    return

# ------------------ Creation of files ------------------------------
def create_LiveOcean_bio_BCs_fromTS(TSfile, strdate=None,
    TSdir = '/results/forcing/LiveOcean/boundary_conditions',
    outFile='bioLOTS_{:y%Ym%md%d}.nc',
    outDir = '/results/forcing/LiveOcean/boundary_conditions/bio',
    nFitFilePath = '/results/forcing/LiveOcean/boundary_conditions/bio/fits/bioOBCfit_NTS.csv',
    siFitFilePath = '/results/forcing/LiveOcean/boundary_conditions/bio/fits/bioOBCfit_SiTS.csv',
    nClimFilePath = '/results/forcing/LiveOcean/boundary_conditions/bio/fits/nmat.csv',
    siClimFilePath = '/results/forcing/LiveOcean/boundary_conditions/bio/fits/simat.csv',
    recalcFits=False):
    """ create BC files from LiveOcean-based TS BC files using linear fit of N and Si to T and S

    :arg str TSfile: name of LiveOcean-based TS Bc file

    :arg str strdate: the LiveOcean rundate in format yyyy-mm-dd. If not provided, it will be
                        inferred from TSfile if possible.

    :arg str TSdir: path to directory where TSfile is located

    :arg str outFile: file name or nowcast-style filename template for output file

    :arg str outDir: path where outFile should be created

    :arg str nFitFilePath: path and filename from which to load N to T,S fit coefficients

    :arg str siFitFilePath: path and filename from which to load Si to T,S fit coefficients

    :arg str nClimFilePath: path and filename from which to load N upper water column climatology

    :arg str siClimFilePath: path and filename from which to load Si upper water column climatology

    :arg Boolean recalcFits: if true, recalculate the T,S fits and store them in the paths
                             they would otherwise be loaded from. Constant variable BC file will
                             also be recalculated and overwritten at default path.

    :returns: Filepath of nutrients boundary conditions file that was created
    :rtype: str
    """

    # if requested, recalculate nut-TS fits and nut climatologies from database
    if recalcFits==True:
        recalcBioTSFits(nFitFilePath = nFitFilePath,siFitFilePath = siFitFilePath,
                         nClimFilePath = nClimFilePath, siClimFilePath = siClimFilePath)

    # if no date is supplied, try to get it from the TS file name. otherwise, process it
    # note: None case is fragile
    if strdate==None:
        TSyear=int(TSfile[-13:-9])
        TSmon=int(TSfile[-8:-6])
        TSday=int(TSfile[-5:-3])
        dtdate=datetime.datetime(TSyear,TSmon,TSday)
    else:
        dtdate = datetime.datetime.strptime(strdate, '%Y-%m-%d')
        TSyear = dtdate.year

    YD=(dtdate-datetime.datetime(TSyear-1,12,31)).days

    # if necessary, substitue date into file name
    if ('{' in outFile):
        outFile=outFile.format(dtdate)

    # TS file is name of LO TS OBC file for the date you want bio OBCs for
    TS = nc.Dataset(os.path.join(TSdir, TSfile))

    # create and open file to write to, set up dimensions and vars
    tofile = os.path.join(outDir, outFile)
    if os.path.exists(tofile):
        os.remove(tofile)
    new = nc.Dataset(tofile, 'w', zlib=True)
    new = _bioFileSetup(TS, new)

    # other definitions
    zs=np.array(new.variables['deptht'])
    zupper=np.extract(zs<100, zs)
    ydays=np.arange(0,365,365/52)

    # load N data
    nmat=np.loadtxt(nClimFilePath,delimiter=',')
    df = pd.read_csv(nFitFilePath,index_col=0)
    mC=df.loc[0,'mC']
    mT=df.loc[0,'mT']
    mS=df.loc[0,'mS']

    # process N
    ztan=[.5*math.tanh((a-70)/20)+1/2 for a in zupper]
    zcoeff=np.ones(np.shape(TS.variables['votemper'])) # zcoeff is multiplier of fit function; 1-zcoeff is multiplier of climatology
    for i in range(0,zupper.size):
        zcoeff[:,i,:,:]=ztan[i]
    funfit=mC +mT*TS.variables['votemper'][:,:,:,:]+mS*TS.variables['vosaline'][:,:,:,:]

    nmat0=np.zeros((np.shape(TS.variables['votemper'])[0],np.shape(nmat)[1]))
    for ii in range(0,np.shape(nmat0)[1]):
        nmat0[:,ii]=np.interp(YD,ydays,nmat[:,ii],period=365)
    nmat_2=np.expand_dims(nmat0,axis=2)
    nmat_2=np.expand_dims(nmat_2,axis=3)
    nmat_3=np.tile(nmat_2,(1,1,1,TS.variables['votemper'].shape[3]))
    clim=np.zeros(TS.variables['votemper'].shape)
    clim[:,0:27,:,:]=nmat_3

    # set N variable
    new.variables['NO3'][:,:,:,:]=zcoeff*funfit+(1-zcoeff)*clim

    # load Si data
    simat=np.loadtxt(siClimFilePath,delimiter=',')
    dfS = pd.read_csv(siFitFilePath,index_col=0)
    mC=dfS.loc[0,'mC']
    mT=dfS.loc[0,'mT']
    mS=dfS.loc[0,'mS']

    # process Si
    funfit=mC +mT*TS.variables['votemper'][:,:,:,:]+mS*TS.variables['vosaline'][:,:,:,:]

    simat0=np.zeros((np.shape(TS.variables['votemper'])[0],np.shape(simat)[1]))
    for ii in range(0,np.shape(simat0)[1]):
        simat0[:,ii]=np.interp(YD,ydays,simat[:,ii],period=365)
    simat_2=np.expand_dims(simat0,axis=2)
    simat_2=np.expand_dims(simat_2,axis=3)
    simat_3=np.tile(simat_2,(1,1,1,TS.variables['votemper'].shape[3]))
    clim=np.zeros(TS.variables['votemper'].shape)
    clim[:,0:27,:,:]=simat_3

    # set Si variable
    new.variables['Si'][:,:,:,:]=zcoeff*funfit+(1-zcoeff)*clim

    new.close()
    TS.close()

    return tofile


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
