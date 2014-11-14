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
"""
from __future__ import division

from collections import OrderedDict
import glob
import logging
import os
import subprocess

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
wgrib2_logger = logging.getLogger('wgrib2')

context = zmq.Context()


# Corners of sub-region of GEM 2.5km operational forecast grid
# that enclose the watersheds (other than the Fraser River)
# that are used to calculate river flows for runoff forcing files
# for the Salish Sea NEMO model.
# The Fraser is excluded because real-time gauge data at Hope are
# available for it.
IST, IEN = 110, 365
JST, JEN = 20, 285


def main():
    # Prepare the worker
    parser = lib.basic_arg_parser(worker_name, description=__doc__)
    parsed_args = parser.parse_args()
    config = lib.load_config(parsed_args.config_file)
    lib.configure_logging(config, logger, parsed_args.debug)
    configure_wgrib2_logging(config)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {.config_file}'.format(parsed_args))
    lib.install_signal_handlers(logger, context)
    socket = lib.init_zmq_req_rep_worker(context, config, logger)
    # Do the work
    checklist = {}
    try:
        grib_to_netcdf(config, checklist)
        logger.info('NEMO-atmos forcing file creation completed')
        # Exchange success messages with the nowcast manager process
        tell_manager('success', config, socket, checklist)
    except subprocess.CalledProcessError:
        logger.critical('NEMO-atmos forcing file creation failed')
        tell_manager('failure', config, socket)
    # Finish up
    context.destroy()
    logger.info('task completed; shutting down')


def configure_wgrib2_logging(config):
    wgrib2_logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(
        config['logging']['wgrib2_log_file'], mode='w')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        config['logging']['message_format'],
        datefmt=config['logging']['datetime_format'])
    handler.setFormatter(formatter)
    wgrib2_logger.addHandler(handler)


def tell_manager(msg_type, config, socket, checklist=None):
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
    today = arrow.utcnow().to('Canada/Pacific')
    yesterday = today.replace(days=-1)
    ymd = today.strftime('y%Ym%md%d')
    p1 = os.path.join(yesterday.format('YYYYMMDD'), '18')
    p2 = os.path.join(today.format('YYYYMMDD'), '06')
    p3 = os.path.join(today.format('YYYYMMDD'), '18')
    logger.info('forecast sections: {} {} {}'.format(p1, p2, p3))
    fcst_section_hrs = OrderedDict([
        # (part, (dir, start hr, end hr))
        ('section 1', (p1, 24-18-1, 24+6-18)),
        ('section 2', (p2, 7-6, 18-6)),
        ('section 3', (p3, 19-18, 23-18)),
    ])

    rotate_grib_wind(config, fcst_section_hrs)
    collect_grib_scalars(config, fcst_section_hrs)
    outgrib, outzeros = concat_hourly_gribs(config, ymd, fcst_section_hrs)
    outgrib, outzeros = crop_to_watersheds(
        config, ymd, IST, IEN, JST, JEN, outgrib, outzeros)
    outnetcdf, out0netcdf = make_netCDF_files(config, ymd, outgrib, outzeros)
    calc_instantaneous(outnetcdf, out0netcdf, ymd)
    change_to_NEMO_variable_names(outnetcdf)
    netCDF4_deflate(outnetcdf)
    checklist.update({today.format('YYYY-MM-DD'): os.path.basename(outnetcdf)})

    plt.savefig('wg.png')


def run_wgrib2(cmd):
    """Run the wgrib2 command (cmd) in a subprocess and log its stdout
    and stderr to the wgrib2 logger. Catch errors from the subprocess,
    log them to the primary logger, and raise the exception for handling
    somewhere higher in the call stack.
    """
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        for line in output.split('\n'):
            if line:
                wgrib2_logger.debug(line)
    except subprocess.CalledProcessError as e:
        logger.error(
            'subprocess {cmd} failed with return code {status}'
            .format(cmd=cmd, status=e.returncode))
        for line in e.output.split('\n'):
            if line:
                logger.error(line)
        raise


def rotate_grib_wind(config, fcst_section_hrs):
    """Use wgrib2 to consolidate each hour's u and v wind components into a
    single file and then rotate the wind direction to geographical
    coordinates.
    """
    GRIBdir = config['weather']['GRIB_dir']
    wgrib2 = config['weather']['wgrib2']
    grid_defn = config['weather']['grid_defn.pl']
    # grid_defn.pl expects to find wgrib2 in the pwd,
    # create a symbolic link to keep it happy
    os.symlink(wgrib2, 'wgrib2')
    for day_fcst, start_hr, end_hr in fcst_section_hrs.values():
        for fhour in range(start_hr, end_hr + 1):
            # Set up directories and files
            sfhour = '{:03d}'.format(fhour)
            outuv = os.path.join(GRIBdir, day_fcst, sfhour, 'UV.grib')
            outuvrot = os.path.join(GRIBdir, day_fcst, sfhour, 'UVrot.grib')
            # Delete residual instances of files that are created so that
            # function can be re-run cleanly
            try:
                os.remove(outuv)
            except Exception:
                pass
            try:
                os.remove(outuvrot)
            except Exception:
                pass
            # Consolidate u and v wind component values into one file
            fn = glob.glob(os.path.join(GRIBdir, day_fcst, sfhour, '*UGRD*'))
            cmd = [wgrib2, fn[0], '-append', '-grib', outuv]
            run_wgrib2(cmd)
            fn = glob.glob(os.path.join(GRIBdir, day_fcst, sfhour, '*VGRD*'))
            cmd = [wgrib2, fn[0], '-append', '-grib', outuv]
            run_wgrib2(cmd)
            # rotate
            GRIDspec = subprocess.check_output([grid_defn, outuv])
            cmd = [wgrib2, outuv]
            cmd.extend('-new_grid_winds earth'.split())
            cmd.append('-new_grid')
            cmd.extend(GRIDspec.split())
            cmd.append(outuvrot)
            run_wgrib2(cmd)
            os.remove(outuv)
    os.unlink('wgrib2')
    logger.info('consolidated and rotated wind components')


def collect_grib_scalars(config, fcst_section_hrs):
    """Use wgrib2 and grid_defn.pl to consolidate each hour's scalar
    variables into an single file and then re-grid them to match the
    u and v wind components.
    """
    GRIBdir = config['weather']['GRIB_dir']
    wgrib2 = config['weather']['wgrib2']
    grid_defn = config['weather']['grid_defn.pl']
    # grid_defn.pl expects to find wgrib2 in the pwd,
    # create a symbolic link to keep it happy
    os.symlink(wgrib2, 'wgrib2')
    for day_fcst, start_hr, end_hr in fcst_section_hrs.values():
        for fhour in range(start_hr, end_hr + 1):
            # Set up directories and files
            sfhour = '{:03d}'.format(fhour)
            outscalar = os.path.join(GRIBdir, day_fcst, sfhour, 'scalar.grib')
            outscalargrid = os.path.join(
                GRIBdir, day_fcst, sfhour, 'gscalar.grib')
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
            for fn in glob.glob(os.path.join(GRIBdir, day_fcst, sfhour, '*')):
                if not ('GRD' in fn) and ('CMC' in fn):
                    cmd = [wgrib2, fn, '-append', '-grib', outscalar]
                    run_wgrib2(cmd)
            #  Re-grid
            GRIDspec = subprocess.check_output([grid_defn, outscalar])
            cmd = [wgrib2, outscalar]
            cmd.append('-new_grid')
            cmd.extend(GRIDspec.split())
            cmd.append(outscalargrid)
            run_wgrib2(cmd)
            os.remove(outscalar)
    os.unlink('wgrib2')
    logger.info('consolidated and re-gridded scalar variables')


def concat_hourly_gribs(config, ymd, fcst_section_hrs):
    """Concatenate in hour order the wind velocity components
    and scalar variables from hourly files into a daily file.

    Also create the zero-hour file that is used to initialize the
    calculation of instantaneous values from the forecast accumulated
    values.
    """
    GRIBdir = config['weather']['GRIB_dir']
    OPERdir = config['weather']['ops_dir']
    wgrib2 = config['weather']['wgrib2']
    outgrib = os.path.join(OPERdir, 'oper_allvar_{ymd}.grib'.format(ymd=ymd))
    outzeros = os.path.join(OPERdir, 'oper_000_{ymd}.grib'.format(ymd=ymd))
    # Delete residual instances of files that are created so that
    # function can be re-run cleanly
    try:
        os.remove(outgrib)
    except Exception:
        pass
    try:
        os.remove(outzeros)
    except Exception:
        pass
    for section, (day_fcst, start_hr, end_hr) in fcst_section_hrs.items():
        for fhour in range(start_hr, end_hr + 1):
            # Set up directories and files
            sfhour = '{:03d}'.format(fhour)
            outuvrot = os.path.join(GRIBdir, day_fcst, sfhour, 'UVrot.grib')
            outscalargrid = os.path.join(
                GRIBdir, day_fcst, sfhour, 'gscalar.grib')
            if section == 'section 1' and fhour == 5:
                cmd = [wgrib2, outuvrot, '-append', '-grib', outzeros]
                run_wgrib2(cmd)
                cmd = [wgrib2, outscalargrid, '-append', '-grib', outzeros]
                run_wgrib2(cmd)
            else:
                cmd = [wgrib2, outuvrot, '-append', '-grib', outgrib]
                run_wgrib2(cmd)
                cmd = [wgrib2, outscalargrid, '-append', '-grib', outgrib]
                run_wgrib2(cmd)
            os.remove(outuvrot)
            os.remove(outscalargrid)
    logger.info(
        'concatenated variables in hour order from hourly files '
        'to daily file {}'.format(outgrib))
    logger.info(
        'created zero-hour file for initialization of accumulated -> '
        'instantaneous values calculations: {}'.format(outzeros))
    return outgrib, outzeros


def crop_to_watersheds(config, ymd, ist, ien, jst, jen, outgrib, outzeros):
    """Crop the grid to the sub-region of GEM 2.5km operational forecast
    grid that encloses the watersheds that are used to calculate river
    flows for runoff forcing files for the Salish Sea NEMO model.
    """
    OPERdir = config['weather']['ops_dir']
    wgrib2 = config['weather']['wgrib2']
    newgrib = os.path.join(
        OPERdir, 'oper_allvar_small_{ymd}.grib'.format(ymd=ymd))
    newzeros = os.path.join(
        OPERdir, 'oper_000_small_{ymd}.grib'.format(ymd=ymd))
    istr = '{ist}:{ien}'.format(ist=ist, ien=ien)
    jstr = '{jst}:{jen}'.format(jst=jst, jen=jen)
    cmd = [wgrib2, outgrib, '-ijsmall_grib', istr, jstr, newgrib]
    run_wgrib2(cmd)
    logger.info(
        'cropped hourly file to watersheds sub-region: {}'
        .format(newgrib))
    cmd = [wgrib2, outzeros, '-ijsmall_grib', istr, jstr, newzeros]
    run_wgrib2(cmd)
    logger.info(
        'cropped zero-hour file to watersheds sub-region: {}'
        .format(newgrib))
    os.remove(outgrib)
    os.remove(outzeros)
    return newgrib, newzeros


def make_netCDF_files(config, ymd, outgrib, outzeros):
    """Convert the GRIB files to netcdf (classic) files.
    """
    OPERdir = config['weather']['ops_dir']
    wgrib2 = config['weather']['wgrib2']
    outnetcdf = os.path.join(OPERdir, 'ops_{ymd}.nc'.format(ymd=ymd))
    out0netcdf = os.path.join(OPERdir, 'oper_000_{ymd}.nc'.format(ymd=ymd))
    cmd = [wgrib2, outgrib, '-netcdf', outnetcdf]
    run_wgrib2(cmd)
    logger.info(
        'created hourly netCDF classic file: {}'
        .format(outnetcdf))
    cmd = [wgrib2, outzeros, '-netcdf', out0netcdf]
    run_wgrib2(cmd)
    logger.info(
        'created zero-hour netCDF classic file: {}'
        .format(out0netcdf))
    os.remove(outgrib)
    os.remove(outzeros)
    return outnetcdf, out0netcdf


def calc_instantaneous(outnetcdf, out0netcdf, ymd):
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
    data0.close()
    os.remove(out0netcdf)

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
    logger.info(
        'calculated instantaneous values from forecast accumulated values '
        'for precipitation and long- & short-wave radiation')


def change_to_NEMO_variable_names(outnetcdf):
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
    logger.info('changed variable names to their NEMO names')

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


def netCDF4_deflate(outnetcdf):
    """Run ncks in a subprocess to convert outnetcdf to netCDF4 format
    with it variables compressed with Lempel-Ziv deflation.
    """
    cmd = ['ncks', '-4', '-L4', '-O', outnetcdf, outnetcdf]
    try:
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        if output:
            for line in output.split('\n'):
                if line:
                    logger.info(line)
        else:
            logger.info('netCDF4 deflated {}'.format(outnetcdf))
    except subprocess.CalledProcessError as e:
        logger.error(
            'subprocess {cmd} failed with return code {status}'
            .format(cmd=cmd, status=e.returncode))
        for line in e.output.split('\n'):
            if line:
                logger.error(line)
        raise


if __name__ == '__main__':
    main()
