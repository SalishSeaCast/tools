.. Salish Sea MEOPAR tools documentation master file

.. _SalishSeaToolsDocs:

*************************************
Salish Sea MEOPAR Tools Documentation
*************************************

This is the documentation for the Salish Sea MEOPAR project tools collection.
The docs describe a collection of tools for working with the Salish Sea MEOPAR NEMO model,
its results,
and associated data.
There is a companion collection of :ref:`project documentation <SalishSeaDocs>`.

The :file:`tools` repo contains several Python packages:

* :py:obj:`SalishSeaToolsPackage` - a :ref:`collection of Python modules <SalishSeaToolsPackage>` that facilitate code reuse across the Salish Sea MEOPAR project

* :py:obj:`SOGTools` - :ref:`Python functions <SOGTools>` for working with the output of the SOG 1-D model

* :py:obj:`Marlin` - the :ref:`Salish Sea NEMO svn-hg Maintenance Tool <Marlin>`

Also documented here are:

* Notes are how the Python packages in the repo are :ref:`developed and maintained <PythonPackagesDevelopmentAndMaintenance>`

* How we :ref:`create netCDF4 files and the metadata conventions <netCDF4FilesCreationAndConventions>` that we use in them

* How to build and use the :ref:`rebuild-nemo-tool` that we use to combine per-processor results files from NEMO-3.4 runs

* Some of the IPython Notebooks and Python scripts that we use to prepare :ref:`bathymetry <BathymetryNotebooksAndTools>` and :ref:`initial conditions & forcing <InitialConditionsAndForcingNotebooksAndTools>` files for NEMO runs

There is also some :ref:`LegacyDocs` from our early days of learning to configure and run NEMO.


Contents:

.. toctree::
   :maxdepth: 2

   SalishSeaTools/index
   SOGTools/index
   SalishSeaCmd/index
   SalishSeaNowcast/index
   netcdf4/index
   erddap/ERDDAP_datasets.ipynb
   visualisation/visualization_workflows_xarray.ipynb
   bathymetry/index
   I_ForcingFiles/index
   LiveOcean/index
   Marlin/index
   python_packaging/index
   nemo-tools/index
   legacy_docs/index

.. include:: license_description.txt
