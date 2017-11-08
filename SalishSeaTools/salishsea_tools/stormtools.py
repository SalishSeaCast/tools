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

"""A collection of tools for storm surge results from the Salish Sea Model.
"""
from __future__ import division

import csv
import datetime
from io import BytesIO
from xml.etree import cElementTree as ElementTree

import arrow
from dateutil import tz
import netCDF4 as NC
import numpy as np
import pandas as pd
import requests

from salishsea_tools import tidetools
from salishsea_tools.places import PLACES


def storm_surge_risk_level(site_name, max_ssh, ttide):
    """Calculate the storm surge risk level for :kbd:`site_name`,
    a tide gauge station name.

    Thresholds are:

    * Highest predicted tide
    * Half way between highest predicted tide and highest historical
      water level
    * Highest historical water level

    Threshold levels are obtained from
    :py:data:`salishsea_tools.places.PLACES` dict.

    :arg str site_name` Name of a tide gauge station at which to
                        calculate the storm surge risk.

    :arg float max_ssh: The maximum sea surface height predicted for
                        :kbd:`site_name`.

    :arg ttide: Tidal predictions from ttide.
    :type ttide: :py:class:`pandas.DataFrame`

    :returns: :py:obj:`None` for no storm surge risk,
              :kbd:`moderate risk` for water level between max tide level
              and the half-way threshold,
              and :kbd:`extreme risk` for water level above the half-way
              threshold
    """
    try:
        max_tide_ssh = max(ttide.pred_all) + PLACES[site_name]['mean sea lvl']
        max_historic_ssh = PLACES[site_name]['hist max sea lvl']
    except KeyError as e:
        raise KeyError(
            'place name or info key not found in '
            'salishsea_tools.places.PLACES: {}'.format(e))
    extreme_threshold = max_tide_ssh + (max_historic_ssh - max_tide_ssh) / 2
    risk_level = (
        None if max_ssh < max_tide_ssh
        else 'extreme risk' if max_ssh > extreme_threshold
        else 'moderate risk')
    return risk_level


def convert_date_seconds(times, start):
    """
    This function converts model output time in seconds to datetime objects.
    Note: Doug has a better version of this in nc_tools.timestamp

    :arg times: array of seconds since the start date of a simulation.
                From time_counter in model output.
    :type times: int

    :arg start: string containing the start date of the simulation in
                format '01-Nov-2006'
    :type start: str

    :arg diff: string indicating the time step in the times data
               E.g. months, seconds, days
    :type diff: str

    :returns: array of datetime objects representing the time of model outputs.
    """
    arr_times = []
    for ii in range(0, len(times)):
        arr_start = arrow.Arrow.strptime(start, '%d-%b-%Y')
        arr_new = arr_start.replace(seconds=times[ii])
        arr_times.append(arr_new.datetime)

    return arr_times


def convert_date_hours(times, start):
    """
    This function converts model output time in hours to datetime objects.

    :arg times: array of hours since the start date of a simulation.
                From time_counter in model output.
    :type times: int

    :arg start: string containing the start date of the simulation in
                format '01-Nov-2006'
    :type start: str

    :returns: array of datetime objects representing the time of model outputs.
    """

    arr_times = []
    for ii in range(0, len(times)):
        arr_start = arrow.Arrow.strptime(start, '%d-%b-%Y')
        arr_new = arr_start.replace(hours=times[ii])
        arr_times.append(arr_new.datetime)

    return arr_times


