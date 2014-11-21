# Copyright 2013-2014 The Salish Sea MEOPAR contributors
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




"""A collection of Python functions to produce model results visualization
figures for analysis and model evaluation of daily nowcast/forecast runs.
"""
from __future__ import division
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from salishsea_tools import nc_tools, viz_tools, stormtools, tidetools
import datetime
import requests
import arrow
from StringIO import StringIO




#
def ssh_PtAtkinson(grid_T, gridB=None, figsize=(20, 5)):
    """Return a figure containing a plot of hourly sea surface height at
    Pt. Atkinson.

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg gridB: Bathymetry dataset for the Salish Sea NEMO model.
    :type gridB: :class:`netCDF4.Dataset`

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: Matplotlib figure object instance
    """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ssh = grid_T.variables['sossheig']
    results_date = nc_tools.timestamp(grid_T, 0).format('YYYY-MM-DD')
    ax.plot(ssh[:, 468, 328], 'o')
    ax.set_xlim(0, 23)
    ax.set_xlabel('UTC Hour on {}'.format(results_date))
    ax.set_ylabel(
        '{label} [{units}]'
        .format(label=ssh.long_name.title(), units=ssh.units))
    ax.grid()
    ax.set_title(
        'Hourly Sea Surface Height at Point Atkinson on {}'.format(results_date))
    return fig

#
def PA_tidal_predictions(grid_T, figsize=(20,5)):
    """ Plots the tidal cycle at Point Atkinson during a 4 week period centred around the dsimulation start date.
    Assumes that a tidal prediction file exists in a specific directory.
    
    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple
    
    :returns: Matplotlib figure object instance
    """
    #beginning and end time of the simulation file.
    t_orig=(nc_tools.timestamp(grid_T,0)).datetime
    t_end =((nc_tools.timestamp(grid_T,-1)).datetime)
    
    #set axis limits 2 weeks before and after start date
    ax_start = t_orig - datetime.timedelta(weeks=2)
    ax_end = t_orig + datetime.timedelta(weeks=2)
    ylims=[-3,3]
    
    #load the tidal prediciton file
    path='/data/nsoontie/MEOPAR/analysis/Susan/'
    filename='Point Atkinson_t_tide_compare8_31-Dec-{}_02-Jan-{}.csv'.format(t_orig.year-1,t_orig.year+1)
    tfile = path+filename
    ttide,msl= stormtools.load_tidal_predictions(tfile)
    
    #plotting
    fig,ax=plt.subplots(1,1,figsize=figsize)
    fig.autofmt_xdate()
    ax.plot(ttide.time,ttide.pred_all,'-k')
    #line indicating current date
    ax.plot([t_orig,t_orig],ylims,'-r')
    ax.plot([t_end,t_end],ylims,'-r')
    #axis limits and labels
    ax.set_xlim([ax_start,ax_end])
    ax.set_ylim(ylims)
    ax.set_title('Tidal Predictions at Point Atkinson')
    ax.set_ylabel('Sea Surface Height [m]')
    
    return fig

#
def compare_tidal_predictions(name, grid_T, gridB, figsize=(20,5)):
    """ Compares modelled water levels to tidal predictions at a station over one day.
    It is assummed that the tidal predictions were calculated ahead of time and stored in a very specific location.
    Tidal predictions were calculated with the eight consituents used in the model.
    
    :arg name: Name of station (e.g Point Atkinson).
    :type name: string
    
    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`
    
    :arg gridB: Bathymetry dataset for the Salish Sea NEMO model.
    :type gridB: :class:`netCDF4.Dataset`
    
    :arg figsize:  Figure size (width, height) in inches
    :type figsize: 2-tuple
    
    :returns: Matplotlib figure object instance
    """
    
    #Locations of interest.
    lons={'Point Atkinson':-123.26}
    lats={'Point Atkinson': 49.33}
    
    #load bathymetry
    bathy, X, Y = tidetools.get_bathy_data(gridB)
    
    #time stamp of simulation
    t_orig=(nc_tools.timestamp(grid_T,0)).datetime
    
    #loading the tidal predictions
    path='/data/nsoontie/MEOPAR/analysis/Susan/'
    filename='_t_tide_compare8_31-Dec-{}_02-Jan-{}.csv'.format(t_orig.year-1,t_orig.year+1)
    tfile = path+name+filename
    ttide,msl= stormtools.load_tidal_predictions(tfile)
    
    #identify grid point of location of interest
    [j,i]=tidetools.find_closest_model_point(lons[name],lats[name],X,Y,bathy,allow_land=True)
    
    #load variables for plotting
    ssh = grid_T.variables['sossheig'][:,j,i]
    count=grid_T.variables['time_counter'][:]
    t = nc_tools.timestamp(grid_T,np.arange(count.shape[0]))
    #convert times to datetimes because that is what the plot wants
    for i in range(len(t)):
        t[i]=t[i].datetime
    
    #plotting
    fig,ax =plt.subplots(1,1,figsize=figsize) 
    ax.plot(t,ssh,label='model')
    ax.plot(ttide.time,ttide.pred_8,label='tidal predictions')
    ax.set_xlim(t_orig,t_orig + datetime.timedelta(days=1))
    ax.set_ylim([-3,3])
    ax.legend(loc=0)
    ax.set_title(name)
    ax.set_ylabel('Water levels wrt MSL (m)')
    ax.set_xlabel('time [UTC]')
    
    return fig

