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


.. _BathymetryNotebooksAndTools:

******************************
Bathymetry Notebooks and Tools
******************************

Full Salish Sea Domain Bathymetry
=================================

* `SalishSeaBathy.ipynb`_: Documents the full domain bathymetry used for the Salish Sea NEMO runs.
  The notebook includes:

  * Conversion of the bathymetry data from the 2-Oct-2013 :file:`WC3_PREP` tarball to a netCDF4 dataset with zlib compression enabled for all variables and :kbd:`least_significant_digit=1` set for the depths
    (:kbd:`Bathymetry`) variable.

  * Clipping of the depths such that depths between 0 and 4m are set to 4m and depths greater than 428m
    (the deepest value in the Strait of Georgia)
    are set to 428m.

  * Algorithmic smoothing

.. _SalishSeaBathy.ipynb: http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SalishSeaBathy.ipynb


Initial Sub-domain Test Bathymetry
==================================

* `SalishSeaSubdomainBathy.ipynb`_: Documents the bathymetry used for the initial Salish Sea NEMO runs on a sub-set of the whole region domain.
  The sub-domain bathymetry was used for the runs known as :kbd:`JPP` and :kbd:`WCSD_RUN_tide_M2_OW_ON_file_DAMP_ANALY`.
  The notebook includes 2 approaches to smoothing to bathymetry to get a successful 72 hour NEMO-3.4 run with M2 tidal forcing:

  * Manual smoothing based on depth adjustments at the locations where test runs failed
  * Algorithmic smoothing applied to the entire sub-domain

.. _SalishSeaSubdomainBathy.ipynb: http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SalishSeaSubdomainBathy.ipynb

* `netCDF4bathy.ipynb`_: Documents the creation of a netCDF4 bathymetry file from the algorithmic smoothed bathymetry with zlib compression enabled for all variables.
  The resulting file is about 1/6 the size
  (227 kb in contrast to 1.6 Mb)

.. _netCDF4bathy.ipynb: http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/netCDF4bathy.ipynb


Bathymetric Attributed Grid (BAG) Datasets
==========================================

.. toctree::
   :maxdepth: 2

   ExploringBagFiles.ipynb
