.. _rebuild-nemo-tool:

************
REBUILD_NEMO
************

Description
===========

From :file:`NEMOGCM/TOOLS/REBUILD_NEMO/src/rebuild_nemo.f90`::

  !!=========================================================================
  !!                        ***  rebuild_nemo  ***
  !!=========================================================================
  !!
  !!  A routine to rebuild NEMO files from multiple processors into one file.
  !!  This routine is designed to be much quicker than the old IOIPSL rebuild
  !!  but at the cost of an increased memory usage.
  !!
  !!  NEMO rebuild has the following features:
  !!     * dynamically works out what variables require rebuilding
  !!     * does not copy subdomain halo regions
  !!     * works for 1,2,3 and 4d arrays or types for all valid NetCDF types
  !!     * utilises OMP shared memory parallelisation where applicable
  !!     * time 'chunking' for lower memory use
  !!       (only for 4D vars with unlimited dimension)
  !!
  !!  Ed Blockley - August 2011
  !!  (based on original code by Matt Martin)
  !!
  !!-------------------------------------------------------------------------
  !!
  !!  The code reads the filestem and number of subdomains from the namelist file nam_rebuild.
  !!
  !!  The 1st subdomain file is used to determine the dimensions and variables in all the input files.
  !!  It is also used to find which dimensions (and hence which variables) require rebuilding
  !!  as well as information about the global domain.
  !!
  !!  It then opens all the input files (unbuffered) and creates an array of netcdf identifiers
  !!  before looping through all the variables and updating the rebuilt output file (either by direct
  !!  copying or looping over the number of domains and rebuilding as appropriate).
  !!
  !!  The code looks more complicated than it is because it has lots of case statements to deal with all
  !!  the various NetCDF data types and with various data dimensions (up to 4d).
  !!
  !!  Diagnostic output is written to numout (default 6 - stdout)
  !!  and errors are written to numerr (default 0 - stderr).
  !!
  !!  If time chunking is specified the code will use less memory but take a little longer.
  !!  It does this by breaking down the 4D input variables over their 4th dimension
  !!  (generally time) by way of a while loop.
  !!
  !!-------------------------------------------------------------------------------

A :command:`ksh` script,
:file:`NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo`,
is provided to run the Fortran tool based on command line arguments and options:

.. code-block:: bash

    NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo

      NEMO Rebuild
      ************

      usage: rebuild_nemo [-t -c] filebase ndomain [rebuild dimensions]

      flags:  -t num      use num threads
              -c num      split 4D vars into time chuncks of size num


Build
=====

.. code-block:: bash

    cd NEMO-code/NEMOGCM/TOOLS
    ./maketools -m salish -n REBUILD_NEMO

will build the Fortran tool on :kbd:`salish`.

.. note::

    :file:`NEMOGCM/TOOLS/REBUILD_NEMO/src/rebuild_nemo.f90` uses very long source code lines.
    Some Fortran compilers require a flag to enable processing of source lines longer than 132 characters.
    For :command:`gfortran` that flag is :kbd:`-ffree-line-length-none`.
    Those flags are included in the :file:`NEMOGCM/ARCH/arch-[salish|ocean].fcm` files in the :ref:`NEMO-code-repo`.


Use
===

.. code-block:: bash

    NEMO-code/NEMOGCM/TOOLS/REBUILD_NEMO/rebuild_nemo JPP_1h_20020102_20020104_grid_T 16

will combine 16 per-processor (aka subdomain) :file:`JPP_1h_20020102_20020104_grid_T_*.nc` results files to create :file:`JPP_1h_20020102_20020104_grid_T.nc` in the same directory.
The 16 per-processor files will remain,
unchanged.
