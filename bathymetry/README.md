The IPython Notebooks in this directory are for manipulating
and visualizing bathymetry netCDF files.

* [BathyZeroTobaetc.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/BathyZeroTobaetc.ipynb)  
* [NEMO-GridBathy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/NEMO-GridBathy.ipynb)  
    
    **NEMO Grid Bathymetry**  
      
    This notebook describes the creation  
    of the `NEMO-forcing/grid/grid_bathy.nc` file  
    containing the calculated grid level depths at each grid point  
    that result from NEMO's partial z-step algorithm.  
    The `grid_bathy.nc` is used to calculate initial conditions  
    and boundary conditions temperature and salinity values that do not  
    induce spurious transient flows at the topographic edges of the domain.  

* [netCDF4bathy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/netCDF4bathy.ipynb)  
    
    **Explore Changing Bathymetry Data Format**  
    **netCDF4 Instead of netCDF3_CLASSIC**  

* [SalishSeaBathy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SalishSeaBathy.ipynb)  
    
    **Salish Sea NEMO Bathymetry**  
      
    This notebook documents the bathymetry used for the Salish Sea NEMO runs.  
      
    The first part of the notebook explores and plots the bathymetry.  

* [SalishSeaSubdomainBathy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SalishSeaSubdomainBathy.ipynb)  
    
    **Salish Sea NEMO Sub-domain Bathymetry**  
      
    This notebook documents the bathymetry used for the   
    initial Salish Sea NEMO runs on a sub-set of the whole region domain.  
    This sub-domain was used for the runs known as `JPP`  
    and `WCSD_RUN_tide_M2_OW_ON_file_DAMP_ANALY`.  
      
    The first part of the notebook explores and plots the bathymetry.  
    The second part records the manual smoothing that was done to  
    get the JPP M2 tidal forcing case to run.  

* [SmoothMouthJdF.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SmoothMouthJdF.ipynb)  
* [TowardSmoothing.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/TowardSmoothing.ipynb)  

##License

These notebooks are copyright 2013-2014
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
