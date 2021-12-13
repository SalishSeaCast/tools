# Copyright 2018-2021 The Salish Sea NEMO Project and
# The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# may requires python version 3.5 or higher for recursive glob

"""Flexible functions for model evalution tasks
"""

import datetime as dt
import numpy as np
import netCDF4 as nc
import pandas as pd
import glob
from salishsea_tools import geo_tools, places
import gsw
import os
import pytz
import pickle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import cmocean as cmo
import warnings
import re
import f90nml
import sys
import xarray as xr

# Check which Excel reader engine is available, if any, and set variable excelEngine
try:
    import openpyxl
    excelEngine='openpyxl'
except ImportError as iE:
    try:
        import xlrd
        excelEngine='xlrd'
    except ImportError as iE:
        excelEngine=None
        warnings.warn("Neither Python Excel module ('openpyxl','xlrd') found",UserWarning)

# :arg dict varmap: dictionary mapping names of data columns to variable names, string to string, model:data
def matchData(
    data,
    filemap,
    fdict,
    mod_start=None,
    mod_end=None,
    mod_nam_fmt='nowcast',
    mod_basedir='/results/SalishSea/nowcast-green/',
    mod_flen=1,
    method='bin',
    meshPath=None,
    maskName='tmask',
    wrapSearch=False,
    fastSearch=False,
    wrapTol=1,
    e3tvar='e3t',
    fid=None,
    sdim=3,
    quiet=False,
    preIndexed=False
    ):
    """Given a discrete sample dataset, find match model output

    note: only one grid mask is loaded so all model variables must be on same grid; defaults to tmask;
        call multiple times for different grids (eg U,W)

    :arg data: pandas dataframe containing data to compare to. Must include the following:
        'dtUTC': column with UTC date and time
        'Lat': decimal latitude
        'Lon': decimal longitude
        'Z': depth, positive     NOT  required if method='ferry' or sdim=2
    :type :py:class:`pandas.DataFrame`

    :arg dict filemap: dictionary mapping names of model variables to filetypes containing them

    :arg dict fdict: dictionary mapping filetypes to their time resolution in hours

    :arg mod_start: first date of time range to match
    :type :py:class:`datetime.datetime`

    :arg mod_end: end of date range to match (not included)
    :type :py:class:`datetime.datetime`

    :arg str mod_nam_fmt: naming format for model files. options are 'nowcast' or 'long'
        'nowcast' example: 05may15/SalishSea_1h_20150505_20150505_ptrc_T.nc
        'long' example: SalishSea_1h_20150206_20150804_ptrc_T_20150427-20150506.nc
                    'long' will recursively search subdirectories (to match Vicky's storage style)

    :arg str mod_basedir: path to search for model files; defaults to nowcast-green

    :arg int mod_flen: length of model files in days; defaults to 1, which is how nowcast data is stored

    :arg str method: method to use for matching. options are:
        'bin'- return model value from grid/time interval containing observation
        'vvlBin' - same as 'bin' but consider tidal change in vertical grid
        'vvlZ' - consider tidal change in vertical grid and interpolate in the vertical
        'ferry' - match observations to top model layer
        'vertNet' - match observations to mean over a vertical range defined by
                    Z_upper and Z_lower; first try will include entire cell containing end points
                    and use e3t_0 rather than time-varying e3t

    :arg str meshPath: path to mesh file; defaults to None, in which case set to:
            '/results/forcing/atmospheric/GEM2.5/operational/ops_y2015m01d01.nc' if maskName is 'ops'
            '/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702_noLPE.nc' else (SalishSeaCast)

    :arg str maskName: variable name for mask in mesh file (check code for consistency if not tmask)
                       for ops vars use 'ops'

    :arg boolean wrapSearch: if True, use wrapper on find_closest_model_point that assumes
                             nearness of subsequent values

    :arg int wrapTol: assumed search radius from previous grid point if wrapSearch=True

    :arg str e3tvar: name of tgrid thicknesses variable; only for method=interpZe3t, which only works on t grid

    :arg Dataset fid: optionally include name of a single dataset when looping is not necessary and all matches come from
        a single file

    :arg int sdim: optionally enter number of spatial dimensions (must be the same for all variables per call);
        defaults to 3; use to match to 2d fields like ssh

    :arg boolean quiet: if True, suppress non-critical warnings

    :arg boolean preIndexed: set True if horizontal  grid indices already in input dataframe; for
               speed; not implemented with all options

    """
    # define dictionaries of mesh lat and lon variables to use with different grids:
    lonvar={'tmask':'nav_lon','umask':'glamu','vmask':'glamv','fmask':'glamf'}
    latvar={'tmask':'nav_lat','umask':'gphiu','vmask':'gphiv','fmask':'gphif'}

    # check that required columns are in dataframe:
    if method == 'ferry' or sdim==2:
        reqsubset=['dtUTC','Lat','Lon']
        if preIndexed:
            reqsubset=['dtUTC','i','j']
    elif method == 'vertNet':
        reqsubset=['dtUTC','Lat','Lon','Z_upper','Z_lower']
        if preIndexed:
            reqsubset=['dtUTC','i','j','Z_upper','Z_lower']
    else:
        reqsubset=['dtUTC','Lat','Lon','Z']
        if preIndexed:
            reqsubset=['dtUTC','i','j','k']
    if not set(reqsubset) <= set(data.keys()):
        raise Exception('{} missing from data'.format([el for el in set(reqsubset)-set(data.keys())],'%s'))

    fkeysVar=list(filemap.keys()) # list of model variables to return
    # don't load more files than necessary:
    ftypes=list(fdict.keys())
    for ikey in ftypes:
        if ikey not in set(filemap.values()):
            fdict.pop(ikey)
    if len(set(filemap.values())-set(fdict.keys()))>0:
        print('Error: file(s) missing from fdict:',set(filemap.values())-set(fdict.keys()))
    ftypes=list(fdict.keys()) # list of filetypes to containing the desired model variables
    # create inverted version of filemap dict mapping file types to the variables they contain
    filemap_r=dict()
    for ift in ftypes:
        filemap_r[ift]=list()
    for ikey in filemap:
        filemap_r[filemap[ikey]].append(ikey)

    # if mod_start and mod_end not provided, use min and max of data datetimes
    if mod_start is None:
        mod_start=np.min(data['dtUTC'])
        print(mod_start)
    if mod_end is None:
        mod_end=np.max(data['dtUTC'])
        print(mod_end)
    # adjustments to data dataframe to avoid unnecessary calculations
    data=data.loc[(data.dtUTC>=mod_start)&(data.dtUTC<mod_end)].copy(deep=True)
    data=data.dropna(how='any',subset=reqsubset) #.dropna(how='all',subset=[*varmap.keys()])

    if maskName=='ops':
        # set default mesh file for ops data (atmos forcing)
        if meshPath==None:
            meshPath='/results/forcing/atmospheric/GEM2.5/operational/ops_y2015m01d01.nc'
        # load lat, lon, and mask (all ones for ops - no land in sky)
        with nc.Dataset(meshPath) as fmesh:
            navlon=np.squeeze(np.copy(fmesh.variables['nav_lon'][:,:]-360))
            navlat=np.squeeze(np.copy(fmesh.variables['nav_lat'][:,:]))
        omask=np.expand_dims(np.ones(np.shape(navlon)),axis=(0,1))
        nemops='GEM2.5'
    else:
        # set default mesh file for SalishSeaCast data
        if meshPath==None:
            meshPath='/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702_noLPE.nc'
        # load lat lon and ocean mask
        with nc.Dataset(meshPath) as fmesh:
            omask=np.copy(fmesh.variables[maskName])
            navlon=np.squeeze(np.copy(fmesh.variables[lonvar[maskName]][:,:]))
            navlat=np.squeeze(np.copy(fmesh.variables[latvar[maskName]][:,:]))
            if method == 'vertNet':
                e3t0=np.squeeze(np.copy(fmesh.variables['e3t_0'][0,:,:,:]))
                if maskName != 'tmask':
                    print('Warning: Using tmask thickness for variable on different grid')
        nemops='NEMO'

    # handle horizontal gridding as necessary; make sure data is in order of ascending time
    if not preIndexed:
        # find location of each obs on model grid and add to data as additional columns 'i' and 'j'
        data=_gridHoriz(data,omask,navlon,navlat,wrapSearch,wrapTol,fastSearch, quiet=quiet,nemops=nemops)
        data=data.sort_values(by=[ix for ix in ['dtUTC','Z','j','i'] if ix in reqsubset]) # preserve list order
    else:
        data=data.sort_values(by=[ix for ix in ['dtUTC','k','j','i'] if ix in reqsubset]) # preserve list order
    data.reset_index(drop=True,inplace=True)

    # set up columns to accept model values; prepend 'mod' to distinguish from obs names
    for ivar in filemap.keys():
        data['mod_'+ivar]=np.full(len(data),np.nan)

    # create dictionary of dataframes of filename, start time, and end time for each file type
    flist=dict()
    for ift in ftypes:
        flist[ift]=index_model_files(mod_start,mod_end,mod_basedir,mod_nam_fmt,mod_flen,ift,fdict[ift])

    # call a function to carry out vertical matching based on specified method
    if method == 'bin':
        data = _binmatch(data,flist,ftypes,filemap_r,omask,maskName,sdim,preIndexed=preIndexed)
    elif method == 'ferry':
        print('data is matched to shallowest model level')
        data = _ferrymatch(data,flist,ftypes,filemap_r,omask,fdict)
    elif method == 'vvlZ':
        data = _interpvvlZ(data,flist,ftypes,filemap,filemap_r,omask,fdict,e3tvar)
    elif method == 'vvlBin':
        data= _vvlBin(data,flist,ftypes,filemap,filemap_r,omask,fdict,e3tvar)
    elif method == 'vertNet':
        data = _vertNetmatch(data,flist,ftypes,filemap_r,omask,e3t0,maskName)
    else:
        print('option '+method+' not written yet')
        return
    data.reset_index(drop=True,inplace=True)
    return data

def _gridHoriz(data,omask,navlon,navlat,wrapSearch,wrapTol,fastSearch=False, resetIndex=False,quiet=False,nemops='NEMO'):
    """ this function finds the horizontal grid (i,j) indices for each model point and adds them
        to the dataframe 'data' as additional columns
        NOTE: points that are matched are dropped from the dataFrame; with quiet=False, the unmatched
        lats and lons are printed
    """
    lmask=-1*(omask[0,0,:,:]-1) # NEMO masks have ocean = 1, but the functions called below require land = 1
    if wrapSearch:
        # this speeds up the matching process for ferry data where there is a high likelihood each point
        #  is close to the point before it
        jj,ii = geo_tools.closestPointArray(data['Lon'].values,data['Lat'].values,navlon,navlat,
                                                        tol2=wrapTol,land_mask = lmask)
        data['j']=[-1 if np.isnan(mm) else int(mm) for mm in jj]
        data['i']=[-1 if np.isnan(mm) else int(mm) for mm in ii]
    elif fastSearch:
        jjii = xr.open_dataset('~/MEOPAR/grid/grid_from_lat_lon_mask999.nc')
        print (data['Lat'])
        mylats = xr.DataArray(data['Lat'])
        mylons = xr.DataArray(data['Lon'])
        jj = jjii.jj.sel(lats=mylats, lons=mylons, method='nearest').values
        ii = jjii.ii.sel(lats=mylats, lons=mylons, method='nearest').values
        print (jj.shape, jj)
        data['j'] = [-1 if mm==-999 else mm for mm in jj]
        data['i'] = [-1 if mm==-999 else mm for mm in ii]
    else:
        data['j']=-1*np.ones((len(data))).astype(int)
        data['i']=-1*np.ones((len(data))).astype(int)
        for la,lo in np.unique(data.loc[:,['Lat','Lon']].values,axis=0):
            try:
                jj, ii = geo_tools.find_closest_model_point(lo, la, navlon,
                                            navlat, grid=nemops,land_mask = lmask,checkTol=True)
            except:
                print('lo:',lo,'la:',la)
                raise
            if isinstance(jj,int):
                data.loc[(data.Lat==la)&(data.Lon==lo),['j','i']]=jj,ii
            else:
                if not quiet:
                    print('(Lat,Lon)=',la,lo,' not matched to domain')
    data.drop(data.loc[(data.i==-1)|(data.j==-1)].index, inplace=True)
    if resetIndex==True:
        data.reset_index(drop=True,inplace=True)
    return data

