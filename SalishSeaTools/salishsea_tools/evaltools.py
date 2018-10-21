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
    maskName='tmask'
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

    """
    # check that required columns are in dataframe:
    if not set(('dtUTC','Lat','Lon','Z')) <= set(data.keys()):
        raise Exception('{} missing from data'.format([el for el in set(('dtUTC','Lat','Lon','Z'))-set(data.keys())],'%s'))

    ## check that entries are minimal and consistent:
    #fkeysVar=list(filemap.keys())
    #for ikey in fkeysVar:
    #    if ikey not in set(varmap.values()):
    #        filemap.pop(ikey) 
    #if len(set(varmap.values())-set(filemap.keys()))>0:
    #    print('Error: file(s) missing from filemap:',set(varmap.values())-set(filemap.keys()))
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
    data=data.dropna(how='any',subset=['dtUTC','Lat','Lon','Z']) #.dropna(how='all',subset=[*varmap.keys()])
    data['j']=-1*np.ones((len(data))).astype(int)
    data['i']=-1*np.ones((len(data))).astype(int)
    with nc.Dataset(meshPath) as fmesh:
        omask=np.copy(fmesh.variables[maskName])
        lmask=-1*(omask[0,0,:,:]-1)
        for la,lo in np.unique(data.loc[:,['Lat','Lon']].values,axis=0):
            jj, ii = geo_tools.find_closest_model_point(lo, la, fmesh.variables['nav_lon'], fmesh.variables['nav_lat'], 
                                                        land_mask = lmask)
            if isinstance(jj,int):
                data.loc[(data.Lat==la)&(data.Lon==lo),['j','i']]=jj,ii
            else:
                print('(Lat,Lon)=',la,lo,' not matched to domain')
    data.drop(data.loc[(data.i==-1)&(data.j==-1)].index, inplace=True)
    data=data.sort_values(by=['dtUTC','Lat','Lon','Z'])
    data.reset_index(drop=True,inplace=True)

    # set up columns to accept model values
    for ivar in filemap.keys():
        data['mod_'+ivar]=np.full(len(data),np.nan)

    # list model files
    flist=dict()
    for ift in ftypes:
        flist[ift]=index_model_files(mod_start,mod_end,mod_basedir,mod_nam_fmt,mod_flen,ift,fdict[ift])

    if method == 'bin':
        data = _binmatch(data,flist,ftypes,filemap_r,omask)
    else:
        print('option '+method+' not written yet')
        return
    return data

def _binmatch(data,flist,ftypes,filemap_r,gridmask):
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
            if gridmask[0,ik,row['j'],row['i']]==1:
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



def loadDFO(basedir='/ocean/eolson/MEOPAR/obs/DFOOPDB/', dbname='DFO_OcProfDB.sqlite',
        datelims=()):
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
    
    if len(datelims)<2:
        qry=session.query(StationTBL.StartYear.label('Year'),StationTBL.StartMonth.label('Month'),
                      StationTBL.StartDay.label('Day'),StationTBL.StartHour.label('Hour'),
                      StationTBL.Lat,StationTBL.Lon,
                     ObsTBL.Pressure,ObsTBL.Depth,ObsTBL.Ammonium,ObsTBL.Ammonium_units,ObsTBL.Chlorophyll_Extracted,
                     ObsTBL.Chlorophyll_Extracted_units,ObsTBL.Nitrate_plus_Nitrite.label('N'),
                      ObsTBL.Silicate.label('Si'),ObsTBL.Silicate_units,SA.label('AbsSal'),Tem.label('T'),TemUnits.label('T_units')).\
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
                      ObsTBL.Silicate.label('Si'),ObsTBL.Silicate_units,SA.label('AbsSal'),Tem.label('T'),TemUnits.label('T_units')).\
                select_from(StationTBL).join(ObsTBL,ObsTBL.StationTBLID==StationTBL.ID).\
                join(CalcsTBL,CalcsTBL.ObsID==ObsTBL.ID).filter(and_(or_(StationTBL.StartYear>start_y,
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth>start_m),
                                                                         and_(StationTBL.StartYear==start_y, StationTBL.StartMonth==start_m, StationTBL.StartDay>=start_d)),
                                                                     or_(StationTBL.StartYear<end_y,
                                                                         and_(StationTBL.StartYear==start_y,StationTBL.StartMonth<start_m),
                                                                         and_(StationTBL.StartYear==start_y,StationTBL.StartMonth==start_m, StationTBL.StartDay<=start_d)),
                                                                    StationTBL.Lat>47-3/2.5*(StationTBL.Lon+123.5),
                                                                    StationTBL.Lat<47-3/2.5*(StationTBL.Lon+121)))
    df1=pd.DataFrame(qry.all())
    df1['Z']=np.where(df1['Depth']>=0,df1['Depth'],-1.0*gsw.z_from_p(p=df1['Pressure'],lat=df1['Lat']))
    df1['dtUTC']=[dt.datetime(int(y),int(m),int(d))+dt.timedelta(hours=h) for y,m,d,h in zip(df1['Year'],df1['Month'],df1['Day'],df1['Hour'])]
    session.close()
    engine.dispose()
    return df1


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
            ll=u'{} < {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii],label=ll)
            ps.append(p0)
        # between min and max:
        for ii in range(1,len(sepvals)):
            iii=np.logical_and(sep0<sepvals[ii],sep0>=sepvals[ii-1])
            if np.sum(iii)>0:
                ll=u'{} {} \u2264 {} < {} {}'.format(sepvals[ii-1],sepunits,lname,sepvals[ii],sepunits).strip()
                p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii],label=ll)
                ps.append(p0)
        # greater than max:
        iii=sep0>=sepvals[ii]
        if np.sum(iii)>0:
            ll=u'{} \u2265 {} {}'.format(lname,sepvals[ii],sepunits).strip()
            p0,=ax.plot(obs0[iii],mod0[iii],'.',color=cols[ii+1],label=ll)
            ps.append(p0)
    return ps


def _deframe(x):
    if isinstance(x,pd.Series) or isinstance(x,pd.DataFrame):
        x=x.values.flatten()
    return x

def printstats(datadf,obsvar,modvar):
    N, modmean, obsmean, bias, RMSE, WSS = stats(datadf.loc[:,[obsvar]],datadf.loc[:,[modvar]])
    print('  N: {}\n  bias: {}\n  RMSE: {}\n  WSS: {}'.format(N,bias,RMSE,WSS))
    return
