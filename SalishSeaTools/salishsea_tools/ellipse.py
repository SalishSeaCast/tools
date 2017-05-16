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

"""A collection of tools for dealing with tidal ellipse calculations."""

import numpy as np
import netCDF4 as nc
from salishsea_tools import (tidetools)
from nowcast import analyze
from nowcast.figures import research_VENUS


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


def ellipse_files_nowcast(to, tf, iss, jss, path, depthrange='None',
                          period='1h', station='None'):
    """ This function loads all the data between the start and the end date
    that contains in the netCDF4 nowcast files in the
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
    :type depthrange: float, string or list.

    :arg period: period of the results files
    :type period: string - '1h' for hourly results or '15m' for 15 minute

    :arg station: station for analysis
    :type station: string 'None' if not applicable. 'ddl', 'east' or 'central'

    :returns: u, v, time, dep.
    """

    # The unstaggering in prepare_vel.py requiers an extra i and j, we add one
    # on here to maintain the area, or point chosen.
    jss = np.append(jss[0]-1, jss)
    iss = np.append(iss[0]-1, iss)

    # Makes a list of the filenames that follow the criteria in the indicated
    # path between the start and end dates.
    if period == '15m':
        files = analyze.get_filenames_15(to, tf, station, path)
        filesu = files
        filesv = files
    else:
        filesu = analyze.get_filenames(to, tf, period, 'grid_U', path)
        filesv = analyze.get_filenames(to, tf, period, 'grid_V', path)

    # Set up depth array and depth range
    depth = nc.Dataset(filesu[-1]).variables['depthu'][:]

    # Case one: for a single depth.
    if type(depthrange) == float or type(depthrange) == int:
        k = np.where(depth <= depthrange)[0][-1]
        dep = depth[k]
    # Case two: for a specific range of depths
    elif type(depthrange) == list:
        k = np.where(np.logical_and(
            depth > depthrange[0],
            depth < depthrange[1]))[0]
        dep = depth[k]
    # Case three: For the whole depth range 0 to 441m.
    else:
        k = depthrange
        dep = depth

    # Load the files
    u, time = analyze.combine_files(filesu, 'vozocrtx', k, jss, iss)
    v, time = analyze.combine_files(filesv, 'vomecrty', k,  jss, iss)

    # For the nowcast the reftime is always Sep10th 2014. Set time of area we
    # are looking at relative to this time.
    reftime = tidetools.CorrTides['reftime']
    time = tidetools.convert_to_hours(time, reftime=reftime)

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
    if depav:
        u_u = analyze.depth_average(u_u, depth, 1)
        v_v = analyze.depth_average(v_v, depth, 1)
    return u_u, v_v


