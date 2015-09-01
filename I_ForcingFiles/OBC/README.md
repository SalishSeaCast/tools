This is a collection of IPython Notebooks for creating,
manipulating, and visualizing open boundary netCDF files.

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[Modifications_JDF_Sal.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/Modifications_JDF_Sal.ipynb)  
    
    This notebook is designed to increase the salinity of the deep water at the Strait of Juan de Fuca boundary.  

* ##[TS_OBC_Softstart.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/TS_OBC_Softstart.ipynb)  
    
    Notebook to prepare OBC files for TS from Thomson, Mihaly & Kulikov, 2007 (JGR) but starting in Sept with initial conditions.  That is a gentle movement to the proper conditions.  

* ##[SSH_PortHardy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/SSH_PortHardy.ipynb)  
    
    This notebook creates monthly forcing files for the sea surface height (hourly frequency) at Port Hardy, in the northern part of the domain. We want sea surface height forcing separated from the tides. We will take the observed sea surface height and remove the tidal predictions.  

* ##[MakeTSfromMasson.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/MakeTSfromMasson.ipynb)  
    
* ##[Masson_Clim_Softstart.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/Masson_Clim_Softstart.ipynb)  
    
    Notebook to prepare OBC files for TS from Masson climatology but starting in Sept with initial conditions before that.  That is a gentle movement to the proper conditions.  Sep 15 is yearday 258. Sep 12 is yearday 255.  But wtime is in day, not yearday.  So Sep 15 is day 257 and Sep 12 is day 254.  

* ##[PrepareSimpleTS-Johnstone.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/PrepareSimpleTS-Johnstone.ipynb)  
    
    Notebook to prepare simple OBC files for T&S for Johnstone Strait from Thomson, 1981 (The book)  

* ##[SSH_Tofino.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/SSH_Tofino.ipynb)  
    
    This notebook creates monthly forcing files for the sea surface height (hourly frequency) at Tofino. We want sea surface height forcing separated from the tides. We will take the observed sea surface height and remove the tidal predictions.  

* ##[SSH.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/SSH.ipynb)  
    
    Notebook to prepare climatology of sea surface height (SSH) at Juan de Fuca boundary.  Data is from  
    http://www.meds-sdmm.dfo-mpo.gc.ca/isdm-gdsi/twl-mne/inventory-inventaire/data-donnees-eng.asp?user=isdm-gdsi&region=PAC&tst=1&no=8615 and I downloaded 2000 through 2013 complete.  Sets barotropic velocities to zero.  

* ##[SSH_NeahBay.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/SSH_NeahBay.ipynb)  
    
    This notebook creates daily forcing files for the sea surface height (hourly frequency) at Neah Bay. This can be used to create "obs" forcing files for nowcasts in the event of a automation system error.  

* ##[MassonClimatology.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/MassonClimatology.ipynb)  
    
* ##[MassonClimDC.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/MassonClimDC.ipynb)  
    
    Notebook to take dNan'd Climatology and correct it for partial steps  

* ##[Open Boundary.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/Open Boundary.ipynb)  
    
    **Notebook to define the Western Open Boundary for Tidal Boundary Files**  

* ##[JohnstoneStraitBoundary.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/JohnstoneStraitBoundary.ipynb)  
    
* ##[PrepareSimpleOBC.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/PrepareSimpleOBC.ipynb)  
    
    Notebook to prepare simple OBC files from Thomson, Mihaly & Kulikov, 2007 (JGR)  

* ##[Reading Neah Bay Surge website.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/OBC/Reading Neah Bay Surge website.ipynb)  
    
    This notebook reads storm surge data from a NOAA website:  
    http://www.nws.noaa.gov/mdl/etsurge/index.php?page=stn&region=wc&datum=mllw&list=&map=0-48&type=both&stn=waneah  


##License

These notebooks and files are copyright 2013-2015
by the [Salish Sea MEOPAR Project Contributors](https://bitbucket.org/salishsea/docs/src/tip/CONTRIBUTORS.rst)
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
