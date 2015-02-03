# Copyright 2013-2015 The Salish Sea MEOPAR contributors
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

from cStringIO import StringIO
import datetime
import glob
import os

import arrow
from dateutil import tz
import matplotlib
from matplotlib.backends import backend_agg as backend
import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import pandas as pd
import requests
from scipy import interpolate as interp

from salishsea_tools import (
    nc_tools,
    viz_tools,
    stormtools,
    tidetools,
)


# Plotting colors
model_c = 'MediumBlue'
observations_c = 'DarkGreen'
predictions_c = 'MediumVioletRed'
stations_c = cm.rainbow(np.linspace(0, 1, 7))

# Time shift for plotting in PST
time_shift = datetime.timedelta(hours=-8)
hfmt = mdates.DateFormatter('%m/%d %H:%M')

# Font format
title_font = {
    'fontname': 'Bitstream Vera Sans', 'size': '15', 'color': 'black',
    'weight': 'medium'
    }
axis_font = {'fontname': 'Bitstream Vera Sans', 'size': '13'}

# Average mean sea level calculated over 1983-2001
# (To be used to centre model output about mean sea level)
MSL_DATUMS = {
    'Point Atkinson': 3.10, 'Victoria': 1.90,
    'Campbell River': 2.89, 'Patricia Bay': 2.30}


def save_image(fig, filename, **kwargs):
    """Save fig as an image file in filename.

    :arg fig: Figure object to save as image file.
    :type fig: :class:`matplotlib.Figure`

    :arg filename: File path/name to save fig object to.
                   The filename extension specifies the type of image
                   file to create;
                   e.g. .png, .svg, etc.
    :type filename: str

    :arg kwargs: Keyword argument names and values to control how fig
                 is rendered;
                 e.g. :kbd:`facecolor=fig.get_facecolor()`,
                 :kbd:`bbox_inches='tight', etc.
                 See the matplotlib docs for details.
    :type kwargs: dict
    """
    canvas = backend.FigureCanvasAgg(fig)
    canvas.print_figure(filename, **kwargs)

def axis_colors(ax, plot):
  """ Formats the background colour of plots and colours
  of labels.

  :arg ax: Axis to be formatted.
  :type ax: axis object

  :arg plot: Keyword for background needed for plot.
  :type plot: string

  :returns: axis format
  """

  labels_c = 'white'
  ticks_c = 'white'
  spines_c = 'white'

  if plot == 'blue':
      ax.set_axis_bgcolor('#2B3E50')
  if plot == 'gray':
      ax.set_axis_bgcolor('#DBDEE1')
  if plot == 'white':
      ax.set_axis_bgcolor('white')

  ax.xaxis.label.set_color(labels_c), ax.yaxis.label.set_color(labels_c)
  ax.tick_params(axis='x', colors=ticks_c), ax.tick_params(axis='y', colors=ticks_c)
  ax.spines['bottom'].set_color(spines_c), ax.spines['top'].set_color(spines_c)
  ax.spines['left'].set_color(spines_c), ax.spines['right'].set_color(spines_c)
  ax.title.set_color('white')

  return ax

def station_coords():
    """ Returns the longitudes and latitudes for  key stations.
    Stations are Campbell River, Point Atkinson, Victoria,
    Cherry Point, Neah Bay, Friday Harbor, and Sandheads.

    :returns: coordinates (lats, lons).
    """

    lats = {'Campbell River': 50.04, 'Point Atkinson': 49.33,
            'Victoria': 48.41, 'Cherry Point': 48.866667,
            'Neah Bay': 48.4, 'Friday Harbor': 48.55,
            'Sandheads': 49.10}
    lons = {'Campbell River': -125.24, 'Point Atkinson': -123.25,
            'Victoria': -123.36, 'Cherry Point': -122.766667,
            'Neah Bay': -124.6, 'Friday Harbor': -123.016667,
            'Sandheads': -123.30}

    return lats, lons

def find_model_point(lon, lat, X, Y):
  """ Finds a model grid point close to a specified latitude and longitude.

  :arg lon: The longitude we are trying to match.
  :type lon: float

  :arg lat: The latitude we are trying to match.
  :type lat: float

  :arg X: The model longitude grid.
  :type X: numpy array

  :arg Y: The model latitude grid.
  :type Y: numpy array

  :returns: x-index (x1) and y-index (y1) of the closest model grid point.
  """

  # Tolerance for searching for grid points
  # (approximate distances between adjacent grid points)
  tol1 = 0.015 # lon
  tol2 = 0.015# lat

  # Search for a grid point with longitude or latitude within
  # tolerance of measured location
  x1, y1 = np.where(
      np.logical_and(
          (np.logical_and(X > lon-tol1, X < lon+tol1)),
          (np.logical_and(Y > lat-tol2, Y < lat+tol2))))

  return x1[0], y1[0]

def interpolate_depth(data, depth_array, depth_new):
  """ Interpolates data field to a desired depth.

  :arg data: The data to be interpolated. Should be one-dimensional over the z-axis.
  :type data: 1-d numpy array

  :arg depth_array: The z-axis for data.
  :type depth_array: 1-d numpy array

  :arg depth_new: The new depth to which we want to interpolate.
  :type depth_new: float

  :returns: float representing the field interpolated to the desired depth (data_interp).
  """

  # Masked arrays are used for more accurate interpolation.
  mu=data==0
  datao=np.ma.array(data,mask=mu)
  mu=depth_array==0
  depth_arrayo=np.ma.array(depth_array,mask=mu)

  # Interpolations
  f= interp.interp1d(depth_arrayo,datao)
  data_interp = f(depth_new)

  return data_interp

def get_model_time_variables(grid_T):
    """ Returns important model time variables.

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :returns: simulation star time (t_orig), simulation end time (t_final),
    and array (t) of output times all as datetime objects.
    """

    # Time range
    t_orig=(nc_tools.timestamp(grid_T,0)).datetime
    t_final=(nc_tools.timestamp(grid_T,-1)).datetime

    # Time for curve
    count=grid_T.variables['time_counter'][:]
    t = nc_tools.timestamp(grid_T,np.arange(count.shape[0]))
    for ind in range(len(t)):
        t[ind]=t[ind].datetime
    t=np.array(t)

    return t_orig,t_final,t

def dateparse(s):
    """ Parse the dates from the VENUS files."""

    unaware =datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%f')
    aware = unaware.replace(tzinfo=tz.tzutc())

    return  aware

def dateparse_NOAA(s):
    """ Parse the dates from the NOAA files."""

    unaware =datetime.datetime.strptime(s, '%Y-%m-%d %H:%M')
    aware = unaware.replace(tzinfo=tz.tzutc())

    return  aware

def dateparse_PAObs(s1,s2,s3,s4):
  """ Parse dates for Point Atkinson observations."""

  s=s1+s2+s3+s4
  unaware =datetime.datetime.strptime(s, '%Y%m%d%H:%M')
  aware = unaware.replace(tzinfo=tz.tzutc())

  return  aware


def load_PA_observations():
  """ Loads the recent water level observations at Point Atkinson.

  Times are in UTC and water level is in metres with respect to Chart Datum.

  :returns: DataFrame object (obs) with a time column and wlev column.
  """

  filename = '/data/nsoontie/MEOPAR/analysis/Nancy/tides/PA_observations/ptatkin_rt.dat'

  obs = pd.read_csv(filename, delimiter=' ',parse_dates=[[0,1,2,3]],header=None,
				date_parser=dateparse_PAObs)
  obs=obs.rename(columns={'0_1_2_3':'time',4:'wlev'})

  return obs


def get_NOAA_wlevels(station_no, start_date, end_date):
    """ Retrieves recent NOAA water levels from a station in a given
    date range.

    NOAA water levels are at 6 minute intervals and are relative to
    mean sea level.
    See: http://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels.

    :arg station_no: NOAA station number.
    :type station_no: int

    :arg start_date: The start of the date range; e.g. 01-Jan-2014.
    :type start_date: str

    :arg end_date: The end of the date range; e.g. 02-Jan-2014.
    :type end_date: str

    :returns: DataFrame object (obs) with time and wlev columns,
    among others that are irrelevant.
    """

    # Time range
    st_ar = arrow.Arrow.strptime(start_date, '%d-%b-%Y')
    end_ar = arrow.Arrow.strptime(end_date, '%d-%b-%Y')

    base_url = (
        'http://tidesandcurrents.noaa.gov/api/datagetter'
        '?product=water_level&application=NOS.COOPS.TAC.WL')
    params = {
        'begin_date': st_ar.format('YYYYMMDD'),
        'end_date': end_ar.format('YYYYMMDD'),
        'datum':  'MSL',
        'station': str(station_no),
        'time_zone': 'GMT',
        'units': 'metric',
        'format': 'csv',
    }
    response = requests.get(base_url, params=params)

    fakefile = StringIO(response.content)
    try:
        obs = pd.read_csv(
            fakefile, parse_dates=[0], date_parser=dateparse_NOAA)
    except ValueError:
        data = {'Date Time': st_ar.datetime, ' Water Level': float('NaN')}
        obs = pd.DataFrame(data=data, index=[0])
    obs = obs.rename(columns={'Date Time': 'time', ' Water Level': 'wlev'})
    return obs


