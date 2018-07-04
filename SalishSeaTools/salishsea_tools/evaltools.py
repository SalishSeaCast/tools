# Copyright 2018 The Salish Sea NEMO Project and
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
from salishsea_tools import geo_tools

def matchData(
    data,
    varmap,
    mod_start,
    mod_end,
    method='bin',
    deltat=0,
    deltad=0.0,
    mod_nam_fmt='nowcast',
    mod_basedir='/results/SalishSea/nowcast-green/',
    mod_flen=1,
    mod_ftype='ptrc_T',
    mod_tres=1,
    meshPath='/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702_noLPE.nc'
    #bathyPath='/results/nowcast-sys/grid/bathymetry_201702.nc'
):
    """Given a dataset, find the nearest model matches

    :arg data: pandas dataframe containing data to compare to. Must include the following:
        'dtUTC': column with UTC date and time
        'Lat': decimal latitude
        'Lon': 
    :type :py:class:`pandas.DataFrame`

    :arg dict varmap: dictionary mapping names of data columns to variable names, string to string

    :arg mod_start: date of start of first selected model file
    :type :py:class:`datetime.datetime`

    :arg mod_end: at least 1 > last start  date for model results

    :type :py:class:`datetime.datetime`

    :arg str method: method to use for matching. options are:
        'bin'- bin in time and space; simplest case
        'interp'- linearly interpolate in time and depth
        'loosetime'- choose best match within temporal window deltat; requires addl input deltat
        'loosespace'- choose best match within horizontal radius deltad; requires addl input deltad
        'loose'- loose time and loose space: requires deltat and deltad

    :arg float deltad: match window radius in km

    :arg int deltat: match window radius in hours
    
    :arg str mod_nam_fmt: naming format for model files. options are 'nowcast' or 'long'
        'nowcast' example: 05may15/SalishSea_1h_20150505_20150505_ptrc_T.nc
        'long' example: SalishSea_1h_20150206_20150804_ptrc_T_20150427-20150506.nc
                    'long' will recursively search subdirectories (to match Vicky's storage style)

    :arg str mod_basedir: path to search for model files; defaults to nowcast-green

    :arg int mod_flen: length of model files in days; defaults to 1, which is how nowcast data is stored

    :arg str mod_ftype: file type specifier, eg ptrc_T, grid_T, etc 

    :arg int mod_tres: temporal resolution of file to read in hours; defaults to 1 for hourly files

    :arg str bathyPath: path to bathymetry file

    """

    flist=index_model_files(mod_start,mod_end,mod_basedir,mod_nam_fmt,mod_flen,mod_ftype,mod_tres)

    with nc.Dataset(meshPath) as mesh:
        mlon = np.copy(mesh.variables['nav_lon'][:, :])
        mlat = np.copy(mesh.variables['nav_lat'][:, :])
        tmask= np.copy(mesh.variables['tmask'][0,:,:,:]

    # restrct data to time range of interest
    data=data.loc[(data.dtUTC>=mod_start)&(data.dtUTC<mod_end)]
    # make sure data is in ascending order in time with monotonically increasing index
    data=data.sort_values('dtUTC').set_index(np.arange(0,len(data)))
    data=data.dropna(how='any',subset=['dtUTC','Lat','Lon']).dropna(how='all',subset=[*varmap.keys()])

    if method == 'bin':
        return _binmatch(data,flist,mlon,mlat,mod_start,mod_end,...)
    else:
        print('option '+method+' not written yet')
        return


def _binmatch(data,flist,mlon,mlat,mod_start,mod_end,...):

    with nc.Dataset(flist['paths'][0]) as fd:
          deptht=np.copy(fd.variables['deptht_bounds'][:])

    list_of_i = list()
    list_of_j = list()
    list_of_k = list()
    list_of_mod=dict()
    for var in varmap.keys:
        list_of_mod[var]=list()
    for n in data.index:
        date = data.dtUTC[n]
        j, i = geo_tools.find_closest_model_point(data.Lon[n], data.Lat[n], 
                                             mlon, mlat, land_mask = tmask[0,:,:])
        k = np.argwhere((deptht[:,0]<=data.depth[n])&(deptht[:,1]>data.depth[n]))
        if mesh.variables['tmask'][0, k, j, i] == 1:
            for m in range(numfiles):
                if (date > bounds[m]) & (date < bounds[m+1]):
                    here = m
            datestr_l = bounds_l[here].strftime('%Y%m%d')
            datestr_r = bounds_r[here].strftime('%Y%m%d')
            datestr = datestr_l + '-' + datestr_r
            nuts = nc.Dataset(glob.glob(PATH + 'SalishSea*1h*ptrc_T*' + datestr +'.nc')[0])
            if date.minute < 30:
                before = datetime.datetime(year = date.year, month = date.month, day = date.day, 
                                   hour = (date.hour), minute = 30) - datetime.timedelta(hours=1)
            if date.minute >= 30:
                before = datetime.datetime(year = date.year, month = date.month, day = date.day, 
                                       hour = (date.hour), minute = 30)
            delta = (date.minute) / 60
            hour = (before - bounds_l[here]).days * 24 + int((before - bounds_l[here]).seconds / 60 / 60)
            ni_val = (delta*(nuts.variables['nitrate'][hour, depth, Yind, Xind] ) + 
                       (1- delta)*(nuts.variables['nitrate'][hour+1, depth, Yind, Xind] ))
            si_val = (delta*(nuts.variables['silicon'][hour, depth, Yind, Xind] ) + 
                       (1- delta)*(nuts.variables['silicon'][hour+1, depth, Yind, Xind] ))
            list_of_lons = np.append(list_of_lons, df2.Lon[n])
            list_of_lats = np.append(list_of_lats, df2.Lat[n])
            list_of_datetimes = np.append(list_of_datetimes, date)
            list_of_cs_ni = np.append(list_of_cs_ni, float(df2['N'][n]))
            list_of_cs_si = np.append(list_of_cs_si, float(df2['Si'][n]))
            list_of_model_ni = np.append(list_of_model_ni, ni_val)
            list_of_model_si = np.append(list_of_model_si, si_val)
            #list_of_depths = np.append(list_of_depths, depth)
            list_of_depths = np.append(list_of_depths, df2.depth[n])

    return newdata

def index_model_files(start,end,basedir,nam_fmt,flen,ftype,tres):
    """
    See inputs for matchData above.
    outputs pandas dataframe containing columns 'paths','t_0', and 't_1'
    """
    if ftype not in ('ptrc_T','grid_T','grid_W','grid_U','grid_V','dia1_T'):
        print('ftype={}, are you sure? (if yes, add to list)'.format(ftype))
    if tres==24:
        ftres='1d'
    else:
        ftres=str(int(tres))+'h'
    ffmt='%Y%m%d'
    dfmt='%d%b%y'
    if nam_fmt=='nowcast':
        stencil='{0}/SalishSea_'+ftres+'_{1}_{1}_'+ftype+'.nc'
    elif nam_fmt=='long':
       stencil='**/SalishSea_'+ftres+'*'+ftype+'_{1}-{2}.nc' 
    else:
        raise Exception('nam_fmt '+nam_fmt+' is not defined')
    iits=start
    ind=0
    inds=list()
    paths=list()
    t_0=list()
    t_1=list()
    while iits<=end:
        iite=iits+dt.timedelta(days=(flen-1))
        iitn=iits+dt.timedelta(days=flen)
        try:
            iifstr=glob.glob(basedir+stencil.format(iits.strftime(dfmt).lower(),iits.strftime(ffmt),iite.strftime(ffmt)),recursive=True)[0]
        except:
            print('file does not exist:  '+basedir+stencil.format(iits.strftime(dfmt).lower(),iits.strftime(ffmt),iite.strftime(ffmt)))
            raise
        inds.append(ind)
        paths.append(iifstr)
        t_0.append(iits)
        t_1.append(iitn)
        iits=iitn
        ind=ind+1
    return pd.DataFrame(data=np.swapaxes([paths,t_0,t_1],0,1),index=inds,columns=['paths','t_0','t_1'])
    
