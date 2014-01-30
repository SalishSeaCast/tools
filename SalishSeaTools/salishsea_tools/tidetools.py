"""A collection of tools for dealing with tidal results for the Salish Sea Model
"""

"""
Copyright 2013-2014 The Salish Sea MEOPAR contributors
and The University of British Columbia

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import netCDF4 as NC
import numpy as np
import datetime
import requests
import pandas as pd
import pytz
from math import radians, sin, cos, asin, sqrt, pi, exp
import matplotlib.pyplot as plt
import matplotlib


def get_all_perm_dfo_wlev(start_date,end_date):

    """
    Get water level data for all permanent DFO water level sites for specified period.
    e.g. get_all_perm_dfo_wlev('01-JAN-2010','31-JAN-2010')

    :arg start_date: string containing the start date e.g. '01-JAN-2010'
    :type start_date: str

    :arg end_date: string containing the end date e.g. '31-JAN-2010'
    :type end_date: str

    :returns: Saves text files with water level data at each site
    """
    stations = {'Point Atkinson':7795, 'Vancouver':7735, 'Patricia Bay':7277, 'Victoria Harbour':7120, 'Bamfield':8545, 'Tofino':8615, 'Winter Harbour':8735, 'Port Hardy':8408, 'Campbell River':8074, 'New Westminster':7654}
    for ttt in stations:
           get_dfo_wlev(stations[ttt],start_date,end_date)

def get_dfo_wlev(station_no,start_date,end_date):
    """
    Download water level data from DFO site for one DFO station for specified period.
    e.g. get_dfo_wlev(7795,'01-JAN-2003','01-JAN-2004')

    :arg station_no: station number e.g. 7795
    :type station_no: int

    :arg start_date: string containing the start date e.g. '01-JAN-2010'
    :type start_date: str

    :arg end_date: string containing the end date e.g. '31-JAN-2010'
    :type end_date: str

    :returns: Saves text file with water level data at one station
    """
    #name the output file
    outfile = 'wlev_'+str(station_no)+'_'+start_date+'_'+end_date+'.csv'
    #form urls and html information
    base_url = 'http://www.meds-sdmm.dfo-mpo.gc.ca/isdm-gdsi/twl-mne/inventory-inventaire/'
    form_handler = 'data-donnees-eng.asp?user=isdm-gdsi&region=PAC&tst=1&no='+str(station_no)
    sitedata = {'start_period': start_date,'end_period': end_date,'resolution': 'h','time_zone': 'l'}
    data_provider = 'download-telecharger.asp?File=E:%5Ciusr_tmpfiles%5CTWL%5C'+str(station_no)+'-'+start_date+'_slev.csv&Name='+str(station_no)+'-'+start_date+'_slev.csv'
    #go get the data from the DFO site
    with requests.Session() as s:
        s.post(base_url + form_handler, data=sitedata)
        r = s.get(base_url + data_provider)
    #write the data to a text file
    with open(outfile, 'w') as f:
        f.write(r.text)
#    print('Results saved here: '+outfile)

def dateParserMeasured(s):
    """
    Function to make datetime object aware of time zone
    e.g. date_parser=dateParserMeasured

    :arg s: string of date and time
    :type s: str

    :returns: datetime object that is timezone aware
    """
    #convert the string to a datetime object
    unaware = datetime.datetime.strptime(s, "%Y/%m/%d %H:%M")
    #add in the local time zone (Canada/Pacific)
    aware = unaware.replace(tzinfo=pytz.timezone('Canada/Pacific'))
    #convert to UTC
    return aware.astimezone(pytz.timezone('UTC'))

def read_dfo_wlev_file(filename):
    """
    Read in the data in the csv file downloaded from DFO website
    e.g. dates, wlev, stat_name, stat_num, stat_lat, stat_lon = tidetools.read_dfo_wlev('wlev_timeseries.csv')

    :arg filename: string of filename to read in
    :type filename: str

    :returns: measured time, measured water level, station name, station number, station lat, station long
    """
    info = pd.read_csv(filename,nrows=4,index_col=0,header=None)
    wlev_meas = pd.read_csv(filename,skiprows=7,parse_dates=[0],date_parser=dateParserMeasured)
    wlev_meas = wlev_meas.rename(columns={'Obs_date': 'time', 'SLEV(metres)': 'slev'})
    #allocate the variables to nice names
    stat_name = info[1][0]
    stat_num = info[1][1]
    stat_lat = info[1][2]
    stat_lon = info[1][3]
    #measured times are in PTZ - first make dates aware of this, then convert dates to UTC
    for x in np.arange(0,len(wlev_meas.time)):
        wlev_meas.time[x] = wlev_meas.time[x].replace(tzinfo=pytz.timezone('Canada/Pacific'))
        print(wlev_meas.time[x])
        wlev_meas.time[x] = wlev_meas.time[x].astimezone(pytz.timezone('UTC'))
        print(wlev_meas.time[x])
    return wlev_meas.time, wlev_meas.slev, stat_name, stat_num, stat_lat, stat_lon

def get_amp_phase_data(runname,loc):
    """
    get the amplitude and phase data for a model run

    :arg runname: name of the model run to process e.g. runname = '50s_15Sep-21Sep', or if you'd like the harmonics of more than one run to be combined into one picture, give a list of names e.g. '40d','41d50d','51d60d'
    :type runname: str

    :arg loc: location of results folder e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :returns: mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha
    """
    if runname == 'concepts110':
        mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_concepts110(loc+runname)
        mod_K1_amp = 0.0
        mod_K1_pha = 0.0
    elif runname == 'jpp72':
        mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_jpp72(loc+runname)
        mod_K1_amp = 0.0
        mod_K1_pha = 0.0
    #'composite' was the first set of runs where I combined the harmonics
    elif runname == 'composite':
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_composite_harms2()
    #this step combines the harmonics of any specified runs
    elif type(runname) is not str and len(runname)>1:
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_composite_harms(runname,loc)
    #this step just gets the harmonics for the one specified run
    else:
       mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data(loc+runname)
    
    return mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha

def plot_amp_phase_maps(runname,loc,grid):
    """
    Plot the amplitude and phase results for a model run
    e.g. plot_amp_phase_maps('50s_15Sep-21Sep')

    :arg runname: name of the model run to process e.g. runname = '50s_15Sep-21Sep', or if you'd like the harmonics of more than one run to be combined into one picture, give a list of names e.g. '40d','41d50d','51d60d'
    :type runname: str

    :arg loc: location of results folder e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :arg grid: netcdf file of grid data e.g. grid = NC.Dataset('/ocean/klesouef/meopar/nemo-forcing/grid/bathy_meter_SalishSea2.nc','r')
    :type grid: netcdf dataset

    :returns: plots the amplitude and phase
    """
    mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_amp_phase_data(runname,loc)
    bathy, X, Y = get_bathy_data(grid)
    titname = ''.join(runname)
    plot_amp_map(X,Y,grid,mod_M2_amp,titname,True,'M2')
    plot_pha_map(X,Y,grid,mod_M2_pha,titname,True,'M2')
    if runname != 'concepts110' and runname != 'jpp72':
        plot_amp_map(X,Y,grid,mod_K1_amp,titname,True,'K1')
        plot_pha_map(X,Y,grid,mod_K1_pha,titname,True,'K1')


def get_netcdf_amp_phase_data(loc):
    """
    Calculate amplitude and phase from the results of a particular run of the Salish Sea model
    e.g. mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data('50s_15Sep-21Sep')

    :arg runname: name of the model run to process e.g. '50s_15Sep-21Sep'
    :type runname: str

    :returns: model M2 amplitude, model K1 amplitude, model M2 phase, model K1 phase
    """
    harmT = NC.Dataset(loc+'/Tidal_Harmonics_eta.nc','r')
     #get imaginary and real components
    mod_M2_eta_real = harmT.variables['M2_eta_real'][0,:,:]
    mod_M2_eta_imag = harmT.variables['M2_eta_imag'][0,:,:]
    mod_K1_eta_real = harmT.variables['K1_eta_real'][0,:,:]
    mod_K1_eta_imag = harmT.variables['K1_eta_imag'][0,:,:]
     #convert to amplitude and phase
    mod_M2_amp = np.sqrt(mod_M2_eta_real**2+mod_M2_eta_imag**2)
    mod_M2_pha = -np.degrees(np.arctan2(mod_M2_eta_imag,mod_M2_eta_real))
    mod_K1_amp = np.sqrt(mod_K1_eta_real**2+mod_K1_eta_imag**2)
    mod_K1_pha = -np.degrees(np.arctan2(mod_K1_eta_imag,mod_K1_eta_real))
    return mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha

def get_netcdf_amp_phase_data_jpp72(loc):
    """
    Calculate amplitude and phase from the results of the JPP72 model
    e.g. mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_jpp72()

    :returns: model M2 amplitude, model M2 phase
    """
    harmT = NC.Dataset(loc+'/JPP_1d_20020102_20020104_grid_T.nc','r')
    #Get amplitude and phase
    mod_M2_x_elev = harmT.variables['M2_x_elev'][0,:,:] #Cj
    mod_M2_y_elev = harmT.variables['M2_y_elev'][0,:,:] #Sj
    #see section 11.6 of NEMO manual (p223/367)
    mod_M2_amp = np.sqrt(mod_M2_x_elev**2+mod_M2_y_elev**2)
    mod_M2_pha = -np.degrees(np.arctan2(mod_M2_y_elev,mod_M2_x_elev))
    return mod_M2_amp, mod_M2_pha

def get_netcdf_amp_phase_data_concepts110(loc):
    """
    Calculate amplitude and phase from the results of the CONCEPTS110 model
    e.g. mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_concepts110()

    :returns: model M2 amplitude, model M2 phase
    """
    harmT = NC.Dataset(loc+'/WC3_Harmonics_gridT_TIDE2D.nc','r')
    mod_M2_amp = harmT.variables['M2_amp'][0,:,:]
    mod_M2_pha = harmT.variables['M2_pha'][0,:,:]
    return mod_M2_amp, mod_M2_pha

def get_bathy_data(grid):
    """
    Get the Salish Sea bathymetry from specified grid NC.Dataset
    e.g. bathy, X, Y = get_bathy_data(grid)

    :arg grid: netcdf object of model grid
    :type grid: netcdf dataset

    :returns: bathy, X, Y
    """
    bathy = grid.variables['Bathymetry'][:,:]
    X = grid.variables['nav_lon'][:,:]
    Y = grid.variables['nav_lat'][:,:]
    return bathy, X, Y

def get_SS_bathy_data():
    """
    Not used any more - assumes that the user is klesouef! :)
    Get the Salish Sea bathymetry and grid data
    e.g. bathy, X, Y = get_SS_bathy_data()

    :returns: bathy, X, Y
    """
    grid = NC.Dataset('/ocean/klesouef/meopar/nemo-forcing/grid/bathy_meter_SalishSea.nc','r')
    bathy = grid.variables['Bathymetry'][:,:]
    X = grid.variables['nav_lon'][:,:]
    Y = grid.variables['nav_lat'][:,:]
    return bathy, X, Y

def get_SS2_bathy_data():
    """
    Not used any more - assumes that the user is klesouef! :)
    Get the Salish Sea 2 bathymetry and grid data
    e.g. bathy, X, Y = get_SS2_bathy_data()

    :returns: bathy, X, Y
    """
    grid = NC.Dataset('/ocean/klesouef/meopar/nemo-forcing/grid/bathy_meter_SalishSea2.nc','r')
    bathy = grid.variables['Bathymetry'][:,:]
    X = grid.variables['nav_lon'][:,:]
    Y = grid.variables['nav_lat'][:,:]
    return bathy, X, Y

#define a function to get the subdomain bathymetry and grid data
def get_subdomain_bathy_data():
    """
    Not used any more - assumes that the user is klesouef! :)
    Get the subdomain bathymetry and grid data
    e.g. bathy, X, Y = get_subdomain_bathy_data()

    :returns: bathy, X, Y
    """
    grid = NC.Dataset('/ocean/klesouef/meopar/nemo-forcing/grid/SubDom_bathy_meter_NOBCchancomp.nc','r')
    bathy = grid.variables['Bathymetry'][:,:]
    X = grid.variables['nav_lon'][:,:]
    Y = grid.variables['nav_lat'][:,:]
    return bathy, X, Y

def find_closest_model_point(lon,lat,X,Y,bathy):
    """
    Gives the grid co-ordinates of the closest non-land model point to a specified lon/lat.

    e.g. x1, j1 = find_closest_model_point(-125.5,49.2,X,Y,bathy)

    where bathy, X and Y are returned from get_SS_bathy_data() or get_subdomain_bathy_data()

    :arg lon: specified longitude
    :type lon: float

    :arg lat: specified latitude
    :type lat: float

    :arg X: specified model longitude
    :type X: numpy array

    :arg Y: specified model latitude
    :type Y: numpy array

    :arg bathy: model bathymetry
    :type bathy: numpy array

    :returns: x1, j1
    """
    #tolerance for searching for grid points (approx. distances between adjacent grid points)
    tol1 = 0.0052  #lon
    tol2 = 0.00189 #lat

    #search for a grid point with lon/lat within tolerance of measured location
    x1, y1=np.where(np.logical_and((np.logical_and(X>lon-tol1,X<lon+tol1)),np.logical_and(Y>lat-tol2,Y<lat+tol2)))
    if np.size(x1)!=0:
        x1 = x1[0]
        y1 = y1[0]
        #What if more than one point is returned from this search? Just take the first one...

        #if x1,y1 is masked, search 3x3 grid around. If all those points are masked, search 4x4 grid around etc
        for ii in np.arange(1,100):
            if bathy.mask[x1,y1]==True:
                for i in np.arange(x1-ii,x1+ii+1):
                    for j in np.arange(y1-ii,y1+ii+1):
                        if bathy.mask[i,j] == False:
                            break
                    if bathy.mask[i,j] == False:
                        break
                if bathy.mask[i,j] == False:
                    break
            else:
                i = x1
                j = y1
    else:
            i=[]
            j=[]
    return i, j

def plot_amp_map(X,Y,grid,amp,titstr,savestr,constflag):
    """
    Plot the amplitude of one constituent throughout the whole domain
    e.g. plot_amp_map(X,Y,grid,mod_M2_amp,'50s_12Sep-19Sep',savestr,'M2')

    :arg X: specified model longitude
    :type X: numpy array

    :arg Y: specified model latitude
    :type Y: numpy array

    :arg grid: model grid netcdf
    :type grid: netcdf dataset

    :arg amp: amplitude
    :type amp: numpy array

    :arg titstr: name of model run
    :type titstr: str

    :arg savestr: flag to save
    :type savestr: bool

    :arg constflag: name of constituent
    :type constflag: str

    :returns: plot of amplitude of constituent
    """
    #make 0 values NaNs so they plot blank
    amp = np.ma.masked_equal(amp,0)
    #range of amplitudes to plot
    plt.figure(figsize=(9,9))
    #add a coastline 
    plot_coastline(grid)
    #add the amplitude contours
    v2 = np.arange(0,1.30,0.10)
    CS = plt.contourf(X,Y,amp,v2,aspect=(1 / np.cos(np.median(X) * np.pi / 180)))
    CS2 = plt.contour(X,Y,amp,v2,colors='black')
    cbar = plt.colorbar(CS)
    cbar.add_lines(CS2)
    cbar.ax.set_ylabel('amplitude [m]')
    plt.xlabel('longitude (deg)')
    plt.ylabel('latitude (deg)')
    plt.title(constflag+' amplitude (m) for '+titstr)
    if savestr:
        plt.savefig(constflag+'_amp_'+titstr+'.pdf')

def plot_pha_map(X,Y,grid,pha,titstr,savestr,constflag):
    """
    Plot the phase of one constituent throughout the whole domain
    e.g. plot_pha_map(X,Y,grid,mod_M2_pha,titstr,savestr,'M2')

    :arg X: specified model longitude
    :type X: numpy array

    :arg Y: specified model latitude
    :type Y: numpy array

    :arg pha: phase
    :type pha: numpy array

    :arg titstr: name of model run
    :type titstr: str

    :arg savestr: flag to save
    :type savestr: bool

    :arg constflag: name of constituent
    :type constflag: str

    :returns: plot of phase of constituent
    """
    #make 0 values NaNs so they plot blank
    pha = np.ma.masked_equal(pha,0)
    plt.figure(figsize=(9,9))
    #add a coastline 
    plot_coastline(grid)
    #plot modelled M2 phase
    v2 = np.arange(-180, 202.5,22.5)
    CS = plt.contourf(X,Y,pha,v2,cmap='gist_rainbow',aspect=(1 / np.cos(np.median(X) * np.pi / 180)))
    matplotlib.rcParams['contour.negative_linestyle'] = 'solid'
    CS2 = plt.contour(X,Y,pha,v2,colors='black')
    cbar = plt.colorbar(CS)
    cbar.add_lines(CS2)
    cbar.ax.set_ylabel('phase [deg]')
    plt.xlabel('longitude (deg)')
    plt.ylabel('latitude (deg)')
    plt.title(constflag+' phase (deg) for '+titstr)
    limits = plt.axis()
    if savestr:
        plt.savefig(constflag+'_pha_'+titstr+'.pdf')

def plot_scatter_pha_amp(Am,Ao,gm,go,constflag,runname):
    """
    Plot scatter plot of measured vs. modelled phase and amplitude
    plot_scatter_pha_amp(Am_K1_all,Ao_K1_all,gm_K1_all,go_K1_all,'K1','50s_30Sep-6Oct')

    :arg Am: modelled amplitude
    :type Am: numpy array

    :arg Ao: observed amplitude
    :type Ao: numpy array

    :arg gm: modelled phase
    :type gm: str

    :arg go: observed phase
    :type go: str

    :arg constflag: name of constituent
    :type constflag: str

    :arg runname: name of model run
    :type runname: str

    :returns: plots and saves scatter plots of measured vs. modelled phase and amplitude
    """
    import matplotlib.pyplot as plt
    plt.figure()
    plt.subplot(1,2,1,aspect='equal')
    plt.plot(Am,Ao,'.')
    plt.plot([0,1],[0,1],'r')
    plt.axis([0,1,0,1])
    plt.xlabel('Modelled amplitude [m]')
    plt.ylabel('Measured amplitude [m]')
    plt.title(constflag)

    plt.subplot(1,2,2,aspect='equal')
    plt.plot(gm,go,'.')
    plt.plot([0,360],[0,360],'r')
    plt.axis([0,360,0,360])
    plt.xlabel('Modelled phase [deg]')
    plt.ylabel('Measured phase [deg]')
    plt.title(constflag)
    plt.savefig(constflag+'_scatter_comps_'+''.join(runname)+'.pdf')

def plot_diffs_on_domain(D,meas_wl_harm,calcmethod,constflag,runname,grid):
    """
    Plot differences as circles of varying radius on a map of the model domain
    e.g. plot_diffs_on_domain(D_F95_all_M2,meas_wl_harm,'F95','M2',runname,grid)

    :arg D: differences calculated between measured and modelled
    :type D: numpy array

    :arg meas_wl_harm: measured water level harmonics read in from csv
    :type meas_wl_harm: numpy array

    :arg calcmethod: method for calculating differences ('F95' or 'M04')
    :type calcmethod: str

    :arg constflag: name of constituent
    :type constflag: str

    :arg runname: name of model run
    :type runname: str

    :returns: plots and saves plots of differences as circles of varying radius on a map of the model domain
    """
    #plot the bathy underneath
    bathy, X, Y = get_bathy_data(grid)
    plt.figure(figsize=(9,9))
    plt.contourf(X,Y,bathy,cmap='spring')
    cbar = plt.colorbar()
    cbar.set_label('depth [m]')
    scalefac = 100

    #plot the differences as dots of varying radii
    legendD = 0.1 #[m]
    #multiply the differences by something big to see the results on a map (D is in [m])
    area = np.array(D)*scalefac
    plt.scatter(np.array(meas_wl_harm.Lon)*-1, meas_wl_harm.Lat, c='b', s=area, marker='o')
    plt.scatter(-124.5,47.9,c='b',s=(legendD*scalefac), marker='o')
    plt.text(-124.4,47.9,'D='+(str(legendD*100))+'cm')
    plt.xlabel('Longitude (deg)')
    plt.ylabel('Latitude (deg)')

    #plot colours and add labels depending on calculation method
    if calcmethod == 'F95':
        plt.scatter(np.array(meas_wl_harm.Lon)*-1, meas_wl_harm.Lat, c='b', s=area, marker='o')
        plt.scatter(-124.5,47.9,c='b',s=(legendD*scalefac), marker='o')
        plt.title(constflag+' differences (Foreman et al) for '+''.join(runname))
        plt.savefig(constflag+'_diffs_F95_'+''.join(runname)+'.pdf')
    if calcmethod == 'M04':
        plt.scatter(np.array(meas_wl_harm.Lon)*-1, meas_wl_harm.Lat, c='g', s=area, marker='o')
        plt.scatter(-124.5,47.9,c='g',s=(legendD*scalefac), marker='o')
        plt.title(constflag+' differences (Masson & Cummins) for '+''.join(runname))
        plt.savefig(constflag+'_diffs_M04_'+''.join(runname)+'.pdf')

def calc_diffs_meas_mod(runname,loc,grid):
    """
    Calculate differences between measured and modelled water level
    e.g. meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all, D_M04_M2_all,Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all = calc_diffs_meas_mod('50s_13Sep-20Sep')

    :arg runname: name of model run
    :type runname: str

    :returns: meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all, D_M04_M2_all,Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all
    """
    #read in the measured data from Foreman et al (1995) and US sites
    import pandas as pd
    meas_wl_harm = pd.read_csv('obs_tidal_wlev_const_all.csv',sep=';')
    meas_wl_harm = meas_wl_harm.rename(columns={'M2 amp': 'M2_amp', 'M2 phase (deg UT)': 'M2_pha', 'K1 amp': 'K1_amp', 'K1 phase (deg UT)': 'K1_pha'})

    import angles
    #make an appropriately named csv file for results
    outfile = 'wlev_harm_diffs_'+''.join(runname)+'.csv'
    D_F95_M2_all = []
    D_M04_M2_all = []
    Am_M2_all = []
    Ao_M2_all = []
    gm_M2_all = []
    go_M2_all = []

    D_F95_K1_all = []
    D_M04_K1_all = []
    Am_K1_all = []
    Ao_K1_all = []
    gm_K1_all = []
    go_K1_all = []

    #get harmonics data
    mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_amp_phase_data(runname,loc)

    #get bathy data
    bathy, X, Y = get_bathy_data(grid)

    with open(outfile, 'wb') as csvfile:
        import csv
        import numpy as np
        from math import radians, cos, sin, asin, sqrt, pi

        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['Station Number','Station Name','Longitude','Latitude','Modelled M2 amp','Observed M2 amp',\
        'Modelled M2 phase','Observed M2 phase','M2 Difference Foreman','M2 Difference Masson',\
        'Modelled K1 amp','Observed K1 amp','Modelled K1 phase','Observed K1 phase',\
        'K1 Difference Foreman','K1 Difference Masson'])
        for t in np.arange(0,len(meas_wl_harm.Lat)):
            x1, y1 = find_closest_model_point(-meas_wl_harm.Lon[t],meas_wl_harm.Lat[t],X,Y,bathy)
            if x1:
                #observed constituents
                Ao_M2 = meas_wl_harm.M2_amp[t]/100 #[m]
                go_M2 = meas_wl_harm.M2_pha[t]  #[degrees UTC]
                Ao_K1 = meas_wl_harm.K1_amp[t]/100 #[m]
                go_K1 = meas_wl_harm.K1_pha[t]  #[degrees UTC]
                #modelled constituents
                Am_M2 = mod_M2_amp[x1,y1] #[m]
                gm_M2 = angles.normalize(mod_M2_pha[x1,y1],0,360) #[degrees ????]
                Am_K1 = mod_K1_amp[x1,y1] #[m]
                gm_K1 = angles.normalize(mod_K1_pha[x1,y1],0,360) #[degrees ????]
                #calculate differences two ways
                D_F95_M2 = sqrt((Ao_M2*np.cos(radians(go_M2))-Am_M2*np.cos(radians(gm_M2)))**2 + (Ao_M2*np.sin(radians(go_M2))-Am_M2*np.sin(radians(gm_M2)))**2)
                D_M04_M2 = sqrt(0.5*(Am_M2**2+Ao_M2**2)-Am_M2*Ao_M2*cos(radians(gm_M2-go_M2)))
                D_F95_K1 = sqrt((Ao_K1*np.cos(radians(go_K1))-Am_K1*np.cos(radians(gm_K1)))**2 + (Ao_K1*np.sin(radians(go_K1))-Am_K1*np.sin(radians(gm_K1)))**2)
                D_M04_K1 = sqrt(0.5*(Am_K1**2+Ao_K1**2)-Am_K1*Ao_K1*cos(radians(gm_K1-go_K1)))
                #write results to csv
                writer.writerow([str(t+1),meas_wl_harm.Site[t],-meas_wl_harm.Lon[t],meas_wl_harm.Lat[t],  Am_M2, Ao_M2, gm_M2, go_M2, D_F95_M2, D_M04_M2, Am_K1, Ao_K1, gm_K1, go_K1, D_F95_K1, D_M04_K1])
                #append the latest result
                Am_M2_all.append(float(Am_M2))
                Ao_M2_all.append(float(Ao_M2))
                gm_M2_all.append(float(gm_M2))
                go_M2_all.append(float(go_M2))
                D_F95_M2_all.append(float(D_F95_M2))
                D_M04_M2_all.append(float(D_M04_M2))
                Am_K1_all.append(float(Am_K1))
                Ao_K1_all.append(float(Ao_K1))
                gm_K1_all.append(float(gm_K1))
                go_K1_all.append(float(go_K1))
                D_F95_K1_all.append(float(D_F95_K1))
                D_M04_K1_all.append(float(D_M04_K1))
            else:
                #if no point found, fill difference fields with 9999
                print('No point found in current domain for station '+str(t+1)+' :(')
                writer.writerow([str(t+1),meas_wl_harm.Site[t],-meas_wl_harm.Lon[t],meas_wl_harm.Lat[t],9999,9999])

#    print('Results saved here: '+outfile)
    return meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all, D_M04_M2_all,Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the distance between two points (from haversine on SO)
    e.g. dist = haversine(-125.1,49.1,-125.12,49.5)

    :arg lon1: longitude of point 1
    :type lon1: float

    :arg lat1: latitude of point 1
    :type lat1: float

    :arg lon2: longitude of point 2
    :type lon2: float

    :arg lat2: latitude of point 2
    :type lat2: float

    :returns: distance between two points in km
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    print('Observation site and model grid point are '+str(round(km,3))+'km apart')
    return km

def plot_meas_mod_locations(measlon, measlat, modlon, modlat,X,Y,bathy):
    """
    Plot two locations on a contour map of bathymetry, where bathy, X and Y are returned from get_SS_bathy_data() or get_subdomain_bathy_data()
    e.g. plot_meas_mod_locations(-124.0, 48.4, -124.2, 48.1,X,Y,bathy)

    :arg measlon: longitude of point 1
    :type measlon: float

    :arg measlat: latitude of point 1
    :type measlat: float

    :arg modlon: longitude of point 2
    :type modlon: float

    :arg modlat: latitude of point 2
    :type modlat: float

    :arg X: specified model longitude
    :type X: numpy array

    :arg Y: specified model latitude
    :type Y: numpy array

    :arg bathy: model bathymetry
    :type bathy: numpy array

    :returns: plots contour plot with 2 points
    """
    plt.contourf(X,Y,bathy)
    plt.colorbar()
    plt.title('Domain of model (depths in m)')
    hold = True
    plt.plot(modlon,modlat,'g.',markersize=10,label='model')
    plt.plot(measlon,measlat,'m.',markersize=10,label='measured')
    plt.xlim([modlon-0.1,modlon+0.1])
    plt.ylim([modlat-0.1,modlat+0.1])
    plt.legend(numpoints=1)

def plot_wlev_const_transect(savename,statnums,runname,loc,grid,*args):
    """
    Plot water level of the modelled M2 and K1 constituents and measured M2 and K1 constituents in a transect at specified stations
    e.g. plot_wlev_const_transect('40d','/ocean/klesouef/meopar/)

    :arg savename: tag for saving the pdf pics
    :type savename: str

    :arg statnums: array of station numbers
    :type statnums: numpy array

    :arg runname: unique name of run
    :type runname: str

    :arg loc: location of model results
    :type loc: str

    :arg grid: netcdf dataset of model grid
    :type grid: netcdf dataset

    :arg args: other runname and results location strings, in case you want to plot more than set of model results on the same figure 
    :type args: str

    :returns: plots transect of M2 and K1 water level constituent
    """
    #runname1, loc1, runname2, loc2
    fig1 = plt.figure(figsize=(15,5))
    ax1 = fig1.add_subplot(111)
    ax1.set_xlabel('Station number [-]')
    ax1.set_ylabel('M2 amplitude [m]')
    fig2 = plt.figure(figsize=(15,5))
    ax2 = fig2.add_subplot(111)
    ax2.set_xlabel('Station number [-]')
    ax2.set_ylabel('K1 amplitude [m]')

    #get the modelled data
    meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all, D_M04_M2_all, Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all = calc_diffs_meas_mod(runname,loc,grid)
    Am_M2_all = np.array(Am_M2_all)
    Ao_M2_all = np.array(Ao_M2_all)
    Am_K1_all = np.array(Am_K1_all)
    Ao_K1_all = np.array(Ao_K1_all)
    #just take the model values at teh statnums we want
    some_model_amps_M2 = np.array([Am_M2_all[statnums]])
    some_model_amps_K1 = np.array([Am_K1_all[statnums]])
    x = np.array(range(0,len(statnums)))
    #plot the M2 model data
    ax1.plot(x,some_model_amps_M2[0,:],'b-o', label=runname+'_model')
    #plot the K1 model data
    ax2.plot(x,some_model_amps_K1[0,:],'b--o', label=runname+'_model')

    if len(args)>0:
        #assuming we will only be adding an additional 3 lines, define 3 colours
        colours = ['g','m','k','r','y']
        for r in range(0,len(args)/2):
            runname = args[2*r]
            loc = args[2*r+1]
            meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all, D_M04_M2_all, Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all = calc_diffs_meas_mod(runname,loc,grid)
            Am_M2_all = np.array(Am_M2_all)
            Ao_M2_all = np.array(Ao_M2_all)
            Am_K1_all = np.array(Am_K1_all)
            Ao_K1_all = np.array(Ao_K1_all)
            some_model_amps_M2 = np.array([Am_M2_all[statnums]])
            some_model_amps_K1 = np.array([Am_K1_all[statnums]])
            x = np.array(range(0,len(statnums)))
            ax1.plot(x,some_model_amps_M2[0,:],'-o',color = colours[r], label=''.join(runname)+'_model')
            ax2.plot(x,some_model_amps_K1[0,:],'--o',color = colours[r], label=''.join(runname)+'_model')

    meas_wl_harm = pd.read_csv('obs_tidal_wlev_const_all.csv',sep=';')
    some_meas_amps_M2 = np.array([Ao_M2_all[statnums]])
    some_meas_amps_K1 = np.array([Ao_K1_all[statnums]])
    sitenames = list(meas_wl_harm.Site[statnums])
    sitelats = np.array(meas_wl_harm.Lat[statnums])
    #M2
    ax1.plot(x,some_meas_amps_M2[0,:],'r-o',label='measured')
    ax1.set_xticks(x)
    ax1.set_xticklabels(statnums+1)
    ax1.legend(loc='lower right')
    ax1.set_title('Line through stations '+str(statnums))
    fig1.savefig('meas_mod_wlev_transect_M2_'+''.join(runname)+'_'+savename+'.pdf')
    #K1
    ax2.plot(x,some_meas_amps_K1[0,:],'r--o',label='measured')
    ax2.set_xticks(x)
    ax2.set_xticklabels(statnums+1)
    ax2.legend(loc='lower right')
    ax2.set_title('Line through stations '+str(statnums))
    fig2.savefig('meas_mod_wlev_transect_K1_'+''.join(runname)+'_'+savename+'.pdf')

def plot_wlev_transect_map(grid,statnums):
    """
    Plot a map of the coastline and the transect of water level stations, which are plotted in plot_wlev_M2_const_transect

    :arg grid: bathymetry file
    :type grid: netcdf dataset

    :arg statnums: station numbers to plot
    :type statnums: numpy array

    :returns: plot of water level stations and coastline
    """

    plt.figure(figsize=(9,9))
    #add a coastline 
    plot_coastline(grid)
    #get the measured data
    meas_wl_harm = pd.read_csv('obs_tidal_wlev_const_all.csv',sep=';')
    sitenames = list(meas_wl_harm.Site[statnums])
    sitelats = np.array(meas_wl_harm.Lat[statnums])
    sitelats = np.array(meas_wl_harm.Lat[statnums])
    sitelons = np.array(-meas_wl_harm.Lon[statnums])
    #plot the transext line
    plt.plot(sitelons,sitelats,'m-o')
    plt.title('Location of Select Stations')
    plt.savefig('meas_mod_wlev_transect_map.pdf')

def plot_coastline(grid):
    """
    Plots a map of the coastline 

    :arg grid: netcdf file of bathymetry
    :type grid: netcdf dataset

    :returns: coastline map
    """
    v1 = np.arange(0, 1, 1)
    lats = grid.variables['nav_lat']
    lons = grid.variables['nav_lon']
    depths = grid.variables['Bathymetry']
    plt.contour(lons,lats,depths,v1,colors='black')

def get_composite_harms2():
    """
    Take the results of the following runs (which are all the same model setup) and combine the harmonics into one 'composite' run
    50s_15-21Sep
    50s_22-25Sep
    50s_26-29Sep
    50s_30Sep-6Oct
    50s_7-13Oct
    
    :returns: mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha
    """

    runnames = ['50s_15-21Sep','50s_22-25Sep','50s_26-29Sep','50s_30Sep-6Oct','50s_7-13Oct']
    runlength = np.array([7.0,4.0,4.0,7.0,7.0])

    mod_M2_eta_real1 = 0.0
    mod_M2_eta_imag1 = 0.0
    mod_K1_eta_real1 = 0.0
    mod_K1_eta_imag1 = 0.0

    for runnum in range(0,len(runnames)):
        harmT = NC.Dataset('/data/dlatorne/MEOPAR/SalishSea/results/'+runnames[runnum]+'/Tidal_Harmonics_eta.nc','r')
        #get imaginary and real components
        mod_M2_eta_real1 = mod_M2_eta_real1 + harmT.variables['M2_eta_real'][0,:,:]*runlength[runnum]
        mod_M2_eta_imag1 = mod_M2_eta_imag1 + harmT.variables['M2_eta_imag'][0,:,:]*runlength[runnum]
        mod_K1_eta_real1 = mod_K1_eta_real1 + harmT.variables['K1_eta_real'][0,:,:]*runlength[runnum]
        mod_K1_eta_imag1 = mod_K1_eta_imag1 + harmT.variables['K1_eta_imag'][0,:,:]*runlength[runnum]

    totaldays = sum(runlength)
    mod_M2_eta_real = mod_M2_eta_real1/totaldays
    mod_M2_eta_imag = mod_M2_eta_imag1/totaldays
    mod_K1_eta_real = mod_K1_eta_real1/totaldays
    mod_K1_eta_imag = mod_K1_eta_imag1/totaldays
    mod_M2_amp = np.sqrt(mod_M2_eta_real**2+mod_M2_eta_imag**2)
    mod_M2_pha = -np.degrees(np.arctan2(mod_M2_eta_imag,mod_M2_eta_real))
    mod_K1_amp = np.sqrt(mod_K1_eta_real**2+mod_K1_eta_imag**2)
    mod_K1_pha = -np.degrees(np.arctan2(mod_K1_eta_imag,mod_K1_eta_real))

    return mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha


def get_composite_harms(runname,loc):
    """
    Take the results of the specified runs (which must all have the same model setup) and combine the harmonics into one 'composite' run

    :arg runname: name of the model run to process e.g. runname = '50s_15Sep-21Sep', or if you'd like the harmonics of more than one run to be combined into one picture, give a list of names e.g. '40d','41d50d','51d60d'
    :type runname: str

    :arg loc: location of results folder e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str
    
    :returns: mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha
    """
    runlength = np.zeros((len(runname),1))
    for k in range(0,len(runname)):
        runlength[k,0] = get_run_length(runname[k],loc)
#        print 'length of run '+str(k)+' = '+str(runlength[k,0])+' days'

    mod_M2_eta_real1 = 0.0
    mod_M2_eta_imag1 = 0.0
    mod_K1_eta_real1 = 0.0
    mod_K1_eta_imag1 = 0.0

    for runnum in range(0,len(runname)):
        harmT = NC.Dataset('/ocean/dlatorne/MEOPAR/SalishSea/results/'+runname[runnum]+'/Tidal_Harmonics_eta.nc','r')
#        print '/ocean/dlatorne/MEOPAR/SalishSea/results/'+runname[runnum]+'/Tidal_Harmonics_eta.nc'
        #get imaginary and real components
        mod_M2_eta_real1 = mod_M2_eta_real1 + harmT.variables['M2_eta_real'][0,:,:]*runlength[runnum]
        mod_M2_eta_imag1 = mod_M2_eta_imag1 + harmT.variables['M2_eta_imag'][0,:,:]*runlength[runnum]
        mod_K1_eta_real1 = mod_K1_eta_real1 + harmT.variables['K1_eta_real'][0,:,:]*runlength[runnum]
        mod_K1_eta_imag1 = mod_K1_eta_imag1 + harmT.variables['K1_eta_imag'][0,:,:]*runlength[runnum]

    totaldays = sum(runlength)
#    print 'total length of combined run = '+str(totaldays)+' days'
    mod_M2_eta_real = mod_M2_eta_real1/totaldays
    mod_M2_eta_imag = mod_M2_eta_imag1/totaldays
    mod_K1_eta_real = mod_K1_eta_real1/totaldays
    mod_K1_eta_imag = mod_K1_eta_imag1/totaldays
    mod_M2_amp = np.sqrt(mod_M2_eta_real**2+mod_M2_eta_imag**2)
    mod_M2_pha = -np.degrees(np.arctan2(mod_M2_eta_imag,mod_M2_eta_real))
    mod_K1_amp = np.sqrt(mod_K1_eta_real**2+mod_K1_eta_imag**2)
    mod_K1_pha = -np.degrees(np.arctan2(mod_K1_eta_imag,mod_K1_eta_real))

    return mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha

def get_current_harms(runname,loc):
    """
    Get harmonics of current at a specified lon, lat and depth

    :arg runname: name of the model run to process e.g. runname = '50s_15Sep-21Sep' (doesn't deal with multiple runs)
    :type runname: str

    :arg loc: location of results folder e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :returns: mod_M2_u_amp, mod_M2_u_pha, mod_M2_v_amp, mod_M2_v_pha
    """
    #u
    harmu = NC.Dataset(loc+runname+'/Tidal_Harmonics_U.nc','r')
    mod_M2_u_real = harmu.variables['M2_u_real'][0,:,:]
    mod_M2_u_imag = harmu.variables['M2_u_imag'][0,:,:]
     #convert to amplitude and phase
    mod_M2_u_amp = np.sqrt(mod_M2_u_real**2+mod_M2_u_imag**2)
    mod_M2_u_pha = -np.degrees(np.arctan2(mod_M2_u_imag,mod_M2_u_real))

    #v
    harmv = NC.Dataset(loc+runname+'/Tidal_Harmonics_V.nc','r')
    mod_M2_v_real = harmv.variables['M2_v_real'][0,:,:]
    mod_M2_v_imag = harmv.variables['M2_v_imag'][0,:,:]
     #convert to amplitude and phase
    mod_M2_v_amp = np.sqrt(mod_M2_v_real**2+mod_M2_v_imag**2)
    mod_M2_v_pha = -np.degrees(np.arctan2(mod_M2_v_imag,mod_M2_v_real))

    return mod_M2_u_amp, mod_M2_u_pha, mod_M2_v_amp, mod_M2_v_pha
    


def get_run_length(runname,loc):
    """ 
    Get the length of the run in days by reading in some data (in a rough way.... :S) from the namelist file

    :arg runname: name of the model run to process e.g. runname = '50s_15Sep-21Sep', or if you'd like the harmonics of more than one run to be combined into one picture, give a list of names e.g. '40d','41d50d','51d60d'
    :type runname: str

    :arg loc: location of results folder e.g. /ocean/dlatorne/MEOPAR/SalishSea/results
    :type loc: str

    :returns: length of run in days
    """
    resfile = loc+runname+'/namelist'
    with open(resfile) as f:
        content = f.readlines()
    
    for t in range(0,len(content)):
        if content[t][3:10] == 'rn_rdt ':
            timestep = int(content[t][19:21])
        if content[t][4:14] == 'nit000_han':
            start_time = int(content[t][17:23])
            end_time = int(content[t+1][17:23])

    #I am fudging this really. The positions in the 'namelist' file could easily change from run to run. 
    #Check this here: 
    if not 'timestep' in locals():
        import sys
        sys.exit('Uh oh! Looks like the "namelist" file has changed for run '+runname+'. You will need to open "namelist" in your results folder, and check the lines that have the timestep, start time and end time against the line matching being done in tidetools.get_run_length. Without this, I cant calculate the time period that the harmonics were calculated over :( Love python')

    run_length = (end_time-start_time)*timestep/60.0/60.0/24.0 #[days]
    
    return run_length


def ap2ep(Au, PHIu, Av, PHIv):
    """
    Convert amplitude and phase to ellipse parameters. Based on MATLAB script by Zhigang Xu, available at
    http://woodshole.er.usgs.gov/operations/sea-mat/tidal_ellipse-html/ap2ep.m
    """

    # Convert tidal amplitude and phase lag (ap-) parameters into tidal ellipse
    # (ep-) parameters. Please refer to ep2app for its inverse function.
    # 
    # Usage:
    #
    # [SEMA,  ECC, INC, PHA]=ap2ep(Au, PHIu, Av, PHIv)
    #
    # where:
    #
    #     Au, PHIu, Av, PHIv are the amplitudes and phase lags (in degrees) of 
    #     u- and v- tidal current components. They can be vectors or 
    #     matrices or multidimensional arrays.
    #     
    #     SEMA: Semi-major axes, or the maximum speed;
    #     ECC:  Eccentricity, the ratio of semi-minor axis over 
    #           the semi-major axis; its negative value indicates that the ellipse
    #           is traversed in clockwise direction.           
    #     INC:  Inclination, the angles (in degrees) between the semi-major 
    #           axes and u-axis.                        
    #     PHA:  Phase angles, the time (in angles and in degrees) when the 
    #           tidal currents reach their maximum speeds,  (i.e. 
    #           PHA=omega*tmax).
    #          
    #           These four ep-parameters will have the same dimensionality 
    #           (i.e., vectors, or matrices) as the input ap-parameters. 
    #
    #     w:    Optional. If it is requested, it will be output as matrices
    #           whose rows allow for plotting ellipses and whose columns are  
    #           for different ellipses corresponding columnwise to SEMA. For
    #           example, plot(real(w(1,:)), imag(w(1,:))) will let you see 
    #           the first ellipse. You may need to use squeeze function when
    #           w is a more than two dimensional array. See example.m. 
    #
    # Document:   tidal_ellipse.ps
    #   
    # Revisions: May  2002, by Zhigang Xu,  --- adopting Foreman's northern 
    # semi major axis convention.
    # 
    # For a given ellipse, its semi-major axis is undetermined by 180. If we borrow
    # Foreman's terminology to call a semi major axis whose direction lies in a range of 
    # [0, 180) as the northern semi-major axis and otherwise as a southern semi major 
    # axis, one has freedom to pick up either northern or southern one as the semi major 
    # axis without affecting anything else. Foreman (1977) resolves the ambiguity by 
    # always taking the northern one as the semi-major axis. This revision is made to 
    # adopt Foreman's convention. Note the definition of the phase, PHA, is still 
    # defined as the angle between the initial current vector, but when converted into 
    # the maximum current time, it may not give the time when the maximum current first 
    # happens; it may give the second time that the current reaches the maximum 
    # (obviously, the 1st and 2nd maximum current times are half tidal period apart)
    # depending on where the initial current vector happen to be and its rotating sense.
    #
    # Version 2, May 2002

    # Assume the input phase lags are in degrees and convert them in radians.
    PHIu = PHIu/180*pi
    PHIv = PHIv/180*pi

    # Make complex amplitudes for u and v
    import cmath
    i = cmath.sqrt(-1)
    u = Au*cmath.exp(-i*PHIu)
    v = Av*cmath.exp(-i*PHIv)

    # Calculate complex radius of anticlockwise and clockwise circles:
    wp = (u+i*v)/2      # for anticlockwise circles
    wm = ((u-i*v)/2).conjugate()  # for clockwise circles
    # and their amplitudes and angles
    Wp = abs(wp)
    Wm = abs(wm)
    THETAp = cmath.phase(wp)
    THETAm = cmath.phase(wm)
   
    # calculate ep-parameters (ellipse parameters)
    SEMA = Wp+Wm             # Semi  Major Axis, or maximum speed
    SEMI = Wp-Wm               # Semin Minor Axis, or minimum speed
    ECC = SEMI/SEMA          # Eccentricity

    PHA = (THETAm-THETAp)/2   # Phase angle, the time (in angle) when the velocity reaches the maximum
    INC = (THETAm+THETAp)/2   # Inclination, the angle between the semi major axis and x-axis (or u-axis).

    # convert to degrees for output
    PHA = PHA/pi*180
    INC = INC/pi*180       
    THETAp = THETAp/pi*180
    THETAm = THETAm/pi*180
    
    #map the resultant angles to the range of [0, 360].
    #PHA=mod(PHA+360, 360)
    PHA=(PHA+360)%360
    #INC=mod(INC+360, 360)
    INC=(INC+360)% 360

    #Mar. 2, 2002 Revision by Zhigang Xu    (REVISION_1)
    #Change the southern major axes to northern major axes to conform the tidal 
    #analysis convention  (cf. Foreman, 1977, p. 13, Manual For Tidal Currents 
    #Analysis Prediction, available in www.ios.bc.ca/ios/osap/people/foreman.htm) 
    k = float(INC)/180
    INC = INC-k*180
    PHA = PHA+k*180
    PHA = PHA%360

    return SEMA,  ECC, INC, PHA

    #Authorship Copyright:
    #
    #    The author retains the copyright of this program, while  you are welcome 
    # to use and distribute it as long as you credit the author properly and respect
    # the program name itself. Particularly, you are expected to retain the original 
    # author's name in this original version or any of its modified version that 
    # you might make. You are also expected not to essentially change the name of 
    # the programs except for adding possible extension for your own version you 
    # might create, e.g. ap2ep_xx is acceptable.  Any suggestions are welcome and 
    # enjoy my program(s)!
    #
    #
    #Author Info:
    #_______________________________________________________________________
    #  Zhigang Xu, Ph.D.                            
    #  (pronounced as Tsi Gahng Hsu)
    #  Research Scientist
    #  Coastal Circulation                   
    #  Bedford Institute of Oceanography     
    #  1 Challenge Dr.
    #  P.O. Box 1006                    Phone  (902) 426-2307 (o)       
    #  Dartmouth, Nova Scotia           Fax    (902) 426-7827            
    #  CANADA B2Y 4A2                   email xuz@dfo-mpo.gc.ca    
    #_______________________________________________________________________
    #
    # Release Date: Nov. 2000, Revised on May. 2002 to adopt Foreman's northern semi 
    # major axis convention.




