def get_NOAA_tides(station_no, start_date, end_date):
    """ Retrieves NOAA predicted tides from a station in a given date range.

    NOAA predicted tides are at 6-minute intervals and are relative to
    mean sea level. See:
    http://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels.

    :arg station_no: NOAA station number.
    :type station_no: integer

    :arg start_date: The start of the date range eg. 01-Jan-2014.
    :type start_date: string

    :arg end_date: The end of the date range eg. 02-Jan-2014.
    :type end_date: string

    :returns: DataFrame object (tides) with time and pred columns.
    """

    # Time range
    st_ar = arrow.Arrow.strptime(start_date, '%d-%b-%Y')
    end_ar = arrow.Arrow.strptime(end_date, '%d-%b-%Y')

    base_url = 'http://tidesandcurrents.noaa.gov/api/datagetter?product=predictions&application=NOS.COOPS.TAC.WL'
    params = {
        'begin_date': st_ar.format('YYYYMMDD'),
        'end_date': end_ar.format('YYYYMMDD'),
        'datum':  'MSL',
        'station': str(station_no),
        'time_zone': 'GMT',
        'units': 'metric',
        'interval': '',
        'format': 'csv', }

    response = requests.get(base_url, params=params)

    fakefile = StringIO(response.content)
    try:
        tides = pd.read_csv(
            fakefile, parse_dates=[0], date_parser=dateparse_NOAA)
    except ValueError:
        data = {'Date Time': st_ar.datetime, ' Prediction': float('NaN')}
        tides = pd.DataFrame(data=data, index=[0])
    tides = tides.rename(columns={'Date Time': 'time', ' Prediction': 'pred'})
    return tides


def get_maxes(ssh, t, res, lon, lat, model_path):
    """ Identifies maximum ssh and other important features such as the timing,
    residual, and wind speed.

    :arg ssh: The ssh field to be maximized.
    :type ssh: numpy array

    :arg t: The times corresponding to the ssh.
    :type t: numpy array

    :arg res: The residual.
    :type res: numpy array

    :arg lon: The longitude of the station for looking up model winds.
    :type lon: float

    :arg lat: The latitude of the station for looking up model winds.
    :type lat: float

    :arg model_path: The directory where the model wind files are stored.
    :type model_path: string

    :returns: maxmimum ssh (max_ssh), index of maximum ssh (index_ssh),
    time of maximum ssh (tmax), residual at that time (max_res), wind
    speed at that time (max_wind), and the index of that wind speed (ind_w).
    """

    # Index when sea surface height is at its maximum at Point Atkinson
    max_ssh = np.max(ssh)
    index_ssh = np.argmax(ssh)
    tmax = t[index_ssh]
    max_res = res[index_ssh]

    # Get model winds
    t_orig=t[0]; t_final = t[-1]
    [wind, direc, t_wind, pr, tem, sol, the, qr, pre] = get_model_winds(lon,lat,t_orig,t_final,model_path)

    # Index where t_wind=tmax
    # (Find a match between the year, month, day and hour)
    ind_w = np.where(t_wind==datetime.datetime(tmax.year,tmax.month,tmax.day,tmax.hour))
    max_wind = wind[ind_w]

    return max_ssh, index_ssh, tmax, max_res, max_wind, ind_w

def compute_residual(ssh, ttide, t_orig, t_final):
    """ Compute the difference between modelled ssh and tidal predictions
    for a range of dates.

    Both modelled ssh and tidal predictions use eight tidal constituents.

    :arg ssh: The modelled ssh (without corrections).
    :type ssh: numpy array

    :arg ttide: The tidal predictions.
    :type ttide: DateFrame object with columns time, pred_all and pred_8

    :arg t_orig: The start of the date range.
    :type t_orig: datetime object

    :arg t_final: The end of the date range.
    :type t_final: datetime object

    :returns: numpy array for residual (res).
    """

    # Time range
    sdt=t_orig.replace(minute=0)
    edt=t_final +datetime.timedelta(minutes=30)

    # Index of ttide.time at start and end
    inds = ttide.time[ttide.time==sdt].index[0]
    inde = ttide.time[ttide.time==edt].index[0]

    tides=np.array(ttide.pred_8)

    # Average tides over two times to shift to the model 1/2 outputs
    shift = 0.5*(tides[inds:inde] + tides[inds+1:inde+1])

    res=ssh-shift

    return res

def get_tides(name):
    """ Returns the tidal predictions at a given station. Tidal
    predictions are calculated for 2014 and 2015.

    This function is only for Victoria, Campbell River, Point Atkinson and
    Patricia Bay. Tidal predictions are stored in a specific location.

    :arg name: The name of the station.
    :type name: string

    :returns: DataFrame object (ttide) with tidal predictions and columns time,
    pred_all, pred_8.
    """

    # Tide file covers 2014 and 2015. Harmonics were from a 2013 time series.
    path='/data/nsoontie/MEOPAR/tools/SalishSeaTools/salishsea_tools/nowcast/tidal_predictions/'
    filename = '_t_tide_compare8_31-Dec-2013_02-Dec-2015.csv'
    tfile = path+name+filename
    ttide,msl= stormtools.load_tidal_predictions(tfile)

    return ttide

def load_VENUS(station):
    """ Loads the most recent State of the Ocean data from the VENUS node
    indicated by station.

    This data set includes pressure, temperature, and salinity among other things.
    See: http://venus.uvic.ca/research/state-of-the-ocean/

    :arg station: The name of the station, either "East" or "Central".
    :type station: string

    :returns: DataFrame (data) with the VENUS data,
    longitude (lon), latitude (lat), and depth (depth) of the node in metres.
    """

    # Define location
    filename = 'SG-{}-VIP/VSG-{}-VIP-State_of_Ocean.txt'.format(station,station)
    if station == 'East':
        lat = 49.0419
        lon = -123.3176
        depth = 170
    elif station == 'Central':
        lat = 49.0401
        lon = -123.4261
        depth=300

    # Access website
    url = 'http://venus.uvic.ca/scripts/log_download.php'
    params = {
    'userid': 'nsoontie@eos.ubc.ca',
    'filename': filename,
    }
    response = requests.get(url, params=params)

    # Parse data
    fakefile = StringIO(response.content)
    data = pd.read_csv(fakefile,delimiter=' ,',skiprows=17,
                   names=['date','pressure','pflag','temp','tflag','sal','sflag','sigmaT','stflag','oxygen','oflag'],
                   parse_dates=['date'],date_parser=dateparse,engine='python')

    return data, lon, lat, depth

def get_weather_filenames(t_orig, t_final, model_path):
   """ Gathers a list of "Operational" atmospheric model filenames
   in a specifed date range.

   :arg t_orig: The beginning of the date range of interest.
   :type t_orig: datetime object

   :arg t_final: The end of the date range of interest.
   :type t_final: datetime object

   :arg model_path: The directory where the model files are stored.
   :type model_path: string

   :returns: list of files names (files) from the Operational model.
   """

   numdays=(t_final-t_orig).days

   dates = [ t_orig + datetime.timedelta(days=num) for num in range(0,numdays+1)]
   dates.sort();

   allfiles=glob.glob(model_path+'ops_y*')

   sstr =model_path+'ops_y'+dates[0].strftime('%Y')+'m'+dates[0].strftime('%m')+'d'+dates[0].strftime('%d')+'.nc'
   estr =model_path+'ops_y'+dates[-1].strftime('%Y')+'m'+dates[-1].strftime('%m')+'d'+dates[-1].strftime('%d')+'.nc'

   files=[]
   for filename in allfiles:
      if filename >= sstr:
	 if filename <= estr:
	   files.append(filename)

   files.sort(key=os.path.basename)

   return files

def get_model_winds(lon, lat, t_orig, t_final, model_path):
   """ Returns meteorological fields for the "Operational" model
   at a given longitude and latitude over a date range.

   :arg lon: The specified longitude.
   :type lon: float

   :arg lat: The specified latitude.
   :type lat: float

   :arg t_orig: The beginning of the date range of interest.
   :type t_orig: datetime object

   :arg t_final: The end of the date range of interest.
   :type t_final: datetime object

   :arg model_path: The directory where the model files are stored.
   :type model_path: string

   :returns: wind speed (wind), wind direction (direc), time (t),
   pressure (pr), temperature (tem), solar radiation (sol),
   thermal radiation (the),humidity (qr), precipitation (pre).
   """

   # Weather file names
   files = get_weather_filenames(t_orig, t_final, model_path)
   weather = nc.Dataset(files[0])
   Y = weather.variables['nav_lat'][:]
   X = weather.variables['nav_lon'][:]-360

   [j,i] = find_model_point(lon,lat,X,Y)

   wind = np.array([]); direc=np.array([],'double'); t=np.array([]); pr=np.array([]);
   sol = np.array([]); the=np.array([]); pre=np.array([]); tem=np.array([]); qr=np.array([]);
   for f in files:
        G = nc.Dataset(f)
        u = G.variables['u_wind'][:,j,i]; v=G.variables['v_wind'][:,j,i];
        pr = np.append(pr,G.variables['atmpres'][:,j,i]); sol=np.append(sol,G.variables['solar'][:,j,i]);
        qr = np.append(qr,G.variables['qair'][:,j,i]); the=np.append(the,G.variables['therm_rad'][:,j,i]);
        pre = np.append(pre,G.variables['precip'][:,j,i]);
        tem = np.append(tem,G.variables['tair'][:,j,i])
        speed = np.sqrt(u**2 + v**2)
        wind = np.append(wind,speed)

        d = np.arctan2(v, u)
        d = np.rad2deg(d + (d<0)*2*np.pi);
        direc = np.append(direc,d)

	ts = G.variables['time_counter']
	# There is no time_origin attribute in OP files; this is hard coded.
        torig = datetime.datetime(1970,1,1)
        for ind in np.arange(ts.shape[0]):
            t = np.append(t, torig + datetime.timedelta(seconds = ts[ind]))
   return wind, direc, t, pr, tem, sol, the, qr, pre
   
  
def draw_coast(ax, PNW_coastline):
  """  Plots the coastline of the Pacific Northwest  .
  
  :arg ax: The axis where coastline is drawn.
  :type ax: axis object
  
  :arg PNW_coastline: Coastline dataset.
  :type PNW_coastline: :class:`mat.Dataset`
  
  :returns: ax
  """ 
  coast={}
  coast['lat'] = PNW_coastline['ncst'][:,1]
  coast['lon'] = PNW_coastline['ncst'][:,0]
  ax.plot(coast['lon'],coast['lat'],'-k',rasterized=True,markersize=1)
    
  return ax

