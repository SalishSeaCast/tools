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

"""A collection of tools for dealing with tidal ellipse calculations."""

import datetime
import matplotlib.pylab as plt
from matplotlib.patches import Ellipse
import numpy as np
import csv
from dateutil import tz
import angles

import netCDF4 as nc
from salishsea_tools import (viz_tools, tidetools)
from salishsea_tools.nowcast import (analyze, research_VENUS)

# Tide correction for amplitude and phase set to September 10th 2014 by nowcast
# Values for there and other constituents can be found in:
# /data/dlatorne/MEOPAR/SalishSea/nowcast/08jul15/ocean.output
CorrTides = {
    'reftime': datetime.datetime(2014, 9, 10, tzinfo=tz.tzutc()),
    'K1': {
        'freq': 15.041069000,
        'ft': 0.891751,
        'uvt': 262.636797},
    'O1': {
        'freq': 13.943036,
        'ft': 0.822543,
        'uvt': 81.472430},
    'Q1': {
        'freq': 13.398661,
        'ft': 0.822543,
        'uvt': 46.278236},
    'P1': {
        'freq': 14.958932,
        'ft': 1.0000000,
        'uvt': 101.042160},
    'M2': {
        'freq': 28.984106,
        'ft': 1.035390,
        'uvt': 346.114490},
    'N2': {
        'freq': 28.439730,
        'ft': 1.035390,
        'uvt': 310.920296},
    'S2': {
        'freq': 30.000002,
        'ft': 1.0000000,
        'uvt': 0.000000},
    'K2': {
        'freq': 30.082138,
        'ft': 0.763545,
        'uvt': 344.740346}
    }


def double(x, M2amp, M2pha, K1amp, K1pha, mean):
    """Function for the fit, assuming only M2 and K2 tidal constituents.

    :arg x:
    :type x:

    :arg M2amp: Tidal amplitude of the M2 constituent
    :type M2amp:

    :arg M2pha: Phase lag of M2 constituent
    :type M2pha:

    :arg K1amp: Tidal amplitude of the K1 constituent
    :type K1amp:

    :arg K1pha: Phase lag of K1 constituent
    :type K1pha:

    :returns:(mean + M2amp*np.cos(M2FREQ*x-M2pha*np.pi/180.)
        +K1amp*np.cos(K1FREQ*x-K1pha*np.pi/180.))
    """
    return(
        mean + M2amp * np.cos(tidetools.M2FREQ * x - M2pha * np.pi / 180.) +
        K1amp * np.cos(tidetools.K1FREQ * x - K1pha * np.pi / 180))


def convention_pha_amp(fitted_amp, fitted_pha):
    """ This function takes the fitted parameters given for phase and
         amplitude of the tidal ellipse and returns them following the
         tidal parameter convention; amplitude is positive and phase
         is between -180 and +180 degrees.

    :arg fitted_amp: The amplitude given by the fitting function.
    :type fitted_amp: float

    :arg fitted_pha: The phase given by the fitting function.
    :type fitted_pha: float

    :return fitted_amp, fitted_pha: The fitted parameters following the
        conventions.
    """

    if fitted_amp < 0:
        fitted_amp = -fitted_amp
        fitted_pha = fitted_pha + 180
    fitted_pha = angles.normalize(fitted_pha, -180, 180)

    return fitted_amp, fitted_pha