#
def get_NOAA_wlevels(station_no, start_date, end_date):
    """ Retrieves recent, 6 minute interval, NOAA water levels relative to mean sea level
    from a station in a given date range.
    
    :arg station_no: NOAA station number.
    :type station_no: integer
    
    :arg start_date: The start of the date range eg. 01-Jan-2014.
    :type start_date: string
    
    :arg end_date: The end of the date range ef. 02-Jan-2014.
    :type end_date: string
    
    :returns: DataFrame object with time and wlev columns, among others that are irrelevant.
    """
    
    outfile = 'wlev_'+str(station_no)+'_'+str(start_date)+'_'+str(end_date)+'.csv'
    
    st_ar=arrow.Arrow.strptime(start_date, '%d-%b-%Y')
    end_ar=arrow.Arrow.strptime(end_date, '%d-%b-%Y')
    
    base_url = 'http://tidesandcurrents.noaa.gov/api/datagetter?product=water_level&application=NOS.COOPS.TAC.WL'
    params = {
    'begin_date': st_ar.format('YYYYMMDD'),
    'end_date': end_ar.format('YYYYMMDD'),
    'datum':  'MSL',
    'station': str(station_no),
    'time_zone': 'GMT',
    'units':'metric',
    'format': 'csv',}

    response = requests.get(base_url, params=params)

    fakefile = StringIO(response.content)
    
    obs = pd.read_csv(fakefile)
    obs=obs.rename(columns={'Date Time': 'time', ' Water Level': 'wlev'})
    
    return obs

#
def compare_water_levels(name, grid_T, gridB, figsize=(20,5) ):
    """ Compares modelled water levels to observed water levels at a NOAA station over one day.
    
    :arg name: Name of the NOAA station (e.g NeahBay, CherryPoint, FridayHarbor).
    :type name: string
    
    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`
    
    :arg gridB: Bathymetry dataset for the Salish Sea NEMO model.
    :type gridB: :class:`netCDF4.Dataset`
    
    :arg figsize:  Figure size (width, height) in inches
    :type figsize: 2-tuple

    :returns: Matplotlib figure object instance
    """
    
    stations = {'CherryPoint': 9449424,'NeahBay':9443090, 'FridayHarbor': 9449880 }
    lats={'CherryPoint': 48.866667,'NeahBay': 48.4, 'FridayHarbor': 48.55}
    lons={'CherryPoint': -122.766667, 'NeahBay':-124.6, 'FridayHarbor': -123.016667}
    
    bathy, X, Y = tidetools.get_bathy_data(gridB)
    
    t_orig=(nc_tools.timestamp(grid_T,0)).datetime
    start_date = t_orig.strftime('%d-%b-%Y')
    end_date = (t_orig + datetime.timedelta(days=1)).strftime('%d-%b-%Y')
    
    obs=get_NOAA_wlevels(stations[name],start_date,end_date)
    
    [j,i]=tidetools.find_closest_model_point(lons[name],lats[name],X,Y,bathy,allow_land=False)
    
    ssh = grid_T.variables['sossheig'][:,j,i]
    count=grid_T.variables['time_counter'][:]
    t = nc_tools.timestamp(grid_T,np.arange(count.shape[0]))
    for i in range(len(t)):
        t[i]=t[i].datetime
    
    fig,ax =plt.subplots(1,1,figsize=figsize) 
    ax.plot(t,ssh,label='model')
    ax.plot(obs.time,obs.wlev,label='observed water levels')
    ax.set_xlim(t_orig,t_orig + datetime.timedelta(days=1))
    ax.set_ylim([-1.5,1.5])
    ax.legend(loc=0)
    ax.set_title(name)
    ax.set_ylabel('Water levels wrt MSL (m)')

    return fig

#
def PA_max_ssh(grid_T, gridB, figsize=(15,10)):
    """Function that plots the water level at every hour throughout the day and identifies the maximum.
    It also plots the sea surface height throughout the region for the time when the sea surface height
    was at its maximum at Point Atkinson.
    
    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`
    
    :arg gridB: Bathymetry dataset for the Salish Sea NEMO model.
    :type gridB: :class:`netCDF4.Dataset`
    
    :arg figsize:  Figure size (width, height) in inches
    :type figsize: 2-tuple
    
    :returns: Matplotlib figure object instance
    """

    #defining Point Atkinson
    lon_PA=-123.26
    lat_PA= 49.33
    bathy, X, Y = tidetools.get_bathy_data(gridB)
    [j,i]=tidetools.find_closest_model_point(lon_PA,lat_PA,X,Y,bathy,allow_land=True)
    
    #loading sea surface height
    ssh = grid_T.variables['sossheig']
    #loading sea surface height at Point Atkinson
    ssh_loc = ssh[:,j,i]
    #index when sea surface height is at its maximum at Point Atkinson
    m = max(ssh_loc)
    index = [k for k, l in enumerate(ssh_loc) if l == m]
    index = index[0]
    #sea surface height when there is a maximum at Point Atkinson
    ssh_max = np.ma.masked_values(ssh[index], 0)
    
    #time for curve
    count=grid_T.variables['time_counter'][:]
    t = nc_tools.timestamp(grid_T,np.arange(count.shape[0]))
    for ind in range(len(t)):
        t[ind]=t[ind].datetime
    t_orig=(nc_tools.timestamp(grid_T,0)).datetime
    start_date = t_orig.strftime('%d-%b-%Y')
    end_date = (t_orig + datetime.timedelta(days=1)).strftime('%d-%b-%Y')
    
    #timestamp
    timestamp = nc_tools.timestamp(grid_T,index)
    
    #figure
    fig,(ax1,ax2) =plt.subplots(1,2,figsize=figsize) 
    
    #curve plot
    ax1.plot(t,ssh_loc,label='Model')
    ax1.plot(t[index],ssh_loc[index],color='Indigo',marker='D',markersize=12,label='Maximum SSH')
    ax1.set_xlim(t_orig,t_orig + datetime.timedelta(days=1))
    ax1.set_ylim([-3,3])
    ax1.set_title('Point Atkinson')
    ax1.set_xlabel(timestamp.strftime('%d-%b-%Y'))
    ax1.set_ylabel('Water levels wrt MSL (m)')
    ax1.legend(loc = 0, numpoints = 1)
    ax1.set_position((0, 0.3, 0.55, 0.4))
    
    #ssh profile
    viz_tools.set_aspect(ax2)
    land_colour = 'burlywood'
    ax2.set_axis_bgcolor(land_colour)
    cmap = plt.get_cmap('RdYlGn_r')
    cs = [-2.5,-2,-1.5,-1,-0.5,0,0.5,1,1.5,2,2.4,2.8,3]
    mesh=ax2.contourf(ssh_max,cs,cmap=cmap,extend='both')
    cbar = fig.colorbar(mesh,ax=ax2)
    cbar.set_ticks(cs)
    cbar.set_label('[m]')
    ax2.grid()
    ax2.set_xlabel('x Index')
    ax2.set_ylabel('y Index')
    viz_tools.plot_coastline(ax2,gridB)
    ax2.set_title('Sea Suface Height: ' + timestamp.strftime('%d-%b-%Y, %H:%M'))
    ax2.plot(i,j,marker='D',color='Indigo',ms=8)

    return fig
