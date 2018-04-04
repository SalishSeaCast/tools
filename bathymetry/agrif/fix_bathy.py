# Copyright 2013-2018 The Salish Sea NEMO Project and
# The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Simple script to enforce minimum depth and fix the longitudes.
# Run this on the file produced by agrif_create_bathy.exe.


import netCDF4 as nc
import numpy as np
import sys


def fix_bathy(infile, mindep):
    """
    Simple script to enforce minimum depth and fix the longitudes.

    Run this on the file produced by agrif_create_bathy.exe.
    """
    with nc.Dataset(infile, 'r+') as f:
        # Enforce minimum bathymetry
        bm = f.variables['Bathymetry'][:]
        idx = (bm > 0) & (bm < mindep)
        if np.any(idx):
            md = np.min(bm[idx])
            print("Min depth {:3f} m, resetting to {:3f} m".format(md, mindep))
            bm[idx] = mindep
            f.variables['Bathymetry'][:] = bm

        # Enforce nav_lon to be in [-180,180] and not [0,360]
        lon = f.variables['nav_lon'][:]
        if np.any(lon > 180):
            lon[lon > 180] -= 360
        f.variables['nav_lon'][:] = lon
        f.variables['nav_lon'].valid_min = np.min(lon)
        f.variables['nav_lon'].valid_max = np.max(lon)


if __name__ == "__main__":
    fix_bathy(sys.argv[1], 4)
