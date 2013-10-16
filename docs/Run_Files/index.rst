*********
Run Files
*********

A collection of files used to run NEMO.  The arch files are architecture files that set the compiler flags and location of libraries for each system.

The :file:`arch-ocean.fcm` is the file to use for the ocean system and for Salish.

The :file:`arch-ifort_jasper.gcm`, based on the file by the same name supplied by P. Myers group, is for running on Jasper on Westgrid.

The .pbs files are the run files for Jasper.  These are what are actually "run" to run the code.  e.g. qsub filename.pbs.

The :file:`GYRE.pbs` runs the simple GYRE configuation on Jasper.

The :file:`AMM_multi.pbs` runs the AMM12 configuration on 32 processors on Jasper.