def get_params(u, v, time, nconst, tidecorr=tidetools.CorrTides):
    """Calculates tidal ellipse parameters from the u and v time series.
    Maintains the shape of the velocities enters only loosing the time
    dimensions.

    :arg u: One of the orthogonal tidal current velocities. Must be already
        prepared for the analysis.
    :type u:  :py:class:'np.ndarray'

    :arg v: One of the orthogonal tidal current velocities. Must be already
        prepared for the analysis.
    :type v:  :py:class:'np.ndarray'

    :arg time: Time over which the velocities were taken; in hours.
    :type time: :py:class:'np.ndarray'

    :arg nconst: The amount of tidal constituents used for the analysis. They
        added in pairs and by order of importance, M2, K1, S2, O1, N2, P1, K2,
        Q1.
    :type nconst: int

    :arg tidecorr: Tidal corrections in aplitude and phase. Default is the
        nowcast values.
    :type tidecorr: dictionary

    :returns: params a dictionary containing the tidal ellipse parameter of the
        chosen constituents
    """
    params = {}
    # Running fittit to get the amplitude and phase of the velcity time series.
    uapparam = tidetools.fittit(u, time, nconst)
    vapparam = tidetools.fittit(v, time, nconst)

    # Cycling through the constituents in the ap-parameter dict given by fittit
    for const in uapparam:
        # Applying tidal corrections to u and v phase parameter
        uapparam[const]['phase'] = (
            uapparam[const]['phase'] + tidecorr[const]['uvt'])
        vapparam[const]['phase'] = (
            vapparam[const]['phase'] + tidecorr[const]['uvt'])

        # Applying tidal corrections to u and v amplitude parameter
        uapparam[const]['amp'] = uapparam[const]['amp'] / tidecorr[const]['ft']
        vapparam[const]['amp'] = vapparam[const]['amp'] / tidecorr[const]['ft']

        # Converting from u/v amplitude and phase to ellipe parameters. Inputs
        # are the amplitude and phase of both velocities, runs once for each
        # contituent
        CX, SX, CY, SY, ap, am, ep, em, maj, mi, the, pha = ellipse_params(
            uapparam[const]['amp'],
            uapparam[const]['phase'],
            vapparam[const]['amp'],
            vapparam[const]['phase'])
        # Filling the dictionary with ep-parameters given by ellipse_param.
        # Each constituent will be a different key.

        params[const] = {
            'Semi-Major Axis': maj,
            'Semi-Minor Axis': mi,
            'Inclination': the,
            'Phase': pha
            }

    return params


def get_params_nowcast_15(
        to, tf,
        station,
        path, nconst,
        depthrange='None',
        depav=False, tidecorr=tidetools.CorrTides):
    """ This function loads all the data between the start and the end date that
    contains quater houlry velocities in the netCDF4 nowcast files in the
    depth range. Then masks, rotates and unstaggers the time series. The
    unstaggering causes the shapes of the returned arrays to be 1 less than
    those of the input arrays in the y and x dimensions. Finally it calculates
    tidal ellipse parameters from the u and v time series. Maintains the shape
    of the velocities enters only loosing the time dimensions.

    :arg to: The beginning of the date range of interest
    :type to: datetime object

    :arg tf: The end of the date range of interest
    :type tf: datetime object

    :arg station: station name for the quater-hourly data
    :type station: string (East or Central)

    :arg path: Defines the path used(eg. nowcast)
    :type path: string

    :arg depthrange: Depth values of interest in meters as a float for a single
        depth or a list for a range. A float will find the closest depth that
        is <= the value given. Default is 'None' for the whole water column
        (0-441m).
    :type depav: float, string or list.

    :arg depav: True will depth average over the whole depth profile given.
        Default is False.
    :type depav: boolean

    :arg depth: depth vector corresponding to the depth of the velocities, only
         requiered if depav=True.
    :type depth: :py:class:'np.ndarray' or string

    :returns: params, dep
    params is dictionary object of the ellipse parameters for each constituent
    dep is the depths of the ellipse paramters
    """

    u, v, time, dep = ellipse_files_nowcast(
        to, tf,
        [1], [1],
        path,
        depthrange=depthrange, period='15m', station=station)
    u_u, v_v = prepare_vel(u, v, depav=depav, depth=dep)
    params = get_params(u_u, v_v, time, nconst, tidecorr=tidecorr)

    return params, dep


def get_params_nowcast(
        to, tf,
        i, j,
        path, nconst,
        depthrange='None',
        depav=False, tidecorr=tidetools.CorrTides):
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
    :type depav: boolean

    :arg depth: depth vector corresponding to the depth of the velocities, only
         requiered if depav=True.
    :type depth: :py:class:'np.ndarray' or string

    :returns: params, dep
    params is dictionary object of the ellipse parameters for each constituent
    dep is the depths of the ellipse paramters
    """

    u, v, time, dep = ellipse_files_nowcast(
        to, tf,
        i, j,
        path,
        depthrange=depthrange)
    u_u, v_v = prepare_vel(u, v, depav=depav, depth=dep)
    params = get_params(u_u, v_v, time, nconst, tidecorr=tidecorr)

    return params, dep
