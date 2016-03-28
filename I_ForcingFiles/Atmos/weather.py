# Copyright 2013-2016 The Salish Sea MEOPAR contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A collection of tools for comparing atmospheric forcing with
observations from the Salish Sea Model.
"""
from __future__ import division

import datetime
import netCDF4 as NC
import numpy as np
import pytz
import arrow
import cStringIO
import requests
from pytz import timezone as tz
from xml.etree import cElementTree as ElementTree
import pandas as pd
from salishsea_tools import tidetools
import csv
import os
from compiler.ast import flatten

def get_EC_observations(station, start_day, end_day):
    """
    Gather Environment Canada weather observations for the station and dates indicated. The dates should span one month because of how EC data is collected.

    :arg station: string with station name (no spaces). e.g. 'PointAtkinson'
    :type station: str

    :arg start_day: string contating the start date in the format '01-Dec-2006'. This is a local time.
    :type start_day: str

    :arg end_day: string contating the end date in the format '01-Dec-2006'. This is a local time
    :type end_day: str

    :returns: wind_speed, wind_dir, temperature, times, lat and lon: wind speed and direction, and time(local) of data from observations. Also latitude and longitude of the station.

    """
    station_ids = {
	'PamRocks': 6817,
	'SistersIsland': 6813,
	'EntranceIsland': 29411,
        'Sandheads': 6831,
        'YVR': 51442, #note, I think YVR station name changed in 2013. Older data use 889
        'PointAtkinson': 844,
        'Victoria': 10944,
        'CampbellRiver': 145,
        'PatriciaBay': 11007, # not exactly at Patricia Bay
	'Esquimalt': 52
    }

    st_ar=arrow.Arrow.strptime(start_day, '%d-%b-%Y')
    end_ar=arrow.Arrow.strptime(end_day, '%d-%b-%Y')

    wind_spd= []; wind_dir=[]; temp=[];
    url = 'http://climate.weather.gc.ca/climateData/bulkdata_e.html'
    query = {
        'timeframe': 1,
        'stationID': station_ids[station],
        'format': 'xml',
        'Year': st_ar.year,
        'Month': st_ar.month,
        'Day': 1,
    }
    response = requests.get(url, params=query)
    tree = ElementTree.parse(cStringIO.StringIO(response.content))
    root = tree.getroot()
    #read lat and lon
    for raw_info in root.findall('stationinformation'):
	lat =float(raw_info.find('latitude').text)
	lon =float(raw_info.find('longitude').text)
    #read data
    raw_data = root.findall('stationdata')
    times = []
    for record in raw_data:
        day = int(record.get('day'))
        hour = int(record.get('hour'))
        year = int(record.get('year'))
        month = int(record.get('month'))
        t = arrow.Arrow(year, month,day,hour,tzinfo=tz('US/Pacific'))
        selectors = (
            (day >= st_ar.day and day <= end_ar.day)
        )
        if selectors:
            try:
                wind_spd.append(float(record.find('windspd').text))
                times.append(t.datetime)
            except TypeError:
                wind_spd.append(0)
                times.append(t.datetime)
	    try:
                wind_dir.append(float(record.find('winddir').text) * 10)
            except:
                wind_dir.append(float('NaN'))
	    try:
                temp.append(float(record.find('temp').text) +273)
            except:
                temp.append(float('NaN'))
    wind_spd= np.array(wind_spd) * 1000 / 3600
    wind_dir=-np.array(wind_dir)+270
    wind_dir=wind_dir + 360 * (wind_dir<0)
    temp=np.array(temp)

    return wind_spd, wind_dir, temp, times, lat, lon

def list_files(startdate, numdays, model):
	""" create a list of files for a given model beginning on startdate and going back numdays.
	model can be a string 'Operational_old' (reformatted GRIB2, older files),
	'Operational' (reformatted GRIB2 on subset), or 'GEM' (netcdf from EC).
	returns the list of files and desired dates"""
 	path=''
	if model =='GEM':
	   path='/ocean/dlatorne/MEOPAR/GEM2.5/NEMO-atmos/res_'
	elif model =='Operational_old':
	   path ='/ocean/sallen/allen/research/Meopar/Operational/oper_allvar_y'
	elif model == 'Operational':
	   path ='/ocean/sallen/allen/research/Meopar/Operational/ops_y'

	dates = [ startdate - datetime.timedelta(days=num) for num in range(0,numdays)]
	dates.sort();
	sstr =path+dates[0].strftime('%Y')+'m'+dates[0].strftime('%m')+'d'+dates[0].strftime('%d')+'.nc'
	estr =path+dates[-1].strftime('%Y')+'m'+dates[-1].strftime('%m')+'d'+dates[-1].strftime('%d')+'.nc'

        for filename in files:
	    if filename < sstr:
		files.remove(filename)
	    if filename > estr:
	        files.remove(filename)

 	files.sort(key=os.path.basename)

	return files

def find_model_point(lon,lat,X,Y):
	"""returns the closest model grid point to the given lat/lon.
	Model grid is X,Y.
	returns j,i
	"""
        # Tolerance for searching for grid points
    	# (approx. distances between adjacent grid points)
   	tol1 = 0.015 # lon
    	tol2 = 0.015# lat

    	# Search for a grid point with lon/lat within tolerance of
    	# measured location
    	x1, y1 = np.where(
                   np.logical_and(
                    (np.logical_and(X > lon-tol1, X < lon+tol1)),
                    (np.logical_and(Y > lat-tol2, Y < lat+tol2))))
    	return x1[0], y1[0]

def compile_model_output(i,j,files,model):
    """ compiles the model variables over severl files into a single array at a j,i grid point.
        Model can be "Operational", "Operational_old", "GEM".
	returns wind speed, wind direction, time,pressure, temperature, solar radiation, thermal radiation and humidity.
    """
    wind=[]; direc=[]; t=[]; pr=[]; sol=[]; the=[]; pre=[]; tem=[]; qr=[];
    for f in files:
        G = nc.Dataset(f)
        u = G.variables['u_wind'][:,j,i]; v=G.variables['v_wind'][:,j,i];
        pr.append(G.variables['atmpres'][:,j,i]); sol.append(G.variables['solar'][:,j,i]);
        qr.append(G.variables['qair'][:,j,i]); the.append(G.variables['therm_rad'][:,j,i]);
        pre.append(G.variables['precip'][:,j,i]);
        tem.append(G.variables['tair'][:,j,i])
        speed = np.sqrt(u**2 + v**2)
        wind.append(speed)

        d = np.arctan2(v, u)
        d = np.rad2deg(d + (d<0)*2*np.pi);
        direc.append(d)

	ts=G.variables['time_counter']
	if model =='GEM':
	   torig = nc_tools.time_origin(G)
	elif model =='Operational' or model=='Operational_old':
           torig = datetime.datetime(1970,1,1) #there is no time_origin attriubte in OP files, so I hard coded this
        for ind in np.arange(ts.shape[0]):
            t.append((torig + datetime.timedelta(seconds=ts[ind])).datetime)

    wind = np.array(wind).reshape(len(filesGEM)*24,)
    direc = np.array(direc,'double').reshape(len(filesGEM)*24,)
    t = np.array(t).reshape(len(filesGEM)*24,)
    pr = np.array(pr).reshape(len(filesGEM)*24,)
    tem = np.array(tem).reshape(len(filesGEM)*24,)
    sol = np.array(sol).reshape(len(filesGEM)*24,)
    the = np.array(the).reshape(len(filesGEM)*24,)
    qr = np.array(qr).reshape(len(filesGEM)*24,)
    pre = np.array(pre).reshape(len(filesGEM)*24,)

    return wind, direc, t, pr, tem, sol, the, qr, pre

def compile_model_output_MF(i,j,files,model):
   """ Uses the MFDataset method to combine all the datasets
       Model can be "Operational", "Operational_old", "GEM".
       returns wind speed, wind direction, time,pressure, temperature, solar radiation, thermal radiation and humidity.
   """
   G = nc.MFDataset(files)

   u = G.variables['u_wind'][:,j,i]; v=G.variables['v_wind'][:,j,i];
   pr = G.variables['atmpres'][:,j,i]; sol = G.variables['solar'][:,j,i];
   qr = G.variables['qair'][:,j,i]; the = G.variables['therm_rad'][:,j,i];
   pre = G.variables['precip'][:,j,i]; tem = G.variables['tair'][:,j,i];

   wind = np.sqrt(u**2 + v**2)
   direc = np.arctan2(v, u)
   direc = np.rad2deg(direc + (direc<0)*2*np.pi);

   ts=G.variables['time_counter']
   if model =='GEM':
      torig = nc_tools.time_origin(G)
   elif model =='Operational' or model=='Operational_old':
      torig = datetime.datetime(1970,1,1) #there is no time_origin attriubte in OP files, so I hard coded this
   for ind in np.arange(ts.shape[0]):
      t.append((torig + datetime.timedelta(seconds=ts[ind])).datetime)

   return wind, direc, t, pr, tem, sol, the, qr, pre

def gather_observed_winds(location, startdate, numdays):
    """Uses the get_EC_observations function to return the winds and temperature at a location over a certain
    timefame, beginning on startdate and running backward from numdays.
    returns wind speed, wind direction, temperature and times, latitude and longitude. """
    dates = [ startdate - datetime.timedelta(days=num) for num in range(-1,numdays+1)]
    dates.sort();
    strd = dates[0].astimezone(pytz.timezone('US/Pacific')); start = strd.strftime('%d-%b-%Y');
    #if only one month of data
    if strd.month == dates[-1].astimezone(pytz.timezone('US/Pacific')).month:
    	endd = strd.replace(month=strd.month+1,day=1);
    	m = endd.month;
    	endd=endd -datetime.timedelta(days=1);
    	end = endd.strftime('%d-%b-%Y');
    	[winds,dirs,temps,times, lat, lon] = get_EC_observations(location,start,end)
    	times=np.array(times);
    #if spans more than one month, we have to be more careful
    else:
        count=1
        m=strd.month
	winds =[]; dirs=[]; times=[]; temps=[]
    	while m != dates[-1].astimezone(pytz.timezone('US/Pacific')).month:
	   d=dates[count].astimezone(pytz.timezone('US/Pacific'));
	   if d.month != m:
	      endd=d-datetime.timedelta(days=1); end = endd.strftime('%d-%b-%Y');
    	      [wind_speed,wind_dir,temp,time, lat, lon] = get_EC_observations(location,start,end)
              winds.append(wind_speed);
	      dirs.append(wind_dir);
	      times.append(time);
	      temps.append(temp)
              m=d.month;  start=d.strftime('%d-%b-%Y')
	   count=count+1
        #after the loop
        endd=dates[-1].astimezone(pytz.timezone('US/Pacific')); end = endd.strftime('%d-%b-%Y');
        [wind_speed,wind_dir,temp,time, lat, lon] = get_EC_observations(location,start,end)
        winds.append(wind_speed); winds=_flatten_list(winds); winds=np.array(winds)
        dirs.append(wind_dir); dirs=_flatten_list(dirs); dirs=np.array(dirs)
        times.append(time); times=_flatten_list(times); times=np.array(times)
        temps.append(temp); temps=_flatten_list(temps); temps=np.array(temps)
    #convert times back to utc
    for i in np.arange(times.shape[0]):
    	times[i] = times[i].astimezone(pytz.timezone('utc'))
    #isolates only requested days
    winds = winds[np.where((times<(startdate +datetime.timedelta(days=1)))
		  & (times>=(startdate -datetime.timedelta(days=numdays-1))))]
    dirs = dirs[np.where((times<(startdate +datetime.timedelta(days=1)))
		  & (times>=(startdate -datetime.timedelta(days=numdays-1))))]
    temps = temps[np.where((times<(startdate +datetime.timedelta(days=1)))
		  & (times>=(startdate -datetime.timedelta(days=numdays-1))))]
    times = times[np.where((times<(startdate +datetime.timedelta(days=1)))
		  & (times>=(startdate -datetime.timedelta(days=numdays-1))))]

    return winds,dirs,temps,times, lat, lon

def _flatten_list(mlist):
   """flattens a list of lists
      returns the flattened list"""
   flat =[val for sublist in mlist for val in sublist]
   return flat


