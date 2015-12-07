.. _NowcastGreenResults:

***************************
Nowcast Green Model Results
***************************

 :file:`/results/SalishSea/nowcast-green/`
  Holds the results from the daily nowcast green ocean runs

These runs started Dec 5, 2012 using physical initial conditions from spin-up run at Dec 1, 2002 and biological initial conditions from observations on Oct ?, ????.

Initial run used:

* Bathymetry #6 (extended Fraser River)
* TS4 tides
* SOG biological model
* practical salinity
* Hollingsworth + energy and enstrophy conserving

Updates needed include:

* iodef.xml file: needs daily, needs tidal stations
* not yet using ssh
* not yet using reverse barometer
* should increase rn_shlat to 0.5
* add sea surface currents to wind stress calculation
* switch salinity to absolute salinity (TEOS-10)

=========== ============================== ==========
 Date                      Change          New Value
=========== ============================== ==========
Dec 5, 2015          start
=========== ============================== ==========
