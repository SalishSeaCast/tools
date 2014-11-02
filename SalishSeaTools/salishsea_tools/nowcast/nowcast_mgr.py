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
import sys

import zmq

from salishsea_tools.nowcast import lib


logger = logging.getLogger('nowcast_mgr')

context = zmq.Context()


def main(args):
    config_file = args[0]
    config = lib.load_config(config_file)
    lib.configure_logging(config, logger)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {}'.format(config_file))
    lib.install_signal_handlers(logger, context)
    socket = init_req_rep(config['ports']['req_rep'], context)
    while True:
        message = socket.recv()
        logger.info('REQ:{}'.format(message))
        reply = parse_message(message)
        socket.send(reply)


def init_req_rep(port, context):
    socket = context.socket(zmq.REP)
    socket.bind('tcp://*:{}'.format(port))
    logger.info('listening for REQs on port {}'.format(port))
    return socket


def parse_message(message):
    if message.startswith('river data kickoff'):
        logger.info('launch river data daily average worker')
        reply = b'ACK'
    return reply


if __name__ == '__main__':
    main(sys.argv[1:])
