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

"""A collection of functions for working with the output of WebTide.
"""


def get_data_from_csv(tidevar, constituent, depth, CFactor):
    """Get the constituent data from the csv file.
    """
    import pandas as pd
    from math import radians
    import numpy
    import math

    theta = radians(29)  # rotation of the grid = 29 degrees

    # correction factors
    base = constituent
    corr = 1   # if not otherwise set
    corr_shift = 0   # if not otherwise set

    if constituent == "M2":
        corr_pha = CFactor['A2 Phase']
        corr_amp = CFactor['A2 Amp']
        corr = CFactor['A2 Flux']
        corr_shift = CFactor['A2 Shift']
    elif constituent == "S2":
        corr_pha = CFactor['A2 Phase'] + CFactor['S2 Phase']
        corr_amp = CFactor['A2 Amp'] * CFactor['S2 Amp']
        corr = CFactor['A2 Flux']
        corr_shift = CFactor['A2 Shift']
    elif constituent == "N2":
        corr_pha = CFactor['A2 Phase'] + CFactor['N2 Phase']
        corr_amp = CFactor['A2 Amp'] * CFactor['N2 Amp']
        corr = CFactor['A2 Flux']
        corr_shift = CFactor['A2 Shift']
    elif constituent == "K2":  # based on S2
        base = "S2"
        corr_pha = CFactor['A2 Phase'] + CFactor['S2 Phase']
        corr_amp = CFactor['A2 Amp'] * CFactor['S2 Amp']
        corr = CFactor['A2 Flux']
        corr_shift = CFactor['A2 Shift']
    elif constituent == "K1":
        corr_pha = CFactor['A1 Phase']
        corr_amp = CFactor['A1 Amp']
    elif constituent == "O1":
        corr_pha = CFactor['A1 Phase'] + CFactor['O1 Phase']
        corr_amp = CFactor['A1 Amp'] * CFactor['O1 Amp']
    elif constituent == "P1":  # based on K1
        base = "K1"
        corr_pha = CFactor['A1 Phase']
        corr_amp = CFactor['A1 Amp']
    elif constituent == "Q1":
        corr_pha = CFactor['A1 Phase'] + CFactor['Q1 Phase']
        corr_amp = CFactor['A1 Amp'] * CFactor['Q1 Amp']
    # WATER LEVEL ELEVATION
    if tidevar == 'T':
        webtide = pd.read_csv('Tidal Elevation Constituents T.csv',
                              skiprows=2)
        webtide = webtide.rename(columns={'Constituent': 'const',
                                          'Longitude': 'lon',
                                          'Latitude': 'lat',
                                          'Amplitude (m)': 'amp',
                                          'Phase (deg GMT)': 'pha'})

        # how long is the boundary?
        boundlen = len(depth[depth != 0])

        # along western boundary, etaZ1 and etaZ2 are 0 in masked cells
        amp_W = numpy.zeros((boundlen+10, 1))
        pha_W = numpy.zeros((boundlen+10, 1))

        # find the boundary
        I = numpy.where(depth != 0)

        # allocate the M2 phase and amplitude from Webtide
        # to the boundary cells
        # (CHECK: Are these allocated in the right order?)
        amp_W[5:boundlen+5, 0] = webtide[webtide.const == (base + ':')].amp * corr_amp
        pha_W[5:boundlen+5, 0] = webtide[webtide.const == (base + ':')].pha + corr_pha

        if constituent == "K1" or constituent == "M2":
            print (constituent, "eta")
            print (pha_W)

        if constituent == "P1":
            amp_W = amp_W * 0.310
            pha_W = pha_W - 3.5
        elif constituent == "K2":
            amp_W = amp_W * 0.235
            pha_W = pha_W - 5.7

        # convert the phase and amplitude to cosine and sine format that NEMO likes
        Z1 = amp_W * numpy.cos(numpy.radians(pha_W))
        Z2 = amp_W * numpy.sin(numpy.radians(pha_W))

    #U VELOCITY
    if tidevar == 'U':
        webtide = pd.read_csv('Tidal Current Constituents U.csv',
                              skiprows=2)
        webtide = webtide.rename(columns={'Constituent': 'const',
                                          'Longitude': 'lon',
                                          'Latitude': 'lat',
                                          'U Amplitude (m)': 'ewamp',
                                          'U Phase (deg GMT)': 'ewpha',
                                          'V Amplitude (m)': 'nsamp',
                                          'V Phase (deg GMT)': 'nspha'})

        # how long is the boundary?
        boundlen = len(depth[depth != 0])

        # Convert amplitudes from north/south u/v into grid co-ordinates

        # Convert phase from north/south into grid co-ordinates (see docs/tides/tides_data_acquisition for details)
        ua_ugrid = numpy.array(webtide[webtide.const == (base + ':')].ewamp) * corr
        va_ugrid = numpy.array(webtide[webtide.const == (base + ':')].nsamp) * corr
        uphi_ugrid = numpy.radians(numpy.array(webtide[webtide.const == (base + ':')].ewpha))
        vphi_ugrid = numpy.radians(numpy.array(webtide[webtide.const == (base + ':')].nspha))

        uZ1 = (ua_ugrid * numpy.cos(theta) * numpy.cos(uphi_ugrid) -
               va_ugrid * numpy.sin(theta) * numpy.sin(vphi_ugrid))
        uZ2 = (ua_ugrid * numpy.cos(theta) * numpy.sin(uphi_ugrid) +
               va_ugrid * numpy.sin(theta) * numpy.cos(vphi_ugrid))
        print ('blah')

        # adjustments for phase correction
        amp = numpy.sqrt(uZ1[:]**2 + uZ2[:]**2)
        pha = []
        for i in range(0, len(amp)):
            pha.append(math.atan2(uZ2[i], uZ1[i]) + numpy.radians(corr_pha + corr_shift))

        if constituent == "P1":
            amp = amp * 0.310
            pha[:] = [phase - numpy.radians(3.5) for phase in pha]
        elif constituent == "K2":
            amp = amp * 0.235
            pha[:] = [phase - numpy.radians(5.7) for phase in pha]

        uZ1 = amp * numpy.cos(pha) * corr_amp
        uZ2 = amp * numpy.sin(pha) * corr_amp

        # find the boundary
        I = numpy.where(depth!=0)

        #allocate the z1 and z2 I calculated from Webtide to the boundary cells
        #along western boundary, etaZ1 and etaZ2 are 0 in masked cells
        #(CHECK: Are these allocated in the right order?)
        Z1 = numpy.zeros((boundlen+10,1))
        Z2 = numpy.zeros((boundlen+10,1))
        Z1[5:boundlen+5,0] = uZ1
        Z2[5:boundlen+5,0] = uZ2

    #V VELOCITY
    if tidevar == 'V':
        webtide = pd.read_csv('Tidal Current Constituents V.csv',\
                              skiprows = 2)
        webtide = webtide.rename(columns={'Constituent': 'const', 'Longitude': 'lon', 'Latitude': 'lat', \
                                          'U Amplitude (m)': 'ewamp', 'U Phase (deg GMT)': 'ewpha',\
                                          'V Amplitude (m)': 'nsamp', 'V Phase (deg GMT)': 'nspha'})
	#how long is the boundary?
        boundlen = len(depth[depth!=0])
        print(boundlen)

        #Convert phase from north/south into grid co-ordinates (see docs/tides/tides_data_acquisition for details)
        ua_vgrid = numpy.array(webtide[webtide.const==(base+':')].ewamp)*corr
        va_vgrid = numpy.array(webtide[webtide.const==(base+':')].nsamp)*corr
        uphi_vgrid = numpy.radians(numpy.array(webtide[webtide.const==(base+':')].ewpha))
        vphi_vgrid = numpy.radians(numpy.array(webtide[webtide.const==(base+':')].nspha))

        vZ1 = -ua_vgrid*numpy.sin(theta)*numpy.cos(uphi_vgrid) - va_vgrid*numpy.cos(theta)*numpy.sin(vphi_vgrid)
        vZ2 = -ua_vgrid*numpy.sin(theta)*numpy.sin(uphi_vgrid) + va_vgrid*numpy.cos(theta)*numpy.cos(vphi_vgrid)

        # adjustments for phase correction
        amp = numpy.sqrt(vZ1[:]**2 + vZ2[:]**2);
        pha=[]
        for i in range(0,len(amp)):
            pha.append(math.atan2(vZ2[i],vZ1[i])+numpy.radians(corr_pha+corr_shift))

        if constituent == "P1":
            amp = amp * 0.310
            pha[:] = [phase - numpy.radians(3.5) for phase in pha]
        elif constituent == "K2":
            amp = amp * 0.235
            pha[:] = [phase - numpy.radians(5.7) for phase in pha]

        vZ1 = amp*numpy.cos(pha)*corr_amp
        vZ2 = amp*numpy.sin(pha)*corr_amp

        #find the boundary
        I = numpy.where(depth!=0)

        #allocate the z1 and z2 I calculated from Webtide to the boundary cells
        #along western boundary, etaZ1 and etaZ2 are 0 in masked cells
        #(CHECK: Are these allocated in the right order?)
        Z1 = numpy.zeros((boundlen+9,1))
        Z2 = numpy.zeros((boundlen+9,1))
        Z1[4:boundlen+4,0] = vZ1
        Z2[4:boundlen+4,0] = vZ2

    return Z1, Z2, I, boundlen

