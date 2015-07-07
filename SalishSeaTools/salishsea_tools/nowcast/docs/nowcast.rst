.. Copyright 2013-2015 The Salish Sea MEOPAR contributors
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
        logger.debug('running in process {}'.format(os.getpid()))
        logger.debug('read config from {.config_file}'.format(parsed_args))
        lib.install_signal_handlers(logger, context)
        socket = lib.init_zmq_req_rep_worker(context, config, logger)

        # Do the work
        try:
            checklist = worker_function(config, ...)
            logger.info('success message')
            # Exchange success messages with the nowcast manager process
            lib.tell_manager(
                worker_name, 'success', config, logger, socket, checklist)
        except lib.WorkerError:
            # Exchange failure messages with nowcast manager process
            logger.critical('failure message')
            lib.tell_manager(worker_name, 'failure', config, logger, socket)
        except SystemExit:
            # Normal termination
            pass
        except:
            logger.critical('unhandled exception:')
            # Log the traceback from any unhandled exception
            for line in traceback.format_exc().splitlines():
                logger.error(line)
            # Exchange crash messages with the nowcast manager process
            lib.tell_manager(worker_name, 'crash', config, logger, socket)

        # Finish up
        context.destroy()
        logger.debug('task completed; shutting down')


    def worker_function(config, ...):
        ...
        return checklist


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

stanza at the end of the module.


Prepare The Worker
------------------

Lines 36 and 37 set up the worker's command-line interface and parse the command-line arguments:

.. code-block:: python

    parser = lib.basic_arg_parser(worker_name, description=__doc__)
    parsed_args = parser.parse_args()

The :py:func:`lib.basic_arg_parser` returns a command-line parser object with the file path/name of the :ref:`NowcastConfigFile` as a required argument,
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
    logger.debug('running in process {}'.format(os.getpid()))
    logger.debug('read config from {.config_file}'.format(parsed_args))

The settings that define where the log files are stored,
how their contents are formatted,
and how many days
(nowcast runs)
log files are preserved at included in the :ref:`NowcastConfigFile`.

The :option:`--debug` on the command-line sets the value of :kbd:`parsed_arg.debug` to :py:obj:`True`
(it defaults to :py:obj:`False`).

The :py:data:`logger` instance has a variety of method for sending messages to the logging system at different levels of importance.
We mostly use :py:meth:`logging.info` for generally informative messages,
:py:meth:`logging.debug` for message about deeper levels of execution,
and :py:meth:`logging.error` for error message.

Here,
we log the id number of the operating system process that the worker is running in,
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

The worker's ZeroMQ connection with the nowcast manager process is initialized in line 43 with:

.. code-block:: python

    socket = lib.init_zmq_req_rep_worker(context, config, logger)

The ZeroMQ socket object returned by :py:func:`~salishsea_tools.nowcast.lib.init_zmq_req_rep_worker` provides the communication channel for messages to be exchanged between the worker and the manager.
We are using a request/reply messaging pattern,
meaning that the manager is always listening for messages and the workers initiate exchanges by sending a message to the manager,
then waiting for an acknowledgement from the manager.

As we'll see below,
the :py:func:`salishsea_tools.nowcast.lib.tell_manager` function handles the details of the message exchanges with the manager;
all we have to do it pass the socket object into it.


Doing the Work
--------------

The block of code from line 46 through line 65 calls the function that does the actual work,
communicates with the nowcast manager,
and handles the exceptions that are raised when things go wrong.

First,
lets look at the exception handling:

.. code-block:: python

    try:
        checklist = worker_function(config, ...)
        logger.info('success message')
        # Exchange success messages with the nowcast manager process
        lib.tell_manager(
            worker_name, 'success', config, logger, socket, checklist)
    except lib.WorkerError:
        # Exchange failure messages with nowcast manager process
        logger.critical('failure message')
        lib.tell_manager(worker_name, 'failure', config, logger, socket)
    except SystemExit:
        # Normal termination
        pass
    except:
        logger.critical('unhandled exception:')
        # Log the traceback from any unhandled exception
        for line in traceback.format_exc().splitlines():
            logger.error(line)
        # Exchange crash messages with the nowcast manager process
        lib.tell_manager(worker_name, 'crash', config, logger, socket)