def _vertNetmatch(data,flist,ftypes,filemap_r,gridmask,e3t0,maskName='tmask'):
    """ basic vertical matching of model output to data
        returns model value from model grid cell that would contain the observation point with
        no interpolation; no consideration of the changing of grid thickenss with the tides (vvl)
        strategy: loop through data, openening and closing model files as needed and storing model data
    """
    if len(data)>5000:
        pprint=True
        lendat=len(data)
    else:
        pprint= False
    # set up columns to hold indices for upper and lower end of range to average over
    data['k_upper']=-1*np.ones((len(data))).astype(int)
    data['k_lower']=-1*np.ones((len(data))).astype(int)
    for ind, row in data.iterrows():
        if (pprint==True and ind%5000==0):
            print('progress: {}%'.format(ind/lendat*100))
        if ind==0: # special case for start of loop; load first files
            fid=dict()
            fend=dict()
            torig=dict()
            for ift in ftypes:
                fid,fend=_nextfile_bin(ift,row['dtUTC'],flist[ift],fid,fend,flist)
                # handle NEMO files time reference
                if 'time_centered' in fid[ftypes[0]].variables.keys():
                    torig[ift]=dt.datetime.strptime(fid[ftypes[0]].variables['time_centered'].time_origin,'%Y-%m-%d %H:%M:%S')
                else:
                    torig[ift]=dt.datetime.strptime(fid[ftypes[0]].variables['time_counter'].time_origin,'%Y-%m-%d %H:%M:%S')
        # loop through each file type to extract data from the appropriate time and location
        for ift in ftypes:
            if row['dtUTC']>=fend[ift]:
                fid,fend=_nextfile_bin(ift,row['dtUTC'],flist[ift],fid,fend,flist)
            # now read data
            # find time index
            try:
                if 'time_centered_bounds' in fid[ift].variables.keys(): # no problem! 
                    ih=_getTimeInd_bin(row['dtUTC'],fid[ift],torig[ift])
                else: # annoying!
                    hpf=(flist[ift]['t_n'][0]-flist[ift]['t_0'][0]).total_seconds()/3600 #hours per file
                    ih=_getTimeInd_bin(row['dtUTC'],fid[ift],torig[ift],hpf=hpf)
            except:
                print(row['dtUTC'],ift,torig[ift])
                tlist=fid[ift].variables['time_centered_bounds'][:,:]
                for el in tlist:
                    print(el)
                print((row['dtUTC']-torig[ift]).total_seconds())
                print(tlist[-1,1])
                raise
            # find depth indices (assume they may be reversed)
            z_l=max(row['Z_upper'],row['Z_lower'])
            z_u=min(row['Z_upper'],row['Z_lower'])
            if len(set(fid[ift].variables.keys()).intersection(set(('deptht_bounds','depthu_bounds','depthv_bounds'))))>0: # no problem! 
                ik_l=_getZInd_bin(z_l,fid[ift],maskName=maskName)
                ik_u=_getZInd_bin(z_u,fid[ift],maskName=maskName)
            else: # workaround for missing variable
                ik_l=_getZInd_bin(z_l,fid[ift],boundsFlag=True,maskName=maskName)
                ik_u=_getZInd_bin(z_u,fid[ift],boundsFlag=True,maskName=maskName)
            # assign values for each var assoc with ift
            if (not np.isnan(ik_l)) and (not np.isnan(ik_u)) and \
                         (gridmask[0,ik_u,row['j'],row['i']]==1):
                data.loc[ind,['k_upper']]=int(ik_u)
                data.loc[ind,['k_lower']]=int(ik_l)
                for ivar in filemap_r[ift]:
                    var=fid[ift].variables[ivar][ih,ik_u:(ik_l+1),row['j'],row['i']]
                    e3t=e3t0[ik_u:(ik_l+1),row['j'],row['i']]
                    imask=gridmask[0,ik_u:(ik_l+1),row['j'],row['i']]
                    meanvar=np.sum(var*e3t*imask)/np.sum(e3t*imask)
                    data.loc[ind,['mod_'+ivar]]=meanvar
                    if gridmask[0,ik_l,row['j'],row['i']]==0:
                        print(f"Warning: lower limit is not an ocean value:",
                             f" i={row['i']}, j={row['j']}, k_upper={ik_u}, k_lower={ik_l},",
                             f"k_seafloor={np.sum(imask)}",
                             f"Lon={row['Lon']}, Lat={row['Lat']}, dtUTC={row['dtUTC']}")
            else:
                print(f"Warning: upper limit is not an ocean value:",
                     f" i={row['i']}, j={row['j']}, k_upper={ik_u},Lat={row['Lat']},",
                     f"Lon={row['Lon']},dtUTC={row['dtUTC']}")
    return data

def _binmatch(data,flist,ftypes,filemap_r,gridmask,maskName='tmask',sdim=3,preIndexed=False):
    """ basic vertical matching of model output to data
        returns model value from model grid cell that would contain the observation point with
        no interpolation; no consideration of the changing of grid thickenss with the tides (vvl)
        strategy: loop through data, openening and closing model files as needed and storing model data
    """
    if len(data)>5000:
        pprint=True
        lendat=len(data)
    else:
        pprint= False
    if not preIndexed:
        data['k']=-1*np.ones((len(data))).astype(int)
    for ind, row in data.iterrows():
        if (pprint==True and ind%5000==0):
            print('progress: {}%'.format(ind/lendat*100))
        if ind==0: # special case for start of loop; load first files
            fid=dict()
            fend=dict()
            torig=dict()
            for ift in ftypes:
                fid,fend=_nextfile_bin(ift,row['dtUTC'],flist[ift],fid,fend,flist)
                if ift=='ops': # specially handle time origin for ops forcing files
                    torig[ift]=dt.datetime.strptime(fid[ftypes[0]].variables['time_counter'].time_origin,'%Y-%b-%d %H:%M:%S')
                else: # handle NEMO files time reference
                    if 'time_centered' in fid[ftypes[0]].variables.keys():
                        torig[ift]=dt.datetime.strptime(fid[ftypes[0]].variables['time_centered'].time_origin,'%Y-%m-%d %H:%M:%S')
                    else:
                        torig[ift]=dt.datetime.strptime(fid[ftypes[0]].variables['time_counter'].time_origin,'%Y-%m-%d %H:%M:%S')
        # loop through each file type to extract data from the appropriate time and location
        for ift in ftypes:
            if row['dtUTC']>=fend[ift]:
                fid,fend=_nextfile_bin(ift,row['dtUTC'],flist[ift],fid,fend,flist)
            # now read data
            # find time index
            if ift=='ops': # special handling for ops atm forcing files
                ih=_getTimeInd_bin_ops(row['dtUTC'],fid[ift],torig[ift])
            else: # NEMO files
                try:
                    if 'time_centered_bounds' in fid[ift].variables.keys(): # no problem! 
                        ih=_getTimeInd_bin(row['dtUTC'],fid[ift],torig[ift])
                    else: # annoying!
                        hpf=(flist[ift]['t_n'][0]-flist[ift]['t_0'][0]).total_seconds()/3600 #hours per file
                        ih=_getTimeInd_bin(row['dtUTC'],fid[ift],torig[ift],hpf=hpf)
                except:
                    print('fend',fend)
                    print('flist[ift]',flist[ift]['paths'][0])
                    print(row['dtUTC'],ift,torig[ift])
                    tlist=fid[ift].variables['time_centered_bounds'][:,:]
                    for el in tlist:
                        print(el)
                    print((row['dtUTC']-torig[ift]).total_seconds())
                    print(tlist[-1,1])
                    raise
            # find depth index if vars are 3d
            if sdim==3:
                if preIndexed:
                    ik=row['k']
                    # assign values for each var assoc with ift
                    if (not np.isnan(ik)) and (gridmask[0,ik,row['j'],row['i']]==1):
                        for ivar in filemap_r[ift]:
                            try:
                                data.loc[ind,['mod_'+ivar]]=fid[ift].variables[ivar][ih,ik,row['j'],row['i']]
                            except:
                                print(ind,ift,ih,ik,row['j'],row['i'])
                                raise
                else:
                    if len(set(fid[ift].variables.keys()).intersection(set(('deptht_bounds','depthu_bounds','depthv_bounds'))))>0: # no problem! 
                        ik=_getZInd_bin(row['Z'],fid[ift],maskName=maskName)
                    else: #workaround for missing variables in postprocessed files
                        ik=_getZInd_bin(row['Z'],fid[ift],boundsFlag=True,maskName=maskName)
                    # assign values for each var assoc with ift
                    if (not np.isnan(ik)) and (gridmask[0,ik,row['j'],row['i']]==1):
                        data.loc[ind,['k']]=int(ik)
                        for ivar in filemap_r[ift]:
                            data.loc[ind,['mod_'+ivar]]=fid[ift].variables[ivar][ih,ik,row['j'],row['i']]
            elif sdim==2:
                # assign values for each var assoc with ift
                if (gridmask[0,0,row['j'],row['i']]==1):
                    for ivar in filemap_r[ift]:
                        data.loc[ind,['mod_'+ivar]]=fid[ift].variables[ivar][ih,row['j'],row['i']]
            else:
                raise('invalid sdim')
    return data

def _vvlBin(data,flist,ftypes,filemap,filemap_r,tmask,fdict,e3tvar):
    """ vertical matching of model output to data by bin method but considering vvl change in
        grid thickness with tides
    """
    data['k']=-1*np.ones((len(data))).astype(int)
    ifte3t=filemap[e3tvar]
    pere3t=fdict[ifte3t]
    pers=np.unique([i for i in fdict.values()])
    # reverse fdict
    fdict_r=dict()
    for iii in pers:
        fdict_r[iii]=list()
    for ikey in fdict:
        fdict_r[fdict[ikey]].append(ikey)
    # so far we have only allowed for 1 file duration for all input files, so all indices equivalent
    # also, we are only dealing with data saved at same interval as e3t
    test=fdict_r.copy()
    test.pop(pere3t)
    if len(test)>0: # loop through and print eliminated variables
        print('Warning: variables excluded because save interval mismatched with e3t:')
        for aa in test:
            for bb in fdict_r[aa]:
                print(filemap_r[bb])

    data['indf'] = [int(flist[ifte3t].loc[(aa>=flist[ifte3t].t_0)&(aa<flist[ifte3t].t_n)].index[0])
                        for aa in data['dtUTC']]
    t2=[flist[ifte3t].loc[aa,['t_0']].values[0] for aa in data['indf'].values]
    data['ih']=[int(np.floor((aa-bb).total_seconds()/(pere3t*3600))) for aa,bb in zip(data['dtUTC'],t2)]
    # now get appropriate e3t for each set of data points:
    for indf,grp0 in data.groupby(['indf']):
        with nc.Dataset(flist[ifte3t].loc[indf,['paths']].values[0]) as fe3t:
            ff=dict()
            for ift in fdict_r[pere3t]:
                ff[ift]=nc.Dataset(flist[ift].loc[indf,['paths']].values[0])
            for (ih,jj,ii),grp1 in grp0.groupby(['ih','j','i']):
                e3t=fe3t.variables[e3tvar][ih,:,jj,ii][tmask[0,:,jj,ii]==1]
                zl=np.zeros((len(e3t),2))
                zl[1:,0]=np.cumsum(e3t[:-1])
                zl[:,1]=np.cumsum(e3t)
                ztar=grp1['Z'].values
                for ift in fdict_r[pere3t]:
                    for iz, iind in zip(ztar,grp1.index):
                        ik=[iii for iii,hhh in enumerate(zl) if hhh[1]>iz][0] # return first index where latter endpoint is larger
                        # assign values for each var assoc with ift
                        if (not np.isnan(ik)) and (tmask[0,ik,jj,ii]==1):
                            data.loc[iind,['k']]=int(ik)
                            for ivar in filemap_r[ift]:
                                data.loc[iind,['mod_'+ivar]]=ff[ift].variables[ivar][ih,ik,jj,ii]
            for ift in fdict_r[pere3t]:
                ff[ift].close()
    return data

def _interpvvlZ(data,flist,ftypes,filemap,filemap_r,tmask,fdict,e3tvar):
    """ vertical interpolation of model output to observation depths considering vvl change in
        grid thickness with tides
    """
    ifte3t=filemap.pop(e3tvar)
    pere3t=fdict.pop(ifte3t)
    pers=np.unique([i for i in fdict.values()])
    # reverse fdict
    fdict_r=dict()
    for iii in pers:
        fdict_r[iii]=list()
    for ikey in fdict:
        fdict_r[fdict[ikey]].append(ikey)
    # so far we have only allowed for 1 file duration for all input files, so all indices equivalent
    # also, we are only dealing with data saved at same interval as e3t
    test=fdict_r.copy()
    test.pop(pere3t)
    if len(test)>0: # loop through and print eliminated variables
        print('Warning: variables excluded because save interval mismatched with e3t:')
        for aa in test:
            for bb in fdict_r[aa]:
                print(filemap_r[bb])

    data['indf'] = [int(flist[ifte3t].loc[(aa>=flist[ifte3t].t_0)&(aa<flist[ifte3t].t_n)].index[0])
                        for aa in data['dtUTC']]
    t2=[flist[ifte3t].loc[aa,['t_0']].values[0] for aa in data['indf'].values]
    data['ih']=[int(np.floor((aa-bb).total_seconds()/(pere3t*3600))) for aa,bb in zip(data['dtUTC'],t2)]
    # now get appropriate e3t for each set of data points:
    for indf,grp0 in data.groupby(['indf']):
        with nc.Dataset(flist[ifte3t].loc[indf,['paths']].values[0]) as fe3t:
            ff=dict()
            for ift in fdict_r[pere3t]:
                ff[ift]=nc.Dataset(flist[ift].loc[indf,['paths']].values[0])
            for (ih,jj,ii),grp1 in grp0.groupby(['ih','j','i']):
                e3t=fe3t.variables[e3tvar][ih,:,jj,ii][tmask[0,:,jj,ii]==1]
                zs=np.cumsum(e3t)-.5*e3t
                ztar=grp1['Z'].values
                for ift in fdict_r[pere3t]:
                    for ivar in filemap_r[ift]:
                        vals=ff[ift].variables[ivar][ih,:,jj,ii][tmask[0,:,jj,ii]==1]
                        data.loc[grp1.index,['mod_'+ivar]]=np.where(ztar<np.sum(e3t),np.interp(ztar,zs,vals),np.nan)
            for ift in fdict_r[pere3t]:
                ff[ift].close()
    return data

