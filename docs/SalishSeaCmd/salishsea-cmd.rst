.. Copyright 2013-2014 The Salish Sea MEOPAR conttributors
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
* You have installed the :ref:`SalishSeaTools` package

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


:kbd:`<TAB>` Completion
-----------------------

The :program:`salishsea` command line interface includes a sub-command that enables it to hook into the :program:`bash` :kbd:`<TAB>` completion machinery.
(:kbd:`<TAB>` completion or `command-line completion`_ is a shell feature whereby partially typed commands are filled out by the shell when the user presses the :kbd:`<TAB>` key.)
The :command:`salishsea complete` command prints a blob of :program:`bash` code that does the job,
so,
capturing that code in a file and then executing it with the :command:`source` command will enable completion for :program:`salishsea` in your current shell session.
You can do that with the compound command:

.. code-block:: bash

    salishsea complete > foo.sh && source foo.sh && rm -f foo.sh

Including that line in your :file:`~/.bashrc` file will ensure that completion for :program:`salishsea` is available in every shell you launch.

.. _command-line completion: http://en.wikipedia.org/wiki/Command-line_completion


Available Commands
==================

The command :command:`salishsea --help` produces a list of the available :program:`salishsea` options and sub-commands:

.. program-output:: echo $PATH; which salishsea

For details of the arguments and options for a sub-command use
:command:`salishsea help <sub-command>`.
For example:

.. program-output:: salishsea help gather

You can check what version of :program:`salishsea` you have installed with:

.. code-block:: bash

    salishsea --version


.. _salishsea-gather:

:kbd:`gather` Sub-command
-------------------------

The :command:`salishsea gather` command gather results from a Salish Sea NEMO run into a results directory. Its operation includes running the :command:`salishsea combine` command to combine the pre-processor MPI results files.

.. program-output:: salishsea help gather


.. _salishsea-get_cgrf:

:kbd:`get_cgrf` Sub-command
---------------------------

The :command:`salishsea get_cgrf` command downloads CGRF products atmospheric forcing files from Dalhousie rsync
repository and symlink with the file names that NEMO expects:

.. program-output:: salishsea help get_cgrf

The command *must* be run in the :file:`/ocean/dlatorne/CGRF/` directory.


.. _salishsea-prepare:

:kbd:`prepare` Sub-command
--------------------------

The :command:`salishsea prepare` command sets up a run directory from which to execute the Salish Sea NEMO run described in the specifed run description,
namelist,
and IOM server definitions files:

.. program-output:: salishsea help prepare

The path to the run directory is printed upon completion of the command.

The name of the run directory created is a Universally Unique Identifier
(UUID)
string because the directory is intended to be ephemerally used for a single run.

The run directory contains a :file:`namelist`
(the file name expected by NEMO)
file that is constructed by concatenating the namelist segments listed in the run description file
(see :ref:`RunDescriptionFileStructure`).
That constructed namelist is concluded with empty instances of all of the namelists that NEMO requires so that default values will be used for any namelist variables not included in the namelist segments listed in the run description file.

The run directory also contains symbolic links to:

* The run description file provided on the command line

* The namelist file provided on the command line,
  aliased as :file:`namelist`,
  the file name expected by NEMO

* The IOM server definitions files provided on the command line,
  aliased to :file:`iodefs.xml`,
  the file name expected by NEMO

* The :file:`xmlio_server.def` file found in the run-set directory where the run description file resides

* The :file:`nemo.exe` and :file:`server.exe` executables found in the :file:`BLD/bin/` directory of the NEMO configuration given by the :kbd:`config_name` and :kbd:`NEMO-code` keys in the run description file.
  :command:`salishsea prepare` aborts with an error message and exit code 2 if the :file:`nemo.exe` file is not found.
  In that case the run directory is not created.
  :command:`salishsea prepare` also check to confirm that :file:`server.exe` exists but only issues a warning if it is not found becuase that is a valid situation if you are not using :kbd:`key_iomput` in your configuration.

