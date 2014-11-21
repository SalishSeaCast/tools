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

"""Salish Sea NEMO nowcast worker that blends EC Data for the Fraser River at
Hope with Climatology for all other rivers and generates runoff file.
"""
from __future__ import division

import logging
import os
import traceback

import arrow
import netCDF4 as NC
import numpy as np
import yaml
import zmq

from salishsea_tools import rivertools
from salishsea_tools.nowcast import lib


worker_name = lib.get_module_name()

logger = logging.getLogger(worker_name)

context = zmq.Context()


def main():
    # Prepare the worker
    parser = lib.basic_arg_parser(worker_name, description=__doc__)
    parsed_args = parser.parse_args()
    config = lib.load_config(parsed_args.config_file)
    lib.configure_logging(config, logger, parsed_args.debug)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {.config_file}'.format(parsed_args))
    lib.install_signal_handlers(logger, context)
    socket = lib.init_zmq_req_rep_worker(context, config, logger)
    # Do the work
    checklist = {}
    try:
        RealFraserClimateElse(config, checklist)
        logger.info(
            'Creation of runoff file from Fraser at Hope '
            'and climatology elsewhere completed')
        # Exchange success messages with nowcast manager process
        lib.tell_manager(
            worker_name, 'success', config, logger, socket, checklist)
    except lib.WorkerError:
        # Exchange failure messages with nowcast manager process
        logger.critical('Rivers runoff file creation failed')
        lib.tell_manager(worker_name, 'failure', config, logger, socket)
    except:
        logger.critical('unhandled exception:')
        for line in traceback.format_exc():
            logger.error(line)
        # Exchange crash messages with the nowcast manager process
        lib.tell_manager(worker_name, 'crash', config, logger, socket)
    # Finish up
    context.destroy()
    logger.info('task completed; shutting down')


def RealFraserClimateElse(config, checklist):
    '''Driver Routine to read Fraser River at Hope flow and insert in
    climatology for everything else'''

    # find yesterday
    utc = arrow.utcnow()
    utc = utc.replace(hours=-8)
    now = utc.floor('day')
    yesterday = now.replace(days=-1)
    # find history of fraser flow
    fraserflow = getFraserAtHope()
    # select yesterday's value
    step1 = fraserflow[fraserflow[:,0] == yesterday.year]
    step2 = step1[step1[:,1] == yesterday.month]
    step3 = step2[step2[:,2] == yesterday.day]
    FlowAtHope = step3[0,3]

    # get climatology
    criverflow, lat, lon, riverdepth = getRiverClimatology()
    # interpolate to today
    driverflow = calculate_daily_flow(yesterday, criverflow)
    logger.debug('Getting file for {yesterday}'.format(yesterday=yesterday))

    # get Fraser Watershed Climatology without Fraser
    otherratio, fraserratio, nonFraser, afterHope = FraserClimatology()

    # calculate combined runoff
    pd = rivertools.get_watershed_prop_dict('fraser')
    runoff = fraser_correction(pd, FlowAtHope , yesterday, afterHope,
                               nonFraser, fraserratio, otherratio,
                               driverflow)

    # and make the file
    directory = '/ocean/sallen/allen/research/MEOPAR/Rivers'
    # set up filename to follow NEMO conventions
    filename = 'RFraserCElse_y'+str(yesterday.year)+'m'+'{:0=2}'.format(yesterday.month)+'d'+'{:0=2}'.format(yesterday.day)+'.nc'

    write_file(directory, filename, yesterday, runoff, lat, lon, riverdepth)
    logger.debug('File written to {directory} as {filename}'.format(
            directory=directory, filename=filename))


def FraserClimatology():
    '''Function to read in the Fraser Climatology separated from Hope Flow'''
    with open('/ocean/sallen/allen/research/MEOPAR/Tools/I_ForcingFiles/Rivers/FraserClimatologySeparation.yaml') as f:
        FraserClimatologySeparation = yaml.safe_load(f)
    otherratio = FraserClimatologySeparation['Ratio that is not Fraser']
    fraserratio = FraserClimatologySeparation['Ratio that is Fraser']
    nonFraser = np.array(FraserClimatologySeparation['non Fraser by Month'])
    afterHope = np.array(FraserClimatologySeparation['after Hope by Month'])
    return otherratio, fraserratio, nonFraser, afterHope


