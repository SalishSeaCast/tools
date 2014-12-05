from __future__ import division

import netCDF4 as nc
import numpy as np


from salishsea_tools import (
    nc_tools)
import pytz, datetime
import os
import urllib2
from bs4 import BeautifulSoup
from StringIO import StringIO
import pandas as pd

def getNBssh():
   """ Script for generate sea surface height forcing files from the Neah Bay storm surge website.""" 

   fB = nc.Dataset('/data/nsoontie/MEOPAR/NEMO-forcing/grid/bathy_meter_SalishSea2.nc','r')
   lat = fB.variables['nav_lat'][:]
   lon = fB.variables['nav_lon'][:]
   fB.close()

   utc_now = datetime.datetime.now(pytz.timezone('UTC'))
   YEAR=utc_now.year; #year of data. 
   isDec=False; isJan=False
   if utc_now.month ==12:
     isDec =True;
   if utc_now.month ==1:
     isJan =True;
   SAVE_PATH = '/ocean/nsoontie/MEOPAR/sshNeahBay/test/'

   #load surge data
   textfile = read_website(SAVE_PATH)
   data = load_surge_data(textfile)

   #Process the dates to find days with a full prediction
   dates=np.array(data.date.values)
   for i in range(dates.shape[0]):
      dates[i]=to_datetime(dates[i],YEAR,isDec,isJan)
   dates_list=list_full_days(dates)

   #loop through full days and save netcdf
   for d in dates_list:
      surges,tc,forecast_flag=retrieve_surge(d,dates,data)
      save_netcdf(d,tc,surges,forecast_flag,textfile,SAVE_PATH,lat,lon)

def load_surge_data(filename):
    """Loads the textfile with surge predictions
    returns as a data structure"""

    #Loading the data from that text file.
    data = pd.read_csv(filename,skiprows=3,names=['date','surge','tide','obs','fcst','anom','comment'], 
    comment='#')
    #drop rows with all Nans
    data= data.dropna(how='all')    
    return data

def read_website(save_path):
    """Reads a website with Neah Bay storm surge predictions/observations
    The data is in a file in the given save_path
    returns the filename where the surge data is stored"""
    url='http://www.nws.noaa.gov/mdl/etsurge/index.php?page=stn&region=wc&datum=msl&list=&map=0-48&type=both&stn=waneah'
    response = urllib2.urlopen(url)
    html = response.read()

    #use BeautifulSoup to parse out table
    soup = BeautifulSoup(html)
    table=str(soup.findAll('pre'))
    table=table.replace('<pre>','')
    table=table.replace('</pre>','')
    table=table.replace('[','')
    table=table.replace(']','')
    
    #save the table as a text file. Use the date the table was generated as a file name?
    today=datetime.datetime.strftime(datetime.datetime.now(pytz.timezone('UTC')),'%Y-%m-%d_%H')
    filename = os.path.join(save_path,'txt','sshNB_{}.txt'.format(today))
    text_file = open(filename, "w")
    text_file.write(table)
    text_file.close()
    
    return filename

