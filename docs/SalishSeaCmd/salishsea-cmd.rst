.. Copyright 2013 The Salish Sea MEOPAR conttributors
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


.. _SalishSeaCmdProcessor:

*********************************
Salish Sea NEMO Command Processor
*********************************

The Salish Sea NEMO command processor,
:program:`salishsea`,
is a command line tool for doing various operations associated with the :ref:`SalishSeaNEMO` model.


Installation
============

These instructions assume that:

* You have an up to date clone of the `tools repo`_
* You have the :ref:`AnacondaPythonDistro` installed
* :file:`$HOME/anaconda/bin` is included in your :envvar:`PATH` environment variable

.. _tools repo: https://bitbucket.org/salishsea/tools/

Use :program:`pip`
(the Python package installer)
to install the :kbd:`SalishSeaCmd` package from the `tools repo`_ in editable mode so that :program:`salishsea` will be automatically updated as the repo evolves:

.. code-block:: bash

    cd tools/SalishSeaCmd
    pip install --editable .

Experienced Python developers may wish to install :program:`salishsea` in other ways:

* In a Python virtual environment
* In :file:`$HOME/.local/` via the :command:`pip install --user` option


Available Commands
==================

The command :program:`salishsea` or :command:`salishsea --help` produces a list of the available :program:`salishsea` options and sub-commands:

.. code-block:: bash

    salishsea --help
    usage: salishsea [-h] [--version] {combine,prepare} ...

    optional arguments:
      -h, --help         show this help message and exit
      --version          show program's version number and exit

    sub-commands:
      {combine,prepare}
        combine          Combine results from an MPI Salish Sea NEMO run.
        prepare          Prepare a Salish Sea NEMO run

    Use `salishsea <sub-command> --help` to get detailed help about a sub-command.

For details of the arguments and options for a sub-command use
:command:`salishsea <sub-command> --help`.
For example:

.. code-block:: bash

    salishsea combine --help
    usage: salishsea combine [-h] [--keep-proc-results] [--no-compress]
                             [--compress-restart] [--delete-restart] [--version]
                             DESC_FILE RESULTS_DIR

    Combine the per-processor results files from an MPI Salish Sea NEMO run
    described in DESC_FILE into files in RESULTS_DIR and compress them using gzip.
    Delete the per-processor files. If RESULTS_DIR does not exist it will be
    created.

    positional arguments:
      DESC_FILE            run description YAML file
      RESULTS_DIR          directory to store results into

    optional arguments:
      -h, --help           show this help message and exit
      --keep-proc-results  don't delete per-processor results files
      --no-compress        don't compress results files
      --compress-restart   compress restart file(s)
      --delete-restart     delete restart file(s)
      --version            show program's version number and exit

You can check what version of :program:`salishsea` you have installed with:

.. code-block:: bash

    salishsea --version


:kbd:`prepare` Sub-command
--------------------------

The :command:`salishsea prepare` command sets up a run directory from which to execute the Salish Sea NEMO run described in the specifed run description,
namelist,
and IOM server definitions files:

.. code-block:: bash

    salishsea prepare --help
    usage: salishsea prepare [-h] [-q] [--version] DESC_FILE NAMELIST IO_DEFS

    Set up the Salish Sea NEMO run described in DESC_FILE and print the path to
    the run directory.

    positional arguments:
      DESC_FILE    run description YAML file
      NAMELIST     NEMO namelist file for run
      IO_DEFS      NEMO IOM server defs file for run

    optional arguments:
      -h, --help   show this help message and exit
      -q, --quiet  don't show the run directory path on completion
      --version    show program's version number and exit

The path to the run directory is printed upon completion of the command.

The name of the run directory created is a Universally Unique Identifier
(UUID)
string because the directory is intended to be ephemerally used for a single run.

The run directory contains symbolic links to:

* the run description file provided on the command line

* the namelist file provided on the command line,
  aliased as :file:`namelist`,
  the file name expected by NEMO

* the IOM server definitions files provided on the command line,
  aliased to :file:`iodefs.xml`,
  the file name expected by NEMO

* the :file:`xmlio_server.def` file found in the run-set directory where the run description file resides

* the :file:`nemo.exe` and :file:`server.exe` executables found in the :file:`BLD/bin/` directory of the NEMO configuration given by the :kbd:`config_name` and :kbd:`NEMO-code` keys in the run description file.
  :command:`salishsea prepare` aborts with an error message and exit code 2 if the :file:`nemo.exe` file is not found.


Run Description File Structure
==============================

:program:`salishsea` run description files are written in YAML_.
They contain key-value pairs that define the names and locations of files and directories that :program:`salishsea` uses to manage Salish Sea NEMO runs and their results.

.. _YAML: http://pyyaml.org/wiki/PyYAMLDocumentation

.. note::

    The :program:`salishsea` tool is under active development and the format of the run description file is changing frequently.

Example:

.. literalinclude:: ../../../SS-run-sets/JPP/JPP.yaml
   :language: yaml

The :kbd:`paths` section of the run description file is a collection of directory paths that :program:`salishsea` uses to find files in other repos that it needs.
The paths may be either absolute or relative.

* The value associated with the :kbd:`NEMO-code` key is the path to the :ref:`NEMO-code-repo` clone where the :file:`rebuild-nemo` tool,
  the NEMO executable,
  etc. for the run are to be found.

