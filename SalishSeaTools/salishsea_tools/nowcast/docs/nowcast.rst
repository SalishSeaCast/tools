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
and atmospheric forcing from the four-times daily produced forecast results from the Environment Canada GEM 2.5km resolution model.

The runs are automated using an asynchronous,
message-based architecture that:

* obtains the forcing datasets from web services
* pre-processes the forcing datasets into the formats expected by NEMO
* uploads the forcing dataset files to the HPC or cloud-computing facility where the run will be executed
* executes the run
* downloads the results
* prepares a collection of plots from the run results for monitoring purposes
* publishes the plots and the processing log to the web

The automation architecture is presently under development.
It consists of a long-running manager process and a collection of worker processes which are launched by the manager or cron to perform specific tasks.


.. _CreatingNowcastWorkers:

Creating Nowcast Workers
========================

Nowcast workers are Python modules that can be imported from :py:mod:`salishsea_tools.nowcast.workers`.
They are composed of some standard code to allow them to interface with the messaging and logging frameworks,
and one or more functions to execute their task in the nowcast system.
Most of the standard code is centred around instantiation of a :py:class:`SalishSeaTools.salishsea_tools.nowcast.nowcast_worker.NowcastWorker` object and executing method calls on it.

Here is a skeleton example of a worker module showing the standard code.
It is explained,
line by line,
below.
Actual
(and obviously, more complicated)
worker modules can be found in :file:`tools/SalishSeaTools/salishsea_tools/nowcast/workers/`.

.. note::
    The skeleton code below describes :py:class:`~SalishSeaTools.salishsea_tools.nowcast.nowcast_worker.NowcastWorker`-based workers.
    Not all workers have been re-implemented to use :py:class:`~SalishSeaTools.salishsea_tools.nowcast.nowcast_worker.NowcastWorker`.


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

    """Salish Sea NEMO nowcast ... worker.
    ...
    """
    import logging

    from .. import lib
    from ..nowcast_worker import NowcastWorker


    worker_name = lib.get_module_name()
    logger = logging.getLogger(worker_name)


    def main():
        worker = NowcastWorker(worker_name, description=__doc__)
        worker.run(worker_func, success, failure)


    def success(parsed_args):
        logger.info('success message')
        return 'success'


    def failure(parsed_args):
        logger.error('failure message')
        return 'failure'


    def worker_func(parsed_args, config):
        ...
        return checklist


    if __name__ == '__main__':
        main()

Lines 1 through 14 are our standard project copyright and license statement.
It uses :kbd:`#` comments rather than being enclosed in triple quotes to segregate it from the docstring which is used in automatic documentation generation and help text.

Lines 16 to 18 are the module's triple-quoted docstring.
As noted above,
it will appear in auto-generated documentation of the module.
For convenience we will also use the docstring as the description element of the worker's command-line help message,
although that can easily be changed if you prefer to put more details in the docstring than you want to appear in the help text.

The minimum set of imports that a worker needs are:

.. code-block:: python

    import logging

    from .. import lib
    from ..nowcast_worker import NowcastWorker

The :py:mod:`logging` module provides the mechanism that we use to print output about the worker's progress and status to the log file or the screen,
effectively developer-approved print statements on steroids :-)
The :ref:`salishsea_tools.nowcast.lib` is our collection of functions that are used across workers.
If you find yourself writing the same function in more than one worker it should probably be generalized and included in :py:mod:`lib`.
The :py:class:`NowcastWorker` class provides the interface to the nowcast framework.
We use relative imports for :py:mod:`lib` and :py:class:`NowcastWorker` because they are defined within the :py:mod:`SalishSeaNowcast` package.

Obviously you will need to import whatever other modules your worker needs for its task.

Next up are 2 module level variables:

.. code-block:: python

    worker_name = lib.get_module_name()
    logger = logging.getLogger(worker_name)

:py:data:`worker_name` is used to identify the source of logging message and message exchanged between the worker and the nowcast manager process. :py:func:`~SalishSeaTools.salishsea_tools.nowcast.lib.get_module_name` provides the worker's module name stripped of its path and :kbd:`.py` suffix.

:py:data:`logger` is our interface to the logging framework and we give this module's instance the worker's name.

