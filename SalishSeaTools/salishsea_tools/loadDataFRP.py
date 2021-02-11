import numpy as np
import pandas as pd
from scipy import signal as ssig
from scipy import stats as spst
import os
import re
import string
from salishsea_tools import geo_tools
import netCDF4 as nc

# list CTD cnv files associated with cast numbers 
cnvlist19={1:'fraser2017101.cnv',
        2:'fraser2017102.cnv',
        3:'fraser2017103.cnv',
        4:'fraser2017104.cnv',
        5:'fraser2017105.cnv',
        6:'fraser2017106.cnv',
        7:'fraser2017107.cnv',
        8:'fraser2017108.cnv',
        9:'fraser2017109.cnv',
        10:'fraser2017110.cnv',
        11:'fraser2017111.cnv',
        12:'fraser2017112.cnv',
        13:'fraser2017113.cnv',
        14.1:'fraser2017114.cnv',
        14.2:'fraser2017114.cnv',
        15:'fraser2017115.cnv',
        16:'fraser2017116.cnv',
        17:'fraser2017117.cnv',
        18:'fraser2017118.cnv',
        19:'fraser2017119.cnv',
        20:'fraser2017120.cnv',
        21:'fraser2017121.cnv',
        22:'fraser2017122.cnv',
        23:'fraser2017123.cnv',
        24:'fraser2017124.cnv'}

cnvlist25={1:'fraser2017001.cnv',
        2:'fraser2017002.cnv',
        3:'fraser2017003.cnv',
        4:'fraser2017004.cnv',
        5:'fraser2017005.cnv',
        6:'fraser2017006.cnv',
        7:'fraser2017007.cnv',
        8:'fraser2017008.cnv',
        9:'fraser2017009.cnv',
        10:'fraser2017010.cnv',
        11:'fraser2017011.cnv',
        12:'fraser2017012.cnv',
        13:'fraser2017013.cnv',
        14.1:'fraser2017014.cnv',
        14.2:'fraser2017014.cnv',
        15:'fraser2017015.cnv',
        16:'fraser2017016.cnv',
        17:'fraser2017017.cnv',
        18:'fraser2017018.cnv',
        19:'fraser2017019.cnv',
        20:'fraser2017020.cnv',
        21:'fraser2017021.cnv',
        22:'fraser2017022.cnv',
        23:'fraser2017023.cnv',
        24:'fraser2017024.cnv'}

class Cast:
    def __init__(self,fpath):
        mSta,mLat,mLon,df=readcnv(fpath)
        self.sta=mSta
        self.lat=mLat
        self.lon=mLon
        self.df=df
        self.source=fpath

class zCast:
    def __init__(self,updf,downdf):
        self.uCast=updf
        self.dCast=downdf

class rawCast:
    def __init__(self):
        self.uCast=dict()
        self.dCast=dict()

class dataPair:
    def __init__(self,zval,varval):
        self.z=zval
        self.val=varval

def fmtVarName(strx):
    """ transform string into one that meets python naming conventions"""
    vName=re.sub('[^a-zA-Z0-9_\-\s/]','',strx.strip())
    vName=re.sub('[\s/]','_',vName)
    vName=re.sub('-','_',vName)
    if re.match('[0-9]',vName):
        vName='_'+vName
    return vName

def rolling_window(a, window):
    # source: http://www.rigtorp.se/2011/01/01/rolling-statistics-numpy.html
    # use example: np.mean(rolling_window(x, 3), -1)
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

def rolling_window_padded(a,window):
    # extend rolling window to be same lenth as input array by duplicating first and last values
    # even values not symmetric
    test=rolling_window(a,window)
    while window>1:
        if window%2==0:
            test=np.concatenate(([test[0,:]],test),axis=0)
        else:
            test=np.concatenate((test,[test[-1,:]]),axis=0)
        window+=-1
    return test

def amp(var,dim=0):
    return np.nanmax(var,dim)-np.nanmin(var,dim)

def turbQC(x):
    # turbidity sensor produced erroneous zero readings interspersed with real data when too close to surface
    # remove suspect values from analysis
    # - median filter alone was not enough

    # remove a point if the max-min of the surrounding 5 point window 
    # is greater than 1/3 the maximum turbidity value of the cast 
    # (remove data within 5 points of a large jump)
    ii1=amp(rolling_window_padded(x,5),-1)>.33*np.nanmax(x)
    # remove data within 5 points of a near-zero turbidity value
    ii2=np.nanmin(rolling_window_padded(x,5),-1)<.3
    y=np.copy(x)
    y[np.logical_or(ii1,ii2,)]=np.nan
    y=ssig.medfilt(y,3) 
    return y

