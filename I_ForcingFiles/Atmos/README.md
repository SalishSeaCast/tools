This is a collection of IPython Notebooks for creating,
manipulating, and visualizing atmospheric forcing netCDF files.

The links below are to static renderings of the notebooks via
[nbviewer.ipython.org](http://nbviewer.ipython.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ##[AtmosphereGridSelection.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/AtmosphereGridSelection.ipynb)  
    
    Notebook to Look at Atmosphereic Domains and Choose Ours  

* ##[CheckAltitude.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/CheckAltitude.ipynb)  
    
    This notebook checks that the altitude.py script generates a files that are reasonable.  
      
    It also combines the monthly altitude calculation into one file by averaging.  

* ##[GetGrib.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/GetGrib.ipynb)  
    
    Notebook to design script to download GRIB2 data from EC webpage  

* ##[gribTnetcdf.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/gribTnetcdf.ipynb)  
    
    Notebook to convert grib2 files to netCDF files that can be used in NEMO  
    Makes use of wgrib2  

* ##[ImproveWeightsFile.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/ImproveWeightsFile.ipynb)  
    
    **Improve Atmospheric Forcing Weights File**  
      
    Transfer the values from a `met_gem_weight.nc`  
    created by `NEMO_EastCoast/NEMO_Preparation/4_weights_ATMOS/get_weight_nemo`  
    into a netCDF4 file with zlib compression on variables  
    and CF-1.6 conventions conformant attributes.  

* ##[InitialGEMCheck.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/InitialGEMCheck.ipynb)  
    
    **Initial Check of GEM Products Forcing Data**  
      
    This notebook is about initial checks and exploration of the 2.5 km grid GEM products  
    atmospheric forcing dataset provided by Luc Fillion's group at EC Dorval.  

* ##[NegativePrecip.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/NegativePrecip.ipynb)  
    
* ##[netCDF4weights-CGRF.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/netCDF4weights-CGRF.ipynb)  
    
    **Convert Atmospheric Forcing Weights to netCDF4**  
      
    Transfer the values from the `met_gem_weight.nc`   
    from the 2-Oct-2013 `WC3_PREP` tarball  
    into a netCDF4 file with zlib compression on variables  
    and CF-1.6 conventions conformant attributes.  

* ##[NoSnow.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/NoSnow.ipynb)  
    
    **No Snow on the Salish Sea**  
      
    Create an annual climatology CGRF-like atmospheric forcing file for NEMO  
    that always supplies zero as the solid precipitation value.  

* ##[RadiationCheck.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/RadiationCheck.ipynb)  
    
    This notebook compares the longwave/shortwave radiation from the GEM2.5 model provided by  
      
    1. Pramod converted from grib2 format to netcdf covering all of Dec 2012  
    2. Kao-Shen at Environment Canada covering 1 hour on Dec 16, 2012  
      
    Question: Are the longwave/shortwave radiation variables in Pramod's netcdf files the ones we should be using? There are several radiation flux variables in the grib2 output.  
      
    Description of grib2 variables  
    https://weather.gc.ca/grib/HRDPS_HR/HRDPS_ps2p5km_P000_deterministic_e.html  
      
    Plan: Comapre Pramod's radiation variables to Kao Shen's.  

* ##[RebaseCGRF.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/RebaseCGRF.ipynb)  
    
    **Rebasing CGRF Atmospheric Forcing Files**  
      
    This notebook documents and verifies the algorithm for  
    rebasing the [CGRF atmospheric forcing dataset][CGRF dataset] files.  
      
    [CGRF dataset]: http://salishsea-meopar-docs.readthedocs.org/en/latest/code-notes/salishsea-nemo/nemo-forcing/atmospheric.html#cgrf-dataset  
      
    The raw CGRF files contain hourly values that run from 06:00 UTC on the file's date  
    to 06:00 UTC on the following day.  
    For hourly forcing,  
    NEMO expects files containing values that run from 00:00 UTC to 23:00 UTC on a date.  
    NEMO also has strict file name requirements for forcing values.  
    To construct such a file some values from two consecutive day's CGRF files must be  
    combined into a file with the name pattern required by NEMO.  
    Since new files need to be created the opportunity is taken to reduce storage requirements  
    by creating them as netCDF4 files with variable-level compression enabled.  
    Metadata that conforms to [CF-1.6 and Salish Sea MEOPAR project conventions][netCDF4 conventions] is included  
    in the new files.  
      
    [netCDF4 conventions]: http://salishsea-meopar-docs.readthedocs.org/en/latest/code-notes/salishsea-nemo/nemo-forcing/netcdf4.html#netcdf4-file-conventions  
      
    All of that processing is implemented in the [`salishsea get_cgrf`][salishsea get_cgrf] command.  
    This notebook provides explanation of that code,  
    and verification that the created files contain wind and precipitation forcing  
    values that are consistent with observations at Sandheads and YVR.  
      
    [salishsea get_cgrf]: http://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaCmd/salishsea-cmd.html#get-cgrf-sub-command  

* ##[VerifyAtmosphericForcing.ipynb](http://nbviewer.ipython.org/urls/bitbucket.org/salishsea/tools/raw/tip/I_ForcingFiles/Atmos/VerifyAtmosphericForcing.ipynb)  
    
    **Verification of Atmospheric Forcing**  


##License

These notebooks and files are copyright 2013-2014
by the [Salish Sea MEOPAR Project Contributors](https://bitbucket.org/salishsea/docs/src/tip/CONTRIBUTORS.rst)
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
http://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file for details of the license.
