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
import grp
import logging
import os
import subprocess
import traceback

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
# Position of Sandheads
SandI, SandJ = 151, 136

#: Weather forcing file name template
FILENAME_TMPL = 'ops_{:y%Ym%md%d}.nc'


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
        lib.tell_manager(
            worker_name, 'success', config, logger, socket, checklist)
    except lib.WorkerError:
        logger.critical('NEMO-atmos forcing file creation failed')
        # Exchange failure messages with the nowcast manager process
        lib.tell_manager(worker_name, 'failure', config, logger, socket)
    except SystemExit:
        # Normal termination
        pass
    except:
        logger.critical('unhandled exception:')
        for line in traceback.format_exc().splitlines():
            logger.error(line)
        # Exchange crash messages with the nowcast manager process
        lib.tell_manager(worker_name, 'crash', config, logger, socket)
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


def grib_to_netcdf(config, checklist):
    """Collect weather forecast results from hourly GRIB2 files
    and produces day-long NEMO atmospheric forcing netCDF files.
    """
    today = arrow.utcnow().to('Canada/Pacific')
    yesterday = today.replace(days=-1)
    tomorrow = today.replace(days=+1)
    nextday = today.replace(days=+2)
    fcst_section_hrs_arr = [OrderedDict() for x in range(3)]

    # today
    p1 = os.path.join(yesterday.format('YYYYMMDD'), '18')
    p2 = os.path.join(today.format('YYYYMMDD'), '00')
    p3 = os.path.join(today.format('YYYYMMDD'), '12')
    logger.info('forecast sections: {} {} {}'.format(p1, p2, p3))
    fcst_section_hrs_arr[0] = OrderedDict([
        # (part, (dir, real start hr, forecast start hr, end hr))
        ('section 1', (p1, -1, 24-18-1, 24-18+0)),
        ('section 2', (p2, 1, 1-0, 12-0)),
        ('section 3', (p3, 13, 13-12, 23-12)),
    ])
    zerostart = [[1, 13]]
    length = [24]
    subdirectory = ['']
    yearmonthday = [today.strftime('y%Ym%md%d')]

    # tomorrow (forecast)
    p1 = os.path.join(today.format('YYYYMMDD'), '12')
    logger.info('tomorrow forecast section: {}'.format(p1))
    fcst_section_hrs_arr[1] = OrderedDict([
        # (part, (dir, start hr, end hr))
        ('section 1', (p1, -1, 24-12-1, 24+23-12)),
    ])
    zerostart.extend([[]])
    length.extend([24])
    subdirectory.extend(['fcst'])
    yearmonthday.extend([tomorrow.strftime('y%Ym%md%d')])

    # next day (forecast)
    p1 = os.path.join(today.format('YYYYMMDD'), '12')
    logger.info('next day forecast section: {}'.format(p1))
    fcst_section_hrs_arr[2] = OrderedDict([
        # (part, (dir, start hr, end hr))
        ('section 1', (p1, -1, 24+24-12-1, 24+24+12-12)),
    ])
    zerostart.extend([[]])
    length.extend([13])
    subdirectory.extend(['fcst'])
    yearmonthday.extend([nextday.strftime('y%Ym%md%d')])

    # set-up plotting
    fig, axs, ip = set_up_plotting()
    # define group
    gid = grp.getgrnam(config['file group']).gr_gid


    for fcst_section_hrs, zstart, flen, subdir, ymd in zip(
            fcst_section_hrs_arr, zerostart, length, subdirectory,
            yearmonthday):
        rotate_grib_wind(config, fcst_section_hrs)
        collect_grib_scalars(config, fcst_section_hrs)
        outgrib, outzeros = concat_hourly_gribs(config, ymd, fcst_section_hrs)
        outgrib, outzeros = crop_to_watersheds(
            config, ymd, IST, IEN, JST, JEN, outgrib, outzeros)
        outnetcdf, out0netcdf = make_netCDF_files(config, ymd, subdir,
                                                  outgrib, outzeros, gid)
        calc_instantaneous(outnetcdf, out0netcdf, ymd, flen, zstart,
                           axs)
        change_to_NEMO_variable_names(outnetcdf, axs, ip)
        ip += 1

        netCDF4_deflate(outnetcdf)
        try:
            os.chown(outnetcdf, -1, gid)
            os.chmod(outnetcdf, lib.PERMS_RWX_RWX_R_W)
        except:
            # don't own file so permissions are correct already
            pass
        if subdir in checklist:
            checklist[subdir].append(os.path.basename(outnetcdf))
        else:
            if subdir:
                checklist[subdir] = [os.path.basename(outnetcdf)]
            else:
                checklist.update({subdir: os.path.basename(outnetcdf)})
    axs[2, 0].legend(loc='upper left')
    fig.savefig('wg.png')


