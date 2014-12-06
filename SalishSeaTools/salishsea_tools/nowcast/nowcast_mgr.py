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

"""Salish Sea NEMO nowcast manager.
"""
from copy import copy
import logging
import os
import pprint
import subprocess
import traceback

import zmq

from salishsea_tools.nowcast import lib


mgr_name = lib.get_module_name()

logger = logging.getLogger(mgr_name)

context = zmq.Context()

checklist = {}


def main():
    parser = lib.basic_arg_parser(mgr_name, description=__doc__)
    parser.prog = 'python -m salishsea_tools.nowcast.{}'.format(mgr_name)
    parsed_args = parser.parse_args()
    config = lib.load_config(parsed_args.config_file)
    lib.configure_logging(config, logger, parsed_args.debug)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {.config_file}'.format(parsed_args))
    lib.install_signal_handlers(logger, context)
    socket = init_req_rep(config['ports']['req_rep'], context)
    while True:
        logger.info('listening...')
        try:
            message = socket.recv()
            reply, next_steps = message_processor(config, message)
            socket.send(reply)
            if next_steps is not None:
                for next_step, next_step_args in next_steps:
                    next_step(*next_step_args)
        except zmq.ZMQError as e:
            # Fatal ZeroMQ problem
            logger.critical('ZMQError: {}'.format(e))
            logger.critical('shutting down')
            break
        except SystemExit:
            # Termination by signal
            break
        except:
            logger.critical('unhandled exception:')
            for line in traceback.format_exc().splitlines():
                logger.error(line)


def init_req_rep(port, context):
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:{}'.format(port))
    logger.info('bound to port {}'.format(port))
    return socket


def message_processor(config, message):
    msg = lib.deserialize_message(message)
    # Unpack message items
    worker = msg['source']
    msg_type = msg['msg_type']
    payload = msg['payload']
    # Message to acknowledge receipt of message from worker
    reply_ack = lib.serialize_message(mgr_name, 'ack')
    # Lookup table of functions to return next step function and its
    # arguments for the message types that we know how to handle
    after_actions = {
        'download_weather': after_download_weather,
        'get_NeahBay_ssh': after_get_NeahBay_ssh,
        'make_runoff_file': after_make_runoff_file,
        'grib_to_netcdf': after_grib_to_netcdf,
        'init_cloud': after_init_cloud,
        'create_compute_node': after_create_compute_node,
        'set_head_node_ip': after_set_head_node_ip,
        'set_ssh_config': after_set_ssh_config,
        'set_mpi_hosts': after_set_mpi_hosts,
        'mount_sshfs': after_mount_sshfs,
        'upload_forcing': after_upload_forcing,
        'make_forcing_links': after_make_forcing_links,
        'download_results': after_download_results,
        'the end': the_end,
    }
    # Handle undefined message type
    if msg_type not in config['msg_types'][worker]:
        logger.warning(
            'undefined message type received from {worker}: {msg_type}'
            .format(worker=worker, msg_type=msg_type))
        reply = lib.serialize_message(mgr_name, 'undefined msg')
        return reply, None
    # Recognized message type
    logger.info(
        'received message from {worker}: ({msg_type}) {msg_words}'
        .format(worker=worker,
                msg_type=msg_type,
                msg_words=config['msg_types'][worker][msg_type]))
    # Handle end of automation message
    if msg_type == 'the end':
        logger.info('worker-automated parts of nowcast completed for today')
        next_steps = after_actions['the end'](config)
        return reply_ack, next_steps
    # Handle need messages from workers
    if msg_type.startswith('need'):
        reply = lib.serialize_message(mgr_name, 'ack', checklist[payload])
        return reply, None
    # Handle success, failure, and crash messages from workers
    next_steps = after_actions[worker](worker, msg_type, payload, config)
    return reply_ack, next_steps


def after_download_weather(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success 00': [
            (update_checklist, [worker, 'weather', payload]),
        ],
        'failure 00': None,
        'success 06': [
            (update_checklist, [worker, 'weather', payload]),
            (launch_worker, ['make_runoff_file', config]),
            (launch_worker, ['grib_to_netcdf', config, ['forecast2']]),
        ],
        'failure 06': None,
        'success 12': [
            (update_checklist, [worker, 'weather', payload]),
            (launch_worker, ['get_NeahBay_ssh', config]),
            (launch_worker, ['grib_to_netcdf', config, ['nowcast+']]),
        ],
        'failure 12': None,
        'success 18': [
            (update_checklist, [worker, 'weather', payload]),
        ],
        'failure 18': None,
        'crash': None,
    }
    return actions[msg_type]


