# Copyright 2013-2015 The Salish Sea MEOPAR contributors
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

"""Salish Sea NEMO nowcast special upload forcing files worker.
Upload the forcing files for a nowcast or forecast run to the HPC/cloud
facility where the run will be executed assuming that the previous
runs were not executed there.

**This worker is intended primarily for recovering from nowcast automation
failures.**
"""
import glob
import logging
import os

import arrow

from .. import lib
from ..nowcast_worker import NowcastWorker
from . import (
    get_NeahBay_ssh,
    grib_to_netcdf,
    make_runoff_file,
)


worker_name = lib.get_module_name()
logger = logging.getLogger(worker_name)


def main():
    worker = NowcastWorker(worker_name, description=__doc__)
    worker.arg_parser.add_argument(
        'host_name', help='Name of the host to upload files to')
    salishsea_today = arrow.now('Canada/Pacific').floor('day')
    worker.arg_parser.add_argument(
        '--run-date', type=lib.arrow_date,
        default=salishsea_today,
        help='''
        Date of the run to upload files for; use YYYY-MM-DD format.
        Defaults to {}.
        '''.format(salishsea_today.format('YYYY-MM-DD')),
    )
    worker.run(upload_all_files, success, failure)


def success(parsed_args):
    logger.info(
        'uoload of ALL nowcast files to {.host_name} completed'
        .format(parsed_args))
    msg_type = 'success'
    return msg_type


def failure(parsed_args):
    logger.error(
        'uoload of ALL nowcast files to {.host_name} failed'
        .format(parsed_args))
    msg_type = 'failure'
    return msg_type


def upload_all_files(host_name, run_date, config):
    host = config['run'][host_name]
    ssh_client, sftp_client = lib.sftp(
        host_name, host['ssh key name']['nowcast'])
    # Neah Bay sea surface height
    for day in range(-1, 2):
        filename = get_NeahBay_ssh.FILENAME_TMPL.format(
            run_date.replace(days=day).date())
        dest_dir = 'obs' if day == -1 else 'fcst'
        localpath = os.path.join(config['ssh']['ssh_dir'], dest_dir, filename)
        remotepath = os.path.join(host['ssh_dir'], dest_dir, filename)
        try:
            _upload_file(sftp_client, host_name, localpath, remotepath)
        except OSError:
            if dest_dir != 'obs':
                raise
            # obs file does not exist, to create symlink to corresponding
            # forecast file
            fcst = os.path.join(config['ssh']['ssh_dir'], 'fcst', filename)
            os.symlink(fcst, localpath)
            logger.warning(
                'ssh obs file not found; created symlink to {}'.format(fcst))
            _upload_file(sftp_client, host_name, localpath, remotepath)
    # Rivers runoff
    for day in range(-1, 0):
        filename = make_runoff_file.FILENAME_TMPL.format(
            run_date.replace(days=day).date())
        localpath = os.path.join(config['rivers']['rivers_dir'], filename)
        remotepath = os.path.join(host['rivers_dir'], filename)
        _upload_file(sftp_client, host_name, localpath, remotepath)
    # Weather
    for day in range(-1, 2):
        filename = grib_to_netcdf.FILENAME_TMPL.format(
            run_date.replace(days=day).date())
        dest_dir = '' if day <= 0 else 'fcst'
        localpath = os.path.join(
            config['weather']['ops_dir'], dest_dir, filename)
        remotepath = os.path.join(host['weather_dir'], dest_dir, filename)
        _upload_file(sftp_client, host_name, localpath, remotepath)
    # Restart File
    prev_run_id = run_date.replace(days=-1).date()
    prev_run_dir = prev_run_id.strftime('%d%b%y').lower()
    local_dir = os.path.join(
        config['run']['results archive']['nowcast'], prev_run_dir)
    localpath = glob.glob(os.path.join(local_dir, '*restart.nc'))
    filename = os.path.basename(localpath[0])
    remote_dir = os.path.join(host['results']['nowcast'], prev_run_dir)
    remotepath = os.path.join(remote_dir, filename)
    _make_remote_directory(sftp_client, host_name, remote_dir)
    _upload_file(sftp_client, host_name, localpath[0], remotepath)
    sftp_client.close()
    ssh_client.close()
    return {host_name: True}


def _upload_file(sftp_client, host_name, localpath, remotepath):
    sftp_client.put(localpath, remotepath)
    sftp_client.chmod(remotepath, lib.PERMS_RW_RW_R)
    logger.debug(
        '{local} uploaded to {host} at {remote}'
        .format(local=localpath, host=host_name, remote=remotepath))


def _make_remote_directory(sftp_client, host_name, remote_dir):
    sftp_client.mkdir(remote_dir, mode=lib.PERMS_RWX_RWX_R_X)
    logger.debug(
        '{remote} directory made on {host}'
        .format(remote=remote_dir, host=host_name))


if __name__ == '__main__':
    main()
