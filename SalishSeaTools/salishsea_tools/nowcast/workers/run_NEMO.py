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

"""Salish Sea NEMO nowcast worker that prepares the YAML run description
file and bash run script for a nowcast or forecast run in the cloud
computing facility, and launches the run.
"""
from __future__ import division

import argparse
import datetime
import logging
import os
import shlex
import subprocess
import traceback

import yaml
import zmq

import salishsea_cmd.api
import salishsea_cmd.lib
from salishsea_tools.namelist import namelist2dict
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
            '{.run_type} NEMO run in {host_name} started'
            .format(parsed_args, host_name=host_name))
        # Exchange success messages with the nowcast manager process
        lib.tell_manager(
            worker_name, 'success', config, logger, socket, checklist)
    except lib.WorkerError:
        logger.critical(
            '{.run_type} NEMO run in {host_name} failed'
            .format(parsed_args, host_name=host_name))
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
        'run_type', choices=set(('nowcast', 'forecast')),
        help='Type of run to execute.'
    )
    return parser


def run_NEMO(host_name, run_type, config):
    host = config['run'][host_name]
    # Update the namelist.time file
    today = datetime.date.today()
    if run_type == 'nowcast':
        run_day = today
        future_limit_days = 1
    elif run_type == 'forecast':
        run_day = today + datetime.timedelta(days=1)
        future_limit_days = 2.5
    restart_timestep = update_time_namelist(
        host, run_type, run_day, future_limit_days)
    # Create the run description data structure and dump it to a YAML file
    dmy = today.strftime('%d%b%y').lower()
    run_id = '{dmy}{run_type}'.format(dmy=dmy, run_type=run_type)
    os.chdir(host['run_prep_dirs'][run_type])
    run_desc = run_description(
        host, run_type, run_day, run_id, restart_timestep)
    run_desc_file = '{}.yaml'.format(run_id)
    with open(run_desc_file, 'wt') as f:
        yaml.dump(run_desc, f, default_flow_style=False)
    logger.debug('run description file: {}'.format(run_desc_file))
    # Create and populate the temporary run directory
    run_dir = salishsea_cmd.api.prepare(run_desc_file, 'iodef.xml')
    logger.debug('temporary run directory: {}'.format(run_dir))
    os.unlink(run_desc_file)
    # Create the bash script to execute the run and gather the results
    namelist = namelist2dict(os.path.join(run_dir, 'namelist'))
    cores = namelist['nammpp'][0]['jpnij']
    results_dir = os.path.join(host['results'][run_type], dmy)
    os.chdir(run_dir)
    script = build_script(run_desc_file, cores, results_dir)
    with open('SalishSeaNEMO.sh', 'wt') as f:
        f.write(script)
    logger.debug(
        'run script: {}'.format(os.path.join(run_dir, 'SalishSeaNEMO.sh')))
    cmd = shlex.split('bash SalishSeaNEMO.sh >stdout 2>stderr')
    logger.info('starting run: "{}"'.format(cmd))
    process = subprocess.Popen(cmd, shell=True)
    logger.debug('run pid: {.pid}'.format(process))
    return {run_type: {
        'run dir': run_dir,
        'pid': process.pid,
    }}


def update_time_namelist(host, run_type, run_day, future_limit_days):
    namelist = os.path.join(host['run_prep_dirs'][run_type], 'namelist.time')
    with open(namelist, 'rt') as f:
        lines = f.readlines()
    new_lines, restart_timestep = calc_new_namelist_lines(
        lines, run_type, run_day, future_limit_days)
    with open(namelist, 'wt') as f:
        f.writelines(new_lines)
    return restart_timestep


