The IPython Notebooks in this directory are evaluation of the
tide and storm surge results calculated by the Salish Sea NEMO model.

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[comp_wlev_harm.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/comp_wlev_harm.ipynb)  
    
* ##[comp_wlev_harm_compositerun.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/comp_wlev_harm_compositerun.ipynb)  
    
* ##[comp_wlev_harm-wNorth.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/comp_wlev_harm-wNorth.ipynb)  
    
* ##[Multi-tides w Fit.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/Multi-tides w Fit.ipynb)  
    
    Study Tides: Multi-constituents : Fit to Tide Frequencies  

* ##[Western Flux Inceased M2K1.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/Western Flux Inceased M2K1.ipynb)  
    
    A run with the flux increased by 25% in M2/K1 tidal currents. Check to see if this gives a better match with tidal amplitudes/phases.  
      
    Compare with Nancy's previous M2K1 run. This had flux corrections at the northe, but not at the west.   

* ##[plot_foreman_thalweg-withNorth.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/plot_foreman_thalweg-withNorth.ipynb)  
    
    For results including the Northern Boundary,  
    plot the Foreman et al (1995) model results against our model results, along a thalweg (the thalweg is defined and plotted by Nancy in computer_thalweg.ipynb)  

* ##[comp_wlev_ts.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/comp_wlev_ts.ipynb)  
    
* ##[comp_current_harm.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/comp_current_harm.ipynb)  
    
    Compare harmonics from currents between measured and modelled. Measured harmonics are taken from Table 3 of Foreman et al (1995)  


* ##[Partial Slip.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/Partial Slip.ipynb)  
    
    A look at the effect of reducing the amount of slip on the tides.   
      
    - 5 day runs with all tidal constituents and flux corrected tides. (double corrected for M2).    
      
      
    1. control - rn_shlat = 0.5  
    2. partial1 - rn_shlat = 0.1  
      
    Note: free slip when rn_shlat = 0 and no slip when rn_shlat = 2.   
      
    Purpose: determine if modifying the amount of slip can affect the tidal amplitudes and phases.  
      


* ##[find_wlev_stations.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/find_wlev_stations.ipynb)  
    
    Where shall we evaluate the storm surge performance of the model? The station needs to have water level data for the period of 2002-2010 (this is when we have wind data).  
      
    * Point Atkinson (49.34,-123.25)  
      
    * Victoria Harbour (48.42,-123.37)  
      
    * Patricia Bay (48.65,-123.45)  
      
    * Campbell River (50.04,-125.25)  
      
    All other sites are not in our domain or do not have water level data for these points  

* ##[find_storms.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/find_storms.ipynb)  
    
* ##[Single Tide 2 days.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/Single Tide 2 days.ipynb)  
    
    Study Tides, over short periods, one Constituent at a Time  

* ##[plot_foreman_thalweg.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/plot_foreman_thalweg.ipynb)  
    
    Plot the Foreman et al (1995) model results against our model results, along a thalweg (the thalweg is defined and plotted by Nancy in computer_thalweg.ipynb)  

* ##[plot_current_ellipses.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/compare_tides/plot_current_ellipses.ipynb)  
    

##License

These notebooks and files are copyright 2013-2014
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
