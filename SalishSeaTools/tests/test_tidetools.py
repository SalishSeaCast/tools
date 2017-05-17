# Copyright 2013-2016 The Salish Sea MEOPAR contributors
# and The University of British Columbia

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the tidetools module.
"""
from __future__ import division

from unittest.mock import (
    mock_open,
    patch,
)
import numpy as np

from salishsea_tools import tidetools


def test_get_run_length():
    m_open = mock_open()
    m_open().__iter__.return_value = '''
!! Run timing control
!!
!! *Note*: The time step is set in the &namdom namelist in the namelist.domain
!!         file.
!!
&namrun        !   Parameters of the run
!-----------------------------------------------------------------------
   cn_exp      = "SalishSea"  ! experience name
   nn_it000    =           1  ! first time step
   nn_itend    =       12096  ! last time step (std 1 day = 8640 re: rn_rdt in &namdom)
   nn_date0    =    20020915  ! date at nit_0000 = 1 (format yyyymmdd)
                              ! used to adjust tides to run date (regardless of restart control)
   nn_leapy    =       1      ! Leap year calendar (1) or not (0)
   ln_rstart   =  .true.      ! start from rest (F) or from a restart file (T)
   nn_rstctl   =       2      ! restart control => activated only if ln_rstart = T
                              !   = 0 nn_date0 read in namelist
                              !       nn_it000 read in namelist
                              !   = 1 nn_date0 read in namelist
                              !       nn_it000 check consistency between namelist and restart
                              !   = 2 nn_date0 read in restart
                              !       nn_it000 check consistency between namelist and restart
   nn_istate   =       0      ! output the initial state (1) or not (0)
   nn_stock    =   12096      ! frequency of creation of a restart file (modulo referenced to 1)
   ln_clobber  =  .true.      ! clobber (overwrite) an existing file
&end

&nam_diaharm   !   Harmonic analysis of tidal constituents ('key_diaharm')
!-----------------------------------------------------------------------
    nit000_han =  8641  ! First time step used for harmonic analysis
    nitend_han = 12096  ! Last time step used for harmonic analysis
    nstep_han  =      90  ! Time step frequency for harmonic analysis
    !! Names of tidal constituents
    tname(1)   = 'K1'
    tname(2)   = 'M2'
&end


!! Domain configuration
!!
&namzgr        !   vertical coordinates
!-----------------------------------------------------------------------
   ln_zco      = .false.   !  z-coordinate - full    steps   (T/F)      ("key_zco" may also be defined)
   ln_zps      = .true.    !  z-coordinate - partial steps   (T/F)
&end

&namdom        !   space and time domain (bathymetry, mesh, timestep)
!-----------------------------------------------------------------------
   nn_bathy    =    1      !  compute (=0) or read (=1) the bathymetry file
   nn_msh      =    0      !  create (=1) a mesh file or not (=0)
   rn_hmin     =    3.     !  min depth of the ocean (>0) or min number of ocean level (<0)
   rn_e3zps_min=    5.     !  partial step thickness is set larger than the minimum of
   rn_e3zps_rat=    0.2    !  rn_e3zps_min and rn_e3zps_rat*e3t, with 0<rn_e3zps_rat<1
                           !
   rn_rdt      =   50.     !  time step for the dynamics (and tracer if nn_acc=0)
   nn_baro     =    5      !  number of barotropic time step            ("key_dynspg_ts")
   rn_atfp     =    0.1    !  asselin time filter parameter
   nn_acc      =    0      !  acceleration of convergence : =1      used, rdt < rdttra(k)
                           !                                =0, not used, rdt = rdttra
   rn_rdtmin   =   300.    !  minimum time step on tracers (used if nn_acc=1)
   rn_rdtmax   =   300.    !  maximum time step on tracers (used if nn_acc=1)
   rn_rdth     =  300.     !  depth variation of tracer time step  (used if nn_acc=1)
&end
        '''.splitlines()
    with patch('salishsea_tools.tidetools.namelist.open', m_open, create=True):
        run_length = tidetools.get_run_length('foo', 'bar')
    np.testing.assert_almost_equal(run_length, 2)