def calc_new_namelist_lines(
    lines, run_type, run_day, future_limit_days,
    timesteps_per_day=TIMESTEPS_PER_DAY,
):
    it000_line, prev_it000 = get_namelist_value('nn_it000', lines)
    itend_line, prev_itend = get_namelist_value('nn_itend', lines)
    date0_line, date0 = get_namelist_value('nn_date0', lines)
    next_it000 = int(prev_it000) + timesteps_per_day
    next_itend = int(prev_itend) + timesteps_per_day
    # Prevent namelist from being updated past today's nowcast/forecast
    # time step values
    date0 = datetime.date(*map(int, [date0[:4], date0[4:6], date0[-2:]]))
    future_limit = datetime.timedelta(days=future_limit_days)
    if next_itend / timesteps_per_day > (run_day - date0 + future_limit).days:
        return lines, int(prev_it000) - 1
    # Increment 1st and last time steps to values for today
    lines[it000_line] = lines[it000_line].replace(prev_it000, str(next_it000))
    lines[itend_line] = lines[itend_line].replace(prev_itend, str(next_itend))
    restart_timestep = {
        'nowcast': int(prev_itend),
        'forecast': int(next_it000) - 1,
    }
    return lines, restart_timestep[run_type]


def get_namelist_value(key, lines):
    line_index = [
        i for i, line in enumerate(lines)
        if line.split()[0] == key][-1]
    value = lines[line_index].split()[2]
    return line_index, value


def run_description(host, run_type, run_day, run_id, restart_timestep):
    # Relative paths from MEOPAR/nowcast/
    prev_day = run_day - datetime.timedelta(days=1)
    init_conditions = os.path.join(
        host['results']['nowcast'],
        prev_day.strftime('%d%b%y').lower(),
        'SalishSea_{:08d}_restart.nc'.format(restart_timestep),
    )
    forcing_home = host['run_prep_dirs']['nowcast']
    run_desc = salishsea_cmd.api.run_description(
        NEMO_code=os.path.abspath(os.path.join(forcing_home, '../NEMO-code/')),
        forcing=os.path.abspath(
            os.path.join(forcing_home, '../NEMO-forcing/')),
        runs_dir=os.path.abspath(os.path.join(forcing_home, '../SalishSea/')),
        init_conditions=os.path.abspath(init_conditions),
    )
    run_desc['run_id'] = run_id
    # Paths to run-specific forcing directories
    run_desc['forcing']['atmospheric'] = os.path.abspath(
        os.path.join(forcing_home, 'NEMO-atmos'))
    run_desc['forcing']['open boundaries'] = os.path.abspath(
        os.path.join(forcing_home, 'open_boundaries'))
    run_desc['forcing']['rivers'] = os.path.abspath(
        os.path.join(forcing_home, 'rivers'))
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


def build_script(run_desc_file, procs, results_dir):
    run_desc = salishsea_cmd.lib.load_run_desc(run_desc_file)
    # Variable definitions
    script = (
        u'{defns}\n'
        .format(
            defns=_definitions(
                run_desc['run_id'], run_desc_file, results_dir,
                procs))
    )
    # Run NEMO
    script += (
        u'echo "Working dir: $(pwd)"\n'
        u'\n'
        u'echo "Starting run at $(date)"\n'
        u'${MPIRUN} ./nemo.exe >>stdout 2>>stderr\n'
        u'echo "Ended run at $(date)"\n'
        u'\n'
    )
    # Gather per-processor results files and deflate the finished netCDF4
    # files
    script += (
        u'echo "Results gathering and deflation started at $(date)"\n'
        u'mkdir -p ${RESULTS_DIR}\n'
        u'${GATHER} ${GATHER_OPTS} ${RUN_DESC} ${RESULTS_DIR}\n'
        u'echo "Results gathering and deflation ended at $(date)"\n'
        u'\n'
    )
    # Delete the (now empty) working directory
    script += (
        u'echo "Deleting run directory"\n'
        u'rmdir $(pwd)\n'
    )
    return script


def _definitions(run_id, run_desc_file, results_dir, procs):
    mpirun = 'mpirun -n {procs}'.format(procs=procs)
    mpirun = ' '.join((mpirun, '--hostfile', '${HOME}/mpi_hosts'))
    defns = (
        u'RUN_ID="{run_id}"\n'
        u'RUN_DESC="{run_desc_file}"\n'
        u'RESULTS_DIR="{results_dir}"\n'
        u'MPIRUN="{mpirun}"\n'
        u'GATHER="{salishsea_cmd} gather"\n'
        u'GATHER_OPTS="--no-compress"\n'
    ).format(
        run_id=run_id,
        run_desc_file=run_desc_file,
        results_dir=results_dir,
        mpirun=mpirun,
        salishsea_cmd='${HOME}/.local/bin/salishsea',
    )
    return defns


if __name__ == '__main__':
    main()
