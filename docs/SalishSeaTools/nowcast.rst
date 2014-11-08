.. Copyright 2013-2014 The Salish Sea MEOPAR contributors
.. and The University of British Columbia
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.


.. _salishsea_tools.nowcast:

*****************************************
:py:mod:`salishsea_tools.nowcast` Package
*****************************************

The :py:mod:`salishsea_tools.nowcast` package is a collection of Python modules associated with running the Salish Sea NEMO model in a daily nowcast/forecast mode.
The runs use as-recent-as-available
(typically previous day)
forcing data for the western boundary sea surface height and the Fraser River flow,
and atmospheric forcing from the twice daily produced forecast results from the Environment Canada GEM 2.5km resolution model.

The runs are automated using an asynchronous,
message-based architecture that:

* obtains the forcing datasets from web services
* pre-processes the forcing datasets into the formats expected by NEMO
* uploads the forcing dataset files to the HPC facility where the run will be executed
* executes the run
* downloads the results
* prepares a collection of plots from the run results for monitoring purposes
* publishes the plots and the processing log to the web

The automation architecture is presently under development.
It consists of a long-running manager process and a collection of worker processes,
some of which are also long-running,
and others which are launched by the manager or cron to perform specific tasks.


.. _salishsea_tools.nowcast.figures:

:py:mod:`nowcast.figures` Module
================================

.. automodule:: nowcast.figures
    :members:


.. _salishsea_tools.nowcast.lib:

:py:mod:`nowcast.lib` Module
============================

.. automodule:: nowcast.lib
    :members:


. _CreatingNowcastWorkers:

Creating Nowcast Workers
========================

Nowcast workers are Python modules that can be imported from :py:mod:`salishsea_tools.nowcast.workers`.
They are composed of some standard code to allow them to interface with the messaging and logging frameworks,
and one or more functions to execute their task in the nowcast system.
Most of the standard code is calls to functions in the :ref:`salishsea_tools.nowcast.lib`.

Here is a skeleton example of a worker showing the standard code.
It is explained,
line by line,
below.

.. code-block:: python
    :linenos:

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

    import zmq

    from salishsea_tools.nowcast import lib


    worker_name = lib.get_module_name()

    logger = logging.getLogger(worker_name)

    context = zmq.Context()


    def main():
        parser = lib.basic_arg_parser(worker_name, description=__doc__)
        parsed_args = parser.parse_args()
        config = lib.load_config(parsed_args.config_file)
        lib.configure_logging(config, logger, parsed_args.debug)
        logger.info('running in process {}'.format(os.getpid()))
        logger.info('read config from {.config_file}'.format(parsed_args))
        lib.install_signal_handlers(logger, context)
        socket = lib.init_zmq_req_rep_worker(context, config, logger)

        # Do some work

        message = lib.serialize_message(worker_name, 'end of nowcast')
        socket.send(message)
        logger.info('sent "end of nowcast" message')
        msg = socket.recv()
        message = lib.deserialize_message(msg)
        logger.info(
            'received message from {source}: {msg_type}'.format(**message))
        context.destroy()
        logger.info('task completed; shutting down')