def plot_corrected_model(ax, t, ssh_loc, ttide, t_orig, t_final, PST, MSL, msl):
    """ Plots and returns corrected model.

    The model is corrected for the tidal constituents that are not included
    in the model forcing.

    :arg ax: The axis where the corrected model is plotted.
    :type ax: axis object

    :arg t: The time of model output.
    :type t: numpy array

    :arg ssh_loc: The model sea surface height to be corrected (1 dimensional).
    :type ssh_loc: numpy array

    :arg ttide: The tidal predictions with columns time, pred_all, pred_8.
    :type ttide: DataFrame object

    :arg t_orig: The start time of the simulation.
    :type t_orig: datetime object

    :arg t_final: The end time of the simulation.
    :type t_final: datetime object

    :arg PST: Specifies if plot should be presented in PST.
    1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg MSL: Specifies if the plot should be centred about mean sea level.
    1=centre about MSL, 0=centre about 0.
    :type MSL: 0 or 1

    :arg msl: The mean sea level for centring the plot.
    :type msl: float

    :returns: corrected model output (ssh_corr).
    """

    #Adjust dates for matching with tides dates.
    sdt=t_orig.replace(minute=0)
    edt=t_final +datetime.timedelta(minutes=30)
    ssh_corr=stormtools.correct_model(ssh_loc,ttide,sdt,edt)

    ax.plot(t+PST*time_shift,ssh_corr+msl*MSL,'-',c=model_c,linewidth=2,label='Corrected model')

    return ssh_corr

def plot_tides(ax, name, PST, MSL, color=predictions_c):
    """ Plots and returns the tidal predictions at a given station during the year of t_orig.

    This function is only for Victoria, Campbell River, Point Atkinson and Patricia Bay.
    Tidal predictions are stored in a specific location.

    :arg ax: The axis where the tides are plotted.
    :type ax: axis object

    :arg name: The name of the station.
    :type name: string

    :arg PST: Specifies if plot should be presented in PST.
    1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg MSL: Specifies if the plot should be centred about mean sea level.
    1=centre about MSL, 0=centre about 0.
    :type MSL: 0 or 1

    :arg color: The color for the tidal predictions plot.
    :type color: string

    :returns: DataFrame object (ttide) with tidal predictions and
    columns time, pred_all, pred_8.
    """

    ttide=get_tides(name)
    ax.plot(ttide.time+PST*time_shift,ttide.pred_all+MSL_DATUMS[name]*MSL,c=color,
		linewidth=2,label='Tidal predictions')

    return ttide

def plot_PA_observations(ax,PST):
  """ Plots the water level observations at Point Atkinson.

  :arg ax: The axis where the PA observations are plotted.
  :type ax: axis object

  :arg PST: Specifies if plot should be presented in PST.
  1 = plot in PST, 0 = plot in UTC.
  :type PST: 0 or 1
  """

  obs=load_PA_observations()
  ax.plot(obs.time +PST*time_shift,obs.wlev,color=observations_c,lw=2,label='Observations')

def plot_threshold_map(ax, ttide, ssh_corr, marker, msize, alpha, name):
  """Determines category (green, yellow, red)
  in which the max sea surface height at a station
  falls.
  """
  #load lats and longs of stations
  lats,lons=station_coords() #these should probably be constants

  # Defining thresholds
  extreme_sshs = {'Point Atkinson': 5.61, 'Campbell River': 5.35, 'Victoria': 3.76}
  extreme_ssh = extreme_sshs[name]
  max_tides=max(ttide.pred_all) + MSL_DATUMS[name]
  mid_tides = 0.5*(extreme_ssh - max_tides)+max_tides
  max_ssh = np.max(ssh_corr) + MSL_DATUMS[name]

  # Threshold colors
  if max_ssh < (max_tides):
    threshold_c = 'green'
  elif max_ssh > (mid_tides):
    threshold_c = 'red'
  else:
    threshold_c = 'Gold'

  ax.plot(lons[name],lats[name],marker=marker,
			color=threshold_c,markersize=msize,markeredgewidth=2,
			alpha=alpha)

  return max_tides, mid_tides, extreme_ssh

def plot_VENUS(ax_sal, ax_temp, station, start, end):
    """ Plots a time series of the VENUS data over a date range.

    :arg ax_sal: The axis in which the salinity is displayed.
    :type ax_sal: axis object

    :arg ax_temp: The axis in which the temperature is displayed.
    :type ax_temp: axis object

    :arg station: The name of the station, either "East" or "Central".
    :type station: string

    :arg start: The start date of the plot.
    :type start: datetime object

    :arg end: The end date of the plot.
    :type end: datetime object

    :returns: longitude (lon), latitude (lat), and depth (depth)
    of the VENUS station.
    """

    [data,lon,lat,depth]= load_VENUS(station)
    ax_sal.plot(data.date[:],data.sal,'r-',label='VENUS')
    ax_sal.set_xlim([start,end])
    ax_temp.plot(data.date[:],data.temp,'r-',label='VENUS')
    ax_temp.set_xlim([start,end])

    return lon, lat, depth

def plot_wind_vector(ax, name, t_orig, t_final, model_path, inds, scale):
  """ Plots a single wind vector at a station in an axis. Winds are averaged over the
  times represnted by the indices in inds[0] and inds[-1].

  :arg ax: The axis for plotting.
  :type ax: an axis object

  :arg name: The name of the station, can be Neah Bay, Point Atkinson, Campbell River,
  Victoria, Friday Harbor, Cherry Point, Sandheads.
  :type name: string

  :arg t_orig: start time of the simulation.
  :type t_orig: datetime object

  :arg t_final: end time fo simulation.
  :type t_final: datetime object

  :arg model_path: path to the weather model data.
  :type model_path: string

  :arg inds: indices corresponding to the time range of desired wind plots.
  If inds='all', the average will span the entire simulation.
  :type inds: numpy array, or string 'all'

  :arg scale: scale of arrows for plotting wind vector.
  :type scale: float

  :returns: tplot, an array with the time range winds were averaged: tplot[0] and tplot[-1] .
  """
  [lats, lons] = station_coords()

  [wind, direc, t, pr, tem, sol, the, qr, pre] = get_model_winds(lons[name],lats[name],t_orig,t_final,model_path)

  if inds =='all':
    inds=np.array([0,np.shape(wind)[0]-1])
  # Calculate U and V
  uwind = np.mean(wind[inds[0]:inds[-1]+1]*np.cos(np.radians(direc[inds[0]:inds[-1]+1]))); uwind=np.array([uwind])
  vwind = np.mean(wind[inds[0]:inds[-1]+1]*np.sin(np.radians(direc[inds[0]:inds[-1]+1]))); vwind=np.array([vwind])

  # Arrows
  ax.arrow(lons[name],  lats[name], scale*uwind[0], scale*vwind[0], head_width=0.05,
		head_length=0.1, width=0.02, color='white',fc='DarkMagenta', ec='black')
  tplot=t[inds[0]:inds[-1]+1]

  return tplot

def isolate_wind_timing(name,grid_T,grid_B,model_path, t,hour=4,average=True):
  """ Isolates indices timing of wind vectors.
  The timing is based on x number of hours before the max water level at a station.

  :arg name: The name of the station, Point Atkinson, Victora, Campbell River are good choices.
  :type name: string

  :arg grid_T: Hourly tracer results dataset from NEMO.
  :type grid_T: :class:`netCDF4.Dataset`

  :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
  :type grid_B: :class:`netCDF4.Dataset`

  :arg model_path: path to the weather model data.
  :type model_path: string

  :arg t: An array of outut times from the NEMO model.
  :type t: numpy array consisting of datetime objects

  :arg hour: The number of hours before max ssh to plt.
  :type hour: integer

  :arg average: Flag to determine if plotting should be averaged over x hours before ssh or just a single time.
  :type average: Boolean (True=average over times, False = only a single time_counter

  :returns: inds, an array with the start and end index for plotting winds.
  """

  [lats, lons] = station_coords()

  # Bathymetry
  bathy, X, Y = tidetools.get_bathy_data(grid_B)

  # Get sea surface height
  [j,i]=tidetools.find_closest_model_point(lons[name],lats[name],X,Y,bathy,allow_land=False)
  ssh = grid_T.variables['sossheig'][:,j,i]

  # "Place holder" residual so function can be used
  placeholder_res=np.zeros_like(ssh)

  # Index at which sea surface height is at its maximum at Point Atkinson
  [max_ssh,index_ssh,tmax,max_res,max_wind,ind_w] = get_maxes(ssh,t,placeholder_res,lons[name],lats[name],model_path)

  # Build indices based in x hours before max ssh if possible. If not, start at beginning of file.
  if ind_w>hour:
    inds =np.array([ind_w[0]-hour,ind_w])
  else:
    inds=np.array([0,ind_w]);
  if not(average):
    inds=np.array([inds[0]])

  return inds

def plot_map(ax, grid_B):
  """ Plots map of Salish Sea region.

  :arg ax: Axis for map.
  :type ax: axis object

  :returns: axis
  """

  viz_tools.set_aspect(ax)
  viz_tools.plot_land_mask(ax, grid_B,color='burlywood',coords='map')
  viz_tools.plot_coastline(ax,grid_B,coords='map')
  ax.set_xlabel('Longitude',**axis_font)
  ax.set_ylabel('Latitude',**axis_font)
  ax.grid()

  return ax