def get_CGRF_weather(start, end, grid):
    """
    Returns the CGRF weather between the dates start and end at the
    grid point defined in grid.

    :arg start: string containing the start date of the CGRF collection in
                format '01-Nov-2006'
    :type start: str

    :arg start: string containing the end date of the CGRF collection in
                format '01-Nov-2006'
    :type start: str

    :arg grid: array of the CGRF grid coordinates for the point of interest
               eg. [244,245]
    :arg type: arr of ints

    :returns: windspeed, winddir pressure and time array from CGRF data for
              the times indicated.
              windspeed is in m/s
              winddir direction wind is blowing to in degrees measured
              counterclockwise from East.
              pressure is in Pa.

    """
    u10 = []
    v10 = []
    pres = []
    time = []
    st_ar = arrow.Arrow.strptime(start, '%d-%b-%Y')
    end_ar = arrow.Arrow.strptime(end, '%d-%b-%Y')

    CGRF_path = '/ocean/dlatorne/MEOPAR/CGRF/NEMO-atmos/'

    for r in arrow.Arrow.range('day', st_ar, end_ar):
        mstr = "{0:02d}".format(r.month)
        dstr = "{0:02d}".format(r.day)

        # u
        strU = 'u10_y' + str(r.year) + 'm' + mstr + 'd' + dstr + '.nc'
        fU = NC.Dataset(CGRF_path+strU)
        var = fU.variables['u_wind'][:, grid[0], grid[1]]
        u10.extend(var[:])

        # time
        tim = fU.variables['time_counter']
        time.extend(tim[:] + (r.day-st_ar.day)*24)
        times = convert_date_hours(time, start)

        # v
        strV = 'v10_y' + str(r.year) + 'm' + mstr + 'd' + dstr + '.nc'
        fV = NC.Dataset(CGRF_path+strV)
        var = fV.variables['v_wind'][:, grid[0], grid[1]]
        v10.extend(var[:])

        # pressure
        strP = 'slp_corr_y' + str(r.year) + 'm' + mstr + 'd' + dstr + '.nc'
        fP = NC.Dataset(CGRF_path+strP)
        var = fP.variables['atmpres'][:, grid[0], grid[1]]
        pres.extend(var[:])

        u10s = np.array(u10)
        v10s = np.array(v10)
        press = np.array(pres)
        windspeed = np.sqrt(u10s**2+v10s**2)

    winddir = np.arctan2(v10, u10) * 180 / np.pi
    winddir = winddir + 360 * (winddir < 0)

    return windspeed, winddir, press, times


def combine_data(data_list):
    """
    This function combines output from a list of netcdf files into a
    dict objects of model fields.
    It is used for easy handling of output from thalweg and surge stations.

    :arg data_list: dict object that contains the netcdf handles for the
                    files to be combined;
                    e.g. {'Thalweg1': f1, 'Thalweg2': f2,...}
                    where f1 = NC.Dataset('1h_Thalweg1.nc','r')
    :type data_list: dict object

    :returns: dict objects us, vs, lats, lons, sals, tmps, sshs
              with the zonal velocity, meridional velocity, latitude,
              longitude, salinity, temperature, and sea surface height
              for each station.
              The keys are the same as those in data_list.
              For example, us['Thalweg1'] contains the zonal velocity
              from the Thalweg 1 station.

    """

    us = {}
    vs = {}
    lats = {}
    lons = {}
    sals = {}
    tmps = {}
    sshs = {}
    for k in data_list:
        net = data_list.get(k)
        us[k] = net.variables['vozocrtx']
        vs[k] = net.variables['vomecrty']
        lats[k] = net.variables['nav_lat']
        lons[k] = net.variables['nav_lon']
        tmps[k] = net.variables['votemper']
        sals[k] = net.variables['vosaline']
        sshs[k] = net.variables['sossheig']
    return us, vs, lats, lons, tmps, sals, sshs


