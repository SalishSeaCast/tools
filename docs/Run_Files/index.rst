***************************
:file:`Run_Files` Directory
***************************

The :file:`tools/Run_Files/` directory contains a collection of :kbd:`makefile` definitions and job submission script files for various architectures and hosts:

* :file:`AA_make.gdef_jasper`: Block of global definitions for NEMO-3.1 build on :kbd:`jasper.westgrid.ca`.
  Courtesty of Paul Myers group at the University of Alberta.
  Add this block of definitions to :file:`modipsl/util/AA_make.ldef` before running  :file:`modipsl/modeles/UTIL/fait_AA_make`.

* :file:`GYRE.pbs`: Sample TORQUE job script to run the GYRE case on a single processor on :kbd:`jasper.westgrid.ca`.
  See https://www.westgrid.ca/support/running_jobs for more information on job scripts and submission of jobs on :kbd:`westgrid.ca` systems.

* :file:`arch-ifort_jasper.fcm`: :kbd:`makefile` definitions for MPI compilation with the :command:`ifort` compiler on :kbd:`jasper.westgrid.ca`.
  Courtesty of Paul Myers group at the University of Alberta.

* :file:`arch-ocean.fcm`: :kbd:`makefile` directives for single processor compilation with the :command:`gfortran` compiler on the UBC-EOAS :kbd:`ocean` machines.
*********
Run Files
*********

A collection of files used to run NEMO.  The arch files are architecture files that set the compiler flags and location of libraries for each system.

The :file:`arch-ocean.fcm` is the file to use for the ocean system and for Salish.

The :file:`arch-ifort_jasper.gcm`, based on the file by the same name supplied by P. Myers group, is for running on Jasper on Westgrid.

The .pbs files are the run files for Jasper.  These are what are actually "run" to run the code.  e.g. qsub filename.pbs.

The :file:`GYRE.pbs` runs the simple GYRE configuation on Jasper.

The :file:`AMM_multi.pbs` runs the AMM12 configuration on 32 processors on Jasper.