def _ferrymatch(data,flist,ftypes,filemap_r,gridmask,fdict):
    """ matching of model output to top grid cells (for ferry underway measurements)
    """
    # loop through data, openening and closing model files as needed and storing model data
    # extract average of upper 3 model levels (approx 3 m)
    # set file name and hour
    if len(data)>5000:
        pprint=True
        lendat=len(data)
    else:
        pprint= False
    for ift in ftypes:
        data['indf_'+ift] = [int(flist[ift].loc[(aa>=flist[ift].t_0)&(aa<flist[ift].t_n)].index[0]) for aa in data['dtUTC']]
        t2=[flist[ift].loc[aa,['t_0']].values[0] for aa in data['indf_'+ift].values]
        data['ih_'+ift]=[int(np.floor((aa-bb).total_seconds()/(fdict[ift]*3600))) for aa,bb in zip(data['dtUTC'],t2)]
        print('done index '+ift,dt.datetime.now())
        indflast=-1
        for ind, row in data.iterrows():
            if (pprint==True and ind%np.round(lendat/10)==0):
                print(ift,'progress: {}%'.format(ind/lendat*100))
            if not row['indf_'+ift]==indflast:
                if not indflast==-1:
                    fid.close()
                fid=nc.Dataset(flist[ift].loc[row['indf_'+ift],['paths']].values[0])
                indflast=row['indf_'+ift]
            for ivar in filemap_r[ift]:
                data.loc[ind,['mod_'+ivar]] = fid.variables[ivar][row['ih_'+ift], 0, row['j'], row['i']]
    return data

def _nextfile_bin(ift,idt,ifind,fid,fend,flist): # to do: replace flist[ift] with ifind and get rid of flist argument
    """ close last file and open the next one"""
    if ift in fid.keys():
        fid[ift].close()
    frow=flist[ift].loc[(ifind.t_0<=idt)&(ifind.t_n>idt)]
    #print('idt:',idt)
    #print(frow)
    #print('switched files: ',frow['paths'].values[0])
    fid[ift]=nc.Dataset(frow['paths'].values[0])
    fend[ift]=frow['t_n'].values[0]
    return fid, fend

def _getTimeInd_bin(idt,ifid,torig,hpf=None):
    """ find time index for SalishSeaCast output interval including observation time """
    if 'time_centered_bounds' in ifid.variables.keys():
        tlist=ifid.variables['time_centered_bounds'][:,:]
        # return first index where latter endpoint is larger
        ih=[iii for iii,hhh in enumerate(tlist) if hhh[1]>(idt-torig).total_seconds()][0]
    else: # hacky fix because time_centered_bounds missing from post-processed daily files
        nt=len(ifid.variables['time_counter'][:])
        tlist=[ii+hpf/(nt*2)*3600 for ii in ifid.variables['time_counter'][:]]
        ih=[iii for iii,hhh in enumerate(tlist) if hhh>(idt-torig).total_seconds()][0]
    return ih

def _getTimeInd_bin_ops(idt,ifid,torig):
    """ find time index for ops file"""
    tlist=ifid.variables['time_counter'][:].data
    tinterval=ifid.variables['time_counter'].time_step
    #ih=[iii for iii,hhh in enumerate(tlist) if (hhh+tinterval/2)>(idt-torig).total_seconds()][0]
    ## NEMO is reading in files as if they were on the half hour so do the same:
    #           return first index where latter endpoint is larger
    ih=[iii for iii,hhh in enumerate(tlist) if (hhh+tinterval)>(idt-torig).total_seconds()][0]
    return ih

def _getZInd_bin(idt,ifid=None,boundsFlag=False,maskName='tmask'):
    """ get vertical index of cell containing observation depth """
    if boundsFlag==True:
        if maskName=='tmask':
            with nc.Dataset('/results/SalishSea/nowcast-green.201812/01jan16/SalishSea_1h_20160101_20160101_ptrc_T.nc') as ftemp:
                tlist=ftemp.variables['deptht_bounds'][:,:]
        elif maskName=='umask':
            with nc.Dataset('/results/SalishSea/nowcast-green.201812/01jan16/SalishSea_1h_20160101_20160101_grid_U.nc') as ftemp:
                tlist=ftemp.variables['depthu_bounds'][:,:]
        elif maskName=='vmask':
            with nc.Dataset('/results/SalishSea/nowcast-green.201812/01jan16/SalishSea_1h_20160101_20160101_grid_V.nc') as ftemp:
                tlist=ftemp.variables['depthv_bounds'][:,:]
        else:
            raise('choice not coded')
    else:
        dboundvar={'tmask':'deptht_bounds','umask':'depthu_bounds','vmask':'depthv_bounds'}
        tlist=ifid.variables[dboundvar[maskName]][:,:]
    if idt<=np.max(tlist):
        ih=[iii for iii,hhh in enumerate(tlist) if hhh[1]>idt][0] # return first index where latter endpoint is larger
    else:
        ih=np.nan
    return ih

def index_model_files(start,end,basedir,nam_fmt,flen,ftype=None,tres=1):
    """
    See inputs for matchData above.
    outputs pandas dataframe containing columns 'paths','t_0', and 't_1'
    where paths are all the model output files of a given type in the time interval (start,end)
    with end not included
    """
    if ftype not in ('ptrc_T','grid_T','grid_W','grid_U','grid_V','dia1_T','carp_T','None',None):
        print('ftype={}, are you sure? (if yes, add to list)'.format(ftype))
    if tres==24:
        ftres='1d'
    else:
        ftres=str(int(tres))+'h'
    ffmt='%Y%m%d'
    dfmt='%d%b%y'
    wfmt='y%Ym%md%d'
    if nam_fmt=='nowcast':
        stencil='{0}/SalishSea_'+ftres+'_{1}_{2}_'+ftype+'.nc'
    elif nam_fmt=='long':
       stencil='**/SalishSea_'+ftres+'*'+ftype+'_{1}-{2}.nc'
    elif nam_fmt=='sockeye':
       stencil=f'*/SalishSea_{ftres}*{ftype}_{{1}}-{{2}}.nc'
    elif nam_fmt == 'optimum':
       stencil = f'???????/SalishSea_{ftres}*{ftype}_{{1}}-{{2}}.nc'
    elif nam_fmt=='wind':
       stencil='ops_{3}.nc'
    elif nam_fmt=='ops':
       stencil='ops_{3}.nc'
    elif nam_fmt=='gemlam':
       stencil='gemlam_{3}.nc'
    elif nam_fmt=='forcing': # use ftype as prefix
       stencil=ftype+'_{3}.nc'
    else:
        raise Exception('nam_fmt '+nam_fmt+' is not defined')
    #Note fix: to avoid errors if hour and second included with start and end time, strip them!
    iits=dt.datetime(start.year,start.month,start.day)
    iite=iits+dt.timedelta(days=(flen-1))
    # check if start is a file start date and if not, try to identify the file including it
    # (in case start date is in the middle of a multi-day file)
    nday=0
    while True:
        try:
            ipathstr=os.path.join(basedir,stencil.format(iits.strftime(dfmt).lower(),
                    iits.strftime(ffmt),iite.strftime(ffmt),iits.strftime(wfmt)))
            iifstr=glob.glob(ipathstr,recursive=True)[0]
            if nday>0:
                print('first file starts on ',iits)
            break # file has been found
        except IndexError:
            nday=nday+1
            if nday==flen:
                iits_str=iits.strftime('%Y %b %d')
                start_str=start.strftime('%Y %b %d')
                if flen==1:
                    exc_msg= (f'\nFile not found:\n{ipathstr}\n'
                             f'Check that results directory is accessible and the start date entered is included in the run. \n')
                else:
                    exc_msg= (f'\nDays per output file is set to {flen}. \n'
                             f'No file found with start date in range {iits_str} to {start_str} \n'
                             f'of form {ipathstr}\n'
                             f'Check that results directory is accessible and the start date entered is included in run. \n')
                raise Exception(exc_msg) # file has not been found
            iits=start-dt.timedelta(days=nday)
            iite=iits+dt.timedelta(days=(flen-1))
    ind=0
    inds=list()
    paths=list()
    t_0=list()
    t_n=list()
    while iits<end:
        iite=iits+dt.timedelta(days=(flen-1))
        iitn=iits+dt.timedelta(days=flen)
        try:
            iifstr=glob.glob(os.path.join(basedir,stencil.format(iits.strftime(dfmt).lower(),
                    iits.strftime(ffmt),iite.strftime(ffmt),iits.strftime(wfmt))),recursive=True)[0]
        except IndexError:
            raise Exception('file does not exist:  '+os.path.join(basedir,stencil.format(iits.strftime(dfmt).lower(),
                iits.strftime(ffmt),iite.strftime(ffmt),iits.strftime(wfmt))))
        inds.append(ind)
        paths.append(iifstr)
        t_0.append(iits)
        t_n.append(iitn)
        iits=iitn
        ind=ind+1
    return pd.DataFrame(data=np.swapaxes([paths,t_0,t_n],0,1),index=inds,columns=['paths','t_0','t_n'])

def index_model_files_flex(basedir,ftype,freq='1d',nam_fmt='nowcast',start=None,end=None):
    """
    See inputs for matchData above.
    outputs pandas dataframe containing columns 'paths','t_0', and 't_1'
    Requires file naming convention with start date and end date as YYYYMMDD_YYYYMMDD
    lists all files of a particular filetype and output frequency from a given results file structure
    useful if there are missing files
    If start and end are provided, date start is included but end is not.
    """
    paths=glob.glob(os.path.join(basedir,'???????','*'+ftype+'*')) # assume if there are subdirectories, they must have nowcast yymmmdd format
    if len(paths)==0: # in case of no subdirectories
        paths=glob.glob(os.path.join(basedir,'*'+ftype+'*'))
    paths=[el for el in paths if re.search(freq,el)] # restrict to files with desired output frequency
    t_0=list()
    t_n=list()
    for ifl in paths:
        if nam_fmt=='nowcast':
            dates=re.findall('\d{8}',re.search('\d{8}_\d{8}',ifl)[0])
        elif nam_fmt=='long':
            dates=re.findall('\d{8}',re.search('\d{8}-\d{8}',ifl)[0])
        else:
            raise Exception('option not implemented: nam_fmt=',nam_fmt)
        t_0.append(dt.datetime.strptime(dates[0],'%Y%m%d'))
        t_n.append(dt.datetime.strptime(dates[1],'%Y%m%d')+dt.timedelta(days=1))
    idf=pd.DataFrame(data=np.swapaxes([paths,t_0,t_n],0,1),index=range(0,len(paths)),columns=['paths','t_0','t_n'])
    if start is not None and end is not None:
        ilocs=(idf['t_n']>start)&(idf['t_0']<end)
        idf=idf.loc[ilocs,:].copy(deep=True)
    idf=idf.sort_values(['t_0']).reset_index(drop=True)
    return idf


def loadDFOCTD(basedir='/ocean/shared/SalishSeaCastData/DFO/CTD/', dbname='DFO_CTD.sqlite',
        datelims=()):
    """
    load DFO CTD data stored in SQLite database (exclude most points outside Salish Sea)
    basedir is location of database
    dbname is database name
    datelims, if provided, loads only data between first and second datetime in tuple
    """
    try:
        from sqlalchemy import create_engine, case
        from sqlalchemy.orm import create_session
        from sqlalchemy.ext.automap import automap_base
        from sqlalchemy.sql import and_, or_, not_, func
    except ImportError:
        raise ImportError('You need to install sqlalchemy in your environment to use this function.')

    # definitions
    # if db does not exist, exit
    if not os.path.isfile(os.path.join(basedir, dbname)):
        raise Exception(f'ERROR: {dbname} does not exist in {basedir}')
    engine = create_engine('sqlite:///' + basedir + dbname, echo = False)
    Base = automap_base()
    # reflect the tables in salish.sqlite:
    Base.prepare(engine, reflect=True)
    # mapped classes have been created
    # existing tables:
    StationTBL=Base.classes.StationTBL
    ObsTBL=Base.classes.ObsTBL
    CalcsTBL=Base.classes.CalcsTBL
    session = create_session(bind = engine, autocommit = False, autoflush = True)
    SA=case([(CalcsTBL.Salinity_T0_C0_SA!=None, CalcsTBL.Salinity_T0_C0_SA)], else_=
             case([(CalcsTBL.Salinity_T1_C1_SA!=None, CalcsTBL.Salinity_T1_C1_SA)], else_=
             case([(CalcsTBL.Salinity_SA!=None, CalcsTBL.Salinity_SA)], else_= None)))
    CT=case([(CalcsTBL.Temperature_Primary_CT!=None, CalcsTBL.Temperature_Primary_CT)], else_=
             case([(CalcsTBL.Temperature_Secondary_CT!=None, CalcsTBL.Temperature_Secondary_CT)], else_=CalcsTBL.Temperature_CT))
    ZD=case([(ObsTBL.Depth!=None,ObsTBL.Depth)], else_= CalcsTBL.Z)
    FL=case([(ObsTBL.Fluorescence_URU_Seapoint!=None,ObsTBL.Fluorescence_URU_Seapoint)], else_= ObsTBL.Fluorescence_URU_Wetlabs)
    if len(datelims)<2:
        qry=session.query(StationTBL.StartYear.label('Year'),StationTBL.StartMonth.label('Month'),
                      StationTBL.StartDay.label('Day'),StationTBL.StartHour.label('Hour'),
                      StationTBL.Lat,StationTBL.Lon,ZD.label('Z'),SA.label('SA'),CT.label('CT'),FL.label('Fluor'),
                      ObsTBL.Oxygen_Dissolved_SBE.label('DO_mLL'),ObsTBL.Oxygen_Dissolved_SBE_1.label('DO_umolkg')).\
                select_from(StationTBL).join(ObsTBL,ObsTBL.StationTBLID==StationTBL.ID).\
                join(CalcsTBL,CalcsTBL.ObsTBLID==ObsTBL.ID).filter(and_(StationTBL.Lat>47-3/2.5*(StationTBL.Lon+123.5),
                                                                    StationTBL.Lat<47-3/2.5*(StationTBL.Lon+121),
                                                                    StationTBL.Include==True,ObsTBL.Include==True,CalcsTBL.Include==True))
    else:
        start_y=datelims[0].year
        start_m=datelims[0].month
        start_d=datelims[0].day
        end_y=datelims[1].year
        end_m=datelims[1].month
        end_d=datelims[1].day
        qry=session.query(StationTBL.StartYear.label('Year'),StationTBL.StartMonth.label('Month'),
                      StationTBL.StartDay.label('Day'),StationTBL.StartHour.label('Hour'),
                      StationTBL.Lat,StationTBL.Lon,ZD.label('Z'),SA.label('SA'),CT.label('CT'),FL.label('Fluor').\
                      ObsTBL.Oxygen_Dissolved_SBE.label('DO_mLL'),ObsTBL.Oxygen_Dissolved_SBE_1.label('DO_umolkg')).\
                select_from(StationTBL).join(ObsTBL,ObsTBL.StationTBLID==StationTBL.ID).\
                join(CalcsTBL,CalcsTBL.ObsTBLID==ObsTBL.ID).filter(and_(or_(StationTBL.StartYear>start_y,
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth>start_m),
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth==start_m, StationTBL.StartDay>=start_d)),
                                                                        or_(StationTBL.StartYear<end_y,
                                                                         and_(StationTBL.StartYear==end_y,StationTBL.StartMonth<end_m),
                                                                         and_(StationTBL.StartYear==end_y,StationTBL.StartMonth==end_m, StationTBL.StartDay<end_d)),
                                                                    StationTBL.Lat>47-3/2.5*(StationTBL.Lon+123.5),
                                                                    StationTBL.Lat<47-3/2.5*(StationTBL.Lon+121),
                                                                    StationTBL.Include==True,ObsTBL.Include==True,CalcsTBL.Include==True))
    df1=pd.read_sql_query(qry.statement, engine)
    df1['dtUTC']=[dt.datetime(int(y),int(m),int(d))+dt.timedelta(hours=h) for y,m,d,h in zip(df1['Year'],df1['Month'],df1['Day'],df1['Hour'])]
    session.close()
    engine.dispose()
    return df1

