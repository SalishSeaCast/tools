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
import gsw
import os
import pytz
import matplotlib.pyplot as plt
import cmocean as cmo
import warnings

# :arg dict varmap: dictionary mapping names of data columns to variable names, string to string, model:data
def matchData(
    data,
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
    meshPath='/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702_noLPE.nc',
    maskName='tmask',
    wrapSearch=False,
    wrapTol=1,
    e3tvar='e3t',
    fid=None,
    sdim=3
    ):
    """Given a dataset, find the nearest model matches

    note: only one grid mask is loaded so all model variables must be on same grid; defaults to tmask

    :arg data: pandas dataframe containing data to compare to. Must include the following:
        'dtUTC': column with UTC date and time
        'Lat': decimal latitude
        'Lon': decimal longitude
        'Z': depth, positive 
    :type :py:class:`pandas.DataFrame`

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

    :arg str maskName: variable name for mask in mesh file (check code for consistency if not tmask)

    :arg boolean wrapSearch: if True, use wrapper on find_closest_model_point that assumes nearness of values

    :arg int wrapTol: assumed search radius from previous grid point if wrapSearch=True

    :arg str e3tvar: name of tgrid thicknesses variable; only for method=interpZe3t, which only works on t grid

    :arg Dataset fid: optionally include name of a single dataset when looping is not necessary and all matches come from
        a single file

    :arg int sdim: optionally enter number of spatial dimensions (must be the same for all variables per call);
        defaults to 3

    """
    # define dictionaries of mesh lat and lon variables to use with different grids:
    lonvar={'tmask':'nav_lon','umask':'glamu','vmask':'glamv','fmask':'glamf'}
    latvar={'tmask':'nav_lat','umask':'gphiu','vmask':'gphiv','fmask':'gphif'}
    # check that required columns are in dataframe:
    if method == 'ferry':
        reqsubset=['dtUTC','Lat','Lon']
    else:
        reqsubset=['dtUTC','Lat','Lon','Z']
    if not set(reqsubset) <= set(data.keys()):
        raise Exception('{} missing from data'.format([el for el in set(reqsubset)-set(data.keys())],'%s'))
    fkeysVar=list(filemap.keys())
    ftypes=list(fdict.keys())
    # don't load more files than necessary:
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
    data=data.dropna(how='any',subset=reqsubset) #.dropna(how='all',subset=[*varmap.keys()])
    with nc.Dataset(meshPath) as fmesh:
        omask=np.copy(fmesh.variables[maskName])
        navlon=np.squeeze(np.copy(fmesh.variables[lonvar[maskName]][:,:]))
        navlat=np.squeeze(np.copy(fmesh.variables[latvar[maskName]][:,:]))
    data=_gridHoriz(data,omask,navlon,navlat,wrapSearch)
    data=data.sort_values(by=[ix for ix in ['dtUTC','Z','j','i'] if ix in reqsubset]) # preserve list order
    data.reset_index(drop=True,inplace=True)

    # set up columns to accept model values
    for ivar in filemap.keys():
        data['mod_'+ivar]=np.full(len(data),np.nan)

    # list model files
    if method != 'netmatch':
        flist=dict()
        for ift in ftypes:
            flist[ift]=index_model_files(mod_start,mod_end,mod_basedir,mod_nam_fmt,mod_flen,ift,fdict[ift])

    if method == 'bin':
        data = _binmatch(data,flist,ftypes,filemap_r,omask,maskName,sdim)
    elif method == 'ferry':
        print('data is matched to mean of upper 3 model levels')
        data = _ferrymatch(data,flist,ftypes,filemap_r,omask,fdict)
    elif method == 'vvlZ':
        data = _interpvvlZ(data,flist,ftypes,filemap,filemap_r,omask,fdict,e3tvar)

    elif method == 'netmatch':
        data =  _netmatch(data,fid,filemap.keys(),omask,maskName=maskName)
    else:
        print('option '+method+' not written yet')
        return
    data.reset_index(drop=True,inplace=True)
    return data

