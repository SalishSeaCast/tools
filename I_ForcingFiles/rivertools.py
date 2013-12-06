import numpy as np
import netCDF4 as NC

#define a function to fill the river file with the rivers of one watershed
def put_watershed_into_runoff(rivertype,watershedname,flux,runoff,run_depth):
	pd = get_watershed_prop_dict(watershedname)
	for key in pd:
		river = pd[key]		
		fill_runoff_array(flux*river['prop'],river['i'],river['di'],river['j'],river['dj'],river['depth'],runoff,run_depth)
	return runoff, run_depth

def get_watershed_prop_dict(watershedname):
	if watershedname == 'howe':	
		#dictionary of rivers in Howe watershed		
		prop_dict = {'Squamish':{'prop':0.9,'i':532,'j':385,'di':1,'dj':2,'depth':3},'Burrard':{'prop':0.1,'i':457,'j':343,'di':3,'dj':1,'depth':3}}
	if watershedname == 'jdf':
		# Assume that 50% of the area of the JdF watershed defined by Morrison et al (2011) is on north side of JdF (Canada side)
		CAFlux = 0.50
		# Assume that 50% of the area of the watershed defined by Morrison et al (2011) is on south side of JdF (US side)
		USFlux = 0.50
		#dictionary of rivers in Juan de Fuca watershed
		prop_dict = {'SanJuan':{'prop':0.33*CAFlux,'i':402,'j':56,'di':1,'dj':2,'depth':3},\
		'Gordon':{'prop':0.14*CAFlux,'i':403,'j':56,'di':1,'dj':1,'depth':3},\
		'Loss':{'prop':0.05*CAFlux,'i':375,'j':71,'di':1,'dj':1,'depth':3},\
		'Jordan':{'prop':0.05*CAFlux,'i':348,'j':96,'di':1,'dj':1,'depth':3},\
		'Muir':{'prop':0.05*CAFlux,'i':326,'j':119,'di':1,'dj':1,'depth':3},\
		'Tugwell':{'prop':0.05*CAFlux,'i':325,'j':120,'di':1,'dj':1,'depth':3},\
		'Sooke':{'prop':0.33*CAFlux,'i':308,'j':137,'di':1,'dj':1,'depth':3},\
		'Elwha':{'prop':0.60*0.50*USFlux,'i':261,'j':134,'di':1,'dj':1,'depth':3},\
		'Tumwater':{'prop':0.60*0.01*USFlux,'i':248,'j':151,'di':1,'dj':1,'depth':3},\
		'Valley':{'prop':0.60*0.01*USFlux,'i':247,'j':152,'di':1,'dj':1,'depth':3},\
		'Ennis':{'prop':0.60*0.02*USFlux,'i':244,'j':156,'di':1,'dj':1,'depth':3},\
		'Morse':{'prop':0.60*0.07*USFlux,'i':240,'j':164,'di':1,'dj':1,'depth':3},\
		'Bagley':{'prop':0.60*0.02*USFlux,'i':239,'j':165,'di':1,'dj':1,'depth':3},\
		'Siebert':{'prop':0.60*0.02*USFlux,'i':235,'j':174,'di':1,'dj':1,'depth':3},\
		'McDonald':{'prop':0.60*0.03*USFlux,'i':233,'j':183,'di':1,'dj':1,'depth':3},\
		'DungenessMatriotti':{'prop':0.60*0.30*USFlux+0.60*0.02*USFlux,'i':231,'j':201,'di':1,'dj':1,'depth':3},\
		'Coville':{'prop':0.40*0.05*USFlux,'i':263,'j':128,'di':1,'dj':1,'depth':3},\
		'Salt':{'prop':0.40*0.05*USFlux,'i':275,'j':116,'di':1,'dj':1,'depth':3},\
		'Field':{'prop':0.40*0.05*USFlux,'i':281,'j':100,'di':1,'dj':1,'depth':3},\
		'Lyre':{'prop':0.40*0.20*USFlux,'i':283,'j':98,'di':1,'dj':1,'depth':3},\
		'EastWestTwin':{'prop':0.40*0.05*USFlux,'i':293,'j':81,'di':1,'dj':1,'depth':3},\
		'Deep':{'prop':0.40*0.05*USFlux,'i':299,'j':72,'di':1,'dj':1,'depth':3},\
		'Pysht':{'prop':0.40*0.10*USFlux,'i':310,'j':65,'di':1,'dj':1,'depth':3},\
		'Clallom':{'prop':0.40*0.10*USFlux,'i':333,'j':45,'di':1,'dj':1,'depth':3},\
		'Hoko':{'prop':0.40*0.20*USFlux,'i':345,'j':35,'di':1,'dj':1,'depth':3},\
		'Sekiu':{'prop':0.40*0.10*USFlux,'i':348,'j':31,'di':1,'dj':1,'depth':3},\
		'Sail':{'prop':0.40*0.05*USFlux,'i':373,'j':17,'di':1,'dj':1,'depth':3}}

	print prop_dict
	return prop_dict

#define a function to get the bathymetry and size of each cell
def get_bathy_cell_size():
	fC = NC.Dataset('../../nemo-forcing/grid/coordinates_seagrid_SalishSea.nc','r')
	e1t = fC.variables['e1t']
	e2t = fC.variables['e2t']
	return e1t, e2t

#define a function to initialise the runoff array
def init_runoff_array():
	fB = NC.Dataset('../../nemo-forcing/grid/bathy_meter_SalishSea.nc','r')
	D = fB.variables['Bathymetry'][:]
	ymax, xmax = D.shape
	runoff = np.zeros((ymax,xmax))
	run_depth = -np.ones((ymax,xmax))
	return runoff, run_depth

#define a function to fill the runoff array
def fill_runoff_array(Flux,istart,di,jstart,dj,depth_of_flux,runoff,run_depth):
	e1t, e2t = get_bathy_cell_size()
	number_cells = di*dj
	area = number_cells*e1t[0,istart,jstart]*e2t[0,istart,jstart]
	w = Flux/area * 1000.   # w is in kg/s not m/s
	runoff[istart:istart+di,jstart:jstart+dj] = w
	run_depth[istart:istart+di,jstart:jstart+dj] = depth_of_flux
	return runoff, run_depth

#define a function to check the runoff adds up to what it should
def check_sum(runoff_orig, runoff_new, Flux):
	e1t, e2t = get_bathy_cell_size()
	print (np.sum(runoff_new)-runoff_orig.sum())*e1t[0,450,200]*e2t[0,450,200]/1000., Flux
