The IPython Notebooks in this directory are related to preparing for storm surge simulations.

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[analysisSS.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/analysisSS.ipynb)  
    
    This notebook analyzes results from storm surge runs. Three cases are presented:  
      
    1. Base case with hourly SSH forcing and CGRF weather. (nov12-nov182006_1)  
      
    2. Hourly SSH forcing without CGRF weather (no surface pressure either). (nov12-nov182006_noweather)  
      
    3. SSH climatology and CGRF weather. (nov12-nov182006_TofinoClim). This crashed at about 6 days.  
      
    4. Weather only. No SSH forcing. Winds + pressure (nov12-nov182006_weather) (crashed)  
      
    5. Weather only but no pressure. No SSH forcing. Just winds. (nov12-nov182006_nopressure)  
      
    These simulations were run with nu=50 and  initial T+S from Oct 25 restart  

* ##[SSH_Tofino_setup.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/SSH_Tofino_setup.ipynb)  
    
    This notebook will create an hourly forcing file for the sea surface height at Tofino. We want sea surface height forcing separated from the tides. We will focus the Nov. 2006 storm surge.   
      
    I will begin by looking at Sept. 15, 2006 through to to Dec. 31, 2006. There was another great storm surge in Dec. 2006.   
      
    Storm surge dates: Nov 15, 2006, Dec 14, 2006  
      
    This notebook is a work in progress. For now I am just evaluating the sea surface height anamoly based on WebTide predictions and observations. In the future, we may want to consider a different tool for evaluating the tides. Kate and I discussed t_tide.  I couldn't figure out how to give amp/phase constituents to WebTide but apparently t_tide does this.   


* ##[weather_Nov-15-2006.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/storm_surges/weather_Nov-15-2006.ipynb)  
    
    This notebook plots the weather at Point Atkinson on Nov. 15, 2006 from the Environment Canada website.   
      
    Additionally, we will look at the weather at YVR and Sandheads since it will be easy to compare with CGRF.   
      
    This is based on some code that Doug wrote to download and plot the EC data from Sandheads and YVR. I removed the correction to UTC so I an easily compare with the data on the EC website. I'm also only plotting the wind speed   


##License

These notebooks and files are copyright 2013-2014
by the Salish Sea MEOPAR Project Contributors
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
