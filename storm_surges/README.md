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
      
    5. No stratifictation but accidentally left rivers on. Also used nu=20. (no_strat) (crashed)  
      
    These simulations were run with nu=50 and  initial T+S from Oct 25 restart  

* ##[dec2006.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/dec2006.ipynb)  
    
    This notebook examines the storm surge for Dec 15, 2006.  

* ##[northForcing.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/northForcing.ipynb)  
    
    This notebook examines the storm surge simulations when tidal forcing at Johnstone Strait is included.  

* ##[SandHeadsWinds.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/SandHeadsWinds.ipynb)  
    
    **Sand Heads Winds**  
      
    This notebook demonstrates how to read the file of historical wind data  
    from the Sand Heads weather station that is maintained in the SOG-forcing  
    repo into a data structure of NumPy arrays.  
      
    The code is based on code in the `bloomcast.wind` module in the [SoG-bloomcast project](https://bitbucket.org/douglatornell/sog-bloomcast).  

* ##[spinups.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/spinups.ipynb)  
    
    A notebook for determining how long it takes for velocities to spinup after initializing with a restart files. This is useful for determing storm surge simulation start dates.   
      
    Note this probably depends on viscosity. This simulations use nu =50.  

* ##[weather_Nov-15-2006.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/weather_Nov-15-2006.ipynb)  
    
    This notebook plots the weather at Point Atkinson on Nov. 15, 2006 from the Environment Canada website.   
      
    Additionally, we will look at the weather at YVR and Sandheads since it will be easy to compare with CGRF.   


##License

These notebooks and files are copyright 2013-2014
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
