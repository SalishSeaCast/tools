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
    import traceback

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
        try:
            worker_function(config, checklist, ...)
            logger.info('success message')
            # Exchange success messages with the nowcast manager process
            lib.tell_manager(
                worker_name, 'success', config, logger, socket, checklist)
            lib.tell_manager(worker_name, 'the end', config, logger, socket)
        except lib.WorkerError:
            # Exchange failure messages with nowcast manager process
            logger.critical('failure message')
            lib.tell_manager(worker_name, 'failure', config, logger, socket)
        except:
            logger.critical('unhandled exception:')
            # Log the traceback from any unhandled exception
            for line in traceback.format_exc().splitlines():
                logger.error(line)
            # Exchange crash messages with the nowcast manager process
            lib.tell_manager(worker_name, 'crash', config, logger, socket)

        # Finish up
        context.destroy()
        logger.info('task completed; shutting down')


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
    import traceback

    import zmq

    from salishsea_tools.nowcast import lib

The :py:mod:`logging` module provides the mechanism that we use to print output about the worker's progress and status to the log file or the screen,
effectively developer-approved print statements on steroids :-)
The :py:mod:`os` module provides the interface to the operating system,
and :py:mod:`traceback` is used to report tracebacks if the worker raises an unanticipated eception.
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

Lines 36 and 37 set up the worker's command-line interface and parse the command-line arguments:

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
on line 38,
we load the :ref:`NowcastConfigFile` given on the command-line into a Python dict data structure:

.. code-block:: python

    config = lib.load_config(parsed_args.config_file)

Lines 39 to 41 configure the logging system and start logging messages about what we've accomplished so far:

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

Line 42:

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

**TODO**


.. _NowcastConfigFile:

Nowcast Configuration File
==========================

**TODO**


Development and Deployment
==========================

Python Package Environment
--------------------------

The nowcast workers that do pre- and post-processing for the runs can be run in a default :ref:`AnacondaPythonDistro` environment with the :ref:`SalishSeaTools` installed.
However,
the workers that interact with the `Ocean Networks Canada`_ private cloud `nefos`_ computing facility
(see :ref:`WorkingOnNefos`)
require additional Python packages to use the `OpenStack`_ APIs.
To avoid adding complexity and potential undesirable interactions and/or side-effects to the default Anaconda Python environment we create an isolated environment for nowcast.

.. _Ocean Networks Canada: http://www.oceannetworks.ca/
.. _nefos: https://www.westgrid.ca/support/systems/Nefos
.. _OpenStack: http://www.openstack.org/

Create a new :program:`conda` environment with Python 2.7 and pip installed in it,
and activate the environment:

.. code-block:: bash

    $ conda create -n nowcast python=2.7 pip

    ...

    $ source activate nowcast

Our first choice for installing packages is the :program:`conda` installer because it uses pre-built binary packages so it is faster and avoids problems that can arise with compilation of C extensions that are part of some of the packages.
Unfortunately,
not all of the packages that we need are available in the :program:`conda` repositories so we use :program:`pip` to install those from the `Python Package Index`_ (PyPI).

.. _Python Package Index: https://pypi.python.org/pypi

Install the packages that the :ref:`SalishSeaTools` depends on,
and the package itself:

.. code-block:: bash

    (nowcast)$ conda install matplotlib netCDF4 numpy pandas pyyaml
    (nowcast)$ pip install arrow angles
    (nowcast)$ cd MEOPAR/tools
    (nowcast)$ pip install --editable SalishSeaTools

Install the Python bindings to the `ZeroMQ`_ messaging library:

.. code-block:: bash

    (nowcast)$ conda install pyzmq

Install the packages available from the :program:`conda` repositories that are used by the `OpenStack` APIs,
and the Python bindings for the `OpenStack compute API`_
(which is called :program:`nova`):

.. code-block:: bash

    (nowcast)$ conda install requests pyopenssl cryptography cffi pycparser
    (nowcast)$ pip install python-novaclient

.. _OpenStack compute API: http://docs.openstack.org/user-guide/content/sdk_compute_apis.html

Finally,
install Sphinx and the sphinx-rtd-theme ReadTheDocs theme,
IPython and IPython Notebook,
and the ipdb debugger:

.. code-block:: bash

    (nowcast)$ conda install sphinx ipython-notebook
    (nowcast)$ pip install sphinx-rtd-theme ipdb

to support writing and building docs,
and developing and debugging Python code and :ref:`salishsea_tools.nowcast.figures` functions.

The complete list of Python packages installed including their version numbers (at time of writing) created by the :command:`pip freeze` command is available in :file:`salishsea_tools/nowcast/requirements.txt`.
