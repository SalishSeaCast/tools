.. _LiveOceanTools:

************************************
Live Ocean Boundary Conditions Tools
************************************

We have developed routines for building our model boundary conditions from  `Live Ocean`_ model results.
Live Ocean is a circulation model for the Pacific Northwest run out of the University Washington by Parker MacCready's group.
This page documents the tools and routines used to create boundary conditions from Live Ocean results.

.. _`Live Ocean`: http://faculty.washington.edu/pmacc/LO/LiveOcean.html

Overview
--------

These routines were designed to be used in the nowcast framework so that each nowcast and forecast simulation is forced with hourly temperature and salinity from the corresponding Live Ocean simulation.  However, the routines are adaptable and are capable of producing, for exammple, a month's worht of daily averged forcing files if needed.

For the nowcast framework, the following things happen:

1. Download today's 72-hour Live Ocean simulation. Live Ocean results are saved at an hourly frequency. Live Ocean results are typcially available around 1PM PST.
2. Save a small sudomain the covers the Salish Sea NEMO Juan de Fuca boundary. Delete the full domain Live Ocean files.
3. Interpolate Live Ocean temperature and salinity onto NEMO boundary.
4. Save interpolated results to a boundary forcing file. Each 24 hour period is saved in a different file. Only the last 48 hours of a simulation are saved.

Ideally these steps are executed every day in an automated system like the workers or a cronjob.

Dependencies
------------

Python Dependencies
*******************

Three python files have been written for this task. These files are saved in :file:`tools/SalishSeaTools/salishsea_tools/`

* :file:`UBC_subdomain.py` - script that extracts and saves the subdomain containing the NEMO Juan de Fuca boundary.

* :file:`LiveOcean_grid.py` - module from Parker MacCready for loading ROMS grid.

* :file:`LiveOcean_BCs.py` - module for interpolating Live Ocean results to NEMO grid and building boundary files.


Other Dependencies
******************

* MATALB - required for converting temperature and salinity to TEOS-10 variables.

* ncks - required for setting time_counter as record dimension in boundary files.

Because of the above two dependencies it is suggested that the code is run on salish.


Bash Scripts
------------

Two bash scripts have been written for primarily for downloading the results and then calling the python routines. Ideally these can be replaced by workers. These scripts are in :file:`analysis-nancy/notebooks/LiveOcean/`.

* :file:`download_day.sh` - Download a Live Ocean simulation and extracts UBC subdomain.
Usage: bash download_day.sh YYYY-MM-DD destination_directory

* :file:`get_daily_LiveOcean.sh` - Calls download_day.sh to download today's Live Ocean results and then call :file:`LiveOcean_BCs.py` to create boundary forcing files. Or this script can be set up as a cronjob.


Storage of files
----------------

* Downloaded Live Ocean subdomain files are stored in :file:`/results/forcing/LiveOcean/downloaded/`. This is coded in :file:`get_daily_LiveOcean.sh`.

* Processed Live Ocean boundary files are stored in :file:`/results/forcing/LiveOcean/boundary_files` and :file:`/results/forcing/LiveOcean/boundary_files/fcst/`. This is coded is the main function :file:`create_files_for_nowcast` in :file:`LiveOcean_BCs.py`.