def get_variables(fU, fV, fT, timestamp, depth):
    """
    Generates masked u,v,SSH,S,T from NETCDF handles fU,fV,fT at timestamp and
    depth.

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

    :returns: masked arrays U,V,E,S,T with of zonal velocity,
     meridional velocity, sea surface height, salinity, and temperature at
     specified time and z-level.

    """
    # get u and ugrid
    u_vel = fU.variables['vozocrtx']  # u currents and grid
    U = u_vel[timestamp, depth, :, :]  # get data at specified level and time.
    # mask u so that white is plotted on land points
    mu = U == 0
    U = np.ma.array(U, mask=mu)

    # get v and v grid
    v_vel = fV.variables['vomecrty']  # v currents and grid
    V = v_vel[timestamp, depth, :, :]  # get data at specified level and time.

    # mask v so that white is plotted on land points
    mu = V == 0
    V = np.ma.array(V, mask=mu)

    # grid for T points
    eta = fT.variables['sossheig']
    E = eta[timestamp, :, :]
    mu = E == 0
    E = np.ma.array(E, mask=mu)

    sal = fT.variables['vosaline']
    S = sal[timestamp, depth, :, :]
    mu = S == 0
    S = np.ma.array(S, mask=mu)

    temp = fT.variables['votemper']
    T = temp[timestamp, depth, :, :]
    mu = T == 0
    T = np.ma.array(T, mask=mu)

    return U, V, E, S, T


def get_EC_observations(station, start_day, end_day):
    """Gather hourly Environment Canada (EC) weather observations for the
    station and dates indicated.

    The hourly EC data is stored in monthly files, so only a single month can
    be downloaded at a time.

    :arg station: Station name (no spaces). e.g. 'PointAtkinson'
    :type station: str

    :arg start_day: Start date in the format '01-Dec-2006'.
    :type start_day: str

    :arg end_day: End date in the format '01-Dec-2006'.
    :type end_day: str

    :returns: wind_speed, wind_dir, temperature, times, lat and lon:
              wind speed is in m/s
              wind_dir is direction wind is blowing to in degrees measured
              counterclockwise from East
              temperature is in Kelvin
              time is UTC
              Also returns latitude and longitude of the station.

    """
    # These ids have been identified as interesting locations in the SoG.
    # It is not necessarily a complete list.
    station_ids = {
        'PamRocks': 6817,
        'SistersIsland': 6813,
        'EntranceIsland': 29411,
        'Sandheads': 6831,
        # NOTE: YVR station name changed in 2013. Older data use 889.
        'YVR': 51442,
        'YVR_old': 889,
        'PointAtkinson': 844,
        'Victoria': 10944,
        'CampbellRiver': 145,
        # NOTE: not exactly Patricia Bay. The EC name is Victoria Hartland CS
        'PatriciaBay': 11007,
        'Esquimalt': 52
    }

    st_ar = arrow.Arrow.strptime(start_day, '%d-%b-%Y')
    end_ar = arrow.Arrow.strptime(end_day, '%d-%b-%Y')
    PST = tz.tzoffset("PST", -28800)

    wind_spd, wind_dir, temp = [], [], []
    url = 'http://climate.weather.gc.ca/climate_data/bulk_data_e.html'
    query = {
        'timeframe': 1,
        'stationID': station_ids[station],
        'format': 'xml',
        'Year': st_ar.year,
        'Month': st_ar.month,
        'Day': 1,
    }
    response = requests.get(url, params=query)
    tree = ElementTree.parse(BytesIO(response.content))
    root = tree.getroot()
    # read lat and lon
    for raw_info in root.findall('stationinformation'):
        lat = float(raw_info.find('latitude').text)
        lon = float(raw_info.find('longitude').text)
    # read data
    raw_data = root.findall('stationdata')
    times = []
    for record in raw_data:
        day = int(record.get('day'))
        hour = int(record.get('hour'))
        year = int(record.get('year'))
        month = int(record.get('month'))
        t = arrow.Arrow(year, month, day, hour, tzinfo=PST)
        selectors = (
            (day == st_ar.day - 1 and hour >= 16)
            or
            (day >= st_ar.day and day < end_ar.day)
            or
            (day == end_ar.day and hour < 16)
        )
        if selectors:
            try:
                wind_spd.append(float(record.find('windspd').text))
                t.to('utc')
                times.append(t.datetime)
            except TypeError:
                wind_spd.append(float('NaN'))
                t.to('utc')
                times.append(t.datetime)
            try:
                wind_dir.append(float(record.find('winddir').text) * 10)
            except:
                wind_dir.append(float('NaN'))
            try:
                temp.append(float(record.find('temp').text)+273)
            except:
                temp.append(float('NaN'))
    wind_spd = np.array(wind_spd) * 1000 / 3600  # km/hr to m/s
    wind_dir = -np.array(wind_dir)+270   # met. direction to cartesian angle
    with np.errstate(invalid='ignore'):
        wind_dir = wind_dir + 360 * (wind_dir < 0)
    temp = np.array(temp)
    for i in np.arange(len(times)):
        times[i] = times[i].astimezone(tz.tzutc())

    return wind_spd, wind_dir, temp, times, lat, lon


