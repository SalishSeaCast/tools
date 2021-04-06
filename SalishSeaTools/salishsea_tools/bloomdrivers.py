import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
import netCDF4 as nc
import datetime as dt
from salishsea_tools import evaltools as et, places, viz_tools, visualisations, geo_tools
import xarray as xr
import pandas as pd
import pickle
import os
import gsw

# Extracting winds from the correct path
def getWindVarsYear(year,loc):
    ''' Given a year, returns the correct directory and nam_fmt for wind forcing as well as the
        location of S3 on the corresponding grid.
            Parameters:
                    year: a year value in integer form 
                    loc: the location name as a string. Eg. loc='S3'
            Returns:
                    jW: y-coordinate for the location
                    iW: x-coordinate for the location
                opsdir: path to directory where wind forcing file is stored
               nam_fmt: naming convention of the appropriate files
    '''
    if year>2014:
        opsdir='/results/forcing/atmospheric/GEM2.5/operational/'
        nam_fmt='ops'
        jW,iW=places.PLACES[loc]['GEM2.5 grid ji']
    else:
        opsdir='/data/eolson/results/MEOPAR/GEMLAM/'
        nam_fmt='gemlam'
        with xr.open_dataset('/results/forcing/atmospheric/GEM2.5/gemlam/gemlam_y2012m03d01.nc') as gridrefWind:
            # always use a post-2011 file here to identify station grid location
            lon,lat=places.PLACES[loc]['lon lat']
            jW,iW=geo_tools.find_closest_model_point(lon,lat,
                    gridrefWind.variables['nav_lon'][:,:]-360,gridrefWind.variables['nav_lat'][:,:],
                    grid='GEM2.5')
                    # the -360 is needed because longitudes in this case are reported in postive degrees East

    return jW,iW,opsdir,nam_fmt

# Metric 1:
def metric1_bloomtime(phyto_alld,no3_alld,bio_time):
    ''' Given datetime array and two 2D arrays of phytoplankton and nitrate concentrations, over time
        and depth, returns a datetime value of the spring phytoplankton bloom date according to the 
        following definition (now called 'metric 1'):
            
            'The spring bloom date is the peak phytoplankton concentration  (averaged from the surface to 
            3 m depth)  within four days of the average upper 3 m nitrate concentration going below 0.5 uM 
            (the half-saturation concentration) for two consecutive days'
            EDIT: 0.5 uM was changed to 2.0 uM to yield more accurate results
            
            Parameters:
                    phyto_alld: 2D array of phytoplankton concentrations (in uM N) over all depths and time 
                                range of 'bio_time'
                      no3_alld: 2D array of nitrate concentrations (in uM N) over all depths and time 
                                range of 'bio_time'
                      bio_time: 1D datetime array of the same time frame as phyto_alld and no3_alld
            Returns:
                    bloomtime1: the spring bloom date as a single datetime value
        
    '''
    # a) get avg phytplankton in upper 3m
    phyto_alld_df=pd.DataFrame(phyto_alld)
    upper_3m_phyto=pd.DataFrame(phyto_alld_df[[0,1,2,3]].mean(axis=1))
    upper_3m_phyto.columns=['upper_3m_phyto']
    #upper_3m_phyto

    # b) get average no3 in upper 3m
    no3_alld_df=pd.DataFrame(no3_alld)
    upper_3m_no3=pd.DataFrame(no3_alld_df[[0,1,2,3]].mean(axis=1))
    upper_3m_no3.columns=['upper_3m_no3']
    #upper_3m_no3

    # make bio_time into a dataframe
    bio_time_df=pd.DataFrame(bio_time)
    bio_time_df.columns=['bio_time']
    metric1_df=pd.concat((bio_time_df,upper_3m_phyto,upper_3m_no3), axis=1)
    
    # c)  Find first location where nitrate crosses below 0.5 micromolar and 
    #     stays there for 2 days 
    # NOTE: changed the value to 2 micromolar
    for i, row in metric1_df.iterrows():
        try:
            if metric1_df['upper_3m_no3'].iloc[i]<2 and metric1_df['upper_3m_no3'].iloc[i+1]<2:
                location1=i
                break
        except IndexError:
            location1=np.nan
            print('bloom not found')

    # d) Find date with maximum phytoplankton concentration within four days (say 9 day window) of date in c)
    bloomrange=metric1_df[location1-4:location1+5]
    bloomtime1=bloomrange.loc[bloomrange.upper_3m_phyto.idxmax(), 'bio_time']

    return bloomtime1


