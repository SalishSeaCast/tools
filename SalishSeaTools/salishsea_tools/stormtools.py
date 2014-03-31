"""
A collection of tools for storm surge results from the Salish Sea Model.
"""

"""
Copyright 2013-2014 The Salish Sea MEOPAR contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import netCDF4 as NC
import numpy as np
import datetime


def convert_date_seconds(times, start):
    """
    This function converts model output time in seconds to datetime objects.
    
    :arg times: array of seconds since the start date of a simulation. From time_counter in model output.
    :type times: int
    
    :arg start: string containing the start date of the simulation in format '01-Nov-2006'
    :type start: str

    :arg diff: string indicating the time step in the times data E.g. months, seconds, days
    :type diff: str
        
    :returns: array of datetime objects representing the time of model outputs.
    """
    import arrow

    arr_times=[]
    for ii in range(0,len(times)):
        arr_start =arrow.Arrow.strptime(start,'%d-%b-%Y')
        arr_new=arr_start.replace(seconds=times[ii])
        arr_times.append(arr_new.datetime)

    return arr_times

def convert_date_hours(times, start):
    """
    This function converts model output time in seconds to datetime objects.
    
    :arg times: array of seconds since the start date of a simulation. From time_counter in model output.
    :type times: int
    
    :arg start: string containing the start date of the simulation in format '01-Nov-2006'
    :type start: str

    :arg diff: string indicating the time step in the times data E.g. months, seconds, days
    :type diff: str
        
    :returns: array of datetime objects representing the time of model outputs.
    """
    import arrow

    arr_times=[]
    for ii in range(0,len(times)):
        arr_start =arrow.Arrow.strptime(start,'%d-%b-%Y')
        arr_new=arr_start.replace(hours=times[ii])
        arr_times.append(arr_new.datetime)

    return arr_times

def get_CGRF_weather(start,end,grid):
    """ 
    Returns the CGRF weather between the dates start and end at the grid point defined in grid. 

    :arg start: string containing the start date of the CGRF collection in format '01-Nov-2006'
    :type start: str

    :arg start: string containing the end date of the CGRF collection in format '01-Nov-2006'
    :type start: str

    :arg grid: array of the CGRF grid coordinates for the point of interest eg. [244,245]
    :arg type: arr of ints

    :returns: windspeed, pressure and time array from CGRF data for the times indicated
    """
    u10=[]; v10=[]; pres=[]; time=[];
    import arrow
    st_ar=arrow.Arrow.strptime(start, '%d-%b-%Y')
    end_ar=arrow.Arrow.strptime(end, '%d-%b-%Y')
    
    CGRF_path = '/ocean/dlatorne/MEOPAR/CGRF/NEMO-atmos/'
    
    for r in arrow.Arrow.range('day', st_ar, end_ar):
        #u
        strU='u10_y' + str(r.year) +'m' +str(r.month) + 'd'+str(r.day) +'.nc'
        fU=NC.Dataset(CGRF_path+strU)
        var=fU.variables['u_wind'][:,grid[0],grid[1]]; u10.extend(var[:])
        
        #time
        tim=fU.variables['time_counter']; time.extend(tim[:] + (r.day-st_ar.day)*24)
        times =convert_date_hours(time,start)
        
        #v
        strV='v10_y' + str(r.year) +'m' +str(r.month) + 'd'+str(r.day) +'.nc'
        fV=NC.Dataset(CGRF_path+strV)
        var=fV.variables['v_wind'][:,grid[0],grid[1]]; v10.extend(var[:])
        
        #pressure
        strP='slp_y' + str(r.year) +'m' +str(r.month) + 'd'+str(r.day) +'.nc'
        fP=NC.Dataset(CGRF_path+strP)
        var=fP.variables['atmpres'][:,grid[0],grid[1]]; pres.extend(var[:])
        
        u10s=np.array(u10); v10s=np.array(v10); press=np.array(pres)
        windspeed=np.sqrt(u10s**2+v10s**2)
    return windspeed, press, times

def combine_data(data_list):
    """
    This function combines output from a list of netcdf files into a dict objects of model fields. It is used for easy handling of output from thalweg and surge stations.
    
    :arg data_list: dict object that contains the netcdf handles for the files to be combined. e.g {'Thelweg1': f1, 'Thalweg2': f2,...} where f1 = NC.Dataset('1h_Thalweg1.nc','r')
    :type data_list: dict object

    :returns: dict objects us, vs, lats, lons, sals, tmps, sshs with the zonal velocity, meridional velocity, latitude, longitude, salinity, temperature, and sea surface height for each station. The keys are the same as those in data_list. For example, us['Thalweg1'] contains the zonal velocity from the Thalweg 1 station.
    """
    
    us={}; vs={}; lats={}; lons={}; sals={}; tmps={}; sshs={};
    for k in data_list:
        net=data_list.get(k)
        us[k]=net.variables['vozocrtx']
        vs[k]=net.variables['vomecrty']
        lats[k]=net.variables['nav_lat']        
        lons[k]=net.variables['nav_lon']
        tmps[k]=net.variables['votemper']
        sals[k]=net.variables['vosaline']
        sshs[k]=net.variables['sossheig']
    return us, vs, lats, lons, tmps, sals, sshs



def get_variables(fU,fV,fT,timestamp,depth):
    """
    Generates masked u,v,SSH,S,T from NETCDF handles fU,fV,fT at timestamp and depth
    
    :arg fU: netcdf handle for Ugrid model output
    :type fU: netcdf handle 

    :arg fV: netcdf handle for Vgrid model output
    :type fV: netcdf handle 

    :arg fT: netcdf handle for Tgrid model output
    :type fT: netcdf handle  

    :arg timestamp: the timestamp for desired model output
    :type timestamp: int
    
    :arg depth: the model z-level for desired output
    :type depth: int

    :returns: masked arrays U,V,E,S,T with of zonal velocity,merdional velocity, sea surface height, salinity, and temperature at specified time and z-level.

    """

    import numpy as np

    # get u and ugrid
    u_vel = fU.variables['vozocrtx']  #u currents and grid
    U = u_vel[timestamp,depth,:,:] #grab data at specified level and time.
    #mask u so that white is plotted on land points
    mu =U== 0
    U= np.ma.array(U,mask=mu)
    
    #get v and v grid
    v_vel = fV.variables['vomecrty']  #v currents and grid
    V = v_vel[timestamp,depth,:,:] #grab data at specified level and time.

    #mask v so that white is plotted on land points
    mu = V == 0
    V= np.ma.array(V,mask=mu)

    #grid for T points
    eta = fT.variables['sossheig']
    E = eta[timestamp,:,:]
    mu=E==0; E = np.ma.array(E,mask=mu)

    sal = fT.variables['vosaline']
    S= sal[timestamp,depth,:,:]
    mu=S==0; S= np.ma.array(S,mask=mu)

    temp=fT.variables['votemper']
    T = temp[timestamp,depth,:,:]
    mu=T==0; T = np.ma.array(T,mask=mu)
    
    return U, V, E, S, T
