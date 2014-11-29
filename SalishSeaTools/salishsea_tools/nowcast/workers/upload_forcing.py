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

"""Salish Sea NEMO nowcast worker that uploads the forcing files
for a nowcast run to the HPC/cloud facility where the run will be
executed.
"""
import argparse
import logging
import os
import traceback

import arrow
import zmq

from salishsea_tools.nowcast import lib
from salishsea_tools.nowcast.workers import (
    get_NeahBay_ssh,
    grib_to_netcdf,
    make_runoff_file,
)


worker_name = lib.get_module_name()

logger = logging.getLogger(worker_name)

context = zmq.Context()


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
    try:
        checklist = upload_forcing(
            parsed_args.host_name, parsed_args.run_date, config, socket)
        logger.info(
            'forcing files upload to {.host_name} completed'
            .format(parsed_args))
        # Exchange success messages with the nowcast manager process
        lib.tell_manager(
            worker_name, 'success', config, logger, socket, checklist)
    except lib.WorkerError:
        logger.critical(
            'forcing files upload to {.host_name} failed'.format(parsed_args))
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


def configure_argparser(prog, description, parents):
    parser = argparse.ArgumentParser(
        prog=prog, description=description, parents=parents)
    parser.add_argument(
        'host_name', help='Name of the host to upload forcing files to')
    parser.add_argument(
        '--run-date', type=lib.arrow_date,
        default=arrow.now().date(),
        help='''
        Date of the run to download results files from;
        defaults to %(default)s.
        ''',
    )
    return parser


def upload_forcing(host_name, run_date, config, socket):
    host = config['run'][host_name]
    ssh_client, sftp_client = lib.sftp(host_name)
    # Neah Bay sea sureface height
    for day in range(-1, 3):
        filename = get_NeahBay_ssh.FILENAME_TMPL.format(
            run_date.replace(days=day).date())
        dest_dir = 'obs' if day == -1 else 'fcst'
        localpath = os.path.join(config['ssh']['ssh_dir'], dest_dir, filename)
        remotepath = os.path.join(host['ssh_dir'], dest_dir, filename)
        upload_file(sftp_client, host_name, localpath, remotepath)
    # Rivers runoff
    filename = make_runoff_file.FILENAME_TMPL.format(
        run_date.replace(days=-1).date())
    localpath = os.path.join(config['rivers']['rivers_dir'], filename)
    remotepath = os.path.join(host['rivers_dir'], filename)
    upload_file(sftp_client, host_name, localpath, remotepath)
    # # Weather
    for day in range(3):
        filename = grib_to_netcdf.FILENAME_TMPL.format(
            run_date.replace(days=day).date())
        dest_dir = '' if day == 0 else 'fcst'
        localpath = os.path.join(
            config['weather']['ops_dir'], dest_dir, filename)
        remotepath = os.path.join(host['weather_dir'], dest_dir, filename)
        upload_file(sftp_client, host_name, localpath, remotepath)
    sftp_client.close()
    ssh_client.close()
    return True


def upload_file(sftp_client, host_name, localpath, remotepath):
    sftp_client.put(localpath, remotepath)
    sftp_client.chmod(remotepath, lib.PERMS_RW_RW_R)
    logger.debug(
        '{local} uploaded to {host} at {remote}'
        .format(local=localpath, host=host_name, remote=remotepath))


if __name__ == '__main__':
    main()