def get_SSH_forcing(boundary, date):
    """A function that returns the ssh forcing for the month of the date and
    boundary indicated.

    :arg str boundary: A string naming the boundary. e.g 'north' or 'west'

    :arg str  date: A string indicating the date of interest. e.g. '01-Dec-2006'.
                    The day needs to be the first day of the month.

    :returns: ssh_forc, time_ssh: arrays of the ssh forcing values and
              corresponding times
    """
    date_arr = arrow.Arrow.strptime(date, '%d-%b-%Y')
    year = date_arr.year
    month = date_arr.month
    month = "%02d" % (month,)
    if boundary == 'north':
        filen = 'sshNorth'
    else:
        filen = 'ssh'
    ssh_path = '/data/nsoontie/MEOPAR/NEMO-forcing/open_boundaries/' + \
               boundary + '/ssh/' + filen + '_y' + str(year) + 'm' + str(month)\
               + '.nc'
    fS = NC.Dataset(ssh_path)
    ssh_forc = fS.variables['sossheig']
    tss = fS.variables['time_counter'][:]
    l = tss.shape[0]
    t = np.linspace(0, l-1, l)  # time array
    time_ssh = convert_date_hours(t, date)

    return ssh_forc, time_ssh


def dateParserMeasured2(s):
    """
    converts string in %d-%b-%Y %H:%M:%S format Pacific time to a
    datetime object UTC time.
    """
    PST = tz.tzoffset("PST", -28800)
    # convert the string to a datetime object
    unaware = datetime.datetime.strptime(s, "%d-%b-%Y %H:%M:%S ")
    # add in the local time zone (Canada/Pacific)
    aware = unaware.replace(tzinfo=PST)
    # convert to UTC
    return aware.astimezone(tz.tzutc())


def dateParserMeasured(s):
    """
    converts string in %Y/%m/%d %H:%M format Pacific time to a
    datetime object UTC time.
    """
    PST = tz.tzoffset("PST", -28800)
    # convert the string to a datetime object
    unaware = datetime.datetime.strptime(s, "%Y/%m/%d %H:%M")
    # add in the local time zone (Canada/Pacific)
    aware = unaware.replace(tzinfo=PST)
    # convert to UTC
    return aware.astimezone(tz.tzutc())


def load_tidal_predictions(filename):
    """Load tidal prediction from a file.

    :arg str filename: The path and file name of a CSV file that contains
                       ttide tidal predictions generated by
                       :kbd:`get_ttide_8.m`.

    :returns: ttide: Tidal predictions and mean sea level,
                     the mean component from the harmonic analysis.
    :rtype: :py:class:`pandas.DataFrame`
    """
    with open(filename) as f:
        mycsv = list(csv.reader(f))
        msl = float(mycsv[1][1])
    ttide = pd.read_csv(
        filename, skiprows=3, parse_dates=[0], date_parser=dateParserMeasured2)
    ttide = ttide.rename(
        columns={
            'time ': 'time',
            ' pred_8 ': 'pred_8',
            ' pred_all ': 'pred_all',
        })
    return ttide, msl


