.. SalishSeaCast tools documentation master file

.. _SalishSeaToolsDocs:

*************************************
SalishSeaCast Tools Documentation
*************************************

This is the documentation for the SalishSeaCast project tools collection.
The docs describe a collection of tools for working with the SalishSeaCast NEMO model,
its results,
and associated data.
There is a companion collection of :ref:`project documentation <SalishSeaDocs>`.

The :file:`tools` repo contains several Python packages:

* :py:obj:`SalishSeaToolsPackage` - a :ref:`collection of Python modules <SalishSeaToolsPackage>` that facilitate code reuse across the SalishSeaCast project

* :py:obj:`SOGTools` - :ref:`Python functions <SOGTools>` for working with the output of the SOG 1-D model

Also documented here are:

* Notes are how the Python packages in the repo are :ref:`developed and maintained <PythonPackagesDevelopmentAndMaintenance>`

* How we :ref:`create netCDF4 files and the metadata conventions <netCDF4FilesCreationAndConventions>` that we use in them

* How to build and use the :ref:`rebuild-nemo-tool` that we use to combine per-processor results files from NEMO-3.4 runs

* Some of the Jupyter Notebooks and Python scripts that we use to prepare :ref:`bathymetry <BathymetryNotebooksAndTools>` and :ref:`initial conditions & forcing <InitialConditionsAndForcingNotebooksAndTools>` files for NEMO runs

There is also some :ref:`LegacyDocs` from our early days of learning to configure and run NEMO.


Contents:

.. toctree::
   :maxdepth: 2

   breaking_changes
   SalishSeaTools/index
   SOGTools/index
   netcdf4/index
   erddap/ERDDAP_datasets.ipynb
   visualisation/visualization_workflows_xarray.ipynb
   bathymetry/index
   I_ForcingFiles/index
   LiveOcean/index
   python_packaging/index
   nemo-tools/index
   legacy_docs/index

.. include:: license_description.txt
