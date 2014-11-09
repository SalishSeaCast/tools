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

"""Salish Sea NEMO nowcast worker that scrapes NOAA Neah Bay storm surge
forecast site and generates western open boundary conditions ssh files.
"""
import datetime
import logging
import os
import urllib2

from bs4 import BeautifulSoup
import pytz
import netCDF4 as nc
import numpy as np
import pandas as pd
import zmq

from salishsea_tools import nc_tools
from salishsea_tools.nowcast import lib


worker_name = lib.get_module_name()

logger = logging.getLogger(worker_name)

context = zmq.Context()


URL = 'http://www.nws.noaa.gov/mdl/etsurge/index.php?page=stn&region=wc&datum=msl&list=&map=0-48&type=both&stn=waneah'


def main():
    parser = lib.basic_arg_parser(worker_name, description=__doc__)
    parsed_args = parser.parse_args()
    config = lib.load_config(parsed_args.config_file)
    lib.configure_logging(config, logger, parsed_args.debug)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {.config_file}'.format(parsed_args))
    lib.install_signal_handlers(logger, context)
    socket = lib.init_zmq_req_rep_worker(context, config, logger)

    getNBssh(config)
    logger.info(
        'Neah Bay sea surface height web scraping and file creation completed')

    # message = lib.serialize_message(worker_name, 'end of nowcast')
    # socket.send(message)
    # logger.info('sent "end of nowcast" message')

    # msg = socket.recv()
    # message = lib.deserialize_message(msg)
    # logger.info(
    #     'received message from {source}: {msg_type}'.format(**message))

    context.destroy()
    logger.info('task completed; shutting down')


def getNBssh(config):
    """Script for generate sea surface height forcing files from the
    Neah Bay storm surge website.
    """
    fB = nc.Dataset(config['bathymetry'])
    lats = fB.variables['nav_lat'][:]
    lons = fB.variables['nav_lon'][:]
    fB.close()
    logger.debug('loaded lats & lons from {bathymetry}'.format(**config))
    # Load surge data
    textfile = read_website(config['ssh']['ssh_dir'])
    data = load_surge_data(textfile)
    # Process the dates to find days with a full prediction
    dates = np.array(data.date.values)
    for i in range(dates.shape[0]):
        dates[i] = to_datetime(dates[i], datetime.date.today().year)
    dates_list = list_full_days(dates)
    # Loop through full days and save netcdf
    for d in dates_list:
        surges, tc, forecast_flag = retrieve_surge(d, dates, data)
        save_netcdf(
            d, tc, surges, forecast_flag, textfile,
            config['ssh']['ssh_dir'], lats, lons)


def read_website(save_path):
    """Reads a website with Neah Bay storm surge predictions/observations.

    The data is in a file in the given save_path returns the filename
    where the surge data is stored.
    """
    response = urllib2.urlopen(URL)
    html = response.read()
    logger.debug(
        'downloaded Neah Bay storm surge observations & predictions from {}'
        .format(URL))
    # Parse the text table out of the HTML
    soup = BeautifulSoup(html)
    table = soup.find('pre').contents
    for line in table:
        line = line.replace('[', '')
        line = line.replace(']', '')
    logger.debug(
        'scraped observations & predictions table from downloaded HTML')
    # Save the table as a text file with the date it was generated as its name
    utc_now = datetime.datetime.now(pytz.timezone('UTC'))
    filename = os.path.join(
        save_path, 'txt', 'sshNB_{:%Y-%m-%d}.txt'.format(utc_now))
    with open(filename, 'wt') as f:
        f.writelines(table)
    logger.debug(
        'observations & predictions table saved to {}'.format(filename))
    return filename


def load_surge_data(filename):
    """Loads the textfile with surge predictions
    returns as a data structure"""

    #Loading the data from that text file.
    data = pd.read_csv(filename,skiprows=3,names=['date','surge','tide','obs','fcst','anom','comment'],
    comment='#')
    #drop rows with all Nans
    data= data.dropna(how='all')
    return data


def save_netcdf(day,tc,surges,forecast_flag,textfile,save_path,lat,lon):
    """saves the surge for a given day in a netcdf file"""
    #define stuff we will need for saving netcdfs - JdF parameters.
    startj = 384
    endj = 471
    lengthj = endj-startj
    r = 1

    daystr = 'ssh_{}.nc'.format(day.strftime('y%Ym%md%d'))
    if forecast_flag:
        savstr = os.path.join(save_path,'fcst',daystr)
        comment = 'Prediction from Neah Bay storm surge website'
    else:
        savstr = os.path.join(save_path,'obs',daystr)
        comment = 'Observation from Neah Bay storm surge website'
    #open netcdf file
    ssh_file = nc.Dataset(savstr, 'w')
    nc_tools.init_dataset_attrs(
    ssh_file,
    title='Neah Bay SSH hourly values',
    notebook_name='',
    nc_filepath=savstr,
    comment=comment)
    ssh_file.source=textfile

    #dimensions
    ssh_file.createDimension('xbT', lengthj*r)
    ssh_file.createDimension('yb', 1)
    ssh_file.createDimension('time_counter', None)
    # variables
    # time_counter
    time_counter = ssh_file.createVariable('time_counter', 'float32', ('time_counter'))
    time_counter.long_name = 'Time axis'
    time_counter.axis = 'T'
    time_counter.units = 'hour since 00:00:00 on ' +day.strftime('%Y-%m-%d')
    # nav_lat and nav_lon
    nav_lat = ssh_file.createVariable('nav_lat','float32',('yb','xbT'))
    nav_lat.long_name = 'Latitude'
    nav_lat.units = 'degrees_north'
    nav_lon = ssh_file.createVariable('nav_lon','float32',('yb','xbT'))
    nav_lon.long_name = 'Longitude'
    nav_lon.units = 'degrees_east'
    # ssh
    sossheig = ssh_file.createVariable('sossheig', 'float32',
                               ('time_counter','yb','xbT'), zlib=True)
    sossheig.units = 'm'
    sossheig.long_name = 'Sea surface height'
    sossheig.coordinates = 'nav_lon nav_lat time_counter'
    sossheig.grid = 'SalishSea2'
    # vobtcrtx, vobtcrty
    vobtcrtx = ssh_file.createVariable('vobtcrtx', 'float32',
                                   ('time_counter','yb','xbT'), zlib=True)
    vobtcrtx.units = 'm/s'
    vobtcrtx.long_name = 'Barotropic U Velocity- ZEROD'
    vobtcrtx.grid = 'SalishSea2'
    vobtcrty = ssh_file.createVariable('vobtcrty', 'float32',
                                   ('time_counter','yb','xbT'), zlib=True)
    vobtcrty.units = 'm/s'
    vobtcrty.long_name = 'Barotropic V Velocity- ZEROD'
    vobtcrty.grid = 'SalishSea2'
    # nbidta, ndjdta, ndrdta
    nbidta = ssh_file.createVariable('nbidta', 'int32' , ('yb','xbT'), zlib=True)
    nbidta.long_name = 'i grid position'
    nbidta.units = 1
    nbjdta = ssh_file.createVariable('nbjdta', 'int32' , ('yb','xbT'), zlib=True)
    nbjdta.long_name = 'j grid position'
    nbjdta.units = 1
    nbrdta = ssh_file.createVariable('nbrdta', 'int32' , ('yb','xbT'), zlib=True)
    nbrdta.long_name = 'position from boundary'
    nbrdta.units = 1

    for ir in range(0,r):
        nav_lat[0,ir*lengthj:(ir+1)*lengthj] = lat[startj:endj,ir]
        nav_lon[0,ir*lengthj:(ir+1)*lengthj] = lon[startj:endj,ir]
        nbidta[0,ir*lengthj:(ir+1)*lengthj] = ir
        nbjdta[0,ir*lengthj:(ir+1)*lengthj] = range(startj,endj)
        nbrdta[0,ir*lengthj:(ir+1)*lengthj] = ir

    for ib in range(0,lengthj*r):
        sossheig[:,0,ib] = surges
        time_counter[:] = tc+1
        vobtcrtx[:,0,ib] = 0*np.ones(len(surges))
        vobtcrty[:,0,ib] = 0*np.ones(len(surges))
    ssh_file.close()


def retrieve_surge(day,dates, data):
    """gathers the surge information for a single day.
    returns the surges in meteres, an array with time_counter and a flag indicating if this day was a forecast"""
    #initialize forecast flag and surge array
    forecast_flag=0; surge=[]
    #grab list of times on this day.
    tc,ds= isolate_day(day,dates)

    for d in ds:
        #convert datetime to string for comparing with times in data
        daystr = d.strftime('%m/%d %HZ')
        tide=data.tide[data.date==daystr].item()
        obs=data.obs[data.date==daystr].item()
        fcst = data.fcst[data.date==daystr].item()
        if obs == 99.90:
            #fall daylight savings
            if fcst==99.90:
                #if surge is empty, just append 0
                if not surge:
                    surge.append(0)
                else:
                #otherwise append previous value
                    surge.append(surge[-1])
            else:
                surge.append(feet_to_metres(fcst-tide))
                forecast_flag=1
        else:
            surge.append(feet_to_metres(obs-tide))
    return surge, tc,  forecast_flag


def isolate_day(day, dates):
    """returns array of time_counter and datetime objects over a 24 hour period covering one full day"""
    tc=np.arange(24)
    dates_return=[];
    for t in dates:
        if t.month==day.month:
            if t.day==day.day:
                dates_return.append(t);
    return tc, np.array(dates_return)


def list_full_days(dates):
    """returns a list of days that have a full 24 hour data set."""

    #check if first day is a full day
    tc,ds= isolate_day(dates[0],dates)
    if ds.shape[0] == tc.shape[0]:
        start = dates[0]
    else:
        start = dates[0] +datetime.timedelta(days=1)
    start=datetime.datetime(start.year,start.month, start.day,tzinfo=pytz.timezone('UTC'))

    #check if last day is a full day
    tc,ds = isolate_day(dates[-1],dates)
    if ds.shape[0] == tc.shape[0]:
        end = dates[-1]
    else:
        end = dates[-1] -datetime.timedelta(days=1)
    end=datetime.datetime(end.year,end.month, end.day,tzinfo=pytz.timezone('UTC'))

    #list of dates that are full
    dates_list = [start +datetime.timedelta(days=i) for i in range((end-start).days+1)]
    return dates_list


def to_datetime(datestr,year):
    """ converts the string given by datestr to a datetime object.
    The year is an argument because the datestr in the NOAA data doesn't have a year.
    Times are in UTC/GMT.
    returns a datetime representation of datestr"""
    dt = datetime.datetime.strptime(datestr,'%m/%d %HZ')
    dt =dt.replace(year=year)
    dt=dt.replace(tzinfo=pytz.timezone('UTC'))
    return dt


def feet_to_metres(feet):
    metres = feet*0.3048
    return metres


if __name__ == '__main__':
    main()
