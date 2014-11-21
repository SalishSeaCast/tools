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

"""Salish Sea NEMO nowcast worker that downloads the results files
from a nowcast run on the HPC/cloud facility to archival storage.
"""
import argparse
import glob
import logging
import os

import arrow
import zmq

from salishsea_tools.nowcast import lib


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
    checklist = {}
    try:
        download_results(parsed_args.run_date, config, checklist)
        logger.info(
            'results files from {} downloaded'.format(config['run']['host']))
        # Exchange success messages with the nowcast manager process
        lib.tell_manager(
            worker_name, 'success', config, logger, socket, checklist)
        lib.tell_manager(worker_name, 'the end', config, logger, socket)
    except lib.WorkerError:
        logger.critical(
            'results files download from {} failed'
            .format(config['run']['host']))
        # Exchange failure messages with the nowcast manager process
        lib.tell_manager(worker_name, 'failure', config, logger, socket)
    # Finish up
    context.destroy()
    logger.info('task completed; shutting down')


def configure_argparser(prog, description, parents):
    parser = argparse.ArgumentParser(
        prog=prog, description=description, parents=parents)
    parser.add_argument(
        '--run-date', type=arrow_date,
        default=arrow.now().date(),
        help='''
        Date of the run to download results files from;
        defaults to %(default)s.
        ''',
    )
    return parser


def arrow_date(string):
    """Convert a YYYY-MM-DD string to an arrow object or raise
    :py:exc:`argparse.ArgumentTypeError`.
    """
    try:
        return arrow.get(string, 'YYYY-MM-DD')
    except arrow.parser.ParserError:
        msg = (
            'unrecognized date format: {} - '
            'please use YYYY-MM-DD'.format(string))
        raise argparse.ArgumentTypeError(msg)


def download_results(run_date, config, checklist):
    results_dir = run_date.strftime('%d%b%y').lower()
    src_dir = os.path.join(config['run']['results'], results_dir)
    src = (
        '{host}:{src_dir}'.format(host=config['run']['host'], src_dir=src_dir))
    dest = os.path.join(config['run']['results archive'])
    cmd = ['scp', '-Cpr', src, dest]
    lib.run_in_subprocess(cmd, logger.debug, logger.error)
    for freq in '1h 1d'.split():
        checklist[freq] = glob.glob(
            os.path.join(dest, results_dir, 'SalishSea_{}_*.nc'.format(freq)))
    for filename in 'stdout stderr'.split():
        filepath = os.path.join(dest, results_dir, filename)
        os.chmod(filepath, lib.PERMS_RW_RW_R)


if __name__ == '__main__':
    main()
