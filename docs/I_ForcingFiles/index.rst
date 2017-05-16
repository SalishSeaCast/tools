.. _InitialConditionsAndForcingNotebooksAndTools:

**************************************************
Initial Conditions and Forcing Notebooks and Tools
**************************************************

The :file:`tools/I_ForcingFiles/` directory contains a collection of IPython Notebooks for creating,
manipulating,
and visualizing initial conditions and forcing netCDF files.
Links to statically rendered versions of these notebooks can be found in the :ref:`tools-repo` repo :file:`I_ForcingFiles/` directory README_.

.. _README: https://bitbucket.org/salishsea/tools/src/tip/I_ForcingFiles/

Many of these notebooks use modules from the :ref:`SalishSeaToolsPackage` so please ensure that you have it installed correctly.


* :file:`AddRivers.ipynb`: an IPython Notebook that prepares the Rivers file for the large Salish Sea NEMO 3.4 domain.

* :file:`LookatInitialForcingFiles.ipynb`: an IPython Notebook that opens bathymetry, coordinate and tide  files from JPP's run of CONCEPTS 110
  It then prepares a various plots.

* :file:`netCDF4weights-CGRF.ipynb`: an IPython Notebook to convert the values from :file:`grid/met_gem_weight.nc` from the :file:`WC3_PREP` 2-Oct-2013 tarball into a netCDF4, :kbd:`zlib=True` file with convention-compliant attributes.

* :file:`NoSnow.ipynb`: an IPython Notebook for the creation of the :file:`atmospheric/no_snow.nc` :ref:`NoSnowConstraint` atmospheric forcing file in the :ref:`NEMO-forcing-repo`.

* :file:`Open Boundary.ipynb`: an IPython Notebook that characterizes the western open boundary of the large Salish Sea NEMO 3.4 domain.

* :file:`Prepare Tide Files.ipynb`: an IPython Notebook that opens JPP's tide files and prepares tide files for NEMO 3.4 in NetCDF format.  This book is for the small domain and does both western and northern boundary.

* :file:`PrepareSimpleOBC.ipynb`: an IPython Notebook that prepares constant boundary values for the western boundary of the large Salish Sea NEMO 3.4 domain.

* :file:`PrepareTS.ipynb`: an IPython Notebook to prepare initial T&S for the large domain based on a single S4-1 profile from Sept 2003.

* :file:`TS_OBC_Softstart.ipynb`: an IPython Notebook to prepare OBC T&S files that start with the initial conditions and switch to the Thomson et al boundary conditions in October.

* :file:`webtide_forcing.ipynb`: an IPython Notebook to prepare tidal forcing files for the large Salish Sea NEMO 3.4 domain, western boundary.

* :file:`correct_pressure.py`: A Python script to correct CGRF pressure files to sea level.

When you add a new notebook to this collection please use :command:`python make_readme.py` in the :file:`tools/I_ForcingFiles/` directory to update the :file:`README.md` and commit and push it too.
