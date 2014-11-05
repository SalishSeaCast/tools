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
"""
import logging
import os
import sys
import urllib

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
FORECAST_DURATION = 42  # hours


def main(args):
    parser = lib.basic_arg_parser()
    parsed_args = parser.parse_args()
    config = lib.load_config(parsed_args.config_file)
    lib.configure_logging(config, logger)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {.config_file}'.format(parsed_args))
    lib.install_signal_handlers(logger, context)
    socket = lib.init_zmq_req_rep_worker(context, config, logger)
    forecast = args[1]
    try:
        get_grib(forecast, config)
        exit_msg = 'weather forecast downloads complete'
    except OSError:
        exit_msg = 'weather forecast downloads failed'
    finally:
        context.destroy()
        logger.info('{}; shutting down'.format(exit_msg))


def get_grib(forecast, config):
    utc = arrow.utcnow()
    now = utc.to('Canada/Pacific')
    date = now.format('YYYYMMDD')
    logger.info(
        'downloading {forecast} forecast GRIB2 files for {date}'
        .format(forecast=forecast, date=date))

    dest_dir_root = config['weather']['GRIB_dir']
    os.chdir(dest_dir_root)
    try:
        os.mkdir(date, 509)  # octal 775 = 'rwxrwxr-x'
    except OSError:
        pass
    os.chdir(date)
    try:
        os.mkdir(forecast, 509)  # octal 775 = 'rwxrwxr-x'
    except OSError:
        forecast_path = os.path.join(dest_dir_root, date, forecast)
        msg = (
            '{} directory already exists; not overwriting'
            .format(forecast_path))
        logger.error(msg)
        raise OSError(msg)
    os.chdir(forecast)

    for fhour in range(0, FORECAST_DURATION+1):
        sfhour = '{:0=3}'.format(fhour)
        try:
            os.mkdir(sfhour, 509)  # octal 775 = 'rwxrwxr-x'
        except OSError:
            sfhour_path = os.path.join(dest_dir_root, date, forecast, sfhour)
            msg = (
                '{} directory already exists; not overwriting'
                .format(sfhour_path))
            logger.error(msg)
            raise OSError(msg)
        os.chdir(sfhour)

        for v in GRIB_VARIABLES:
            filename = FILENAME_TEMPLATE.format(
                variable=v, date=date, forecast=forecast, hour=sfhour)
            fileURL = URL_TEMPLATE.format(
                forecast=forecast, hour=sfhour, filename=filename)
            _, http_msg = urllib.urlretrieve(fileURL, filename)
            logger.info(
                'downloaded {bytes} bytes from {fileURL}'.format(
                    bytes=http_msg.getheader('Content-Length'),
                    fileURL=fileURL))
            os.chmod(filename, 436)  # octial 664 = 'rw-rw-r--'
        os.chdir('..')
    os.chdir('..')


if __name__ == '__main__':
    main(sys.argv[1:])
