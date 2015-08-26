
# coding: utf-8

# # Imports from figures.py

# In[1]:

from __future__ import division, print_function
from cStringIO import StringIO
from IPython.core.display import HTML
from salishsea_tools.nowcast import figures
from glob import glob
import datetime
import glob
import os
import arrow
from dateutil import tz
from datetime import datetime, timedelta
from sklearn import linear_model
from pylab import *
from matplotlib.backends import backend_agg as backend
import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import netCDF4 as nc
import numpy as np
import pandas as pd
import requests
import math
from scipy import interpolate as interp
import scipy.io as sio

from salishsea_tools import (
    nc_tools,
    viz_tools,
    stormtools,
    tidetools,
)


# Font format
title_font = {
    'fontname': 'Bitstream Vera Sans', 'size': '15', 'color': 'black',
    'weight': 'medium'
}
axis_font = {'fontname': 'Bitstream Vera Sans', 'size': '13'}

bathy = nc.Dataset('/data/nsoontie/MEOPAR/NEMO-forcing/grid/bathy_meter_SalishSea2.nc')
PNW_coastline = sio.loadmat('/ocean/rich/more/mmapbase/bcgeo/PNW.mat')


def results_dataset(period, grid):
    """Return the results dataset for period (e.g. 1h or 1d)
    and grid (e.g. grid_T, grid_U) from results_dir.
    """
    filename_pattern = 'SalishSea_{period}_*_{grid}.nc'
    # Results dataset location
    results_home = '/data/dlatorne/MEOPAR/SalishSea/nowcast/'
    results_dir = os.path.join(results_home, run_date.strftime('%d%b%y').lower())
    filepaths = glob(os.path.join(results_dir, filename_pattern.format(period=period, grid=grid)))
    return nc.Dataset(filepaths[0])

today = datetime.datetime.today()
oneday = datetime.timedelta(days = 1)
run_date= today - oneday
date_str_yesterday = run_date.strftime('%Y%m%d')
date_str_today = today.strftime('%Y%m%d')

def date(year, month, day_start, day_end, period, grid):
    
    day_range = np.arange(day_start, day_end+1)
    day_len = len(day_range)
    files_all = [None] * day_len
    inds = np.arange(day_len)
    
    for i, day in zip(inds, day_range):
        run_date = datetime.datetime(year,month, day)
        results_home = '/data/dlatorne/MEOPAR/SalishSea/nowcast/'
        results_dir = os.path.join(results_home, run_date.strftime('%d%b%y').lower())
        filename = 'SalishSea_' + period + '_' + run_date.strftime('%Y%m%d').lower() +         '_' + run_date.strftime('%Y%m%d').lower() + '_' + grid + '.nc'
        file_single = os.path.join(results_dir, filename)
        files_all[i] = file_single

    return files_all



from glob import glob
grid_T_hr = results_dataset('1h', 'grid_T')
filepath_name = date(today.year,today.month,today.day,today.day,'1h','grid_T') 



latitude=grid_T_hr.variables['nav_lat'] 
longitude=grid_T_hr.variables['nav_lon']

sal_hr = grid_T_hr.variables['vosaline']
t, z = 3, 1
sal_hr = np.ma.masked_values(sal_hr[t, z], 0)


def find_dist (q, lon11, lat11, X, Y, bathy, longitude, latitude, saline_nemo_3rd, saline_nemo_4rd):
    k=0
    values =0
    valuess=0
    dist = np.zeros(9)
    weights = np.zeros(9)
    value_3rd=np.zeros(9)
    value_4rd=np.zeros(9)
    regr =linear_model.LinearRegression()
    regr.fit(lon11,lat11);
    regr.coef_

    [x1, j1] = tidetools.find_closest_model_point(lon11[q],regr.predict(lon11[q]),                                        X,Y,bathy,lon_tol=0.0052,lat_tol=0.00210,allow_land=False)
    for i in np.arange(x1-1,x1+2):
        for j in np.arange(j1-1,j1+2):
            dist[k]=tidetools.haversine(lon11[q],lat11[q],longitude[i,j],latitude[i,j])
            weights[k]=1.0/dist[k]
            value_3rd[k]=saline_nemo_3rd[i,j]*weights[k]
            value_4rd[k]=saline_nemo_4rd[i,j]*weights[k]
            values=values+value_3rd[k]
            valuess=valuess+value_4rd[k]
            k+=1
            
    return values, valuess, weights


