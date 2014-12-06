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

"""Salish Sea NEMO nowcast weather model dataset download worker.
Download the GRIB2 files from today's 06 or 18 EC GEM 2.5km operational
model forecast.
"""
import argparse
import logging
import os
import traceback

import arrow
import zmq

from salishsea_tools.nowcast import lib


worker_name = lib.get_module_name()

logger = logging.getLogger(worker_name)

context = zmq.Context()


GRIB_VARIABLES = (
    'UGRD_TGL_10_',  # u component of wind velocity at 10m elevation
    'VGRD_TGL_10_',  # v component of wind velocity at 10m elevation
    'DSWRF_SFC_0_',  # accumulated downward shortwave (solar) radiation
                     # at ground level
    'DLWRF_SFC_0_',  # accumulated downward longwave (thermal) radiation
                     # at ground level
    'TMP_TGL_2_',    # air temperature at 2m elevation
    'SPFH_TGL_2_',   # specific humidity at 2m elevation
    'APCP_SFC_0_',   # accumulated precipitation at ground level
    'PRMSL_MSL_0_',  # atmospheric pressure at mean sea level
)
URL_TEMPLATE = (
    'http://dd.weather.gc.ca/model_hrdps/west/grib2/{forecast}/{hour}/{filename}'
)
FILENAME_TEMPLATE = (
    'CMC_hrdps_west_{variable}ps2.5km_{date}{forecast}_P{hour}-00.grib2'
)
FORECAST_DURATION = 48  # hours


def main():
    # Prepare the worker
    base_parser = lib.basic_arg_parser(
        worker_name, description=__doc__, add_help=False)
    parser = configure_argparser(
        prog=base_parser.prog,
        description=base_parser.description,
        parents=[base_parser],
    )
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
        get_grib(parsed_args.forecast, config, checklist)
        logger.info(
            'weather forecast {.forecast} downloads complete'
            .format(parsed_args))
        # Exchange success messages with the nowcast manager process
        msg_type = '{} {}'.format('success', parsed_args.forecast)
        lib.tell_manager(
            worker_name, msg_type, config, logger, socket, checklist)
    except lib.WorkerError:
        logger.error(
            'weather forecast {.forecast} downloads failed'
            .format(parsed_args))
        msg_type = '{} {}'.format('failure', parsed_args.forecast)
        # Exchange failure messages with nowcast manager process
        lib.tell_manager(worker_name, msg_type, config, logger, socket)
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


def configure_argparser(prog, description, parents):
    parser = argparse.ArgumentParser(
        prog=prog, description=description, parents=parents)
    parser.add_argument(
        'forecast', choices=set(('00', '06', '12', '18')),
        help='Name of forecast to download files from.',
    )
    return parser


def get_grib(forecast, config, checklist):
    utc = arrow.utcnow()
    utc = utc.replace(hours=-int(forecast))
    date = utc.format('YYYYMMDD')
    logger.info(
        'downloading {forecast} forecast GRIB2 files for {date}'
        .format(forecast=forecast, date=date))
    dest_dir_root = config['weather']['GRIB_dir']
    os.chdir(dest_dir_root)
    lib.mkdir(date, logger, grp_name=config['file group'])
    os.chdir(date)
    lib.mkdir(forecast, logger, grp_name=config['file group'], exist_ok=False)
    os.chdir(forecast)
    for fhour in range(1, FORECAST_DURATION+1):
        sfhour = '{:0=3}'.format(fhour)
        lib.mkdir(
            sfhour, logger, grp_name=config['file group'], exist_ok=False)
        os.chdir(sfhour)
        for v in GRIB_VARIABLES:
            filename = FILENAME_TEMPLATE.format(
                variable=v, date=date, forecast=forecast, hour=sfhour)
            fileURL = URL_TEMPLATE.format(
                forecast=forecast, hour=sfhour, filename=filename)
            headers = lib.get_web_data(
                fileURL, logger, filename, retry_time_limit=9000)
            logger.debug(
                'downloaded {bytes} bytes from {fileURL}'.format(
                    bytes=headers['Content-Length'],
                    fileURL=fileURL))
            lib.fix_perms(filename)
        os.chdir('..')
    os.chdir('..')
    checklist.update({'{} forecast'.format(forecast): True})


if __name__ == '__main__':
    main()