def readcnv(fpath):
    alphnumlist=list(string.ascii_letters)+list(string.digits)
    # define regexes for reading headers:
    reSta=re.compile('(?<=\*\*\sStation:)\s?([0-9])+\s?') # assumes numeric station identifiers
    reLat=re.compile('(?<=\*\*\sLatitude\s=)\s?([\-0-9\.]+)\s([\-\.0-9]+)\s?([NS])')
    reLon=re.compile('(?<=\*\*\sLongitude\s=)\s?([\-0-9\.]+)\s([\-\.0-9]+)\s?([EW])')
    # start_time = May 08 2002 09:39:10
    reST=re.compile('(?<=\#\sstart_time\s=).*')
    #reTZ=re.compile('(?<=\*\*\s...\s\(Time\)\s=).*')
    #reCr=re.compile('(?<=\*\*\sCruise:).*')
    reNam=re.compile('(?<=\#\sname\s)([0-9]+)\s=\s(.*)\:\s?(.*)\s?')
    
    # define regex for finding searching:
    spStart=re.compile('^\s*[0-9]') # starts with space characters followed by digit

    headers=list()
    #lineno=0
    mSta=None
    mLat=None
    mLon=None
    with open(fpath, 'rt', encoding="ISO-8859-1") as f:
        for fline in f:
            if fline.startswith('**'):
                if reSta.search(fline):
                    mSta=reSta.search(fline).groups() 
                if reLat.search(fline):
                    mLat=reLat.search(fline).groups()
                if reLon.search(fline):
                    mLon=reLon.search(fline).groups()
            elif reNam.search(fline):
                headers.append(fmtVarName(reNam.search(fline).groups(1)[1]))
            elif fline.startswith('*END*'):
                break
            #lineno+=1
        #still in with file open
        df=pd.read_csv(f,delim_whitespace=True,names=headers)
    # file closed
    
    return mSta,mLat,mLon,df

def bindepth(inP,inV,edges,targets=[],prebin=False):
    # calculate depth-associated variables
    # 1st calculate bin averages of depth and variable
    # then use np interp to estimate at-grid-point values
    # edges must be monotonically increasing
    if prebin==True:
        newP,newV=bindepth(inP,inV,np.arange(edges[0],edges[-1],.05),prebin=False)
        inP=newP
        inV=newV
    inP=inP[~np.isnan(inV)]
    inV=inV[~np.isnan(inV)]
    binned=np.digitize(inP,edges)
    Pa=np.empty(len(edges)-1)
    Va=np.empty(len(edges)-1)
    if len(targets) == 0:
        Pi=.5*(edges[:-1]+edges[1:])
    else:
        Pi=targets[:(len(edges)-1)]
    Vi=np.empty(len(edges)-1)
    for jj in range(1,len(edges)):
        ll=(binned==jj) #&(~np.isnan(inV))
        if np.sum(ll)>0:
            Pa[jj-1]=np.mean(inP[ll])
            Va[jj-1]=np.mean(inV[ll])
        else:
            Pa[jj-1]=np.nan
            Va[jj-1]=np.nan
    # linearly extrapolate some values, but not beyond range of original data
    pnew=Pa[0]-(Pa[1]-Pa[0])
    vnew=Va[0]-(Va[1]-Va[0])
    Pa=np.concatenate(([pnew],Pa))
    Va=np.concatenate(([vnew],Va))
    Vi=np.interp(Pi,Pa[~np.isnan(Va)],Va[~np.isnan(Va)],right=np.nan,left=np.nan)
    Vi[Pi>np.max(inP)]=np.nan
    Vi[Pi<np.min(inP)]=np.nan
    return Pi, Vi

def cXfromX(X):
    X=np.array(X)
    X[np.isnan(X)]=-5
    Y=np.nan*X
    iii=(X>0)&(X<100)
    Y[iii]=-np.log(X[iii]/100.0)/.25
    return Y

def turbReg(m,Cx,fl):
    return np.maximum(0.0,m[0]*Cx-m[1]*fl-m[2])

def turbFit(df0):
    # calculate conversion factor for sb19 ctd turbidity to ALS bottle turbidity
    # force through (0,0)
    x=df0.loc[(df0.ALS_Turb_NTU>0)&(df0.sb19Turb_uncorrected>0)]['sb19Turb_uncorrected'].values
    x=x[:,np.newaxis]
    y=df0.loc[(df0.ALS_Turb_NTU>0)&(df0.sb19Turb_uncorrected>0)]['ALS_Turb_NTU']
    tinv=np.linalg.lstsq(x,y,rcond=None)[0]
    tcor=1.0/tinv
    return tcor

