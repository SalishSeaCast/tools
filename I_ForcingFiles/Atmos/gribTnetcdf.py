# Standard Imports
from __future__ import division
import arrow
import glob
import netCDF4 as nc
import numpy as np
import os
import subprocess as sp
# next two lines are to allow Salish (without good Display) to produce the plots
# in matplotlib
import matplotlib as mt
mt.use('Agg')
import matplotlib.pyplot as plt

def gribTnetcdf():
    '''Script to convert hourly GRIB files to daily netcdf files
       Calculate instantaneous fluxes
       and rename to NEMO names'''

    GRIBdir = '../../../GRIB/'
    OPERdir = '../../../Operational/'
    utc = arrow.utcnow()
    now = utc.to('Canada/Pacific')
    year = now.year; month = now.month; day = now.day
    yesterday = now.replace(days=-1)
    yearm1 = yesterday.year; monthm1 = yesterday.month; daym1 = yesterday.day
    size = 'watershed'
    ymd = 'y{year}m{month}d{day}'.format(year=year,month=month,day=day)
    p1 = '{year}{month}{day}/18/'.format(year=yearm1,month=monthm1,day=daym1)
    p2 = '{year}{month}{day}/06/'.format(year=year,month=month,day=day)
    p3 = '{year}{month}{day}/18/'.format(year=year,month=month,day=day)
    HoursWeNeed = {
            'part one':  (p1, 24-18-1, 24+6-18),
            'part two':  (p2, 7-6, 18-6),
            'part three':(p3, 19-18, 23-18),
           }
    if size == 'full':
        fileextra = ''
    elif size == 'watershed':  # see AtmosphericGridSelection.ipynb
        fileextra = ''
        ist = 110; ien = 365
        jst = 20; jen = 285
        
    try:
        os.remove('wglog')
    except Exception: 
        pass
    logfile = open('wglog','w')
        

    process_gribUV(GRIBdir, HoursWeNeed, logfile)
    process_gribscalar(GRIBdir, HoursWeNeed, logfile)
    outgrib, outzeros = GRIBappend(OPERdir, GRIBdir, ymd, HoursWeNeed,
                                       logfile)
    if size != 'full':
        outgrib, outzeros = subsample(OPERdir, ymd, ist, ien, jst, jen, 
                                          outgrib, outzeros, logfile)
    outnetcdf,out0netcdf = makeCDF(OPERdir, ymd, fileextra, outgrib, 
                                           outzeros, logfile)
    processCDF(outnetcdf, out0netcdf, ymd)
    renameCDF(outnetcdf)
    plt.savefig('wg.png')

def process_gribUV(GRIBdir, HoursWeNeed, logfile):
    '''Script to align winds with N/S, amalgamate files'''
    for part in ('part one','part two','part three'):
        for fhour in range(HoursWeNeed[part][1],HoursWeNeed[part][2]+1):
        
            # set up directories and files
            sfhour = '{:0=3}'.format(fhour)
            dire = HoursWeNeed[part][0]
            outuv = GRIBdir+dire+sfhour+'/UV.grib' 
            try:
                os.remove(outuv)
            except Exception: 
                pass
            outuvrot = GRIBdir+dire+sfhour+'/UVrot.grib'
            try:
                os.remove(outuvrot)
            except Exception:
                pass

        
            # append U and V
            fn = glob.glob(GRIBdir+dire+sfhour+'/*UGRD*')
            sp.call(["./wgrib2",fn[0],"-append","-grib",outuv], stdout=logfile)
            fn = glob.glob(GRIBdir+dire+sfhour+'/*VGRD*')
            sp.call(["./wgrib2",fn[0],"-append","-grib",outuv], stdout=logfile)
            # print sp.check_output(["./wgrib2",fn[0],"-vt"])
        
            # rotate
            GRIDspec = sp.check_output(
                ["/ocean/sallen/allen/research/Meopar/private-tools/PThupaki/grid_defn.pl",outuv])
            cmd = ["./wgrib2", outuv]
            cmd.extend("-new_grid_winds earth".split())
            cmd.append("-new_grid")
            cmd.extend(GRIDspec.split())
            cmd.append(outuvrot)
            sp.call(cmd, stdout=logfile)
            os.remove(outuv)

