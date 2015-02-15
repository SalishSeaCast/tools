The IPython Notebooks in this directory are for manipulating
and visualizing bathymetry netCDF files.

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[BathyZeroTobaetc.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/BathyZeroTobaetc.ipynb)  
    
* ##[Thalweg Work.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Thalweg Work.ipynb)  
    
    Determine the Thalweg in more Detail and Channelize it  

* ##[Bathymetry inside NEMO.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Bathymetry inside NEMO.ipynb)  
    
    Notebook to look at the Bathymetry that NEMO actually uses after it does its processing  

* ##[TowardSmoothing.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/TowardSmoothing.ipynb)  
    
* ##[Smooth, preserving thalweg.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Smooth, preserving thalweg.ipynb)  
    
    Smooth around the Thalweg  

* ##[bathyImage.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/bathyImage.ipynb)  
    
    This notebook creates an image of the bathymetry and coastlines. Includes:  
      
    1. Bathymetry  
    2. Location of Rivers  
    3. Storm Surge points  
      
    Other important points?  

* ##[More Smoothing.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/More Smoothing.ipynb)  
    
    Notebook to take our SalishSea2 bathymetry which was smoothed to dh/hbar = 0.8 and smooth it more to 0.33.  
    We show below that this makes the Thalweg more rugged as it pulls shallow areas from the sides across the channel.  

* ##[SmoothMouthJdF.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SmoothMouthJdF.ipynb)  
    
    This notebook takes our original smoothed Salish Sea bathymetry and produces a bathymetry with the mouth of Juan de Fuca identical for the first 6 grid points.  

* ##[SalishSeaSubdomainBathy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SalishSeaSubdomainBathy.ipynb)  
    
    **Salish Sea NEMO Sub-domain Bathymetry**  
      
    This notebook documents the bathymetry used for the   
    initial Salish Sea NEMO runs on a sub-set of the whole region domain.  
    This sub-domain was used for the runs known as `JPP`  
    and `WCSD_RUN_tide_M2_OW_ON_file_DAMP_ANALY`.  
      
    The first part of the notebook explores and plots the bathymetry.  
    The second part records the manual smoothing that was done to  
    get the JPP M2 tidal forcing case to run.  

* ##[Find TS for new Bathymetry.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Find TS for new Bathymetry.ipynb)  
    
* ##[SalishSeaBathy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SalishSeaBathy.ipynb)  
    
    **Salish Sea NEMO Bathymetry**  
      
    This notebook documents the bathymetry used for the Salish Sea NEMO runs.  
      
    The first part of the notebook explores and plots the bathymetry.  

* ##[NEMO-GridBathy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/NEMO-GridBathy.ipynb)  
    
    **NEMO Grid Bathymetry**  
      
    This notebook describes the creation  
    of the `NEMO-forcing/grid/grid_bathy.nc` file  
    containing the calculated grid level depths at each grid point  
    that result from NEMO's partial z-step algorithm.  
    The `grid_bathy.nc` is used to calculate initial conditions  
    and boundary conditions temperature and salinity values that do not  
    induce spurious transient flows at the topographic edges of the domain.  

* ##[Thalweg Smoothing.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Thalweg Smoothing.ipynb)  
    
    Smooth the Thalweg  

* ##[netCDF4bathy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/netCDF4bathy.ipynb)  
    
    **Explore Changing Bathymetry Data Format**  
    **netCDF4 Instead of netCDF3_CLASSIC**  


##License

These notebooks and files are copyright 2013-2015
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
