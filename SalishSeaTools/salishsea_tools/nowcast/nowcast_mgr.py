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
import logging
import os
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
            reply, next_steps = parse_message(config, message)
            socket.send(reply)
            if next_steps is not None:
                for next_step, next_step_args in next_steps:
                    next_step(*next_step_args)
        except SystemExit:
            # Normal termination
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


def parse_message(config, message):
    msg = lib.deserialize_message(message)
    # Unpack message items
    worker = msg['source']
    msg_type = msg['msg_type']
    payload = msg['payload']
    # Message to acknowledge receipt of message from worker
    reply_ack = lib.serialize_message(mgr_name, 'ack')
    # Lookup table of functions to return next step function and its
    # arguments for the message types that we know how to handle
    actions = {
        'download_weather': after_download_weather,
        'get_NeahBay_ssh': after_get_NeahBay_ssh,
        'make_runoff_file': after_make_runoff_file,
        'grib_to_netcdf': after_grib_to_netcdf,
        'init_cloud': after_init_cloud,
        'create_compute_node': after_create_compute_node,
        'set_head_node_ip': after_set_head_node_ip,
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
    # Recongnized message type
    logger.info(
        'received message from {worker}: ({msg_type}) {msg_words}'
        .format(worker=worker,
                msg_type=msg_type,
                msg_words=config['msg_types'][worker][msg_type]))
    # Handle end of automation message
    if msg_type == 'the end':
        logger.info('worker-automated parts of nowcast completed for today')
        next_steps = actions['the end'](config)
        return reply_ack, next_steps
    # Handle success and failure messages from workers
    next_steps = actions[worker](worker, msg_type, payload, config)
    return reply_ack, next_steps


def the_end(config):
    next_step = finish_automation
    next_step_args = [config]
    return [(next_step, next_step_args)]


def after_download_weather(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success 06': None,
        'failure 06': None,
        'success 18': [(launch_worker, ['grib_to_netcdf', config])],
        'failure 18': None,
        'crash': None,
    }
    return actions[msg_type]


def after_get_NeahBay_ssh(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [(update_checklist, [worker, 'sshNeahBay', payload])],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_make_runoff_file(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [(update_checklist, [worker, 'rivers', payload])],
        'failure': None,
        'crash': None,
    }
    return actions[msg_type]


def after_grib_to_netcdf(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'weather forcing', payload]),
            (launch_worker, ['upload_forcing', config]),
        ],
        'failure': None,
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
        existing_nodes = [
            int(node.lstrip('nowcast')) for node in payload.keys()]
        for i in range(config['run']['nodes']):
            if i not in existing_nodes:
                node_name = 'nowcast{}'.format(i)
                actions['success'].append(
                    (launch_worker,
                     ['create_compute_node', config, [node_name]]))
    return actions[msg_type]


def after_create_compute_node(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'nodes', payload]),
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


def after_upload_forcing(worker, msg_type, payload, config):
    actions = {
        # msg type: [(step, [step_args])]
        'success': [
            (update_checklist, [worker, 'forcing upload', payload]),
            (launch_worker, ['make_forcing_links', config]),
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
    except KeyError:
        checklist[key] = worker_checklist
    logger.debug('checklist: {}'.format(checklist))
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


def finish_automation(config):
    checklist = {}
    logger.info('checklist cleared')
    rotate_log_file(config)


def rotate_log_file(config):
    try:
        for handler in logger.handlers:
            logger.info('rotating log file')
            handler.doRollover()
            os.chmod(config['logging']['log_file'], lib.PERMS_RW_RW_R)
            logger.info('log file rotated')
            logger.info('running in process {}'.format(os.getpid()))
    except AttributeError:
        # Logging handler has no rollover; probably a StreamHandler
        pass


if __name__ == '__main__':
    main()
