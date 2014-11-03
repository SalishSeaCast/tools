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

"""Salish Sea NEMO nowcast library functions for use by manager and workers.
"""
import logging
import signal
import sys

import yaml
import zmq


def load_config(config_file):
    """Load the YAML config_file and return its contents as a dict.

    :arg config_file: Path/name of YAML configuration file for
                      Salish Sea NEMO nowcast.
    :type str:

    :returns: config dict
    """
    with open(config_file, 'rt') as f:
        config = yaml.load(f)
    return config


def configure_logging(config, logger):
    """Set up logging configuration.

    This function assumes that the logger instance has been created
    in the module from which the function is called.
    That is typically done with a module-level command like::

      logger = logging.getLogger('weather_download')

    where `weather_download` is replaced with the name of the module.

    :arg config: Configuration data structure.
    :type config: dict

    :arg logger: Logger instance to be configured.
    :type logger: :obj:`logging.Logger` instance
    """
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        config['logging']['message_format'],
        datefmt=config['logging']['datetime_format'])
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def install_signal_handlers(logger, context):
    """Install handlers to cleanly deal with interrupt and terminate signals.

    This function assumes that the logger and context instances
    have been created in the module from which the function is called.
    That is typically done with a module-level commands like::

      logger = logging.getLogger('weather_download')

      context = zmq.Context()

    where `weather_download` is replaced with the name of the module.

    :arg logger: Logger instance.
    :type logger: :class:`logging.Logger` instance

    :arg context: ZeroMQ context instance.
    :type context: :class:`zmq.Context` instance
    """
    def sigint_handler(signal, frame):
        logger.info(
            'interrupt signal (SIGINT or Ctrl-C) received; shutting down')
        context.destroy()
        sys.exit(0)

    def sigterm_handler(signal, frame):
        logger.info(
            'termination signal (SIGTERM) received; shutting down')
        context.destroy()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)


def init_zmq_req_rep_worker(context, config, logger):
    """Initialize a ZeroMQ request/reply (REQ/RPE) worker.

    :arg context: ZeroMQ context instance.
    :type context: :class:`zmq.Context` instance

    :arg config: Configuration data structure.
    :type config: dict

    :arg logger: Logger instance.
    :type logger: :class:`logging.Logger` instance

    :returns: ZeroMQ socket for communication with nowcast manager process.
    """
    socket = context.socket(zmq.REP)
    port = config['ports']['req_rep']
    socket.connect('tcp://localhost:{}'.format(port))
    logger.info('ready to send REQ messages on port {}'.format(port))
    return socket