def website_thumbnail(grid_B, grid_T, model_path, PNW_coastline, scale=0.1,
                           PST=1, figsize = (18, 20)):
    """ Thumbnail for the UBC Storm Surge website includes 
    the thresholds indicating the risk of flooding in three 
    stations and the wind speeds and directions. It also 
    includes a brief description of threshold colours.

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg model_path: The directory where the model wind files are stored.
    :type model_path: string
    
    :arg PNW_coastline: Coastline dataset.
    :type PNW_coastline: :class:`mat.Dataset`

    :arg scale: scale factor or wind arrows
    :type scale: float

    :arg PST: Specifies if plot should be presented in PST.
    1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """
    
    title_font_thumb = {
    'fontname': 'Bitstream Vera Sans', 'size': '40', 'color': 'black',
    'weight': 'medium'
    }
    axis_font_thumb = {'fontname': 'Bitstream Vera Sans', 'size': '30'}

    # Stations information
    [lats, lons] = station_coords()

    # Bathymetry
    bathy, X, Y = tidetools.get_bathy_data(grid_B)

    # Time range
    t_orig, t_final, t = get_model_time_variables(grid_T)

    # Wind time
    inds = isolate_wind_timing('Point Atkinson', grid_T, grid_B,
                               model_path, t, 4, average=True)

    # Set up loop
    names = ['Point Atkinson', 'Campbell River', 'Victoria']

    # Set up Information
    max_sshs = {}; max_times = {}; max_winds = {}

    # Figure
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(2, 3, width_ratios=[1, 1, 1], height_ratios=[6, 1])
    gs.update(hspace=0.15, wspace=0.05)
    ax = fig.add_subplot(gs[0, :])
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[1, 1])
    ax3 = fig.add_subplot(gs[1, 2])

    # Map
    viz_tools.set_aspect(ax)
    viz_tools.plot_land_mask(ax, grid_B,color='burlywood',coords='map')
    viz_tools.plot_coastline(ax,grid_B,coords='map')
    draw_coast(ax, PNW_coastline)
    ax.set_xlabel('Longitude',**axis_font_thumb)
    ax.set_ylabel('Latitude',**axis_font_thumb)
    ax.grid()
    ax.set_xlim([-126.4,-121.3])
    ax.set_ylim([46.8,51.1])

    for name in names:
        # Get sea surface height
        [j, i] = tidetools.find_closest_model_point(lons[name], lats[name],
                                            X, Y, bathy, allow_land=False)
        ssh = grid_T.variables['sossheig']
        ssh_loc = ssh[:, j, i]

        # Get tides and ssh
        ttide = get_tides(name)
        sdt = t_orig.replace(minute=0)
        edt = t_final + datetime.timedelta(minutes=30)
        ssh_corr = stormtools.correct_model(ssh_loc, ttide, sdt, edt)

        # Plot thresholds
        plot_threshold_map(ax, ttide, ssh_corr, 'o', 70, 0.3, name)
        # Plot winds
        twind = plot_wind_vector(ax, name, t_orig, t_final, model_path, inds, scale)

        # Information
        res = compute_residual(ssh_loc, ttide, t_orig, t_final)
        [max_ssh, index_ssh, tmax, max_res, max_wind, ind_w] = get_maxes(ssh_corr, t, res, lons[name], lats[name], model_path)
        max_sshs[name] = max_ssh
        max_times[name] = tmax
        max_winds[name] = max_wind

    # Add winds for other stations
    for name in ['Neah Bay', 'Cherry Point', 'Sandheads', 'Friday Harbor']:
        plot_wind_vector(ax, name, t_orig, t_final, model_path, inds, scale)

    # Reference arrow
    ax.arrow(-121.5, 50.9, 0.*scale, -5.*scale,
              head_width=0.05, head_length=0.1, width=0.02,
              color='white',fc='DarkMagenta', ec='black')
    ax.text(-121.6, 50.95, "Reference: 5 m/s", rotation=90, fontsize=20)

    # Location labels
    ax.text(-125.7, 47.8, 'Pacific\nOcean', fontsize=30, color='DimGray')
    ax.text(-122.8, 50.1, '  British\nColumbia', fontsize=30, color='DimGray')
    ax.text(-124.2, 47.3, 'Washington\n    State', fontsize=30, color='DimGray')
    ax.text(-122.2, 47.6, ' Puget\nSound', fontsize=20, color='DimGray')
    ax.text(-124.6, 48.1, 'Strait of\nJuan de Fuca', fontsize=20, color='DimGray', rotation=-18)
    ax.text(-124.5, 49.1, 'Strait of \n Georgia', fontsize=20, color='DimGray', rotation=-18)

    # Figure format
    t = (twind[0]+PST*time_shift).strftime('%A, %B %d, %Y')
    ax.set_title('Marine and Atmospheric Conditions\n {time}'.format(time=t), **title_font_thumb)
    fig.patch.set_facecolor('#2B3E50')
    axis_colors(ax, 'gray')

    # Legend
    axs = [ax1, ax2, ax3]
    cs=['green','Gold','red']
    for ax, name,thresh_c in zip (axs, names,cs):
        plt.setp(ax.spines.values(), visible=False)
        ax.xaxis.set_visible(False); ax.yaxis.set_visible(False)
        axis_colors(ax, 'blue')
        display_time=(max_times[name]+PST*time_shift).strftime('%H:%M')
        ax.set_xlim([0, 1]); ax.set_ylim([0, 1])
        ax.plot(0.2,0.5,marker='o', color=thresh_c,markersize=70,markeredgewidth=2, alpha=0.6)
    ax1.text(0.4, 0.2, 'Green:\nNo flooding\nrisk', fontsize=25, color='w')
    ax2.text(0.4, 0.2, 'Yellow:\nRisk of\nhigh water', fontsize=25, color='w')
    ax3.text(0.4, 0.2, 'Red:\nExtreme risk\nof flooding', fontsize=25, color='w')

    return fig
  
  
def PA_tidal_predictions(grid_T,  PST=1, MSL=0, figsize=(20, 5)):
    """ Plots the tidal cycle at Point Atkinson during a 4 week period
    centred around the simulation start date.

    This function assumes that a tidal prediction file exists in a
    specific directory.
    Tidal predictions were calculated with ttide based on a time series
    from 2013.
    Plots are of predictions caluclated with all consituents.

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg PST: Specifies if plot should be presented in PST.
    1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg MSL: Specifies if the plot should be centred about mean sea level.
    1=centre about MSL, 0=centre about 0.
    :type MSL: 0 or 1

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Time range
    t_orig,t_end,t_nemo=get_model_time_variables(grid_T)
    timezone=PST*'[PST]' + abs((PST-1))*'[UTC]'

    # Axis limits are set as 2 weeks before and after start date.
    ax_start = t_orig - datetime.timedelta(weeks=2)
    ax_end = t_orig + datetime.timedelta(weeks=2)
    ylims=[-3,3]

    # Figure
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(1, 1, 1)
    fig.patch.set_facecolor('#2B3E50')
    fig.autofmt_xdate()
    ttide=plot_tides(ax,'Point Atkinson',PST,MSL,'black')

    # Line indicating current date
    ax.plot([t_orig +time_shift*PST,t_orig+time_shift*PST],ylims,'-r',lw=2)
    ax.plot([t_end+time_shift*PST,t_end+time_shift*PST],ylims,'-r',lw=2)

    # Axis
    ax.set_xlim([ax_start+time_shift*PST,ax_end+time_shift*PST])
    ax.set_ylim(ylims)
    ax.set_title('Tidal Predictions at Point Atkinson: ' + t_orig.strftime('%d-%b-%Y'),**title_font)
    ax.set_ylabel('Sea Surface Height [m]',**axis_font)
    ax.set_xlabel('Time {}'.format(timezone),**axis_font)
    ax.grid()
    axis_colors(ax, 'gray')
    ax.text(1., -0.2,
            'Tidal predictions calculated with t_tide: http://www.eos.ubc.ca/~rich/#T_Tide',
        horizontalalignment='right',
        verticalalignment='top',
        transform=ax.transAxes, color = 'white')

    return fig

def compare_water_levels(grid_T, grid_B, PST=1, figsize=(20, 15)):
    """ Compares modelled water levels to observed water levels and tides
    at a NOAA station over one day.

    See: http://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels

    This function applies to stations at Cherry Point, Neah Bay,
    and Friday Harbor.

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg PST: Specifies if plot should be presented in PST.
    1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg figsize:  Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Stations information
    [lats, lons] = station_coords()
    stations = {
        'Cherry Point': 9449424,
        'Neah Bay': 9443090,
        'Friday Harbor': 9449880,
    }

    # Bathymetry
    bathy, X, Y = tidetools.get_bathy_data(grid_B)

    # Time range
    t_orig,t_final,t=get_model_time_variables(grid_T)
    start_date = t_orig.strftime('%d-%b-%Y')
    end_date = t_final.strftime('%d-%b-%Y')
    timezone=PST*'[PST]' + abs((PST-1))*'[UTC]'

    # Figure
    fig = plt.figure(figsize=figsize)
    fig.patch.set_facecolor('#2B3E50')
    gs = gridspec.GridSpec(3, 2,width_ratios=[1.5,1])
    gs.update(wspace=0.17, hspace=0.2)

    # Map
    ax0 = fig.add_subplot(gs[:,1])
    plot_map(ax0, grid_B)
    ax0.set_xlim(-124.8, -122.2)
    ax0.set_ylim(48, 50)
    ax0.set_title('Station Locations',**title_font)
    axis_colors(ax0, 'gray')

    # Citation
    ax0.text(0.03 , -0.45,
        'Observed water levels and tidal predictions from NOAA:\nhttp://tidesandcurrents.noaa.gov/stations.html?type=Water+Levels',
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax0.transAxes, color = 'white')

    m = np.arange(3)
    names = ['Neah Bay', 'Friday Harbor', 'Cherry Point']

    for name, M in zip(names, m):

        #Map
        ax0.plot(lons[name],lats[name],marker='D',color='DarkMagenta',
			markersize=10,markeredgewidth=2)
        bbox_args = dict(boxstyle='square',facecolor='white',alpha=0.8)
        ax0.annotate(name,(lons[name]-0.05,lats[name]-0.15),fontsize=15,
			color='black',bbox=bbox_args)

	# NOAA
        obs=get_NOAA_wlevels(stations[name],start_date,end_date)
        tides=get_NOAA_tides(stations[name],start_date,end_date)

        # Get sea surface height
        [j,i]=tidetools.find_closest_model_point(lons[name],lats[name],X,Y,bathy,allow_land=False)
        ssh = grid_T.variables['sossheig'][:,j,i]

        # Sea surface height plots
        ax = fig.add_subplot(gs[M,0])
        ax.plot(t[:]+time_shift*PST,ssh,c=model_c,linewidth=2,label='Model')
        ax.plot(obs.time[:]+time_shift*PST,obs.wlev,c=observations_c,linewidth=2,
			label='Observed water levels')
        ax.plot(tides.time+time_shift*PST,tides.pred,c=predictions_c,linewidth=2,
			label='Tidal predictions')

	#Axis
        ax.set_xlim(t_orig+time_shift*PST,t_final+time_shift*PST)
        ax.set_ylim([-3,3])
        ax.set_title('Hourly Sea Surface Height at '+name + ': ' + t_orig.strftime('%d-%b-%Y'),**title_font)
        ax.set_ylabel('Water Levels wrt MSL (m)',**axis_font)
        ax.set_xlabel('Time {}'.format(timezone),**axis_font)
        ax.grid()
        axis_colors(ax, 'gray')
        ax.xaxis.set_major_formatter(hfmt)
        fig.autofmt_xdate()
        if M == 0:
	   legend = ax.legend(bbox_to_anchor=(1.285, 1), loc=2, borderaxespad=0.,
						prop={'size':15}, title=r'Legend')
	   legend.get_title().set_fontsize('20')

    return fig