Python scoping rules make module level variables available for use in any functions in the module without passing them as arguments but assigning new values to them elsewhere in the module will surely mess things up.


The :py:func:`main` Function
----------------------------

The :py:func:`main` function is where our worker gets down to work.
It is called when the worker is run from the command line by virtue of the

.. code-block:: python

    if __name__ == '__main__':
        main()

stanza at the end of the module.

The minimum possible :py:func:`main` functions is shown in lines 32 to 34:

.. code-block:: python

    def main():
        worker = NowcastWorker(worker_name, description=__doc__)
        worker.run(worker_func, success, failure)

First,
we create an instance of the :py:class:`~SalishSeaTools.salishsea_tools.nowcast.nowcast_worker.NowcastWorker` class that we call,
by convention,
:py:data:`worker`.
The :py:class:`~SalishSeaTools.salishsea_tools.nowcast.nowcast_worker.NowcastWorker` constructor takes 2 arguments:

* the :py:data:`worker_name` that we defined as a module-level variable above
* a :py:data:`description` string that is used as the description element of the worker's command-line help message;
  here we use the worker's module docstring
  (that is automatically stored in the :py:data:`__doc__` module-level variable)

See the :py:class:`nowcast.nowcast_worker.NowcastWorker` documentation for details of the :py:class:`~SalishSeaTools.salishsea_tools.nowcast.nowcast_worker.NowcastWorker` object's contructor arguments,
other attributes,
and methods.

Second,
we call the :py:meth:`run` method on the :py:data:`worker` to do the actual work.
The :py:meth:`run` method takes 3 function names as arguments:

* :py:data:`worker_func` is the name of the function that does the worker's job
* :py:data:`success` is the name of the function to be called when the worker finishes successfully
* :py:data:`failure` is the name of the function to be caled when the worker fails

All 3 functions must be defined in the worker module.
Their required call signatures and return values are described below.

It is also possible to add command-line arguments to the :py:data:`worker`.
See :ref:`ExtendingTheCommandLineParser`.


:py:func:`success` and :py:func:`failure` Functions
---------------------------------------------------

The :py:func:`success` function is called when the worker successfully completes its task.
It is used to generate the message that is sent to the nowcast manager process to indicate the worker's success so that the nowcast automation can proceed to the next appropriate worker(s).
A minimal :py:func:`success` function is shown in lines 34 through 36:

.. code-block:: python

    def success(parsed_args):
        logger.info('success message')
        return 'success'

The name of the function is :py:func:`success` by convention,
but it could be anything provided that it is the 2nd argument passed to the :py:meth:`worker.run` method.

The :py:func:`success` function must accept exactly 1 argument,
named :py:data:`parsed_args` by convention.
It is an :py:obj:`argparse.Namespace` object that has the worker's command-line argument names and values as attributes.
The :py:data:`parsed_args` argument must be accepted even by :py:func:`success` functions that don't use it.

The :py:func:`success` function should emit a message to the logging system at the :py:data:`logging.INFO` level that describes the worker's success.

The :py:func:`success` function must return a string that is the key of a message type that is registered for the worker in the :ref:`NowcastConfigFile`.
The returned message type is used to send a message indicating the worker's success to the nowcast manager process.

Here is a more sophisticated example of a :py:func:`success` function from the :py:mod:`download_weather` worker:

.. code-block:: python

    def success(parsed_args):
        logger.info(
            'weather forecast {.forecast} downloads complete'
            .format(parsed_args))
        msg_type = 'success {.forecast}'.format(parsed_args)
        return msg_type

The :py:func:`failure` function is very similar to the :py:func:`success` function except that it is called if the worker fails to complete its task.
It is used to generate the message that is sent to the nowcast manager process to indicate the worker's failure so that appropriate notifications can be produces and/or remedial action(s) taken.
A minimal :py:func:`failure` function is shown on lines 39 through 41:

.. code-block:: python

    def failure(parsed_args):
        logger.error('failure message')
        return 'failure'

The name of the function is :py:func:`failure` by convention,
but it could be anything provided that it is the 3rd argument passed to the :py:meth:`worker.run` method.