def _gridHoriz(data,omask,navlon,navlat,wrapSearch,resetIndex=False):
    lmask=-1*(omask[0,0,:,:]-1)
    if wrapSearch:
        jj,ii = geo_tools.closestPointArray(data['Lon'].values,data['Lat'].values,navlon,navlat,
                                                        tol2=wrapTol,land_mask = lmask)
        data['j']=[-1 if np.isnan(mm) else int(mm) for mm in jj]
        data['i']=[-1 if np.isnan(mm) else int(mm) for mm in ii]
    else:
        data['j']=-1*np.ones((len(data))).astype(int)
        data['i']=-1*np.ones((len(data))).astype(int)
        for la,lo in np.unique(data.loc[:,['Lat','Lon']].values,axis=0):
            try:
                jj, ii = geo_tools.find_closest_model_point(lo, la, navlon,
                                            navlat, land_mask = lmask,checkTol=True)
            except:
                print('lo:',lo,'la:',la)
                raise
            if isinstance(jj,int):
                data.loc[(data.Lat==la)&(data.Lon==lo),['j','i']]=jj,ii
            else:
                print('(Lat,Lon)=',la,lo,' not matched to domain')
    data.drop(data.loc[(data.i==-1)|(data.j==-1)].index, inplace=True)
    if resetIndex==True:
        data.reset_index(drop=True,inplace=True)
    return data

def _interpvvlZ(data,flist,ftypes,filemap,filemap_r,tmask,fdict,e3tvar):
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
                data.loc[ind,['mod_'+ivar]]=np.mean(fid.variables[ivar][row['ih_'+ift],:3,row['j'],row['i']])
        #for ifind in np.unique(data.loc[:,['indf_'+ift]].values,axis=0):
        #    fid=nc.Dataset(flist[ift].loc[ifind[0],['paths']].values[0])
        #    idata=data.loc[data['indf_'+ift]==ifind[0]]
        #    for ih,iij,iii in np.unique(idata.loc[:,['ih_'+ift,'j','i']].values,axis=0):
        #        if (gridmask[0,0,iij,iii]==1):
        #            for ivar in filemap_r[ift]:
        #                data.loc[(data['indf_'+ift]==ifind[0])&(data['ih_'+ift]==ih)&(data['j']==iij)&(data['i']==iii),['mod_'+ivar]]=\
        #                                                np.mean(fid.variables[ivar][ih,:3,iij,iii])
        #    fid.close()
    return data

def _binmatch(data,flist,ftypes,filemap_r,gridmask,maskName='tmask',sdim=3):
    # loop through data, openening and closing model files as needed and storing model data
    if len(data)>5000:
        pprint=True
        lendat=len(data)
    else: 
        pprint= False
    data['k']=-1*np.ones((len(data))).astype(int)
    for ind, row in data.iterrows():
        if (pprint==True and ind%5000==0):
            print('progress: {}%'.format(ind/lendat*100))
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
            # find depth index if vars are 3d
            if sdim==3:
                ik=_getZInd_bin(row['Z'],fid[ift],maskName=maskName)
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

def _netmatch(data,fid,varlist,gridmask,maskName='tmask'):
    # match single file to all data
    if len(data)>5000:
        pprint=True
        lendat=len(data)
    else: 
        pprint= False
    for ind, row in data.iterrows():
            # find depth index
            ik=_getZInd_bin(row['Z'],fid,boundsFlag=True,maskName=maskName)
            # assign values for each var assoc with ift
            if (not np.isnan(ik)) and (gridmask[0,ik,row['j'],row['i']]==1):
                for ivar in varlist:
                    data.loc[ind,['mod_'+ivar]]=fid.variables[ivar][0,ik,row['j'],row['i']]
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

def _getZInd_bin(idt,ifid=None,boundsFlag=False,maskName='tmask'):
    if boundsFlag==True:
        if maskName=='tmask':
            with nc.Dataset('/results2/SalishSea/nowcast-green.201812/01jan16/SalishSea_1h_20160101_20160101_ptrc_T.nc') as ftemp:
                tlist=ftemp.variables['deptht_bounds'][:,:]
        elif maskName=='umask':
            with nc.Dataset('/results2/SalishSea/nowcast-green.201812/01jan16/SalishSea_1h_20160101_20160101_grid_U.nc') as ftemp:
                tlist=ftemp.variables['depthu_bounds'][:,:]
        elif maskName=='vmask':
            with nc.Dataset('/results2/SalishSea/nowcast-green.201812/01jan16/SalishSea_1h_20160101_20160101_grid_V.nc') as ftemp:
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

