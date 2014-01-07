#A collection of tools for dealing with tidal results for the Salish Sea Model

import netCDF4 as NC
import numpy as np
import datetime
import requests
import pandas as pd
import pytz
from math import radians, sin, cos, asin, sqrt
import matplotlib.pyplot as plt

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
    print('Results saved here: '+outfile)

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

def plot_amp_phase_maps(runname):
    """
    Plot the amplitude and phase results for a model run
    e.g. plot_amp_phase_maps('50s_15Sep-21Sep')
    
    :arg runname: name of the model run to process e.g. '50s_15Sep-21Sep'
    :type runname: str

    :returns: plots the amplitude and phase 
    """
    if runname == 'concepts110': 
        mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_concepts110()
        bathy, X, Y = get_subdomain_bathy_data()        
    elif runname == 'jpp72':
        mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_jpp72()
        bathy, X, Y = get_subdomain_bathy_data()        
    elif runname == '40d':
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data_40d(runname)
        bathy, X, Y = get_SS2_bathy_data()
    else:            
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data(runname)
        bathy, X, Y = get_SS_bathy_data()
    plot_amp_map(X,Y,mod_M2_amp,runname,True,'M2')
    plot_pha_map(X,Y,mod_M2_pha,runname,True,'M2')
    if runname != 'concepts110' and runname != 'jpp72':
        plot_amp_map(X,Y,mod_K1_amp,runname,True,'K1')
        plot_pha_map(X,Y,mod_K1_pha,runname,True,'K1')

def get_netcdf_amp_phase_data_40d(runname):
    """
    Calculate amplitude and phase from the results of the 40 day run of the Salish Sea model
    e.g. mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data('50s_15Sep-21Sep')

    :arg runname: name of the model run to process e.g. '50s_15Sep-21Sep'
    :type runname: str

    :returns: model M2 amplitude, model K1 amplitude, model M2 phase, model K1 phase
    """
    harmT = NC.Dataset('/ocean/dlatorne/MEOPAR/SalishSea/results/'+runname+'/Tidal_Harmonics_eta.nc','r')
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


def get_netcdf_amp_phase_data(runname):
    """
    Calculate amplitude and phase from the results of a particular run of the Salish Sea model
    e.g. mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data('50s_15Sep-21Sep')

    :arg runname: name of the model run to process e.g. '50s_15Sep-21Sep'
    :type runname: str

    :returns: model M2 amplitude, model K1 amplitude, model M2 phase, model K1 phase
    """
    harmT = NC.Dataset('/data/dlatorne/MEOPAR/SalishSea/results/'+runname+'/Tidal_Harmonics_eta.nc','r')
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

def get_netcdf_amp_phase_data_jpp72():
    """
    Calculate amplitude and phase from the results of the JPP72 model
    e.g. mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_jpp72()
    
    :returns: model M2 amplitude, model M2 phase
    """
    harmT = NC.Dataset('/ocean/klesouef/meopar/SS-run-sets/JPP/72h_3d_iomput/JPP_1d_20020102_20020104_grid_T.nc','r')
    #Get amplitude and phase
    mod_M2_x_elev = harmT.variables['M2_x_elev'][0,:,:] #Cj
    mod_M2_y_elev = harmT.variables['M2_y_elev'][0,:,:] #Sj
    #see section 11.6 of NEMO manual (p223/367)
    mod_M2_amp = np.sqrt(mod_M2_x_elev**2+mod_M2_y_elev**2)
    mod_M2_pha = -np.degrees(np.arctan2(mod_M2_y_elev,mod_M2_x_elev))
    return mod_M2_amp, mod_M2_pha

def get_netcdf_amp_phase_data_concepts110():
    """
    Calculate amplitude and phase from the results of the CONCEPTS110 model
    e.g. mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_concepts110()
    
    :returns: model M2 amplitude, model M2 phase
    """
    harmT = NC.Dataset('/ocean/klesouef/meopar/tools/NetCDF_Plot/WC3_Harmonics_gridT_TIDE2D.nc','r')
    mod_M2_amp = harmT.variables['M2_amp'][0,:,:]
    mod_M2_pha = harmT.variables['M2_pha'][0,:,:]
    return mod_M2_amp, mod_M2_pha

