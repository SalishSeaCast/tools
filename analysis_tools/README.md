The IPython Notebooks in this directory provide discussion,
examples, and best practices for plotting various kinds of model results
from netCDF files. There are code examples in the notebooks and also
examples of the use of functions from the
[`salishsea_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html)
package.
If you are new to the Salish Sea MEOPAR project or to IPython Notebook,
netCDF, and Matplotlib you should read the introductory notebooks
in the following order:

* [Exploring netCDF Files.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Exploring netCDF Files.ipynb)
* [Plotting Bathymetry Colour Meshes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Bathymetry Colour Meshes.ipynb)
* [Plotting Tracers on Horizontal Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Tracers on Horizontal Planes.ipynb)
* [Plotting Velocity Fields on Horizontal Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Velocity Fields on Horizontal Planes.ipynb)
* [Plotting Velocities and Tracers on Vertical Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Velocities and Tracers on Vertical Planes.ipynb)

The links above and below are to static renderings of the notebooks via
[nbviewer.ipython.org](https://nbviewer.jupyter.org/).
Descriptions under the links below are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[Plotting Bathymetry Colour Meshes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Bathymetry Colour Meshes.ipynb)

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

* ##[Exploring netCDF Files.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Exploring netCDF Files.ipynb)

    **Exploring netCDF Files**

    This notebook provides discussion, examples, and best practices for working with netCDF files in Python.
    Topics include:

    * The [`netcdf4-python`](http://http://unidata.github.io/netcdf4-python/) library
    * The [`salishsea_tools.nc_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html#module-nc_tools) code module
    * Reading netCDF files into Python data structures
    * Exploring netCDF dataset dimensions, variables, and attributes
    * Working with netCDF variable data as [NumPy](http://www.numpy.org/) arrays

* ##[Plotting Tracers on Horizontal Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Tracers on Horizontal Planes.ipynb)

    **Plotting Tracers on Horizontal Planes (Depth Slices)**

    This notebook contains discussion, examples, and best practices for plotting tracer variable (e.g. temperature, salinity, sea surface height) results from NEMO as colour meshes. It extends the discussion of horizontal slice visualizations in the [Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting%20Bathymetry%20Colour%20Meshes) notebook with plotting of slices at selected depths and time steps of variables like temperature and salinity that are calculated on the 3D grid.
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

* ##[Plotting Velocities and Tracers on Vertical Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Velocities and Tracers on Vertical Planes.ipynb)

    **Plotting Velocities and Tracers on Vertical Planes**

    This notebook contains discussion, examples, and best practices for plotting velocity field and tracer results from NEMO on vertical planes.
    Topics include:

    * Plotting colour meshes of velocity on vertical sections through the domain
    * Using `nc_tools.timestamp()` to get time stamps from results datasets
    * Plotting salinity as a colour mesh on thalweg section

* ##[Exploring a Nowcast Time Series from ERDDAP.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Exploring a Nowcast Time Series from ERDDAP.ipynb)

    **Exploring a Nowcast Time Series from ERDDAP**

    This notebook contains discussion and examples of accessing a time series of
    results from the Salish Sea NEMO Nowcast system from the ERDDAP server.
    The time series of interest span several days of nowcast runs,
    so ERDDAP provides a more convenient way of accessing the results than building
    the time series by loading several single day nowcast results file.
    We'll use the [xarray](http://xarray.pydata.org/) to demonstrate it powerful
    time period selection,
    and built-in plotting features that facilitate quick dataset visualization.
    Topics include:

    * Opening ERDDAP datasets with `xarray`
    * Examining dataset and variable metadata
    * Creating rudimentary plots of dataset variable for quick visualization
    * Selecting single point values of variables from datasets by index and by value
    * Selecting time series slices of variables from datasets by date/time ranges

* ##[Plotting Velocity Fields on Horizontal Planes.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting Velocity Fields on Horizontal Planes.ipynb)

    **Plotting Velocity Fields on Horizontal Planes (Depth Slices)**

    This notebook contains discussion, examples, and best practices for plotting velocity field results from NEMO. It extends the discussion of horizontal plane visualizations in the [Plotting Bathymetry Colour Meshes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting%20Bathymetry%20Colour%20Meshes) and [Plotting Tracers on Horizontal Planes.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Plotting%20Tracers%20on%20Horizontal%20Planes.ipynb) notebooks with plotting of quiver and streamline plots in addition to colour mesh plots.
    Topics include:

    * Reading velocity component values from NEMO `*grid_[UVW].nc` results files
    * Plotting colour meshes of velocity components
    * "Un-staggering" velocity component values for vector plots
    * Quiver plots of velocity vectors
    * Streamline plots of velocity fields

* ##[Exploring netCDF Datasets from ERDDAP.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Exploring netCDF Datasets from ERDDAP.ipynb)

    **Exploring netCDF Datasets from ERDDAP Servers**

    This notebook provides discussion, examples, and best practices for
    working with netCDF datasets from ERDDAP servers in Python.
    Topics include:

    * [ERDDAP](http://coastwatch.pfeg.noaa.gov/erddap/) servers
    * The [`netcdf4-python`](http://unidata.github.io/netcdf4-python/) library
    * The [`salishsea_tools.nc_tools`](http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaTools/salishsea-tools.html#module-nc_tools) code module
    * Reading netCDF datasets from an ERDDAP server into Python data structures
    * Exploring netCDF dataset dimensions, variables, and attributes
    * Working with netCDF variable data as [NumPy](http://www.numpy.org/) arrays

* ##[Exploring netCDF Datasets Using xarray.ipynb](https://nbviewer.jupyter.org/urls/bitbucket.org/salishsea/tools/raw/tip/analysis_tools/Exploring netCDF Datasets Using xarray.ipynb)

    **Exploring netCDF Datasets Using the xarray Package**

    This notebook provides discussion, examples, and best practices for
    working with netCDF datasets in Python using the [`xarray`](http://xarray.pydata.org/) package.
    Topics include:

    * The [`xarray`](http://xarray.pydata.org/) package
    * Reading netCDF datasets into Python data structures
    * Exploring netCDF dataset dimensions, variables, and attributes
    * Working with netCDF variable data as [NumPy](http://www.numpy.org/) arrays


##License

These notebooks and files are copyright 2013-2016
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