Like the :py:func:`success` function,
the :py:func:`failure` function must accept exactly 1 argument,
named :py:data:`parsed_args` by convention.
It is an :py:obj:`argparse.Namespace` object that has the worker's command-line argument names and values as attributes.
The :py:data:`parsed_args` argument must be accepted even by :py:func:`failure` functions that don't use it.

The :py:func:`failure` function should emit a message to the logging system at the :py:data:`logging.ERROR` level that describes the worker's failure.

The :py:func:`failure` function must return a string that is the key of a message type that is registered for the worker in the :ref:`NowcastConfigFile`.
The returned message type is used to send a message indicating the worker's failure to the nowcast manager process.


Doing the Work
--------------

Lines 44 through 46 show the required call signature and return value for the function that is called to do the worker's task:

.. code-block:: python

    def worker_func(parsed_args, config):
        ...
        return checklist

The name of the function can be anything provided that it is the 1st argument passed to the :py:meth:`worker.run` method.
Ideally,
the function name should be descriptive of the worker's task.
If you can't think of anything else,
you can use the name of the worker module.

The function must accept exactly 2 arguments:

* The 1st argument is named :py:data:`parsed_args` by convention.
  It is an :py:obj:`argparse.Namespace` object that has the worker's command-line argument names and values as attributes.
  The :py:data:`parsed_args` argument must be accepted even by worker functions that don't use it.

* The 2nd argument is named :py:data:`config` by convention.
  It is a Python :py:obj:`dict` containing the keys and values read from the :ref:`NowcastConfigFile`.
  The :py:data:`config` argument must be accepted even by worker functions that don't use it.

The function must return a Python :py:obj:`dict`,
known as :py:data:`checklist` by convention.
:py:data:`checklist` must contain at least 1 key/value pair that provides information about the worker's successful completion.
:py:data:`checklist` is sent to the nowcast manager process as the payload of the worker's success message.
A simple example of a :py:data:`checklist` from the :py:mod:`download_weather` worker is:

.. code-block:: python

    checklist = {'{} forecast'.format(forecast): True}

which just indicates that the particular forecast download was successful.
A more sophisticated :py:data:`checklist` such as the one produced by the :py:mod:`SalishSeaTools.salishsea_tools.nowcast.workers.get_NeahBay_ssh` worker contains multiple keys and lists of filenames.

The function whose name is passed as the 1st argument passed to the :py:meth:`worker.run` method can be a driver function that calls other functions in the worker module to subdivide the worker task into smaller,
more readable,
and more testable sections.
By convention,
such "2nd level" functions are marked as private by prefixing their names with the :kbd:`_` (underscore) character;
e.g. :py:func:`_calc_date`.
This in line with the Python language convention that functions and methods that start with an underscore should not be called outside the module in which they are defined.

The worker should emit messages to the logging system that indicate its progress.
Messages logged at the :py:data:`logging.INFO` level via :py:func:`logger.info` appear in the :file:`nowcast.log` file.
That logging level should be used for "high level" progress messages,
and preferrably not used inside loops.
:py:data:`logging.DEBUG` level messages logged via :py:func:`logger.debug` can be used for more detailed logging.
Those messages appear in the :file:`nowcast.debug.log` file.

If a worker function encounters an expected error condition
(a file download failure or timeout, for example)
it should emit a message to the logging system at the :py:data:`logging.CRITICAL` level via :py:func:`logger.critical` and raise a :py:exc:`salishsea_tools.nowcast.lib.WorkerError` exception.
Here is an example that handles an empty downloaded file in the :py:mod:`download_weather` worker:

.. code-block:: python

    if size == 0:
        logger.critical('Problem, 0 size file {}'.format(fileURL))
        raise lib.WorkerError

This sections has only outlined the basic code structure and conventions for writing nowcast workers.
The best way to learn now to write a new worker is by studying the code in the existing worker modules in :file:`SalishSeaTools/salishsea_tools/nowcast/workers/`.


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

.. _SalishSeaNowcastPythnonPackageEnvironmwnt:

Salish Sea Nowcast Python Package Environment
---------------------------------------------

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

.. _ZeroMQ: http://zeromq.org/

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


.. _SalishSeaNowcastDirectoryStructure:

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


Mitigating a :mod:`download_weather` Worker Failure
---------------------------------------------------

