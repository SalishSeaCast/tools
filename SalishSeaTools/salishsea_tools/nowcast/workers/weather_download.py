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

"""Salish Sea NEMO nowcast weather model dataset download worker.
"""
import logging
import os
import sys

import zmq

from salishsea_tools.nowcast import lib


logger = logging.getLogger('weather_download')

context = zmq.Context()


def main(args):
    config_file = args[0]
    config = lib.load_config(config_file)
    lib.configure_logging(config, logger)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {}'.format(config_file))
    lib.install_signal_handlers(logger, context)
    socket = lib.init_zmq_worker(context, config, logger)


if __name__ == '__main__':
    main(sys.argv[1:])