def after_get_NeahBay_ssh(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'sshNeahBay', payload]),
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_make_runoff_file(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'rivers', payload]),
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_grib_to_netcdf(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success nowcast+': [
            (update_checklist, [worker, 'weather forcing', payload]),
            (launch_worker,
             ['upload_forcing', config, [config['run']['hpc host']]]),
            (launch_worker, ['init_cloud', config]),
        ],
        'failure nowcast+': None,
        'success forecast2': [
            (update_checklist, [worker, 'weather forcing', payload]),
        ],
        'failure forecast2': None,
        'crash': None,
    }
    return actions[msg_type]


def after_init_cloud(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'nodes', payload]),
        ],
        'failure': None,
        'crash': None,
    }
    if msg_type == 'success':
        existing_nodes = []
        for node in copy(payload.keys()):
            try:
                existing_nodes.append(int(node.lstrip('nowcast')))
            except ValueError:
                # ignore nodes whose names aren't of the form nowcasti
                payload.pop(node)
        host_name = config['run']['cloud host']
        host = config['run'][host_name]
        for i in range(host['nodes']):
            if i not in existing_nodes:
                node_name = 'nowcast{}'.format(i)
                actions['success'].append(
                    (launch_worker,
                     ['create_compute_node', config, [node_name]]))
        actions['success'].append([is_cloud_ready, [config]])
    return actions[msg_type]


def after_create_compute_node(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'nodes', payload]),
            (is_cloud_ready, [config]),
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_set_head_node_ip(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'cloud addr', payload]),
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_set_ssh_config(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'ssh config', payload]),
            (launch_worker, ['set_mpi_hosts', config]),
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_set_mpi_hosts(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'mpi_hosts', payload]),
            (launch_worker, ['mount_sshfs', config]),
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_mount_sshfs(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'sshfs mount', payload]),
            (launch_worker,
             ['upload_forcing', config, [config['run']['cloud host']]]),
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_upload_forcing(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'forcing upload', payload]),
            (launch_worker,
             ['make_forcing_links', config, [payload.keys()[0]]]),
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_make_forcing_links(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'forcing links', payload])
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_download_results(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'results files', payload])
        ],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def update_checklist(worker, key, worker_checklist):
    try:
        checklist[key].update(worker_checklist)
    except (KeyError, ValueError, AttributeError):
        checklist[key] = worker_checklist
    logger.debug('checklist:\n{}'.format(pprint.pformat(checklist)))
    logger.info(
        'checklist updated with {} items from {} worker'.format(key, worker))


def launch_worker(worker, config, cmd_line_args=[]):
    cmd = [
        config['python'], '-m',
        'salishsea_tools.nowcast.workers.{}'.format(worker),
        config['config_file'],
    ]
    if cmd_line_args:
        cmd.extend(cmd_line_args)
    logger.info('launching {} worker'.format(worker))
    subprocess.Popen(cmd)


def is_cloud_ready(config):
    global checklist
    host_name = config['run']['cloud host']
    host = config['run'][host_name]
    if 'nowcast0' in checklist['nodes']:
        if 'cloud addr' not in checklist:
            # Add an empty address so that worker only gets launched once
            checklist['cloud addr'] = ''
            launch_worker('set_head_node_ip', config)
        if len(checklist['nodes']) >= host['nodes']:
            checklist['cloud ready'] = True
            logger.info(
                '{node_count} nodes in {host} ready for '
                'run provisioning'
                .format(node_count=host['nodes'], host=host_name))
            launch_worker('set_ssh_config', config)


def the_end(config):
    next_step = finish_automation
    next_step_args = [config]
    return [(next_step, next_step_args)]


def finish_automation(config):
    global checklist
    checklist = {}
    logger.info('checklist cleared')
    rotate_log_file(config)


def rotate_log_file(config):
    try:
        for handler in logger.handlers:
            logger.info('rotating log file')
            handler.doRollover()
            lib.fix_perms(config['logging']['log_file'])
            logger.info('log file rotated')
            logger.info('running in process {}'.format(os.getpid()))
    except AttributeError:
        # Logging handler has no rollover; probably a StreamHandler
        pass


if __name__ == '__main__':
    main()