def fittit(uaus, time):
    """Function to find tidal components from a tidal current component
        over the whole area given. Can be done over depth, or an area.
        Time must be in axis one, depth in axis two if applicable then the
        x and y if an area.
        Must perform twice, once for each tidal current vector
        in order to complete the analysis.
        In order to calculate the tidal components of an area at a single
        depth the velocity vector must only have 3 dimensions. For a depth
        profile it must only have 2 dimensions
        ***[time, depth, x, y]

    :arg uaus: One of the orthogonal tidal current velocities.
    :type uaus:  :py:class:'np.ndarray' or float

    :arg time: Time over which the velocitie were being taken in seconds.
    :type time: :py:class:'np.ndarray'

    :returns M2amp, M2pha, K1amp, K1pha:
        The amplitude and phase lag of each tidal component (M2 and K1)
        of a single tidal velocity vector.

    """
    # Case 1: a time series of velocities with depth at a single location.
    if uaus.ndim == 2:
        # The parameters are the same shape as the velocities without the time
        # dimension.
        thesize = uaus.shape[1]
        M2amp = np.zeros(thesize)
        M2pha = np.zeros(thesize)
        K1amp = np.zeros(thesize)
        K1pha = np.zeros(thesize)

        # Calculates the parameters for one depth and one location at a time
        # from its time series
        for dep in np.arange(0, len(uaus[1])):
            if uaus[:, dep].any() != 0:
                fitted, cov = tidetools.curve_fit(
                    tidetools.double,
                    time[:],
                    uaus[:, dep])
                # Rotating to have a positive amplitude and a phase between
                # [-180, 180]
                fitted[0], fitted[1] = tidetools.convention_pha_amp(
                    fitted[0],
                    fitted[1])
                fitted[2], fitted[3] = tidetools.convention_pha_amp(
                    fitted[2],
                    fitted[3])
                M2amp[dep] = fitted[0]
                M2pha[dep] = fitted[1]
                K1amp[dep] = fitted[2]
                K1pha[dep] = fitted[3]

    # Case 2 : a time series of an area of velocities at a single depth
    elif uaus.ndim == 3:
        thesize = (uaus.shape[1], uaus.shape[2])
        M2amp = np.zeros(thesize)
        M2pha = np.zeros(thesize)
        K1amp = np.zeros(thesize)
        K1pha = np.zeros(thesize)

        for i in np.arange(0, uaus.shape[1]):
            for j in np.arange(0, uaus.shape[2]):
                if uaus[:, i, j].any() != 0.:
                    fitted, cov = tidetools.curve_fit(
                        tidetools.double,
                        time[:],
                        uaus[:, i, j])
                    fitted[0], fitted[1] = tidetools.convention_pha_amp(
                        fitted[0],
                        fitted[1])
                    fitted[2], fitted[3] = tidetools.convention_pha_amp(
                        fitted[2],
                        fitted[3])
                    M2amp[i, j] = fitted[0]
                    M2pha[i, j] = fitted[1]
                    K1amp[i, j] = fitted[2]
                    K1pha[i, j] = fitted[3]

    # Case 3: a time series of an area of velocities with depth
    elif uaus.ndim == 4:
        thesize = (uaus.shape[1], uaus.shape[2], uaus.shape[3])
        M2amp = np.zeros(thesize)
        M2pha = np.zeros(thesize)
        K1amp = np.zeros(thesize)
        K1pha = np.zeros(thesize)

        for dep in np.arange(0, uaus.shape[1]):
            for i in np.arange(0, uaus.shape[2]):
                for j in np.arange(0, uaus.shape[3]):
                    if uaus[:, dep, i, j].any() != 0.:
                        fitted, cov = tidetools.curve_fit(
                            tidetools.double,
                            time[:],
                            uaus[:, dep, i, j])
                        fitted[0], fitted[1] = tidetools.convention_pha_amp(
                            fitted[0],
                            fitted[1])
                        fitted[2], fitted[3] = tidetools.convention_pha_amp(
                            fitted[2],
                            fitted[3])
                        M2amp[dep, i, j] = fitted[0]
                        M2pha[dep, i, j] = fitted[1]
                        K1amp[dep, i, j] = fitted[2]
                        K1pha[dep, i, j] = fitted[3]

    # Case 4: a time series of a single location with a single depth.
    else:
        M2amp = 0
        M2pha = 0
        K1amp = 0
        K1pha = 0

        if uaus[:].any() != 0.:
            fitted, cov = tidetools.curve_fit(
                tidetools.double,
                time[:],
                uaus[:])
            fitted[0], fitted[1] = tidetools.convention_pha_amp(
                fitted[0],
                fitted[1])
            fitted[2], fitted[3] = tidetools.convention_pha_amp(
                fitted[2],
                fitted[3])
            M2amp = fitted[0]
            M2pha = fitted[1]
            K1amp = fitted[2]
            K1pha = fitted[3]
    return M2amp, M2pha, K1amp, K1pha


def ellipse_params(uamp, upha, vamp, vpha):
    """Calculates ellipse parameters based on the amplitude
        and phase for a tidal constituent.

    :arg uamp: u fitted amplitude of the chosen constituent
    :type uamp: :py:class:`numpy.ndarray`

    :arg upha: u fitted phase of the chosen constituent
    :type upha: :py:class:`numpy.ndarray`

    :arg vamp: v fitted amplitude of the chosen constituent
    :type vamp: :py:class:`numpy.ndarray`

    :arg vpha: v fitted phase of the chosen constituent
    :type vpha: :py:class:`numpy.ndarray`

    :returns CX, SX, CY, SY, ap, am, ep, em, major, minor, theta, phase
        The positively and negatively rotating amplitude and phase.
        As well as the major and minor axis and the axis tilt.
   """

    CX = uamp*np.cos(np.pi*upha/180.)
    SX = uamp*np.sin(np.pi*upha/180.)
    CY = vamp*np.cos(np.pi*vpha/180.)
    SY = vamp*np.sin(np.pi*vpha/180.)
    ap = np.sqrt((CX+SY)**2+(CY-SX)**2)/2.
    am = np.sqrt((CX-SY)**2+(CY+SX)**2)/2.
    ep = np.arctan2(CY-SX, CX+SY)
    em = np.arctan2(CY+SX, CX-SY)
    major = ap+am
    minor = ap-am
    theta = (ep+em)/2.*180./np.pi
    phase = (em-ep)/2.*180./np.pi

    # Make angles be between [0,360]
    phase = (phase+360) % 360
    theta = (theta+360) % 360

    ind = np.divide(theta, 180)
    k = np.floor(ind)
    theta = theta - k*180
    phase = phase + k*180
    phase = (phase+360) % 360

    return CX, SX, CY, SY, ap, am, ep, em, major, minor, theta, phase


