This is a collection of IPython Notebooks for creating,
manipulating, and visualizing tidal forcing netCDF files.

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[johnstone_strait_tides.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Tides/johnstone_strait_tides.ipynb)  
    
    Make tidal boundary conditions for the Northern boundary in Johnstone Strait. Use data from Webtide and from Thomson & Huggett (1980) to make netcdf input files.  
      
    Edited by Nancy in March, 2014. Modified measured grid rotation ($129^\circ$ instead of $-51^\circ$) and error in S2 elevation calculation.  
      
    Edited by Susan in April, 2014.  Modified grid rotation to rotate versus across grid rather than up grid.  Corrects phases of currents.  

* ##[johnstone_tides_contd.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Tides/johnstone_tides_contd.ipynb)  
    
    This notebook extends Kate's work on generating forcing files for the tides at Johnstone Strait. Kate's notebook is based on observations from Thomson and Huggett (1980). Unfortunately, their observations are not long enough to retrieve the smaller tidal constuents: O1, S2, N2, P1, Q1, K2.  
      
    To determine these constituents, we will calculate the amplitude and phase change of the M2/K1 harmonics between the Webtide point closest to our boundary and the Johnstone Strait harmonics that Kate has determined. We will apply the same change to the remaining constituents.   

* ##[Prepare Tide Files.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Tides/Prepare Tide Files.ipynb)  
    
    Notebook to prepare NEMO 3.4 Tide Files based on CONCEPTS 110 Tide Files  

* ##[webtide_forcing.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Tides/webtide_forcing.ipynb)  
    
    Get the forcing from WebTide (http://www.bio.gc.ca/science/research-recherche/ocean/webtide/index-eng.php) for the Juan de Fuca boundary of the model  


##License

These notebooks and files are copyright 2013-2014
by the [Salish Sea MEOPAR Project Contributors](https://bitbucket.org/salishsea/docs/src/tip/CONTRIBUTORS.rst)
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
