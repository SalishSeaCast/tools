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
	mod_M2_x_elev = harmT.variables['M2_x_elev'][0,:,:] #Cj
	mod_M2_y_elev = harmT.variables['M2_y_elev'][0,:,:] #Sj
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

#define a function to get the subdomain bathymetry and grid data
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

#define a function to plot a scatter plot of measured vs. modelled phase and amplitude
# e.g. plot_scatter_pha_amp(Am_K1_all,Ao_K1_all,gm_K1_all,go_K1_all,'K1','50s_30Sep-6Oct')
def plot_scatter_pha_amp(Am,Ao,gm,go,constflag,runname):
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

#define a function to plot the differences on a map of the domain
# e.g. plot_diffs_on_domain(D_F95_all_M2,meas_wl_harm,'F95','M2',runname):
def plot_diffs_on_domain(D,meas_wl_harm,calcmethod,constflag,runname):
	import matplotlib.pyplot as plt

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