The Environment Canada (EC) 2.5 km resolution GEM forecast model products from the High Resolution Deterministic Prediction System (HDRPS) are critical inputs for the nowcast system.
They are also the only input source that is transient -
each of the 4 daily forecast data sets are only available for slightly over a day,
and EC does not maintain an archive of the HDRPS products.

The HDRPS products files that we use are downloaded every 6 hours via the :py:mod:`SalishSeaTools.salishsea_tools.nowcast.workers.download_weather` worker.
The downloads are controlled by 4 :program:`cron` jobs that run on :kbd:`salish`:

  * The :kbd:`06` forecast download starts at 04:00
  * The :kbd:`12` forecast download starts at 10:00
  * The :kbd:`18` forecast download starts at 16:00
  * The :kbd:`00` forecast download starts at 22:00

The :py:mod:`download_weather` worker uses an exponential back-off and retry strategy to try very hard to get the required files in the face of network congestion and errors.
If things are going really badly it can take nearly 5 hours to complete or fail to complete a forecast download.
If a failure does occur the `info log file`_ will contain a :kbd:`CRITICAL` message like::

  2015-07-08 10:00:03 INFO [download_weather] downloading 12 forecast GRIB2 files for 20150708
  2015-07-08 14:57:29 CRITICAL [download_weather] unhandled exception:
  2015-07-08 14:57:29 ERROR [download_weather] Traceback (most recent call last):
  ...

followed by the traceback from the error that caused the failure.
The `debug log file`_ will show more details about the specific file downloads and will also include the :kbd:`CRITICAL` log message.

.. _info log file: eoas.ubc.ca/~dlatorne/MEOPAR/nowcast/nowcast.log
.. _debug log file: eoas.ubc.ca/~dlatorne/MEOPAR/nowcast/nowcast.debug.log

In the rare event that the nowcast automation system fails to download the HDRPS products every 6 hours via the :py:mod:`SalishSeaTools.salishsea_tools.nowcast.workers.download_weather` worker,
it is critical that someone re-run that worker.
Even if the worker cannot be re-run in the nowcast system deployment environment on :kbd:`salish` due to permission issues the forecast products can be downloaded using a development and testing environment and directory structure as described above
(see :ref:`SalishSeaNowcastPythnonPackageEnvironmwnt` and :ref:`SalishSeaNowcastDirectoryStructure`).
That can be accomplished as follows:

#. Activate your nowcast :program:`conda` environment,
   and navigate to your nowcast development and testing environment:

   .. code-block:: bash

       $ source activate nowcast
       (nowcast)$ cd MEOPAR/nowcast/

#. Edit the :file:`MEOPAR/nowcast/nowcast.yaml` file to set a destination in your filespace for the GRIB2 files that the worker downloads:

   .. code-block:: yaml

       weather:
         # Destination directory for downloaded GEM 2.5km operational model GRIB2 files
         # GRIB_dir: /ocean/sallen/allen/research/MEOPAR/GRIB/
         GRIB_dir: /ocean/<your_userid>/MEOPAR/GRIB/

   .. note::

        The directory :file:`/ocean/<your_userid>/MEOPAR/GRIB/` must exist.
        Create it if necessary with:

        .. code-block:: bash

            $ mkdir -p /ocean/<your_userid>/MEOPAR/GRIB/