def loadDataFRP_init(exp='all'):
    if exp not in {'exp1', 'exp2', 'exp3', 'all'}:
        print('option exp='+exp+' is not defined.')
        raise
    with open('/ocean/shared/SalishSeaCastData/FRPlume/stationsDigitizedFinal.csv','r') as fa:
    	df0_a=pd.read_csv(fa,header=0,na_values='None')
    with open('/ocean/shared/SalishSeaCastData/FRPlume/util/stationsDigitized_ancillary.csv','r') as fb:
    	df0_b=pd.read_csv(fb,header=0,na_values='None')
    df0=pd.merge(df0_a,df0_b,how='left',on=['Station','Date'])

    # if values present, calculate correction factor for sb19 turbidity (divide sb19 turbidity by tcor)
    # fit true turb to observed turb
    # calculate here while all values present
    if np.sum(df0.sb19Turb_uncorrected>0)>0:
        tcor=turbFit(df0)
    else:
        tcor=np.nan
    if exp=='exp1':
        df0=df0.drop(df0.index[df0.Date != 20170410])
    elif exp=='exp2':
        df0=df0.drop(df0.index[df0.Date != 20170531])
    elif exp=='exp3':
        df0=df0.drop(df0.index[df0.Date != 20171101])

    basedir1='/ocean/shared/SalishSeaCastData/FRPlume/ctd/20170410/'
    basedir2='/ocean/shared/SalishSeaCastData/FRPlume/ctd/20170531/'
    basedir3='/ocean/shared/SalishSeaCastData/FRPlume/ctd/20171101/'
    dir19='19-4561/4_derive'
    dir25='25-0363/4_derive'
    dir19T10='19-4561/4b_deriveTEOS10'
    dir25T10='25-0363/4a_deriveTEOS10'
    
    clist=[]
    if (exp=='exp1' or exp=='all'):
        clist = clist + list(range(1,10))
    if (exp=='exp2' or exp=='all'):
        clist = clist + [10,11,12,13,14.1,14.2,15,16,17,18]
    if (exp=='exp3' or exp=='all'):
        clist = clist + list(range(19,25))

    fpath19=dict()
    fpath25=dict()
    for ii in clist:
        if ii<10:
            fpath19[ii]=os.path.join(basedir1,dir19T10,cnvlist19[ii])
            fpath25[ii]=os.path.join(basedir1,dir25T10,cnvlist25[ii])
        elif ii<19:
            fpath19[ii]=os.path.join(basedir2,dir19T10,cnvlist19[ii])
            fpath25[ii]=os.path.join(basedir2,dir25T10,cnvlist25[ii])
        else:
            fpath19[ii]=os.path.join(basedir3,dir19T10,cnvlist19[ii])
            fpath25[ii]=os.path.join(basedir3,dir25T10,cnvlist25[ii])
        
    cast19=dict()
    cast25=dict()
    for ii in clist:
        cast19[ii]=Cast(fpath19[ii])
        cast25[ii]=Cast(fpath25[ii])
    return df0, clist, tcor, cast19, cast25