def salinity_fxn(saline, route_name):
    #saline=sio.loadmat('/data/jieliu/MEOPAR/FerrySalinity/%s/%s_TSG%s.mat' %(route_name, route_name, date_str_yesterday))
    struct= (((saline['%s_TSG' %route_name])['output'])[0,0])['Practical_Salinity'][0,0]
    salinity = struct['data'][0,0]
    time = struct['matlabTime'][0,0]
    lonn = struct['longitude'][0,0]
    latt = struct['latitude'][0,0]
    
    
    a=len(time)
    lon1=np.zeros([a,1])
    lat1=np.zeros([a,1])
    salinity1=np.zeros([a,1])
    if route_name == 'HBDB':       
        run_lower = today.replace(hour = 2, minute = 40)
        run_upper = today.replace(hour= 4, minute = 20)
    elif route_name =='TWDP':
        run_lower = today.replace(hour = 3, minute =0)
        run_upper = today.replace(hour= 5, minute=0)
    elif route_name =='TWSB':
        run_lower = today.replace(hour = 2, minute=0)
        run_upper = today.replace(hour= 4, minute=0) 
    else:
        print ('This is not a station!')
    for i in np.arange(0,a):
        matlab_datenum = np.float(time[i])
        python_datetime = datetime.datetime.fromordinal(int(matlab_datenum))        + timedelta(days=matlab_datenum%1) - timedelta(days = 366)
        
        #if((python_datetime.year == run_date.year) & (python_datetime.month == run_date.month)\
          # & (python_datetime.day == run_date.day)
            #& (python_datetime.hour >= 3))&(python_datetime.hour < 5):
        if (python_datetime >= run_lower) &(python_datetime <= run_upper):
            lon1[i]=lonn[i]
            lat1[i]=latt[i]
            salinity1[i]=salinity[i]
            
    mask=lon1[:,0]!=0
    lon1_2_4=lon1[mask]
    lat1_2_4=lat1[mask]
    salinity1_2_4=salinity1[mask]
    lon11=lon1_2_4[0:-1:20]
    lat11=lat1_2_4[0:-1:20]
    salinity11=salinity1_2_4[0:-1:20]
    
    bathy, X, Y = tidetools.get_SS2_bathy_data()
    
    aa=date(run_date.year,run_date.month,run_date.day,run_date.day,'1h','grid_T') 
    
    date_str_title = today.strftime('%d-%b-%Y') ##creat a string based on this date
    tracers=nc.Dataset(aa[0])
    j=int(aa[0][65:67])
    jj=int(aa[0][67:69])
    latitude=tracers.variables['nav_lat'][:] 
    longitude=tracers.variables['nav_lon'][:] 
    saline_nemo = tracers.variables['vosaline']

    if route_name =='TWSB':
        saline_nemo_3rd = saline_nemo[2,1, 0:898, 0:398] 
        saline_nemo_4rd = saline_nemo[3,1, 0:898, 0:398]
    else:
        saline_nemo_3rd = saline_nemo[3,1, 0:898, 0:398] 
        saline_nemo_4rd = saline_nemo[4,1, 0:898, 0:398]
    #saline_nemo_3rd = saline_nemo[3,1, 0:898, 0:398] 
    #saline_nemo_4rd = saline_nemo[4,1, 0:898, 0:398]
    
    matrix=np.zeros([len(lon11),9])
    values=np.zeros([len(lon11),1])
    valuess=np.zeros([len(lon11),1])
    value_mean_3rd_hour=np.zeros([len(lon11),1])
    value_mean_4rd_hour=np.zeros([len(lon11),1]) 
    for q in np.arange(0,len(lon11)):
       values[q], valuess[q], matrix[q,:]=find_dist(q, lon11, lat11, X, Y,                                     bathy, longitude, latitude, saline_nemo_3rd, saline_nemo_4rd)
       value_mean_3rd_hour[q]=values[q]/sum(matrix[q])
       value_mean_4rd_hour[q]=valuess[q]/sum(matrix[q])

    return lon11, lat11, lon1_2_4, lat1_2_4,    value_mean_3rd_hour, value_mean_4rd_hour,    salinity11, salinity1_2_4,date_str_title

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

ferry_stations = {'Tsawwassen': {'lat': 49.0084,'lon': -123.1281},
                  'Duke': {'lat': 49.1632,'lon': -123.8909},
                  'Vancouver': {'lat': 49.2827,'lon': -123.1207},
                  'Horseshoe Bay':{'lat':49.3742 ,'lon':-123.2728 },
                  'Nanaimo': {'lat':49.1632 , 'lon':-123.8909 },
                  'Swartz':{'lat':48.6882 , 'lon':-123.4102 }
                 }


