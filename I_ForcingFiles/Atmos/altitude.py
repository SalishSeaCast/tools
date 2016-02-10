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

#A script to calculate the average grid cell height from CGRF atmospheric 
#forcing files. One month of data should be given at a time. Saves a netcdf 
#file with the averagre grid cell height.

#Assumes atmosphere is a dry ideal gas in hydrostatic balance and has a 
#constant lapse rate. See this notebook:
#  http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/analysis/raw/tip/storm_surges/Pressure%20to%20sea%20level.ipynb

from __future__ import division
import netCDF4 as NC
import numpy as np
from salishsea_tools import nc_tools

#define the month and year.
start_day = 1
end_day=31
month=12
year =2003

#define constants
R = 287 #ideal gas constant
g = 9.81 #gravity
gam = 0.0098 #lapse rate(deg/m)
p0=101000 #average sea surface heigh in Pa

#path for CGRF data
CGRF = '/home/dlatorne/MEOPAR/CGRF/NEMO-atmos/'

#function for calculating altitude
def altitude(P,T,p0):
    #P is the pressure over the grid and T is the temperature
    #p0 is the sea level pressure. An appropriate choice is 101000 Pa.
    z = T/gam*((P/p0)**(-gam*R/g) -1 )
    return z

#an array to store cumulative grid cell height
zcum =0

for d in xrange(start_day,end_day+1):
    #load CGRF data
    m = "%02d" % (month,); da= "%02d" % (d,)
    pstr = 'slp_y'+str(year)+'m' + str(m) +'d'+str(da)+'.nc'
    print pstr
    Tstr =  't2_y'+str(year)+'m' + str(m) +'d'+str(da)+'.nc'
    C = NC.Dataset(CGRF+pstr,'r')
    press=C.variables['atmpres'][:]
    C = NC.Dataset(CGRF+Tstr,'r')
    temp=C.variables['tair'][:]

    #average pressure and temperature over one day
    pavg = np.mean(press,0)
    tavg = np.mean(temp,0)

    #caclulate average grid cell altitude over one day
    zavg=altitude(pavg,tavg,p0)
    zcum=zcum+zavg

Z = zcum/end_day
lat=C.variables['nav_lat'][:]
lon=C.variables['nav_lon'][:]

#save in a netcdf file
alt_str= 'altitude_y' +str(year) +'m'+str(m)+'.nc'
alt_file = NC.Dataset(alt_str, 'w', zlib=True)
# dataset attributes - can't get this to work
#nc_tools.init_dataset_attrs(
#    alt_file, 
#    title='Average monthly altitude',
#    notebook='altitude.py',
#    nc_filepath=alt_str,
#    comment='Average altitude at each CGRF grid cell')
#dimensions
alt_file.createDimension('x', Z.shape[0])
alt_file.createDimension('y', Z.shape[1])
#lat/lon variables
nav_lat = alt_file.createVariable('nav_lat','float32',('x','y'))
nav_lat.long_name = 'Latitude'
nav_lat.units = 'degrees_north'
nav_lat[:]=lat
nav_lon = alt_file.createVariable('nav_lon','float32',('x','y'))
nav_lon.long_name = 'Longitude'
nav_lon.units = 'degrees_east'
nav_lon[:]=lon
#altitude
alt = alt_file.createVariable('alt','float32',('x','y'))
alt.long_name = 'Altitude'
alt.units = 'metres'
alt[:]=Z

alt_file.close()
