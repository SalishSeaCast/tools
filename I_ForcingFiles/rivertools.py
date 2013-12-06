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
		prop_dict = {'SanJuan':{'prop':0.33*CAFlux,'i':402,'j':56,'di':1,'dj':1,'depth':3},\
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

	if watershedname == 'puget':
		#WRIA17 10% of Puget Sound Watershed
		WRIA17 = 0.10
		#WRIA16 10% of Puget Sound Watershed
		WRIA16 = 0.10
		#WRIA15 15% of Puget Sound Watershed
		WRIA15 = 0.15
		#WRIA14 5% of Puget Sound Watershed
		WRIA14 = 0.05
		#WRIA13 3% of Puget Sound Watershed
		WRIA13 = 0.03
		#WRIA12 2% of Puget Sound Watershed
		WRIA12 = 0.02
		#WRIA11 15% of Puget Sound Watershed
		WRIA11 = 0.15
		#WRIA10 20% of Puget Sound Watershed
		WRIA10 = 0.20
		#WRIA9 10% of Puget Sound Watershed
		WRIA9 = 0.10
		#WRIA8 10% of Puget Sound Watershed
		WRIA8 = 0.10

		prop_dict = {'Johnson':{'prop':0.05*WRIA17,'i':207,'j':202,'di':1,'dj':1,'depth':3},\
		'Jimmycomelately':{'prop':0.05*WRIA17,'i':199,'j':202,'di':1,'dj':1,'depth':3},\
		'SalmonSnow':{'prop':0.25*WRIA17,'i':182,'j':219,'di':1,'dj':1,'depth':3},\
		'Chimacum':{'prop':0.20*WRIA17,'i':185,'j':240,'di':1,'dj':1,'depth':3},\
		'Thorndike':{'prop':0.05*WRIA17,'i':137,'j':215,'di':1,'dj':1,'depth':3},\
		'Torboo':{'prop':0.05*WRIA17,'i':149,'j':208,'di':1,'dj':1,'depth':3},\
		'LittleBigQuilcene':{'prop':0.35*WRIA17,'i':146,'j':199,'di':1,'dj':1,'depth':3},\
		'Dosewalips':{'prop':0.20*WRIA16,'i':124,'j':177,'di':1,'dj':1,'depth':3},\
		'Duckabush':{'prop':0.14*WRIA16,'i':119,'j':167,'di':1,'dj':1,'depth':3},\
		'Fulton':{'prop':0.02*WRIA16,'i':116,'j':156,'di':1,'dj':1,'depth':3},\
		'Waketick':{'prop':0.02*WRIA16,'i':108,'j':141,'di':1,'dj':1,'depth':3},\
		'HammaHamma':{'prop':0.14*WRIA16,'i':107,'j':139,'di':1,'dj':1,'depth':3},\
		'Jorsted':{'prop':0.02*WRIA16,'i':104,'j':135,'di':1,'dj':1,'depth':3},\
		'Eagle':{'prop':0.02*WRIA16,'i':98,'j':127,'di':1,'dj':1,'depth':3},\
		'Lilliwaup':{'prop':0.02*WRIA16,'i':95,'j':118,'di':1,'dj':1,'depth':3},\
		'Finch':{'prop':0.02*WRIA16,'i':87,'j':108,'di':1,'dj':1,'depth':3},\
		'Skokomish':{'prop':0.40*WRIA16,'i':75,'j':103,'di':1,'dj':1,'depth':3},\
		'Rendsland':{'prop':0.025*WRIA15,'i':81,'j':107,'di':1,'dj':1,'depth':3},\
		'Tahuya':{'prop':0.20*WRIA15,'i':72,'j':114,'di':1,'dj':1,'depth':3},\
		'Mission':{'prop':0.05*WRIA15,'i':73,'j':149,'di':1,'dj':1,'depth':3},\
		'Union':{'prop':0.10*WRIA15,'i':74,'j':153,'di':1,'dj':1,'depth':3},\
		'Coulter':{'prop':0.05*WRIA15,'i':64,'j':153,'di':1,'dj':1,'depth':3},\
		'Minter':{'prop':0.05*WRIA15,'i':46,'j':168,'di':1,'dj':1,'depth':3},\
		'Butley':{'prop':0.05*WRIA15,'i':47,'j':178,'di':1,'dj':1,'depth':3},\
		'Olalla':{'prop':0.05*WRIA15,'i':48,'j':197,'di':1,'dj':1,'depth':3},\
		'BlackjackClearBarkerBigValley1':{'prop':0.1125*WRIA15,'i':68,'j':210,'di':1,'dj':1,'depth':3},\
		'BlackjackClearBarkerBigValley2':{'prop':0.1125*WRIA15,'i':108,'j':232,'di':1,'dj':1,'depth':3},\
		'BigBear':{'prop':0.05*WRIA15,'i':112,'j':189,'di':1,'dj':1,'depth':3},\
		'Swaback':{'prop':0.025*WRIA15,'i':112,'j':185,'di':1,'dj':1,'depth':3},\
		'Stavis':{'prop':0.025*WRIA15,'i':113,'j':174,'di':1,'dj':1,'depth':3},\
		'Anderson':{'prop':0.05*WRIA15,'i':107,'j':150,'di':1,'dj':1,'depth':3},\
		'Dewatta':{'prop':0.05*WRIA15,'i':94,'j':122,'di':1,'dj':1,'depth':3},\
		'Sherwood':{'prop':0.15*WRIA14,'i':60,'j':149,'di':1,'dj':1,'depth':3},\
		'DeerJohnsGoldboroughMillSkookumKennedySchneider':{'prop':0.375*WRIA14,'i':47,'j':130,'di':1,'dj':1,'depth':3},\
		'DeerJohnsGoldboroughMillSkookumKennedySchneiderPerry':{'prop':0.475*WRIA14,'i':20,'j':120,'di':1,'dj':1,'depth':3},\
		'McClaneDeschutesWoodwardWoodland':{'prop':1.0*WRIA13,'i':22,'j':121,'di':1,'dj':1,'depth':3},\
		'Chambers':{'prop':1.0*WRIA12,'i':6,'j':162,'di':1,'dj':1,'depth':3},\
		'NisquallyMcAllister':{'prop':1.0*WRIA11,'i':0,'j':137,'di':1,'dj':1,'depth':3},\
		'Puyallup':{'prop':0.995*WRIA10,'i':10,'j':195,'di':1,'dj':1,'depth':3},\
		'Hylebas':{'prop':0.005*WRIA10,'i':13,'j':199,'di':1,'dj':1,'depth':3},\
		'Duwamish1':{'prop':0.50*WRIA9,'i':68,'j':243,'di':1,'dj':1,'depth':3},\
		'Duwamish2':{'prop':0.50*WRIA9,'i':68,'j':246,'di':1,'dj':1,'depth':3},\
		'CedarSammamish':{'prop':1.0*WRIA8,'i':88,'j':246,'di':1,'dj':1,'depth':3}}
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
