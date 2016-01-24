.. _NowcastResults:

*********************
Nowcast Model Results
*********************

:file:`/results/SalishSea/nowcast/` holds the results from the daily nowcast runs.

:file:`/results/SalishSea/forecast/` holds the results from the daily forecast runs.

:file:`/results/SalishSea/forecast2/` holds the results from the daily forecast2 runs.

Initial run used:

* NEMO-3.4
* Bathymetry #2 (truncated Fraser River)
* TS4 tides
* practical salinity


Model Parameter Changes Over Time
=================================

.. |br| raw:: html

    <br>

===========  ===================================================  ==============  ==================
 Date                       Change                                New Value       Changeset
===========  ===================================================  ==============  ==================
27-Oct-2014  1st :file:`nowcast/` run results                     N/A
20-Nov-2014  1st :file:`forecast/` run results                    N/A
26-Nov-2014  Changed to tidal forcing tuned for better |br|       see changeset   efa8c39a9a7c_
             accuracy at Point Atkinson
28-Nov-2014  1st :file:`forecast2/` run results                   N/A
07-Dec-2014  Changed temperature of run-off from all rivers |br|  see changeset   e691e0c99dff_
             to that of the Fraser (one day only)
14-Dec-2014  Changed temperature of run-off from all rivers |br|  see changeset   e691e0c99dff_
             to that of the Fraser (ongoing)
28-Mar-2015  Horizontal turbulent diffusivity (kappa) |br|        10              89d2c2653d9e_
             reduced from 20.5
06-Aug-2015  Changed lateral momentum diffusion from |br|         see changeset   064a3be69f54_
             horizontal to iso-neutral direction
29-Sep-2015  Vertical background turbulent viscosity |br|         1.0e-5          9fdb426ea91f_
             reduced from 1.0e-4
03-Nov-2015  Increased deep salinity of western boundary |br|     see changeset   956b5587d773_
             conditions based onclimatological comparisons |br|
             with IOS & WOD data
22-Nov-2015  Corrected and moved river run-off grid |br|          see changeset   5d1e00c2f44e_
             locations: |br|
             Oyster & 4 Jervis Inlet rivers were on land, |br|
             southern-most Fraser portion corrected from |br|
             Deas Slough to Canoe Pass
27-Nov-2015  Changed from using Neah Bay forecast residuals |br|  see changeset   65ce47429291_
             to using that forecast and calculating our own |br|
             residuals via ttide
15-Dec-2015  One day only: no weather available, used |br|        N/A             N/A
             14-Dec-2015 forecast
24-Jan-2016  Add vertical eddy viscosity & diffusion |br|         see changesets  e927e26ebe34_ |br|
             coefficients to :file:`*grid_W.nc` output |br|
             files. |br|
             Remove snowfall rate from :file:`*_grid_T.nc` |br|                   71946bd297a4_
             output files.
===========  ===================================================  ==============  ==================

.. _efa8c39a9a7c: https://bitbucket.org/salishsea/ss-run-sets/commits/efa8c39a9a7c
.. _e691e0c99dff: https://bitbucket.org/salishsea/ss-run-sets/commits/e691e0c99dff
.. _89d2c2653d9e: https://bitbucket.org/salishsea/ss-run-sets/commits/89d2c2653d9e
.. _064a3be69f54: https://bitbucket.org/salishsea/ss-run-sets/commits/064a3be69f54
.. _9fdb426ea91f: https://bitbucket.org/salishsea/ss-run-sets/commits/9fdb426ea91f
.. _956b5587d773: https://bitbucket.org/salishsea/ss-run-sets/commits/956b5587d773
.. _5d1e00c2f44e: https://bitbucket.org/salishsea/nemo-forcing/commits/5d1e00c2f44e
.. _65ce47429291: https://bitbucket.org/salishsea/tools/commits/65ce47429291
.. _e927e26ebe34: https://bitbucket.org/salishsea/ss-run-sets/commits/e927e26ebe34
.. _71946bd297a4: https://bitbucket.org/salishsea/ss-run-sets/commits/71946bd297a4