def getFraserAtHope():
    '''get Fraser Flow data at Hope from ECget file'''
    filename = '/data/dlatorne/SOG-projects/SOG-forcing/ECget/Fraser_flow'
    fraserflow = np.loadtxt(filename)
    return fraserflow


def getRiverClimatology():
    '''read in the monthly climatology that we will use for all the other rivers'''
    #open monthly climatology
    filename = '/ocean/sallen/allen/research/MEOPAR/nemo-forcing/rivers/rivers_month.nc'
    clim_rivers = NC.Dataset(filename)
    criverflow = clim_rivers.variables['rorunoff']

    # get other variables so we can put them in new files
    lat = clim_rivers.variables['nav_lat']
    lon = clim_rivers.variables['nav_lon']
    riverdepth = clim_rivers.variables['rodepth']
    return criverflow, lat, lon, riverdepth

def calculate_daily_flow(r, criverflow):
    '''interpolate the daily values from the monthly values'''

    pyear, nyear = r.year, r.year
    if r.day < 16:
        prevmonth = r.month-1
        if prevmonth == 0:  # handle January
            prevmonth = 12
            pyear = pyear - 1
        nextmonth = r.month
    else:
        prevmonth = r.month
        nextmonth = r.month + 1
        if nextmonth == 13: # handle December
            nextmonth = 1
            nyear = nyear + 1

    fp = r - arrow.get(pyear,prevmonth,15)
    fn = arrow.get(nyear,nextmonth,15) - r
    ft = fp+fn
    fp = fp.days/ft.days
    fn = fn.days/ft.days
    driverflow = fn*criverflow[prevmonth-1] + fp*criverflow[nextmonth-1]
    return driverflow


def write_file(directory, filename, r, flow, lat, lon, riverdepth):
    ''' given the flow and the riverdepth and the date, write the nc file'''
    nemo = NC.Dataset(directory+'/'+filename, 'w')
    nemo.description = 'Real Fraser Values, Daily Climatology for Other Rivers'

    # dimensions
    ymax, xmax = lat.shape
    nemo.createDimension('x', xmax)
    nemo.createDimension('y', ymax)
    nemo.createDimension('time_counter', None)

    # variables
    # latitude and longitude
    nav_lat = nemo.createVariable('nav_lat','float32',('y','x'),zlib=True)
    nav_lat = lat
    x = nemo.createVariable('nav_lon','float32',('y','x'),zlib=True)
    nav_lon = lon
    # time
    time_counter = nemo.createVariable('time_counter', 'float32', ('time_counter'),zlib=True)
    time_counter.units = 'non-dim'
    time_counter[0:1] = range(1,2)
    # runoff
    rorunoff = nemo.createVariable('rorunoff', 'float32', ('time_counter','y','x'), zlib=True)
    rorunoff._Fillvalue = 0.
    rorunoff._missing_value = 0.
    rorunoff._units = 'kg m-2 s-1'
    rorunoff[0,:] = flow
    # depth
    rodepth = nemo.createVariable('rodepth','float32',('y','x'),zlib=True)
    rodepth._Fillvalue = -1.
    rodepth.missing_value = -1.
    rodepth.units = 'm'
    rodepth = riverdepth
    nemo.close()


def fraser_correction(pd, fraserflux, r, afterHope, NonFraser, fraserratio, otherratio,
                      runoff):
    ''' for the Fraser Basin only, replace basic values with the new climatology after Hope and the
     observed values for Hope.  Note, we are changing runoff only and not using/changing river
     depth '''
    for key in pd:
        if "Fraser" in key:
            flux = calculate_daily_flow(r,afterHope) + fraserflux
            subarea = fraserratio
        else:
            flux = calculate_daily_flow(r,NonFraser)
            subarea = otherratio

        river = pd[key]
        runoff = rivertools.fill_runoff_array(flux*river['prop']/subarea,river['i'],
                          river['di'],river['j'],river['dj'],river['depth'],
                          runoff,np.empty_like(runoff))[0]
    return runoff


if __name__ == '__main__':
    main()
