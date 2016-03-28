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

# Read  from command line
pres_file=sys.argv[1] #pressure file
tmp_file=sys.argv[2] #temperature file
sav_dir=sys.argv[3] #directory for saving

#Grab time
f = nc.Dataset(tmp_file)
time =f.variables['time_counter']

#generate strings for saving file
a=arrow.get(time.time_origin, 'YYYY-MMM-DD HH:mm:ss')
y=a.year; mo=a.month; da=a.day
m = "%02d" % (mo,); d= "%02d" % (da,)
sav_str = sav_dir + '/slp_corr_y'+str(y) + 'm'+str(m)+'d'+str(d)+'.nc'

#generate the pressure file
nc_tools.generate_pressure_file(sav_str,pres_file,tmp_file,'altitude_CGRF.nc',a)


