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

* `Salish Sea NEMO Command Processor`_
* `SalishSeaNowcast Package`_
* :ref:`Marlin`

.. _Salish Sea NEMO Command Processor: https://bitbucket.org/salishsea/salishseacmd
.. _SalishSeaNowcast Package: https://bitbucket.org/salishsea/salishseanowcast


Python 3
========

The Salish Sea project uses Python 3.
Your should write and test your code using Python 3.
See :ref:`AnacondaPythonDistro` for instructions on how to install a Python 3 working environment,
or :ref:`Python3Enviro` if you want to set up a Python 3 environment within your Anaconda Python 2 installation.

Because of the way that the module systems on :kbd:`jasper` and :kbd:`orcinus` work the :ref:`SalishSeaToolsPackage` and :ref:`SalishSeaCmdProcessor` (:kbd:`SalishSeaCmd` package) must retain backward compatibility to Python 2.7.
The primary implication of that is that modules that use the division operation should have:

.. code-block:: python

    from __future__ import division

as their first import so that floating point division is enabled.


.. _LibraryCodeStandardCopyrightHeaderBlock:

Standard Copyright Header Block
===============================

Every Python library module show start with our standard copyright notice::

  # Copyright 2013-2017 The Salish Sea MEOPAR contributors
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
If you have questions about the attribution and licensing of a piece of code,
please talk to Doug.

The :ref:`salishsea_tools.namelist` is a (rare) example of differently licensed code from another developer that we include in our libraries.

Sphinx documentation files in the :ref:`tools-repo` repo should also start with the same standard copyright notice::

  .. Copyright 2013-2017 The Salish Sea MEOPAR conttributors
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

* Only import things that you are actually using in your module.
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
  * Other Salish Sea project libraries
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


.. _LibraryCodePublicAndPrivate:

Public and Private Objects
==========================

Many compiled languages like Java provide statements to mark functions,
methods,
etc. as *private*,
meaning that they are inaccessible outside of their particular program scope.
Dynamic languages like Python have very strong introspection capabilities that make such privacy constraints impossible.
Instead,
the Python community relies on the social convention that functions,
methods,
etc. that are spelled with leading underscore characters (:kbd:`_`) are considered to be private.

We use that social convention to say,

  "I have marked this function as private because I don't want to guarantee that I won't change its arguments later and I don't want other people to rely its definition.",

or,

  "This function just exists to wrap some lines of code so that the function that calls it is more readable,
  or because I need to use this bit of code in several places in this module.
  It is not intended to be used outside of this module."

Here's an example of private functions from the :py:mod:`nowcast.figures.publish.strm_surge_alerts` module:

.. code-block:: python

    def storm_surge_alerts(
        grids_15m, weather_path, coastline, tidal_predictions,
        figsize=(18, 20),
        theme=nowcast.figures.website_theme,
    ):
        ...
        plot_data = _prep_plot_data(grids_15m, tidal_predictions, weather_path)
        fig, (ax_map, ax_pa_info, ax_cr_info, ax_vic_info) = _prep_fig_axes(
            figsize, theme)
        _plot_alerts_map(ax_map, coastline, plot_data, theme)
        ...

The :py:func:`storm_surge_alerts` function is public.
It is intended to be called by the :py:mod:`nowcast.workers.make_plots` worker.

The :py:func:`_prep_plot_data`,
:py:func:`_prep_fig_axes`,
and :py:func:`_plot_alerts_map` functions that :py:func:`storm_surge_alerts` calls are private functions within :py:mod:`nowcast.figures.publish.storm_surge_alerts` module.
Their purpose is code encapsulation and improving readability but they are not useful outside of the module,
so they are named with a leading underscore to indicate that.

The "leading underscore means private" convention is most commonly used for functions and methods of classes but it can be used on any Python object
(variables, classes, modules, etc.) -
it is simply a naming convention.

The `Sphinx autodoc extension`_ that we use for :ref:`LibraryCodeAutoGeneratedDocs` respects the leading underscore naming convention and does not generate documentation for objects that are thusly named.


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


.. _LibraryCodeReturnSimpleNamespacesFromFunctions:

Return :py:obj:`SimpleNamespace` from Functions
===============================================

If you are writing a function that returns more than one value,
consider returning the collection of values as a `SimpleNamespace`_.
If your function returns more than 3 values,
definitely return them as a :py:obj:`SimpleNamespace`.

.. _SimpleNamespace: https://docs.python.org/3/library/types.html#types.SimpleNamespace

:py:obj:`SimpleNamespace` objects that have fields accessible by attribute lookup
(dotted notation).
They also have a helpful string representation which lists the namespace contents in a name=value format.

.. code-block:: python

    >>> p = SimpleNamespace(x=11, y=22)
    >>> p.x + p.y               # fields also accessible by name
    33
    >>> p                       # readable string representation with a name=value style
    namespace(x=11, y=22)

Using the :py:func:`salishsea_tools.data_tools.load_ADCP` function code as an example:

.. code-block:: python
    :linenos:

    from types import SimpleNamespace


    def load_ADCP(
            daterange, station='central',
            adcp_data_dir='/ocean/dlatorne/MEOPAR/ONC_ADCP/',
    ):
        """
        ...

        :returns: :py:attr:`datetime` attribute holds a :py:class:`numpy.ndarray`
                  of data datatime stamps,
                  :py:attr:`depth` holds the depth at which the ADCP sensor is
                  deployed,
                  :py:attr:`u` and :py:attr:`v` hold :py:class:`numpy.ndarray`
                  of the zonal and meridional velocity profiles at each datetime.
        :rtype: 4 element :py:class:`types.SimpleNamespace`
        """
        ...
        return SimpleNamespace(datetime=datetime, depth=depth, u=u, v=v)

Returning a :py:obj:`SimpleNamespace` lets us call :py:func:`load_ADCP` like:

.. code-block:: python

    adcp_data = load_ADCP(('2016 05 01', '2016 05 31'))

and we can access the depth that the sensor is located at as:

.. code-block:: python

    adcp_data.depth

This makes for compact and easy to understand code that our future selves and others will appreciate when they read our code.


Module-Specific Best Practices
==============================

.. _LibraryCodeSalishSeaToolsPlaces:

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