# Metric 2: 
def metric2_bloomtime(sphyto,sno3,bio_time):
    ''' Given datetime array and two 1D arrays of surface phytplankton and nitrate concentrations 
        over time, returns a datetime value of the spring phytoplankton bloom date according to the 
        following definition (now called 'metric 2'):
            
            'The first peak in which chlorophyll concentrations are above 5 ug/L for more than two days'
            
            Parameters:
                    sphyto: 1D array of phytoplankton concentrations (in uM N) over time 
                                range of 'bio_time'
                      sno3: 1D array of nitrate concentrations (in uM N) over time 
                                range of 'bio_time'
                  bio_time: 1D datetime array of the same time frame as sphyto and sno3
            Returns:
                    bloomtime2: the spring bloom date as a single datetime value
        
    '''
    
    df = pd.DataFrame({'bio_time':bio_time, 'sphyto':sphyto, 'sno3':sno3})

    # to find all the peaks:
    df['phytopeaks'] = df.sphyto[(df.sphyto.shift(1) < df.sphyto) & (df.sphyto.shift(-1) < df.sphyto)]
    
    # need to covert the value of interest from ug/L to uM N (conversion factor: 1.8 ug Chl per umol N)
    chlvalue=5/1.8

    # extract the bloom time date   
    for i, row in df.iterrows():
        try:
            if df['sphyto'].iloc[i-1]>chlvalue and df['sphyto'].iloc[i-2]>chlvalue and pd.notna(df['phytopeaks'].iloc[i]):
                bloomtime2=df.bio_time[i]
                break
            elif df['sphyto'].iloc[i+1]>chlvalue and df['sphyto'].iloc[i+2]>chlvalue and pd.notna(df['phytopeaks'].iloc[i]):
                bloomtime2=df.bio_time[i]
                break
        except IndexError:
            bloomtime2=np.nan
            print('bloom not found')
    return bloomtime2


# Metric 3: 
def metric3_bloomtime(sphyto,sno3,bio_time):
    ''' Given datetime array and two 1D arrays of surface phytplankton and nitrate concentrations 
        over time, returns a datetime value of the spring phytoplankton bloom date according to the 
        following definition (now called 'metric 3'):
            
            'The median + 5% of the annual Chl concentration is deemed “threshold value” for each year. 
            For a given year, bloom initiation is determined to be the week that first reaches the 
            threshold value (by looking at weekly averages) as long as one of the two following weeks 
            was >70% of the threshold value'
            
            Parameters:
                    sphyto: 1D array of phytoplankton concentrations (in uM N) over time 
                                range of 'bio_time'
                      sno3: 1D array of nitrate concentrations (in uM N) over time 
                                range of 'bio_time'
                  bio_time: 1D datetime array of the same time frame as sphyto and sno3
            Returns:
                    bloomtime3: the spring bloom date as a single datetime value
        
    '''
    # 1) determine threshold value    
    df = pd.DataFrame({'bio_time':bio_time, 'sphyto':sphyto, 'sno3':sno3})   
    
    # a) find median chl value of that year, add 5% (this is only feb-june, should we do the whole year?)
    threshold=df['sphyto'].median()*1.05
    # b) secondthresh = find 70% of threshold value
    secondthresh=threshold*0.7    

    # 2) Take the average of each week and make a dataframe with start date of week and weekly average
    weeklychl = pd.DataFrame(df.resample('W', on='bio_time').sphyto.mean())
    weeklychl.reset_index(inplace=True)

    # 3) Loop through the weeks and find the first week that reaches the threshold. 
        # Is one of the two week values after this week > secondthresh? 

    for i, row in weeklychl.iterrows():
        try:
            if weeklychl['sphyto'].iloc[i]>threshold and weeklychl['sphyto'].iloc[i+1]>secondthresh:
                bloomtime3=weeklychl.bio_time[i]
                break
            elif weeklychl['sphyto'].iloc[i]>threshold and weeklychl['sphyto'].iloc[i+2]>secondthresh:
                bloomtime3=weeklychl.bio_time[i]
                break
        except IndexError:
            bloomtime2=np.nan
            print('bloom not found')

    return bloomtime3

