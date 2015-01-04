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

"""Salish Sea NEMO nowcast worker that monitors and reports on the
progress of a run in the cloud computing facility.
"""
import argparse
import errno
import logging
import os
import time
import traceback

import zmq

from salishsea_tools.nowcast import lib


worker_name = lib.get_module_name()

logger = logging.getLogger(worker_name)

context = zmq.Context()


POLL_INTERVAL = 5 * 60  # seconds


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
    socket = lib.init_zmq_req_rep_worker(
        context, config, logger, config['zmq']['server'])
    # Do the work
    host_name = config['run']['cloud host']
    try:
        checklist = watch_NEMO(
            parsed_args.run_type, parsed_args.pid, config, socket)
        logger.info(
            '{.run_type} NEMO run in {host_name} completed'
            .format(parsed_args, host_name=host_name))
        # Exchange success messages with the nowcast manager process
        msg_type = 'success {.run_type}'.format(parsed_args)
        lib.tell_manager(
            worker_name, msg_type, config, logger, socket, checklist)
    except lib.WorkerError:
        logger.critical(
            '{.run_type} NEMO run in {host_name} failed'
            .format(parsed_args, host_name=host_name))
        # Exchange failure messages with the nowcast manager process
        msg_type = 'failure {.run_type}'.format(parsed_args)
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
        'run_type', choices=set(('nowcast', 'forecast')),
        help='Type of run to execute.'
    )
    parser.add_argument(
        'pid', type=int,
        help='PID of the NEMO run bash script to monitor.'
    )
    return parser


def watch_NEMO(run_type, pid, config, socket):
    # Ensure that the run is in progress
    if not pid_exists(pid):
        msg = 'NEMO run pid {} does not exist'.format(pid)
        logger.error(msg)
        lib.tell_manager(worker_name, 'log.error', config, logger, socket, msg)
        raise lib.WorkerError()
    # Watch for the run bash script process to end
    while pid_exists(pid):
        # TODO: report on progress of the run via logging
        msg = 'pid {} exists, continuing to watch...'.format(pid)
        logger.debug(msg)
        lib.tell_manager(worker_name, 'log.debug', config, logger, socket, msg)
        time.sleep(POLL_INTERVAL)
    # TODO: confirm that the run and subsequent results gathering
    # completed successfully
    return {run_type: {'completed': True}}


def pid_exists(pid):
    """Check whether pid exists in the current process table.

    From: http://stackoverflow.com/a/6940314
    """
    if pid < 0:
        return False
    if pid == 0:
        # According to "man 2 kill" PID 0 refers to every process
        # in the process group of the calling process.
        # On certain systems 0 is a valid PID but we have no way
        # to know that in a portable fashion.
        raise ValueError('invalid PID 0')
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH)
            raise
    else:
        return True

if __name__ == '__main__':
    main()