def load_observations(start, end, location):
    """
    Loads tidal observations from the DFO website using tidetools function

    :arg start: a string representing the starting date of the observations.
    :type start: string in format %d-%b-%Y

    :arg end: a string representing the end date of the observations.
    :type end: string in format %d-%b-%Y

    :arg location: a string representing the location for observations
    :type location: a string from the following - PointAtkinson, Victoria,
                    PatriciaBay, CampbellRiver

    :returns: wlev_meas: a dict object with the water level measurements
                         reference to Chart Datum
    """
    stations = {'PointAtkinson': 7795, 'Victoria': 7120, 'PatriciaBay': 7277,
                'CampbellRiver': 8074}
    statID_PA = stations[location]
    filename = 'wlev_' + str(statID_PA) + '_' + start + '_' + end + '.csv'
    tidetools.get_dfo_wlev(statID_PA, start, end)
    wlev_meas = pd.read_csv(filename, skiprows=7, parse_dates=[0],
                            date_parser=dateParserMeasured)
    wlev_meas = wlev_meas.rename(columns={'Obs_date': 'time',
                                          'SLEV(metres)': 'slev'})
    return wlev_meas


def observed_anomaly(ttide, wlev_meas, msl):
    """
    Calculates the observed anomaly (water level obs - tidal predictions).

    :arg ttide: A struc object that contains tidal predictions from
                get_ttide_8.m
    :type ttide: struc with dimensions time, pred_all, pred_8

    :arg wlev_meas: A struc object with observations from DFO
    :type wlev_meas: sruc with dimensions time, slev

    :arg msl: The mean sea level from tidal predictions
    :type msl: float

    :returns: ssanomaly: the ssh anomaly (wlev_meas.slev-(ttide.pred_all+msl))
    """
    ssanomaly = np.zeros(len(wlev_meas.time))
    for i in np.arange(0, len(wlev_meas.time)):
        # check that there is a corresponding time
        # if any(wlev_pred.time == wlev_meas.time[i]):
        ssanomaly[i] = (wlev_meas.slev[i] -
                        (ttide.pred_all[ttide.time == wlev_meas.time[i]] +
                         msl))
        if not(ssanomaly[i]):
            ssanomaly[i] = float('Nan')

    return ssanomaly


def modelled_anomaly(sshs, location):
    """
    Calculates the modelled ssh anomaly by finding the difference between a
    simulation with all forcing and a simulation with tides only.

    :arg sshs: A struc object with ssh data from all_forcing and tidesonly
               model runs
    :type sshs: struc with dimensions 'all_forcing' and 'tidesonly'

    :arg location: string defining the desired location
    :type location: string either "PointAtkinson", "Victoria", "PatriciaBay",
                    "CampbellRiver"

    :returns: anom: the difference between all_forcing and tidesonly
    """
    anom = (sshs['all_forcing'][location][:, 0, 0] -
            sshs['tidesonly'][location][:, 0, 0])
    return anom


def correct_model(ssh, ttide, sdt, edt):
    """
    Adjusts model output by correcting for error in using only 8 constituents

    :arg ssh: an array with model ssh data
    :type ssh: array of numbers

    :arg ttide: struc with tidal predictions. Assumes tidal predictions
                are on the the hour can model output is on the 1/2 hour.
    :type ttide: struc with dimension time, pred_all, pred_8

    :arg sdt: datetime object representing start date of simulation
    :type sdt: datetime object

    :arg edt: datetime object representing end date of simulation
    :type edt: datetime object

    :returns: corr_model: the corrected model output
    """
    # find index of ttide.time at start and end
    inds = ttide.time[ttide.time == sdt].index[0]
    inde = ttide.time[ttide.time == edt].index[0]

    difference = ttide.pred_all-ttide.pred_8
    difference = np.array(difference)
    # average correction over two times to shift to the model 1/2 outputs
    # question: should I reconsider this calculation by interpolating?
    corr = 0.5*(difference[inds:inde] + difference[inds+1:inde+1])

    corr_model = ssh+corr
    return corr_model