def index_model_files(start,end,basedir,nam_fmt,flen,ftype,tres):
    """
    See inputs for matchData above.
    outputs pandas dataframe containing columns 'paths','t_0', and 't_1'
    """
    if ftype not in ('ptrc_T','grid_T','grid_W','grid_U','grid_V','dia1_T','carp_T','None'):
        print('ftype={}, are you sure? (if yes, add to list)'.format(ftype))
    if tres==24:
        ftres='1d'
    else:
        ftres=str(int(tres))+'h'
    ffmt='%Y%m%d'
    dfmt='%d%b%y'
    wfmt='y%Ym%md%d'
    if nam_fmt=='nowcast':
        stencil='{0}/SalishSea_'+ftres+'_{1}_{1}_'+ftype+'.nc'
    elif nam_fmt=='long':
       stencil='**/SalishSea_'+ftres+'*'+ftype+'_{1}-{2}.nc'
    elif nam_fmt=='wind':
       stencil='ops_{3}.nc'
    else:
        raise Exception('nam_fmt '+nam_fmt+' is not defined')
    iits=start
    iite=iits+dt.timedelta(days=(flen-1))
    # check if start is a file start date and if not, try to identify the file including it
    nday=0
    while True:
        try:
            iifstr=glob.glob(basedir+stencil.format(iits.strftime(dfmt).lower(),
                    iits.strftime(ffmt),iite.strftime(ffmt),iits.strftime(wfmt)),recursive=True)[0]
            if nday>0:
                print('first file starts on ',iits)
            break # file has been found
        except IndexError:
            nday=nday+1
            iits=start-dt.timedelta(days=nday)
            iite=iits+dt.timedelta(days=(flen-1))
            if nday==flen:
                raise Exception('no file found including date '+str(start)+\
                        ' of form:\n '+basedir+stencil.format(iits.strftime(dfmt).lower(),
                        iits.strftime(ffmt),iite.strftime(ffmt),iits.strftime(wfmt)))
    ind=0
    inds=list()
    paths=list()
    t_0=list()
    t_n=list()
    while iits<=end:
        iite=iits+dt.timedelta(days=(flen-1))
        iitn=iits+dt.timedelta(days=flen)
        try:
            iifstr=glob.glob(basedir+stencil.format(iits.strftime(dfmt).lower(),
                    iits.strftime(ffmt),iite.strftime(ffmt),iits.strftime(wfmt)),recursive=True)[0]
        except IndexError:
            raise Exception('file does not exist:  '+basedir+stencil.format(iits.strftime(dfmt).lower(),
                iits.strftime(ffmt),iite.strftime(ffmt),iits.strftime(wfmt)))
        inds.append(ind)
        paths.append(iifstr)
        t_0.append(iits)
        t_n.append(iitn)
        iits=iitn
        ind=ind+1
    return pd.DataFrame(data=np.swapaxes([paths,t_0,t_n],0,1),index=inds,columns=['paths','t_0','t_n']) 


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
    SA=case([(CalcsTBL.Salinity_T0_C0_SA!=None, CalcsTBL.Salinity_T0_C0_SA)], else_=
             case([(CalcsTBL.Salinity_T1_C1_SA!=None, CalcsTBL.Salinity_T1_C1_SA)], else_=
             case([(CalcsTBL.Salinity_SA!=None, CalcsTBL.Salinity_SA)], else_= None)))
    CT=case([(CalcsTBL.Temperature_Primary_CT!=None, CalcsTBL.Temperature_Primary_CT)], else_=
             case([(CalcsTBL.Temperature_Secondary_CT!=None, CalcsTBL.Temperature_Secondary_CT)], else_=CalcsTBL.Temperature_CT))
    ZD=case([(ObsTBL.Depth!=None,ObsTBL.Depth)], else_= CalcsTBL.Z)
    if len(datelims)<2:
        qry=session.query(StationTBL.StartYear.label('Year'),StationTBL.StartMonth.label('Month'),
                      StationTBL.StartDay.label('Day'),StationTBL.StartHour.label('Hour'),
                      StationTBL.Lat,StationTBL.Lon,ZD.label('Z'),SA.label('SA'),CT.label('CT')).\
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
                      StationTBL.Lat,StationTBL.Lon,ZD.label('Z'),SA.label('SA'),CT.label('CT')).\
                select_from(StationTBL).join(ObsTBL,ObsTBL.StationTBLID==StationTBL.ID).\
                join(CalcsTBL,CalcsTBL.ObsTBLID==ObsTBL.ID).filter(and_(or_(StationTBL.StartYear>start_y,
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth>start_m),
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth==start_m, StationTBL.StartDay>=start_d)),
                                                                     or_(StationTBL.StartYear<end_y,
                                                                         and_(StationTBL.StartYear==start_y,StationTBL.StartMonth<start_m),
                                                                         and_(StationTBL.StartYear==start_y,StationTBL.StartMonth==start_m, StationTBL.StartDay<=start_d)),
                                                                    StationTBL.Lat>47-3/2.5*(StationTBL.Lon+123.5),
                                                                    StationTBL.Lat<47-3/2.5*(StationTBL.Lon+121),
                                                                    StationTBL.Include==True,ObsTBL.Include==True,CalcsTBL.Include==True))
    df1=pd.DataFrame(qry.all())
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
    JDFLocsTBL=Base.classes.JDFLocsTBL
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
                     ObsTBL.Pressure,ObsTBL.Depth,ObsTBL.Ammonium,ObsTBL.Ammonium_units,ObsTBL.Chlorophyll_Extracted,
                     ObsTBL.Chlorophyll_Extracted_units,ObsTBL.Nitrate_plus_Nitrite.label('N'),
                      ObsTBL.Silicate.label('Si'),ObsTBL.Silicate_units,SA.label('AbsSal'),CT.label('ConsT')).\
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
                     ObsTBL.Pressure,ObsTBL.Depth,ObsTBL.Ammonium,ObsTBL.Ammonium_units,ObsTBL.Chlorophyll_Extracted,
                     ObsTBL.Chlorophyll_Extracted_units,ObsTBL.Nitrate_plus_Nitrite.label('N'),
                      ObsTBL.Silicate.label('Si'),ObsTBL.Silicate_units,SA.label('AbsSal'),CT.label('ConsT')).\
                select_from(StationTBL).join(ObsTBL,ObsTBL.StationTBLID==StationTBL.ID).\
                join(CalcsTBL,CalcsTBL.ObsID==ObsTBL.ID).filter(and_(or_(StationTBL.StartYear>start_y,
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth>start_m),
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth==start_m, StationTBL.StartDay>=start_d)),
                                                                     or_(StationTBL.StartYear<end_y,
                                                                         and_(StationTBL.StartYear==end_y,StationTBL.StartMonth<end_m),
                                                                         and_(StationTBL.StartYear==end_y,StationTBL.StartMonth==end_m, StationTBL.StartDay<=end_d)),
                                                                    StationTBL.Lat>47-3/2.5*(StationTBL.Lon+123.5),
                                                                    StationTBL.Lat<47-3/2.5*(StationTBL.Lon+121)))#,
                                                                    #not_(and_(StationTBL.Lat>48.77,StationTBL.Lat<49.27,
                                                                    #          StationTBL.Lon<-123.43))))
    if excludeSaanich:
        df1=pd.DataFrame(qry.filter(not_(and_(StationTBL.Lat>48.47,StationTBL.Lat<48.67,
                                              StationTBL.Lon>-123.6,StationTBL.Lon<-123.43))).all())
    else:
        df1=pd.DataFrame(qry.all())
    df1['Z']=np.where(df1['Depth']>=0,df1['Depth'],-1.0*gsw.z_from_p(p=df1['Pressure'],lat=df1['Lat']))
    df1['dtUTC']=[dt.datetime(int(y),int(m),int(d))+dt.timedelta(hours=h) for y,m,d,h in zip(df1['Year'],df1['Month'],df1['Day'],df1['Hour'])]
    session.close()
    engine.dispose()
    return df1