def compare_tidalpredictions_maxSSH(
    grid_T, grid_B, model_path, PST=1, MSL=0, name='Point Atkinson',
    figsize=(20, 12),
):
    """Plots a map for sea surface height when it was at its maximum
    at Point Atkinson and compares modelled water levels to tidal
    predications over one day.

    It is assummed that the tidal predictions were calculated ahead of
    time and stored in a very specific location.
    The tidal predictions were calculated with all constituents using
    ttide based on a time series from 2013.
    The corrected model takes into account errors resulting in using
    only 8 constituents.
    The residual is calculated as corrected model - tides
    (with all constituents).

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg model_path: The directory where the model wind files are stored.
    :type model_path: string

    :arg PST: Specifies if plot should be presented in PST.
    1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg MSL: Specifies if the plot should be centred about mean sea level.
    1=centre about MSL, 0=centre about 0.
    :type MSL: 0 or 1

    :arg name: Name of station.
    :type name: string

    :arg figsize:  Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Stations information
    [lats, lons] = station_coords()

    # Time range
    t_orig,t_final,t=get_model_time_variables(grid_T)
    tzone=PST*'[PST]' + abs((PST-1))*'[UTC]'

    # Bathymetry
    bathy, X, Y = tidetools.get_bathy_data(grid_B)

    # Get sea surface height
    [j,i]=tidetools.find_closest_model_point(lons[name],lats[name],X,Y,bathy,allow_land=False)
    ssh = grid_T.variables['sossheig']
    ssh_loc = ssh[:,j,i]

    # Figure
    fig = plt.figure(figsize=figsize)
    fig.patch.set_facecolor('#2B3E50')
    gs = gridspec.GridSpec(3, 2, width_ratios=[2,1])
    gs.update(wspace=0.13, hspace=0.2)
    ax0 = fig.add_subplot(gs[0, 0])  # information box
    axis_colors(ax0, 'blue')
    plt.setp(ax0.spines.values(), visible=False)  # hide axes for information box
    ax0.xaxis.set_visible(False); ax0.yaxis.set_visible(False)
    ax1 = fig.add_subplot(gs[1, 0])  # sea surface height
    ax2 = fig.add_subplot(gs[:, 1])  # map
    ax3 = fig.add_subplot(gs[2, 0])  # residual

    # Sea surface height plot
    ttide=plot_tides(ax1,name,PST,MSL)
    ssh_corr=plot_corrected_model(ax1,t,ssh_loc,ttide,t_orig,t_final,
			PST,MSL,MSL_DATUMS[name])
    ax1.plot(t+PST*time_shift,ssh_loc,'--',c=model_c,linewidth=1,label='Model')

    # Compute residual
    res = compute_residual(ssh_loc,ttide,t_orig,t_final)

    # Find maximim sea surface height and timing
    max_ssh,index,tmax,max_res,max_wind,ind_w = get_maxes(ssh_corr, t, res,
                            lons[name], lats[name], model_path)
    ax0.text(0.05, 0.9, name, fontsize=20,
             horizontalalignment='left',
             verticalalignment='top', color = 'white')
    ax0.text(0.05, 0.75,
         'Max SSH: {:.2f} metres above mean sea level'.format(max_ssh),
             fontsize=15, horizontalalignment='left',
             verticalalignment='top', color = 'white')
    ax0.text(0.05, 0.6,
      'Time of max: {time} {timezone}'.format(time=tmax +PST*time_shift,
           timezone=PST*'[PST]' + abs((PST-1))*'[UTC]'),
             fontsize=15, horizontalalignment='left',
             verticalalignment='top', color = 'white')
    ax0.text(0.05, 0.45,
         'Residual: {:.2f} metres'.format(max_res),
             fontsize=15, horizontalalignment='left',
             verticalalignment='top', color = 'white')
    ax0.text(0.05, 0.3,
         'Wind speed: {:.1f} m/s'.format(float(max_wind)),
             fontsize=15, horizontalalignment='left',
             verticalalignment='top', color = 'white')

    # Mark point for maximum ssh
    ax1.plot(tmax+PST*time_shift, max_ssh, color='white', marker='o',
             markersize=10, markeredgewidth=3, label='Maximum SSH')

    # Axis for sea surface height plot
    ax1.set_xlim(t_orig+PST*time_shift,t_final+PST*time_shift)
    ax1.set_ylim([-3,3])
    ax1.set_title('Hourly Sea Surface Height at ' + name + ': ' + (t_orig).strftime('%d-%b-%Y'),**title_font)
    ax1.set_xlabel('Time {}'.format(tzone),**axis_font)
    ax1.set_ylabel('Water Levels wrt MSL (m)',**axis_font)
    ax1.grid()
    ax1.legend(loc = 0, numpoints = 1)
    axis_colors(ax1, 'gray')
    ax1.xaxis.set_major_formatter(hfmt)

    # Plot Residual
    ax3.plot(t +PST*time_shift,res,'-k',linewidth=2,label='Residual')

    # Axis for residual plot
    ax3.set_xlim(t_orig+PST*time_shift,t_final+PST*time_shift)
    ax3.set_ylim([-1,1])
    ax3.set_xlabel('Time {}'.format(tzone),**axis_font)
    ax3.set_ylabel('Residual (m)',**axis_font)
    ax3.set_yticks(np.arange(-1.0,1.25,0.25))
    ax3.grid()
    ax3.legend(loc = 0, numpoints = 1)
    axis_colors(ax3, 'gray')
    ax3.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate()

    # Map of sea surface height
    cs = [-1,-0.5,0.5,1, 1.5,1.6,1.7,1.8,1.9,2,2.1,2.2,2.4,2.6]
    ssh_max_field = np.ma.masked_values(ssh[index], 0)
    mesh=ax2.contourf(ssh_max_field,cs,cmap='nipy_spectral',extend='both',alpha=0.6)
    ax2.contour(ssh_max_field,cs,colors='k',linestyles='--')

    cbar = fig.colorbar(mesh,ax=ax2)
    cbar.set_ticks(cs)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')
    cbar.set_label('[m]', color='white')

    ax2.set_title('Sea Surface Height: ' + (tmax+PST*time_shift).strftime('%d-%b-%Y, %H:%M'),**title_font)
    ax2.set_xlabel('X Index',**axis_font)
    ax2.set_ylabel('Y Index',**axis_font)
    ax2.grid()

    axis_colors(ax2, 'white')
    viz_tools.plot_coastline(ax2,grid_B)
    viz_tools.plot_land_mask(ax2,grid_B,color='burlywood')
    ax2.plot(i, j, marker='o', color='white', markersize=10,
             markeredgewidth=3)

    return fig

def plot_thresholds_all(grid_T, grid_B, model_path, PST=1, MSL=1, figsize=(20, 15.5)):
  """Plots sea surface height over one day with respect to warning thresholds.

  This function applies only to Point Atkinson, Campbell River, and Victoria.
  There are three different warning thresholds.
  The locations of stations are colored depending on the threshold in
  which they fall: green, yellow, red.

  :arg grid_T: Hourly tracer results dataset from NEMO.
  :type grid_T: :class:`netCDF4.Dataset`

  :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
  :type grid_B: :class:`netCDF4.Dataset`

  :arg model_path: The directory where the model wind files are stored.
  :type model_path: string

  :arg PST: Specifies if plot should be presented in PST.
  1 = plot in PST, 0 = plot in UTC.
  :type PST: 0 or 1

  :arg MSL: Specifies if the plot should be centred about mean sea level.
  1=centre about MSL, 0=centre about 0.
  :type MSL: 0 or 1

  :arg figsize:  Figure size (width, height) in inches.
  :type figsize: 2-tuple

  :returns: matplotlib figure object instance (fig).
  """

  # Figure
  fig = plt.figure(figsize=figsize)
  fig.patch.set_facecolor('#2B3E50')
  gs = gridspec.GridSpec(3, 2, width_ratios=[1.5,1])
  gs.update(wspace=0.13, hspace=0.2)

  # Map of region
  ax0=fig.add_subplot(gs[:, 1])
  plot_map(ax0, grid_B)
  ax0.set_xlim(-125.4, -122.2)
  ax0.set_ylim(48, 50.3)
  ax0.set_title('Degree of Flood Risk',**title_font)
  axis_colors(ax0, 'gray')

 # Stations information
  [lats, lons] = station_coords()

  # Bathymetry
  bathy, X, Y = tidetools.get_bathy_data(grid_B)

  m = np.arange(3)
  names = ['Point Atkinson', 'Campbell River', 'Victoria']
  extreme_sshs = [5.61,5.35,3.76]

  for M, name, extreme_ssh in zip(m, names, extreme_sshs):

     # Get sea surface height
     [j,i]=tidetools.find_closest_model_point(lons[name],lats[name],X,Y,bathy,allow_land=False)
     ssh = grid_T.variables['sossheig']
     ssh_loc = ssh[:,j,i]

     # Time range
     t_orig,t_final,t=get_model_time_variables(grid_T)
     tzone=PST*'[PST]' + abs((PST-1))*'[UTC]'

     # Sea surface height plot
     ax = fig.add_subplot(gs[M,0])

     # Plot tides, corrected model and original model
     if name =='Point Atkinson':
       plot_PA_observations(ax,PST)
     ttide=plot_tides(ax,name,PST,MSL)
     ssh_corr=plot_corrected_model(ax,t,ssh_loc,ttide,t_orig,t_final,
			PST,MSL,MSL_DATUMS[name])
     ax.plot(t+PST*time_shift,ssh_loc+MSL_DATUMS[name]*MSL,'--',
			c=model_c,linewidth=1,label='Model')

     # Axis
     ax.set_xlim(t_orig+PST*time_shift,t_final+PST*time_shift)
     ax.set_ylim([-1,6])
     ax.set_title('Hourly Sea Surface Height at ' + name + ': ' + (t_orig).strftime('%d-%b-%Y'), **title_font)
     ax.set_xlabel('Time {}'.format(tzone),**axis_font)
     ax.set_ylabel('Water Level above Chart Datum (m)',**axis_font)
     ax.grid()
     axis_colors(ax, 'gray')
     ax.xaxis.set_major_formatter(hfmt)
     fig.autofmt_xdate()

     # Map
     bbox_args = dict(boxstyle='square',facecolor='white',alpha=0.8)
     ax0.annotate(name,(lons[name]-0.05,lats[name]-0.18),fontsize=15,
				color='black',bbox=bbox_args)

     # Define thresholds in sea surface height plots
     [max_tides, mid_tides, extreme_ssh] = plot_threshold_map(ax0,ttide, ssh_corr, 'D', 10, 1.0, name)

     # Plot thresholds in sea surface height plots
     ax.axhline(y=max_tides,color='Gold',linewidth=2,ls='solid',label='Maximum tides')
     ax.axhline(y=mid_tides,color='Red',linewidth=2,ls='solid',label='Extreme water')
     ax.axhline(y=extreme_ssh,color='DarkRed',linewidth=2,ls='solid',label='Historical maximum')

     # Legend
     if M == 0:
	   legend = ax.legend(bbox_to_anchor=(1.285, 1), loc=2, borderaxespad=0.,
				prop={'size':15}, title=r'Legend')
	   legend.get_title().set_fontsize('20')

  # Citation
  ax0.text(0.03 , -0.45,
        'Tidal predictions calculated with t_tide: http://www.eos.ubc.ca/~rich/#T_Tide \nObserved water levels from Fisheries and Oceans, Canada \nvia Scott Tinis at stormsurgebc.ca',
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax0.transAxes, color = 'white')

  return fig

def Sandheads_winds(grid_T, grid_B, model_path, PST=1, figsize=(20, 12)):
    """ Plots the observed and modelled winds at Sandheads during
    the simulation.

    Observations are from Environment Canada data:
    http://climate.weather.gc.ca/
    Modelled winds are the HRDPS nested model from Environment Canada.

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg model_path: The directory where the model files are stored.
    :type model_path: string

    :arg PST: Specifies if plot should be presented in PST.
    1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg figsize:  Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Time range
    t_orig,t_end,t_nemo=get_model_time_variables(grid_T)
    timezone=PST*'[PST]' + abs((PST-1))*'[UTC]'

    # Strings for timetamps of EC data
    start=t_orig.strftime('%d-%b-%Y')
    end=t_end.strftime('%d-%b-%Y')

    [winds,dirs,temps,time, lat,lon] = stormtools.get_EC_observations('Sandheads',start,end)
    time=np.array(time)

    # Get modelled winds
    [wind, direc, t, pr, tem, sol, the, qr, pre]=get_model_winds(lon,lat,t_orig,t_end,model_path)
    gs = gridspec.GridSpec(2, 2,width_ratios=[1.5,1])
    gs.update(wspace=0.13, hspace=0.2)

    # Figure
    fig = plt.figure(figsize=figsize)
    fig.patch.set_facecolor('#2B3E50')
    ax1 = fig.add_subplot(gs[0,0])
    ax2 = fig.add_subplot(gs[1,0])
    ax0 = fig.add_subplot(gs[:,1])

    # Plot wind speed
    ax1.plot(time +PST*time_shift,winds,color=observations_c,lw=2,label='Observations')
    ax1.plot(t+PST*time_shift,wind,lw=2,color=model_c,label='Model')
    ax1.set_xlim([t_orig+PST*time_shift,t_end+PST*time_shift])
    ax1.set_ylim([0,20])
    ax1.set_title('Winds at Sandheads:  ' + start ,**title_font)
    ax1.set_ylabel('Wind Speed (m/s)',**axis_font)
    ax1.set_xlabel('Time {}'.format(timezone),**axis_font)
    ax1.legend(loc=0)
    ax1.grid()
    axis_colors(ax1, 'gray')
    ax1.xaxis.set_major_formatter(hfmt)

    # Plot wind direction
    ax2.plot(time+PST*time_shift,dirs,lw=2,color=observations_c,label='Observations')
    ax2.plot(t+PST*time_shift,direc,lw=2,color=model_c,label='Model')
    ax2.set_xlim([t_orig+PST*time_shift,t_end+PST*time_shift])
    ax2.set_ylim([0,360])
    ax2.set_xlabel('Time '+ PST*'[PST]' + abs((PST-1))*'[UTC]',**axis_font)
    ax2.set_ylabel('Wind Direction \n (degress CCW of East)',**axis_font)
    ax2.legend(loc=0)
    ax2.grid()
    axis_colors(ax2, 'gray')
    ax2.xaxis.set_major_formatter(hfmt)
    fig.autofmt_xdate()

    # Map
    plot_map(ax0, grid_B)
    ax0.set_xlim([-124.8,-122.2])
    ax0.set_ylim([48,50])
    ax0.set_title('Station Locations',**title_font)
    axis_colors(ax0, 'gray')

    ax0.plot(lon,lat,marker='D',color='DarkMagenta',markersize=10,markeredgewidth=2)
    bbox_args = dict(boxstyle='square',facecolor='white',alpha=0.8)
    ax0.annotate('Sandheads',(lon-0.05,lat-0.15),fontsize=15,color='black',bbox=bbox_args)

    # Citation
    ax0.text(0.0, -0.15,
        'Observations from Environment Canada data. http://climate.weather.gc.ca/ \nModelled winds are from the High Resolution Deterministic Prediction System \nof Environment Canada.\nhttps://weather.gc.ca/grib/grib2_HRDPS_HR_e.html',
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax0.transAxes, color = 'white')


    return fig

