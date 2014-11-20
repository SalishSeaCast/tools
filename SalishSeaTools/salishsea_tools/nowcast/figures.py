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
from salishsea_tools import nc_tools, stormtools, tidetools
import datetime




#SEA SURFACE HEIGHT
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
    bathy = gridB.variables['Bathymetry'][:, :]
    X = gridB.variables['nav_lon'][:, :]
    Y = gridB.variables['nav_lat'][:, :]
    
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
