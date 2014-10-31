# Standard Imports
from __future__ import division
import arrow
import os
import sys
import urllib

def GetGrib(forecast):
    '''Script to download GRIB2 data from EC webpage'''

    # variables we need
    variablenames = ("UGRD_TGL_10_","VGRD_TGL_10_","DSWRF_SFC_0_","DLWRF_SFC_0_", "TMP_TGL_2_",
                 "SPFH_TGL_2_","APCP_SFC_0_","PRMSL_MSL_0_")
    # template for filename
    filename_template = 'CMC_hrdps_west_{variable}ps2.5km_{date}{forecast}_P{hour}-00.grib2'
    # template for URL
    url_template = 'http://dd.weather.gc.ca/model_hrdps/west/grib2/{forecast}/{hour}/'
    # head of destination directory (your MEOPAR/GRIB)
    dirlead = "../../../GRIB/"

    # things we may, in the future, want to read as arguments
    utc = arrow.utcnow()
    now = utc.to('Canada/Pacific')
    date = now.format('YYYYMMDD')
    print date

    os.chdir(dirlead)
    if forecast == '06':
        os.mkdir(date)
    os.chdir(date)
    os.mkdir(forecast)
    os.chdir(forecast)
    for fhour in range(0,42+1):
        sfhour = '{:0=3}'.format(fhour)
        os.mkdir(sfhour)
        os.chdir(sfhour)
        for v in variablenames:
            filename = filename_template.format(variable=v,date=date,forecast=forecast,hour=sfhour)
            fileURL = url_template.format(forecast=forecast,hour=sfhour)+filename
            urllib.urlretrieve(fileURL, filename)
        os.chdir('..')
    os.chdir('..')


def main():
    """Command-line interface.
    """
    script = sys.argv[0]
    forecast = sys.argv[1]
    GetGrib(forecast)

if __name__ == '__main__':
    main()
