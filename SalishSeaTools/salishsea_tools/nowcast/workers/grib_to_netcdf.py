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

"""Salish Sea NEMO nowcast worker that collects weather forecast results
from hourly GRIB2 files and produces day-long NEMO atmospheric forceing
netCDF files.

Note that wgrib2 and Pramod Thupaki's grid_defn.pl are assumed to be
symlinked in the working directory.
"""
from __future__ import division

import glob
import logging
import os
import subprocess as sp

import arrow
import netCDF4 as nc
import numpy as np
import zmq

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
    grib_to_netcdf(config, checklist)
    logger.info('NEMO-atmos forcing file creation completed')
    # Exchange success messages with the nowcast manager process
#    success(config, socket, checklist)
    # Finish up
    context.destroy()
    logger.info('task completed; shutting down')


def success(config, socket, checklist):
    msg_type = 'success'
    # Send message to nowcast manager
    message = lib.serialize_message(worker_name, msg_type, checklist)
    socket.send(message)
    logger.info(
        'sent message: ({msg_type}) {msg_words}'
        .format(
            msg_type=msg_type,
            msg_words=config['msg_types'][worker_name][msg_type]))
    # Wait for and process response
    msg = socket.recv()
    message = lib.deserialize_message(msg)
    source = message['source']
    msg_type = message['msg_type']
    logger.info(
        'received message from {source}: ({msg_type}) {msg_words}'
        .format(source=source,
                msg_type=message['msg_type'],
                msg_words=config['msg_types'][source][msg_type]))


def grib_to_netcdf(config, checklist):
    """Collect weather forecast results from hourly GRIB2 files
    and produces day-long NEMO atmospheric forcing netCDF files.
    """
    GRIBdir = config['weather']['GRIB_dir']
    OPERdir = config['weather']['ops_dir']
    utc = arrow.utcnow()
    now = utc.to('Canada/Pacific')
    year, month, day = now.year, now.month, now.day
    yesterday = now.replace(days=-1)
    yearm1, monthm1, daym1 = yesterday.year, yesterday.month, yesterday.day
    ymd = (
        'y{year}m{month:0=2}d{day:0=2}'
        .format(year=year, month=month, day=day))
    p1 = (
        '{year}{month:0=2}{day:0=2}/18/'
        .format(year=yearm1, month=monthm1, day=daym1))
    p2 = (
        '{year}{month:0=2}{day:0=2}/06/'
        .format(year=year, month=month, day=day))
    p3 = (
        '{year}{month:0=2}{day:0=2}/18/'
        .format(year=year, month=month, day=day))
    logger.debug('forecast sections: '.format(p1, p2, p3))
    HoursWeNeed = {
        # part: (dir, start hr, end hr)
        'part one':  (p1, 24-18-1, 24+6-18),
        'part two':  (p2, 7-6, 18-6),
        'part three': (p3, 19-18, 23-18),
    }

    # CLEANUP
    size = 'watershed'
    if size == 'full':
        fileextra = ''
    elif size == 'watershed':  # see AtmosphericGridSelection.ipynb
        fileextra = ''
        ist, ien = 110, 365
        jst, jen = 20, 285

    # PROMOTE TO MODULE LEVEL
    try:
        os.remove('wglog')
    except Exception:
        pass
    logfile = open('wglog', 'w')


    process_gribUV(GRIBdir, HoursWeNeed, logfile)
    process_gribscalar(GRIBdir, HoursWeNeed, logfile)
    outgrib, outzeros = GRIBappend(
        OPERdir, GRIBdir, ymd, HoursWeNeed, logfile)
    if size != 'full':
        outgrib, outzeros = subsample(
            OPERdir, ymd, ist, ien, jst, jen, outgrib, outzeros, logfile)
    outnetcdf, out0netcdf = makeCDF(
        OPERdir, ymd, fileextra, outgrib, outzeros, logfile)
    processCDF(outnetcdf, out0netcdf, ymd)
    renameCDF(outnetcdf)

    plt.savefig('wg.png')