def average_winds_at_station(grid_T, grid_B, model_path, station, figsize=(20, 15)):
  """ Plots winds averaged over simulation time at individual or all
  stations.

  This function applies to stations at Campbell River, Point Atkinson,
  Victoria, Cherry Point, Neah Bay, and Friday Harbor.

  :arg grid_T: Hourly tracer results dataset from NEMO.
  :type grid_T: :class:`netCDF4.Dataset`

  :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
  :type grid_B: :class:`netCDF4.Dataset`

  :arg model_path: The directory where the model files are stored.
  :type model_path: string

  :arg station: Name of one station or 'all' for all stations.
  :type station: string

  :arg figsize:  Figure size (width, height) in inches.
  :type figsize: 2-tuple

  :returns: matplotlib figure object instance (fig).
  """

  # Stations information
  [lats, lons] = station_coords()

  # Map
  fig = plt.figure(figsize=figsize)
  ax = fig.add_subplot(1, 1, 1)
  fig.patch.set_facecolor('#2B3E50')
  plot_map(ax, grid_B)

  # Arrow scale
  scale = 0.1

  # Time range
  [t_orig,t_final,t] = get_model_time_variables(grid_T)

  # Condition if plotting all stations or a single station
  if station == 'all':
    names = ['Neah Bay', 'Victoria', 'Friday Harbor', 'Cherry Point', 'Sandheads', 'Point Atkinson', 'Campbell River']
    colors=stations_c
  else:
    names=[station]
    colors=['DarkMagenta']

  # Loop through all stations to plot arrows and markers
  for name, station_c in zip (names, colors):
    plot_time=plot_wind_vector(ax, name, t_orig, t_final, model_path, 'all', scale)
    ax.plot(lons[name], lats[name], marker='D',color=station_c,
            markersize=14, markeredgewidth=2,label=name)

  # Reference arrow
  ax.arrow(-122, 51, 0.*scale, -5.*scale,
           head_width=0.05, head_length=0.1, width=0.02,
           color='white',fc='DarkMagenta', ec='black')
  ax.text(-122.1, 50.95, "Reference: 5 m/s", rotation=90, fontsize = 14)

  # Times for titles and legend
  t1=(plot_time[0] +time_shift).strftime('%d-%b-%Y %H:%M');
  t2=(plot_time[-1]+time_shift).strftime('%d-%b-%Y %H:%M')
  legend = ax.legend(numpoints=1, bbox_to_anchor=(0.9, 1.05), loc=2, borderaxespad=0.,
                     prop={'size':15}, title=r'Stations')
  legend.get_title().set_fontsize('20')
  ax.set_title('Modelled winds averaged over \n {t1} [PST] to {t2} [PST]'.format(t1=t1,t2=t2),**title_font)

  # Citation
  ax.text(0.6,-0.07,
          'Modelled winds are from the High Resolution Deterministic Prediction System \nof Environment Canada: https://weather.gc.ca/grib/grib2_HRDPS_HR_e.html',
          horizontalalignment='left',
          verticalalignment='top',
          transform=ax.transAxes, color = 'white')

  axis_colors(ax, 'gray')

  return fig