def process_gribscalar(GRIBdir, HoursWeNeed, logfile):
    '''append scalar files, put on same grid as UV'''
    for part in ('part one','part two','part three'):
        for fhour in range(HoursWeNeed[part][1],HoursWeNeed[part][2]+1):
            
            # set up directories and files
            sfhour = '{:0=3}'.format(fhour)
            dire = HoursWeNeed[part][0]
            outscalar = GRIBdir+dire+sfhour+'/scalar.grib' 
            try:
                os.remove(outscalar)
            except Exception: 
                pass
            outscalargrid = GRIBdir+dire+sfhour+'/gscalar.grib'
            try:
                os.remove(outscalargrid)
            except Exception: 
                pass
            for fn in glob.glob(GRIBdir+dire+sfhour+'/*'):
                if not ("GRD" in fn) and ("CMC" in fn):                
                    sp.call(["./wgrib2",fn,"-append","-grib",outscalar], 
                                                        stdout=logfile)
    #  put on new grid
            GRIDspec = sp.check_output(
              ["/ocean/sallen/allen/research/Meopar/private-tools/PThupaki/grid_defn.pl",outscalar])
            cmd = ["./wgrib2", outscalar]
            cmd.append("-new_grid")
            cmd.extend(GRIDspec.split())
            cmd.append(outscalargrid)
            sp.call(cmd, stdout=logfile, stderr=logfile)
            os.remove(outscalar)

def GRIBappend(OPERdir, GRIBdir, ymd, HoursWeNeed, logfile):
    '''Append all the hours and the vector and scalar files'''
    outgrib = os.path.join(OPERdir, 'oper_allvar_{ymd}.grib'.format(ymd=ymd))   
    outzeros = os.path.join(OPERdir, 'oper_000_{ymd}.grib'.format(ymd=ymd))
    try:
        os.unremove(outgrib)
    except Exception: 
        pass
    try:
        os.remove(outzeros)
    except Exception: 
        pass

    for part in ('part one','part two','part three'):
        for fhour in range(HoursWeNeed[part][1],HoursWeNeed[part][2]+1):
        
            # set up directories and files
            sfhour = '{:0=3}'.format(fhour)
            dire = HoursWeNeed[part][0]
            outuvrot = GRIBdir+dire+sfhour+'/UVrot.grib'
            outscalargrid = GRIBdir+dire+sfhour+'/gscalar.grib'
            if fhour == 0 or (part == 'part one' and fhour == 5):
                sp.call(["./wgrib2",outuvrot,"-append","-grib",outzeros],
                        stdout=logfile)
                sp.call(["./wgrib2",outscalargrid,"-append","-grib",outzeros],
                        stdout=logfile) 
            else:
                sp.call(["./wgrib2",outuvrot,"-append","-grib",outgrib],
                        stdout=logfile)
                sp.call(["./wgrib2",outscalargrid,"-append","-grib",outgrib],
                        stdout=logfile) 
            os.remove(outuvrot)
            os.remove(outscalargrid)
    return outgrib, outzeros

def subsample(OPERdir, ymd, ist, ien, jst, jen, outgrib, outzeros, logfile):
    '''sub sample onto smaller grid'''
    newgrib = os.path.join(OPERdir, 'oper_allvar_small_{ymd}.grib'.format(ymd=ymd))
    newzeros = os.path.join(OPERdir, 'oper_000_small_{ymd}.grib'.format(ymd=ymd))
    istr = '{ist}:{ien}'.format(ist=ist,ien=ien)
    jstr = '{jst}:{jen}'.format(jst=jst,jen=jen)
    sp.call(["./wgrib2", outgrib, "-ijsmall_grib",istr,jstr,newgrib], 
             stdout=logfile)   
    sp.call(["./wgrib2", outzeros, "-ijsmall_grib",istr,jstr,newzeros],
             stdout=logfile)
    os.remove(outgrib)
    os.remove(outzeros)
    return newgrib, newzeros

