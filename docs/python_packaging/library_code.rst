.. Copyright 2013-2015 The Salish Sea MEOPAR conttributors
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


.. _GuidelinesAndBestPracticesForWritingLibraryCode:

******************************************************
Guidelines and Best Practices for Writing Library Code
******************************************************

The notes in this section are about writing readable,
maintainable Python code that your future self and other people will be able to use,
maintain,
and improve.
While much of what follows is applicable to any Python code that you may write,
some of the points are particularly relevant to code going into modules in the :ref:`tools-repo`;
e.g. the :ref:`SalishSeaToolsPackage` and the :ref:`SalishSeaNowcastPackage`.

A primary guide for writing Python code is `PEP 8 -- Style Guide for Python Code`_.

.. _PEP 8 -- Style Guide for Python Code: https://www.python.org/dev/peps/pep-0008/

Installing the `flake8`_ static analysis tool and enabling your editor to use it to highlight problem code will help you to write well-styled code.
See :ref:`PythonSourceCodeCheckingViaFlake8` for details of how to set that up for emacs.

.. _flake8: https://flake8.readthedocs.org/en/latest/

If you are looking for examples of the coding style preferred in Salish Sea project modules,
checkout out the code in these packages:

* :ref:`SalishSeaCmdProcessor`
* :ref:`SalishSeaNowcastPackage`
* :ref:`Marlin`


Python 3
========

The Salish Sea project uses Python 3.
Your should write and test your code using Python 3.
See :ref:`AnacondaPythonDistro` for instructions on how to install a Python 3 working environment,
or :ref:`Python3Enviro` if you want to set up a Python 3 environment within your Anaconda Python 2 installation.

Because of the way that the module systems on :kbd:`jasper` and :kbd:`orcinus` work the :ref:`SalishSeaToolsPackage` and :ref:`SalishSeaCmdProcessor` (:kbd:`SalishSeaCmd` package) must retain backward compatibility to Pythion 2.7.
The primary implication of that is that modules that use the division operation should have:

.. code-block:: python

    from __future__ import division

as their first import so that floating point division is enabled.


Imports
=======

* Only import thimgs that you are actually using in your module.
  `flake8`_ will identify unused imports for you.

* Never use:

  .. code-block:: python

      from something import *

* When you are importing several things from the same place do it like this:

  .. code-block:: python

      from salishsea_tools import (
          nc_tools,
          viz_tools,
          stormtools,
          tidetools,
      )

* Imports should be grouped:

  * Python standard library
  * Other installed libraries
  * Other Salish Sea proecjt libraries
  * The library that the module is part of

  The groups should be separated by an empty line,
  and the imports should be sorted alphabetically within the groups.

  An example from the ::py:mod:`SalishSeaNowcast.nowcast.workers.get_NeahBay_ssh` nowcast system worker module:

  .. code-block:: python

      import datetime
      import logging
      import os
      import shutil

      from bs4 import BeautifulSoup
      import matplotlib
      import netCDF4 as nc
      import numpy as np
      import pandas as pd
      import pytz

      from salishsea_tools import nc_tools

      from nowcast import (
          figures,
          lib,
      )
      from nowcast.nowcast_worker import NowcastWorker


Module-Specific Best Practices
==============================

:py:mod:`salishsea_tools.places`
--------------------------------

The SalishSeaTools.salishsea_tools.places.PLACES` data structure is
intended to be the single source of truth for information about
geographic places that are used in analysis and presentation of
Salish Sea NEMO model results.

It is intended to replace data structures like
:py:data:`SalishSeaNowcast.nowcast.figures.SITES`,
:py:data:`SalishSeaNowcast.nowcast.research_ferries.ferry_stations`,
etc.

Library code that uses the :py:data:`~salishsea_tools.places.PLACES`
data structure should use :kbd:`try...except` to catch :py:exc:`KeyError`
exceptions and produce an error message that is more informative than
the default,
for example:

.. code-block:: python

    try:
        max_tide_ssh = max(ttide.pred_all) + PLACES[site_name]['mean sea lvl']
        max_historic_ssh = PLACES[site_name]['hist max sea lvl']
    except KeyError as e:
        raise KeyError(
            'place name or info key not found in '
            'salishsea_tools.places.PLACES: {}'.format(e))