#. Run the :py:mod:`SalishSeaTools.salishsea_tools.nowcast.workers.download_weather` worker for the appropriate forecast with debug logging,
   for example:

   .. code-block:: bash

       (nowcast)$ python -m salishsea_tools.nowcast.workers.download_weather nowcast.yaml 12 --debug

   You will need to hit :kbd:`Ctrl-C` at least once (maybe twice) to terminate the worker because it ends by waiting indefinitely for confirmation of its success or failure from the nowcast manager.

   The command above downloads the 12 forecast.
   The :kbd:`--debug` flag causes the logging output of the worker to be displayed on the screen (so that you can see what is going on) instead of being written to a file.
   The (abridged) output should look like::

     2015-07-08 17:59:34 DEBUG [download_weather] running in process 5506
     2015-07-08 17:59:34 DEBUG [download_weather] read config from nowcast.yaml
     2015-07-08 17:59:34 DEBUG [download_weather] connected to localhost port 5555
     2015-07-08 17:59:34 INFO [download_weather] downloading 12 forecast GRIB2 files for 20150708
     2015-07-08 17:59:34 INFO [download_weather] downloading 12 forecast GRIB2 files for 20150708
     2015-07-08 17:59:37 DEBUG [download_weather] downloaded 248557 bytes from http://dd.weather.gc.ca/model_hrdps/west/grib2/12/001/CMC_hrdps_west_UGRD_TGL_10_ps2.5km_2015070812_P001-00.grib2
     2015-07-08 17:59:40 DEBUG [download_weather] downloaded 253914 bytes from http://dd.weather.gc.ca/model_hrdps/west/grib2/12/001/CMC_hrdps_west_VGRD_TGL_10_ps2.5km_2015070812_P001-00.grib2
     2015-07-08 17:59:42 DEBUG [download_weather] downloaded 47222 bytes from http://dd.weather.gc.ca/model_hrdps/west/grib2/12/001/CMC_hrdps_west_DSWRF_SFC_0_ps2.5km_2015070812_P001-00.grib2

     ...

     2015-07-08 18:16:49 DEBUG [download_weather] downloaded 71893 bytes from http://dd.weather.gc.ca/model_hrdps/west/grib2/12/048/CMC_hrdps_west_APCP_SFC_0_ps2.5km_2015070812_P048-00.grib2
     2015-07-08 18:16:52 DEBUG [download_weather] downloaded 135163 bytes from http://dd.weather.gc.ca/model_hrdps/west/grib2/12/048/CMC_hrdps_west_PRMSL_MSL_0_ps2.5km_2015070812_P048-00.grib2
     2015-07-08 18:16:52 INFO [download_weather] weather forecast 12 downloads complete
     2015-07-08 18:16:52 INFO [download_weather] weather forecast 12 downloads complete
     2015-07-08 18:16:52 DEBUG [download_weather] sent message: (success 12) 12 weather forecast ready
     ^C
     2015-07-08 18:22:52 INFO [download_weather] interrupt signal (SIGINT or Ctrl-C) received; shutting down
     2015-07-08 18:22:52 INFO [download_weather] interrupt signal (SIGINT or Ctrl-C) received; shutting down
     ^C
     2015-07-08 18:22:57 INFO [download_weather] interrupt signal (SIGINT or Ctrl-C) received; shutting down
     2015-07-08 18:22:57 INFO [download_weather] interrupt signal (SIGINT or Ctrl-C) received; shutting down
     2015-07-08 18:22:57 DEBUG [download_weather] task completed; shutting down

You can use the :kbd:`-h` or :kbd:`--help` flags to get a usage message that explains the worker's required arguments,
and its option flags:

.. code-block:: bash

    (nowcast)$ python -m salishsea_tools.nowcast.workers.download_weather --help

.. code-block:: none

    usage: python -m salishsea_tools.nowcast.workers.download_weather
           [-h] [--debug] [--yesterday] config_file {18,00,12,06}

    Salish Sea NEMO nowcast weather model dataset download worker. Download the
    GRIB2 files from today's 00, 06, 12, or 18 EC GEM 2.5km HDRPS operational
    model forecast.

    positional arguments:
      config_file    Path/name of YAML configuration file for Salish Sea NEMO
                     nowcast.
      {18,00,12,06}  Name of forecast to download files from.

    optional arguments:
      -h, --help     show this help message and exit
      --debug        Send logging output to the console instead of the log file;
                     intended only for use when the worker is run in foreground
                     from the command-line.
      --yesterday    Download forecast files for previous day's date.

The :kbd:`--yesterday` flag allows you to download the previous day's forecast files.
Use that flag only during the several hour period for which two day's forecast files exist in the http://dd.weather.gc.ca/model_hrdps/west/grib2/ file space.
To determine if the :kbd:`--yesterday` flag can be used check the contents of a forecast's hourly directories;
e.g. http://dd.weather.gc.ca/model_hrdps/west/grib2/06/001/,
to see if files for 2 days exist.


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


.. _salishsea_tools.nowcast.nowcast_worker:

:py:mod:`nowcast.nowcast_worker` Module
=======================================

.. automodule:: nowcast.nowcast_worker
    :members:
