***************************
:file:`Run_Files` Directory
***************************

The :file:`tools/Run_Files/` directory contains a collection of :kbd:`makefile` definitions and job submission script files for various architectures and hosts.


NEMOGCM :kbd:`makefile` Definitions
===================================

* :file:`arch-ifort_jasper.fcm`: :kbd:`makefile` definitions for MPI compilation with the :command:`ifort` compiler on :kbd:`jasper.westgrid.ca`.
  Based on a file from Paul Myers' group at the University of Alberta.

* :file:`arch-salish.fcm`: :kbd:`makefile` definitions for MPI compilation with the :command:`mpif90` compiler on :kbd:`salish.eos.ubc.ca`.

* :file:`arch-ocean.fcm`: :kbd:`makefile` definitions for single processor compilation with the :command:`gfortran` compiler on the UBC-EOAS :kbd:`ocean` machines.


TORQUE Job Scripts
==================

TORQUE scripts are submitted with the :command:`qsub` command.

See https://www.westgrid.ca/support/running_jobs for information on job scripts and submission of jobs on :kbd:`westgrid.ca` systems.

* :file:`AMM_multi.pbs`: run the AMM12 configuration on 32 processors on :kbd:`jasper.westgrid.ca`

* :file:`GYRE.pbs`: run the GYRE case on a single processor on :kbd:`jasper.westgrid.ca`


NEMO-3.1 Build Script Definitions
=================================

* :file:`AA_make.gdef_jasper`: Block of global definitions for NEMO-3.1 build on :kbd:`jasper.westgrid.ca`.
  Based on a file from Paul Myers' group at the University of Alberta.
  Add this block of definitions to :file:`modipsl/util/AA_make.ldef` before running  :file:`modipsl/modeles/UTIL/fait_AA_make`.