def loadDFO(basedir='/ocean/eolson/MEOPAR/obs/DFOOPDB/', dbname='DFO_OcProfDB.sqlite',
        datelims=(),excludeSaanich=True):
    """
    load DFO data stored in SQLite database
    basedir is location of database
    dbname is database name
    datelims, if provided, loads only data between first and second datetime in tuple
    """
    try:
        from sqlalchemy import create_engine, case
        from sqlalchemy.orm import create_session
        from sqlalchemy.ext.automap import automap_base
        from sqlalchemy.sql import and_, or_, not_, func
    except ImportError:
        raise ImportError('You need to install sqlalchemy in your environment to use this function.')
    # definitions
    # if db does not exist, exit
    if not os.path.isfile(os.path.join(basedir, dbname)):
        raise Exception('ERROR: {}.sqlite does not exist'.format(dbname))
    engine = create_engine('sqlite:///' + basedir + dbname, echo = False)
    Base = automap_base()
    # reflect the tables in salish.sqlite:
    Base.prepare(engine, reflect=True)
    # mapped classes have been created
    # existing tables:
    StationTBL=Base.classes.StationTBL
    ObsTBL=Base.classes.ObsTBL
    CalcsTBL=Base.classes.CalcsTBL
    session = create_session(bind = engine, autocommit = False, autoflush = True)
    SA=case([(CalcsTBL.Salinity_Bottle_SA!=None, CalcsTBL.Salinity_Bottle_SA)], else_=
             case([(CalcsTBL.Salinity_T0_C0_SA!=None, CalcsTBL.Salinity_T0_C0_SA)], else_=
             case([(CalcsTBL.Salinity_T1_C1_SA!=None, CalcsTBL.Salinity_T1_C1_SA)], else_=
             case([(CalcsTBL.Salinity_SA!=None, CalcsTBL.Salinity_SA)], else_=
             case([(CalcsTBL.Salinity__Unknown_SA!=None, CalcsTBL.Salinity__Unknown_SA)],
                  else_=CalcsTBL.Salinity__Pre1978_SA)
            ))))
    Tem=case([(ObsTBL.Temperature!=None, ObsTBL.Temperature)], else_=
             case([(ObsTBL.Temperature_Primary!=None, ObsTBL.Temperature_Primary)], else_=
             case([(ObsTBL.Temperature_Secondary!=None, ObsTBL.Temperature_Secondary)], else_=ObsTBL.Temperature_Reversing)))
    TemUnits=case([(ObsTBL.Temperature!=None, ObsTBL.Temperature_units)], else_=
             case([(ObsTBL.Temperature_Primary!=None, ObsTBL.Temperature_Primary_units)], else_=
             case([(ObsTBL.Temperature_Secondary!=None, ObsTBL.Temperature_Secondary_units)],
                  else_=ObsTBL.Temperature_Reversing_units)))
    TemFlag=ObsTBL.Quality_Flag_Temp
    CT=case([(CalcsTBL.Temperature_CT!=None, CalcsTBL.Temperature_CT)], else_=
         case([(CalcsTBL.Temperature_Primary_CT!=None, CalcsTBL.Temperature_Primary_CT)], else_=
         case([(CalcsTBL.Temperature_Secondary_CT!=None, CalcsTBL.Temperature_Secondary_CT)],
              else_=CalcsTBL.Temperature_Reversing_CT)
        ))

    if len(datelims)<2:
        qry=session.query(StationTBL.StartYear.label('Year'),StationTBL.StartMonth.label('Month'),
                      StationTBL.StartDay.label('Day'),StationTBL.StartHour.label('Hour'),
                      StationTBL.Lat,StationTBL.Lon,
                     ObsTBL.Pressure,ObsTBL.Depth,ObsTBL.Chlorophyll_Extracted,
                     ObsTBL.Chlorophyll_Extracted_units,ObsTBL.Nitrate_plus_Nitrite.label('N'),
                      ObsTBL.Silicate.label('Si'),ObsTBL.Silicate_units,SA.label('AbsSal'),CT.label('ConsT'),
                      ObsTBL.Oxygen_Dissolved,ObsTBL.Oxygen_Dissolved_units).\
                select_from(StationTBL).join(ObsTBL,ObsTBL.StationTBLID==StationTBL.ID).\
                join(CalcsTBL,CalcsTBL.ObsID==ObsTBL.ID).filter(and_(StationTBL.Lat>47-3/2.5*(StationTBL.Lon+123.5),
                                                                    StationTBL.Lat<47-3/2.5*(StationTBL.Lon+121)))
    else:
        start_y=datelims[0].year
        start_m=datelims[0].month
        start_d=datelims[0].day
        end_y=datelims[1].year
        end_m=datelims[1].month
        end_d=datelims[1].day
        qry=session.query(StationTBL.StartYear.label('Year'),StationTBL.StartMonth.label('Month'),
                      StationTBL.StartDay.label('Day'),StationTBL.StartHour.label('Hour'),
                      StationTBL.Lat,StationTBL.Lon,
                     ObsTBL.Pressure,ObsTBL.Depth,ObsTBL.Chlorophyll_Extracted,
                     ObsTBL.Chlorophyll_Extracted_units,ObsTBL.Nitrate_plus_Nitrite.label('N'),
                      ObsTBL.Silicate.label('Si'),ObsTBL.Silicate_units,SA.label('AbsSal'),CT.label('ConsT'),
                      ObsTBL.Oxygen_Dissolved,ObsTBL.Oxygen_Dissolved_units).\
                select_from(StationTBL).join(ObsTBL,ObsTBL.StationTBLID==StationTBL.ID).\
                join(CalcsTBL,CalcsTBL.ObsID==ObsTBL.ID).filter(and_(or_(StationTBL.StartYear>start_y,
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth>start_m),
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth==start_m, StationTBL.StartDay>=start_d)),
                                                                     or_(StationTBL.StartYear<end_y,
                                                                         and_(StationTBL.StartYear==end_y,StationTBL.StartMonth<end_m),
                                                                         and_(StationTBL.StartYear==end_y,StationTBL.StartMonth==end_m, StationTBL.StartDay<end_d)),
                                                                    StationTBL.Lat>47-3/2.5*(StationTBL.Lon+123.5),
                                                                    StationTBL.Lat<47-3/2.5*(StationTBL.Lon+121)))#,
                                                                    #not_(and_(StationTBL.Lat>48.77,StationTBL.Lat<49.27,
                                                                    #          StationTBL.Lon<-123.43))))
    if excludeSaanich:
        qry1=qry.filter(not_(and_(StationTBL.Lat>48.47,StationTBL.Lat<48.67,
                                              StationTBL.Lon>-123.6,StationTBL.Lon<-123.43)))
        df1=pd.read_sql_query(qry1.statement, engine)
    else:
        df1=pd.read_sql_query(qry.statement, engine)
    df1['Z']=np.where(df1['Depth']>=0,df1['Depth'],-1.0*gsw.z_from_p(p=df1['Pressure'].values,lat=df1['Lat'].values))
    df1['dtUTC']=[dt.datetime(int(y),int(m),int(d))+dt.timedelta(hours=h) for ind, (y,m,d,h) in df1.loc[:,['Year','Month','Day','Hour']].iterrows()]
    session.close()
    engine.dispose()
    return df1

def _lt0convert(arg):
    #  convert text '<0' to numeric zero since nutrient concentrations cannot be negative
    if arg=='<0':
        val=0.0
    else:
        val=pd.to_numeric(arg, errors='coerce',downcast=None)
    return float(val)

