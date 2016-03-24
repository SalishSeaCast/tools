.. Copyright 2013-2016 The Salish Sea MEOPAR conttributors
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


.. _LibraryCodeStandardCopyrightHeaderBlock:

Standard Copyright Header Block
===============================

Every Python library module show start with our standard copyright notice::

  # Copyright 2013-2016 The Salish Sea MEOPAR contributors
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

The copyright notice is marked as comments with the :kbd:`#` character at the beginning of lines rather than enclosing the block in triple quotes so that it will not be interpreted by code introspection tools as the module docstring.

The exception to using the above notice is if the module contains code that we have copied from somewhere.
In that case the copyright ownership needs to be changed to make appropriate attribution.
The license notice may also need to be changed if the code is released under a license other than Apache 2.0.
If you have questions about the attirbution and licensing of a piece of code,
please talk to Doug.

The :ref:`salishsea_tools.namelist` is a (rare) example of differently licensed code from another developer that we include in our libraries.

Sphinx documentation files in the :ref:`tools-repo` repo should also start with the same standard copyright notice::

  .. Copyright 2013-2016 The Salish Sea MEOPAR conttributors
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

though the comment indicator at the beginning of the lines is,
of course,
different.


.. _LibraryCodeImports:

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


.. _LibraryCodeAutoGeneratedDocs:

Automatic Module Documentation Generation
=========================================

We use the `Sphinx autodoc extension`_ to produce API
(Application Programming Interface)
documentation like the :ref:`SalishSeaToolsPackage` `API docs`_.
The autodoc extension pulls documentation from docstrings into the documentation tree in a semi-automatic way.
When commits are pushed to Bitbucket a signal is sent to :kbd:`readthedocs.org` where the changes are pulled in,
Sphinx is run to update the HTML rendered docs,
and the revised version is published at http://salishsea-meopar-tools.readthedocs.org/en/latest/.

.. _Sphinx autodoc extension: http://www.sphinx-doc.org/en/stable/ext/autodoc.html
.. _API docs: http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/api.html

See :ref:`DocumentationWithSphinx` for more details.

To add a new module's docstrings to the auto-generated API docs you need to add a block of reStructuredText to the API docs file for the package in which the module resides.
For example,
to auto-generate docs for the :py:mod:`salishsea_tools.data_tools` module,
the following block needs to be added to :file:`tools/SalishSeaTools/docs/api.rst`:

.. code-block:: restructuredtext
    :linenos:

    .. _salishsea_tools.data_tools:

    :py:mod:`data_tools` Module
    ===========================

    .. automodule:: salishsea_tools.data_tools
        :members:

Line 1 is a cross-reference label for the module docs.
It must be unique,
so we use the module's Python namespace expressed in dotted notation.
Once the above block of rst has been committed and pushed to Bitbucket it will become possible to link to it in either the :ref:`tools-repo` or :ref:`docs-repo` docs using:

.. code-block:: restructuredtext

    :ref:`salishsea_tools.data_tools`

Within the :ref:`tools-repo` repo only you can also link to the module docs with:

.. code-block:: restructuredtext

    :py:mod:`salishsea_tools.data_tools`

thanks to automatic index generation provided by the autodoc extension.

Lines 3 and 4 are the section heading for the module's docs.
We use the :kbd:`:py:mod:` semantic markup to make the module name stand out in the rendered docs,
and to provide meaning in the docs source file.
The heading underline should be appropriate to the level of the section in the API docs file.
In most cases that is :kbd:`========` that render in an HTML :kbd:`<h2>` tag.

Lines 6 and 7 are the directives that tell the autodoc extension where to find the module's code and how to process the module's contents.
The example shows the case that we most commonly use:
identifying the module by it dotted notation namespace path.
The :kbd:`:members:` option on line 7 tells autodoc to generate docs for all of the public elements
(classes, functions, module-level data structures, etc.)
it finds in the module.

See the `Sphinx autodoc extension`_ docs for more details.


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