If everything goes according to plan,
only the code in the :kbd:`try:` stanza will be executed.

If the worker function encounters an expected error condition
(a file download failure or timeout, for example)
it should raise a :py:exc:`salishsea_tools.nowcast.lib.WorkerError` exception.
The :kbd:`except lib.WorkerError:` stanza catches that exception,
logs it at the critical level,
and tells the manager that the worker has failed.

The :py:exc:`SystemExit` exception is raised by the signal handler that we installed at line 42 when the worker is terminated by an interrupt or kill signal.
This is the normal termination path,
so we let that exception pass.

Finally,
the bare :kbd:`except:` stanza catches any unhandled exceptions,
logs their traceback at the error level so that we can diagnose the error,
and tells the manager that the worker crashed.


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

The nowcast manager and workers require several Python packages that are not part of the default :ref:`AnacondaPythonDistro` environment.
To avoid adding complexity and potential undesirable interactions and/or side-effects to the default Anaconda Python environment we create an isolated environment for nowcast.

Ensure that your :program:`conda` package manager is up to date:

.. code-block:: bash

    $ conda update conda

Create a new :program:`conda` environment with Python 2.7 and program:`pip` installed in it,
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
the package itself,
and its companion package :ref:`SalishSeaCmdProcessor`:

.. code-block:: bash

    (nowcast)$ conda install matplotlib netCDF4 numpy pandas pyyaml requests scipy
    (nowcast)$ pip install arrow angles
    (nowcast)$ cd MEOPAR/tools
    (nowcast)$ pip install --editable SalishSeaTools
    (nowcast)$ pip install --editable SalishSeaCmd

Install the additional packages that the nowcast manager and workers depend on:

* thee paramiko package that provides a Python implementation of the SSH2 protocol
* the Python bindings to the `ZeroMQ`_ messaging library
* the BeautifulSoup HTML parsing package

.. code-block:: bash

    (nowcast)$ conda install paramiko pyzmq
    (nowcast)$ pip install BeautifulSoup4

Finally,
install Sphinx,
the sphinx-bootstrap-theme,
and the mako template library used for the salishsea.eos.ubc.ca site:

.. code-block:: bash

    (nowcast)$ conda install sphinx
    (nowcast)$ pip install mako sphinx-bootstrap-theme

The above packages are sufficient to run the nowcast system.
For development and debugging of Python code,
:ref:`salishsea_tools.nowcast.figures` functions,
etc.,
you may also want to install IPython and IPython Notebook,
the pytest and coverage unit testing tools,
and the ipdb debugger:

.. code-block:: bash

    (nowcast)$ conda install ipython-notebook pytest coverage
    (nowcast)$ pip install ipdb

The complete list of Python packages installed including their version numbers (at time of writing) created by the :command:`conda env export` command is available in :file:`salishsea_tools/nowcast/environment.yaml`.
You can also use that file to do almost all of the above more succinctly with:

.. code-block:: bash

    $ cd MEOPAR/tools
    $ conda env create -f SalishSeaTools/salishsea_tools/nowcast/environment.yaml
    $ source activate nowcast
    (nowcast)$ pip install --editable SalishSeaTools
    (nowcast)$ pip install --editable SalishSeaCmd

To deactivate the :kbd:`nowcast` environment and return to your root Anaconda Python environment use:

.. code-block:: bash

    (nowcast)$ source deactivate


Directory Structure for Development and Testing
-----------------------------------------------

.. warning::

    Development and testing of nowcast workers, etc. should only be done on machines *other than* :kbd:`salish`.
    If you test on :kbd:`salish` your test runs will interact with the production nowcast manager process and,
    in all likelihood,
    cause other workers to run at in appropriate times,
    potentially disrupting the production real-time runs.