def loadPSF(datelims=(),loadChl=True,loadCTD=False):
    """ load PSF data from spreadsheets, optionally loading matched T and S data from nearest CTD casts """
    dfs=list()
    dfchls=list()
    if len(datelims)<2:
        datelims=(dt.datetime(2014,1,1),dt.datetime(2020,1,1))
    if loadCTD:
        ctddfs=dict()
    if datelims[0].year<2016:
        # load 2015
        f2015 = pd.read_excel('/ocean/eolson/MEOPAR/obs/PSFCitSci/All_Yrs_Nutrients_2018-01-31_EOEdit.xlsx',
                         sheet_name = '2015 N+P+Si',dtype={'date (dd/mm/yyyy)':str},engine=excelEngine)
        f2015=f2015.drop(f2015.loc[(f2015['lon']<-360)|(f2015['lon']>360)].index)
        f2015 = f2015.dropna(subset = ['date (dd/mm/yyyy)', 'Time (Local)', 'lat', 'lon', 'depth'], how='any')
        ds=f2015['date (dd/mm/yyyy)'].values
        ts=f2015['Time (Local)'].values
        dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime.strptime(ii,'%Y-%m-%d %H:%M:%S')+dt.timedelta(hours=jj.hour,minutes=jj.minute,seconds=jj.second)
            ).astimezone(pytz.utc).replace(tzinfo=None) for ii,jj in zip(ds,ts)]
        f2015['dtUTC']=dts
        f2015.rename(columns={'lat':'Lat','lon':'Lon','depth':'Z','station':'Station','no23':'NO23','po4':'PO4','si':'Si'},inplace=True)
        f2015.drop(['num','date (dd/mm/yyyy)','Time (Local)'],axis=1,inplace=True)
        f2015_g=f2015.groupby(['Station','Lat','Lon','dtUTC','Z'],as_index=False)
        f2015_m=f2015_g.mean()
        f2015=f2015_m.reindex()
        dfs.append(f2015)
        if loadChl:
            # load 2015 chl
            Chl2015=pd.read_csv('/ocean/eolson/MEOPAR/obs/PSFCitSci/Chla_2015PSFSalish_Sea_22.01.2018vers_8_CN_edits.csv',encoding='latin-1',
                                dtype={'Date sampled (mm/dd/yyyy)':str, 'Time of Day (Local)':str,
                                        'Latitude':str,'Longitude':str,'Chl a':float,'Phaeophytin':float,'Depth':float},parse_dates=False)
            degminlat=[ii.split('ç') for ii in Chl2015['Latitude'].values]
            Chl2015['Lat']=[float(ii[0])+float(ii[1])/60 for ii in degminlat]
            degminlon=[ii.split('ç') for ii in Chl2015['Longitude'].values]
            Chl2015['Lon']=[-1.0*(float(ii[0])+float(ii[1])/60) for ii in degminlon]
            Chl2015 = Chl2015.dropna(subset = ['Date sampled (mm/dd/yyyy)', 'Time of Day (Local)', 'Lat', 'Lon', 'Depth'], how='any')
            ds=Chl2015['Date sampled (mm/dd/yyyy)']
            ts=Chl2015['Time of Day (Local)']
            dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime.strptime(ii+'T'+jj,'%m/%d/%yT%I:%M:%S %p')).astimezone(pytz.utc).replace(tzinfo=None)
                 for ii,jj in zip(ds,ts)]
            Chl2015['dtUTC']=dts
            Chl2015['Z']=[float(ii) for ii in Chl2015['Depth']]
            Chl2015.drop(['Date sampled (mm/dd/yyyy)','Time of Day (Local)','Latitude','Longitude','Depth'],axis=1,inplace=True)
            Chl2015.rename(columns={'Chl a':'Chl','Phaeophytin':'Phaeo','Station Name':'Station'},inplace=True)
            Chl2015_g=Chl2015.groupby(['Station','Lat','Lon','dtUTC','Z'],as_index=False)
            Chl2015_m=Chl2015_g.mean()
            Chl2015=Chl2015_m.reindex()
            dfchls.append(Chl2015)
        if loadCTD:
            phys2015=pd.read_csv('/ocean/eolson/MEOPAR/obs/PSFCitSci/phys/CitSci2015_20180621.csv',skiprows=lambda x: x in [0,1,2,3,4,6],delimiter=',',
                    dtype={'Patrol': str,'ID':str,'station':str,'datetime':str,'latitude':float,'longitude':float},
                    converters={'pressure': lambda x: float(x),'depth': lambda x: float(x),'temperature': lambda x: float(x),
                                'conductivity': lambda x: float(x),'salinity': lambda x: float(x),
                                'o2SAT': lambda x: float(x),'o2uM':lambda x: float(x),'chl':lambda x: float(x)})
            ctddfs[2015]=dict()
            ctddfs[2015]['df']=phys2015
            ctddfs[2015]['dtlims']=(dt.datetime(2014,12,31),dt.datetime(2016,1,1))
    if (datelims[0].year<2017) and (datelims[1].year>2015):
        # load 2016
        f2016N = pd.read_excel('/ocean/eolson/MEOPAR/obs/PSFCitSci/All_Yrs_Nutrients_2018-01-31_EOEdit.xlsx',
                         sheet_name = '2016 N+P',dtype={'NO3+NO':str,'PO4':str},na_values=('nan','NaN','30..09'),
                         engine=excelEngine)
        f2016N = f2016N.drop(f2016N.keys()[11:], axis=1)
        f2016N['NO23']=[_lt0convert(ii) for ii in f2016N['NO3+NO']]
        f2016N['PO4_2']=[_lt0convert(ii) for ii in f2016N['PO4']]
        f2016N = f2016N.dropna(subset = ['Date (dd/mm/yyyy)', 'Time (Local)', 'Latitude', 'Longitude', 'Depth'], how='any')
        ds=f2016N['Date (dd/mm/yyyy)']
        ts=f2016N['Time (Local)']
        dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime(ii.year,ii.month,ii.day)+dt.timedelta(hours=jj.hour,minutes=jj.minute,seconds=jj.second)
            ).astimezone(pytz.utc).replace(tzinfo=None) for ii,jj in zip(ds,ts)]
        f2016N['dtUTC']=dts
        f2016N.drop(['Crew','Date (dd/mm/yyyy)','Time (Local)', 'Lat_reported',
               'Long_reported','PO4','NO3+NO'],axis=1,inplace=True)
        f2016N.rename(columns={'PO4_2':'PO4','Latitude':'Lat','Longitude':'Lon','Depth':'Z'},inplace=True)
        f2016N_g=f2016N.groupby(['Station','Lat','Lon','dtUTC','Z'],as_index=False)
        f2016N_m=f2016N_g.mean()
        f2016Si = pd.read_excel('/ocean/eolson/MEOPAR/obs/PSFCitSci/All_Yrs_Nutrients_2018-01-31_EOEdit.xlsx',
                                sheet_name = '2016 SiO2',engine=excelEngine)
        f2016Si = f2016Si.drop(f2016Si.keys()[9:], axis=1)
        f2016Si = f2016Si.dropna(subset = ['DDMMYYYY', 'Time (Local)', 'Latitude', 'Longitude', 'Depth'], how='any')
        ds=f2016Si['DDMMYYYY']
        ts=f2016Si['Time (Local)']
        dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime(ii.year,ii.month,ii.day)+dt.timedelta(hours=jj.hour,minutes=jj.minute,seconds=jj.second)
            ).astimezone(pytz.utc).replace(tzinfo=None) for ii,jj in zip(ds,ts)]
        f2016Si['dtUTC']=dts
        z=[0 if (iii=='S') else float(iii) for iii in f2016Si['Depth'].values]
        f2016Si['Z']=z
        f2016Si.rename(columns={'Latitude':'Lat','Longitude':'Lon','SiO2 µM':'Si','Site ID':'Station'},inplace=True)
        f2016Si.drop(['DDMMYYYY','Time (Local)', 'Lat_reported',
               'Long_reported','Depth'],axis=1,inplace=True)
        f2016Si_g=f2016Si.groupby(['Station','Lat','Lon','dtUTC','Z'],as_index=False)
        f2016Si_m=f2016Si_g.mean()
        f2016 = pd.merge(f2016N_m, f2016Si_m,  how='outer', left_on=['Station','Lat','Lon','dtUTC','Z'], right_on = ['Station','Lat','Lon','dtUTC','Z'])
        dfs.append(f2016)
        if loadChl:
            # load 2016 chl
            Chl2016Dat=pd.read_csv('/ocean/eolson/MEOPAR/obs/PSFCitSci/2016ChlorophyllChlData.csv')#,encoding='latin-1')
            Chl2016Sta=pd.read_csv('/ocean/eolson/MEOPAR/obs/PSFCitSci/2016ChlorophyllStationData.csv')
            Chl2016Sta.rename(columns={'DateCollected ':'DateCollected','Latitude':'Lat','Longitude':'Lon'},inplace=True)
            Chl2016Sta.dropna(subset = ['DateCollected', 'TimeCollected', 'Lat','Lon', 'Depth_m'], how='any',inplace=True)
            Chl2016Sta.drop_duplicates(inplace=True)
            Chl2016Dat.drop(Chl2016Dat.loc[Chl2016Dat.quality_flag>3].index,axis=0,inplace=True)
            Chl2016Dat.drop(['Chla_ugL','Phaeophytin_ugL','quality_flag','ShipBoat'],axis=1,inplace=True)
            Chl2016Dat.rename(columns={'MeanChla_ugL':'Chl','MeanPhaeophytin_ugL':'Phaeo'},inplace=True)
            Chl2016=pd.merge(Chl2016Sta,Chl2016Dat,how='inner', left_on=['DateCollected','Station','Depth_m'], right_on = ['DateCollected','Station','Depth_m'])
            Chl2016['Z']=[float(ii) for ii in Chl2016['Depth_m']]
            ds=Chl2016['DateCollected']
            ts=Chl2016['TimeCollected']
            dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime.strptime(ii+'T'+jj,'%m-%d-%YT%I:%M:%S %p')).astimezone(pytz.utc).replace(tzinfo=None)
                 for ii,jj in zip(ds,ts)]
            Chl2016['dtUTC']=dts
            Chl2016.drop(['DateCollected','TimeCollected','CV'],axis=1,inplace=True)
            dfchls.append(Chl2016)
        if loadCTD:
            phys2016=pd.read_csv('/ocean/eolson/MEOPAR/obs/PSFCitSci/phys/CitSci2016_20180621.csv',skiprows=lambda x: x in [0,1,2,3,4,5,6,7,9],delimiter=',',
                    dtype={'Patrol': str,'ID':str,'station':str,'datetime':str,'latitude':float,'longitude':float},
                    converters={'pressure': lambda x: float(x),'depth': lambda x: float(x),'temperature': lambda x: float(x),
                                'conductivity': lambda x: float(x),'salinity': lambda x: float(x),
                                'o2SAT': lambda x: float(x),'o2uM':lambda x: float(x),'chl':lambda x: float(x)})
            ctddfs[2016]=dict()
            ctddfs[2016]['df']=phys2016
            ctddfs[2016]['dtlims']=(dt.datetime(2015,12,31),dt.datetime(2017,1,1))
    if (datelims[1].year>2016):
        # load 2017
        f2017 = pd.read_excel('/ocean/eolson/MEOPAR/obs/PSFCitSci/All_Yrs_Nutrients_2018-01-31_EOEdit.xlsx',
                         sheet_name = '2017 N+P+Si',skiprows=3,dtype={'Date (dd/mm/yyyy)':dt.date,'Time (Local)':dt.time,
                                                                      'NO3+NO':str,'PO4':str,'Si':str},engine=excelEngine)
        f2017['NO23']=[_lt0convert(ii) for ii in f2017['NO3+NO']]
        f2017['PO4_2']=[_lt0convert(ii) for ii in f2017['PO4']]
        f2017['Si_2']=[_lt0convert(ii) for ii in f2017['Si']]
        degminlat=[ii.split('°') for ii in f2017['Latitude'].values]
        f2017['Lat']=[float(ii[0])+float(ii[1])/60 for ii in degminlat]
        degminlon=[ii.split('°') for ii in f2017['Longitude'].values]
        f2017['Lon']=[-1.0*(float(ii[0])+float(ii[1])/60) for ii in degminlon]
        f2017 = f2017.dropna(subset = ['Date (dd/mm/yyyy)', 'Time (Local)', 'Lat', 'Lon', 'Depth'], how='any')
        ds=f2017['Date (dd/mm/yyyy)']
        ts=f2017['Time (Local)']
        dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime(ii.year,ii.month,ii.day)+dt.timedelta(hours=jj.hour,minutes=jj.minute,seconds=jj.second)
            ).astimezone(pytz.utc).replace(tzinfo=None) for ii,jj in zip(ds,ts)]
        f2017['dtUTC']=dts
        f2017.drop(['Crew','Date (dd/mm/yyyy)','Time (Local)','Comments','Latitude','Longitude','NO3+NO'],axis=1,inplace=True)
        f2017.rename(columns={'Depth':'Z','PO4_2':'PO4','Si_2':'Si'},inplace=True)
        f2017_g=f2017.groupby(['Station','Lat','Lon','dtUTC','Z'],as_index=False)
        f2017_m=f2017_g.mean()
        f2017=f2017_m.reindex()
        dfs.append(f2017)
        if loadChl:
            # load 2017 chl
            Chl2017=pd.read_excel('/ocean/eolson/MEOPAR/obs/PSFCitSci/PSF 2017 Chla_Data_Final_v-January 22-2018_CN_edits.xlsx',
                                  sheet_name='avg-mean-cv%',skiprows=15,usecols=[1,3,4,5,7,9,11],
                                  names=['Date','Station','Time','Z0','Chl','Qflag','Phaeo'],engine=excelEngine)
            Chl2017.dropna(subset=['Station','Date','Time','Z0'],how='any',inplace=True)
            Chl2017.dropna(subset=['Chl','Phaeo'],how='all',inplace=True)
            Chl2017.drop(Chl2017.loc[Chl2017.Qflag>3].index,axis=0,inplace=True)
            ds=Chl2017['Date']
            ts=Chl2017['Time']
            dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime(ii.year,ii.month,ii.day)+dt.timedelta(hours=jj.hour,minutes=jj.minute,seconds=jj.second)).astimezone(pytz.utc).replace(tzinfo=None)
                for ii,jj in zip(ds,ts)]
            Chl2017['dtUTC']=dts
            staMap2017=f2017.loc[:,['Station','Lat','Lon']].copy(deep=True)
            staMap2017.drop_duplicates(inplace=True)
            Chl2017=pd.merge(Chl2017,staMap2017,how='inner', left_on=['Station'], right_on = ['Station'])
            Chl2017['Z']=[float(ii) for ii in Chl2017['Z0']]
            Chl2017.drop(['Qflag','Date','Z0','Time'],axis=1,inplace=True)
            dfchls.append(Chl2017)
        if loadCTD:
            phys2017=pd.read_csv('/ocean/eolson/MEOPAR/obs/PSFCitSci/phys/CitSci2017_20180621.csv',skiprows=lambda x: x in [0,1,2,3,4,5,7],delimiter=',',
                    dtype={'Patrol': str,'ID':str,'station':str,'datetime':str,'latitude':float,'longitude':float},
                    converters={'pressure': lambda x: float(x),'depth': lambda x: float(x),'temperature': lambda x: float(x),
                                'conductivity': lambda x: float(x),'salinity': lambda x: float(x),
                                'o2SAT': lambda x: float(x),'o2uM':lambda x: float(x),'chl':lambda x: float(x)})
            ctddfs[2017]=dict()
            ctddfs[2017]['df']=phys2017
            ctddfs[2017]['dtlims']=(dt.datetime(2016,12,31),dt.datetime(2018,1,1))
    if len(dfs)>1:
        df=pd.concat(dfs,ignore_index=True,sort=True)
        if loadChl:
            dfChl=pd.concat(dfchls, ignore_index=True,sort=True)
    else:
        df=dfs[0]
        if loadChl:
            dfChl=dfchls[0]
    if loadChl:
        df_a=pd.merge(df, dfChl,  how='outer', left_on=['Station','Lat','Lon','dtUTC','Z'], right_on = ['Station','Lat','Lon','dtUTC','Z'])
        df=df_a
    # set surface sample to more likely value of 0.55 m to aid matching with CTD data
    # extra 0.01 is to make np.round round up to 1 so that CTD data can match
    df.loc[df.Z==0,['Z']]=0.51
    df=df.loc[(df.dtUTC>=datelims[0])&(df.dtUTC<datelims[1])].copy(deep=True)
    if loadCTD:
        df1=df.copy(deep=True)
        for ik in ctddfs.keys():
            idf=ctddfs[ik]['df']
            dtsP=[dt.datetime.strptime(ii,'%d/%m/%Y %H:%M:%S') for ii in idf['datetime'].values]
            tPacP=utc_to_pac(dtsP)
            PacDayP=[dt.datetime(ii.year,ii.month,ii.day) for ii in tPacP]
            idf['tPacPhys']=tPacP
            idf['PacDay']=PacDayP
            idf['dtUTCPhys']=dtsP
            idf['StaTrim']=[ii.replace('-','') for ii in idf['station']]
            idf['HrsPast']=[(ii-dt.datetime(2014,1,1)).total_seconds()/3600 for ii in dtsP]
            idf['CT']=[gsw.CT_from_t(SA,t,p) for SA, t, p, in zip(idf['salinity'],idf['temperature'],idf['pressure'])]
        tPac=utc_to_pac(df['dtUTC'])
        PacDay=[dt.datetime(ii.year,ii.month,ii.day) for ii in tPac]
        df1['tPac']=tPac
        df1['PacDay']=PacDay
        df1['StaTrim']=[ii.replace('-','') for ii in df['Station']]
        df1['HrsPast']=[(ii-dt.datetime(2014,1,1)).total_seconds()/3600 for ii in df['dtUTC']]
        df['SA']=np.nan
        df['CT']=np.nan
        df['pLat']=np.nan
        df['pLon']=np.nan
        df['tdiffH']=np.nan
        for ik in ctddfs.keys():
            jdf=ctddfs[ik]['df']
            dtlims=ctddfs[ik]['dtlims']
            for i, row in df1.loc[(df1['dtUTC']>dtlims[0])&(df1['dtUTC']<dtlims[1])].iterrows():
                idf=jdf.loc[(jdf.StaTrim==row['StaTrim'])&(jdf.depth==np.round(row['Z']))&(np.abs(jdf.HrsPast-row['HrsPast'])<1.0)\
                                 &(np.abs(jdf.latitude-row['Lat'])<0.05)&(np.abs(jdf.longitude-row['Lon'])<0.05)]
                if len(idf)>0:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        sal=np.nanmean(idf['salinity'].values)
                        tem=np.nanmean(idf['CT'].values)
                        lat=np.nanmean(idf['latitude'].values)
                        lon=np.nanmean(idf['longitude'].values)
                    tdelta=np.nanmean([np.abs((ii-row['dtUTC']).total_seconds()/3600) for ii in idf['dtUTCPhys']])
                    df.at[i,'SA']=sal
                    df.at[i,'CT']=tem
                    df.at[i,'pLat']=lat
                    df.at[i,'pLon']=lon
                    df.at[i,'tdiffH']=tdelta
    return df