def rotate_grib_wind(config, fcst_section_hrs):
    """Use wgrib2 to consolidate each hour's u and v wind components into a
    single file and then rotate the wind direction to geographical
    coordinates.
    """
    GRIBdir = config['weather']['GRIB_dir']
    wgrib2 = config['weather']['wgrib2']
    grid_defn = config['weather']['grid_defn.pl']
    # grid_defn.pl expects to find wgrib2 in the pwd,
    # create a symbolic link to keep it happy (if its not already there)
    try:
        os.symlink(wgrib2, 'wgrib2')
    except OSError:
        pass
    for day_fcst, realstart, start_hr, end_hr in fcst_section_hrs.values():
        for fhour in range(start_hr, end_hr + 1):
            # Set up directories and files
            sfhour = '{:03d}'.format(fhour)
            outuv = os.path.join(GRIBdir, day_fcst, sfhour, 'UV.grib')
            outuvrot = os.path.join(GRIBdir, day_fcst, sfhour, 'UVrot.grib')
            # Delete residual instances of files that are created so that
            # function can be re-run cleanly
            try:
                os.remove(outuv)
            except OSError:
                pass
            try:
                os.remove(outuvrot)
            except OSError:
                pass
            # Consolidate u and v wind component values into one file
            fn = glob.glob(os.path.join(GRIBdir, day_fcst, sfhour, '*UGRD*'))
            cmd = [wgrib2, fn[0], '-append', '-grib', outuv]
            lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
            fn = glob.glob(os.path.join(GRIBdir, day_fcst, sfhour, '*VGRD*'))
            cmd = [wgrib2, fn[0], '-append', '-grib', outuv]
            lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
            # rotate
            GRIDspec = subprocess.check_output([grid_defn, outuv])
            cmd = [wgrib2, outuv]
            cmd.extend('-new_grid_winds earth'.split())
            cmd.append('-new_grid')
            cmd.extend(GRIDspec.split())
            cmd.append(outuvrot)
            lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
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
    for day_fcst,  realstart, start_hr, end_hr in fcst_section_hrs.values():
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
            except OSError:
                pass
            try:
                os.remove(outscalargrid)
            except OSError:
                pass
            # Consolidate scalar variables into one file
            for fn in glob.glob(os.path.join(GRIBdir, day_fcst, sfhour, '*')):
                if not ('GRD' in fn) and ('CMC' in fn):
                    cmd = [wgrib2, fn, '-append', '-grib', outscalar]
                    lib.run_in_subprocess(
                        cmd, wgrib2_logger.debug, logger.error)
            #  Re-grid
            GRIDspec = subprocess.check_output([grid_defn, outscalar])
            cmd = [wgrib2, outscalar]
            cmd.append('-new_grid')
            cmd.extend(GRIDspec.split())
            cmd.append(outscalargrid)
            lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
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
    except OSError:
        pass
    try:
        os.remove(outzeros)
    except OSError:
        pass
    for day_fcst,  realstart, start_hr, end_hr in fcst_section_hrs.values():
        for fhour in range(start_hr, end_hr + 1):
            # Set up directories and files
            sfhour = '{:03d}'.format(fhour)
            outuvrot = os.path.join(GRIBdir, day_fcst, sfhour, 'UVrot.grib')
            outscalargrid = os.path.join(
                GRIBdir, day_fcst, sfhour, 'gscalar.grib')
            if (fhour == start_hr and realstart == -1):
                cmd = [wgrib2, outuvrot, '-append', '-grib', outzeros]
                lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
                cmd = [wgrib2, outscalargrid, '-append', '-grib', outzeros]
                lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
            else:
                cmd = [wgrib2, outuvrot, '-append', '-grib', outgrib]
                lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
                cmd = [wgrib2, outscalargrid, '-append', '-grib', outgrib]
                lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
            os.remove(outuvrot)
            os.remove(outscalargrid)
    logger.info(
        'concatenated variables in hour order from hourly files '
        'to daily file {}'.format(outgrib))
    logger.info(
        'created zero-hour file for initialization of accumulated -> '
        'instantaneous values calculations: {}'.format(outzeros))
    return outgrib, outzeros


def crop_to_watersheds(config, ymd, ist, ien, jst, jen, outgrib,
                       outzeros):
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
    lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
    logger.info(
        'cropped hourly file to watersheds sub-region: {}'
        .format(newgrib))
    cmd = [wgrib2, outzeros, '-ijsmall_grib', istr, jstr, newzeros]
    lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
    logger.info(
        'cropped zero-hour file to watersheds sub-region: {}'
        .format(newgrib))
    os.remove(outgrib)
    os.remove(outzeros)
    return newgrib, newzeros