def surge_tide(ssh, ttide, sdt, edt):
    """
    Calculates the sea surface height from the model run with surge only.
    That is, adds tidal prediction to modelled surge.
    :arg ssh: shh from surge only model run
    :type ssh: array of numbers

    :arg ttide: struc with tidal predictions
    :type ttide: struc with dimension time, pred_all, pred_8

    :arg sdt: datetime object representing start date of simulation
    :type sdt: datetime object

    :arg edt: datetime object representing end date of simulation
    :type edt: datetime object

    :returns: surgetide: the surge only run with tides added
              (mean not included)
    """
    # find index of ttide.time at start and end
    inds = ttide.time[ttide.time == sdt].index[0]
    inde = ttide.time[ttide.time == edt].index[0]

    # average correction over two times to shift to the model 1/2 outputs
    tide = np.array(ttide.pred_all)
    tide_corr = 0.5*(tide[inds:inde] + tide[inds+1:inde+1])

    surgetide = ssh+tide_corr
    return surgetide


def get_statistics(obs, model, t_obs, t_model, sdt, edt):
    """
    Calculates several statistics, such as mean error, maximum value, etc.
    for model and observations in a given time period.

    :arg obs: observation data
    :type obs: array

    :arg model: model data
    :type model: array

    :arg t_obs: observations time
    :type t_obs: array

    :arg t_model: model time
    :type t_model: array

    :arg sdt: datetime object representing start date of analysis period
    :type sdt: datetime object

    :arg edt: datetime object representing end date of analysis period
    :type edt: datetime object

    :returns: max_obs, max_model, tmax_obs, tmax_model, mean_error,
              mean_abs_error, rms_error, gamma2 (see Bernier Thompson 2006),
              correlation matrix, willmott score, mean_obs, mean_model,
              std_obs, std_model
    """
    # truncate model
    trun_model, trun_tm = truncate(
        model, t_model, sdt.replace(minute=30), edt.replace(minute=30))
    trun_model = trun_model[:-1]
    trun_tm = trun_tm[:-1]
    #  truncate and interpolate observations
    obs_interp = interp_to_model_time(trun_tm, obs, t_obs)
    # rebase observations
    # rbase_obs, rbase_to = rebase_obs(trun_obs, trun_to)
    error = trun_model-obs_interp
    # calculate statistics
    gamma2 = np.var(error)/np.var(obs_interp)
    mean_error = np.mean(error)
    mean_abs_error = np.mean(np.abs(error))
    rms_error = _rmse(error)
    corr = np.corrcoef(obs_interp, trun_model)
    max_obs, tmax_obs = _find_max(obs_interp, trun_tm)
    max_model, tmax_model = _find_max(trun_model, trun_tm)
    mean_obs = np.mean(obs_interp)
    mean_model = np.mean(trun_model)
    std_obs = np.std(obs_interp)
    std_model = np.std(trun_model)

    ws = willmott_skill(obs_interp, trun_model)

    return (
        max_obs, max_model, tmax_obs, tmax_model, mean_error, mean_abs_error,
        rms_error, gamma2, corr, ws, mean_obs, mean_model, std_obs, std_model,
    )


def truncate(data, time, sdt, edt):
    """
    Returns truncated array for the time period of interest
    :arg data: data to be truncated
    :type data: array

    :arg time: time output associated with data
    :type time: array

    :arg sdt: datetime object representing start date of analysis period
    :type sdt: datetime object

    :arg edt: datetime object representing end date of analysis period
    :type edt: datetime object

    :returns: data_t, time_t, truncated data and time arrays
    """
    inds = np.where(time == sdt)[0]
    inde = np.where(time == edt)[0]

    data_t = np.array(data[inds:inde + 1])
    time_t = np.array(time[inds:inde + 1])

    return data_t, time_t