def ellipse_files_nowcast(to, tf, iss, jss, path, depthrange='None'):
    """ This function loads all the data between the start and the end date
    that contains hourly velocities in the netCDF4 nowcast files in the
    specified depth range. This will make an area with all the indices
    indicated, the area must be continuous for unstaggering.

    :arg to: The beginning of the date range of interest
    :type to: datetime object

    :arg tf: The end of the date range of interest
    :type tf: datetime object

    :arg iss: x index.
    :type i: list or numpy.array

    :arg jss: y index.
    :type j: list or numpy.array

    :arg path: Defines the path used(eg. nowcast)
    :type path: string

    :arg depthrange: Depth values of interest in meters as a float for a single
        depth or a list for a range. A float will find the closest depth that
        is <= the value given. Default is 'None' for the whole water column
        (0-441m).
    :type depav: float, string or list.

    :returns: u, v, time, dep.
    """

    # The unstaggering in prepare_vel.py requiers an extra i and j, we add one
    # on here to maintain the area, or point chosen.
    jss = np.append(jss[0]-1, jss)
    iss = np.append(iss[0]-1, iss)

    # Makes a list of the filenames that follow the criteria in the indicated
    # path between the start and end dates.
    filesu = analyze.get_filenames(to, tf, '1h', 'grid_U', path)
    filesv = analyze.get_filenames(to, tf, '1h', 'grid_V', path)

    # Set up depth array and depth range
    depth = nc.Dataset(filesu[-1]).variables['depthu'][:]

    # Case one: for a single depth.
    if type(depthrange) == float or type(depthrange) == int:
        k = np.where(depth <= depthrange)[0][-1]
        u, time = analyze.combine_files(filesu, 'vozocrtx', k, jss, iss)
        v, time = analyze.combine_files(filesv, 'vomecrty', k,  jss, iss)
        dep = depth[k]

    # Case two: for a specific range of depths
    elif type(depthrange) == list:
        k = np.where(np.logical_and(
            depth > depthrange[0],
            depth < depthrange[1]))[0]
        dep = depth[k]
        u, time = analyze.combine_files(filesu, 'vozocrtx', k, jss, iss)
        v, time = analyze.combine_files(filesv, 'vomecrty', k,  jss, iss)

    # Case three: For the whole depth range 0 to 441m.
    else:
        u, time = analyze.combine_files(
            filesu, 'vozocrtx', depthrange, jss, iss)
        v, time = analyze.combine_files(
            filesv, 'vomecrty', depthrange, jss, iss)
        dep = depth

    # For the nowcast the reftime is always Sep10th 2014. Set time of area we
    # are looking at relative to this time.
    reftime = datetime.datetime(2014, 9, 10, tzinfo=tz.tzutc())
    time = tidetools.convert_to_seconds(time, reftime=reftime)

    return u, v, time, dep


def prepare_vel(u, v, depav=False, depth='None'):
    """ Preparing the time series of the orthogonal pair of velocities to get tidal
    ellipse parameters. This function masks, rotates and unstaggers the time
    series. The depth averaging does not work over masked values.

    :arg u: One of the orthogonal components of the time series of tidal
        current velocities.
    :type u:  :py:class:'np.ndarray'

    :arg v: One of the orthogonal components of the time series of tidal
        current velocities.
    :type v:  :py:class:'np.ndarray'

    :arg depav: True will depth average over the whole depth profile given.
        Default is False.
    :type dep: boolean

    :arg depth: depth vector corresponding to the depth of the velocities, only
        requiered if depav=True.
    :type depth: :py:class:'np.ndarray' or string
    """
    # Masks land values
    u_0 = np.ma.masked_values(u, 0)
    v_0 = np.ma.masked_values(v, 0)

    # Unstaggers velocities. Will loose one x and one y dimension due to
    # unstaggering.
    u_u, v_v = research_VENUS.unstag_rot(u_0, v_0)

    # Depth averaging over all the depth values given if set to True.
    if depav == True:
        u_u = analyze.depth_average(u_u, depth, 1)
        v_v = analyze.depth_average(v_v, depth, 1)
    return u_u, v_v