#Define a function that creates Netcdf files from the following information
# - choose variable (elevation ('T'), u ('U') or v ('V'))
# - choose constituent ('O1', 'P1', 'Q1', 'K1', 'K2', 'N2', 'M2', 'S2')
# - give z1 and z2 data
# - depth data


def create_tide_netcdf(tidevar, constituent, depth, number, code, CFactors):
    import netCDF4 as NC
    import numpy

    # get the data from the csv file
    Z1, Z2, I, boundlen = get_data_from_csv(
        tidevar, constituent, depth, CFactors)
    print (boundlen, tidevar, I[0][0])

    if len(number) == 1:
        name = 'SalishSea' + number
    else:
        name = number
    nemo = NC.Dataset(
         name+'_'+code+'_west_tide_'+constituent+'_grid_'+tidevar+'.nc',
         'w')
    nemo.description = 'Tide data from WebTide - K1 phase shifted'

    # give the netcdf some dimensions
    # note that the real boundary extends on more grid point to the south
    # in v than for ssh or u
    if tidevar == 'V':
        nemo.createDimension('xb', boundlen+9)
    else:
        nemo.createDimension('xb', boundlen+10)
    nemo.createDimension('yb', 1)

    # add in the counter around the boundary
    # (taken from Susan's code in Prepare Tide Files)
    xb = nemo.createVariable('xb', 'int32', ('xb',), zlib=True)
    xb.units = 'non dim'
    xb.longname = 'counter around boundary'
    yb = nemo.createVariable('yb', 'int32', ('yb',), zlib=True)
    yb.units = 'non dim'
    if tidevar == 'V':
        xb[:] = numpy.arange(I[0][0]-4, I[0][-1]+6)
    else:
        xb[:] = numpy.arange(I[0][0]-5, I[0][-1]+6)
    yb[0] = 1
    print (xb.shape)

    # create i and j grid position
    nbidta = nemo.createVariable('nbidta', 'int32', ('yb', 'xb'), zlib=True)
    nbidta.units = 'non dim'
    nbidta.longname = 'i grid position'
    nbjdta = nemo.createVariable('nbjdta', 'int32', ('yb', 'xb'), zlib=True)
    nbjdta.units = 'non dim'
    nbjdta.longname = 'j grid position'
    nbrdta = nemo.createVariable('nbrdta', 'int32', ('yb', 'xb'), zlib=True)
    nbrdta.units = 'non dim'

    # give values for West Boundary (this is where the webtide points go)
    nbidta[:] = 1
    if tidevar == 'V':
        nbjdta[:] = numpy.arange(I[0][0]-4, I[0][-1]+6)
    else:
        nbjdta[:] = numpy.arange(I[0][0]-5, I[0][-1]+6)

    # give values for the corner
    nbrdta[:] = 1

    if tidevar == 'T':
        z1 = nemo.createVariable('z1', 'float32', ('yb', 'xb'), zlib=True)
        z1.units = 'm'
        z1.longname = 'tidal elevation: cosine'
        z2 = nemo.createVariable('z2', 'float32', ('yb', 'xb'), zlib=True)
        z2.units = 'm'
        z2.longname = 'tidal elevation: sine'
        z1[0, 0:boundlen+10] = Z1[:, 0]
        z2[0, 0:boundlen+10] = Z2[:, 0]
        print(Z1.size)
        print(z1.size)
        print(z2.size)

    if tidevar == 'U':
        u1 = nemo.createVariable('u1', 'float32', ('yb', 'xb'), zlib=True)
        u1.units = 'm'
        u1.longname = 'tidal x-velocity: cosine'
        u2 = nemo.createVariable('u2', 'float32', ('yb', 'xb'), zlib=True)
        u2.units = 'm'
        u2.longname = 'tidal x-velocity: sine'
        u1[0, 0:boundlen+10] = Z1[:, 0]
        u2[0, 0:boundlen+10] = Z2[:, 0]

    if tidevar == 'V':
        v1 = nemo.createVariable('v1', 'float32', ('yb', 'xb'), zlib=True)
        v1.units = 'm'
        v1.longname = 'tidal y-velocity: cosine'
        v2 = nemo.createVariable('v2', 'float32', ('yb', 'xb'), zlib=True)
        v2.units = 'm'
        v2.longname = 'tidal y-velocity: sine'
        print (v1.shape, v2.shape)
        print (Z1.shape)
        v1[0, 0:boundlen+9] = Z1[:, 0]
        v2[0, 0:boundlen+9] = Z2[:, 0]

    return Z1, Z2
    nemo.close()