def rebase_obs(data, time):
    """
    Rebases the observations so that they are given on the half hour instead
    of hour.
    Half hour outputs calculated by averaging between two hourly outputs.

    :arg data: data to be rebased
    :type data: array

    :arg time: time outputs associated with data
    :type time: array

    :returns: rebase_data, rebase_time, the data and times shifted by half an
              hour
    """
    rebase_data = 0.5*(data[1:]+data[:-1])
    rebase_time = []
    for k in range(time.shape[0]):
        rebase_time.append(time[k].replace(minute=30))
    rebase_time = np.array(rebase_time)
    rebase_time = rebase_time[0:-1]
    return rebase_data, rebase_time


def _rmse(diff):
    return np.sqrt(np.mean(diff**2))


def _find_max(data, time):
    max_data = np.nanmax(data)
    time_max = time[np.nanargmax(data)]

    return max_data, time_max


def willmott_skill(obs, model):
    """Calculates the Willmott skill score of the model. See Willmott 1982.
    :arg obs: observations data
    :type obs: array

    :arg model: model data
    :type model: array

    :returns: ws, the Willmott skill score
    """
    obar = np.nanmean(obs)
    mprime = model - obar
    oprime = obs - obar

    diff_sq = np.sum((model-obs)**2)
    add_sq = np.sum((np.abs(mprime) + np.abs(oprime))**2)

    ws = 1-diff_sq/add_sq
    return ws


def get_NOAA_wlev(station_no, start_date, end_date):
    """Download water level data from NOAA site for one NOAA station
    for specified period.

    :arg station_no: Station number e.g. 9443090.
    :type station_no: int

    :arg start_date: Start date; e.g. '01-JAN-2010'.
    :type start_date: str

    :arg end_date: End date; e.g. '31-JAN-2010'
    :type end_date: str

    :returns: Saves text file with water level data in meters at one station.
              Time zone is UTC
    """
    # Name the output file
    outfile = ('wlev_' + str(station_no) + '_' + str(start_date) +
               '_' + str(end_date) + '.csv')
    # Form urls and html information
    st_ar = arrow.Arrow.strptime(start_date, '%d-%b-%Y')
    end_ar = arrow.Arrow.strptime(end_date, '%d-%b-%Y')

    base_url = 'http://tidesandcurrents.noaa.gov'
    form_handler = (
        '/stationhome.html?id='
        + str(station_no))
    data_provider = (
        '/api/datagetter?product=hourly_height&application=NOS.COOPS.TAC.WL'
        + '&begin_date=' + st_ar.format('YYYYMMDD') + '&end_date='
        + end_ar.format('YYYYMMDD')
        + '&datum=MLLW&station='+str(station_no)
        + '&time_zone=GMT&units=metric&interval=h&format=csv')
    # Go get the data from the DFO site
    with requests.Session() as s:
        s.post(base_url)
        r = s.get(base_url + data_provider)
    # Write the data to a text file
    with open(outfile, 'w') as f:
        f.write(r.text)


def get_NOAA_predictions(station_no, start_date, end_date):
    """Download tide predictions from NOAA site for one NOAA station
    for specified period.

    :arg int station_no: Station number e.g. 9443090.

    :arg str start_date: Start date; e.g. '01-JAN-2010'.

    :arg str end_date: End date; e.g. '31-JAN-2010'

    :returns: Saves text file with predictions in meters at one station.
              Time zone is UTC
    """
    # Name the output file
    outfile = ('predictions_' + str(station_no) + '_' + str(start_date) + '_'
               + str(end_date) + '.csv')
    # Form urls and html information

    st_ar = arrow.Arrow.strptime(start_date, '%d-%b-%Y')
    end_ar = arrow.Arrow.strptime(end_date, '%d-%b-%Y')

    base_url = 'http://tidesandcurrents.noaa.gov'
    form_handler = (
        '/stationhome.html?id='
        + str(station_no))
    data_provider = (
        '/api/datagetter?product=predictions&application=NOS.COOPS.TAC.WL'
        + '&begin_date=' + st_ar.format('YYYYMMDD') + '&end_date='
        + end_ar.format('YYYYMMDD')
        + '&datum=MLLW&station='+str(station_no)
        + '&time_zone=GMT&units=metric&interval=h&format=csv')
    # Go get the data from the DFO site
    with requests.Session() as s:
        s.post(base_url)
        r = s.get(base_url + data_provider)
    # Write the data to a text file
    with open(outfile, 'w') as f:
        f.write(r.text)


