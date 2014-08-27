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

#Script to correct CGRF pressure to sea level.
#Assumes atmosphere is a dry ideal gas in hydrostatic balance and has a 
#constant lapse rate. See this notebook:
#  http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/analysis/raw/tip/storm_surges/Pressure%20to%20sea%20level.ipynb

# Call like this: python correct_pressure.py pressure_file temperature_file save_directory

from __future__ import division
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
from salishsea_tools import (viz_tools,
    bathy_tools,
    nc_tools,
)
import sys
import arrow

# pressure correction function
def slp(Z,P,T):
    ps = P*(gam*(Z/T) +1)**(g/gam/R)
    return ps

#define constants
R = 287 #ideal gas constant
g = 9.81 #gravity
gam = 0.0098 #lapse rate(deg/m)
p0=101000 #average sea surface heigh in Pa

# Read  from command line
pres_file=sys.argv[1] #pressure file
tmp_file=sys.argv[2] #temperature file
sav_dir=sys.argv[3] #directory for saving

#Load pressure, temperature and altitude data
f = nc.Dataset(pres_file)
press=f.variables['atmpres']
f = nc.Dataset(tmp_file)
temp=f.variables['tair']
time =f.variables['time_counter']
lon=f.variables['nav_lon']
lat=f.variables['nav_lat']
f=nc.Dataset('altitude_y2003.nc')
alt=f.variables['alt']

#correct pressure
press_corr=np.zeros(press.shape)
for k in range(press.shape[0]):
    press_corr[k,:,:] = slp(alt,press[k,:,:],temp[k,:,:])

#generate strings for saving file
a=arrow.get(time.time_origin, 'YYYY-MMM-DD HH:mm:ss')
y=a.year; mo=a.month; da=a.day
m = "%02d" % (mo,); d= "%02d" % (da,)
sav_str = sav_dir + '/slp_corr_y'+str(y) + 'm'+str(m)+'d'+str(d)+'.nc'

#Create netcdf
slp_file = nc.Dataset(sav_str, 'w', zlib=True)
# dataset attributes
slp_file.title='CGRF pressure corrected to sea level - ' +str(y)+'/'+str(m)+'/'+str(d)
slp_file.comment='Corrected sea level pressure -CGRF'
#dimensions
slp_file.createDimension('time_counter',0)
slp_file.createDimension('y', press_corr.shape[1])
slp_file.createDimension('x', press_corr.shape[2])
#time counter
time_counter=slp_file.createVariable('time_counter','double', ('time_counter',))
time_counter.calendar=time.calendar
time_counter.long_name=time.long_name
time_counter.title=time.title
time_counter.units=time.units
time_counter.time_origin=time.time_origin
time_counter[:]=time[:]
#lat/lon variables
nav_lat = slp_file.createVariable('nav_lat','float32',('y','x'))
nav_lat.long_name = 'Latitude'
nav_lat.units = 'degrees_north'
nav_lat.valid_max=lat.valid_max
nav_lat.valid_min=lat.valid_min
nav_lat[:]=lat
nav_lon = slp_file.createVariable('nav_lon','float32',('y','x'))
nav_lon.long_name = 'Longitude'
nav_lon.units = 'degrees_east'
nav_lon.valid_max=lon.valid_max
nav_lon.valid_min=lon.valid_min
nav_lon[:]=lon
#Pressure
atmpres = slp_file.createVariable('atmpres','float32',('time_counter','y','x'))
atmpres.long_name = 'Sea Level Pressure'
atmpres.units = 'Pascals'
atmpres.missing_value=press.missing_value
atmpres.valid_min=press.valid_min
atmpres.valid_max=press.valid_max
atmpres.axis=press.axis
atmpres[:]=press_corr[:]

slp_file.close()