def winds_at_max_ssh(grid_T, grid_B, model_path, station, figsize=(20, 15)):
  """ Plots winds at individual stations 4 hours before the
  maxmimum sea surface height at Point Atkinson.

  If that data is not available then the plot is generated at the start of the simulation.
  This function applies to stations at Campbell River, Point Atkinson, Victoria,
  Cherry Point, Neah Bay, and Friday Harbor.

  :arg grid_T: Hourly tracer results dataset from NEMO.
  :type grid_T: :class:`netCDF4.Dataset`

  :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
  :type grid_B: :class:`netCDF4.Dataset`

  :arg model_path: The directory where the model files are stored.
  :type model_path: string

  :arg station: Name of the station.
  :type station: string

  :arg figsize:  Figure size (width, height) in inches.
  :type figsize: 2-tuple

  :returns: matplotlib figure object instance (fig).
  """

  # Stations information
  [lats, lons] = station_coords()

  # Map
  fig = plt.figure(figsize=figsize)
  ax = fig.add_subplot(1, 1, 1)
  fig.patch.set_facecolor('#2B3E50')
  plot_map(ax, grid_B)

  # Arrow scale
  scale = 0.1

  # Time range
  [t_orig,t_final,t] = get_model_time_variables(grid_T)

  # Reference arrow
  ax.arrow(-122, 51, 0.*scale, -5.*scale,
              head_width=0.05, head_length=0.1, width=0.02,
              color='white',fc='DarkMagenta', ec='black')
  ax.text(-122.1, 50.95, "Reference: 5 m/s", rotation=90, fontsize = 14)

  # Condition if plotting all stations or a single station
  if station == 'all':
        names = ['Neah Bay', 'Victoria', 'Friday Harbor', 'Cherry Point', 'Sandheads', 'Point Atkinson', 'Campbell River']
        colors=stations_c
  else:
        names=[station]
        colors=['DarkMagenta']

  # Indices for plotting wind vectors
  inds = isolate_wind_timing('Point Atkinson',grid_T,grid_B,model_path,t,4,average=False)

  # Loop through all stations to plot arrows and markers
  for name, station_c in zip (names, colors):
    plot_time=plot_wind_vector(ax, name, t_orig, t_final, model_path, inds, scale)
    ax.plot(lons[name], lats[name], marker='D',
	    color=station_c, markersize=14, markeredgewidth=2,label=name)

  # Time for title and legend
  plot_time=(plot_time[0]+time_shift).strftime('%d-%b-%Y %H:%M')
  legend = ax.legend(numpoints=1, bbox_to_anchor=(0.9, 1.05), loc=2, borderaxespad=0.,
						prop={'size':15}, title=r'Stations')
  legend.get_title().set_fontsize('20')
  ax.set_title('Modelled winds at \n {time} [PST]'.format(time=plot_time),**title_font)

  # Citation
  ax.text(0.6,-0.07,
    'Modelled winds are from the High Resolution Deterministic Prediction System \nof Environment Canada: https://weather.gc.ca/grib/grib2_HRDPS_HR_e.html',
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax.transAxes, color = 'white')

  axis_colors(ax, 'gray')

  return fig

def thalweg_salinity(grid_T_d, figsize=(20,8), cs = [26,27,28,29,30,30.2,30.4,30.6,30.8,31,32,33,34]):
    """ Plots the daily average salinity field along the thalweg.

    :arg grid_T_d: Daily tracer results dataset from NEMO.
    :type grid_T_d: :class:`netCDF4.Dataset`

    :arg figsize:  Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :arg cs: List of salinity contour levels for shading.
    :type cs: list

    :returns: matplotlib figure object instance (fig).
    """

    # Tracer data
    lon_d = grid_T_d.variables['nav_lon']
    lat_d = grid_T_d.variables['nav_lat']
    dep_d = grid_T_d.variables['deptht']
    sal_d = grid_T_d.variables['vosaline']

    # Call thalweg
    lines = np.loadtxt('/data/nsoontie/MEOPAR/tools/bathymetry/thalweg_working.txt',
				delimiter=" ", unpack=False)
    lines = lines.astype(int)

    thalweg_lon = lon_d[lines[:,0],lines[:,1]]
    thalweg_lat = lat_d[lines[:,0],lines[:,1]]

    ds=np.arange(0,lines.shape[0],1);
    XX,ZZ = np.meshgrid(ds,-dep_d[:])

    # Salinity along thalweg
    salP=sal_d[0,:,lines[:,0],lines[:,1]]
    salP= np.ma.masked_values(salP,0)

    # Figure
    fig,ax=plt.subplots(1,1,figsize=figsize)
    fig.patch.set_facecolor('#2B3E50')
    mesh=ax.contourf(XX,ZZ,salP,cs,cmap='hsv',extend='both')

    cbar=fig.colorbar(mesh,ax=ax)
    cbar.set_ticks(cs)
    cbar.set_label('Practical Salinity [psu]',color='white',**axis_font)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')

    timestamp = nc_tools.timestamp(grid_T_d,0)
    ax.set_title('Salinity field along thalweg: ' + timestamp.format('DD-MMM-YYYY'),**title_font)
    ax.set_ylabel('Depth [m]',**axis_font)
    ax.set_xlabel('Position along Thalweg',**axis_font)
    axis_colors(ax, 'white')
    ax.set_axis_bgcolor('burlywood')

    return fig


def plot_surface(grid_T_d, grid_U_d, grid_V_d, grid_B, limits, figsize):
    """ Plots the daily average surface salinity, temperature, and currents.

    :arg grid_T_d: Daily tracer results dataset from NEMO.
    :type grid_T_d: :class:`netCDF4.Dataset`

    :arg grid_U_d: Daily zonal velocity results dataset from NEMO.
    :type grid_U_d: :class:`netCDF4.Dataset`

    :arg grid_V_d: Daily meridional velocity results dataset from NEMO.
    :type grid_V_d: :class:`netCDF4.Dataset`

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg limits: Figure limits [xmin,xmax,ymin,ymax]
                           or 'default' for entire region.
    :type limits: 2-tuple

    :arg figsize: Figure size (width, height) in inches or 'default'.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Limits
    if limits == 'default':
        limits = [0, 398, 0, 898]

    xmin = limits[0]
    xmax = limits[1]
    ymin = limits[2]
    ymax = limits[3]

    # Figure size
    if figsize == 'default':
        figsize = (20, 12)

    # Tracer data
    sal_d = grid_T_d.variables['vosaline']
    tem_d = grid_T_d.variables['votemper']

    # Bathymetry
    bathy, X, Y = tidetools.get_bathy_data(grid_B)

    # Preparing salinity and temperature
    t, z = 0, 0
    sal_d = np.ma.masked_values(sal_d[t, z], 0)
    tem_d = np.ma.masked_values(tem_d[t, z], 0)

    tracers = [sal_d, tem_d]
    titles = ['Average Salinity: ', 'Average Temperature: ']
    cmaps = ['gist_ncar_r', 'jet']
    units = ['[]', '[degC]']

    # Figure
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=figsize)
    fig.patch.set_facecolor('#2B3E50')

    axs = [ax1, ax2]
    plots = np.arange(1, 3, 1)

    for ax, tracer, title, cmap, unit, plot in zip(
            axs, tracers, titles, cmaps, units, plots):

        # Map
        cmap = plt.get_cmap(cmap)

        # Colormaps
        if plot == 1:   # salinity
            cs = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36]
        if plot == 2:   # temperature
            cs = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

        # Plot salinity and temperature
        mesh = ax.contourf(tracer, cmap=cmap, vmin=0, vmax=cs[-1])

        # Axis
        ax.set_xlim(xmin,xmax)
        ax.set_ylim(ymin,ymax)
        cbar = fig.colorbar(mesh,ax=ax)
        timestamp = nc_tools.timestamp(grid_T_d,0)
        ax.set_title(title + timestamp.format('DD-MMM-YYYY'),**title_font)
        ax.set_xlabel('X Index',**axis_font)
        ax.set_ylabel('Y Index',**axis_font)
        ax.grid()
        cbar.set_ticks(cs)
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')
        cbar.set_label(unit,color='white',**axis_font)
        viz_tools.plot_coastline(ax,grid_B)
        axis_colors(ax, 'white')
        ax.set_axis_bgcolor('burlywood')

    # Preparing velocity
    ugrid = grid_U_d.variables['vozocrtx']
    vgrid = grid_V_d.variables['vomecrty']
    zlevels = grid_U_d.variables['depthu']
    timesteps = grid_U_d.variables['time_counter']
    t, zlevel = 0, 0

    y_slice = np.arange(0, ugrid.shape[2])
    x_slice = np.arange(0, ugrid.shape[3])

    arrow_step = 25
    y_slice_a = y_slice[::arrow_step]
    x_slice_a = x_slice[::arrow_step]

    ugrid_tzyx = np.ma.masked_values(ugrid[t, zlevel, y_slice_a, x_slice_a], 0)
    vgrid_tzyx = np.ma.masked_values(vgrid[t, zlevel, y_slice_a, x_slice_a], 0)

    u_tzyx, v_tzyx = viz_tools.unstagger(ugrid_tzyx, vgrid_tzyx)

    speeds = np.sqrt(np.square(u_tzyx) + np.square(v_tzyx))

    # Colormap
    cs = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]

    # Plot velocity
    quiver = ax3.quiver(x_slice_a[1:], y_slice_a[1:], u_tzyx, v_tzyx, speeds,
					  pivot='mid', cmap='gnuplot_r', width=0.015)

    # Axis
    viz_tools.plot_land_mask(ax3, grid_B, xslice=x_slice, yslice=y_slice, color='burlywood')
    viz_tools.plot_coastline(ax3,grid_B)

    cbar = fig.colorbar(quiver,ax=ax3)
    cbar.set_ticks(cs)
    cbar.set_label('[m / s]',color='white',**axis_font)
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='w')

    ax3.set_xlim(x_slice[0], x_slice[-1])
    ax3.set_ylim(y_slice[0], y_slice[-1])
    plt.axis((xmin, xmax, ymin, ymax))
    ax3.grid()


    ax3.set_title('Average Velocity Field: ' + timestamp.format('DD-MMM-YYYY') +
                  u', depth\u2248{d:.2f} {z.units}'.format(d=zlevels[zlevel], z=zlevels),**title_font)
    ax3.set_xlabel('X Index',**axis_font)
    ax3.set_ylabel('Y Index',**axis_font)
    ax3.quiverkey(quiver, 355, 850, 1, '1 m/s', coordinates='data',
				color='Indigo', labelcolor='black')
    axis_colors(ax3, 'white')

    return fig

def compare_VENUS(station, grid_T, grid_B, figsize=(6,10)):
    """ Compares the model's temperature and salinity
    with observations from VENUS station.

    :arg station: Name of the station ('East' or 'Central')
    :type station: string

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Time range
    t_orig,t_end,t=get_model_time_variables(grid_T)

    # Bathymetry
    bathy, X, Y = tidetools.get_bathy_data(grid_B)

    # VENUS data
    fig,(ax_sal, ax_temp) = plt.subplots(2,1,figsize=figsize,sharex=True)
    fig.patch.set_facecolor('#2B3E50')
    fig.autofmt_xdate()
    lon, lat, depth = plot_VENUS(ax_sal, ax_temp, station, t_orig, t_end)

    # Grid point of VENUS station
    [j,i]=tidetools.find_closest_model_point(lon,lat,X,Y,bathy,allow_land=True)

    # Model data
    sal = grid_T.variables['vosaline'][:,:,j,i]
    temp = grid_T.variables['votemper'][:,:,j,i]
    ds = grid_T.variables['deptht']

    # Interpolating data
    salc=[]
    tempc=[]
    for ind in np.arange(0,sal.shape[0]):
        salc.append(interpolate_depth(sal[ind,:],ds,depth))
        tempc.append(interpolate_depth(temp[ind,:],ds,depth))

    # Plot model data
    ax_sal.plot(t,salc,'-b',label='Model')
    ax_temp.plot(t,tempc,'-b',label='Model')

    # Axis
    ax_sal.set_title('VENUS - {}'.format(station) ,**title_font)
    ax_sal.set_ylim([30,32])
    ax_sal.set_ylabel('Practical Salinity [psu]',**axis_font)
    ax_sal.legend(loc=0)
    ax_temp.set_ylim([7,11])
    ax_temp.set_xlabel('Time [UTC]',**axis_font)
    ax_temp.set_ylabel('Temperature [deg C]',**axis_font)
    axis_colors(ax_sal, 'gray')
    axis_colors(ax_temp, 'gray')

    return fig

