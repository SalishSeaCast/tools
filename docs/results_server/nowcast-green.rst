.. _NowcastGreenResults:

***************************
Nowcast Green Model Results
***************************

:file:`/results/SalishSea/nowcast-green/` holds the results from the daily nowcast green ocean runs.

Those runs started 5-Dec-2015 using physical initial conditions from spin-up run at 1-Dec-2002 and biological initial conditions from observations on Oct ?, ????.

Initial run used:

* NEMO-3.6
* Bathymetry #6 (extended Fraser River)
* TS4 tides
* SOG biological model
* practical salinity
* Hollingsworth + energy and enstrophy conserving

Updates needed include:

* should increase rn_shlat to 0.5
* switch salinity to absolute salinity (TEOS-10)

=========== ======================= ============= ===================================
 Date        Change                  New Value     Comments
=========== ======================= ============= ===================================
5-Dec-2015   N/A                     N/A           1st run results
8-Dec-2015   N/A                     N/A           Nutrients went NaN
12-Dec-2015  ssh                     N/A           Added ssh west boundary
12-Dec-2015  ssh                     N/A           Added reversed barometer
12-Dec-2015  rn_vfac                 1             Added relative winds/currents
12-Dec-2015  N/A                     N/A           Added daily and tidal output files
12-Dec-2015  biology starting        07-Dec-2015   Biology restart 07Dec2015 file
13-Dec-2015  biology starting        original      Repeatedly using initial file
15-Dec-2015  wind forecast           N/A           no weather, used previous fcst
17-Dec-2015  rdt                     30 s          Decrease baroclinic time step
18-Dec-2015  rdt                     40 s          Restore baroclinic time step
18-Dec-2015  vert. adv. tracers      N/A           Hack sub-stepping passive tracers
19-Dec-2015  biology restart         N/A           use restart file from prev. day
=========== ======================= ============= ===================================