The directory structure described in this section mirrors the one used for the production deployment of the nowcast system.
It can be used to:

* test nowcast workers during development
* test rendering of page templates for the :kbd:`salishsea.eos.ubc.ca` site
* download EC weather model products in the event of an automation failure

The directory structure looks like::

  MEOPAR/
  `-- nowcast/
      |-- nowcast.yaml@
      `-- www/
          |-- salishsea-site/
          `-- templates@

:file:`nowcast.yaml` is a symlink to your :file:`MEOPAR/tools/SalishSeaTools/salishsea_tools/nowcast/nowcast.yaml` configuration file.

The :file:`salishsea-site/` directory tree is a clone of the :ref:`salishsea-site-repo` repo.
This clone is for automation testing only - you should not make commits in it.

:file:`templates` is a symlink to your :file:`MEOPAR/tools/SalishSeaTools/salishsea_tools/nowcast/www/templates/` directory,
where the templates for the pages that nowcast creates on the :kbd:`salishsea.eos.ubc.ca` site are stored.

So,
the commands to create the directory structure are:

.. code-block:: bash

    (nowcast)$ cd MEOPAR/
    (nowcast)$ mkdir -p nowcast/www/
    (nowcast)$ cd nowcast/
    (nowcast)$ ln -s ../tools/SalishSeaTools/salishsea_tools/nowcast/nowcast.yaml
    (nowcast)$ cd www/
    (nowcast)$ hg clone ssh://hg@bitbucket.org/salishsea/salishsea-site
    (nowcast)$ ln -s ../../tools/SalishSeaTools/salishsea_tools/nowcast/www/templates


Testing :kbd:`salishsea.eos.ubc.ca` Site Page Templates
-------------------------------------------------------

The pages that the nowcast automation maintains on the :kbd:`salishsea.eos.ubc.ca` site are generated from templates stored in :file:`MEOPAR/tools/SalishSeaTools/salishsea_tools/nowcast/www/templates/`.
Those templates are reStructuredText files that contain `Mako`_ directives that facilitate,
among other things,
substitution of concrete values (like specific dates) into placeholder variables,
and control structures like loops that simplify repetitive page elements (like collections of figure images),
and if-else blocks that allow conditional inclusion or exclusion of page elements.

.. _Mako: http://www.makotemplates.org/

So,
the process to get from a `Mako`_ page template to an HTML page happens in 2 stages:

#. Use a :py:class:`mako.template.Template` object derived from a :file:`.mako` file and a Python dict of placeholder variable names and values to render a :file:`.rst` file.

#. Use :command:`sphinx-build` to render the :file:`.rst` file to a :file:`.html` file.

In the nowcast production deployment the :file:`make_site_page.py` worker processes one or more page template(s) from the :file:`MEOPAR/tools/SalishSeaTools/salishsea_tools/nowcast/www/templates/` directory to create one or more :file:`.rst` file(s) in the :file:`MEOPAR/nowcast/www/salishsea-site/` directory tree.
When the :file:`make_site_page.py` worker sends a success message to the nowcast manager the :file:`push_to_web.py` worker is launched to:

#. Execute the :command:`hg update` command in :file:`MEOPAR/nowcast/www/salishsea-site/` to pull in any changes from other sources.

#. Execute the equivalent of :command:`make html` in the :file:`MEOPAR/nowcast/www/salishsea-site/site/` directory to run :command:`sphinx-build` to generate the new/changed pages of the site.

#. Execute an :command:`rsync` command to push the changes to the web server.

To test the rendering of site page templates we need to emulate the processing that the :file:`make_site_page.py` worker does and then run :command:`make html` in the :file:`MEOPAR/nowcast/www/salishsea-site/site/` directory so that we can preview the rendered page(s) from the :file:`MEOPAR/nowcast/www/salishsea-site/site/_build/html/` directory tree.

Since each page template contains a unique set of placeholder variables,
creating a general purpose template rendering test tool is probably more effort than it is worth.
Instead sample code that tests an early version of the template used to create the http://salishsea.eos.ubc.ca/storm-surge/forecast.html page is provided.
You can implement similar test code for other page templates in a Python script that you run from the command-line,
or in an IPython Notebook.

The template we're going to test looks like:

.. code-block:: mako

    ************************************************************************
    ${fcst_date.strftime('%A, %d %B %Y')} -- Salish Sea Storm Surge Forecast
    ************************************************************************

    Disclaimer
    ==========

    This site presents output from a research project.
    Results are not expected to be a robust prediction of the storm surge.


    Plots
    =====

    .. raw:: html
        <%
            run_dmy = run_date.strftime('%d%b%y').lower()
        %>
        %for svg_file in svg_file_roots:
        <object class="img-responsive" type="image/svg+xml"
          data="../_static/nemo/results_figures/forecast/${run_dmy}/${svg_file}_${run_dmy}.svg">
        </object>
        <hr>
        %endfor

    Model sea surface height has been evaluated through a series of hindcasts for significant surge events in 2006, 2009, and 2012 [1].

    [1] Soontiens, N., Allen, S., Latornell, D., Le Souef, K., Machuca, I., Paquin, J.-P., Lu, Y., Thompson, K., Korbel, V. (2015).  Storm surges in the Strait of Georgia simulated with a regional model. in prep.

The code below assumes that you are working in your :file:`MEOPAR/nowcast/` directory.

First some imports:

.. code-block:: python

    import datetime
    import os

    import mako.template

Create the template object from the :file:`.mako` file:

.. code-block:: python

    template_path = 'www/templates/'
    template_file = 'forecast.mako'
    mako_file = os.path.join(template_path, template_file)
    tmpl = mako.template.Template(filename=mako_file)

Now,
build the file name/path of the :file:`.rst` file that will be produces when we render the template:

.. code-block:: python

    site_path = 'www/salishsea-site/site/'
    page_path = 'storm-surge/'
    page_name = 'forecast.rst'
    rst_file = os.path.join(site_path, page_path, page_name)

Next,
calculate the template placeholder variables dict.
For this version of the forecast page we need the run date,
the forecast date,
and a list of figure image file name roots.

.. code-block:: python

    run_date = datetime.datetime.today()
    fcst_date = run_date + datetime.timedelta(days=1)
    vars = {
        'run_date': run_date,
        'fcst_date': fcst_date,
        'svg_file_roots': [
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
    }

Finally,
use the :py:meth:`render` method of the template object to create the :file:`.rst` file:

.. code-block:: python

    with open(rst_file, 'wt') as f:
        f.write(tmpl.render(**vars))

Putting it all together:

.. code-block:: python

    import datetime
    import os

    import mako.template


    # Load the template
    template_path = 'www/templates/'
    template_file = 'forecast.mako'
    mako_file = os.path.join(template_path, template_file)
    tmpl = mako.template.Template(filename=mako_file)

    # Calculate the file path/name of the .rst file
    site_path = 'www/salishsea-site/site/'
    page_path = 'storm-surge/'
    page_name = 'forecast.rst'
    rst_file = os.path.join(site_path, page_path, page_name)

    # Calculate the template placeholder variable values
    run_date = datetime.datetime.today()
    fcst_date = run_date + datetime.timedelta(days=1)
    vars = {
        'run_date': run_date,
        'fcst_date': fcst_date,
        'svg_file_roots': [
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
    }

    # Render the template
    with open(rst_file, 'wt') as f:
        f.write(tmpl.render(**vars))

Having executed the above code,
you should be able to go to :file:`MEOPAR/nowcast/www/salishsea-site/site/`,
execute :command:`make html`,
and preview the finished :file:`.html` page:

.. code-block:: bash

    (nowcast)$ cd MEOPAR/nowcast/www/salishsea-site/site/
    (nowcast)$ make html
    ...
    (nowcast)$ firefox _build/html/storm-surge/forecast.html