def get_operational_weather(start, end, grid):
    """
    Returns the operational weather between the dates start and end at
    the grid point defined in grid.

    :arg start: string containing the start date of the weather collection
                in format '01-Nov-2006'
    :type start: str

    :arg start: string containing the end date of the weather collection in
                format '01-Nov-2006'
    :type start: str

    :arg grid: array of the operational grid coordinates for the point of
               interest eg. [244,245]
    :arg type: arr of ints

    :returns: windspeed, winddir pressure and time array from weather data
              for the times indicated
              wind speed is m/s
              winddir is direction wind is blowing in degrees counterclockwise
              from east
              pressure is kPa
              time is UTC
    """
    u10 = []
    v10 = []
    pres = []
    time = []
    st_ar = arrow.Arrow.strptime(start, '%d-%b-%Y')
    end_ar = arrow.Arrow.strptime(end, '%d-%b-%Y')

    ops_path = '/ocean/sallen/allen/research/Meopar/Operational/'
    opsp_path = '/ocean/nsoontie/MEOPAR/GEM2.5/ops/'

    for r in arrow.Arrow.range('day', st_ar, end_ar):
        mstr = "{0:02d}".format(r.month)
        dstr = "{0:02d}".format(r.day)
        fstr = 'ops_y' + str(r.year) + 'm' + mstr + 'd' + dstr + '.nc'
        f = NC.Dataset(ops_path+fstr)
        # u
        var = f.variables['u_wind'][:, grid[0], grid[1]]
        u10.extend(var[:])
        # v
        var = f.variables['v_wind'][:, grid[0], grid[1]]
        v10.extend(var[:])
        # pressure
        fpstr = ('slp_corr_ops_y' + str(r.year) + 'm' + mstr + 'd' + dstr
                 + '.nc')
        fP = NC.Dataset(opsp_path+fpstr)
        var = fP.variables['atmpres'][:, grid[0], grid[1]]
        pres.extend(var[:])
        # time
        tim = f.variables['time_counter']
        time.extend(tim[:])
        times = convert_date_seconds(time, '01-Jan-1970')

        u10s = np.array(u10)
        v10s = np.array(v10)
        press = np.array(pres)

    windspeed = np.sqrt(u10s**2+v10s**2)
    winddir = np.arctan2(v10, u10) * 180 / np.pi
    winddir = winddir + 360 * (winddir < 0)
    return windspeed, winddir, press, times


def interp_to_model_time(time_model, varp, tp):
    """
    Interpolates a variable to model output times.

    :arg model_time: array of model output times as datetime objects
    :type model_time: array with datetimes

    :arg varp: array of variable to be interpolated
    :type varp: array

    :arg tp: array of times associated with variable
    :type tp: array

    :returns: varp_interp, the variable interpolated to model_times
    """
    # Strategy: convert times to seconds past a reference value.
    # Use this as the independent variable in interpolation.
    # Set epoc (reference) time.
    epoc = time_model[0]

    #  Determine tp times wrt epc
    tp_wrt_epoc = []
    for t in tp:
        tp_wrt_epoc.append((t-epoc).total_seconds())

    # Interpolate observations to model times
    varp_interp = []
    for t in time_model:
        mod_wrt_epoc = (t-epoc).total_seconds()
        varp_interp.append(np.interp(mod_wrt_epoc, tp_wrt_epoc, varp))

    return varp_interp
