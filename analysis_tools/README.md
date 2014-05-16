The IPython Notebooks in this directory provide discussion,
examples, and best practices for plotting various kinds of model results
from netCDF files. There are code examples in the notebooks and also
examples of the use of functions from the
[`salishsea_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html)
package.
If you are new to the Salish Sea MEOPAR project or to IPython Notebook,
netCDF, and Matplotlib you should read the introductory notebooks
in the following order:

* [Exploring netCDF Files.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Exploring netCDF Files.ipynb)
* [Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Bathymetry Colour Meshes.ipynb)
* [Plotting Tracers on Horizontal Planes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Tracers on Horizontal Planes.ipynb)
* [Plotting Velocity Fields on Horizontal Planes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Velocity Fields on Horizontal Planes.ipynb)

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[compute_thalweg.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/compute_thalweg.ipynb)  
    
* ##[Exploring netCDF Files.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Exploring netCDF Files.ipynb)  
    
    **Exploring netCDF Files**  
      
    This notebook provides discussion, examples, and best practices for working with netCDF files in Python.  
    Topics include:  
      
    * The [`netcdf4-python`](http://http://unidata.github.io/netcdf4-python/) library  
    * The [`salishsea_tools.nc_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html#module-nc_tools) code module  
    * Reading netCDF files into Python data structures  
    * Exploring netCDF dataset dimensions, variables, and attributes  
    * Working with netCDF variable data as [NumPy](http://www.numpy.org/) arrays  

* ##[Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Bathymetry Colour Meshes.ipynb)  
    
    **Plotting Bathymetry Colour Meshes**  
      
    This notebook contains discussion, examples, and best practices for plotting bathymetry data as colour meshes. It also serves as a basic introduction setting up horizontal slice visualizations of any model result quantities.  
    Topics include:  
      
    * The [matplotlib](http://matplotlib.org/) library and its `pyplot` and `pylab` interfaces  
    * The [`salishsea_tools.viz_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html#module-viz_tools) code module  
    * Making plots appear below the code cells that create them in IPython Notebooks  
    * Figure and Axes objects  
    * Plotting bathymetry depth data as 2-D pseudocolour mesh plots  
    * Controlling the size and aspect ratio of plots,  
    in particular setting the aspect ratio to match the Salish Sea NEMO model lateral grid  
    * Using different colour maps for colour mesh plots and adding colour bar scales to them  
    * Controlling the colour of land areas  
    * Setting axes limits and zooming in on regions of the domain  
    * Plotting on latitude/longitude map coordinates  
    * Saving plots as image files and displaying image files in notebooks  

* ##[Plotting Tracers on Horizontal Planes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Tracers on Horizontal Planes.ipynb)  
    
    **Plotting Tracers on Horizontal Planes (Depth Slices)**  
      
    This notebook contains discussion, examples, and best practices for plotting tracer variable (e.g. temperature, salinity, sea surface height) results from NEMO as colour meshes. It extends the discussion of horizontal slice visualizations in the [Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Plotting%20Bathymetry%20Colour%20Meshes) notebook with plotting of slices at selected depths and time steps of variables like temperature and salinity that are calculated on the 3D grid.  
    Topics include:  
      
    * Reading tracer variable values from NEMO `*grid_T.nc` results files  
    * Plotting sea surface height fields at selected times  
    * Approximate land areas masks for tracer field plots  
    * Using slices to zoom in on domain regions  
    * Plotting contour bands and lines  
    * Plotting temperature fields at selected depths  
    * Adding contour lines to colour mesh plots  
    * Anomaly plots  
    * Plotting salinity fields with various colour scales  

* ##[Plotting Velocity Fields on Horizontal Planes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Velocity Fields on Horizontal Planes.ipynb)  
    
    **Plotting Velocity Fields on Horizontal Planes (Depth Slices)**  
      
    This notebook contains discussion, examples, and best practices for plotting velocity field results from NEMO. It extends the discussion of horizontal plane visualizations in the [Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Plotting%20Bathymetry%20Colour%20Meshes) and [Plotting Tracers on Surface and Depth Slices.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Plotting%20Tracers%20on%20Surface%20and%20Depth%20Slices.ipynb) notebooks with plotting of quiver and streamline plots in addition to colour mesh plots.  
    Topics include:  
      
    * Reading velocity component values from NEMO `*grid_[UVW].nc` results files  
    * Plotting colour meshes of velocity components  
    * "Un-staggering" velocity component values for vector plots  
    * Quiver plots of velocity vectors  


##License

These notebooks and files are copyright 2013-2014
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