def loadPSFCTD(datelims=(),pathbase='/ocean/eolson/MEOPAR/obs/PSFCitSci/phys'):
    """ load PSF CTD data only """
    if len(datelims)<2:
        datelims=(dt.datetime(2014,1,1),dt.datetime(2020,1,1))
    ctddfs=list()
    if datelims[0].year<2016:
        # load 2015
        phys2015=pd.read_csv(os.path.join(pathbase,'CitSci2015_20180621.csv'),skiprows=lambda x: x in [0,1,2,3,4,6],delimiter=',',
                dtype={'Patrol': str,'ID':str,'station':str,'datetime':str,'latitude':float,'longitude':float},
                converters={'pressure': lambda x: float(x),'depth': lambda x: float(x),'temperature': lambda x: float(x),
                            'conductivity': lambda x: float(x),'salinity': lambda x: float(x),
                            'o2SAT': lambda x: float(x),'o2uM':lambda x: float(x),'chl':lambda x: float(x)})
        ctddfs.append(phys2015)
        print(np.min(phys2015['salinity']),np.max(phys2015['salinity']))
    if (datelims[0].year<2017) and (datelims[1].year>2015):
        # load 2016
        phys2016=pd.read_csv(os.path.join(pathbase,'CitSci2016_20180621.csv'),skiprows=lambda x: x in [0,1,2,3,4,5,6,7,9],delimiter=',',
                dtype={'Patrol': str,'ID':str,'station':str,'datetime':str,'latitude':float,'longitude':float},
                converters={'pressure': lambda x: float(x),'depth': lambda x: float(x),'temperature': lambda x: float(x),
                            'conductivity': lambda x: float(x),'salinity': lambda x: float(x),
                            'o2SAT': lambda x: float(x),'o2uM':lambda x: float(x),'chl':lambda x: float(x)})
        ctddfs.append(phys2016)
        print(np.min(phys2016['salinity']),np.max(phys2016['salinity']))
    if (datelims[1].year>2016):
        # load 2017
        phys2017=pd.read_csv(os.path.join(pathbase,'CitSci2017_20180621.csv'),skiprows=lambda x: x in [0,1,2,3,4,5,7],delimiter=',',
                dtype={'Patrol': str,'ID':str,'station':str,'datetime':str,'latitude':float,'longitude':float},
                converters={'pressure': lambda x: float(x),'depth': lambda x: float(x),'temperature': lambda x: float(x),
                            'conductivity': lambda x: float(x),'salinity': lambda x: float(x),
                            'o2SAT': lambda x: float(x),'o2uM':lambda x: float(x),'chl':lambda x: float(x)})
        ctddfs.append(phys2017)
        print(np.min(phys2017['salinity']),np.max(phys2017['salinity']))
    # note: csv files report salnity in TEOS-10 g/kg
    df=pd.concat(ctddfs,ignore_index=True,sort=True)
    df['dtUTC']=[dt.datetime.strptime(ii,'%d/%m/%Y %H:%M:%S') for ii in df['datetime'].values]
    df['CT']=[gsw.CT_from_t(SA,t,p) for SA, t, p, in zip(df['salinity'],df['temperature'],df['pressure'])]
    df.rename(columns={'salinity':'SA','latitude':'Lat','longitude':'Lon','depth':'Z'},inplace=True)
    return df

def loadHakai(datelims=(),loadCTD=False):
    """ load data from Hakai sampling program from spreadsheets"""
    if len(datelims)<2:
        datelims=(dt.datetime(1900,1,1),dt.datetime(2100,1,1))
    start_date=datelims[0]
    end_date=datelims[1]

    f0 = pd.read_excel('/ocean/eolson/MEOPAR/obs/Hakai/Dosser20180911/2018-09-11_144804_HakaiData_nutrients.xlsx',
                     sheet_name = 'Hakai Data',engine=excelEngine)
    f0.drop(['ACTION','Lat', 'Long', 'Collection Method', 'Installed', 'Lab Technician', 'NH4+', 'NO2+NO3 (ug/L)',
           'no2_no3_units', 'TP', 'TDP', 'TN', 'TDN', 'SRP', 'Project Specific ID', 'Hakai ID', 'Source',
           'po4pfilt', 'no3nfilt', 'po4punfl', 'no3nunfl', 'nh4nunfl', 'NH4+ Flag',
           'TP FLag', 'TDP FLag', 'TN Flag', 'TDN FLag','Volume (ml)',
           'SRP Flag', 'PO4 Flag', 'po4pfilt_flag', 'no3nfilt_flag','Preserved', 'Analyzed',
           'po4punfl_flag', 'no3nunfl_flag', 'nh4nunfl_flag', 'Analyzing Lab', 'Sample Status',
           'Quality Level', 'Comments', 'Quality Log'], axis = 1, inplace = True)
    dts0=[pytz.timezone('Canada/Pacific').localize(i).astimezone(pytz.utc).replace(tzinfo=None)
            for i in f0['Collected']]
    f0['dtUTC']=dts0

    fc = pd.read_csv('/ocean/eolson/MEOPAR/obs/Hakai/Dosser20180911/ctd-bulk-1536702711696.csv',
                    usecols=['Cast PK','Cruise','Station', 'Drop number','Start time', 'Bottom time',
                             'Latitude', 'Longitude', 'Depth (m)', 'Temperature (deg C)', 'Temperature flag', 'Pressure (dbar)',
                             'Pressure flag', 'PAR', 'PAR flag', 'Fluorometry Chlorophyll (ug/L)', 'Fluorometry Chlorophyll flag',
                             'Turbidity (FTU)', 'Turbidity flag',
                             'Salinity (PSU)', 'Salinity flag'],
                    dtype={'Drop number':np.float64,'PAR flag':str,'Fluorometry Chlorophyll flag':str},na_values=('null','-9.99e-29'))

    ## fix apparent typos:
    # reversed lats and lons
    iii=fc['Latitude']>90
    lons=-1*fc.loc[iii,'Latitude'].values
    lats=-1*fc.loc[iii,'Longitude'].values
    fc.loc[iii,'Longitude']=lons
    fc.loc[iii,'Latitude']=lats

    # remove data with missing lats and lons
    nans=fc.loc[(fc['Latitude'].isnull())|(fc['Longitude'].isnull())]
    fc=fc.drop(nans.index)

    # apparently bad lats/lons
    QU16bad=fc.loc[(fc['Station']=='QU16')&(fc['Latitude']>50.3)]
    fc=fc.drop(QU16bad.index)
    QU36bad=fc.loc[(fc['Station']=='QU36')&(fc['Latitude']>50.2)]
    fc=fc.drop(QU36bad.index)
    QU37bad=fc.loc[(fc['Station']=='QU37')&(fc['Longitude']<-125.1)]
    fc=fc.drop(QU37bad.index)
    QU38bad=fc.loc[(fc['Station']=='QU38')&(fc['Longitude']>-125.2)]
    fc=fc.drop(QU38bad.index)
    QU5bad=fc.loc[(fc['Station']=='QU5')&(fc['Longitude']>-125.18)]
    fc=fc.drop(QU5bad.index)

    # remove data with suspicious 0 temperature and salinity
    iind=(fc['Temperature (deg C)']==0)&(fc['Salinity (PSU)']==0)
    fc.loc[iind,['Temperature (deg C)', 'Pressure (dbar)', 'PAR', 'Fluorometry Chlorophyll (ug/L)', 'Turbidity (FTU)', 'Salinity (PSU)']]=np.nan

    fc['dt']=[dt.datetime.strptime(i.split('.')[0],'%Y-%m-%d %H:%M:%S') for i in fc['Start time']]
    dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime.strptime(i.split('.')[0],'%Y-%m-%d %H:%M:%S')).astimezone(pytz.utc).replace(tzinfo=None)
            for i in fc['Start time']]
    fc['dtUTC']=dts

    dloc=[dt.datetime(i.year,i.month,i.day) for i in fc['dt']]
    fc['dloc']=dloc

    fcS=fc.loc[:,['Latitude','Longitude']].groupby([fc['Station'],fc['dloc']]).mean().reset_index()

    f0['Station']=f0['Site ID']
    #f0['dt']=[dt.datetime.strptime(i,'%Y-%m-%d %H:%M:%S') for i in f0['Collected']]
    dloc0=[dt.datetime(i.year,i.month,i.day) for i in f0['Collected']]
    f0['dloc']=dloc0

    fdata=f0.merge(fcS,how='left')

    fdata['Lat']=fdata['Latitude']
    fdata['Lon']=fdata['Longitude']
    fdata['Z']=fdata['Line Out Depth']

    fdata['SA']=np.nan
    fdata['CT']=np.nan
    fdata['pZ']=np.nan
    df2=fdata.copy(deep=True)

    zthresh=1.5
    print("Note: CTD depths (pZ) may vary from bottle depths (Z) by up to ",str(zthresh)," m.")
    for i, row in df2.iterrows():
        idf=fc.loc[(fc.Station==row['Station'])&(fc.dloc==row['dloc'])&\
                   ((np.abs(fc['Depth (m)']-row['Pressure Transducer Depth (m)'])<zthresh)|(np.abs(fc['Depth (m)']-row['Line Out Depth'])<zthresh))]
        if len(idf)>0:
            zrow=row['Pressure Transducer Depth (m)'] if ~np.isnan(row['Pressure Transducer Depth (m)']) else row['Line Out Depth']
            zdifmin=np.min([np.abs(ii-zrow) for ii in idf['Depth (m)']])
            # if there are multiple minimum distance rows, just take the first
            idfZ=idf.loc[np.abs(idf['Depth (m)']-zrow)==zdifmin]
            isna = (not np.isnan(idfZ['Salinity (PSU)'].values[0])) and (not np.isnan(idfZ['Pressure (dbar)'].values[0])) and \
                    (not np.isnan(idfZ['Longitude'].values[0])) and (not np.isnan(idfZ['Latitude'].values[0]))
            isnat = (not np.isnan(idfZ['Temperature (deg C)'].values[0]))
            sal=gsw.SA_from_SP(idfZ['Salinity (PSU)'].values[0],idfZ['Pressure (dbar)'].values[0],idfZ['Longitude'].values[0],
                                idfZ['Latitude'].values[0]) if isna else np.nan
            tem=gsw.CT_from_t(sal,idfZ['Temperature (deg C)'].values[0],idfZ['Pressure (dbar)'].values[0]) if (isna and isnat) else np.nan
            fdata.at[i,'SA']=sal
            fdata.at[i,'CT']=tem
            fdata.at[i,'pZ']=idfZ['Depth (m)'].values[0]

    fdata2=fdata.loc[(fdata['dtUTC']>=start_date)&(fdata['dtUTC']<end_date)&(fdata['Z']>=0)&(fdata['Z']<440)&(fdata['Lon']<360)&(fdata['Lat']<=90)].copy(deep=True).reset_index()
    fdata2.drop(['no','event_pk','Date','Sampling Bout','Latitude','Longitude','index','Gather Lat','Gather Long', 'Pressure Transducer Depth (m)',
                'Filter Type','dloc','Collected','Line Out Depth','Replicate Number','Work Area','Survey','Site ID','NO2+NO3 Flag','SiO2 Flag'],axis=1,inplace=True)
    return fdata2