# Surface monthly average calculation given 2D array with depth and time:
def D2_3monthly_avg(time,x):
     
    ''' Given datetime array of 3 months and a 2D array of variable x, over time
        and depth, returns an array containing the 3 monthly averages of the 
        surface values of variable x
           
           Parameters:
                    time: datetime array of each day starting from the 1st day 
                          of the first month, ending on the last day of the third month
                       x: 2-dimensional numpy array containing daily averages of the 
                           same length and time frame as 'time', and depth profile
            Returns:
                    jan_x, feb_x, mar_x: monthly averages of variable x at surface
    '''
    
    depthx=pd.DataFrame(x)
    surfacex=np.array(depthx[[0]]).flatten()
    df=pd.DataFrame({'time':time, 'x':surfacex})
    monthlyx=pd.DataFrame(df.resample('M', on='time').x.mean())
    monthlyx.reset_index(inplace=True)
    jan_x=monthlyx.iloc[0]['x']
    feb_x=monthlyx.iloc[1]['x']
    mar_x=monthlyx.iloc[2]['x']
    return jan_x, feb_x, mar_x



# mid depth nitrate (30-90m):
def D1_3monthly_avg(time,x):
   
    ''' Given datetime array of 3 months and a 1D array of variable x with time,
        returns an array containing the 3 monthly averages of the variable x
           
           Parameters:
                    time: datetime array of each day starting from the 1st day 
                          of the first month, ending on the last day of the third month
                       x: 1-dimensional numpy array containing daily averages of the 
                           same length and time frame as 'time'
            Returns:
                    jan_x, feb_x, mar_x: monthly averages of variable x
    '''
    
    df=pd.DataFrame({'time':time, 'x':x})
    monthlyx=pd.DataFrame(df.resample('M', on='time').x.mean())
    monthlyx.reset_index(inplace=True)
    jan_x=monthlyx.iloc[0]['x']
    feb_x=monthlyx.iloc[1]['x']
    mar_x=monthlyx.iloc[2]['x']
    return jan_x, feb_x, mar_x

# Monthly average calculation given 1D array and non-datetime :
def D1_3monthly_avg2(time,x):
    
    ''' Given non-datetime array of 3 months and a 1D array of variable x with time,
        returns an array containing the 3 monthly averages of the variable x
           
           Parameters:
                    time: non-datetime array of each day starting from the 1st day 
                          of the first month, ending on the last day of the third month
                       x: 1-dimensional numpy array containing daily averages of the 
                          same length and time frame as 'time'
            Returns:
                    jan_x, feb_x, mar_x: monthly averages of variable x
    '''
    
    
    df=pd.DataFrame({'time':time, 'x':x})
    df["time"] = pd.to_datetime(df["time"])
    monthlyx=pd.DataFrame(df.resample('M',on='time').x.mean())
    monthlyx.reset_index(inplace=True)
    jan_x=monthlyx.iloc[0]['x']
    feb_x=monthlyx.iloc[1]['x']
    mar_x=monthlyx.iloc[2]['x']
    return jan_x, feb_x, mar_x

def halo_de(ncname,ts_x,ts_y):
    
    ''' Given a path to a SalishSeaCast netcdf file and an x, y pair, 
        returns halocline depth, where halocline depth is defined a midway between 
        two cells that have the largest salinity gradient
        ie max abs((sal1-sal2)/(depth1-depth2))

            Parameters:
                    ncname (str): path to a netcdf file containing 
                    a valid salinity variable (vosaline)
                    ts_x (int): x-coordinate at which halocline is calculated
                    tx_y (int): y-coordinate at which halocline is calculated
            Returns:
                    halocline_depth: depth in meters of maximum salinity gradient
    '''
    
     # o
        
    halocline = 0
    grid = nc.Dataset('/data/vdo/MEOPAR/NEMO-forcing/grid/mesh_mask201702.nc')
    nemo = nc.Dataset(ncname)
    
    #get the land mask
    col_mask = grid['tmask'][0,:,ts_y,ts_x] 
    
    #get the depths of the watercolumn and filter only cells that have water
    col_depths = grid['gdept_0'][0,:,ts_y,ts_x]
    col_depths = col_depths[col_mask==1] 