def loadDataFRP(exp='all',sel='narrow',dp=1.0):
    if exp not in {'exp1', 'exp2', 'all'}:
        print('option exp='+exp+' is not defined.')
        raise
    if sel not in {'narrow', 'wide'}:
        print('option sel='+sel+' is not defined.')
        raise
    df0, clist, tcor, cast19, cast25 = loadDataFRP_init(exp=exp)
    parDZ=.78
    xmisDZ=.36
    turbDZ=.67
    pshiftdict={'gsw_ctA0':0.0,'gsw_srA0':0.0,'xmiss':xmisDZ,'seaTurbMtr':turbDZ,'par':parDZ,
                'wetStar':0.0,'sbeox0ML_L':0.0,'seaTurbMtrnoQC':turbDZ}

    zCasts=dict()
    for nn in clist:
        ip=np.argmax(cast25[nn].df['prSM'].values)
        ilag=df0.loc[df0.Station==nn,'ishift_sub19'].values[0]
        pS_pr=df0.loc[df0.Station==nn,'pS_pr'].values[0]
        pE_pr=df0.loc[df0.Station==nn,'pE_pr'].values[0]
        pS_tur=df0.loc[df0.Station==nn,'pStart25'].values[0]
        pE_tur=df0.loc[df0.Station==nn,'pEnd25'].values[0]
        if sel=='narrow':
            pS=pS_tur
            pE=pE_tur
            prebin=False
        elif sel=='wide':
            pS=pS_pr
            pE=pE_pr
            prebin=True
        pmax=cast25[nn].df.loc[ip,'prSM']
        edges=np.arange(dp/2,pmax+dp,dp)
        #edges=np.arange(0,pmax+dp,dp)
        dCast=pd.DataFrame()
        uCast=pd.DataFrame()
        
        cast19[nn].df['seaTurbMtrnoQC']=cast19[nn].df['seaTurbMtr']
        cast19[nn].df['seaTurbMtr']=turbQC(cast19[nn].df['seaTurbMtr'])

        def makeVcol(incast_p,outcast,var,i0,i1,incast_v=None):
            # incast_p: [cast25[nn]] cast to get pressure from; also used for var unless incast_v specified
            # outcast: [dCast or uCast] cast to save resulting aligned data to
            # i0, i1: [pS:ip/ip:pE] starting and ending indices for data to include relative to incast_p
            # var: variable name to extract
            # incast_v [cast19[nn]] if variables are from sbe19, specify that cast; otherwise get variable from incast_p (25)
            # vplag: ilag to align sbe19 to sbe25 in case where var is from sbe19; defaults to 0 for sbe25
            # NOTE: dataframes are mutable; changes to outcast propagate to its input df
            if incast_v is None:
                incast_v=incast_p
                vplag=0
            else:
                vplag=ilag
            inP=incast_p.df.loc[i0:i1]['prSM'].values-pshiftdict[var] # p
            inV=incast_v.df.loc[(i0+vplag):(i1+vplag)][var].values # var
            if sel=='wide':
                inV[inP<.1]=np.nan
            p, out=bindepth(inP,inV,edges,prebin=prebin)
            if len(outcast) == 0: # pressure not added yet
                outcast['prSM']=p
            outcast[var]=out
            return 

        # fix first 2 casts for which sb25 pump did not turn on. use sb19
        if nn==1 or nn==2:
            ##xmiss: xmis25=1.14099414691*xmis19+-1.6910134322
            cast19[nn].df['xmis']=1.14099414691*cast19[nn].df['CStarTr0']-1.6910134322 # down var
            for var in ('gsw_ctA0','gsw_srA0','xmiss'):
                #downcast
                makeVCol(cast25[nn],dCast,var,pS,ip,incast_v=cast19[nn])
                #upcast
                makeVCol(cast25[nn],uCast,var,ip,pE,incast_v=cast19[nn]) 
            makeVcol(cast25[nn],dCast,'par',pS,ip)
            makeVcol(cast25[nn],uCast,'par',ip,pE)
            uCast['wetStar']=np.nan
            dCast['wetStar']=np.nan
            uCast['sbeox0ML_L']=np.nan
            dCast['sbeox0ML_L']=np.nan
        else:
            for var in ('gsw_ctA0','gsw_srA0','xmiss','par','wetStar','sbeox0ML_L'):
                if not nn==14.2:
                    #downcast
                    makeVcol(cast25[nn],dCast,var,pS,ip)
                else:# special case where there is no downcast
                    if len(dCast)==0: # pressure not added yet
                        dCast=pd.DataFrame(np.nan*np.ones(10),columns=['prSM'])
                    dCast[var]=np.nan*np.ones(10)
                if not nn==14.1:
                    #upcast    
                    makeVCol(cast25[nn],uCast,var,ip,pE)
                else:# special case where there is no upcast
                    if len(dCast)==0: # pressure not added yet
                        uCast=pd.DataFrame(np.nan*np.ones(10),columns=['prSM'])
                    uCast[var]=np.nan*np.ones(10)
        if not nn==14.2:
            #turbidity downcast
            makeVCol(cast25[nn],dCast,'seaTurbMtr',pS,ip,incast_v=cast19[nn])
            makeVCol(cast25[nn],dCast,'seaTurbMtrnoQC',pS,ip,incast_v=cast19[nn])
            dCast['turb']=dCast['seaTurbMtr']*1.0/tcor
        else: # special case where there is no downcast
            dCast['turb']=np.nan*np.ones(10)
        if not nn==14.1:
            #turbidity upcast
            makeVCol(cast25[nn],uCast,'seaTurbMtr',ip,pE,incast_v=cast19[nn])
            makeVCol(cast25[nn],uCast,'seaTurbMtrnoQC',ip,pE,incast_v=cast19[nn])
            uCast['turb']=uCast['seaTurbMtr']*1.0/tcor
        else: # special case where there is no upcast
            uCast['turb']=np.nan*np.ones(10)

        zCasts[nn]=zCast(uCast,dCast)

    return df0, zCasts