def ssh_PtAtkinson(grid_T, grid_B=None, figsize=(20, 5)):
    """ Plots hourly sea surface height at Point Atkinson.

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ssh = grid_T.variables['sossheig']
    results_date = nc_tools.timestamp(grid_T, 0).format('YYYY-MM-DD')
    ax.plot(ssh[:, 468, 328], 'o')
    ax.set_title(
        'Hourly Sea Surface Height at Point Atkinson on {}'.format(results_date))
    ax.set_xlabel('UTC Hour from {}'.format(results_date))
    ax.set_ylabel(
        '{label} [{units}]'
        .format(label=ssh.long_name.title(), units=ssh.units))
    ax.grid()

    return fig


def plot_threshold_website(grid_B, grid_T, model_path, scale=0.1,
                           PST=1, figsize = (18, 20)):
    """ Overview image for Salish Sea website. Plots a map of the Salish Sea with
    markers indicating extreme water at Point Atkinson, Victoria nd Campbell
    River. Also plots wind vectors averaged over 4 ours before the max ssh at
    Point Atkinson. Includes text boxes with max water level and timing.

    :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
    :type grid_B: :class:`netCDF4.Dataset`

    :arg grid_T: Hourly tracer results dataset from NEMO.
    :type grid_T: :class:`netCDF4.Dataset`

    :arg model_path: The directory where the model wind files are stored.
    :type model_path: string

    :arg scale: scale factor or wind arrows
    :type scale: float

    :arg PST: Specifies if plot should be presented in PST.
    1 = plot in PST, 0 = plot in UTC.
    :type PST: 0 or 1

    :arg figsize: Figure size (width, height) in inches.
    :type figsize: 2-tuple

    :returns: matplotlib figure object instance (fig).
    """

    # Stations information
    [lats, lons] = station_coords()

    # Bathymetry
    bathy, X, Y = tidetools.get_bathy_data(grid_B)

    # Time range
    t_orig, t_final, t = get_model_time_variables(grid_T)

    # Wind time
    inds = isolate_wind_timing('Point Atkinson', grid_T, grid_B,
                               model_path, t, 4, average=True)

    # Set up loop
    names = ['Point Atkinson', 'Campbell River', 'Victoria']

    # Set up Information
    max_sshs = {}; max_times = {}; max_winds = {}

    # Figure
    fig = plt.figure(figsize=figsize)
    gs = gridspec.GridSpec(2, 3, width_ratios=[1, 1, 1], height_ratios=[6, 1])
    gs.update(hspace=0.1, wspace=0.05)
    ax = fig.add_subplot(gs[0, :])
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[1, 1])
    ax3 = fig.add_subplot(gs[1, 2])

    # Map
    plot_map(ax, grid_B)

    for name in names:
        # Get sea surface height
        [j, i] = tidetools.find_closest_model_point(lons[name], lats[name],
                                            X, Y, bathy, allow_land=False)
        ssh = grid_T.variables['sossheig']
        ssh_loc = ssh[:, j, i]

        # Get tides and ssh
        ttide = get_tides(name)
        sdt = t_orig.replace(minute=0)
        edt = t_final + datetime.timedelta(minutes=30)
        ssh_corr = stormtools.correct_model(ssh_loc, ttide, sdt, edt)

        # Plot thresholds
        plot_threshold_map(ax, ttide, ssh_corr, 'o', 55, 0.3, name)
        # Plot winds
        twind = plot_wind_vector(ax, name, t_orig, t_final, model_path, inds, scale)

        # Information
        res = compute_residual(ssh_loc, ttide, t_orig, t_final)
        [max_ssh, index_ssh, tmax, max_res, max_wind, ind_w] = get_maxes(ssh_corr, t, res, lons[name], lats[name], model_path)
        max_sshs[name] = max_ssh
        max_times[name] = tmax
        max_winds[name] = max_wind

    # Add winds for other stations
    for name in ['Neah Bay', 'Cherry Point', 'Sandheads', 'Friday Harbor']:
        plot_wind_vector(ax, name, t_orig, t_final, model_path, inds, scale)

    # Reference arrow
    ax.arrow(-121.5, 51, 0.*scale, -5.*scale,
              head_width=0.05, head_length=0.1, width=0.02,
              color='white',fc='DarkMagenta', ec='black')
    ax.text(-121.6, 50.95, "Reference: 5 m/s", rotation=90, fontsize=14)

    # Location labels
    ax.text(-125.6, 48.1, 'Pacific Ocean', fontsize=13)
    ax.text(-122.8, 50.1, 'British Columbia', fontsize=13)
    ax.text(-123.8, 47.3, 'Washington \n State', fontsize=13)

    ax.text(-122.3, 47.6, 'Puget Sound', fontsize=13)
    ax.text(-124.7, 48.45, 'Strait of Juan de Fuca', fontsize=13, rotation=-18)
    ax.text(-123.95, 49.25, 'Strait of \n Georgia', fontsize=13, rotation=-2)

    ax.text(-123.1, 49.4, 'Point \n Atkinson', fontsize=20)
    ax.text(-125.9, 50.05, 'Campbell \n River', fontsize=20)
    ax.text(-123.5, 48.2, 'Victoria', fontsize=20)

    # Figure format
    time = (twind[0]+PST*time_shift).strftime('%A, %B %d, %Y')
    ax.set_title('Marine and Atmospheric Conditions\n {Time}'.format(Time=time), **title_font)
    fig.patch.set_facecolor('#2B3E50')
    axis_colors(ax, 'gray')


    # Citation
    t1 = (twind[0]+PST*time_shift).strftime('%Y/%m/%d %H:%M')
    t2 = (twind[-1]+PST*time_shift).strftime('%Y/%m/%d %H:%M')
    timezone = PST*'[PST]' + abs((PST-1))*'[UTC]'
    ax.text(0.4,-0.25,
      'Wind vectors averaged over: {time1} to {time2} {tzone}'.format(time1=t1,time2=t2,tzone=timezone),
        horizontalalignment='left',
        verticalalignment='top',
        transform=ax.transAxes, color = 'white',fontsize=14)
    ax.text(0.4, -0.29,
      'Modelled winds are from the High Resolution Deterministic Prediction System\nof Environment Canada: https://weather.gc.ca/grib/grib2_HRDPS_HR_e.html',
        horizontalalignment = 'left',
        verticalalignment = 'top',
        transform=ax.transAxes, color = 'white',fontsize=14)

    # Information_box
    axs = [ax1, ax2, ax3]
    for ax, name in zip (axs, names):
        plt.setp(ax.spines.values(), visible=False)
        ax.xaxis.set_visible(False); ax.yaxis.set_visible(False)
        axis_colors(ax, 'blue')
        display_time=(max_times[name]+PST*time_shift).strftime('%H:%M')


        ax.text(0.05, 0.9, name, fontsize=20,
                horizontalalignment='left', verticalalignment='top', color = 'w')
        ax.text(0.05, 0.7, 'Maximum Water Level: {:.2f} m'.format(max_sshs[name]+MSL_DATUMS[name]),fontsize=15,
                horizontalalignment='left',verticalalignment='top', color = 'w')
        ax.text(0.05, 0.3, 'Time: {time} {tzone}'.format(time=display_time,tzone=timezone),
	        fontsize=15,horizontalalignment='left', verticalalignment='top', color = 'w')
        ax.text(0.05, 0.5,'Wind speed: {:.1f} m/s'.format(float(max_winds[name])),fontsize=15,
                 horizontalalignment='left',verticalalignment='top', color = 'w')

    return fig
