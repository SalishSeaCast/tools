.. Copyright 2013 – present by the SalishSeaCast contributors
.. and The University of British Columbia
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..    https://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.


.. _SalishSeaToolsPackageDevelopment:

********************************************
:py:obj:`SalishSeaTools` Package Development
********************************************

.. _SalishSeaToolsPythonVersions:

Python Versions
===============

.. image:: https://img.shields.io/python/required-version-toml?tomlFilePath=https://raw.githubusercontent.com/SalishSeaCast/SalishSeaCmd/main/pyproject.toml&logo=Python&logoColor=gold&label=Python
    :target: https://docs.python.org/3
    :alt: Python Version from PEP 621 TOML

The :py:obj:`SalishSeaTools` package is developed using `Python`_ 3.13.
The minimum supported Python version is 3.11.
The :ref:`SalishSeaToolsContinuousIntegration` workflow on GitHub ensures that the package
is tested for all versions of Python>=3.11.

.. _Python: https://www.python.org/


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
you can create and activate an environment called :kbd:`salishsea-tools` that will have
all of the Python packages necessary for development,
testing,
and building the documentation with the commands:

.. _Conda: https://conda.io/en/latest/
.. _Miniconda: https://docs.conda.io/en/latest/miniconda.html

.. code-block:: bash

    $ cd tools
    $ conda env create -f SalishSeaTools/envs/environment-dev.yaml
    $ conda activate salishsea-tools

:kbd:`SalishSeaTools` is installed in `editable install mode`_ as part of the conda environment
creation process.
That means that the package is installed from the cloned repo in a way that it will be
automatically updated as the repo evolves.

.. _editable install mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs

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
  loading intersphinx inventory from https://salishsea-meopar-docs.readthedocs.org/en/latest/objects.inv...
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
    (salishsea-tools)$ pytest

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

You can monitor what lines of code the test suite exercises using the `coverage.py`_ and `pytest-cov`_ tools with the command:

.. _coverage.py: https://coverage.readthedocs.io/en/latest/
.. _pytest-cov: https://pytest-cov.readthedocs.io/en/latest/

.. code-block:: bash

    (salishsea-tools)$ cd tools/SalishSeaTools/
    (salishsea-tools)$ pytest --cov=./

The test coverage report will be displayed below the test suite run output.

Alternatively,
you can use

.. code-block:: bash

    (salishsea-tools)$ pytest --cov=./ --cov-report html

to produce an HTML report that you can view in your browser by opening
:file:`tools/SalishSeaTools/htmlcov/index.html`.


.. _SalishSeaToolsContinuousIntegration:

Continuous Integration
----------------------

The :kbd:`SalishSeaTools` package unit test suite is run and a coverage report is generated
whenever changes are pushed to GitHub.
The results are visible on the `repo actions page`_,
from the green checkmarks beside commits on the `repo commits page`_,
or from the green checkmark to the left of the "Latest commit" message on the
`repo code overview page`_ .
The testing coverage report is uploaded to `codecov.io`_

.. _repo actions page: https://github.com/SalishSeaCast/SalishSeaTools/actions
.. _repo commits page: https://github.com/SalishSeaCast/SalishSeaTools/commits/main
.. _repo code overview page: https://github.com/SalishSeaCast/SalishSeaTools
.. _codecov.io: https://app.codecov.io/gh/SalishSeaCast/SalishSeaTools

The `GitHub Actions`_ workflow configuration that defines the continuous integration
tasks is in the :file:`.github/workflows/pytest-with-coverage.yaml` file.

.. _GitHub Actions: https://docs.github.com/en/actions


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


Release Process
===============

Releases are done at Doug's discretion when significant pieces of development work have been
completed.

The release process steps are:

#. Use :command:`hatch version release` to bump the version from ``.devn`` to the next release
   version identifier

#. Confirm that :file:`tools/docs/breaking_changes.rst` includes any relevant notes for the
   version being released

#. Commit the version bump and breaking changes log update


#. Create an annotated tag for the release with :guilabel:`Git -> New Tag...` in PyCharm
   or :command:`git tag -e -a vyy.n`

#. Push the version bump commit and tag to GitHub

#. Use the GitHub web interface to create a release,
   editing the auto-generated release notes into sections:

   * Features
   * Bug Fixes
   * Documentation
   * Maintenance
   * Dependency Updates

#. Use the GitHub :guilabel:`Issues -> Milestones` web interface to edit the release
   milestone:

   * Change the :guilabel:`Due date` to the release date
   * Delete the "when it's ready" comment in the :guilabel:`Description`

#. Use the GitHub :guilabel:`Issues -> Milestones` web interface to create a milestone for
   the next release:

   * Set the :guilabel:`Title` to the next release version,
     prepended with a ``v``;
     e.g. ``v25.1``
   * Set the :guilabel:`Due date` to the end of the year of the next release
   * Set the :guilabel:`Description` to something like
     ``v25.1 release - when it's ready :-)``
   * Create the next release milestone

#. Review the open issues,
   especially any that are associated with the milestone for the just released version,
   and update their milestone.

#. Close the milestone for the just released version.

#. Use :command:`hatch version minor,dev` to bump the version for the next development cycle,
   or use :command:`hatch version major,minor,dev` for a year rollover version bump

#. Commit the version bump

#. Push the version bump commit to GitHub
