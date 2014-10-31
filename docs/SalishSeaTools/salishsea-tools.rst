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


.. _SalishSeaTools:

************************
Salish Sea Tools Package
************************

The Salish Sea Tools package is a collection of Python modules that facilitate code reuse for the Salish Sea MEOPAR project.


Installation
============

These instructions assume that:

* You have an up to date clone of the `tools repo`_
* You have the :ref:`AnacondaPythonDistro` installed
* :file:`$HOME/anaconda/bin` is included in your :envvar:`PATH` environment variable

.. _tools repo: https://bitbucket.org/salishsea/tools/

Use :program:`pip`
(the Python package installer)
to install the :kbd:`SalishSeaTools` package from the `tools repo`_ in editable mode so that the package will be automatically updated as the repo evolves:

.. code-block:: bash

    cd tools/SalishSeaTools
    pip install --editable .

Experienced Python developers may wish to install the package in other ways:

* In a Python virtual environment
* In :file:`$HOME/.local/` via the :command:`pip install --user` option

To use the package in your IPython Notebooks or Python scripts import the package:

.. code-block:: python

    import salishsea_tools

    salishsea_tools.bathy_tools.plot_colourmesh(...)

or import modules from it:

.. code-block:: python

    from salishsea_tools import nc_tools

    nc_tools.check_dataset_attrs(...)


.. _salishsea_tools.bathy_tools:

:py:mod:`bathy_tools` Module
============================

.. automodule:: bathy_tools
    :members:


.. _salishsea_tools.hg_commands:

:py:mod:`hg_commands` Module
============================

.. automodule:: hg_commands
    :members:


.. _salishsea_tools.namelist:

:py:mod:`namelist` Module
=========================

.. automodule:: namelist
    :members: namelist2dict

.. _salishsea_tools.nc_tools:

:py:mod:`nc_tools` Module
=========================

.. automodule:: nc_tools
    :members:


.. _salishsea_tools.nowcast.figures:

:py:mod:`nowcast.figures` Module
================================

.. automodule:: nowcast.figures
    :members:


.. _salishsea_tools.tidetools:

:py:mod:`tidetools` Module
==========================

.. automodule:: tidetools
    :members:


.. _salishsea_tools.viz_tools:

:py:mod:`viz_tools` Module
==========================

.. automodule:: viz_tools
    :members:


.. _salishsea_tools.stormtools:

:py:mod:`stormtools` Module
===========================

.. automodule:: stormtools
    :members:
