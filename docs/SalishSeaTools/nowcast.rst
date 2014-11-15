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


.. _CreatingNowcastWorkers:

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
    import os

    import zmq

    from salishsea_tools.nowcast import lib


    worker_name = lib.get_module_name()

    logger = logging.getLogger(worker_name)

    context = zmq.Context()


    def main():
        # Prepare the worker
        parser = lib.basic_arg_parser(worker_name, description=__doc__)
        parsed_args = parser.parse_args()
        config = lib.load_config(parsed_args.config_file)
        lib.configure_logging(config, logger, parsed_args.debug)
        logger.info('running in process {}'.format(os.getpid()))
        logger.info('read config from {.config_file}'.format(parsed_args))
        lib.install_signal_handlers(logger, context)
        socket = lib.init_zmq_req_rep_worker(context, config, logger)

        # Do the work
        checklist = {}
        worker_function(config, checklist, ...)
        log.info('success message')

        # Exchange success messages with the nowcast manager process
        success(config, socket, checklist)

        # Finish up
        context.destroy()
        logger.info('task completed; shutting down')


    def success(config, socket, checklist):
        msg_type = 'success'
        # Send message to nowcast manager
        message = lib.serialize_message(worker_name, msg_type, checklist)
        socket.send(message)
        logger.info(
            'sent message: ({msg_type}) {msg_words}'
            .format(
                msg_type=msg_type,
                msg_words=config['msg_types'][worker_name][msg_type]))
        # Wait for and process response
        msg = socket.recv()
        message = lib.deserialize_message(msg)
        source = message['source']
        msg_type = message['msg_type']
        logger.info(
            'received message from {source}: ({msg_type}) {msg_words}'
            .format(source=source,
                    msg_type=message['msg_type'],
                    msg_words=config['msg_types'][source][msg_type]))


    if __name__ == '__main__':
        main()

Lines 1 through 14 are our standard project copyright and license statement.
It uses :kbd:`#` comments rather than being enclosed in triple quotes to segregate it from the docstring which is used in automatic documentation generation and help text.

Lines 16 an 17 are the module's triple-quoted docstring.
As noted above,
it wall appear in auto-generated documentation of the module.
For convenience we will also use the docstring as the description element of the worker's command-line help message,
although that can easily be changed if you prefer to put more details in the docstring than you want to appear in the help text.

The minimum set of imports that a worker needs are:

.. code-block:: python

    import logging
    import os

    import zmq

    from salishsea_tools.nowcast import lib

The :py:mod:`logging` module provides the mechanism that we use to print output about the worker's progress and status to the log file or the screen,
effectively developer-approved print statements on steroids :-)
:py:mod:`zmq` is the Python bindings to the `ZeroMQ`_ messaging library that we use to communicate between the workers and the nowcast manager process.
The :ref:`salishsea_tools.nowcast.lib` is our collection of functions that are used across workers.
If you find yourself writing the same function in more than one worker it should probably be generalized and included in :py:mod:`lib`.

.. _ZeroMQ: http://zeromq.org/

Obviously you will need to import whatever other modules your worker needs for its task.

Next up are 3 module level variables:

.. code-block:: python

    worker_name = lib.get_module_name()

    logger = logging.getLogger(worker_name)

    context = zmq.Context()

:py:data:`worker_name` is used to identify the source of logging message and message exchanged between the worker and the nowcast manager process. :py:func:`lib.get_module_name` provides the worker's module name stripped of its path and :kbd:`.py` suffix.

:py:data:`logger` is our interface to the logging framework and we give this module's instance the worker's name.

:py:data:`context` is the interface to the ZeroMQ messaging framework.
There must only ever be one ZeroMQ context per module.

Python scoping rules make module level variables available for use in any functions in the module without passing them as arguments but assigning new values to them elsewhere in the module will surely mess things up.

The :py:func:`main` function is where our worker gets down to work.
It is called when the worker is run from the command line by virtue of the

.. code-block:: python

    if __name__ == '__main__':
        main()

block at the end of the module.


Prepare The Worker
------------------

Lines 35 and 36 set up the worker's command-line interface and parse the command-line arguments:

.. code-block:: python

    parser = lib.basic_arg_parser(worker_name, description=__doc__)
    parsed_args = parser.parse_args()

The :py:func:`lib.basic_arg_parser` returns a command-line parser instance with the file path/name of the :ref:`NowcastConfigFile` as a required argument,
and :option:`--debug` and :option:`--help` option flags.
The value of :py:data:`worker_name` is used to construct the parser's usage message.
Passing :py:data:`__doc__` as the value of :kbd:`description` causes the worker's module docstring to be used as the parser's descriptive text;
pass your own string instead to override that.
Try:

.. code-block:: bash

    $ python -m salishsea_tools.nowcast.workers.get_NeahBay_ssh --help

to see an example of the basic parser.

The :option:`--debug` flag is provided for development and debugging purposes.
It causes the logging message to be written to the screen instead of the the log file.

See :ref:`ExtendingTheCommandLineParser` for details of how to add required arguments and options flags to the basic parser.

Next,
on line 37,
we load the :ref:`NowcastConfigFile` given on the command-line into a Python dict data structure:

.. code-block:: python

    config = lib.load_config(parsed_args.config_file)

Lines 38 to 40 configure the logging system and start logging messages about what we've accomplished so far:

.. code-block:: python

    lib.configure_logging(config, logger, parsed_args.debug)
    logger.info('running in process {}'.format(os.getpid()))
    logger.info('read config from {.config_file}'.format(parsed_args))

The settings that define where the log files are stored,
how their contents are formatted,
and how many days
(nowcast runs)
log files are preserved at included in the :ref:`NowcastConfigFile`.

The :option:`--debug` on the command-line sets the value of :kbd:`parsed_arg.debug` to :py:obj:`True`
(it defaults to :py:obj:`False`).

The :py:data:`logger` instance has a variety of method for sending messages to the logging system at different levels of importance.
We mostly use :py:meth:`logging.info` for generally informative methods,
:py:meth:`logging.debug` for message about deeper levels of execution,
and :py:meth:`logging.error` for error message.

Here,
we log the id of the operating system process that the worker is running in,
and the file path/name of the configuration file that it is using.

Line 41:

.. code-block:: python

    lib.install_signal_handlers(logger, context)

installs signal handlers to cleanly deal with interrupt and termination signals from the operating system.
This means that if a worker running in :option:`--debug` mode is interrupted with a :kbd:`Ctrl-C` it will end cleanly,
logging the fact that it has been interrupted,
and shutting down the ZeroMQ messaging system.
Likewise,
if a worker running in the background is sent an interrupt or termination signal with

.. code-block:: bash

    kill <pid>

or

.. code-block:: bash

    kill -9 <pid>

it will shutdown cleanly.


.. _ExtendingTheCommandLineParser:

Extending the Command-line Parser
---------------------------------


.. _NowcastConfigFile:

Nowcast Configuration File
==========================