def loadDataFRP_raw(exp='all',sel='narrow',meshPath='/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702.nc'):
    import gsw # use to convert p to z
    if exp not in {'exp1', 'exp2', 'exp3', 'all'}:
        print('option exp='+exp+' is not defined.')
        raise
    if sel not in {'narrow', 'wide'}:
        print('option sel='+sel+' is not defined.')
        raise
    df0, clist, tcor, cast19, cast25 = loadDataFRP_init(exp=exp)
    
    zCasts=dict()
    for nn in clist:
        zCasts[nn]=rawCast()
        ip=np.argmax(cast25[nn].df['prSM'].values)
        ilag=df0.loc[df0.Station==nn,'ishift_sub19'].values[0]
        pS_pr=df0.loc[df0.Station==nn,'pS_pr'].values[0]
        pE_pr=df0.loc[df0.Station==nn,'pE_pr'].values[0]
        pS_tur=df0.loc[df0.Station==nn,'pStart25'].values[0]
        pE_tur=df0.loc[df0.Station==nn,'pEnd25'].values[0]
        if sel=='narrow':
            pS=pS_tur
            pE=pE_tur
        elif sel=='wide':
            pS=pS_pr
            pE=pE_pr

        parDZ=.78
        xmisDZ=.36
        turbDZ=.67
        zshiftdict={'gsw_ctA0':0.0,'gsw_srA0':0.0,'xmiss':xmisDZ,'seaTurbMtr':turbDZ,'par':parDZ,
                    'wetStar':0.0,'sbeox0ML_L':0.0}
        for var in ('gsw_ctA0','gsw_srA0','xmiss','par','wetStar','sbeox0ML_L'):
            if not nn==14.2:
                #downcast
                inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0])-zshiftdict[var] # down z
                inV=cast25[nn].df.loc[pS:ip][var].values # down var
                if sel=='wide':
                    inV[inP<.1]=np.nan
                zCasts[nn].dCast[var]=dataPair(inP,inV)
            else:# special case where there is no downcast
                zCasts[nn].dCast[var]=dataPair(np.nan,np.nan)
            if not nn==14.1:
                #upcast    
                inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0])-zshiftdict[var] # down z
                inV=cast25[nn].df.loc[ip:pE][var].values # down var
                if sel=='wide':
                    inV[inP<.1]=np.nan
                zCasts[nn].uCast[var]=dataPair(inP,inV)
            else:# special case where there is no upcast
                zCasts[nn].uCast[var]=dataPair(np.nan,np.nan)
        if not nn==14.2:
            #turbidity downcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0])-turbDZ # down z
            inV0=cast19[nn].df.loc[(pS+ilag):(ip+ilag)]['seaTurbMtr'].values # down var
            if sel=='wide':
                # additional QC for broader data selection
                ii1=amp(rolling_window_padded(inV0,5),-1)>.5*np.nanmax(inV0)
                # get rid of near-zero turbidity values; seem to be dropped signal
                ii2=np.nanmin(rolling_window_padded(inV0,5),-1)<.3
                inV0[np.logical_or(ii1,ii2)]=np.nan
            inV=ssig.medfilt(inV0,3) # down var
            if sel=='wide': # exclude above surface data
                with np.errstate(invalid='ignore'):
                    inV[inP<.1]=np.nan
            zCasts[nn].dCast['turb_uncor']=dataPair(inP,inV)
            zCasts[nn].dCast['turb']=dataPair(inP,inV*1.0/tcor)
        else: # special case where there is no downcast
            zCasts[nn].dCast['turb_uncor']=dataPair(np.nan,np.nan)
            zCasts[nn].dCast['turb']=dataPair(np.nan,np.nan)
        if not nn==14.1:
            #turbidity upcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0])-turbDZ # up z
            inV0=cast19[nn].df.loc[(ip+ilag):(pE+ilag)]['seaTurbMtr'].values # up var
            if sel=='wide':
                # additional QC for broader data selection
                ii1=amp(rolling_window_padded(inV0,5),-1)>.5*np.nanmax(inV0)
                # get rid of near-zero turbidity values; seem to be dropped signal
                ii2=np.nanmin(rolling_window_padded(inV0,5),-1)<.3
                inV0[np.logical_or(ii1,ii2)]=np.nan
            inV=ssig.medfilt(inV0,3) # down var
            if sel=='wide': # exclude above surface data
                with np.errstate(invalid='ignore'):
                    inV[inP<.1]=np.nan
            zCasts[nn].uCast['turb_uncor']=dataPair(inP,inV)
            zCasts[nn].uCast['turb']=dataPair(inP,inV*1.0/tcor)
        else: # special case where there is no upcasts
            zCasts[nn].uCast['turb_uncor']=dataPair(np.nan,np.nan)
            zCasts[nn].uCast['turb']=dataPair(np.nan,np.nan)

    # fix first 2 casts for which sb25 pump did not turn on. use sb19
    if (exp=='exp1' or exp=='all'):
        for nn in range(1,3):

            ip=np.argmax(cast25[nn].df['prSM'].values)
            ilag=df0.loc[df0.Station==nn,'ishift_sub19'].values[0]
            pS_pr=df0.loc[df0.Station==nn,'pS_pr'].values[0]
            pE_pr=df0.loc[df0.Station==nn,'pE_pr'].values[0]
            pS_tur=df0.loc[df0.Station==nn,'pStart25'].values[0]
            pE_tur=df0.loc[df0.Station==nn,'pEnd25'].values[0]
            if sel=='narrow':
                pS=pS_tur
                pE=pE_tur
            elif sel=='wide':
                pS=pS_pr
                pE=pE_pr

            ##temperature
            #downcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0]) # down z
            inV=cast19[nn].df.loc[(pS+ilag):(ip+ilag)]['gsw_ctA0'].values # down var
            if sel=='wide':
                inV[inP<.1]=np.nan
            zCasts[nn].dCast['gsw_ctA0']=dataPair(inP,inV)
            #upcast    
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0]) # up z
            inV=cast19[nn].df.loc[(ip+ilag):(pE+ilag)]['gsw_ctA0'].values # up var
            if sel=='wide':
                inV[inP<.1]=np.nan
            zCasts[nn].uCast['gsw_ctA0']=dataPair(inP,inV)

            ##sal
            #downcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0]) # down z
            inV=cast19[nn].df.loc[(pS+ilag):(ip+ilag)]['gsw_srA0'].values # down var
            if sel=='wide':
                inV[inP<.1]=np.nan
            zCasts[nn].dCast['gsw_srA0']=dataPair(inP,inV)
            #upcast    
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0]) # up z
            inV=cast19[nn].df.loc[(ip+ilag):(pE+ilag)]['gsw_srA0'].values # up var
            if sel=='wide':
                inV[inP<.1]=np.nan
            zCasts[nn].uCast['gsw_srA0']=dataPair(inP,inV)

            ##xmiss: xmis25=1.14099414691*xmis19+-1.6910134322
            #downcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0])-xmisDZ # down z
            inV=1.14099414691*cast19[nn].df.loc[(pS+ilag):(ip+ilag)]['CStarTr0'].values-1.6910134322 # down var
            if sel=='wide':
                inV[inP<.1]=np.nan
            zCasts[nn].dCast['xmiss']=dataPair(inP,inV)
            #upcast    
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'].values[0])-xmisDZ # up p
            inV=1.14099414691*cast19[nn].df.loc[(ip+ilag):(pE+ilag)]['CStarTr0'].values-1.6910134322 # up var
            if sel=='wide':
                inV[inP<.1]=np.nan
            zCasts[nn].dCast['wetStar']=dataPair(np.nan,np.nan)
            zCasts[nn].uCast['wetStar']=dataPair(np.nan,np.nan)
            zCasts[nn].dCast['sbeox0ML_L']=dataPair(np.nan,np.nan)
            zCasts[nn].uCast['sbeox0ML_L']=dataPair(np.nan,np.nan)

    return df0, zCasts

