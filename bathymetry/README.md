The Jupyter Notebooks in this directory are for manipulating
and visualizing bathymetry netCDF files.

The links below are to static renderings of the notebooks via
[nbviewer.org](https://nbviewer.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ## [blast a river.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/blast a river.ipynb)  
    
* ## [FindTSforSmoothedMouths.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/FindTSforSmoothedMouths.ipynb)  
    
    For smoothed mouths we need to fill in any new grid points.

* ## [Deepen by Grid Thickness.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Deepen by Grid Thickness.ipynb)  
    
* ## [More Smoothing.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/More Smoothing.ipynb)  
    
    Notebook to take our SalishSea2 bathymetry which was smoothed to dh/hbar = 0.8 and smooth it more to 0.33.
    We show below that this makes the Thalweg more rugged as it pulls shallow areas from the sides across the channel.

* ## [Smooth, preserving thalweg.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Smooth, preserving thalweg.ipynb)  
    
    Smooth around the Thalweg

* ## [SmoothMouthJdF-DownOneGrid.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/SmoothMouthJdF-DownOneGrid.ipynb)  
    
    This notebook takes our downonegrid Salish Sea bathymetry and produces a bathymetry with the mouth of Juan de Fuca and Johnstone Strait identical for the first 6 grid points.

* ## [Process202108Bathymetry.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Process202108Bathymetry.ipynb)  
    
    **Process 2021 08 Bathymetry: Based on Process2201803 Bathymetry ****
    New Fraser River, taking 2 m up to 0 to narrow the banks
    
    Take the bathymetry produced by Michael including the better resolved river and process it.
    We need to do the following steps:
    1. Straighten North Open Boundary
    2. Straighten West Open Boundary
    3. Check continuity and Add Mixed Islands
    3.1 Fix Puget
    4. Smooth
    4.1 Extra smooth Puget
    5. Add shallow Jetty
    6. Check dredged River Channel
    7. Plot up our Final Bathymetry
    8. Write out bathy file and jetty extra friction files
    Note: original 201702 processing did Check continuity and add mixed islands and fix Puget after smoothing.
    
    9.Check continuity and islands led to  
    9.1 connect Roche Harbour  
    9.2 remove extra little island  
    9.3 don't close north of Read Island  
    9.4 Disconnect Stuart Island 
    and  
    9.5 Deepen South Puget connection

* ## [NEMOBathymetryfromMeshMask.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/NEMOBathymetryfromMeshMask.ipynb)  
    
    Notebook to create a Nemo Bathymetry file for the ERDDAP server  
    Based on:   
    Nancy/NEMO depths vs bathymetry file.ipynb

* ## [ProcessNewRiverBathymetry.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/ProcessNewRiverBathymetry.ipynb)  
    
    **Process New River Bathymetry ****
    Take the bathymetry produced by Michael including the better resolved river and process it.
    We need to do the following steps:
    1. Straighten North Open Boundary
    2. Straighten West Open Boundary
    3. Check continuity and Add Mixed Islands
    3.1 Fix Puget
    4. Smooth
    4.1 Extra smooth Puget
    5. Add shallow Jetty
    6. Check dredged River Channel
    7. Plot up our Final Bathymetry
    8. Write out bathy file and jetty extra friction files
    Note: original 201702 processing did Check continuity and add mixed islands and fix Puget after smoothing.

* ## [LongRiver.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/LongRiver.ipynb)  
    
    **Look at Bathymetry 6 ****
    and decide on river input points, and annotate the River with local landmarks

* ## [Deepen Haro Boundary Region.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Deepen Haro Boundary Region.ipynb)  
    
* ## [BathyZeroTobaetc.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/BathyZeroTobaetc.ipynb)  
    
* ## [ExploringBagFiles.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/ExploringBagFiles.ipynb)  
    
    **Exploring `.bag` Bathymetry Data Files**
    
    An exploration of data and metadata in Bathymetric Attributed Grid (BAG) files.

* ## [SmoothMouthJdF.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/SmoothMouthJdF.ipynb)  
    
    This notebook takes our original smoothed Salish Sea bathymetry and produces a bathymetry with the mouth of Juan de Fuca identical for the first 6 grid points.

* ## [mesh_mask_SalishSea2_metadata.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/mesh_mask_SalishSea2_metadata.ipynb)  
    
    **`mesh_mask_SalishSea2.nc` Metadata**
    
    Add metadata to the NEMO-generated mesh mask file for the SalishSea2 bathymetry
    so that a well-defined ERDDAP dataset can be produced from it.

* ## [SalishSeaBathy.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/SalishSeaBathy.ipynb)  
    
    **Salish Sea NEMO Bathymetry**
    
    This notebook documents the bathymetry used for the Salish Sea NEMO runs.
    
    The first part of the notebook explores and plots the bathymetry.

* ## [mesh_mask201702_metadata.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/mesh_mask201702_metadata.ipynb)  
    
    **`mesh_mask201702.nc` Metadata**
    
    Add metadata to the NEMO-generated mesh mask file for the 201702 bathymetry
    so that a well-defined ERDDAP dataset can be produced from it.

* ## [SalishSeaSubdomainBathy.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/SalishSeaSubdomainBathy.ipynb)  
    
    **Salish Sea NEMO Sub-domain Bathymetry**
    
    This notebook documents the bathymetry used for the 
    initial Salish Sea NEMO runs on a sub-set of the whole region domain.
    This sub-domain was used for the runs known as `JPP`
    and `WCSD_RUN_tide_M2_OW_ON_file_DAMP_ANALY`.
    
    The first part of the notebook explores and plots the bathymetry.
    The second part records the manual smoothing that was done to
    get the JPP M2 tidal forcing case to run.

* ## [Thalweg Smoothing.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Thalweg Smoothing.ipynb)  
    
    Smooth the Thalweg

* ## [mesh_mask_downbyone2_metadata.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/mesh_mask_downbyone2_metadata.ipynb)  
    
    **`mesh_mask_downbyone2.nc` Metadata**
    
    Add metadata to the NEMO-generated mesh mask file for the downbyone2 bathymetry
    so that a well-defined ERDDAP dataset can be produced from it.

* ## [TowardSmoothing.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/TowardSmoothing.ipynb)  
    
* ## [Bathymetry in Boundary Pass.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Bathymetry in Boundary Pass.ipynb)  
    
    Comparison between original bathy and smoothed bathy

* ## [netCDF4bathy.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/netCDF4bathy.ipynb)  
    
    **Explore Changing Bathymetry Data Format**
    **netCDF4 Instead of netCDF3_CLASSIC**

* ## [Find TS for new Bathymetry.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Find TS for new Bathymetry.ipynb)  
    
    If topography is deepened, we need to extend Temp and Salinity Downward.
    
    Also includes a cell to convert to Reference Salinity

* ## [Bathymetry inside NEMO.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Bathymetry inside NEMO.ipynb)  
    
    Notebook to look at the Bathymetry that NEMO actually uses after it does its processing

* ## [Thalweg Work.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Thalweg Work.ipynb)  
    
    Determine the Thalweg in more Detail and Channelize it

* ## [bathyImage.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/bathyImage.ipynb)  
    
    This notebook creates an image of the bathymetry and coastlines. Includes:
    
    1. Bathymetry
    2. Location of Rivers
    3. Storm Surge points
    
    Other important points?

* ## [Process201803Bathymetry.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/Process201803Bathymetry.ipynb)  
    
    **Process 2018 03 Bathymetry ****
    New Fraser River, taking 2 m up to 0 to narrow the banks
    
    Take the bathymetry produced by Michael including the better resolved river and process it.
    We need to do the following steps:
    1. Straighten North Open Boundary
    2. Straighten West Open Boundary
    3. Check continuity and Add Mixed Islands
    3.1 Fix Puget
    4. Smooth
    4.1 Extra smooth Puget
    5. Add shallow Jetty
    6. Check dredged River Channel
    7. Plot up our Final Bathymetry
    8. Write out bathy file and jetty extra friction files
    Note: original 201702 processing did Check continuity and add mixed islands and fix Puget after smoothing.

* ## [NEMO-GridBathy.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/NEMO-GridBathy.ipynb)  
    
    **NEMO Grid Bathymetry**
    
    This notebook describes the creation
    of the `NEMO-forcing/grid/grid_bathy.nc` file
    containing the calculated grid level depths at each grid point
    that result from NEMO's partial z-step algorithm.
    The `grid_bathy.nc` is used to calculate initial conditions
    and boundary conditions temperature and salinity values that do not
    induce spurious transient flows at the topographic edges of the domain.

* ## [JettyBathymetryTracers.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/JettyBathymetryTracers.ipynb)  
    
    Look at Jetty Bathymetry from Mesh Mask and create a TS file

* ## [LookAt201803Bathymetry.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/LookAt201803Bathymetry.ipynb)  
    
* ## [bathy_for_jie.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/bathymetry/bathy_for_jie.ipynb)  
    

## License

These notebooks and files are copyright by the
[UBC EOAS MOAD Group](https://github.com/UBC-MOAD/docs/blob/main/CONTRIBUTORS.rst)
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file in this repository for details of the license.
