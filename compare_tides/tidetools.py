#A collection of tools for dealing with tidal results for the Salish Sea Model

import netCDF4 as NC
import numpy as np

#define a function to plot the amplitude and phase results for the required run
def plot_amp_phase_maps(runname):
	if runname == 'concepts110': 
		mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_concepts110()
		bathy, X, Y = get_subdomain_bathy_data()		
	elif runname == 'jpp72':
		mod_M2_amp, mod_M2_pha = get_netcdf_amp_phase_data_jpp72()
		bathy, X, Y = get_subdomain_bathy_data()		
	else:			
		mod_M2_amp, mod_K1_amp, mod_M2_pha, mod_K1_pha = get_netcdf_amp_phase_data(runname)
		bathy, X, Y = get_SS_bathy_data()
	plot_amp_map(X,Y,mod_M2_amp,runname,True,'M2')
	plot_pha_map(X,Y,mod_M2_pha,runname,True,'M2')
	if runname != 'concepts110' and runname != 'jpp72':
		plot_amp_map(X,Y,mod_K1_amp,runname,True,'K1')
		plot_pha_map(X,Y,mod_K1_pha,runname,True,'K1')

#define a function to calculate amplitude and phase from the results
def get_netcdf_amp_phase_data(runname):
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

#define a function to calculate amplitude and phase from the results for jpp72
def get_netcdf_amp_phase_data_jpp72():
	harmT = NC.Dataset('/ocean/klesouef/meopar/SS-run-sets/JPP/72h_3d_iomput/JPP_1d_20020102_20020104_grid_T.nc','r')
	#Get amplitude and phase
	mod_M2_x_elev = harmT.variables['M2_x_elev'][0,:,:]    #Cj
	mod_M2_y_elev = harmT.variables['M2_y_elev'][0,:,:]    #Sj
	#see section 11.6 of NEMO manual (p223/367)
	mod_M2_amp = np.sqrt(mod_M2_x_elev**2+mod_M2_y_elev**2)
	mod_M2_pha = -np.degrees(np.arctan2(mod_M2_y_elev,mod_M2_x_elev))
	return mod_M2_amp, mod_M2_pha

#define a function to calculate amplitude and phase from the results for concepts110
def get_netcdf_amp_phase_data_concepts110():
	harmT = NC.Dataset('/ocean/klesouef/meopar/tools/NetCDF_Plot/WC3_Harmonics_gridT_TIDE2D.nc','r')
	mod_M2_amp = harmT.variables['M2_amp'][0,:,:]
	mod_M2_pha = harmT.variables['M2_pha'][0,:,:]
	return mod_M2_amp, mod_M2_pha

#define a function to get the Salish Sea bathymetry and grid data
def get_SS_bathy_data():
   	grid = NC.Dataset('/ocean/klesouef/meopar/nemo-forcing/grid/bathy_meter_SalishSea.nc','r')
	bathy = grid.variables['Bathymetry'][:,:]
	X = grid.variables['nav_lon'][:,:]
	Y = grid.variables['nav_lat'][:,:]
	return bathy, X, Y

#define a function to get the Salish Sea bathymetry and grid data
def get_subdomain_bathy_data():
	grid = NC.Dataset('/ocean/klesouef/meopar/nemo-forcing/grid/SubDom_bathy_meter_NOBCchancomp.nc','r')
	bathy = grid.variables['Bathymetry'][:,:]
	X = grid.variables['nav_lon'][:,:]
	Y = grid.variables['nav_lat'][:,:]
	return bathy, X, Y

#define a function to find the closest model grid point to the measured data
def find_closest_model_point(lon,lat,X,Y,bathy):
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

#define a function to plot the amplitude of one constituent throughout the domain
#e.g. tidetools.plot_amp_map(X,Y,mod_M2_amp,titstr,savestr,'M2')
def plot_amp_map(X,Y,amp,titstr,savestr,constflag):
	import matplotlib.pyplot as plt
	import numpy
	#make 0 values NaNs so they plot blank
	amp = numpy.ma.masked_equal(amp,0)
	#range of amplitudes to plot	
	v = np.arange(0, 1.30, 0.1)
	plt.figure(figsize=(9,9))	
    	CS = plt.contourf(X,Y,amp,v,cmap='cool',aspect=(1 / numpy.cos(numpy.median(X) * numpy.pi / 180)))
	plt.colorbar(CS)
	plt.xlabel('longitude (deg)')
	plt.ylabel('latitude (deg)')
	plt.title(constflag+' amplitude (m) for '+titstr)
	if savestr:
	    plt.savefig('/ocean/klesouef/meopar/tools/compare_tides/'+constflag+'_amp_'+titstr+'.pdf')

#define a function to plot the phase of one constituent throughout the domain
# eg. tidetools.plot_pha_map(X,Y,mod_M2_amp,titstr,savestr,'M2')
def plot_pha_map(X,Y,pha,titstr,savestr,constflag):
	import matplotlib.pyplot as plt
	import numpy
	#make 0 values NaNs so they plot blank
	pha = numpy.ma.masked_equal(pha,0)
	#plot modelled M2 phase 
	v = np.arange(-180, 202.5,22.5)
	plt.figure(figsize=(9,9))	
	CS = plt.contourf(X,Y,pha,v,cmap='gist_rainbow',aspect=(1 / numpy.cos(numpy.median(X) * numpy.pi / 180)))
	plt.colorbar(CS)
	plt.xlabel('longitude (deg)')
	plt.ylabel('latitude (deg)')
	plt.title(constflag+' phase (deg) for '+titstr)
	limits = plt.axis()
	if savestr:
	    plt.savefig('/ocean/klesouef/meopar/tools/compare_tides/'+constflag+'_pha_'+titstr+'.pdf')