### if there is no water, no halocline
    if (len(col_depths) == 0):
        halocline = np.nan
    
    else: 
        #get the salinity of the point, again filtering for where water exists
        col_sal = nemo['vosaline'][0,:,ts_y,ts_x]
        col_sal = col_sal[col_mask==1]

        #get the gradient in salinity
        sal_grad = np.zeros_like(col_sal)

        for i in range(0, (len(col_sal)-1)):
            sal_grad[i] = np.abs((col_sal[i]-col_sal[i+1])/(col_depths[i]-col_depths[i+1]))

        #print(sal_grad)

        loc_max = np.where(sal_grad == np.nanmax(sal_grad))
        loc_max = (loc_max[0][0])

        #halocline is halfway between the two cells
        halocline = col_depths[loc_max] + 0.5*(col_depths[loc_max+1]-col_depths[loc_max])

    
    return halocline


# regression line and r2 value for plots
def reg_r2(driver,bloomdate):
    
    '''Given two arrays of the same length, returns linear regression best 
       fit line and r-squared value.
        
            Parameters:
                    driver: 1D array of the independent (predictor) variable
                 bloomdate: 1D array of the dependent (response) variable, the 
                            same length as "driver"     
            Returns:
                    y: y-coordinates of best fit line
                   r2: r-squared value of regression fit
                    m: slope of line
                    c: y-intercepth of line
    '''
    
    A = np.vstack([driver, np.ones(len(driver))]).T
    m, c = np.linalg.lstsq(A, bloomdate,rcond=None)[0]
    m=round(m,3)
    c=round(c,2)
    y = m*driver + c
    model, resid = np.linalg.lstsq(A, bloomdate,rcond=None)[:2]
    r2 = 1 - resid / (len(bloomdate) * np.var(bloomdate))
    return y, r2, m, c

# depth of turbocline
def turbo(eddy,time,depth):
    '''Given a datetime array of 3 months, a depth array, and 2D array of eddy 
        diffusivity over time and depth, returns the average turbocline depth 
        for each of the three months. Turbocline depth is defined here as the depth 
        before the depth at which eddy diffusivity reaches a value of 0.001 m^2/s
        
            Parameters: 
                    eddy: 2-dimensional numpy array containing daily averaged eddy diffusivity
                            of the same time frame as 'time', and over depth 
                    time: datetime array of each day starting from the 1st day 
                          of the first month, ending on the last day of the third month
                   depth: depth array from grid_T 
            Returns: 
                 jan_turbo: average turbocline depth of the first month (single value)
                 feb_turbo: average turbocline depth of the second month (single value)
                 mar_turbo: average turbocline depth of the third month (single value)
    '''
    turbo=list()
    for day in eddy: 
        dfed=pd.DataFrame({'depth':depth[:-1], 'eddy':day[1:]}) 
        dfed=dfed.iloc[1:] # dropping surface values
        dfed[:21] #keep top 21 (25m depth)
        for i, row in dfed.iterrows():
            try:
                if row['eddy']<0.001:
                    turbo.append(dfed.at[i,'depth'])
                    break
            except IndexError:
                turbo.append(np.nan)
                print('turbocline depth not found')
    dfturbo=pd.DataFrame({'time':time, 'turbo':turbo})
    monthlyturbo=pd.DataFrame(dfturbo.resample('M', on='time').turbo.mean())
    monthlyturbo.reset_index(inplace=True)
    jan_turbo=monthlyturbo.iloc[0]['turbo']
    feb_turbo=monthlyturbo.iloc[1]['turbo']
    mar_turbo=monthlyturbo.iloc[2]['turbo']
    return jan_turbo, feb_turbo, mar_turbo

def density_diff(sal,temp,time):
    
    '''Given a datetime array of 3 months, a 2D array of salinity over time and depth, 
       a 2D array of temperature over time and depth, returns the difference in density
       from the surface to a series of depths averaged over each month for 3 months
        
            Parameters: 
                    sal: 2-dimensional numpy array containing daily averaged salinity
                         of the same time frame as 'time', and over depth 
                   temp: 2-dimensional numpy array containing daily averaged temperature
                         of the same time frame as 'time', and over depth 
                    time: datetime array of each day starting from the 1st day 
                          of the first month, ending on the last day of the third month
                   
            Returns: 
                 density_diffs: a dictionary containing a description as a string and the
                                density difference from the surface to some depth (the depth
                                range is 5m to 30m, in increments of 5m)
                                Eg. 'Jan 5m': somevalue
                                    describes that the numerical value on the right (somevalue) 
                                    is the density difference from the surface to 5m depth, averaged
                                    over the first month
    '''
    p=0
    depthrange={5:5,10:10,15:15,19:20,20:25,21:30}
    density_diffs=dict()
    for ind,depth in depthrange.items():
        dsal=pd.DataFrame(sal)
        dtemp=pd.DataFrame(temp)
      
        surfacedens=gsw.rho(dsal.iloc[:,0],dtemp.iloc[:,0],p)  # get the surface density
        idens=gsw.rho(dsal.iloc[:,ind],dtemp.iloc[:,ind],p)  # get the density at that depth
        densdiff=idens-surfacedens                               # get the daily density difference
        
        df=pd.DataFrame({'time':time, 'densdiff':densdiff})  
        monthlydiff=pd.DataFrame(df.resample('M', on='time').densdiff.mean()) # average over months
        monthlydiff.reset_index(inplace=True)
        density_diffs[f'Jan {depth}m']=monthlydiff.iloc[0]['densdiff']
        density_diffs[f'Feb {depth}m']=monthlydiff.iloc[1]['densdiff']
        density_diffs[f'Mar {depth}m']=monthlydiff.iloc[2]['densdiff']
    return density_diffs


