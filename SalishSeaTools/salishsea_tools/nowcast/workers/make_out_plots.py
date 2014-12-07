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

"""Salish Sea NEMO nowcast worker that produces the ssh and weather
plots for a nowcast run
"""
import argparse
from glob import glob
import logging
import os
import traceback

import arrow
import matplotlib.pylab as plt
import netCDF4 as nc
import zmq

from salishsea_tools.nowcast import (
    figures, 
    lib,
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
        checklist = make_out_plots(parsed_args.run_date, config, socket)
        logger.info('Made the "Out" plots completed')
        # Exchange success messages with the nowcast manager process
        lib.tell_manager(
            worker_name, 'success', config, logger, socket, checklist)
    except lib.WorkerError:
        logger.critical(
            'Made the "Out" plots failed')
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
        '--run-date', type=lib.arrow_date, default=arrow.now(),
        help='''
        Date of the run to download results files from;
        defaults to %(default)s.
        ''',
    )
    return parser

def make_out_plots(run_date, config, socket):

    # set-up, read from config file
    results_home = config['run']['results archive']['nowcast']
    results_dir = os.path.join(results_home, run_date.strftime('%d%b%y').lower())
    model_path = config['weather']['ops_dir']
    bathy = nc.Dataset(config['bathymetry'])

    # configure plot directory for saving
    date_key = run_date.strftime('%d%b%y').lower()
    plots_dir = os.path.join(results_home, date_key, 'figures')
    lib.mkdir(plots_dir, logger, grp_name='sallen')

    # get the results
    grid_T_hr = results_dataset('1h', 'grid_T', results_dir)

    # do the plots
    fig = figures.PA_tidal_predictions(grid_T_hr)
    filename = os.path.join(plots_dir, 
                        'PA_tidal_predictions_{date}.svg'.format(date=date_key))
    plt.savefig(filename)

    fig = figures.compare_tidalpredictions_maxSSH( 
                    grid_T_hr, bathy, model_path, name='Victoria')
    filename = os.path.join(plots_dir, 
                        'Vic_maxSSH__{date}.svg'.format(date=date_key))
    plt.savefig(filename)
    
    fig = figures.compare_tidalpredictions_maxSSH( 
                                             grid_T_hr, bathy, model_path)
    filename = os.path.join(plots_dir, 
                        'PA_maxSSH_{date}.svg'.format(date=date_key))
    plt.savefig(filename)
    
    fig = figures.compare_tidalpredictions_maxSSH( 
                         grid_T_hr, bathy, model_path, name='Campbell River') 
    filename = os.path.join(plots_dir, 
                        'CR_maxSSH_{date}.svg'.format(date=date_key))
    plt.savefig(filename)

    fig = figures.compare_water_levels(grid_T_hr, bathy)
    filename = os.path.join(plots_dir, 
                        'NOAA_ssh_{date}.svg'.format(date=date_key))
    plt.savefig(filename)

    fig = figures.plot_thresholds_all(grid_T_hr, bathy, model_path)
    filename = os.path.join(plots_dir,
                 'WaterLevel_Thresholds_{date}.svg'.format(date=date_key))
    plt.savefig(filename)

    fig = figures.Sandheads_winds(grid_T_hr, bathy, model_path)
    filename = os.path.join(plots_dir, 
                        'SH_wind_{date}.svg'.format(date=date_key))
    plt.savefig(filename)

    

def results_dataset(period, grid, results_dir):
    """Return the results dataset for period (e.g. 1h or 1d)
    and grid (e.g. grid_T, grid_U) from results_dir.
    """
    filename_pattern = 'SalishSea_{period}_*_{grid}.nc'
    filepaths = glob(os.path.join(results_dir, 
                   filename_pattern.format(period=period, grid=grid)))
    return nc.Dataset(filepaths[0])

if __name__ == '__main__':
    main()