def salinity_ferry_route(grid_T, grid_B, PNW_coastline, route_name):
    """ plot daily salinity comparisons between ferry observations 
    and model results as well as ferry route with model salinity 
    distribution.
    
    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`
    
    :arg PNW_coastline: Coastline dataset.
    :type PNW_coastline: :class:`mat.Dataset`
    
    :arg ferry_sal: saline
    :type ferry_sal: numpy
    
    :returns: fig
    """

    fig, axs = plt.subplots(1, 2, figsize=(15, 8))

    figures.plot_map(axs[1], grid_B, PNW_coastline)
    axs[1].set_xlim(-124.5, -122.5)
    axs[1].set_ylim(48.2, 49.6)
    viz_tools.set_aspect(axs[1],coords='map',lats=latitude)
    cmap=plt.get_cmap('spectral')
    cmap.set_bad('burlywood')
    mesh=axs[1].contourf(longitude[:],latitude[:],sal_hr[:], 10, cmap=cmap)
    cbar=fig.colorbar(mesh)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')
    cbar.set_label('Pratical Salinity', color='white')
    
    axs[1].set_title('Ferry Route: 3am[UTC] 1.5m model result ', **title_font)
 
    bbox_args = dict(boxstyle='square', facecolor='white', alpha=0.7)
    if route_name == 'HBDB':
        stations=['Horseshoe Bay','Nanaimo','Vancouver']
    elif route_name =='TWDP':
        stations=['Tsawwassen','Duke','Vancouver']
    elif route_name =='TWSB':
        stations =['Tsawwassen','Swartz', 'Vancouver']
        
    for stn in stations:
        axs[1].plot(ferry_stations[stn]['lon'], ferry_stations[stn]['lat'], marker='D',                     color='white',                 markersize=10, markeredgewidth=2)
        
    axs[1].annotate (stations[0],(ferry_stations[stations[0]]['lon'] + 0.02,    ferry_stations[stations[0]]['lat'] + 0.12), fontsize=15, color='black', bbox=bbox_args )
    axs[1].annotate (stations[1],(ferry_stations[stations[1]]['lon'] - 0.5,    ferry_stations[stations[1]]['lat'] ),fontsize=15, color='black', bbox=bbox_args )
    axs[1].annotate (stations[2],(ferry_stations[stations[2]]['lon'] ,    ferry_stations[stations[2]]['lat']+ 0.09 ),fontsize=15, color='black', bbox=bbox_args )
    
    figures.axis_colors(axs[1], 'white')
    
    saline=sio.loadmat('/data/jieliu/MEOPAR/FerrySalinity/%s/%s_TSG%s.mat' %(route_name, route_name, date_str_yesterday))
    
    lon11, lat11, lon1_2_4, lat1_2_4,    value_mean_3rd_hour, value_mean_4rd_hour,    salinity11,salinity1_2_4, date_str_title = salinity_fxn(saline, route_name)
    axs[1].plot(lon11,lat11,'black', linewidth = 4)
    if route_name =='TWSB':
        model_salinity_3rd_hour=axs[0].plot(lon11,value_mean_3rd_hour,'DodgerBlue',\
                                    linewidth=2, label='2 am [UTC]')
        model_salinity_4rd_hour=axs[0].plot(lon11,value_mean_4rd_hour,'MediumBlue',\
                                        linewidth=2, label="3 am [UTC]" )
    else:
        model_salinity_3rd_hour=axs[0].plot(lon11,value_mean_3rd_hour,'DodgerBlue',\
                                    linewidth=2, label='3 am [UTC]')
        model_salinity_4rd_hour=axs[0].plot(lon11,value_mean_4rd_hour,'MediumBlue',\
                                        linewidth=2, label="4 am [UTC]" )

    observation_salinity=axs[0].plot(lon1_2_4,salinity1_2_4,'DarkGreen', linewidth=2, label="Observed")
    axs[0].text(0.25, -0.1,'Observations from Ocean Networks Canada',                 transform=axs[0].transAxes, color='white')

    axs[0].set_xlim(-124, -123)
    axs[0].set_ylim(0, 30)
    axs[0].set_title('Surface Salinity: ' + date_str_title, **title_font)
    axs[0].set_xlabel('Longitude', **axis_font)
    axs[0].set_ylabel('Practical Salinity', **axis_font)
    axs[0].legend(loc = 4)
    axs[0].grid()
   

    fig.patch.set_facecolor('#2B3E50')
    figures.axis_colors(axs[0], 'gray')
    
    return fig




