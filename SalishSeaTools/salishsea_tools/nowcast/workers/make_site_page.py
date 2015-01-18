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

"""Salish Sea NEMO nowcast worker that creates pages for the salishsea
site from page templates.
"""
import argparse
import datetime
import logging
import os
import shutil
import traceback

import arrow
import mako.template
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
    try:
        checklist = make_site_page(
            parsed_args.run_type, parsed_args.page_type, parsed_args.run_date,
            config)
        logger.info(
            '{0.page_type} page for {0.run_type} salishsea site prepared'
            .format(parsed_args))
        # Exchange success messages with the nowcast manager process
        msg_type = 'success {.page_type}'.format(parsed_args)
        lib.tell_manager(
            worker_name, msg_type, config, logger, socket, checklist)
    except lib.WorkerError:
        logger.critical(
            '{.page_type} page preparation failed'.format(parsed_args))
        # Exchange failure messages with the nowcast manager process
        msg_type = 'failure {.page_type}'.format(parsed_args)
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
        'run_type', choices=set(('nowcast', 'forecast', 'forecast2',)),
        help='''
        Type of run that the results come from.
        '''
    )
    parser.add_argument(
        'page_type', choices=set(('publish', 'research')),
        help='''
        Type of page to render from template to salishsea site prep directory.
        '''
    )
    parser.add_argument(
        '--run-date', type=lib.arrow_date,
        default=arrow.now().date(),
        help='''
        Date of the run to download results files from;
        use YYYY-MM-DD format.
        Defaults to %(default)s.
        ''',
    )
    return parser


def make_site_page(run_type, page_type, run_date, config):
    results_date = {
        'nowcast': run_date,
        'forecast': run_date + datetime.timedelta(days=1),
        'forecast2': run_date + datetime.timedelta(days=2),
    }
    run_title = {
        'nowcast': 'Nowcast',
        'forecast': 'Forecast',
        'forecast2': 'Preliminary Forecast',
    }
    svg_file_roots = {
        'publish': ['Threshold_website',
                    'PA_tidal_predictions',
                    'Vic_maxSSH',
                    'PA_maxSSH',
                    'CR_maxSSH',
                    'NOAA_ssh',
                    'WaterLevel_Thresholds',
                    'SH_wind',
                    'Avg_wind_vectors',
                    'Wind_vectors_at_max',
                    ],
        'research': ['Salinity_on_thalweg',
                     'T_S_Currents_on_surface',
                     'Compare_VENUS_East',
                     'Compare_VENUS_Central',
                     ],
        }
    # Load template
    mako_file = os.path.join(
        config['web']['templates_path'], '.'.join((page_type, 'mako')))
    tmpl = mako.template.Template(filename=mako_file)
    logger.debug('read template: {}'.format(mako_file))
    # Render template to rst
    repo_name = config['web']['site_repo_url'].rsplit('/')[-1]
    repo_path = os.path.join(config['web']['www_path'], repo_name)
    rst_file = os.path.join(
        repo_path,
        config['web']['site_nemo_results_path'],
        run_type,
        ''.join((page_type, '_',
                 results_date[run_type].strftime('%d%b%y').lower(), '.rst')))

    vars = {
        'run_date': run_date,
        'run_type': run_type,
        'results_date': results_date[run_type],
        'run_title': run_title[run_type],
        'svg_file_roots': svg_file_roots[page_type],
        }
    with open(rst_file, 'wt') as f:
        f.write(tmpl.render(**vars))
    lib.fix_perms(rst_file, grp_name=config['file group'])
    logger.debug('rendered page: {}'.format(rst_file))
    checklist = {' '.join((run_type, page_type)): rst_file}
    # If appropriate copy rst file to forecast file
    if run_type in ('forecast', 'forecast2') and page_type == 'publish':
        forecast_file = os.path.join(
            repo_path,
            config['web']['site_storm_surge_path'],
            '.'.join(('forecast', 'rst')))
        shutil.copy2(rst_file, forecast_file)
        logger.debug('copied page to forecast: {}'.format(forecast_file))
        checklist['Most recent forecast'] = forecast_file
    return checklist


if __name__ == '__main__':
    main()