def save_netcdf(day,tc,surges,forecast_flag,textfile,save_path,lat,lon):
    """saves the surge for a given day in a netcdf file""" 
    #define stuff we will need for saving netcdfs - JdF parameters.
    startj = 384
    endj = 471
    lengthj = endj-startj
    r = 1

    daystr = 'ssh_{}.nc'.format(day.strftime('y%Ym%md%d'))
    if forecast_flag:
        savstr = os.path.join(save_path,'fcst',daystr)
        comment = 'Prediction from Neah Bay storm surge website'
    else:
        savstr = os.path.join(save_path,'obs',daystr)
        comment = 'Observation from Neah Bay storm surge website'
    #open netcdf file
    ssh_file = nc.Dataset(savstr, 'w')
    nc_tools.init_dataset_attrs(
    ssh_file, 
    title='Neah Bay SSH hourly values', 
    notebook_name='', 
    nc_filepath=savstr,
    comment=comment)
    ssh_file.source=textfile

    #dimensions
    ssh_file.createDimension('xbT', lengthj*r)
    ssh_file.createDimension('yb', 1)
    ssh_file.createDimension('time_counter', None)
    # variables
    # time_counter
    time_counter = ssh_file.createVariable('time_counter', 'float32', ('time_counter'))
    time_counter.long_name = 'Time axis'
    time_counter.axis = 'T'
    time_counter.units = 'hour since 00:00:00 on ' +day.strftime('%Y-%m-%d')
    # nav_lat and nav_lon
    nav_lat = ssh_file.createVariable('nav_lat','float32',('yb','xbT'))
    nav_lat.long_name = 'Latitude'
    nav_lat.units = 'degrees_north'
    nav_lon = ssh_file.createVariable('nav_lon','float32',('yb','xbT'))
    nav_lon.long_name = 'Longitude'
    nav_lon.units = 'degrees_east'
    # ssh
    sossheig = ssh_file.createVariable('sossheig', 'float32', 
                               ('time_counter','yb','xbT'), zlib=True)
    sossheig.units = 'm'
    sossheig.long_name = 'Sea surface height'   
    sossheig.coordinates = 'nav_lon nav_lat time_counter'
    sossheig.grid = 'SalishSea2'
    # vobtcrtx, vobtcrty
    vobtcrtx = ssh_file.createVariable('vobtcrtx', 'float32',
                                   ('time_counter','yb','xbT'), zlib=True)
    vobtcrtx.units = 'm/s'
    vobtcrtx.long_name = 'Barotropic U Velocity- ZEROD'   
    vobtcrtx.grid = 'SalishSea2'
    vobtcrty = ssh_file.createVariable('vobtcrty', 'float32',
                                   ('time_counter','yb','xbT'), zlib=True)
    vobtcrty.units = 'm/s'
    vobtcrty.long_name = 'Barotropic V Velocity- ZEROD'   
    vobtcrty.grid = 'SalishSea2'
    # nbidta, ndjdta, ndrdta
    nbidta = ssh_file.createVariable('nbidta', 'int32' , ('yb','xbT'), zlib=True)
    nbidta.long_name = 'i grid position'
    nbidta.units = 1
    nbjdta = ssh_file.createVariable('nbjdta', 'int32' , ('yb','xbT'), zlib=True)
    nbjdta.long_name = 'j grid position'
    nbjdta.units = 1
    nbrdta = ssh_file.createVariable('nbrdta', 'int32' , ('yb','xbT'), zlib=True)
    nbrdta.long_name = 'position from boundary'
    nbrdta.units = 1
    
    for ir in range(0,r):
        nav_lat[0,ir*lengthj:(ir+1)*lengthj] = lat[startj:endj,ir]
        nav_lon[0,ir*lengthj:(ir+1)*lengthj] = lon[startj:endj,ir]
        nbidta[0,ir*lengthj:(ir+1)*lengthj] = ir
        nbjdta[0,ir*lengthj:(ir+1)*lengthj] = range(startj,endj)
        nbrdta[0,ir*lengthj:(ir+1)*lengthj] = ir
        
    for ib in range(0,lengthj*r):
        sossheig[:,0,ib] = surges
        time_counter[:] = tc+1
        vobtcrtx[:,0,ib] = 0*np.ones(len(surges))
        vobtcrty[:,0,ib] = 0*np.ones(len(surges))

    ssh_file.close()

def retrieve_surge(day,dates, data):
    """gathers the surge information for a single day. 
    returns the surges in meteres, an array with time_counter and a flag indicating if this day was a forecast"""
    #initialize forecast flag and surge array
    forecast_flag=0; surge=[]
    #grab list of times on this day.
    tc,ds= isolate_day(day,dates)
    
    for d in ds:
        #convert datetime to string for comparing with times in data
        daystr = d.strftime('%m/%d %HZ')
        tide=data.tide[data.date==daystr].item()
        obs=data.obs[data.date==daystr].item()
        fcst = data.fcst[data.date==daystr].item()
        if obs == 99.90:
            #fall daylight savings
            if fcst==99.90:
                #if surge is empty, just append 0
                if not surge:
                    surge.append(0)
                else:  
                #otherwise append previous value 
                    surge.append(surge[-1])
            else:
                surge.append(feet_to_metres(fcst-tide))
                forecast_flag=1
        else:
            surge.append(feet_to_metres(obs-tide))
    
    return surge, tc,  forecast_flag

def isolate_day(day, dates):
    """returns array of time_counter and datetime objects over a 24 hour period covering one full day"""
    tc=np.arange(24)
    dates_return=[];
    for t in dates:
        if t.month==day.month:
            if t.day==day.day:
                dates_return.append(t);
    return tc, np.array(dates_return)

def list_full_days(dates):
    """returns a list of days that have a full 24 hour data set."""
    
    #check if first day is a full day
    tc,ds= isolate_day(dates[0],dates)
    if ds.shape[0] == tc.shape[0]:
        start = dates[0]
    else:
        start = dates[0] +datetime.timedelta(days=1)
    start=datetime.datetime(start.year,start.month, start.day,tzinfo=pytz.timezone('UTC'))

    #check if last day is a full day
    tc,ds = isolate_day(dates[-1],dates)
    if ds.shape[0] == tc.shape[0]:
        end = dates[-1]
    else:
        end = dates[-1] -datetime.timedelta(days=1)
    end=datetime.datetime(end.year,end.month, end.day,tzinfo=pytz.timezone('UTC'))
    
    #list of dates that are full
    dates_list = [start +datetime.timedelta(days=i) for i in range((end-start).days+1)]
    return dates_list

def to_datetime(datestr,year,isDec,isJan):
    """ converts the string given by datestr to a datetime object.
    The year is an argument because the datestr in the NOAA data doesn't have a year.
    Times are in UTC/GMT.
    returns a datetime representation of datestr"""
    dt = datetime.datetime.strptime(datestr,'%m/%d %HZ')
    if isDec and dt.month ==1:
          dt =dt.replace(year=year+1)
    elif isJan and dt.month==12:
          dt =dt.replace(year=year-1)
    else:
       dt=dt.replace(year=year)
    dt=dt.replace(tzinfo=pytz.timezone('UTC'))
    return dt

def feet_to_metres(feet):
    metres = feet*0.3048
    return metres

if __name__ == '__main__':
    getNBssh()