def load_ferry_ERDDAP(datelims, variables=None):
    """ load ferry data from ERDDAP, return a pandas dataframe.  Do conversion on temperature to
    conservative temperature, oxygen to uMol and rename grid i and grid j columns

    :arg datelims: start date and end date; as a 2-tuple of datetimes
    :type datelims: tuple

    :arg variables: variables to pull from the ferry, see base list below; as a list of strings
    :type variables: list

    :returns: variable values from ERDDAP for time period requested: as pandas dataframe
    :rtype: :py:class:`pandas.dataframe`
    """

    # load erddapy here so your can use the tools on computers without web access (sockeye)
    from erddapy import ERDDAP

    server = "https://salishsea.eos.ubc.ca/erddap"

    protocol = "tabledap"
    dataset_id = "ubcONCTWDP1mV18-01"

    if variables == None:
        variables = [
            "latitude",
            "longitude",
            "chlorophyll",
            "temperature",
            "salinity",
            "turbidity",
            "o2_concentration_corrected",
            "time",
            "nemo_grid_j",
            "nemo_grid_i"
        ]

    start_date = datelims[0].strftime('%Y-%m-%dT00:00:00Z')
    end_date = datelims[1].strftime('%Y-%m-%dT00:00:00Z')

    constraints = {
    "time>=": start_date,
    "time<=": end_date,
    "nemo_grid_j>=": 0,
    "on_crossing_mask=": 1,
    }

    obs = ERDDAP(server=server, protocol=protocol)
    obs.dataset_id = dataset_id
    obs.variables = variables
    obs.constraints = constraints

    obs_pd = obs.to_pandas(index_col="time (UTC)", parse_dates=True,).dropna()

    obs_pd['oxygen (uM)'] = 44.661 * obs_pd['o2_concentration_corrected (ml/l)']
    obs_pd['conservative temperature (oC)'] = gsw.CT_from_pt(obs_pd['salinity (g/kg)'], obs_pd['temperature (degrees_Celcius)'] )
    obs_pd['dtUTC'] = obs_pd.index.tz_localize(None)
    obs_pd.reset_index(inplace=True)
    obs_pd.rename(columns={"latitude (degrees_north)": "Lat", "longitude (degrees_east)": "Lon",
                      "nemo_grid_j (count)": "j", "nemo_grid_i (count)": "i"}, inplace=True)

    return obs_pd


def load_ONC_node_ERDDAP(datelims, variables=None):
    """ load ONC data from the nodes from ERDDAP, return a pandas dataframe.  Do conversion on temperature to
    conservative temperature. Pull out grid i, grid j and depth from places

    :arg datelims: start date and end date; as a 2-tuple of datetimes
    :type datelims: tuple

    :arg variables: variables to pull from the ferry, see base list below; as a list of strings
    :type variables: list

    :returns: variable values from ERDDAP for time period requested: as pandas dataframe
    :rtype: :py:class:`pandas.dataframe`
    """

    # load erddapy here so your can use the tools on computers without web access (sockeye)
    from erddapy import ERDDAP

    server = "https://salishsea.eos.ubc.ca/erddap"

    protocol = "tabledap"
    dataset_ids = ["ubcONCSCVIPCTD15mV1", "ubcONCSEVIPCTD15mV1", "ubcONCLSBBLCTD15mV1", "ubcONCUSDDLCTD15mV1"]
    nodes = ["Central node", "Delta BBL node", "Delta DDL node", "East node"]

    if variables == None:
        variables = [
            "latitude",
            "longitude",
            "temperature",
            "salinity",
            "time",
            "depth",
        ]

    start_date = datelims[0].strftime('%Y-%m-%dT00:00:00Z')
    end_date = datelims[1].strftime('%Y-%m-%dT00:00:00Z')

    constraints = {
    "time>=": start_date,
    "time<=": end_date,
    }

    obs_tot = []

    for inode, (dataset_id, node) in enumerate(zip(dataset_ids, nodes)):
        print (node, start_date, end_date)

        obs = ERDDAP(server=server, protocol=protocol)
        obs.dataset_id = dataset_id
        obs.variables = variables
        obs.constraints = constraints

        try:
            obs_pd = obs.to_pandas(index_col="time (UTC)", parse_dates=True,).dropna()
        except Exception as error:
            print (error)
            print ('Assuming no data')
            columns = ["dtUTC", "conservative temperature (oC)", "salinity (g/kg)", "latitude (degrees_north)", "longitude (degrees_east)"]
            obs_pd = pd.DataFrame(columns=columns)
        else:
            obs_pd['conservative temperature (oC)'] = gsw.CT_from_pt(obs_pd['salinity (g/kg)'], obs_pd['temperature (degrees_Celcius)'] )
            obs_pd['dtUTC'] = obs_pd.index.tz_localize(None)

        obs_pd.reset_index(inplace=True)
        obs_pd.rename(columns={"latitude (degrees_north)": "Lat", "longitude (degrees_east)": "Lon"}, inplace=True)
        (obs_pd['j'], obs_pd['i']) = places.PLACES[node]['NEMO grid ji']
        obs_pd['k'] = places.PLACES[node]['NEMO grid k']

        obs_tot.append(obs_pd)

    obs_concat = pd.concat(obs_tot)
    obs_concat.to_csv('checkitout.csv')

    return obs_concat


def WSS(obs,mod):
    # Willmott skill core, cannot include any NaN values
    return 1.0-np.sum((mod-obs)**2)/np.sum((np.abs(mod-np.mean(obs))+np.abs(obs-np.mean(obs)))**2)

def RMSE(obs,mod):
    # root mean square error, cannot include any NaN values
    return np.sqrt(np.sum((mod-obs)**2)/len(mod))

def stats(obs0,mod0):
    """ calculate useful model-data comparison statistics """
    obs0=_deframe(obs0)
    mod0=_deframe(mod0)
    iii=np.logical_and(~np.isnan(obs0),~np.isnan(mod0))
    obs=obs0[iii]
    mod=mod0[iii]
    N=len(obs)
    if N>0:
        modmean=np.mean(mod)
        obsmean=np.mean(obs)
        bias=modmean-obsmean
        vRMSE=RMSE(obs,mod)
        vWSS=WSS(obs,mod)
    else:
        modmean=np.nan
        obsmean=np.nan
        bias=np.nan
        vRMSE=np.nan
        vWSS=np.nan
    return N, modmean, obsmean, bias, vRMSE, vWSS

def varvarScatter(ax,df,obsvar,modvar,colvar,vmin=0,vmax=0,cbar=False,cm=cmo.cm.thermal,args={}):
    """ add scatter plot to axes ax with df[obsvar] on x-axis, df[modvar] on y-axis,
        and color determined by df[colvar]
        vmin and vmax are limits on color scale
    """
    obs0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[colvar]==df[colvar]),[obsvar]])
    mod0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[colvar]==df[colvar]),[modvar]])
    sep0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[colvar]==df[colvar]),[colvar]])
    if 'norm' in args:
        ps=ax.scatter(obs0,mod0,c=sep0,cmap=cm,**args)
    else:
        if vmin==vmax:
            vmin=np.min(sep0)
            vmax=np.max(sep0)
        ps=ax.scatter(obs0,mod0,c=sep0,vmin=vmin,vmax=vmax,cmap=cm,**args)
    if cbar==True:
        plt.colorbar(ps)
    return ps

def varvarPlot(ax,df,obsvar,modvar,sepvar='',sepvals=np.array([]),lname='',sepunits='',
    cols=('darkslateblue','royalblue','skyblue','mediumseagreen','darkseagreen','goldenrod',
            'coral','tomato','firebrick','mediumvioletred','magenta'),labels=''):
    """ model vs obs plot like varvarScatter but colors taken from a list
        as determined by determined from df[sepvar] and a list of bin edges, sepvals """
    # remember labels must include < and > cases
    if len(lname)==0:
        lname=sepvar
    ps=list()
    if len(sepvals)==0:
        obs0=_deframe(df[obsvar])
        mod0=_deframe(df[modvar])
        ps.append(ax.plot(obs0,mod0,'.',color=cols[0],label=lname))
    else:
        obs0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar]),[obsvar]])
        mod0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar]),[modvar]])
        sep0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar]),[sepvar]])
        sepvals=np.sort(sepvals)
        # less than min case:
        ii=0
        iii=sep0<sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} < {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[0]
            else:
                ll=u'{} $<$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii],label=ll)
            ps.append(p0)
        # between min and max:
        for ii in range(1,len(sepvals)):
            iii=np.logical_and(sep0<sepvals[ii],sep0>=sepvals[ii-1])
            if np.sum(iii)>0:
                #ll=u'{} {} \u2264 {} < {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                if len(labels)>0:
                    ll=labels[ii]
                else:
                    ll=u'{} {} $\leq$ {} $<$ {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii],label=ll)
                ps.append(p0)
        # greater than max:
        iii=sep0>=sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} \u2265 {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[ii+1]
            else:
                ll=u'{} $\geq$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii+1],label=ll)
            ps.append(p0)
    return ps

def varvarIter(ax,df,obsvar,modvar,sepvar='',lname='',
    cols=('darkslateblue','royalblue','skyblue','mediumseagreen','darkseagreen','goldenrod',
            'coral','tomato','firebrick','mediumvioletred','magenta'),labels=''):
    """ model vs obs plot like varvarScatter but colors taken from a list
        as determined by determined from df[sepvar] and a list of bin edges, sepvals """
    # remember labels must include < and > cases
    if len(lname)==0:
        lname=sepvar
    ps=list()
    df2=df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])]
    for ii,isep in enumerate(df2[sepvar].drop_duplicates().values):
        obs0=_deframe(df2.loc[df2[sepvar]==isep,[obsvar]])
        mod0=_deframe(df2.loc[df2[sepvar]==isep,[modvar]])
        p0,=ax.plot(obs0,mod0,'.',color=cols[ii],label=isep)
        ps.append(p0)
    return ps

def tsertser_graph(ax,df,obsvar,modvar,start_date,end_date,sepvar='',sepvals=([]),lname='',sepunits='',
                  ocols=('blue','darkviolet','teal','green','deepskyblue'),
                  mcols=('fuchsia','firebrick','orange','darkgoldenrod','maroon'),labels=''):
    """ Creates timeseries by adding scatter plot to axes ax with df['dtUTC'] on x-axis,
        df[obsvar] and df[modvar] on y axis, and colors taken from a listas determined from
        df[sepvar] and a list of bin edges, sepvals
    """
    if len(lname)==0:
        lname=sepvar
    ps=list()
    if len(sepvals)==0:
        obs0=_deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[obsvar]])
        mod0=_deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[modvar]])
        time0=_deframe(df.loc[(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),['dtUTC']])
        p0,=ax.plot(time0,obs0,'.',color=ocols[0],label=f'Observed {lname}')
        ps.append(p0)
        p0,=ax.plot(time0,mod0,'.',color=mcols[0],label=f'Modeled {lname}')
        ps.append(p0)
    else:
        obs0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[obsvar]])
        mod0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[modvar]])
        time0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),['dtUTC']])
        sep0=_deframe(df.loc[(df[obsvar]==df[obsvar])&(df[modvar]==df[modvar])&(df[sepvar]==df[sepvar])&(df['dtUTC'] >= start_date)&(df['dtUTC']<= end_date),[sepvar]])
        sepvals=np.sort(sepvals)
                # less than min case:
        ii=0
        iii=sep0<sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} < {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[0]
            else:
                ll=u'{} $<$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(time0[iii],obs0[iii],'.',color=ocols[ii],label=f'Observed {ll}')
            ps.append(p0)
            p0,=ax.plot(time0[iii],mod0[iii],'.',color=mcols[ii],label=f'Modeled {ll}')
            ps.append(p0)
        # between min and max:
        for ii in range(1,len(sepvals)):
            iii=np.logical_and(sep0<sepvals[ii],sep0>=sepvals[ii-1])
            if np.sum(iii)>0:
                #ll=u'{} {} \u2264 {} < {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                if len(labels)>0:
                    ll=labels[ii]
                else:
                    ll=u'{} {} $\leq$ {} $<$ {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                p0,=ax.plot(time0[iii],obs0[iii],'.',color=ocols[ii],label=f'Observed {ll}')
                ps.append(p0)
                p0,=ax.plot(time0[iii],mod0[iii],'.',color=mcols[ii],label=f'Modeled {ll}')
                ps.append(p0)
        # greater than max:
        iii=sep0>=sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} \u2265 {} {}'.format(lname,sepvals[ii],sepunits).strip()
            if len(labels)>0:
                ll=labels[ii+1]
            else:
                ll=u'{} $\geq$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(time0[iii],obs0[iii],'.',color=ocols[ii+1],label=f'Observed {ll}')
            ps.append(p0)
            p0,=ax.plot(time0[iii],mod0[iii],'.',color=mcols[ii+1],label=f'Modeled {ll}')
            ps.append(p0)
    yearsFmt = mdates.DateFormatter('%d %b %y')
    ax.xaxis.set_major_formatter(yearsFmt)
    return ps


def _deframe(x):
    # if array is pandas series or dataframe, return the values only
    if isinstance(x,pd.Series) or isinstance(x,pd.DataFrame):
        x=x.values.flatten()
    return x

def _flatten_nested_dict(tdic0):
    # used by displayStats function
    # tdic argument is nested dictionary of consistent structure
    def _flatten_nested_dict_inner(tdic,ilist,data):
        # necessary because mutable defaults instantiated when function is defined;
        # need different entry point at start
        for el in tdic.keys():
            if isinstance(tdic[el],dict):
                data=_flatten_nested_dict_inner(tdic[el],ilist+list((el,)),data)
            else:
                data.append(ilist+list((el,tdic[el])))
        return data
    ilist0=list()
    data0=list()
    data0=_flatten_nested_dict_inner(tdic0,ilist0,data0)
    return data0

def displayStats(statdict,level='Subset',suborder=None):
    # stats dict starting from variable level
    cols={'Subset':('Subset','Metric',''),
          'Variable':('Variable','Subset','Metric',''),
          'Year':('Year','Variable','Subset','Metric','')}
    ind={'Subset':['Order','Subset','Metric'],
         'Variable':['Variable','Order','Subset','Metric'],
         'Year':['Variable','Subset','Metric']}
    pcols={'Subset':['Metric'],
           'Variable':['Metric'],
           'Year':['Year','Metric']}
    allrows=_flatten_nested_dict(statdict)
    tdf=pd.DataFrame(allrows,columns=cols[level])
    if suborder is not None:
        subD={suborder[ii]: ii for ii in range(0,len(suborder))}
        tdf['Order']=[subD[tdf['Subset'][ii]] for ii in range(0,len(tdf['Subset']))]
    tdf.set_index(ind[level],inplace=True)
    tbl=pd.pivot_table(tdf,index=ind[level][:-1],columns=pcols[level]).rename_axis(index={'Order':None},columns={'Metric':None}).style.format({
        'N': '{:d}',
        'Bias':'{:.3f}',
        'WSS':'{:.3f}',
        'RMSE':'{:.3f}'})
    return tbl,tdf