def get_params(u, v, time, tidecorr=CorrTides):
    """Calculates tidal ellipse parameters from the u and v time series.
    Maintains the shape of the velocities enters only loosing the time
    dimensions.

    :arg u: One of the orthogonal tidal current velocities. Must be already
        prepared for the analysis.
    :type u:  :py:class:'np.ndarray'

    :arg v: One of the orthogonal tidal current velocities. Must be already
        prepared for the analysis.
    :type v:  :py:class:'np.ndarray'

    :arg time: Time over which the velocities were taken; in seconds.
    :type time: :py:class:'np.ndarray'

    :arg tidecorr: Tidal corrections in aplitude and phase. Default is the
        nowcast values.
    :type tidecorr: dictionary

    :returns: params a dictionary containing the tidal ellipse parameter of the
        chosen constituents
    """

    # Running fittit to get the amplitude and phase of the velcity time series.
    uM2amp, uM2pha, uK1amp, uK1pha = fittit(u, time)
    vM2amp, vM2pha, vK1amp, vK1pha = fittit(v, time)

    # Tide corrections from a dictionary
    uM2pha = uM2pha + tidecorr['M2']['uvt']
    uK1pha = uK1pha + tidecorr['K1']['uvt']
    vM2pha = vM2pha + tidecorr['M2']['uvt']
    vK1pha = vK1pha + tidecorr['K1']['uvt']

    uM2amp = uM2amp * tidecorr['M2']['ft']
    uK1amp = uK1amp * tidecorr['K1']['ft']
    vM2amp = vM2amp * tidecorr['M2']['ft']
    vK1amp = vK1amp * tidecorr['K1']['ft']

    # Converting from u/v amplitude and phase to ellipe parameters.
    CX, SX, CY, SY, ap, am, ep, em, maj, mi, the, pha = tidetools.ellipse_params(
        uM2amp, uM2pha, vM2amp, vM2pha)

    CXk, SXk, CYk, SYk, apk, amk, epk, emk, majk, mik, thek, phak = tidetools.ellipse_params(
        uK1amp, uK1pha, vK1amp, vK1pha)

    # Saving all the useful parameters in a matrix. The shape of the parameters
    # is based on the u and v variables but averaged over time.

    params = {
        'M2': {
            'Semi-Major Axis': maj,
            'Semi-Minor Axis': mi,
            'Inclination': the,
            'Phase': pha},
        'K1': {
            'Semi-Major Axis': majk,
            'Semi-Minor Axis': mik,
            'Inclination': thek,
            'Phase': phak}}

    return params


def get_params_nowcast(
        to, tf,
        i, j, path,
        depthrange='None',
        depav=False, tidecorr=CorrTides):
    """ This function loads all the data between the start and the end date that
    contains hourly velocities in the netCDF4 nowcast files in the specified
    depth range. Then masks, rotates and unstaggers the time series. The
    unstaggering causes the shapes of the returned arrays to be 1 less than
    those of the input arrays in the y and x dimensions. Finally it calculates
    tidal ellipse parameters from the u and v time series. Maintains the shape
    of the velocities enters only loosing the time dimensions.

    :arg to: The beginning of the date range of interest
    :type to: datetime object

    :arg tf: The end of the date range of interest
    :type tf: datetime object

    :arg i: x index, must have at least 2 values for unstaggering, will loose
        the first i during the unstaggering in prepare_vel.
    :type i: float or list

    :arg j: y index, must have at least 2 values for unstaggering, will loose
        the first j during the unstaggering in prepare_vel.
    :type j: float or list

    :arg path: Defines the path used(eg. nowcast)
    :type path: string

    :arg depthrange: Depth values of interest in meters as a float for a single
        depth or a list for a range. A float will find the closest depth that
        is <= the value given. Default is 'None' for the whole water column
        (0-441m).
    :type depav: float, string or list.

    :arg depav: True will depth average over the whole depth profile given.
        Default is False.
    :type dep: boolean

    :arg depth: depth vector corresponding to the depth of the velocities, only
         requiered if depav=True.
    :type depth: :py:class:'np.ndarray' or string

    :returns: params, a numpy array containting [M2 semi-major, M2 semi-minor,
         M2 inclication, M2 phase, K1 semi-major, K1 semi-minor, K1
         inclication,K1 phase]
    """

    u, v, time, dep = ellipse_files_nowcast(
        to, tf,
        i, j,
        path,
        depthrange=depthrange)
    u_u, v_v = prepare_vel(u, v, depav=depav, depth=dep)
    params = get_params(u_u, v_v, time, tidecorr=tidecorr)

    return params, dep
