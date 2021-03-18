.. Copyright 2013-2021 The Salish Sea MEOPAR contributors
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


.. _SalishSeaToolsPackageDevelopment:

*****************************************
:kbd:`SalishSeaTools` Package Development
*****************************************

.. _SalishSeaToolsPythonVersions:

Python Versions
===============

The :kbd:`SalishSeaTools` package is developed and tested using `Python`_ 3.9.
The package uses some Python language features that are not available in versions prior to 3.6,
in particular:

* `formatted string literals`_
  (aka *f-strings*)
* the `file system path protocol`_

.. _Python: https://www.python.org/
.. _formatted string literals: https://docs.python.org/3/reference/lexical_analysis.html#f-strings
.. _file system path protocol: https://docs.python.org/3/whatsnew/3.6.html#whatsnew36-pep519


.. _SalishSeaToolsGettingTheCode:

Getting the Code
================

Clone the code and documentation `repository`_ from GitHub with:

.. _repository: https://github.com/SalishSeaCast/tools

.. code-block:: bash

    $ git clone git@github.com:SalishSeaCast/tools.git


.. _SalishSeaToolsDevelopmentEnvironment:

Development Environment
=======================

Setting up an isolated development environment using `Conda`_ is recommended.
Assuming that you have `Miniconda`_ installed,
you can create and activate an environment called :kbd:`salishsea-tools` that will have all of the Python packages necessary for development,
testing,
and building the documentation with the commands:

.. _Conda: https://conda.io/en/latest/
.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html

.. code-block:: bash

    $ cd tools
    $ conda env create -f SalishSeaTools/environment.yaml
    $ conda activate salishsea-tools
    (salishsea-tools)$ pip install --editable SalishSeaTools

The :kbd:`--editable` option in the :command:`pip install` commands above installs the :kbd:`SalishSeaTools` from the cloned repo via symlinks so that it will be automatically updated as the repos evolve.

To deactivate the environment use:

.. code-block:: bash

    (salishsea-tools)$ conda deactivate


.. _SalishSeaToolsBuildingTheDocumentation:

Building the Documentation
==========================

The documentation for the :kbd:`SalishSeaTools` package is written in `reStructuredText`_ and converted to HTML using `Sphinx`_.
Creating a :ref:`SalishSeaToolsDevelopmentEnvironment` as described above includes the installation of Sphinx.
The documentation is integrated into the :ref:`tools-repo` docs.
Building the documentation is driven by :file:`tools/docs/Makefile`.
With your :kbd:`salishsea-tools` development environment activated,
use:

.. _reStructuredText: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _Sphinx: https://www.sphinx-doc.org/en/master/

.. code-block:: bash

    (salishsea-tools)$ cd tools
    (salishsea-tools)$ (cd docs && make clean html)

to do a clean build of the documentation.
The output looks something like::

  rm -rf _build/*
  sphinx-build -b html -d _build/doctrees   . _build/html
  Running Sphinx v1.3.1
  making output directory...
  loading pickled environment... not yet created
  loading intersphinx inventory from http://salishsea-meopar-docs.readthedocs.org/en/latest/objects.inv...
  building [mo]: targets for 0 po files that are out of date
  building [html]: targets for 40 source files that are out of date
  updating environment: 40 added, 0 changed, 0 removed
  reading sources... [100%] results_server/nowcast-green
  looking for now-outdated files... none found
  pickling environment... done
  checking consistency... done
  preparing documents... done
  writing output... [100%] results_server/nowcast-green
  generating indices...
  highlighting module code... [100%] salishsea_tools.hg_commands
  writing additional pages... search
  copying static files... done
  copying extra files... done
  dumping search index in English (code: en) ... done
  dumping object inventory... done
  build succeeded.

The HTML rendering of the docs ends up in :file:`tools/docs/_build/html/`.
You can open the :file:`SalishSeaTools/index.html` file in that directory tree in your browser to preview the results of the build before committing and pushing your changes to Bitbucket.

Whenever you push changes to the :ref:`tools-repo` on Bitbucket the documentation is automatically re-built and rendered at https://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/.


.. _SalishSeaToolsRuningTheUnitTests:

Running the Unit Tests
======================

The test suite for the :kbd:`SalishSeaTools` package is in :file:`tools/SalishSeaTools/tests/`.
The `pytest`_ tools is used for test fixtures and as the test runner for the suite.

.. _pytest: https://docs.pytest.org/en/latest/

With your :kbd:`salishsea-tools` development environment activated,
use:

.. code-block:: bash

    (salishsea-tools)$ cd tools/SalishSeaTools/
    (salishsea-tools)$ py.test

to run the test suite.
The output looks something like::

  ============================ test session starts =============================
  platform linux -- Python 3.5.1, pytest-2.8.5, py-1.4.31, pluggy-0.3.1
  rootdir: /home/doug/Documents/MEOPAR/tools/SalishSeaTools, inifile:
  collected 189 items

  tests/test_bathy_tools.py ........
  tests/test_hg_commands.py ...........
  tests/test_namelist.py ..............
  tests/test_nc_tools.py ...............................................
  tests/test_stormtools.py ....
  tests/test_teos_tools.py ............
  tests/test_tidetools.py .
  tests/test_unit_conversions.py .............................................
  tests/test_viz_tools.py ...............................
  tests/test_wind_tools.py ................

  ========================= 189 passed in 1.38 seconds =========================

You can monitor what lines of code the test suite exercises using the `coverage.py`_ tool with the command:

.. _coverage.py: https://coverage.readthedocs.org/en/latest/

.. code-block:: bash

    (salishsea-tools)$ cd tools/SalishSeaTools/
    (salishsea-tools)$ coverage run -m py.test

and generate a test coverage report with:

.. code-block:: bash

    (salishsea-tools)$ coverage report

to produce a plain text report,
or

.. code-block:: bash

    (salishsea-tools)$ coverage html

to produce an HTML report that you can view in your browser by opening :file:`tools/SalishSeaTools/htmlcov/index.html`.

The run the test suite under Python 2.7,
create a Python 2.7 :ref:`SalishSeaToolsDevelopmentEnvironment`.


.. _SalishSeaToolsVersionControlRepository:

Version Control Repository
==========================

The :kbd:`SalishSeaTools` package code and documentation source files are available as part of the :ref:`tools-repo` `Git`_ repository at https://github.com/SalishSeaCast/tools.

.. _Git: https://git-scm.com/


.. _SalishSeaToolsIssueTracker:

Issue Tracker
=============

Development tasks,
bug reports,
and enhancement ideas are recorded and managed in the issue tracker at https://github.com/SalishSeaCast/tools/issues using the component tag :kbd:`SalishSeaTools`.
