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


.. _SalishSeaToolsPackageInstallation:

**************************************************
:kbd:`SalishSeaTools` Package Installation and Use
**************************************************

:kbd:`SalishSeaTools` is a Python 3 package that provides a collection of Python modules that facilitate code reuse for the Salish Sea MEOPAR project.

These instructions assume that:

* You have an up to date clone of the :ref:`tools-repo` repo
* You have the Python 3 version of :ref:`AnacondaPythonDistro` or `Miniconda`_ installed
* :file:`$HOME/anaconda3/bin` is included in your :envvar:`PATH` environment variable if your are using the :ref:`AnacondaPythonDistro`,
  or :file:`$HOME/miniconda3/bin` is included in your :envvar:`PATH` environment variable if your are using `Miniconda`_

.. _Miniconda: http://conda.pydata.org/miniconda.html

To install the :kbd:`SalishSeaTools` package in your :kbd:`root` Anaconda or Miniconda environment use:

.. code-block:: bash

    $ cd tools
    $ pip install --editable SalishSeaTools

The :kbd:`--editable` option in the :command:`pip install` commands installs the packages via symlinks so that changes in the package modules will be automatically available in your working environment as the repo evolves.

The :kbd:`SalishSeaTools` package can also be installed in an isolated :program:`conda` environment.
The common use case for doing so it development,
testing,
and documentation of the package;
please see the :ref:`SalishSeaToolsPackageDevelopment` section for details.

To use the package in your Jupyter Notebooks or Python scripts import the package:

.. code-block:: python

    import salishsea_tools

    salishsea_tools.bathy_tools.plot_colourmesh(...)

or import modules from it:

.. code-block:: python

    from salishsea_tools import nc_tools

    nc_tools.check_dataset_attrs(...)