def create_northern_tides(Z1,Z2,tidevar,constituent,code, name='SalishSea2'):
    import netCDF4 as NC
    import numpy as np
    from salishsea_tools import nc_tools

    nemo = NC.Dataset(name+'_'+code+'_North_tide_'+constituent+'_grid_'+tidevar+'.nc', 'w', zlib=True)

    #start and end points
    starti = 32
    endi = 62
    lengthi = endi-starti

    # dataset attributes
    nc_tools.init_dataset_attrs(
        nemo,
        title='Tidal Boundary Conditions for Northern Boundary',
        notebook_name='johnstone_strait_tides',
        nc_filepath='../../../nemo-forcing/open_boundaries/north/SalishSea2_North_tide_'+constituent+'_grid_'+tidevar+'.nc',
        comment='Tidal current and amplitude data from Thomson & Huggett 1980')

    # dimensions (only need x and y, don't need depth or time_counter)
    nemo.createDimension('xb', lengthi)
    nemo.createDimension('yb', 1)

    # variables
    # nbidta, ndjdta, ndrdta
    nbidta = nemo.createVariable('nbidta', 'int32' , ('yb','xb'))
    nbidta.long_name = 'i grid position'
    nbidta.units = 1
    nbjdta = nemo.createVariable('nbjdta', 'int32' , ('yb','xb'))
    nbjdta.long_name = 'j grid position'
    nbjdta.units = 1
    nbrdta = nemo.createVariable('nbrdta', 'int32' , ('yb','xb'))
    nbrdta.long_name = 'position from boundary'
    nbrdta.units = 1
    print (nbidta.shape)
    # add in the counter around the boundary (taken from Susan's code in Prepare Tide Files)
    xb = nemo.createVariable('xb', 'int32', ('xb',),zlib=True)
    xb.units = 'non dim'
    xb.long_name = 'counter around boundary'
    yb = nemo.createVariable('yb', 'int32', ('yb',),zlib=True)
    yb.units = 'non dim'
    yb.long_name = 'counter along boundary'
    yb[0] = 897
    xb[:] = np.arange(starti,endi)

    # values
    # nbidta, nbjdta
    nbidta[:] = np.arange(starti,endi)
    nbjdta[:] = 897
    nbrdta[:] = 1

    if tidevar=='T':
        z1 = nemo.createVariable('z1','float32',('yb','xb'),zlib=True)
        z1.units = 'm'
        z1.long_name = 'tidal elevation: cosine'
        z2 = nemo.createVariable('z2','float32',('yb','xb'),zlib=True)
        z2.units = 'm'
        z2.long_name = 'tidal elevation: sine'
        z1[0,:] = np.array([Z1]*lengthi)
        z2[0,:] = np.array([Z2]*lengthi)

    if tidevar=='U':
        u1 = nemo.createVariable('u1','float32',('yb','xb'),zlib=True)
        u1.units = 'm'
        u1.long_name = 'tidal x-velocity: cosine'
        u2 = nemo.createVariable('u2','float32',('yb','xb'),zlib=True)
        u2.units = 'm'
        u2.long_name = 'tidal x-velocity: sine'
        u1[0,0:lengthi] = Z1[:,0]
        u2[0,0:lengthi] = Z2[:,0]

    if tidevar=='V':
        v1 = nemo.createVariable('v1','float32',('yb','xb'),zlib=True)
        v1.units = 'm'
        v1.long_name = 'tidal y-velocity: cosine'
        v2 = nemo.createVariable('v2','float32',('yb','xb'),zlib=True)
        v2.units = 'm'
        v2.long_name = 'tidal y-velocity: sine'
        v1[0,0:lengthi] = Z1[:,0]
        v2[0,0:lengthi] = Z2[:,0]

    nc_tools.check_dataset_attrs(nemo)
    nemo.close()

def create_northern_tides_contd(Z1,Z2,tidevar,constituent,code, name='SalishSea2'):
    import netCDF4 as NC
    import numpy as np
    from salishsea_tools import nc_tools

    nemo = NC.Dataset(name+'_'+code+'_North_tide_'+constituent+'_grid_'+tidevar+'.nc', 'w', zlib=True)

    #start and end points
    starti = 32
    endi = 62
    lengthi = endi-starti

    # dataset attributes
    nc_tools.init_dataset_attrs(
        nemo,
        title='Tidal Boundary Conditions for Northern Boundary',
        notebook_name='johnstone_tides_contd',
        nc_filepath='../../../NEMO-forcing/open_boundaries/north/tides/SalishSea2_North_tide_'+constituent+'_grid_'+tidevar+'.nc',
        comment='Tidal current and amplitude data scaled based on differences between K1/M2 and North observations and webtide.')

    # dimensions (only need x and y, don't need depth or time_counter)
    nemo.createDimension('xb', lengthi)
    nemo.createDimension('yb', 1)

    # variables
    # nbidta, ndjdta, ndrdta
    nbidta = nemo.createVariable('nbidta', 'int32' , ('yb','xb'))
    nbidta.long_name = 'i grid position'
    nbidta.units = 1
    nbjdta = nemo.createVariable('nbjdta', 'int32' , ('yb','xb'))
    nbjdta.long_name = 'j grid position'
    nbjdta.units = 1
    nbrdta = nemo.createVariable('nbrdta', 'int32' , ('yb','xb'))
    nbrdta.long_name = 'position from boundary'
    nbrdta.units = 1
    print (nbidta.shape)
    # add in the counter around the boundary (taken from Susan's code in Prepare Tide Files)
    xb = nemo.createVariable('xb', 'int32', ('xb',),zlib=True)
    xb.units = 'non dim'
    xb.long_name = 'counter around boundary'
    yb = nemo.createVariable('yb', 'int32', ('yb',),zlib=True)
    yb.units = 'non dim'
    yb.long_name = 'counter along boundary'
    yb[0] = 897
    xb[:] = np.arange(starti,endi)

    # values
    # nbidta, nbjdta
    nbidta[:] = np.arange(starti,endi)
    nbjdta[:] = 897
    nbrdta[:] = 1

    if tidevar=='T':
        z1 = nemo.createVariable('z1','float32',('yb','xb'),zlib=True)
        z1.units = 'm'
        z1.long_name = 'tidal elevation: cosine'
        z2 = nemo.createVariable('z2','float32',('yb','xb'),zlib=True)
        z2.units = 'm'
        z2.long_name = 'tidal elevation: sine'
        z1[0,:] = np.array([Z1]*lengthi)
        z2[0,:] = np.array([Z2]*lengthi)

    if tidevar=='U':
        u1 = nemo.createVariable('u1','float32',('yb','xb'),zlib=True)
        u1.units = 'm'
        u1.long_name = 'tidal x-velocity: cosine'
        u2 = nemo.createVariable('u2','float32',('yb','xb'),zlib=True)
        u2.units = 'm'
        u2.long_name = 'tidal x-velocity: sine'
        u1[0,0:lengthi] = Z1[:,0]
        u2[0,0:lengthi] = Z2[:,0]

    if tidevar=='V':
        v1 = nemo.createVariable('v1','float32',('yb','xb'),zlib=True)
        v1.units = 'm'
        v1.long_name = 'tidal y-velocity: cosine'
        v2 = nemo.createVariable('v2','float32',('yb','xb'),zlib=True)
        v2.units = 'm'
        v2.long_name = 'tidal y-velocity: sine'
        v1[0,0:lengthi] = Z1[:,0]
        v2[0,0:lengthi] = Z2[:,0]

    nc_tools.check_dataset_attrs(nemo)
    nemo.close()









