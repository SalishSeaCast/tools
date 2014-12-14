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

"""Salish Sea NEMO nowcast worker that creates the forcing file symlinks
for a nowcast run on the HPC/cloud facility where the run will be
executed.
"""
from __future__ import division

import argparse
import datetime
import logging
import os
import traceback

import zmq

import salishsea_cmd.api
from salishsea_tools.nowcast import lib


worker_name = lib.get_module_name()

logger = logging.getLogger(worker_name)

context = zmq.Context()


TIMESTEPS_PER_DAY = 8640


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
    # Change salishsea_cmd.api logging formatter to nowcast style
    api_handler = salishsea_cmd.api.log.handlers[0]
    formatter = logging.Formatter(
        config['logging']['message_format'],
        datefmt=config['logging']['datetime_format'])
    api_handler.setFormatter(formatter)

    lib.install_signal_handlers(logger, context)
    socket = lib.init_zmq_req_rep_worker(
        context, config, logger, config['nowcast_mgr'])
    # Do the work
    host_name = config['run']['cloud host']
    try:
        checklist = run_NEMO(host_name, parsed_args.run_type, config)
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
    return parser


def run_NEMO(host_name, run_type, config):
    host = config['run'][host_name]
    today = datetime.date.today()
    prev_itend = update_time_namelist(host, run_type, today)
    dmy = today.strftime('%d%b%y').lower()
    run_id = '{dmy}{run_type}'.format(dmy=dmy, run_type=run_type)
    run_desc = run_description(host, run_type, today, run_id, prev_itend)
    results_dir = os.path.join(host['results'][run_type], dmy)
    salishsea_cmd.api.run_in_subprocess(
        run_id, run_desc, 'iodef.xml', os.path.abspath(results_dir))
    return {run_type: True}


def update_time_namelist(
    host, run_type, today, timesteps_per_day=TIMESTEPS_PER_DAY,
):
    namelist = os.path.join(host['run_prep_dirs'][run_type], 'namelist.time')
    with open(namelist, 'rt') as f:
        lines = f.readlines()
    it000_line, prev_it000 = get_namelist_value('nn_it000', lines)
    itend_line, prev_itend = get_namelist_value('nn_itend', lines)
    date0_line, date0 = get_namelist_value('nn_date0', lines)
    # Prevent namelist from being updated past today
    next_itend = int(prev_itend) + timesteps_per_day
    date0 = datetime.date(*map(int, [date0[:4], date0[4:6], date0[-2:]]))
    one_day = datetime.timedelta(days=1)
    if next_itend / timesteps_per_day > (today - date0 + one_day).days:
        return int(prev_it000) - 1
    # Increment 1st and last time steps to values for today
    lines[it000_line] = lines[it000_line].replace(
        prev_it000, str(int(prev_itend) + 1))
    lines[itend_line] = lines[itend_line].replace(prev_itend, str(next_itend))
    with open(namelist, 'wt') as f:
        f.writelines(lines)
    return int(prev_itend)


def get_namelist_value(key, lines):
    line_index = [
        i for i, line in enumerate(lines)
        if line.split()[0] == key][-1]
    value = lines[line_index].split()[2]
    return line_index, value


def run_description(host, run_type, today, run_id, prev_itend):
    # Relative paths from MEOPAR/nowcast/
    yesterday = today - datetime.timedelta(days=1)
    init_conditions = os.path.join(
        host['results'][run_type],
        yesterday.strftime('%d%b%y').lower(),
        'SalishSea_{:08d}_restart.nc'.format(prev_itend),
    )
    run_prep_dir = host['run_prep_dirs'][run_type]
    run_desc = salishsea_cmd.api.run_description(
        NEMO_code=os.path.abspath(os.path.join(run_prep_dir, '../NEMO-code/')),
        forcing=os.path.abspath(
            os.path.join(run_prep_dir, '../NEMO-forcing/')),
        runs_dir=os.path.abspath(os.path.join(run_prep_dir, '../SalishSea/')),
        init_conditions=os.path.abspath(init_conditions),
    )
    run_desc['run_id'] = run_id
    # Paths to run-specific forcing directories
    run_desc['forcing']['atmospheric'] = os.path.abspath(
        os.path.join(run_prep_dir, 'NEMO-atmos'))
    run_desc['forcing']['open boundaries'] = os.path.abspath(
        os.path.join(run_prep_dir, 'open_boundaries'))
    run_desc['forcing']['rivers'] = os.path.abspath(
        os.path.join(run_prep_dir, 'rivers'))
    # Paths to namelist section files
    run_desc['namelists'] = [
        os.path.abspath('namelist.time'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.domain'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.surface.nowcast'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.lateral.nowcast'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.bottom'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.tracers'),
        os.path.abspath('../SS-run-sets/SalishSea/namelist.dynamics'),
        os.path.abspath(
            '../SS-run-sets/SalishSea/namelist.compute.{}'
            .format(host['mpi decomposition'])),
    ]
    return run_desc


if __name__ == '__main__':
    main()