def process_gribUV(GRIBdir, HoursWeNeed, logfile):
    """Use wgrib2 to consolidate each hour's u and v wind components into a
    single file and then rotate the wind direction to geographical
    coordinates.
    """
    for part in ('part one', 'part two', 'part three'):
        for fhour in range(HoursWeNeed[part][1], HoursWeNeed[part][2]+1):
            # Set up directories and files
            sfhour = '{:0=3}'.format(fhour)
            dire = HoursWeNeed[part][0]
            outuv = GRIBdir+dire+sfhour+'/UV.grib'
            try:
                os.remove(outuv)
            except Exception:
                pass
            outuvrot = GRIBdir+dire+sfhour+'/UVrot.grib'
            try:
                os.remove(outuvrot)
            except Exception:
                pass
            # Consolidate u and v wind component values into one file
            fn = glob.glob(GRIBdir+dire+sfhour+'/*UGRD*')
            sp.call(
                ['./wgrib2', fn[0], '-append', '-grib', outuv], stdout=logfile)
            fn = glob.glob(GRIBdir+dire+sfhour+'/*VGRD*')
            sp.call(
                ['./wgrib2', fn[0], '-append', '-grib', outuv], stdout=logfile)
            ### print sp.check_output(["./wgrib2",fn[0],"-vt"])
            # rotate
            GRIDspec = sp.check_output(['./grid_defn.pl', outuv])
            cmd = ['./wgrib2', outuv]
            cmd.extend('-new_grid_winds earth'.split())
            cmd.append('-new_grid')
            cmd.extend(GRIDspec.split())
            cmd.append(outuvrot)
            sp.call(cmd, stdout=logfile)
            os.remove(outuv)


def process_gribscalar(GRIBdir, HoursWeNeed, logfile):
    """Use wgrib2 and grid_defn.pl to consolidate each hour's scalar
    variables into an single file and then re-grid them to match the
    u and v wind components.
    """
    for part in ('part one', 'part two', 'part three'):
        for fhour in range(HoursWeNeed[part][1], HoursWeNeed[part][2]+1):
            # Set up directories and files
            sfhour = '{:0=3}'.format(fhour)
            dire = HoursWeNeed[part][0]
            outscalar = GRIBdir+dire+sfhour+'/scalar.grib'
            outscalargrid = GRIBdir+dire+sfhour+'/gscalar.grib'
            # Delete residual instances of files that are created so that
            # function can be re-run cleanly
            try:
                os.remove(outscalar)
            except Exception:
                pass
            try:
                os.remove(outscalargrid)
            except Exception:
                pass
            # Consolidate scalar variables into one file
            for fn in glob.glob(GRIBdir+dire+sfhour+'/*'):
                if not ('GRD' in fn) and ('CMC' in fn):
                    sp.call(
                        ['./wgrib2', fn, '-append', '-grib', outscalar],
                        stdout=logfile)
            #  Re-grid
            GRIDspec = sp.check_output(['./grid_defn.pl', outscalar])
            cmd = ['./wgrib2', outscalar]
            cmd.append('-new_grid')
            cmd.extend(GRIDspec.split())
            cmd.append(outscalargrid)
            sp.call(cmd, stdout=logfile, stderr=logfile)
            os.remove(outscalar)


def GRIBappend(OPERdir, GRIBdir, ymd, HoursWeNeed, logfile):
    """Concatenate in hour order the wind velocity components
    and scalar variables from hourly files into a daily file.

    Also create the zero-hour file that is used to initialize the
    calculation of instantaneous values from the forecast accumulated
    values.
    """
    outgrib = os.path.join(OPERdir, 'oper_allvar_{ymd}.grib'.format(ymd=ymd))
    outzeros = os.path.join(OPERdir, 'oper_000_{ymd}.grib'.format(ymd=ymd))
    # Delete residual instances of files that are created so that
    # function can be re-run cleanly
    try:
        os.unremove(outgrib)
    except Exception:
        pass
    try:
        os.remove(outzeros)
    except Exception:
        pass
    for part in ('part one', 'part two', 'part three'):
        for fhour in range(HoursWeNeed[part][1], HoursWeNeed[part][2]+1):
            # Set up directories and files
            sfhour = '{:0=3}'.format(fhour)
            dire = HoursWeNeed[part][0]
            outuvrot = GRIBdir+dire+sfhour+'/UVrot.grib'
            outscalargrid = GRIBdir+dire+sfhour+'/gscalar.grib'
            if fhour == 0 or (part == 'part one' and fhour == 5):
                sp.call(
                    ['./wgrib2', outuvrot, '-append', '-grib', outzeros],
                    stdout=logfile)
                sp.call(
                    ['./wgrib2', outscalargrid, '-append', '-grib', outzeros],
                    stdout=logfile)
            else:
                sp.call(
                    ['./wgrib2', outuvrot, '-append', '-grib', outgrib],
                    stdout=logfile)
                sp.call(
                    ["./wgrib2", outscalargrid, '-append', "-grib", outgrib],
                    stdout=logfile)
            os.remove(outuvrot)
            os.remove(outscalargrid)
    return outgrib, outzeros