def avg_eddy(eddy,time,ij,ii):
    
    '''Given a 2D array of eddy diffusivity over time and depth, a datetime array of 3 months,
        the x and y coordinates of the location of interest, returns the average eddy diffusivity 
        over the upper 15 and 30, each averaged over every month
        
            Parameters: 
                    eddy: 2-dimensional numpy array containing daily averaged eddy diffusivity
                            of the same time frame as 'time', and over depth 
                    time: datetime array of each day starting from the 1st day 
                          of the first month, ending on the last day of the third month
                      ij: y-coordinate for location 
                      ii: x-coordinate for location
            Returns: 
                 jan_eddyk1: average eddy diffusivity over upper 15m, averaged over the first month
                 feb_eddyk1: average eddy diffusivity over upper 15m, averaged over the second month
                 mar_eddyk1: average eddy diffusivity over upper 15m, averaged over the third month
                 jan_eddyk2: average eddy diffusivity over upper 30m, averaged over the first month
                 feb_eddyk2: average eddy diffusivity over upper 30m, averaged over the second month
                 mar_eddyk2: average eddy diffusivity over upper 30m, averaged over the third month
    '''
    
    k1=15 # 15m depth is index 15 (actual value is 15.096255)
    k2=22 # 30m depth is index 22 (actual value is 31.101034)
    with xr.open_dataset('/data/vdo/MEOPAR/NEMO-forcing/grid/mesh_mask201702.nc') as mesh:
            tmask=np.array(mesh.tmask[0,:,ij,ii])
            e3t_0=np.array(mesh.e3t_0[0,:,ij,ii])
            e3t_k1=np.array(mesh.e3t_0[:,k1,ij,ii])
            e3t_k2=np.array(mesh.e3t_0[:,k1,ij,ii])
    # vertical sum of microzo in mmol/m3 * vertical grid thickness in m:
    inteddy=list()
    avgeddyk1=list()
    avgeddyk2=list()
    for dailyeddy in eddy:
        eddy_tgrid=(dailyeddy[1:]+dailyeddy[:-1])
        eddy_e3t=eddy_tgrid*e3t_0[:-1]
        avgeddyk1.append(np.sum(eddy_e3t[:k1]*tmask[:k1])/np.sum(e3t_0[:k1]))
        avgeddyk2.append(np.sum(eddy_e3t[:k2]*tmask[:k2])/np.sum(e3t_0[:k2]))

    df=pd.DataFrame({'time':time, 'eddyk1':avgeddyk1,'eddyk2':avgeddyk2})
    monthlyeddyk1=pd.DataFrame(df.resample('M', on='time').eddyk1.mean())
    monthlyeddyk2=pd.DataFrame(df.resample('M', on='time').eddyk2.mean())
    monthlyeddyk1.reset_index(inplace=True)
    monthlyeddyk2.reset_index(inplace=True)
    jan_eddyk1=monthlyeddyk1.iloc[0]['eddyk1']
    feb_eddyk1=monthlyeddyk1.iloc[1]['eddyk1']
    mar_eddyk1=monthlyeddyk1.iloc[2]['eddyk1']
    jan_eddyk2=monthlyeddyk2.iloc[0]['eddyk2']
    feb_eddyk2=monthlyeddyk2.iloc[1]['eddyk2']
    mar_eddyk2=monthlyeddyk2.iloc[2]['eddyk2']
    return jan_eddyk1, feb_eddyk1, mar_eddyk1,jan_eddyk2,feb_eddyk2,mar_eddyk2