# Script to create TEOS-10 boundary conditions by modifing a previous set of
# boundary conditions.
# Usage: python create_TEOS-10_BCs.py input.nc output.nc title
# title is a string for the output file's title metadata
# At the moment, this only work consistently with python 2.7.
import netCDF4 as nc
import numpy as np

import shutil
import os
import datetime
import sys

from salishsea_tools import gsw_calls


def create_BCs(infile, outfile, title, dS_is_zero=True):
    """
    Create new boundary conditions in TEOS-10 variables.

    :arg str infile: path to netCDF file boundary conditions Practical
                     Salinity and Conservative Temperature
    :arg str outfile: path where new netCDF boundary conditions should be
                      saved

    :arg dS_is_zero: True if we are assuming dS = 0, in which case
                     we calculate Reference Salinity (SR). False for Absolute
                     Salinity (SA) calculated with matlab gsw function. Recall,
                     SA = SR + dS, so dS = 0 means SA = SR.
    :type dS_is_zero: boolean
    """
    try:
        shutil.copy(infile, outfile)
    except shutil.Error:
        print("Variables in {} will be overwritten.".format(infile))
    F = nc.Dataset(outfile, 'r+')
    # Load variables
    sal = F.variables['vosaline']
    temp = F.variables['votemper']
    dep = np.expand_dims(
        np.expand_dims(
            np.expand_dims(F.variables['deptht'][:], axis=0),
            axis=2),
        axis=3) + np.zeros(sal.shape)
    long = F.variables['nav_lon'][:] + np.zeros(sal[:].shape)
    lat = F.variables['nav_lat'][:] + np.zeros(sal[:].shape)
    # Create TEOS-10 stuff
    p = gsw_calls.generic_gsw_caller('gsw_p_from_z.m', [-dep, lat])
    sal_pract = np.copy(sal[:])
    if dS_is_zero:
        sal_abs = gsw_calls.generic_gsw_caller('gsw_SR_from_SP.m',
                                               [sal_pract, ])
        sal_title = 'Reference Salinity'
    else:
        sal_abs = gsw_calls.generic_gsw_caller('gsw_SA_from_SP.m',
                                               [sal_pract, p, long, lat])
        sal_title = 'Absolute Salinity'
    temp_pot = np.copy(temp[:])
    temp_cons = gsw_calls.generic_gsw_caller('gsw_CT_from_pt.m',
                                             [sal_abs, temp_pot])
    # Write into netcdf file
    sal[:] = sal_abs
    temp[:] = temp_cons
    # Update variable metadata
    sal.setncatts({'units': 'g/kg',
                   'long_name': sal_title})
    temp.setncatts({'units': 'deg C',
                    'long_name': 'Conservative Temperature'})
    # Update file metadata - maybe we should just pass this into function?
    F.title = title

    source = F.source
    F.source = source + ("\n https://bitbucket.org/salishsea/"
                         "tools/src/tip/I_ForcingFiles/OBC/"
                         "Temperature to conservative temperature in"
                         " boundary conditions.ipynb"
                         "\n https://bitbucket.org/salishsea/"
                         "tools/I_ForcingFiles/OBC/"
                         "create_TEOS-10_BCs.py")

    F.comment = "Temperature and salinity are TEOS-10 variables:"\
                " Conservative Temperature and {}".format(sal_title)

    F.references = "https://bitbucket.org/salishsea/nemo-forcing/src/tip/"\
                   "open_boundaries/{}/{}".format(os.path.basename(
                                                  os.path.split(outfile)[0]),
                                                  os.path.basename(outfile))

    history = F.history
    F.history = history + \
        ("\n [{} ] Converted temperature and salinity to Conservative "
         "Temperature and "
         "{}".format(datetime.datetime.today().strftime('%Y-%m-%d'),
                     sal_title)
         )

    F.close()


if __name__ == "__main__":
    create_BCs(sys.argv[1], sys.argv[2], sys.argv[3])