def _lt0convert(arg):
    if arg=='<0':
        val=0.0
    else:
        val=pd.to_numeric(arg, errors='coerce',downcast=None)
    return float(val)

def loadPSF(datelims=(),loadChl=True,loadCTD=False):
    dfs=list()
    dfchls=list()
    if len(datelims)<2:
        datelims=(dt.datetime(2014,1,1),dt.datetime(2020,1,1))
    if loadCTD:
        ctddfs=dict()
    if datelims[0].year<2016:
        # load 2015
        f2015 = pd.read_excel('/ocean/eolson/MEOPAR/obs/PSFCitSci/All_Yrs_Nutrients_2018-01-31_EOEdit.xlsx',
                         sheet_name = '2015 N+P+Si',dtype={'date (dd/mm/yyyy)':str})
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
                         sheet_name = '2016 N+P',dtypes={'NO3+NO':str,'PO4':str},na_values=('nan','NaN','30..09'))
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
        f2016Si = pd.read_excel('/ocean/eolson/MEOPAR/obs/PSFCitSci/All_Yrs_Nutrients_2018-01-31_EOEdit.xlsx',sheet_name = '2016 SiO2')
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
                         sheet_name = '2017 N+P+Si',skiprows=3,dtypes={'Date (dd/mm/yyyy)':dt.date,'Time (Local)':dt.time,
                                                                      'NO3+NO':str,'PO4':str,'Si':str})
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
                                  sheet_name='avg-mean-cv%',skiprows=15,usecols=[1,3,4,5,7,9,11],names=['Date','Station','Time','Z0','Chl','Qflag','Phaeo'])
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
    df=df.loc[(df.dtUTC>=datelims[0])&(df.dtUTC<=datelims[1])].copy(deep=True)
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