def make_netCDF_files(config, ymd, subdir, outgrib, outzeros, gid):
    """Convert the GRIB files to netcdf (classic) files.
    """
    OPERdir = config['weather']['ops_dir']
    wgrib2 = config['weather']['wgrib2']
    outnetcdf = os.path.join(OPERdir, subdir, 'ops_{ymd}.nc'.format(ymd=ymd))
    out0netcdf = os.path.join(OPERdir, subdir,
                              'oper_000_{ymd}.nc'.format(ymd=ymd))
    cmd = [wgrib2, outgrib, '-netcdf', outnetcdf]
    lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
    logger.info(
        'created hourly netCDF classic file: {}'
        .format(outnetcdf))
    try:
        os.chown(outnetcdf, -1, gid)
        os.chmod(outnetcdf, 436)  # octal 664 = 'rw-rw-r--'
    except OSError:
        # File isn't owned by current user, but that's okay
        pass
    cmd = [wgrib2, outzeros, '-netcdf', out0netcdf]
    lib.run_in_subprocess(cmd, wgrib2_logger.debug, logger.error)
    logger.info(
        'created zero-hour netCDF classic file: {}'
        .format(out0netcdf))
    os.remove(outgrib)
    os.remove(outzeros)
    return outnetcdf, out0netcdf


def calc_instantaneous(outnetcdf, out0netcdf, ymd, flen, zstart, axs):
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

    axs[1, 0].plot(acc_values['acc']['APCP_surface'][:, SandI, SandJ], 'o-')

    for var in acc_vars:
        acc_values['inst'][var][0] = (
            acc_values['acc'][var][0] - acc_values['zero'][var][0]) / 3600
        for realhour in range(1, flen):
            if realhour in zstart:
                acc_values['inst'][var][realhour] = (
                    acc_values['acc'][var][realhour] / 3600)
            else:
                acc_values['inst'][var][realhour] = (
                    acc_values['acc'][var][realhour]
                    - acc_values['acc'][var][realhour-1]) / 3600

    axs[1, 1].plot(
        acc_values['inst']['APCP_surface'][:, SandI, SandJ], 'o-',
        label=ymd)

    for var in acc_vars:
        data.variables[var][:] = acc_values['inst'][var][:]
    data.close()
    logger.info(
        'calculated instantaneous values from forecast accumulated values '
        'for precipitation and long- & short-wave radiation')


def change_to_NEMO_variable_names(outnetcdf, axs, ip):
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
    axs[0, ip].pcolormesh(Temp[0])
    axs[0, ip].set_xlim([0, Temp.shape[2]])
    axs[0, ip].set_ylim([0, Temp.shape[1]])
    axs[0, ip].plot(SandI, SandJ, 'wo')

    if ip == 0:
        label = "day 1"
    elif ip == 1:
        label = "day 2"
    else:
        label = "day 3"
    humid = data.variables['qair'][:]
    axs[1, 2].plot(humid[:, SandI, SandJ], '-o')
    solar = data.variables['solar'][:]
    axs[2, 0].plot(solar[:, SandI, SandJ], '-o', label=label)
    longwave = data.variables['therm_rad'][:]
    axs[2, 1].plot(longwave[:, SandI, SandJ], '-o')
    pres = data.variables['atmpres'][:]
    axs[2, 2].plot(pres[:, SandI, SandJ], '-o')
    uwind = data.variables['u_wind'][:]
    axs[3, 0].plot(uwind[:, SandI, SandJ], '-o')
    vwind = data.variables['v_wind'][:]
    axs[3, 1].plot(vwind[:, SandI, SandJ], '-o')
    axs[3, 2].plot(np.sqrt(
        uwind[:, SandI, SandJ]**2 + vwind[:, SandI, SandJ]**2), '-o')

    data.close()


def netCDF4_deflate(outnetcdf):
    """Run ncks in a subprocess to convert outnetcdf to netCDF4 format
    with it variables compressed with Lempel-Ziv deflation.
    """
    cmd = ['ncks', '-4', '-L4', '-O', outnetcdf, outnetcdf]
    try:
        lib.run_in_subprocess(cmd, logger.debug, logger.error)
        logger.info('netCDF4 deflated {}'.format(outnetcdf))
    except lib.WorkerError:
        raise


def set_up_plotting():
    fig, axs = plt.subplots(4, 3, figsize=(10, 15))
    axs[0, 0].set_title('Air Temp. 0 hr')
    axs[0, 1].set_title('Air Temp. +1 day')
    axs[0, 2].set_title('Air Temp. +2 days')
    axs[1, 0].set_title('Accumulated Precip')
    axs[1, 1].set_title('Instant. Precip')
    axs[1, 2].set_title('Humidity')
    axs[2, 0].set_title('Solar Rad')
    axs[2, 1].set_title('Longwave Down')
    axs[2, 2].set_title('Sea Level Pres')
    axs[3, 0].set_title('u wind')
    axs[3, 1].set_title('v wind')
    axs[3, 2].set_title('Wind Speed')
    ip = 0
    return fig, axs, ip


if __name__ == '__main__':
    main()
