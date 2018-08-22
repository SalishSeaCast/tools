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
    filemap,
    fdict,
    mod_start,
    mod_end,
    mod_nam_fmt='nowcast',
    mod_basedir='/results/SalishSea/nowcast-green/',
    mod_flen=1,
    method='bin',
    deltat=0,
    deltad=0.0,
    meshPath='/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702_noLPE.nc'
    ):
    """Given a dataset, find the nearest model matches

    :arg data: pandas dataframe containing data to compare to. Must include the following:
        'dtUTC': column with UTC date and time
        'Lat': decimal latitude
        'Lon': decimal longitude
        'Z': depth, positive 
    :type :py:class:`pandas.DataFrame`

    :arg dict varmap: dictionary mapping names of data columns to variable names, string to string, model:data

    :arg dict filemap: dictionary mapping names of model variables to filetypes containing them 

    :arg dict fdict: dictionary mapping filetypes to their time resolution in hours

    :arg mod_start: date of start of first selected model file
    :type :py:class:`datetime.datetime`

    :arg mod_end: last date of model run
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

    :arg str meshPath: path to mesh file

    """
    # check that required columns are in dataframe:
    if not set(('dtUTC','Lat','Lon','Z')) <= set(data.keys()):
        raise Exception('{} missing from data'.format([el for el in set(('dtUTC','Lat','Lon','Z'))-set(data.keys())],'%s'))

    # check that entries are minimal and consistent:
    fkeysVar=list(filemap.keys())
    for ikey in fkeysVar:
        if ikey not in set(varmap.values()):
            filemap.pop(ikey) 
    if len(set(varmap.values())-set(filemap.keys()))>0:
        print('Error: file(s) missing from filemap:',set(varmap.values())-set(filemap.keys()))
    fkeysVar=list(filemap.keys())
    ftypes=list(fdict.keys())
    for ikey in ftypes:
        if ikey not in set(filemap.values()):
            fdict.pop(ikey) 
    if len(set(filemap.values())-set(fdict.keys()))>0:
        print('Error: file(s) missing from fdict:',set(filemap.values())-set(fdict.keys()))
    ftypes=list(fdict.keys()) 
    # reverse filemap dict
    filemap_r=dict()
    for ift in ftypes:
        filemap_r[ift]=list()
    for ikey in filemap:
        filemap_r[filemap[ikey]].append(ikey)

    # adjustments to data dataframe
    data=data.loc[(data.dtUTC>=mod_start)&(data.dtUTC<mod_end)].copy(deep=True)
    data=data.dropna(how='any',subset=['dtUTC','Lat','Lon','Z']).dropna(how='all',subset=[*varmap.keys()])
    data['j']=np.zeros((len(data))).astype(int)
    data['i']=np.zeros((len(data))).astype(int)
    with nc.Dataset(meshPath) as fmesh:
        lmask=-1*(fmesh.variables['tmask'][0,0,:,:]-1)
        for la,lo in np.unique(data.loc[:,['Lat','Lon']].values,axis=0):
            jj, ii = geo_tools.find_closest_model_point(lo, la, fmesh.variables['nav_lon'], fmesh.variables['nav_lat'], 
                                                        land_mask = lmask)
            data.loc[(data.Lat==la)&(data.Lon==lo),['j','i']]=jj,ii
    data=data.sort_values(by=['dtUTC','Lat','Lon','Z'])
    data.reset_index(drop=True,inplace=True)

    # set up columns to accept model values
    for ivar in varmap.values():
        data['mod_'+ivar]=np.zeros((len(data)))

    # list model files
    flist=dict()
    for ift in ftypes:
        flist[ift]=index_model_files(mod_start,mod_end,mod_basedir,mod_nam_fmt,mod_flen,ift,fdict[ift])

    if method == 'bin':
        data = _binmatch(data,flist,ftypes,filemap_r)
    else:
        print('option '+method+' not written yet')
        return
    return data, varmap

def _binmatch(data,flist,ftypes,filemap_r):
    # loop through data, openening and closing model files as needed and storing model data
    for ind, row in data.iterrows():
        if ind==0: # load first files
            fid=dict()
            fend=dict()
            for ift in ftypes:
                fid,fend=_nextfile_bin(ift,row['dtUTC'],flist[ift],fid,fend,flist)
            torig=dt.datetime.strptime(fid[ftypes[0]].variables['time_centered'].time_origin,'%Y-%m-%d %H:%M:%S') # assumes same for all files in run
        for ift in ftypes:
            if row['dtUTC']>=fend[ift]:
                fid,fend=_nextfile_bin(ift,row['dtUTC'],flist[ift],fid,fend,flist)
            # now read data
            # find time index
            ih=_getTimeInd_bin(row['dtUTC'],fid[ift],torig)
            # find depth index
            ik=_getZInd_bin(row['Z'],fid[ift])
            # assign values for each var assoc with ift
            for ivar in filemap_r[ift]:
                data.loc[ind,['mod_'+ivar]]=fid[ift].variables[ivar][ih,ik,row['j'],row['i']]
    return data

def _nextfile_bin(ift,idt,ifind,fid,fend,flist):
    if ift in fid.keys():
        fid[ift].close()
    frow=flist[ift].loc[(ifind.t_0<=idt)&(ifind.t_n>idt)]
    fid[ift]=nc.Dataset(frow['paths'].values[0])
    fend[ift]=frow['t_n'].values[0]
    return fid, fend

def _getTimeInd_bin(idt,ifid,torig):
    tlist=ifid.variables['time_centered_bounds'][:,:]
    ih=[iii for iii,hhh in enumerate(tlist) if hhh[1]>(idt-torig).total_seconds()][0] # return first index where latter endpoint is larger
    return ih

def _getZInd_bin(idt,ifid):
    tlist=ifid.variables['deptht_bounds'][:,:]
    ih=[iii for iii,hhh in enumerate(tlist) if hhh[1]>idt][0] # return first index where latter endpoint is larger
    return ih

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
    t_n=list()
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
        t_n.append(iitn)
        iits=iitn
        ind=ind+1
    return pd.DataFrame(data=np.swapaxes([paths,t_0,t_n],0,1),index=inds,columns=['paths','t_0','t_n']) 
