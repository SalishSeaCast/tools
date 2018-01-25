# Copyright 2015-2016 Ben Moore-Maley and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Routines for loading SOG model output files into Pandas data structures
"""

from datetime import datetime, timedelta
from dateutil.parser import parse
import numpy as np
import pandas as pd
import xarray as xr
import carbonate as carb


def load_TS(filename):
    '''Load the timeseries file from path FILENAME into a dataframe TS_OUT
    '''

    # Load timeseries file and extract headers
    file_obj = open(filename, 'rt')
    for index, line in enumerate(file_obj):
        line = line.strip()
        if line.startswith('*FieldNames:'):
            field_names = line.split(': ', 1)[1].split(', ')
        elif line.startswith('*FieldUnits:'):
            field_units = line.split(': ', 1)[1].split(', ')
        elif line.startswith('*EndOfHeader'):
            break

    # Read timeseries data into dataframe and assign header
    data = pd.read_csv(
        filename, delim_whitespace=True, header=0, names=field_names,
        skiprows=index+1,
    )

    # Extract startdate and convert to MPL time
    datetime_start = parse(
        field_units[0].split('hr since ', 1)[1].split(' LST', 1)[0],
    )

    # Create date dataframe and append to DATA
    date = pd.DataFrame({
        'date': [
            datetime_start + timedelta(hours=hour) for hour in data['time']
        ],
    })
    TS_out = pd.concat([date, data], axis=1).set_index('date').to_xarray()

    return TS_out


def load_hoff(filename):
    '''Load the hoffmueller file from path FILENAME into a panel HOFF_OUT
    '''

    # Load timeseries file and extract headers
    file_obj = open(filename, 'rt')
    for index, line in enumerate(file_obj):
        line = line.strip()
        if line.startswith('*FieldNames:'):
            field_names = line.split(': ', 1)[1].split(', ')
        elif line.startswith('*FieldUnits:'):
            field_units = line.split(': ', 1)[1].split(', ')
        elif line.startswith('*HoffmuellerStartYr:'):
            year_start = line.split(': ', 1)[1]
        elif line.startswith('*HoffmuellerStartDay:'):
            day_start = line.split(': ', 1)[1]
        elif line.startswith('*HoffmuellerStartSec:'):
            sec_start = line.split(': ', 1)[1]
        elif line.startswith('*HoffmuellerInterval:'):
            interval = line.split(': ', 1)[1]
        elif line.startswith('*EndOfHeader'):
            break

    # Read timeseries data into dataframe and assign header
    data = pd.read_csv(filename, delim_whitespace=True, header=0,
                       names=field_names, skiprows=index, chunksize=82,
                       index_col=0)

    # Timestamp in matplotlib time
    datetime_start = datetime.strptime(
        year_start + day_start, '%Y%j',
    ) + timedelta(seconds=int(sec_start))

    # Extract dataframe chunks
    datetime_index = []
    data_list = []
    for index, chunk in enumerate(data):
        datetime_index.append(
            datetime_start + timedelta(days=index*float(interval)),
        )
        data_list.append(chunk.to_xarray())

    # Concatenate xarray dataset list along time axis
    hoff_out = xr.concat(
        data_list, dim=xr.DataArray(datetime_index, name='time', dims='time'),
    )

    return hoff_out


def loadSOG(filepath):
    '''Loads SOG timeseries and hoffmueller files from FILEPATH and returns
    Pandas dataframes PHYS_TS, BIO_TS, CHEM_TS, and panel HOFF
    '''

    # Load timeseries and hoff files from FILEPATH
    phys_TS = load_TS(filepath + 'timeseries/std_phys_SOG.out')
    bio_TS  = load_TS(filepath + 'timeseries/std_bio_SOG.out')
    chem_TS = load_TS(filepath + 'timeseries/std_chem_SOG.out')
    hoff    = load_hoff(filepath + 'profiles/hoff-SOG.dat')
    
    # Construct depth array for calcs
    depth_array = hoff.minor_axis.values
    date_array  = hoff.major_axis.values
    depth, dummy = np.meshgrid(depth_array, np.ones(date_array.size))
    
    # Calculate surface pH and Omega_A
    pH_sur, Omega_A_sur = carb.calc_carbonate(
       chem_TS['surface alkalinity'],                # TAlk [uM]
       chem_TS['surface DIC concentration'],         # DIC [uM]
       calc_sigma(phys_TS['surface temperature'],
                  phys_TS['surface salinity']),      # sigma_t [kg m3]
       phys_TS['surface salinity'],                  # salinity [PSS 78]
       phys_TS['surface temperature'],               # temperature [deg C]
       0.0,                                          # pressure [dbar]
       bio_TS['surface nitrate concentration'] / 16, # phosphate [uM]
       bio_TS['surface silicon concentration'])      # silicate [uM]
    
    # Calculate 3 m avg pH and Omega_A
    pH_3m, Omega_A_3m   = carb.calc_carbonate(
       chem_TS['3 m avg alkalinity'],                # TAlk [uM]
       chem_TS['3 m avg DIC concentration'],         # DIC [uM]
       calc_sigma(phys_TS['3 m avg temperature'],
                  phys_TS['3 m avg salinity']),      # sigma_t [kg m3]
       phys_TS['3 m avg salinity'],                  # salinity [PSS 78]
       phys_TS['3 m avg temperature'],               # temperature [deg C]
       0.0,                                          # pressure [dbar]
       bio_TS['3 m avg nitrate concentration'] / 16, # phosphate [uM]
       bio_TS['3 m avg silicon concentration'])      # silicate [uM]
    
    # Calculate hoffmueller pH and Omega_A
    hoff['pH'], hoff['Omega_A'] = carb.calc_carbonate(
       hoff.ix['alkalinity', :, :],                  # TAlk [uM]
       hoff.ix['dissolved inorganic carbon', :, :],  # DIC [uM]
       hoff.ix['sigma-t', :, :],                     # sigma_t [kg m3]
       hoff.ix['salinity', :, :],                    # salinity [PSS 78]
       hoff.ix['temperature', :, :],                 # temperature [deg C]
       depth,                                        # pressure [dbar]
       hoff.ix['nitrate', :, :] / 16,                # phosphate [uM]
       hoff.ix['silicon', :, :])                     # silicate [uM]
    
    # Append pH and Omega timeseries to CHEM_TS
    chem_TS = pd.concat([chem_TS, pd.DataFrame({
                    'surface pH': pH_sur,
                    '3 m avg pH': pH_3m,
                    'surface Omega_A': Omega_A_sur,
                    '3 m avg Omega_A': Omega_A_3m})], axis=1)

    return phys_TS, bio_TS, chem_TS, hoff


def loadSOG_batch(filesystem, bloomyear, filestr):
    '''Loads SOG timeseries and hoffmueller files given parameters FILESYSTEM,
    BLOOMYEAR, and FILESTR and returns PHYS_TS, BIO_TS, CHEM_TS, and HOFF
    '''

    # Specify standard timeseries output paths
    filepath = '/ocean/bmoorema/research/SOG/{0}/{1}/{2}/{3}/{3}_{4}/'.format(
        filesystem['category'], filesystem['test'], filesystem['type'],
        bloomyear, filestr)
    
    # Load timeseries and hoffmueller files from FILEPATH
    phys_TS, bio_TS, chem_TS, hoff = loadSOG(filepath)
    
    return phys_TS, bio_TS, chem_TS, hoff


def calc_sigma(T, S):
    '''Calculate and return density anomaly SIGMA_T given temperature T and
    salinity S
    '''
    
    # Calculate the square root of the salinities
    sqrtS = np.sqrt(S)

    # Calculate the density profile at the grid point depths
    # Pure water density at atmospheric pressure
    # (Bigg P.H., (1967) Br. J. Applied Physics 8 pp 521-537)
    R1 = ((((6.536332e-9 * T - 1.120083e-6) * T + 1.001685e-4) * T
           - 9.095290e-3) * T + 6.793952e-2) * T - 28.263737
    
    # Seawater density at atmospheric pressure
    # Coefficients of salinity
    R2 = (((5.3875e-9 * T - 8.2467e-7) * T + 7.6438e-5) * T
          - 4.0899e-3) * T + 8.24493e-1
    R3 = (-1.6546e-6 * T + 1.0227e-4) * T - 5.72466e-3
    
    # International one-atmosphere equation of state of seawater
    sig = (4.8314e-4 * S + R3 * sqrtS + R2) * S + R1
    
    # Specific volume at atmospheric pressure
    V350P = 1.0 / 1028.1063
    sva = -sig * V350P / (1028.1063 + sig)
    
    # Density anomoly at atmospheric pressure
    sigma = 28.106331 - sva / (V350P * (V350P + sva))
    
    return sigma