def displayStatsFlex(statdict,cols,ind,pcols,suborder=None):
    # more flexible version of stats display
    # stats dict starting from variable level
    allrows=_flatten_nested_dict(statdict)
    tdf=pd.DataFrame(allrows,columns=cols)
    if suborder is not None:
        subD={suborder[ii]: ii for ii in range(0,len(suborder))}
        tdf['Order']=[subD[tdf['Subset'][ii]] for ii in range(0,len(tdf['Subset']))]
    tdf.set_index(ind,inplace=True)
    tbl=pd.pivot_table(tdf,index=ind[:-1],columns=pcols).rename_axis(index={'Order':None},columns={'Metric':None}).style.format({
        'N': '{:d}',
        'Bias':'{:.3f}',
        'WSS':'{:.3f}',
        'RMSE':'{:.3f}'})
    return tbl,tdf

def utc_to_pac(timeArray):
    # UTC to Pacific time zone
    return [pytz.utc.localize(ii).astimezone(pytz.timezone('Canada/Pacific')) for ii in timeArray]

def pac_to_utc(pactime0):
    # input datetime object without tzinfo in Pacific Time and
    # output datetime object (or np array of them) without tzinfo in UTC
    pactime=np.array(pactime0,ndmin=1)
    if pactime.ndim>1:
        raise Exception('Error: ndim>1')
    out=np.empty(pactime.shape,dtype=object)
    pac=pytz.timezone('Canada/Pacific')
    utc=pytz.utc
    for ii in range(0,len(pactime)):
        itime=pactime[ii]
        loc_t=pac.localize(itime)
        utc_t=loc_t.astimezone(utc)
        out[ii]=utc_t.replace(tzinfo=None)
    return (out[0] if np.shape(pactime0)==() else out)

def pdt_to_utc(pactime0):
    # input datetime object without tzinfo in Pacific Daylight Time and
    # output datetime object (or np array of them) without tzinfo in UTC
    # verified: PDT is GMT+7 at all times of year
    pactime=np.array(pactime0,ndmin=1)
    if pactime.ndim>1:
        raise Exception('Error: ndim>1')
    out=np.empty(pactime.shape,dtype=object)
    pac=pytz.timezone('Etc/GMT+7')
    utc=pytz.utc
    for ii in range(0,len(pactime)):
        itime=pactime[ii]
        loc_t=pac.localize(itime)
        utc_t=loc_t.astimezone(utc)
        out[ii]=utc_t.replace(tzinfo=None)
    return (out[0] if np.shape(pactime0)==() else out)

def pst_to_utc(pactime0):
    # input datetime object without tzinfo in Pacific Standard Time and
    # output datetime object (or np array of them) without tzinfo in UTC
    # verified: PST is GMT+8 at all times of year (GMT does not switch)
    pactime=np.array(pactime0,ndmin=1)
    if pactime.ndim>1:
        raise Exception('Error: ndim>1')
    out=np.empty(pactime.shape,dtype=object)
    pac=pytz.timezone('Etc/GMT+8')
    utc=pytz.utc
    for ii in range(0,len(pactime)):
        itime=pactime[ii]
        loc_t=pac.localize(itime)
        utc_t=loc_t.astimezone(utc)
        out[ii]=utc_t.replace(tzinfo=None)
    return (out[0] if np.shape(pactime0)==() else out)

def datetimeToDecDay(dtin0):
    # handle single datetimes or arrays
    dtin=np.array(dtin0,ndmin=1)
    if dtin.ndim>1:
        raise Exception('Error: ndim>1')
    out=np.empty(dtin.shape,dtype=object)
    for ii in range(0,len(dtin)):
        tdif=dtin[ii]-dt.datetime(1900,1,1)
        out[ii]=tdif.days+tdif.seconds/(3600*24)
    return (out[0] if np.shape(dtin0)==() else out)

def printstats(datadf,obsvar,modvar):
    N, modmean, obsmean, bias, RMSE, WSS = stats(datadf.loc[:,[obsvar]],datadf.loc[:,[modvar]])
    print('  N: {}\n  bias: {}\n  RMSE: {}\n  WSS: {}'.format(N,bias,RMSE,WSS))
    return

def datetimeToYD(idt):
    if type(idt)==dt.datetime:
        yd=(idt-dt.datetime(idt.year-1,12,31)).days
    else: # assume array or pandas, or acts like it
        yd=[(ii-dt.datetime(ii.year-1,12,31)).days for ii in idt]
    return yd

def getChlNRatio(nmlfile='namelist_smelt_cfg',basedir=None,nam_fmt=None,idt=dt.datetime(2015,1,1)):
    """ for a given run, load the bio namelist and extract the chl to nitrogen ratio for phytoplankton
    """
    if not ((basedir and nam_fmt) or os.path.isfile(nmlfile)):
        raise Exception('nmlfile must contain full namelist path or basedir and nam_fmt must be defined')
    if basedir:
        if nam_fmt=='nowcast':
            nmlfile=os.path.join(basedir,idt.strftime('%d%b%y').lower(),nmlfile)
        elif nam_fmt=='long':
            nmlfile=os.path.join(basedir,nmlfile)
        else:
            raise Exception('Invalid nam_fmt')
    with open(nmlfile) as nmlf:
        nml=f90nml.read(nmlf)
    return nml['nampisprod']['zz_rate_si_ratio_diat']

def load_Pheo_data(year,datadir='/ocean/eolson/MEOPAR/obs/WADE/ptools_data/ecology'):
    """ This function automatically loads the chlorophyll bottle data from WADE for a
        given year specified by the user. The output is a pandas dataframe with all of
        the necessary columns and groups needed for matching to the model data.
    """
    ## duplicate Station/Date entries with different times seem to be always within a couple of hours,
    # so just take the first (next cell)
    dfTime=pd.read_excel('/ocean/eolson/MEOPAR/obs/WADE/WDE_Data/OlsonSuchyAllen_UBC_PDR_P003790-010721.xlsx',
                        engine='openpyxl',sheet_name='EventDateTime')
    test=dfTime.groupby(['FlightDate','SiteCode'])['TimeDown \n(Local - PST or PDT)'].count()
    # drop duplicate rows
    dfTime.drop_duplicates(subset=['FlightDate','SiteCode'],keep='first',inplace=True)
    print(dfTime.keys())
    dfTime['dtPac']=[dt.datetime.combine(idate, itime) for idate, itime \
             in zip(dfTime['FlightDate'],dfTime['TimeDown \n(Local - PST or PDT)'])]
    dfTime['dtUTC']=[pac_to_utc(ii) for ii in dfTime['dtPac']]
    # PROCESS STATION LOCATION INFO (based on Parker's code)
    sta_fn='/ocean/eolson/MEOPAR/obs/WADE/WDE_Data/OlsonSuchyAllen_UBC_PDR_P003790-010721.xlsx'
    sheetname='Site Info'
    sta_df =pd.read_excel(sta_fn,engine='openpyxl',sheet_name=sheetname)
    sta_df.dropna(how='any',subset=['Lat_NAD83 (deg / dec_min)','Long_NAD83 (deg / dec_min)','Station'],inplace=True)
    sta_df = sta_df.set_index('Station')
    # get locations in decimal degrees
    for sta in sta_df.index:
        lat_str = sta_df.loc[sta, 'Lat_NAD83 (deg / dec_min)']
        lat_deg = float(lat_str.split()[0]) + float(lat_str.split()[1])/60
        sta_df.loc[sta,'Lat'] = lat_deg
        #
        lon_str = sta_df.loc[sta, 'Long_NAD83 (deg / dec_min)']
        lon_deg = float(lon_str.split()[0]) + float(lon_str.split()[1])/60
        sta_df.loc[sta,'Lon'] = -lon_deg
    sta_df.pop('Lat_NAD83 (deg / dec_min)');
    sta_df.pop('Long_NAD83 (deg / dec_min)');
    fn='/ocean/eolson/MEOPAR/obs/WADE/WDE_Data/OlsonSuchyAllen_UBC_PDR_P003790-010721.xlsx'
    sheetname='LabChlaPheo'
    chlPheo =pd.read_excel(fn,engine='openpyxl',sheet_name=sheetname)
    chlPheo.dropna(how='any',subset=['Date','Station','SamplingDepth'],inplace=True)
    # average over replicates
    chlPheo2=pd.DataFrame(chlPheo.groupby(['Date','Station','SamplingDepth'],as_index=False).mean())
    # join to station info (lat/lon)
    chlPheo3=pd.merge(left=sta_df,right=chlPheo2,how='right',
                     left_on='Station',right_on='Station')
    # join to date/time
    dfTime['dtUTC']=[pac_to_utc(dt.datetime.combine(idate,itime)) for idate,itime in \
                    zip(dfTime['FlightDate'],dfTime['TimeDown \n(Local - PST or PDT)'])]
    dfTime2=dfTime.loc[:,['FlightDate','SiteCode','dtUTC']]
    chlPheoFinal=pd.merge(left=chlPheo3,right=dfTime2,how='left',
                          left_on=['Date','Station'],right_on=['FlightDate','SiteCode'])
    #drop the 47 NA datetime values
    chlPheoFinal.dropna(how='any',subset=['dtUTC'],inplace=True)
    #Add extra columns for later use
    chlPheoFinal['Z']=chlPheoFinal['SamplingDepth']
    chlPheoFinal['Year']=[ii.year for ii in chlPheoFinal['dtUTC']]
    chlPheoFinal['YD']=datetimeToYD(chlPheoFinal['dtUTC'])
    chlPheoYear=pd.DataFrame(chlPheoFinal.loc[chlPheoFinal.Year==year])
    return chlPheoYear

def load_WADE_data(year,datadir='/ocean/eolson/MEOPAR/obs/WADE/ptools_data/ecology'):
    """ This function automatically loads the nutrient bottle data from WADE for a given year
        specified by the user. The output is a pandas dataframe with all of te necessary
        columns and groups needed for matching to the model data.
    """
    dfSta=pickle.load(open(os.path.join(datadir,'sta_df.p'),'rb'))
    dfBot=pickle.load(open(os.path.join(datadir,f'Bottles_{str(year)}.p'),'rb'))
    df=pd.merge(left=dfSta,right=dfBot,how='right',
             left_on='Station',right_on='Station')
    try:
        len(df.loc[pd.isnull(df['Latitude'])]) == 0
    except:
        pass
        print('Warning!, Stations found without Latitude or Longitude value!')
    try:
        len(df) == len(dfBot)
    except:
        pass
        print(f'Warning!, Merge completed incorrectly. length of bottle data = {len(dfBot)} length of merged data = {len(df)}')
    # where no time is provided, set time to midday Pacific time = ~ 20:00 UTC
    df['UTCDateTime']=[iiD+dt.timedelta(hours=20) if pd.isnull(iiU) \
                    else iiU for iiU,iiD in \
                    zip(df['UTCDateTime'],df['Date'])]
    df.rename(columns={'UTCDateTime':'dtUTC','Latitude':'Lat','Longitude':'Lon'},inplace=True)
    df['Z']=-1*df['Z']
    df.head()
    df['NO23']=df['NO3(uM)D']+df['NO2(uM)D'] # the model does not distinguish between NO2 and NO3
    df['Amm']=df['NH4(uM)D']
    df['Si']=df['SiOH4(uM)D']
    df['Year']=[ii.year for ii in df['dtUTC']]
    df['YD']=datetimeToYD(df['dtUTC'])
    return(df)


def load_CTD_data(year,datadir='/ocean/eolson/MEOPAR/obs/WADE/ptools_data/ecology'):
    """ Returns a dataframe containing CTD data for a given year merged with station data
    """
    dfSta=pickle.load(open(os.path.join(datadir,'sta_df.p'),'rb'))
    dfCTD0=pickle.load(open(os.path.join(datadir,f'Casts_{str(year)}.p'),'rb'))
    dfCTD=pd.merge(left=dfSta,right=dfCTD0,how='right',
             left_on='Station',right_on='Station')
    try:
        dfCTD.groupby(['Station','Year','YD','Z']).count()==[1]
    except:
        pass
        print('Only one cast per CTD station per day')
    # where no time is provided, set time to midday Pacific time = ~ 20:00 UTC
    dfCTD['dtUTC']=[iiD+dt.timedelta(hours=20) for iiD in dfCTD['Date']] #Does this mean it also has that flaw where we are not sure when the data was collected?
    dfCTD.rename(columns={'Latitude':'Lat','Longitude':'Lon'},inplace=True)
    dfCTD['Z']=-1*dfCTD['Z']
    # Calculate Absolute (Reference) Salinity (g/kg) and Conservative Temperature (deg C) from
    # Salinity (psu) and Temperature (deg C):
    press=gsw.p_from_z(-1*dfCTD['Z'],dfCTD['Lat'])
    dfCTD['SA']=gsw.SA_from_SP(dfCTD['Salinity'],press,
                           dfCTD['Lon'],dfCTD['Lat'])
    dfCTD['CT']=gsw.CT_from_t(dfCTD['SA'],dfCTD['Temperature'],press)
    dfCTD['Year']=[ii.year for ii in dfCTD['dtUTC']]
    dfCTD['YD']=datetimeToYD(dfCTD['dtUTC'])
    return(dfCTD)
