The IPython Notebooks in this directory provide discussion,
examples, and best practices for plotting various kinds of model results
from netCDF files. There are code examples in the notebooks and also
examples of the use of functions from the
[`salishsea_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html)
package.
If you are new to the Salish Sea MEOPAR project or to IPython Notebook,
netCDF, and Matplotlib you should read the introductory notebooks
in the following order:

* [Exploring netCDF Files.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Exploring netCDF Files.ipynb)
* [Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Plotting Bathymetry Colour Meshes.ipynb)
* [Plotting Tracers on Surface and Depth Slices.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Plotting Tracers on Surface and Depth Slices.ipynb)

Also included are notebooks from initial experiments around visualization
of NEMO results.

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[compareViscosity.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/compareViscosity.ipynb)  
    
    A script to compare runs with different viscosities.  

* ##[compute_thalweg.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/compute_thalweg.ipynb)  
    
* ##[crashAnalysis.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/crashAnalysis.ipynb)  
    
    A code to look at the data from the crashed run. What is going wrong!  
    Looks at currents, bathymetry, and sea surface height around the crashed time step.   

* ##[Exploring netCDF Files.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Exploring netCDF Files.ipynb)  
    
    **Exploring netCDF Files**  
      
    This notebook provides discussion, examples, and best practices for working with netCDF files in Python.  
    Topics include:  
      
    * The [`netcdf4-python`](http://http://unidata.github.io/netcdf4-python/) library  
    * The [`salishsea_tools.nc_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html#module-nc_tools) code module  
    * Reading netCDF files into Python data structures  
    * Exploring netCDF dataset dimensions, variables, and attributes  
    * Working with netCDF variable data as [NumPy](http://www.numpy.org/) arrays  

* ##[GYRE_openNC_plot.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/GYRE_openNC_plot.ipynb)  
    
    This notebook opens NetCDF files from a test run of NEMO 3.4 in the GYRE configuration.  It then prepares a contour plot of temperature and a quiver plot of velocity.  

* ##[mergeCompare.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/mergeCompare.ipynb)  
    
    Comparing merge-tests on Salish and Japser. A week long run to see how the differences evolve.   

* ##[NancysCurrents.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/NancysCurrents.ipynb)  
    
    A script to examine currents. It includes a function for unstaggering the u/v data.  

* ##[nu200_nu50.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/nu200_nu50.ipynb)  
    
    This notebook runs a comparison between the $\nu=200$ and $\nu=50$ simulations by Doug.   
      
    The focus is on currents and tracers.   

* ##[Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Plotting Bathymetry Colour Meshes.ipynb)  
    
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

* ##[Plotting Tracers on Surface and Depth Slices.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Plotting Tracers on Surface and Depth Slices.ipynb)  
    
    **Plotting Tracers on Surface and Depth Slices**  
      
    This notebook contains discussion, examples, and best practices for plotting tracer variable (e.g. temperature, salinity, sea surface height) results from NEMO as colour meshes. It extends the discussion of horizontal slice visualizations in the [Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Plotting%20Bathymetry%20Colour%20Meshes.ipynb) notebook with plotting of slices at selected depths and time steps of variables like temperature and salinity that are calculated on the 3D grid.  
    Topics include:  
      
    * Reading tracer variable values from NEMO `*grid_T.nc` results files  
    * Plotting sea surface height fields at selected times  
    * Approximate land areas masks for tracer field plots  
    * Using slices to zoom in on domain regions  
    * Plotting contour bands and lines  
    * Plotting temperature fields at selected depths  
    * Plotting salinity fields with a logarithmic colour scale  

* ##[SusansViewerWQuiver.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/SusansViewerWQuiver.ipynb)  
    
* ##[Tidal Movie.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Tidal Movie.ipynb)  
    
    Notebook that opens the NetCDF files created by NEMO and creates a movie.  


* ##[Vertical Tracer Cross-sections.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/Vertical Tracer Cross-sections.ipynb)  
    
    Notebook to plot surface salinity and vertical cross-sections  

* ##[WCSD_openNC_plot.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/NetCDF_Plot/WCSD_openNC_plot.ipynb)  
    
    Notebook that opens the NetCDF(3) files created by BIO CONCEPTS 110 WCSD and plots them.  
    Velocity plots are totally dominated by high velocities in the islands. Most useful is the flickery movie of the seasurface height.  


##License

These notebooks and files are copyright 2013-2014
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
