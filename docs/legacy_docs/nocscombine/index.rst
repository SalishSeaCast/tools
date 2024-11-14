***********
NOCSCOMBINE
***********

.. warning::

    NOCSCOMBINE is old and slow.
    Use :ref:`rebuild-nemo-tool` instead.

NOCSCOMBINE is a tool to combine the per-processor NetCDF results files that are generated when NEMO is run in parallel using MPI.
One description of its use can be found at http://www.hector.ac.uk/cse/distributedcse/reports/nemo/nemo_notes/node18.html.
The NOCSCOMBINE code was downloaded from ftp://ftp.soc.soton.ac.uk/omfftp/NEMO/.

The :file:`nocscombine.F90` file contains this notice regarding distribution and use of the package::

  Unless otherwise indicated, all other software has been authored
  by an employee or employees of the National Oceanography Centre,
  Southampton, UK (NOCS).  NOCS operates as a collaboration
  between the Natural Environment Research Council (NERC) and
  the University of Southampton.  The public may copy and use
  this software without charge, provided that this Notice and
  any statement of authorship are reproduced on all copies.
  Neither NERC nor the University makes any warranty, express
  or implied, or assumes any liability or responsibility for the
  use of this software.


Usage
=====

From the :file:`README.nocscombine` file:

.. include:: ../../../nocscombine/README.nocscombine
    :literal:


Building :command:`nocscombine`
===============================

The :file:`NOCSCOMBINE.tar` tarball includes several :file:`Makefiles` but it is almost certainly necessary to create your own :file:`Makefile` to set the
:makevar:`FC`,
:makevar:`LDR`,
:makevar:`NCHOME`,
and :makevar:`LIBS` variables appropriately.
This repository contains :file:`Makefile.jasper` to build :command:`nocscombine` on :kbd:`jasper.westgrid.ca` using the values:

.. code-block:: make

    FC = ifort -fixed -80 -O3 -DLARGE_FILE -c
    LDR = ifort -O3 -fixed -o nocscombine
    NCHOME = /lustre/jasper/software/netcdf/netcdf-4.1.3
    LIBS = -L$(NCHOME)/lib -I$(NCHOME)/include -lnetcdf -lnetcdff -lhdf5_hl -lhdf5 -lz -lsz
