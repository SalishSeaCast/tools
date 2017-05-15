The IPython Notebooks in this directory are for manipulating
and visualizing bathymetry netCDF files.

The links below are to static renderings of the notebooks via
[nbviewer.jupyter.org](http://nbviewer.jupyter.org/).
Descriptions under the links below are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[mesh_mask201702_metadata.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/mesh_mask201702_metadata.ipynb)  
    
    **`mesh_mask201702.nc` Metadata**  
      
    Add metadata to the NEMO-generated mesh mask file for the 201702 bathymetry  
    so that a well-defined ERDDAP dataset can be produced from it.  

* ##[SmoothMouthJdF.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SmoothMouthJdF.ipynb)  
    
    This notebook takes our original smoothed Salish Sea bathymetry and produces a bathymetry with the mouth of Juan de Fuca identical for the first 6 grid points.  

* ##[Thalweg Work.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Thalweg Work.ipynb)  
    
    Determine the Thalweg in more Detail and Channelize it  

* ##[SmoothMouthJdF-DownOneGrid.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SmoothMouthJdF-DownOneGrid.ipynb)  
    
    This notebook takes our downonegrid Salish Sea bathymetry and produces a bathymetry with the mouth of Juan de Fuca and Johnstone Strait identical for the first 6 grid points.  

* ##[More Smoothing.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/More Smoothing.ipynb)  
    
    Notebook to take our SalishSea2 bathymetry which was smoothed to dh/hbar = 0.8 and smooth it more to 0.33.  
    We show below that this makes the Thalweg more rugged as it pulls shallow areas from the sides across the channel.  

* ##[ExploringBagFiles.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/ExploringBagFiles.ipynb)  
    
    **Exploring `.bag` Bathymetry Data Files**  
      
    An exploration of data and metadata in Bathymetric Attributed Grid (BAG) files.  

* ##[Deepen by Grid Thickness.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Deepen by Grid Thickness.ipynb)  
    
* ##[NEMO-GridBathy.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/NEMO-GridBathy.ipynb)  
    
    **NEMO Grid Bathymetry**  
      
    This notebook describes the creation  
    of the `NEMO-forcing/grid/grid_bathy.nc` file  
    containing the calculated grid level depths at each grid point  
    that result from NEMO's partial z-step algorithm.  
    The `grid_bathy.nc` is used to calculate initial conditions  
    and boundary conditions temperature and salinity values that do not  
    induce spurious transient flows at the topographic edges of the domain.  

* ##[Bathymetry inside NEMO.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Bathymetry inside NEMO.ipynb)  
    
    Notebook to look at the Bathymetry that NEMO actually uses after it does its processing  

* ##[blast a river.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/blast a river.ipynb)  
    
* ##[Bathymetry in Boundary Pass.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Bathymetry in Boundary Pass.ipynb)  
    
    Comparison between original bathy and smoothed bathy  

* ##[FindTSforSmoothedMouths.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/FindTSforSmoothedMouths.ipynb)  
    
    For smoothed mouths we need to fill in any new grid points.  

* ##[bathy_for_jie.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/bathy_for_jie.ipynb)  
    
* ##[SalishSeaSubdomainBathy.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SalishSeaSubdomainBathy.ipynb)  
    
    **Salish Sea NEMO Sub-domain Bathymetry**  
      
    This notebook documents the bathymetry used for the   
    initial Salish Sea NEMO runs on a sub-set of the whole region domain.  
    This sub-domain was used for the runs known as `JPP`  
    and `WCSD_RUN_tide_M2_OW_ON_file_DAMP_ANALY`.  
      
    The first part of the notebook explores and plots the bathymetry.  
    The second part records the manual smoothing that was done to  
    get the JPP M2 tidal forcing case to run.  

* ##[netCDF4bathy.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/netCDF4bathy.ipynb)  
    
    **Explore Changing Bathymetry Data Format**  
    **netCDF4 Instead of netCDF3_CLASSIC**  

* ##[mesh_mask_downbyone2_metadata.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/mesh_mask_downbyone2_metadata.ipynb)  
    
    **`mesh_mask_downbyone2.nc` Metadata**  
      
    Add metadata to the NEMO-generated mesh mask file for the downbyone2 bathymetry  
    so that a well-defined ERDDAP dataset can be produced from it.  

* ##[TowardSmoothing.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/TowardSmoothing.ipynb)  
    
* ##[BathyZeroTobaetc.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/BathyZeroTobaetc.ipynb)  
    
* ##[JettyBathymetryTracers.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/JettyBathymetryTracers.ipynb)  
    
    Look at Jetty Bathymetry from Mesh Mask and create a TS file  

* ##[Smooth, preserving thalweg.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Smooth, preserving thalweg.ipynb)  
    
    Smooth around the Thalweg  

* ##[ProcessNewRiverBathymetry.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/ProcessNewRiverBathymetry.ipynb)  
    
    **Process New River Bathymetry ****  
    Take the bathymetry produced by Michael including the better resolved river and process it.  
    We need to do the following steps:  
    1. Straighten North Open Boundary  
    2. Straighten West Open Boundary  
    3. Smooth  
    4. Add shallow Jetty  
    5. Check dredged River Channel  
    6. Check continuity and Add Mixed Islands  
    7. Fix Puget  
    8. Write out bathy file and jetty extra friction files  

* ##[Thalweg Smoothing.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Thalweg Smoothing.ipynb)  
    
    Smooth the Thalweg  

* ##[mesh_mask_SalishSea2_metadata.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/mesh_mask_SalishSea2_metadata.ipynb)  
    
    **`mesh_mask_SalishSea2.nc` Metadata**  
      
    Add metadata to the NEMO-generated mesh mask file for the SalishSea2 bathymetry  
    so that a well-defined ERDDAP dataset can be produced from it.  

* ##[Find TS for new Bathymetry.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Find TS for new Bathymetry.ipynb)  
    
    If topography is deepened, we need to extend Temp and Salinity Downward.  
      
    Also includes a cell to convert to Reference Salinity  

* ##[bathyImage.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/bathyImage.ipynb)  
    
    This notebook creates an image of the bathymetry and coastlines. Includes:  
      
    1. Bathymetry  
    2. Location of Rivers  
    3. Storm Surge points  
      
    Other important points?  

* ##[SalishSeaBathy.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/SalishSeaBathy.ipynb)  
    
    **Salish Sea NEMO Bathymetry**  
      
    This notebook documents the bathymetry used for the Salish Sea NEMO runs.  
      
    The first part of the notebook explores and plots the bathymetry.  

* ##[Deepen Haro Boundary Region.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/Deepen Haro Boundary Region.ipynb)  
    
* ##[NEMOBathymetryfromMeshMask.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/NEMOBathymetryfromMeshMask.ipynb)  
    
    Notebook to create a Nemo Bathymetry file for the ERDDAP server    
    Based on:     
    Nancy/NEMO depths vs bathymetry file.ipynb  

* ##[LongRiver.ipynb](http://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/bathymetry/LongRiver.ipynb)  
    
    **Look at Bathymetry 6 ****  
    and decide on river input points, and annotate the River with local landmarks  


##License

These notebooks and files are copyright 2013-2017
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