def loadDataFRP_SSGrid(exp='all',sel='narrow',meshPath='/ocean/eolson/MEOPAR/NEMO-forcing/grid/mesh_mask201702.nc'):
    import gsw # only in this function; use to convert p to z
    if exp not in {'exp1', 'exp2', 'all'}:
        print('option exp='+exp+' is not defined.')
        raise
    if sel not in {'narrow', 'wide'}:
        print('option sel='+sel+' is not defined.')
        raise
    df0, clist, tcor, cast19, cast25 = loadDataFRP_init(exp=exp)
    
    # load mesh
    mesh=nc.Dataset(meshPath,'r')
    tmask=mesh.variables['tmask'][0,:,:,:]
    gdept=mesh.variables['gdept_0'][0,:,:,:]
    gdepw=mesh.variables['gdepw_0'][0,:,:,:]
    nav_lat=mesh.variables['nav_lat'][:,:]
    nav_lon=mesh.variables['nav_lon'][:,:]
    mesh.close()

    zCasts=dict()
    for nn in clist:
        ip=np.argmax(cast25[nn].df['prSM'].values)
        ilag=df0.loc[df0.Station==nn,'ishift_sub19'].values[0]
        pS_pr=df0.loc[df0.Station==nn,'pS_pr'].values[0]
        pE_pr=df0.loc[df0.Station==nn,'pE_pr'].values[0]
        pS_tur=df0.loc[df0.Station==nn,'pStart25'].values[0]
        pE_tur=df0.loc[df0.Station==nn,'pEnd25'].values[0]
        if sel=='narrow':
            pS=pS_tur
            pE=pE_tur
            prebin=False
        elif sel=='wide':
            pS=pS_pr
            pE=pE_pr
            prebin=True


        jj, ii=geo_tools.find_closest_model_point(df0.loc[df0.Station==nn]['LonDecDeg'].values[0],
                                       df0.loc[df0.Station==nn]['LatDecDeg'].values[0], nav_lon, nav_lat)
        
        zmax=-1*gsw.z_from_p(cast25[nn].df.loc[ip,'prSM'],
                                    df0.loc[df0.Station==nn]['LatDecDeg'])
        edges=gdepw[:,jj,ii]
        targets=gdept[:,jj,ii]
        edges=edges[edges<zmax]
        targets=targets[:(len(edges)-1)]
        parDZ=.78
        xmisDZ=.36
        turbDZ=.67

        zshiftdict={'gsw_ctA0':0.0,'gsw_srA0':0.0,'xmiss':xmisDZ,'seaTurbMtr':turbDZ,'par':parDZ,
                    'wetStar':0.0,'sbeox0ML_L':0.0}
        dCast=pd.DataFrame()
        uCast=pd.DataFrame()
        for var in ('gsw_ctA0','gsw_srA0','xmiss','par','wetStar','sbeox0ML_L'):
            if not nn==14.2:
                #downcast
                inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'])-zshiftdict[var] # down z
                inV=cast25[nn].df.loc[pS:ip][var].values # down var
                if sel=='wide':
                    inV[inP<.1]=np.nan
                p, out=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
                if var=='gsw_ctA0':
                    dCast=pd.DataFrame(p,columns=['depth_m'])
                    dCast['indk']=np.arange(0,len(p))
                dCast[var]=out
            else:# special case where there is no downcast
                if var=='gsw_ctA0':
                    dCast=pd.DataFrame(np.nan*np.ones(10),columns=['depth_m'])
                    dCast['indk']=np.nan*np.ones(10)
                dCast[var]=np.nan*np.ones(10)
            if not nn==14.1:
                #upcast    
                inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'])-zshiftdict[var] # down z
                inV=cast25[nn].df.loc[ip:pE][var].values # down var
                if sel=='wide':
                    inV[inP<.1]=np.nan
                p, out=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
                if var=='gsw_ctA0':
                    uCast=pd.DataFrame(p,columns=['depth_m'])
                    uCast['indk']=np.arange(0,len(p))
                uCast[var]=out
            else:# special case where there is no upcast
                if var=='gsw_ctA0':
                    uCast=pd.DataFrame(np.nan*np.ones(10),columns=['depth_m'])
                    uCast['indk']=np.nan*np.ones(10)
                uCast[var]=np.nan*np.ones(10)
        if not nn==14.2:
            #turbidity downcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'])-turbDZ # down z
            inV0=cast19[nn].df.loc[(pS+ilag):(ip+ilag)]['seaTurbMtr'].values # down var
            if sel=='wide':
                # additional QC for broader data selection
                ii1=amp(rolling_window_padded(inV0,5),-1)>.5*np.nanmax(inV0)
                # get rid of near-zero turbidity values; seem to be dropped signal
                ii2=np.nanmin(rolling_window_padded(inV0,5),-1)<.3
                inV0[np.logical_or(ii1,ii2)]=np.nan
            inV=ssig.medfilt(inV0,3) # down var
            if sel=='wide': # exclude above surface data
                with np.errstate(invalid='ignore'):
                    inV[inP<.1]=np.nan
            p, tur=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
            dCast['turb']=tur*1.0/tcor
        else: # special case where there is no downcast
            dCast['turb']=np.nan*np.ones(10)
        if not nn==14.1:
            #turbidity upcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'])-turbDZ # up z
            inV0=cast19[nn].df.loc[(ip+ilag):(pE+ilag)]['seaTurbMtr'].values # up var
            if sel=='wide':
                # additional QC for broader data selection
                ii1=amp(rolling_window_padded(inV0,5),-1)>.5*np.nanmax(inV0)
                # get rid of near-zero turbidity values; seem to be dropped signal
                ii2=np.nanmin(rolling_window_padded(inV0,5),-1)<.3
                inV0[np.logical_or(ii1,ii2)]=np.nan
            inV=ssig.medfilt(inV0,3) # down var
            if sel=='wide': # exclude above surface data
                with np.errstate(invalid='ignore'):
                    inV[inP<.1]=np.nan
            p, tur=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
            uCast['turb']=tur*1.0/tcor
        else: # special case where there is no upcasts
            uCast['turb']=np.nan*np.ones(10)

        zCasts[nn]=zCast(uCast,dCast)

    # fix first 2 casts for which sb25 pump did not turn on. use sb19
    if (exp=='exp1' or exp=='all'):
        for nn in range(1,3):

            uCast=zCasts[nn].uCast
            dCast=zCasts[nn].dCast

            ip=np.argmax(cast25[nn].df['prSM'].values)
            ilag=df0.loc[df0.Station==nn,'ishift_sub19'].values[0]
            pS_pr=df0.loc[df0.Station==nn,'pS_pr'].values[0]
            pE_pr=df0.loc[df0.Station==nn,'pE_pr'].values[0]
            pS_tur=df0.loc[df0.Station==nn,'pStart25'].values[0]
            pE_tur=df0.loc[df0.Station==nn,'pEnd25'].values[0]
            if sel=='narrow':
                pS=pS_tur
                pE=pE_tur
            elif sel=='wide':
                pS=pS_pr
                pE=pE_pr

            jj, ii=geo_tools.find_closest_model_point(df0.loc[df0.Station==nn]['LonDecDeg'].values[0],
                                       df0.loc[df0.Station==nn]['LatDecDeg'].values[0], nav_lon, nav_lat)
            
            zmax=-1*gsw.z_from_p(cast25[nn].df.loc[ip,'prSM'],
                                    df0.loc[df0.Station==nn]['LatDecDeg'])
            edges=gdepw[:,jj,ii]
            targets=gdept[:,jj,ii]
            edges=edges[edges<zmax]
            targets=targets[:(len(edges)-1)]

            ##temperature
            #downcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg']) # down z
            inV=cast19[nn].df.loc[(pS+ilag):(ip+ilag)]['gsw_ctA0'].values # down var
            if sel=='wide':
                inV[inP<.1]=np.nan
            p, out=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
            dCast['gsw_ctA0']=out
            #upcast    
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg']) # up z
            inV=cast19[nn].df.loc[(ip+ilag):(pE+ilag)]['gsw_ctA0'].values # up var
            if sel=='wide':
                inV[inP<.1]=np.nan
            p, out=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
            uCast['gsw_ctA0']=out

            ##sal
            #downcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg']) # down z
            inV=cast19[nn].df.loc[(pS+ilag):(ip+ilag)]['gsw_srA0'].values # down var
            if sel=='wide':
                inV[inP<.1]=np.nan
            p, out=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
            dCast['gsw_srA0']=out
            #upcast    
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg']) # up z
            inV=cast19[nn].df.loc[(ip+ilag):(pE+ilag)]['gsw_srA0'].values # up var
            if sel=='wide':
                inV[inP<.1]=np.nan
            p, out=bindepth(inP,inV,edges,prebin=prebin)
            uCast['gsw_srA0']=out

            ##xmiss: xmis25=1.14099414691*xmis19+-1.6910134322
            #downcast
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[pS:ip]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'])-xmisDZ # down z
            inV=1.14099414691*cast19[nn].df.loc[(pS+ilag):(ip+ilag)]['CStarTr0'].values-1.6910134322 # down var
            if sel=='wide':
                inV[inP<.1]=np.nan
            p, out=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
            dCast['xmiss']=out
            #upcast    
            inP=-1*gsw.z_from_p(cast25[nn].df.loc[ip:pE]['prSM'].values,
                                    df0.loc[df0.Station==nn]['LatDecDeg'])-xmisDZ # up p
            inV=1.14099414691*cast19[nn].df.loc[(ip+ilag):(pE+ilag)]['CStarTr0'].values-1.6910134322 # up var
            if sel=='wide':
                inV[inP<.1]=np.nan
            p, out=bindepth(inP,inV,edges=edges,targets=targets,prebin=prebin)
            uCast['xmiss']=out

            uCast['wetStar']=np.nan
            dCast['wetStar']=np.nan
            uCast['sbeox0ML_L']=np.nan
            dCast['sbeox0ML_L']=np.nan

            zCasts[nn]=zCast(uCast,dCast)
    
    return df0, zCasts