def get_SS_bathy_data():
    """
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

def plot_amp_map(X,Y,amp,titstr,savestr,constflag):
    """
    Plot the amplitude of one constituent throughout the whole domain
    e.g. plot_amp_map(X,Y,mod_M2_amp,'50s_12Sep-19Sep',savestr,'M2')

    :arg X: specified model longitude
    :type X: numpy array

    :arg Y: specified model latitude
    :type Y: numpy array

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
    v = np.arange(0, 1.30, 0.1)
    plt.figure(figsize=(9,9))    
    CS = plt.contourf(X,Y,amp,v,cmap='cool',aspect=(1 / np.cos(np.median(X) * np.pi / 180)))
    plt.colorbar(CS)
    plt.xlabel('longitude (deg)')
    plt.ylabel('latitude (deg)')
    plt.title(constflag+' amplitude (m) for '+titstr)
    if savestr:
        plt.savefig('/ocean/klesouef/meopar/tools/compare_tides/'+constflag+'_amp_'+titstr+'.pdf')

def plot_pha_map(X,Y,pha,titstr,savestr,constflag):
    """
    Plot the phase of one constituent throughout the whole domain
    e.g. plot_pha_map(X,Y,mod_M2_pha,titstr,savestr,'M2')

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
    #plot modelled M2 phase 
    v = np.arange(-180, 202.5,22.5)
    plt.figure(figsize=(9,9))    
    CS = plt.contourf(X,Y,pha,v,cmap='gist_rainbow',aspect=(1 / np.cos(np.median(X) * np.pi / 180)))
    plt.colorbar(CS)
    plt.xlabel('longitude (deg)')
    plt.ylabel('latitude (deg)')
    plt.title(constflag+' phase (deg) for '+titstr)
    limits = plt.axis()
    if savestr:
        plt.savefig('/ocean/klesouef/meopar/tools/compare_tides/'+constflag+'_pha_'+titstr+'.pdf')

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
    plt.savefig('/ocean/klesouef/meopar/tools/compare_tides/'+constflag+'_scatter_comps_'+runname+'.pdf')

def plot_diffs_on_domain(D,meas_wl_harm,calcmethod,constflag,runname):
    """
    Plot differences as circles of varying radius on a map of the model domain
    e.g. plot_diffs_on_domain(D_F95_all_M2,meas_wl_harm,'F95','M2',runname)

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
    bathy, X, Y = get_SS_bathy_data()
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
        plt.title(constflag+' differences (Foreman et al) for '+runname)
        plt.savefig('/ocean/klesouef/meopar/tools/compare_tides/'+constflag+'_diffs_F95_'+runname+'.pdf')
    if calcmethod == 'M04':
        plt.scatter(np.array(meas_wl_harm.Lon)*-1, meas_wl_harm.Lat, c='g', s=area, marker='o')
        plt.scatter(-124.5,47.9,c='g',s=(legendD*scalefac), marker='o')
        plt.title(constflag+' differences (Masson & Cummins) for '+runname)
        plt.savefig('/ocean/klesouef/meopar/tools/compare_tides/'+constflag+'_diffs_M04_'+runname+'.pdf')
    
def calc_diffs_meas_mod(runname):
    """
    Calculate differences between measured and modelled water level
    e.g. meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all, D_M04_M2_all,Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all = calc_diffs_meas_mod('50s_13Sep-20Sep')

    :arg runname: name of model run 
    :type runname: str

    :returns: meas_wl_harm, Am_M2_all, Ao_M2_all, gm_M2_all, go_M2_all, D_F95_M2_all, D_M04_M2_all,Am_K1_all, Ao_K1_all, gm_K1_all, go_K1_all, D_F95_K1_all, D_M04_K1_all
    """
    #read in the measured data from Foreman et al (1995)
    import pandas as pd
    meas_wl_harm = pd.read_csv('/ocean/klesouef/meopar/tools/compare_tides/obs_tidal_wlev_const_Foreman95.csv')
    meas_wl_harm = meas_wl_harm.rename(columns={'M2 amp': 'M2_amp', 'M2 phase (deg UT)': 'M2_pha', 'K1 amp': 'K1_amp', 'K1 phase (deg UT)': 'K1_pha'})

    import angles
    #make an appropriately named csv file for results
    outfile = '/ocean/klesouef/meopar/tools/compare_tides/wlev_harm_diffs_'+runname+'.csv'
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

    #get bathy and harmonics data
    if runname == 'concepts110':
        mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_concepts110()
        bathy, X, Y = get_subdomain_bathy_data()
    elif runname == 'jpp72':
        mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_jpp72()
        bathy, X, Y = get_subdomain_bathy_data()
    elif runname == '40d':
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data_40d(runname)
        bathy, X, Y = get_SS2_bathy_data()
    else:
        mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data(runname)
        bathy, X, Y = get_SS_bathy_data()

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

    print('Results saved here: '+outfile)
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
    :type: numpy array

    :arg Y: specified model latitude
    :type: numpy array

    :arg bathy: model bathymetry
    :type: numpy array

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
    