def subsample(OPERdir, ymd, ist, ien, jst, jen, outgrib, outzeros, logfile):
    """Crop the grid to the Salish Sea NEMO model domain.
    """
    newgrib = os.path.join(
        OPERdir, 'oper_allvar_small_{ymd}.grib'.format(ymd=ymd))
    newzeros = os.path.join(
        OPERdir, 'oper_000_small_{ymd}.grib'.format(ymd=ymd))
    istr = '{ist}:{ien}'.format(ist=ist, ien=ien)
    jstr = '{jst}:{jen}'.format(jst=jst, jen=jen)
    sp.call(
        ['./wgrib2', outgrib, '-ijsmall_grib', istr, jstr, newgrib],
        stdout=logfile)
    sp.call(
        ['./wgrib2', outzeros, '-ijsmall_grib', istr, jstr, newzeros],
        stdout=logfile)
    os.remove(outgrib)
    os.remove(outzeros)
    return newgrib, newzeros


def makeCDF(OPERdir, ymd, fileextra, outgrib, outzeros, logfile):
    """Convert the GRIB files to netcdf (classic) files.
    """
    outnetcdf = os.path.join(
        OPERdir,
        'ops{fileextra}_{ymd}.nc'.format(fileextra=fileextra, ymd=ymd))
    out0netcdf = os.path.join(OPERdir, 'oper_000_{ymd}.nc'.format(ymd=ymd))
    sp.call(['./wgrib2', outgrib, '-netcdf', outnetcdf], stdout=logfile)
    sp.call(['./wgrib2', outzeros, '-netcdf', out0netcdf], stdout=logfile)
    os.remove(outgrib)
    os.remove(outzeros)
    return outnetcdf, out0netcdf


def processCDF(outnetcdf, out0netcdf, ymd):
    """Calculate instantaneous values from the forecast accumulated values
    for the precipitation and radiation variables.
    """
    data = nc.Dataset(outnetcdf, 'r+')
    data0 = nc.Dataset(out0netcdf, 'r')
    acc_vars = ('APCP_surface', 'DSWRF_surface', 'DLWRF_surface')
    acc_values = {
        'acc': {},
        'zero': {},
        'inst': {},
    }
    for var in acc_vars:
        acc_values['acc'][var] = data.variables[var][:]
        acc_values['zero'][var] = data0.variables[var][:]
        acc_values['inst'][var] = np.empty_like(acc_values['acc'][var])

    plt.subplot(2, 3, 1)
    plt.plot(acc_values['acc']['APCP_surface'][:, 200, 200], 'o-')
    plt.title(ymd)

    for var in acc_vars:
        acc_values['inst'][var][0] = (
            acc_values['acc'][var][0] - acc_values['zero'][var][0]) / 3600
        for t in range(1, 7):
            acc_values['inst'][var][t] = (
                acc_values['acc'][var][t] - acc_values['acc'][var][t-1]) / 3600
        acc_values['inst'][var][7] = acc_values['acc'][var][7] / 3600
        for t in range(8, 19):
            acc_values['inst'][var][t] = (
                acc_values['acc'][var][t] - acc_values['acc'][var][t-1]) / 3600
        acc_values['inst'][var][19] = (acc_values['acc'][var][19]) / 3600
        for t in range(20, 24):
            acc_values['inst'][var][t] = (
                acc_values['acc'][var][t] - acc_values['acc'][var][t-1]) / 3600
    plt.subplot(2, 3, 2)
    plt.plot(acc_values['inst']['APCP_surface'][:, 200, 200])
    for var in acc_vars:
        data.variables[var][:] = acc_values['inst'][var][:]
    data.close()
    data0.close()
    os.remove(out0netcdf)


def renameCDF(outnetcdf):
    """Rename variables to match NEMO naming conventions.
    """
    data = nc.Dataset(outnetcdf, 'r+')
    data.renameDimension('time', 'time_counter')
    data.renameVariable('latitude', 'nav_lat')
    data.renameVariable('longitude', 'nav_lon')
    data.renameVariable('time', 'time_counter')
    data.renameVariable('UGRD_10maboveground', 'u_wind')
    data.renameVariable('VGRD_10maboveground', 'v_wind')
    data.renameVariable('DSWRF_surface', 'solar')
    data.renameVariable('SPFH_2maboveground', 'qair')
    data.renameVariable('DLWRF_surface', 'therm_rad')
    data.renameVariable('TMP_2maboveground', 'tair')
    data.renameVariable('PRMSL_meansealevel', 'atmpres')
    data.renameVariable('APCP_surface', 'precip')
    Temp = data.variables['tair'][:]
    plt.subplot(2, 3, 3)
    plt.pcolormesh(Temp[0])
    plt.xlim([0, Temp.shape[2]])
    plt.ylim([0, Temp.shape[1]])
    plt.subplot(2, 3, 4)
    precip = data.variables['precip'][:]
    plt.plot(precip[:, 200, 200])
    solar = data.variables['solar'][:]
    plt.subplot(2, 3, 5)
    plt.plot(solar[:, 150, 150])
    longwave = data.variables['therm_rad'][:]
    plt.subplot(2, 3, 6)
    plt.plot(longwave[:, 150, 150])
    data.close()


if __name__ == '__main__':
    main()
