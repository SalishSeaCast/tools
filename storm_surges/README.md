The IPython Notebooks in this directory are related to preparing for storm surge simulations.

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[analysisSS.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/analysisSS.ipynb)  
    
    This notebook analyzes results from storm surge runs. Three cases are presented:  
      
    1. Base case with hourly SSH forcing and CGRF weather. (all_forcing)  
      
    2. Hourly SSH forcing without CGRF weather. (ssh_only)  
      
    3. Weather only. No SSH forcing. Winds + pressure (weather_only)  
      
    4. Weather only but no pressure. No SSH forcing. Just winds. (nopressure) (crashed)  
      
      
    These simulations were run with nu=50 and  initial T+S from Oct 25 restart  

* ##[Preparing for Delta.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/Preparing for Delta.ipynb)  
    
    This notebook looks for a grid point close to Delta so that we can start including that community in our output.   

* ##[northForcing.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/northForcing.ipynb)  
    
    This notebook examines the storm surge simulations when tidal forcing at Johnstone Strait is included.  

* ##[New Tides and December Storm.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/New Tides and December Storm.ipynb)  
    
    This notebook will examine the effect of the corrected Northern tides on the December 2006 storm surge.  

* ##[SandHeadsWinds.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/SandHeadsWinds.ipynb)  
    
    **Sand Heads Winds**  
      
    This notebook demonstrates how to read the file of historical wind data  
    from the Sand Heads weather station that is maintained in the SOG-forcing  
    repo into a data structure of NumPy arrays.  
      
    The code is based on code in the `bloomcast.wind` module in the [SoG-bloomcast project](https://bitbucket.org/douglatornell/sog-bloomcast).  

* ##[Effect of Stratification.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/Effect of Stratification.ipynb)  
    
    This notebook examines the effect of stratificaiton on storm surge elevations using the Dec.15, 2006 storm as a case study.  

* ##[dec2006.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/dec2006.ipynb)  
    
    This notebook examines the storm surge for Dec 15, 2006.  

* ##[Testing Port Hardy.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/Testing Port Hardy.ipynb)  
    
    This notebook examines the sea surface height forcing from Port Hardy to ensure it is performing as expected. We would also like to determine the importance of including Port Hardy forcing at the northern boundary.  

* ##[spinups.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/spinups.ipynb)  
    
    A notebook for determining how long it takes for velocities to spinup after initializing with a restart files. This is useful for determing storm surge simulation start dates.   
      
    Note this probably depends on viscosity. This simulations use nu =50.  

* ##[FindWindEvents.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/FindWindEvents.ipynb)  
    
    This notebook looks for large wind events in Sandheads historical wind data. We are looking for a wind storm that did not result in a surge. We would like to ensure that the model does not make a surge if one did not actually occur.   
      
    This codes uses a combination of Doug's class for reading Sandheads data and Kate's methodology for finding ssh anamolies.  

* ##[weather_Nov-15-2006.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/weather_Nov-15-2006.ipynb)  
    
    This notebook plots the weather at Point Atkinson on Nov. 15, 2006 from the Environment Canada website.   
      
    Additionally, we will look at the weather at YVR and Sandheads since it will be easy to compare with CGRF.   

* ##[Tofino and Port Hardy Comparison.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/Tofino and Port Hardy Comparison.ipynb)  
    
    This notebook compares the hourly sea surface height anomaly at Tofino and Port Hardy. We do not have a surge prediction tool at Port Hardy so this comparison will guide our decisions regarding the northern boundary condition on sea surface height.   


##License

These notebooks and files are copyright 2013-2014
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
