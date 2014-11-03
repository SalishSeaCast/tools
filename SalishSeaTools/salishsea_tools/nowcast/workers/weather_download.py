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


logger = logging.getLogger('weather_download')

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


def main(args):
    config_file = args[0]
    config = lib.load_config(config_file)
    lib.configure_logging(config, logger)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {}'.format(config_file))
    lib.install_signal_handlers(logger, context)
    socket = lib.init_zmq_worker(context, config, logger)
    forecast = args[1]
    get_grib(forecast, config)
    context.destroy()
    logger.info()


def get_grib(forecast, config):
    utc = arrow.utcnow()
    now = utc.to('Canada/Pacific')
    date = now.format('YYYYMMDD')
    logger.info(
        'downloading {forecast} forecast GRIB2 files for {date}'
        .format(forecast=forecast, date=date))
    dest_dir_root = config['weather']['GRIB_dir']
    os.chdir(dest_dir_root)
    if forecast == '06':
        os.mkdir(date)
    os.chdir(date)
    os.mkdir(forecast)
    os.chdir(forecast)
    for fhour in range(0, 42+1):
        sfhour = '{:0=3}'.format(fhour)
        os.mkdir(sfhour)
        os.chdir(sfhour)
        for v in GRIB_VARIABLES:
            filename = FILENAME_TEMPLATE.format(
                variable=v, date=date, forecast=forecast, hour=sfhour)
            fileURL = URL_TEMPLATE.format(
                forecast=forecast, hour=sfhour, filename=filename)
            urllib.urlretrieve(fileURL, filename)
        os.chdir('..')
    os.chdir('..')


if __name__ == '__main__':
    main(sys.argv[1:])
