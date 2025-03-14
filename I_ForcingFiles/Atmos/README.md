This is a collection of Jupyter Notebooks for creating,
manipulating, and visualizing atmospheric forcing netCDF files.

The links below are to static renderings of the notebooks via
[nbviewer.org](https://nbviewer.org/).
Descriptions below the links are from the first cell of the notebooks
(if that cell contains Markdown or raw text).

* ## [GetGrib.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/GetGrib.ipynb)

    Notebook to design script to download GRIB2 data from EC webpage

* ## [NegativePrecip.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/NegativePrecip.ipynb)

* ## [InitialGEMCheck.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/InitialGEMCheck.ipynb)

    **Initial Check of GEM Products Forcing Data**

    This notebook is about initial checks and exploration of the 2.5 km grid GEM products
    atmospheric forcing dataset provided by Luc Fillion's group at EC Dorval.

* ## [RebaseCGRF.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/RebaseCGRF.ipynb)

    **Rebasing CGRF Atmospheric Forcing Files**

    This notebook documents and verifies the algorithm for
    rebasing the [CGRF atmospheric forcing dataset][CGRF dataset] files.

    [CGRF dataset]: https://salishsea-meopar-docs.readthedocs.org/en/latest/code-notes/salishsea-nemo/nemo-forcing/atmospheric.html#cgrf-dataset

    The raw CGRF files contain hourly values that run from 06:00 UTC on the file's date
    to 06:00 UTC on the following day.
    For hourly forcing,
    NEMO expects files containing values that run from 00:00 UTC to 23:00 UTC on a date.
    NEMO also has strict file name requirements for forcing values.
    To construct such a file some values from two consecutive day's CGRF files must be
    combined into a file with the name pattern required by NEMO.
    Since new files need to be created the opportunity is taken to reduce storage requirements
    by creating them as netCDF4 files with variable-level compression enabled.
    Metadata that conforms to [CF-1.6 and SalishSeaCast project conventions][netCDF4 conventions] is included
    in the new files.

    [netCDF4 conventions]: https://salishsea-meopar-docs.readthedocs.org/en/latest/code-notes/salishsea-nemo/nemo-forcing/netcdf4.html#netcdf4-file-conventions

    All of that processing is implemented in the [`salishsea get_cgrf`][salishsea get_cgrf] command.
    This notebook provides explanation of that code,
    and verification that the created files contain wind and precipitation forcing
    values that are consistent with observations at Sandheads and YVR.

    [salishsea get_cgrf]: https://salishsea-meopar-tools.readthedocs.org/en/latest/SalishSeaCmd/salishsea-cmd.html#get-cgrf-sub-command

* ## [ProcessPramodArchive.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/ProcessPramodArchive.ipynb)

    Notebook to process Pramod's archived grib files to produce our netcdf files

* ## [OriginalVelocities.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/OriginalVelocities.ipynb)

* ## [CheckAltitude.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/CheckAltitude.ipynb)

    This notebook checks that the altitude.py script generates a files that are reasonable.

    It also combines the monthly altitude calculation into one file by averaging.

* ## [VerifyAtmosphericForcing.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/VerifyAtmosphericForcing.ipynb)

    **Verification of Atmospheric Forcing**

* ## [CGridLocations.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/CGridLocations.ipynb)

* ## [RadiationCheck.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/RadiationCheck.ipynb)

    This notebook compares the longwave/shortwave radiation from the GEM2.5 model provided by

    1. Pramod converted from grib2 format to netcdf covering all of Dec 2012
    2. Kao-Shen at Environment Canada covering 1 hour on Dec 16, 2012

    Question: Are the longwave/shortwave radiation variables in Pramod's netcdf files the ones we should be using? There are several radiation flux variables in the grib2 output.

    Description of grib2 variables
    https://weather.gc.ca/grib/HRDPS_HR/HRDPS_ps2p5km_P000_deterministic_e.html

    Plan: Comapre Pramod's radiation variables to Kao Shen's.

* ## [gribTnetcdf.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/gribTnetcdf.ipynb)

    Notebook to convert grib2 files to netCDF files that can be used in NEMO
    Makes use of wgrib2

* ## [netCDF4weights-CGRF.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/netCDF4weights-CGRF.ipynb)

    **Convert Atmospheric Forcing Weights to netCDF4**

    Transfer the values from the `met_gem_weight.nc`
    from the 2-Oct-2013 `WC3_PREP` tarball
    into a netCDF4 file with zlib compression on variables
    and CF-1.6 conventions conformant attributes.

* ## [ImproveWeightsFile.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/ImproveWeightsFile.ipynb)

    **Improve Atmospheric Forcing Weights File**

    Transfer the values from a `met_gem_weight.nc`
    created by `NEMO_EastCoast/NEMO_Preparation/4_weights_ATMOS/get_weight_nemo`
    into a netCDF4 file with zlib compression on variables
    and CF-1.6 conventions conformant attributes.

* ## [CheckGridCoLocation.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/CheckGridCoLocation.ipynb)

    Are the ugrid, vgrid and temperature at the same points

* ## [NoSnowIce.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/NoSnowIce.ipynb)

    **Create `no_snow_ice.nc` File for NEMO Surface Forcing**

    Create a netCDF4 file containing 2 variables named `snow` and `ice`.
    The coordinates of the variable are `y` and `x`.
    The values of `snow` and `ice` at all points in the domain is floating point zero.

    The resulting `no_snow_ice.nc` file can be used as an annual climatology in NEMO atmospheric forcing
    that does not require on-the-fly interpolation.
    It imposes a no snow, ever condition on the NEMO configuration.
    The no ice, ever condition that it provides works in conjunction with the code in `sbcice_if.F90` contributed by Michael Dunphy
    to provide a minimal ice-model substitute.
    In Michael's words,
    > "The point is to make sure water temperatures don’t go below the local freezing point,
    > and there are some limits on heat exchanges as well."

* ## [RotateVelocities.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/RotateVelocities.ipynb)

    Rotate the Wind

* ## [AtmosphereGridSelection.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/AtmosphereGridSelection.ipynb)

    Notebook to Look at Atmosphereic Domains and Choose Ours

* ## [CheckRotation.ipynb](https://nbviewer.org/github/SalishSeaCast/tools/blob/main/I_ForcingFiles/Atmos/CheckRotation.ipynb)


## License

These notebooks and files are copyright by the
[UBC EOAS MOAD Group](https://github.com/UBC-MOAD/docs/blob/main/CONTRIBUTORS.rst)
and The University of British Columbia.

They are licensed under the Apache License, Version 2.0.
https://www.apache.org/licenses/LICENSE-2.0
Please see the LICENSE file in this repository for details of the license.
