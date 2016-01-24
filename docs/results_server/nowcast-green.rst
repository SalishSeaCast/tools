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


Model Parameter Changes Over Time
=================================

.. |br| raw:: html

    <br>

===========  ===================================================  ==============  ==================
Date                       Change                                 New Value       Changeset
===========  ===================================================  ==============  ==================
5-Dec-2015   1st run results                                      N/A
8-Dec-2015   Nutrients went NaN                                   N/A
12-Dec-2015  Added western sea surface height boundary |br|       N/A
             conditions
12-Dec-2015  Added reversed barometer to sea surface height       N/A
12-Dec-2015  Added relative winds/currents (:kbd:`rn_vfac`)       1
12-Dec-2015  Added daily and tidal output files                   N/A
12-Dec-2015  Biology restart 07Dec2015 file (biology starting)    07-Dec-2015
13-Dec-2015  Repeatedly using initial file (biology starting)     original
15-Dec-2015  One day only: no weather available, used |br|        N/A             N/A
             14-Dec-2015 forecast
17-Dec-2015  Decrease baroclinic time step (:kbd:`rdt`)           30 s
18-Dec-2015  Restore baroclinic time step (:kbd:`rdt`)            40 s
18-Dec-2015  Hack sub-stepping passive tracers |br|               N/A
             (vertical advection tracers)
19-Dec-2015  Use restart file from prev. day (biology restart)    N/A
22-Dec-2015  Elise's proper sub-stepping |br|                     N/A
             (vertical advection tracers)
23-Dec-2015  use biology light in physics model |br|              True
             (:kbd:`ln_qsr_bio`)
24-Jan-2016  Add vertical eddy viscosity & diffusion |br|         see changesets  e927e26ebe34_ |br|
             coefficients to :file:`*grid_W.nc` output |br|
             files. |br|
             Remove snowfall rate from :file:`*_grid_T.nc` |br|                   71946bd297a4_
             output files.
===========  ===================================================  ==============  ==================

.. _e927e26ebe34: https://bitbucket.org/salishsea/ss-run-sets/commits/e927e26ebe34
.. _71946bd297a4: https://bitbucket.org/salishsea/ss-run-sets/commits/71946bd297a4