def loadPSF2015():
    nutrients_2015 = pd.read_csv('/ocean/eolson/MEOPAR/obs/PSFCitSci/PSFbottledata2015_CN_edits_EOCor2.csv')
    data=nutrients_2015.loc[pd.notnull(nutrients_2015['date'])&
                        pd.notnull(nutrients_2015['Time'])&
                        pd.notnull(nutrients_2015['lat'])&
                        pd.notnull(nutrients_2015['lon'])].copy(deep=True)
    data['Lat']=data['lat']
    data['Lon']=data['lon']
    data['Z']=data['depth']
    ts=data['Time'].values
    ds=data['date'].values
    dts=[pytz.timezone('Canada/Pacific').localize(dt.datetime.strptime(ii+' '+jj,'%d-%m-%Y %I:%M:%S %p')).astimezone(pytz.utc).replace(tzinfo=None)
        for ii,jj in zip(ds,ts)]
    data['dtUTC']=dts
    return data

def loadHakai(datelims=(),loadCTD=False):
    if len(datelims)<2:
        datelims=(dt.datetime(1900,1,1),dt.datetime(2100,1,1))
    start_date=datelims[0]
    end_date=datelims[1]    

    f0 = pd.read_excel('/ocean/eolson/MEOPAR/obs/Hakai/Dosser20180911/2018-09-11_144804_HakaiData_nutrients.xlsx',
                     sheet_name = 'Hakai Data')
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

    fdata2=fdata.loc[(fdata['dtUTC']>start_date)&(fdata['dtUTC']<end_date)&(fdata['Z']>=0)&(fdata['Z']<440)&(fdata['Lon']<360)&(fdata['Lat']<=90)].copy(deep=True).reset_index()
    fdata2.drop(['no','event_pk','Date','Sampling Bout','Latitude','Longitude','index','Gather Lat','Gather Long', 'Pressure Transducer Depth (m)',
                'Filter Type','dloc','Collected','Line Out Depth','Replicate Number','Work Area','Survey','Site ID','NO2+NO3 Flag','SiO2 Flag'],axis=1,inplace=True)    
    return fdata2

def stats(obs0,mod0):
    obs0=_deframe(obs0)
    mod0=_deframe(mod0)
    iii=np.logical_and(~np.isnan(obs0),~np.isnan(mod0))
    obs=obs0[iii]
    mod=mod0[iii]
    N=len(obs)
    modmean=np.mean(mod)
    obsmean=np.mean(obs)
    bias=modmean-obsmean
    RMSE=np.sqrt(np.sum((mod-obs)**2)/N)
    WSS=1.0-np.sum((mod-obs)**2)/np.sum((np.abs(mod-obsmean)+np.abs(obs-obsmean))**2)
    return N, modmean, obsmean, bias, RMSE, WSS

def varvarScatter(ax,df,obsvar,modvar,colvar,vmin=0,vmax=0,cbar=False,cm=cmo.cm.thermal,args={}):
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
    cols=('darkslateblue','royalblue','skyblue','mediumseagreen','darkseagreen','goldenrod','coral','tomato','firebrick','mediumvioletred','magenta')):
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
            ll=u'{} $<$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii],label=ll)
            ps.append(p0)
        # between min and max:
        for ii in range(1,len(sepvals)):
            iii=np.logical_and(sep0<sepvals[ii],sep0>=sepvals[ii-1])
            if np.sum(iii)>0:
                #ll=u'{} {} \u2264 {} < {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                ll=u'{} {} $\leq$ {} $<$ {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii],label=ll)
                ps.append(p0)
        # greater than max:
        iii=sep0>=sepvals[ii]
        if np.sum(iii)>0:
            #ll=u'{} \u2265 {} {}'.format(lname,sepvals[ii],sepunits).strip()
            ll=u'{} $\geq$ {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii+1],label=ll)
            ps.append(p0)
    return ps


def _deframe(x):
    if isinstance(x,pd.Series) or isinstance(x,pd.DataFrame):
        x=x.values.flatten()
    return x

def utc_to_pac(timeArray):
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