* The coordinates and bathymetry files given in the :kbd:`grid` section of the run description file

* The initial conditions,
  open boundary conditions,
  and rivers run-off forcing directories given in the :kbd:`forcing` section of the run description file.
  The initial conditions may be specified from a restart file instead of a directory of netCDF files,
  in which case the restart file is synlinked as :file:`restart.nc`,
  the file name expected by NEMO.

See the :ref:`RunDescriptionFileStructure` section for details of the run description file.

The :command:`salishsea prepare` command concludes by printing the path to the run directory it created.
Example:

.. code-block:: bash

    salishsea prepare SalishSea.yaml namelist.1h iodef.xml
    Created run directory ../../runs/SalishSea/38e87e0c-472d-11e3-9c8e-0025909a8461


.. _RunDescriptionFileStructure:

Run Description File Structure
==============================

:program:`salishsea` run description files are written in YAML_.
They contain key-value pairs that define the names and locations of files and directories that :program:`salishsea` uses to manage Salish Sea NEMO runs and their results.

.. _YAML: http://pyyaml.org/wiki/PyYAMLDocumentation

Example:

.. literalinclude:: SalishSea.yaml.example
   :language: yaml

The value associated with the :kbd:`config_name` key is the name of the NEMO configuration to use for runs.
It is the name of a directory in :file:`NEMO-code/NEMOGCM/CONFIG/`.

The :kbd:`paths` section of the run description file is a collection of directory paths that :program:`salishsea` uses to find files in other repos that it needs.
The paths may be either absolute or relative.

* The value associated with the :kbd:`NEMO-code` key is the path to the :ref:`NEMO-code-repo` clone where the NEMO executable,
  etc. for the run are to be found.

* The :kbd:`forcing` key value is the path to the :ref:`NEMO-forcing-repo` clone where the netCDF files for the grid coordinates,
  bathymetry,
  initial conditions,
  open boundary conditions,
  etc. are found.

* The :kbd:`runs directory` key gives the path to the directory where run directories will be created by the :command:`salishsea prepare` sub-command.

The :kbd:`grid` section of the file contains 2 keys that provide the names of the coordinates and bathymetry files to use for the run.
Those file are presumed to be in the :file:`grid/` directory of the :ref:`NEMO-forcing-repo` clone pointed to by the :kbd:`forcing` key in the :kbd:`paths` section.

The :kbd:`forcing` section of the run description file contains 3 keys that provide the names of directories in the :ref:`NEMO-forcing-repo` where initial conditions and forcing files are found.
Those directory names are used in the appropriate places in the namelist.

The value associated with the :kbd:`atmospheric` key is the path to the :ref:`AtmosphericForcing` files.
It is symlinked as :file:`NEMO-atmos/` in the run directory,
and that directory name is used on the :kbd:`namsbc_core` namelist.

The :kbd:`initial conditions` key can,
alternatively,
be used to give the path to and name of a restart file,
e.g.:

.. code-block:: yaml

    initial conditions: ../../SalishSea/results/50s_22-25Sep/SalishSea_00019008_restart.nc

which will be symlinked in the run directory as :file:`restart.nc`.

The :kbd:`namelists` section of the run description file contains a list of NEMO namelist segments that will be concatenated to construct the :file:`namelist` file for the run.
That constructed :file:`namelist` is concluded with empty instances of all of the namelists that NEMO requires so that default values will be used for any namelist variables not included in the namelist segments listed in the run description file.
The blob of empty namelist instances is defined as a constant in the :py:mod:`salishsea_cmd.prepare_processor` module in the :py:mod:`SalishSeaCmd` package.


.. _salishsea-api:

API
===

This section documents the Salish Sea Nemo command processor Application Programming Interface (API).
The API provides Python function interfaces to command processor sub-commands for use in other sub-command processor modules,
and by other software.

.. autofunction:: api.combine
