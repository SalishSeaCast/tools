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
import pytz
from scipy import interpolate as interp


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
    ax.set_xlabel('UTC Hour from {}'.format(results_date))
    ax.set_ylabel(
        '{label} [{units}]'
        .format(label=ssh.long_name.title(), units=ssh.units))
    ax.grid()
    ax.set_title(
        'Hourly Sea Surface Height at Point Atkinson on {}'.format(results_date))
    return fig

#
def PA_tidal_predictions(grid_T, figsize=(20,5)):
    """ Plots the tidal cycle at Point Atkinson during a 4 week period centred around the simulation start date.
    Assumes that a tidal prediction file exists in a specific directory.
    Tidal predictions were calculated with ttide based on a time series from 2013.

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
    Tidal predictions were calculated with ttide based on a time series from 2013.

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
    t_final=(nc_tools.timestamp(grid_T,-1)).datetime

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
    ax.set_xlim(t_orig,t_final)
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
    NOAA water levels from: http://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels

    :arg station_no: NOAA station number.
    :type station_no: integer

    :arg start_date: The start of the date range eg. 01-Jan-2014.
    :type start_date: string

    :arg end_date: The end of the date range eg. 02-Jan-2014.
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
    NOAA water levels from: http://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels

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
    t_final=(nc_tools.timestamp(grid_T,-1)).datetime
    start_date = t_orig.strftime('%d-%b-%Y')
    end_date = t_final.strftime('%d-%b-%Y')

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
    ax.set_xlim(t_orig,t_final)
    ax.set_ylim([-1.6,1.6])
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
    t_orig = (nc_tools.timestamp(grid_T,0)).datetime
    t_final = (nc_tools.timestamp(grid_T,-1)).datetime
    start_date = t_orig.strftime('%d-%b-%Y')
    end_date = t_final.strftime('%d-%b-%Y')

    #timestamp
    timestamp = nc_tools.timestamp(grid_T,index)

    #figure
    fig,(ax1,ax2) =plt.subplots(1,2,figsize=figsize)

    #curve plot
    ax1.plot(t,ssh_loc,label='Model')
    ax1.plot(t[index],ssh_loc[index],color='Indigo',marker='D',markersize=12,label='Maximum SSH')
    ax1.set_xlim(t_orig,t_final)
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

#
def Sandheads_winds(grid_T, figsize=(20,10)):
    """ Plot the observed winds at Sandheads during the simulation.
     Observations are from Environment Canada data: http://climate.weather.gc.ca/

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg figsize:  Figure size (width, height) in inches
    :type figsize: 2-tuple

    :returns: Matplotlib figure object instance
    """

    #simulation date range.
    t_orig=(nc_tools.timestamp(grid_T,0)).datetime
    t_end=(nc_tools.timestamp(grid_T,-1)).datetime
    #strings for timetamps of EC data
    start=t_orig.strftime('%d-%b-%Y')
    end=t_end.strftime('%d-%b-%Y')

    [winds,dirs,temps,time, lat,lon] = stormtools.get_EC_observations('Sandheads',start,end)

    fig,axs=plt.subplots(2,1,figsize=figsize)
    #plotting wind speed
    ax=axs[0]
    ax.set_title('Winds at Sandheads ' + start )
    ax.plot(time,winds)
    ax.set_xlim([time[0],time[-1]])
    ax.set_ylim([0,20])
    ax.set_ylabel('Wind speed (m/s)')
    #plotting wind direction
    ax=axs[1]
    ax.plot(time,dirs)
    ax.set_ylabel('Wind direction \n (degress CCW of East)')
    ax.set_ylim([0,360])
    ax.set_xlim([time[0],time[-1]])
    ax.set_xlabel('Time [UTC]')

    return fig

#
def thalweg_salinity(grid_T_d,figsize=(20,8),cs = [26,27,28,29,30,30.2,30.4,30.6,30.8,31,32,33,34]):
    """ Plot the daily averaged salinity field along the thalweg.

    :arg grid_T_d: Daily tracer results dataset from NEMO.
    :type grid_T_d: :class:`netCDF4.Dataset`

    :arg figsize:  Figure size (width, height) in inches
    :type figsize: 2-tuple

    :arg cs: list of salinity contour levels for shading.
    :type cs: list

    :returns: Matplotlib figure object instance
    """

    lon_d = grid_T_d.variables['nav_lon']
    lat_d = grid_T_d.variables['nav_lat']
    dep_d = grid_T_d.variables['deptht']
    sal_d = grid_T_d.variables['vosaline']

    lines = np.loadtxt('/data/nsoontie/MEOPAR/tools/analysis_tools/thalweg.txt', delimiter=" ", unpack=False)
    lines = lines.astype(int)

    thalweg_lon = lon_d[lines[:,0],lines[:,1]]
    thalweg_lat = lat_d[lines[:,0],lines[:,1]]

    ds=np.arange(0,lines.shape[0],1);
    XX,ZZ = np.meshgrid(ds,-dep_d[:])

    salP=sal_d[0,:,lines[:,0],lines[:,1]]
    salP= np.ma.masked_values(salP,0)

    fig,ax=plt.subplots(1,1,figsize=figsize)
    land_colour = 'burlywood'
    ax.set_axis_bgcolor(land_colour)
    mesh=ax.contourf(XX,ZZ,salP,cs,cmap='hsv',extend='both')

    cbar=fig.colorbar(mesh,ax=ax)
    cbar.set_ticks(cs)
    cbar.set_label('Practical Salinity [psu]')

    timestamp = nc_tools.timestamp(grid_T_d,0)
    ax.set_title('Salinity field along thalweg: ' + timestamp.format('DD-MMM-YYYY'))
    ax.set_ylabel('Depth [m]')
    ax.set_xlabel('position along thalweg')

    return fig

#
def plot_surface(grid_T_d, grid_U_d, grid_V_d, gridB, figsize=(20,10)):
    """Function that plots the daily average surface salinity, temperature and currents.

    :arg grid_T_d: Daily tracer results dataset from NEMO.
    :type grid_T_d: :class:`netCDF4.Dataset`

    :arg grid_U_d: Daily zonal velocity results dataset from NEMO.
    :type grid_U_d: :class:`netCDF4.Dataset`

    :arg grid_V_d: Daily meridional velocity results dataset from NEMO.
    :type grid_V_d: :class:`netCDF4.Dataset`

    :arg gridB: Bathymetry dataset for the Salish Sea NEMO model.
    :type gridB: :class:`netCDF4.Dataset`

    :arg figsize: figure size (width, height) in inches.
    :type figsize: 2-tuple

    """

    #loading lon, lat, depth, salinity, temperature
    lon_d = grid_T_d.variables['nav_lon']
    lat_d = grid_T_d.variables['nav_lat']
    dep_d = grid_T_d.variables['deptht']
    sal_d = grid_T_d.variables['vosaline']
    tem_d = grid_T_d.variables['votemper']

    bathy, X, Y = tidetools.get_bathy_data(gridB)

    #tracers ready to plot
    t, z = 0, 0
    sal_d = np.ma.masked_values(sal_d[t, z], 0)
    tem_d = np.ma.masked_values(tem_d[t, z], 0)


    #for loop
    tracers = [sal_d, tem_d]
    titles = ['Average Salinity: ','Average Temperature: ']
    cmaps = ['ocean','jet']
    units = ['[psu]','[degC]']

    fig, (ax1,ax2,ax3) = plt.subplots(1, 3, figsize=figsize)
    axs = [ax1, ax2]
    plots = np.arange(1,3,1)

    #***temperature and salinity plots

    for ax,tracer,title,cmap,unit,plot in zip(axs,tracers,titles,cmaps,units,plots):
        #general set up
        viz_tools.set_aspect(ax)
        land_colour = 'burlywood'
        ax.set_axis_bgcolor(land_colour)
        cmap = plt.get_cmap(cmap)

        #colourmap breakdown
        if plot == 1:
            cs = [0,4,8,12,16,20,24,28,32,36]
        if plot == 2:
            cs = [0,2,4,6,8,10,12,14,16,18,20]

        #plotting tracers
        mesh=ax.contourf(tracer,cs,cmap=cmap,extend='both')

        #colour bars
        cbar = fig.colorbar(mesh,ax=ax)
        cbar.set_ticks(cs)

        #labels
        ax.grid()
        ax.set_xlabel('x Index')
        ax.set_ylabel('y Index')
        timestamp = nc_tools.timestamp(grid_T_d,0)
        ax.set_title(title + timestamp.format('DD-MMM-YYYY'))
        cbar.set_label(unit)

    #loading velocity components
    ugrid = grid_U_d.variables['vozocrtx']
    vgrid = grid_V_d.variables['vomecrty']
    zlevels = grid_U_d.variables['depthu']
    timesteps = grid_U_d.variables['time_counter']

    #day's average, surface velocity field
    t, zlevel = 0, 0

    #region
    y_slice = np.arange(0, ugrid.shape[2])
    x_slice = np.arange(0, ugrid.shape[3])

    arrow_step = 25
    y_slice_a = y_slice[::arrow_step]
    x_slice_a = x_slice[::arrow_step]

    #masking arrays
    ugrid_tzyx = np.ma.masked_values(ugrid[t, zlevel, y_slice_a, x_slice_a], 0)
    vgrid_tzyx = np.ma.masked_values(vgrid[t, zlevel, y_slice_a, x_slice_a], 0)
    #unstagger velocity values
    u_tzyx, v_tzyx = viz_tools.unstagger(ugrid_tzyx, vgrid_tzyx)
    #velocity magnitudes
    speeds = np.sqrt(np.square(u_tzyx) + np.square(v_tzyx))

    #***velocity plot
    viz_tools.set_aspect(ax3)
    cs = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]

    quiver = ax3.quiver(x_slice_a[1:], y_slice_a[1:], u_tzyx, v_tzyx, speeds, pivot='mid', cmap='gnuplot_r', width=0.015)
    viz_tools.plot_land_mask(ax3, gridB, xslice=x_slice, yslice=y_slice, color='burlywood')

    cbar = fig.colorbar(quiver,ax=ax3)
    cbar.set_ticks(cs)
    cbar.set_label('[m / s]')

    ax3.set_xlim(x_slice[0], x_slice[-1])
    ax3.set_ylim(y_slice[0], y_slice[-1])
    ax3.grid()

    ax3.set_xlabel('x Index')
    ax3.set_ylabel('y Index')
    ax3.set_title('Average Velocity Field: ' + timestamp.format('DD-MMM-YYYY') +
                  u', depth\u2248{d:.2f} {z.units}'.format(d=zlevels[zlevel], z=zlevels))
    ax3.quiverkey(quiver, 355, 850, 1, '1 m/s', coordinates='data', color='Indigo', labelcolor='black')

    return fig

    #***VENUS

#
def dateparse(s):
    """Parse the dates from the VENUS files"""
    unaware =datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
    aware = unaware.replace(tzinfo=pytz.timezone('utc'))
    return  aware

#
def load_VENUS(station):
    """
    Loads the most recent State of the Ocean data from the VENUS node indicated by station. T
    This data set includes pressure, temperature, and salinity among other things.
    See: http://venus.uvic.ca/research/state-of-the-ocean/

    :arg station: the name of the station, either "East" or "Central"
    :type station: string

    :returns: A DataFrame with the VENUS data, and the longitude and latitude and depth (m) of the node
    """
    #define location
    filename = 'SG-{}-VIP/VSG-{}-VIP-State_of_Ocean.txt'.format(station,station)
    if station == 'East':
        lat = 49.0419
        lon = -123.3176
        depth = 170
    elif station == 'Central':
        lat = 49.0401
        lon = -123.4261
        depth=300

    #hit the website
    url = 'http://venus.uvic.ca/scripts/log_download.php'
    params = {
    'userid': 'nsoontie@eos.ubc.ca',
    'filename': filename,
    }
    response = requests.get(url, params=params)

    #parse the data
    fakefile = StringIO(response.content)
    data = pd.read_csv(fakefile,delimiter=' ,',skiprows=17,
                   names=['date','pressure','pflag','temp','tflag','sal','sflag','sigmaT','stflag','oxygen','oflag'],
                   parse_dates=['date'],date_parser=dateparse)

    return data, lon, lat, depth

#
def plot_VENUS(ax_sal, ax_temp, station, start, end):
    """
    Plot a time series of the VENUS data between start and end.

    :arg ax_sal: The axis in which the salinity is displayed.
    :type ax_sal: axis object

    :arg ax_temp: The axis in which the temperature is displayed.
    :type ax_temp: axis object

    :arg station: the name of the station, either "East" or "Central"
    :type station: string

    :arg start: the start date of the plot
    :type start: datetime object

    :arg end: the end date of the plot
    :type end: datetime object

    :returns: the longitude, latitude and depth of the VENUS station

    """
    [data,lon,lat,depth]= load_VENUS(station)
    ax_sal.plot(data.date[:],data.sal,'r-',label='VENUS')
    ax_sal.set_xlim([start,end])
    ax_temp.plot(data.date[:],data.temp,'r-',label='VENUS')
    ax_temp.set_xlim([start,end])

    return lon, lat, depth

#
def interpolate_depth(data, depth_array, depth_new):
    """
    Interpolates data field to a desired depth.

    :arg data: The data to be interpolated. Should be one-dimensional over the z-axis.
    :type data: 1-d numpy array

    :arg depth_array: The z-axis for data.
    :type depth_array: 1-d numpy array.

    :arg depth_new: The new depth to which we want to interpolate.
    :type depth_new: float

    :returns: a float representing the field interpolated to the desired depth.
    """
    #using masked arrays for more accurate interpolation
    mu=data==0
    datao=np.ma.array(data,mask=mu)
    mu=depth_array==0
    depth_arrayo=np.ma.array(depth_array,mask=mu)
    #interpolations
    f= interp.interp1d(depth_arrayo,datao)
    data_interp = f(depth_new)
    return data_interp

#
def compare_VENUS(station, grid_T, gridB, figsize=(6,10)):
    """
    Compare the model's temperature and salinity with observations VENUS station (either Central or East).

    :arg station: The name of the station ('East' or 'Central')
    :type station: string

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg gridB: Model bathymetry file.
    :type gridB: :class:`netCDF4.Dataset`

    :arg figsize: figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: Matplotlib figure object instance
    """

    #set date of this simulation
    t_orig=(nc_tools.timestamp(grid_T,0)).datetime
    t_end =((nc_tools.timestamp(grid_T,-1)).datetime)

    #load bathymetry
    bathy, X, Y = tidetools.get_bathy_data(gridB)

    #process VENUS data
    fig,(ax_sal, ax_temp) = plt.subplots(2,1,figsize=figsize,sharex=True)
    fig.autofmt_xdate()
    lon, lat, depth = plot_VENUS(ax_sal, ax_temp, station, t_orig, t_end)

    #identify grid point of VENUS station (could this just be saved somewhere?)
    [j,i]=tidetools.find_closest_model_point(lon,lat,X,Y,bathy,allow_land=True)
    #load model data
    sal = grid_T.variables['vosaline'][:,:,j,i]
    temp = grid_T.variables['votemper'][:,:,j,i]
    ds = grid_T.variables['deptht']
    count=grid_T.variables['time_counter'][:]
    t = nc_tools.timestamp(grid_T,np.arange(count.shape[0]))
    #convert times to datetimes because that is what the plot wants
    for i in range(len(t)):
        t[i]=t[i].datetime

    #interpolating data
    salc=[]
    tempc=[]
    for ind in np.arange(0,sal.shape[0]):
        salc.append(interpolate_depth(sal[ind,:],ds,depth))
        tempc.append(interpolate_depth(temp[ind,:],ds,depth))

    #plot model data
    ax_sal.plot(t,salc,'-b',label='model')
    ax_temp.plot(t,tempc,'-b',label='model')

    #pretty the plot
    ax_sal.set_ylabel('Practical Salinity [psu]')
    ax_sal.legend(loc=0)
    ax_sal.set_title('VENUS - {}'.format(station) )
    ax_sal.set_ylim([30,32])
    ax_temp.set_ylabel('Temperature [deg C]')
    ax_temp.set_xlabel('Time [UTC]')
    ax_temp.set_ylim([7,11])

    return fig

#