def makeCDF(OPERdir, ymd, fileextra, outgrib, outzeros, logfile):
    '''convert the grid files to netcdf (classic) files'''
    outnetcdf = os.path.join(OPERdir, 
            'ops{fileextra}_{ymd}.nc'.format(fileextra=fileextra, ymd=ymd))
    out0netcdf = os.path.join(OPERdir, 'oper_000_{ymd}.nc'.format(ymd=ymd))
    sp.call(["./wgrib2", outgrib, "-netcdf", outnetcdf], stdout=logfile)
    sp.call(["./wgrib2", outzeros, "-netcdf", out0netcdf], stdout=logfile)
    os.remove(outgrib)
    os.remove(outzeros)
    return outnetcdf,out0netcdf

def processCDF(outnetcdf, out0netcdf, ymd):
    '''calculate instantaneous values for accumulated variables'''
    data = nc.Dataset(outnetcdf, 'r+')
    data0 = nc.Dataset(out0netcdf, 'r')
    acc_vars = ('APCP_surface', 'DSWRF_surface', 'DLWRF_surface')
    acc_values = {
        'acc': {},
        'zero': {},
        'inst': {},
    }
    for var in acc_vars:
        acc_values['acc'][var] = data.variables[var][:]
        acc_values['zero'][var] = data0.variables[var][:]
        acc_values['inst'][var] = np.empty_like(acc_values['acc'][var])
    plt.subplot(2,3,1)
    plt.plot(acc_values['acc']['APCP_surface'][:,200,200],'o-')
    plt.title(ymd)

    for var in acc_vars:
        acc_values['inst'][var][0] = (acc_values['acc'][var][0] - acc_values['zero'][var][0])/3600.
        for t in range(1,7):
            acc_values['inst'][var][t] = (acc_values['acc'][var][t] - acc_values['acc'][var][t-1])/3600.    
        acc_values['inst'][var][7] = acc_values['acc'][var][7]/3600.
        for t in range(8,19):
            acc_values['inst'][var][t] = (acc_values['acc'][var][t] - acc_values['acc'][var][t-1])/3600.
        acc_values['inst'][var][19] = (acc_values['acc'][var][19])/3600.
        for t in range(20,24):
            acc_values['inst'][var][t] = (acc_values['acc'][var][t] - acc_values['acc'][var][t-1])/3600.
    plt.subplot(2,3,2)
    plt.plot(acc_values['inst']['APCP_surface'][:,200,200])
    for var in acc_vars:
        data.variables[var][:] = acc_values['inst'][var][:]
    data.close()
    data0.close()
    os.remove(out0netcdf)

def renameCDF(outnetcdf):
    '''rename variables to match NEMO naming conventions'''
    data = nc.Dataset(outnetcdf, 'r+')
    data.renameDimension('time','time_counter')
    data.renameVariable('latitude','nav_lat')
    data.renameVariable('longitude','nav_lon')
    data.renameVariable('time','time_counter')
    data.renameVariable('UGRD_10maboveground','u_wind')
    data.renameVariable('VGRD_10maboveground','v_wind')
    data.renameVariable('DSWRF_surface','solar')
    data.renameVariable('SPFH_2maboveground','qair')
    data.renameVariable('DLWRF_surface','therm_rad')
    data.renameVariable('TMP_2maboveground','tair')
    data.renameVariable('PRMSL_meansealevel','atmpres')
    data.renameVariable('APCP_surface','precip')
    Temp = data.variables['tair'][:]
    plt.subplot(2,3,3)
    plt.pcolormesh(Temp[0])
    plt.xlim([0,Temp.shape[2]])
    plt.ylim([0,Temp.shape[1]])
    plt.subplot(2,3,4)
    precip = data.variables['precip'][:]
    plt.plot(precip[:,200,200])
    solar = data.variables['solar'][:]
    plt.subplot(2,3,5)
    plt.plot(solar[:,150,150])
    longwave = data.variables['therm_rad'][:]
    plt.subplot(2,3,6)
    plt.plot(longwave[:,150,150])
    
    data.close()

if __name__ == '__main__':
    gribTnetcdf()

