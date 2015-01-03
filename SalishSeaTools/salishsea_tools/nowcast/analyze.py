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
figures for analysis and model evaluation of daily nowcast runs.
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

from salishsea_tools.nowcast import figures

# Time shift for plotting in PST
time_shift = datetime.timedelta(hours=-8)

# Average mean sea level calculated over 1983-2001
# (To be used to centre model output about mean sea level)
MSL_DATUMS = {
    'Point Atkinson': 3.10, 'Victoria': 1.90,
    'Campbell River': 2.89, 'Patricia Bay': 2.30}

def get_filenames(t_orig, t_final, period, grid, model_path):
  """Returns a list with the filenames for all files over the
  defined period of time and sorted in chronological order.
  
  :arg t_orig: The beginning of the date range of interest.
  :type t_orig: datetime object
  
  :arg t_final: The end of the date range of interest.
  :type t_final: datetime object
  
  :arg period: Time interval of model results (eg. 1h or 1d).
  :type period: string
  
  :arg grid: Type of model results (eg. grid_T, grid_U, etc).
  :type grid: string
  
  :arg model	_path: The directory where the model files are stored.
  :type model_path: string
  
  :returns: list of strings (files).
  """
  
  numdays=(t_final-t_orig).days
  dates = [ t_orig + datetime.timedelta(days=num) for num in range(0,numdays+1)]
  dates.sort();
  
  allfiles=glob.glob(model_path+'*/SalishSea_'+period+'*_'+grid+'.nc')
  sstr ='SalishSea_'+period+ '_'+dates[0].strftime('%Y%m%d') +'_'+dates[0].strftime('%Y%m%d') +'_'+grid+'.nc'
  estr ='SalishSea_'+period+ '_'+dates[-1].strftime('%Y%m%d') +'_'+dates[-1].strftime('%Y%m%d') +'_'+grid+'.nc'
  
  files=[]
  for filename in allfiles:
    if os.path.basename(filename) >= sstr:
      if os.path.basename(filename) <= estr:
	files.append(filename)
	
  files.sort(key=os.path.basename)
  
  return files
  
def combine_files(files, var, depth, j, i):
  """Returns the value of the variable entered over 
  multiple files covering a certain period of time.
  
  :arg files: Multiple result files in chronological order.
  :type files: list
  
  :arg var: Name of variable (sossheig = sea surface height,
                      vosaline = salinity, votemper = temperature,
                      vozocrtx = Velocity U-component,
                      vomecrty = Velocity V-component).
  :type var: string
  
  :arg depth: Depth of model results ('None' if var=sossheig).
  :type depth: integer or string
  
  :arg j: Longitude index of location.
  :type j: integer
  
  :arg i: Latitude index of location.
  :type i: integer
  
  :returns: array of model results (var_ary and time).
  """
  
  time=np.array([]); 
  var_ary=np.array([]);
  
  for f in files:
    G=nc.Dataset(f)
    if depth=='None':
      var_tmp=G.variables[var][:,j,i]
    else:
      var_tmp=G.variables[var][:,depth,j,i]
    
    var_ary=np.append(var_ary,var_tmp,axis=0)
    t=nc_tools.timestamp(G,np.arange(var_tmp.shape[0]))
    for ind in range(len(t)):
      t[ind]=t[ind].datetime
    
    time=np.append(time,t)
	
  return var_ary,time

def plot_files(grid_B, files, var, depth, t_orig, t_final, name, figsize=(20,5)):
  """Plots values of  variable over multiple files covering 
  a certain period of time.
  
  :arg grid_B: Bathymetry dataset for the Salish Sea NEMO model.
  :type grid_B: :class:`netCDF4.Dataset`
    
  :arg files: Multiple result files in chronological order.
  :type files: list
    
  :arg var: Name of variable (sossheig = sea surface height,
                      vosaline = salinity, votemper = temperature,
                      vozocrtx = Velocity U-component,
                      vomecrty = Velocity V-component).
  :type var: string
    
  :arg depth: Depth of model results ('None' if var=sossheig).
  :type depth: integer or string
    
  :arg name: The name of the station.
  :type name: string
    
  :arg figsize: Figure size (width, height) in inches.
  :type figsize: 2-tuple
  
  :returns: matplotlib figure object instance (fig) and axis object (ax).
  """
    
  # Stations information
  [lats, lons] = figures.station_coords()
    
  # Bathymetry
  bathy, X, Y = tidetools.get_bathy_data(grid_B)
    
  # Get index
  [j,i]=tidetools.find_closest_model_point(lons[name],lats[name],X,Y,bathy,allow_land=False)
    
  # Call function
  var_ary, time= combine_files(files, var, depth, j, i)
    
  #Figure
  fig, ax=plt.subplots(1,1,figsize=figsize)
  
  #Plot
  ax.plot(time,var_ary)
  
  ax_start = t_orig
  ax_end = t_final + datetime.timedelta(days=1)
  ax.set_xlim(ax_start, ax_end)
 
  hfmt = mdates.DateFormatter('%m/%d %H:%M')
  ax.xaxis.set_major_formatter(hfmt)
  fig.autofmt_xdate()
    
  return fig, ax
  
def compare_ssh_tides(grid_B, files, t_orig, t_final, name, PST=0, MSL=0):
    
  fig, ax = plot_files(grid_B, files, 'sossheig', 'None', t_orig, t_final, name)
  
  figures.plot_tides(ax, name, t_orig, PST, MSL, color='green')
  
  ax_start = t_orig
  ax_end = t_final + datetime.timedelta(days=1)
  ax.set_xlim(ax_start, ax_end)
  