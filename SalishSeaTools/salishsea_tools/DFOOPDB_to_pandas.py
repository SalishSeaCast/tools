import pandas as pd
import re
import os
import glob
import numpy as np

def loadDFO(basedir,varlist={},savedir='./'):
    """ Returns stations dataframe and obs (profiles) dataframe
    :arg basedir: path to the directory containing the files to be loaded
                  eg basedir='/ocean/eolson/MEOPAR/obs/temptest/'
            NOTE: basedir should contain only files to be read (or links to them)
    :type basedir: str
    
    :arg varlist: set containing variables to be loaded; see choosevars below
    :type varlist: set

    :arg savedir: directory to save log and error files to; defaults to current directory
    :type savedir: str
    """
    # these files log which files have been processed and record certain types of errors that can happen
    # you may want to take this part out and print the things that are written in these files to the screen instead
    fout=open(basedir+'createDBfromDFO_OPDB_log.txt','w')
    ferr=open(basedir+'createDBfromDFO_OPDB_errors.txt','w')
    fout.write('Files processed:\n')
    
    # create full list of filenames
    filenames=list()
    filenames=[os.path.join(basedir,f) for f in os.listdir(basedir)]
    filenames.sort()

    if len(varlist)==0:
        # create set of variable names to load if they are present in files
        choosevars={'Ammonia', 'Ammonium', 'Flag_Ammonium', 'Carbon_Dissolved_Organic',
            'Flag_Carbon_Dissolved_Organic', 'Carbon_Particulate_Organic', 'Carbon_Particulate_Total',
            'Flag_Carbon_Particulate_Total','Flag_Chlorophyll', 'Chlorophyll_Extracted',
            'Flag_Chlorophyll_Extracted', 'Chlorophyll_Extracted_gt0point7um',
            'Chlorophyll_Extracted_gt5point0um', 'Chlorophyll_plus_PhaeoPigment_Extracted', 'Date',
            'Depth', 'Depth_Nominal', 'Flag_Salinity', 'Flag_Salinity_Bottle', 'Flag_Silicate',
            'Flag_pH', 'Fluorescence_URU', 'Fluorescence_URU_Seapoint', 'Fluorescence_URU_Seatech',
            'Fluorescence_URU_Wetlabs', 'Latitude', 'Longitude', 'Nitrate', 'Flag_Nitrate',
            'Nitrate_plus_Nitrite', 'Flag_Nitrate_plus_Nitrite', 'Nitrate_plus_nitrite_ISUS',
            'Nitrate_plus_nitrite_ISUS_Voltage', 'Nitrite', 'Flag_Nitrite','Nitrogen_Dissolved_Organic',
            'Flag_Nitrogen_Dissolved_Organic', 'Nitrogen_Particulate_Organic','Nitrogen_Particulate_Total',
            'Flag_Nitrogen_Particulate_Total', 'Oxygen', 'Quality_Flag_Oxyg','Oxygen_Dissolved',
            'Flag_Oxygen_Dissolved', 'Oxygen_Dissolved_SBE', 'PAR', 'PAR_Reference',
            'PhaeoPigment_Extracted', 'Flag_PhaeoPigment_Extracted', 'Flag_Phaeophytin',  'Phosphate',
            'Flag_Phosphate','Quality_Flag_Phos', 'Phosphate(inorg)', 'Phytoplankton_Volume', 'Pressure',
            'Pressure_Reversing', 'Production_Primary', 'Quality_Flag_Nitr', 'Quality_Flag_Time',
            'Quality_Flag_Tota', 'Salinity', 'Salinity_Bottle', 'Salinity_T0_C0', 'Salinity_T1_C1',
            'Salinity__Pre1978','Quality_Flag_Sali','Salinity__Unknown', 'Sample_Method', 'Silicate',
            'Quality_Flag_Sili', 'Station', 'Temperature', 'Quality_Flag_Temp','Temperature_Draw',
            'Temperature_Primary','Temperature_Reversing', 'Temperature_Secondary', 'Time', 'Time_of_Obs',
            'Total_Phosphorus', 'Transmissivity', 'Turbidity_Seapoint'}
    else:
        chosevars=varlist
    varlistu=choosevars | {x+'_units' for x in choosevars if not re.search('Flag', x)}


    # create function that returns datatype for a given field name
    def coltype(ikey):
        typedict = {
            'Date': str,
            'Sample_Method': str,
            'Station': str,
            'Time': str,
            'Time_of_Obs.': str,
        }
        for varn in varlistu:
            if (re.search('Flag', varn) or varn in varlistu-choosevars):
                typedict[varn]=str
        return typedict.get(ikey, float) # 2nd argument is default value returned if ikey not in typedict

    # define Table Classes:
    dfStation=pd.DataFrame(columns=('ID','STATION','EVENT NUMBER','LATITUDE','Lat','LONGITUDE','Lon','WATER DEPTH',
                    'WDIR', 'WSPD','START TIME','StartDay','StartMonth','StartYear','StartHour','StartTimeZone',
                    'DATA DESCRIPTION','MISSION','AGENCY','COUNTRY','PROJECT','SCIENTIST','PLATFORM','sourceFile'))
    tdictSta={'ID':int,'STATION':str,'EVENT NUMBER':str,'LATITUDE':str,'Lat':float,'LONGITUDE':str,'Lon':float,'WATER DEPTH':float,
                    'WDIR':float, 'WSPD':float,'START TIME':str,'StartDay':int,'StartMonth':int,'StartYear':int,'StartHour':float,
                    'StartTimeZone':str,'DATA DESCRIPTION':str,'MISSION':str,'AGENCY':str,'COUNTRY':str,'PROJECT':str,
                    'SCIENTIST':str,'PLATFORM':str,'sourceFile':str,'StationTBLID':int}
    dfObs=pd.DataFrame(columns=list(('ID','sourceFile','StationTBLID',))+list([cname for cname in varlistu]))
    tdictObs={'ID':int,'sourceFile':str,'StationTBLID':int}
    for cname in varlistu:
        tdictObs[cname]=coltype(cname)

    stationNo=0
    obsNo=0
    for ifile in filenames:
        stationNo+=1
        sourceFile=re.search('\/ocean\/eolson\/MEOPAR\/obs\/(.*)', ifile).group(1)
        fout.write(sourceFile+'\n')
        varNames={}
        varLens={}
        varUnits={}
        stationData={}
        stationData['ID']=stationNo
        stationData['sourceFile']=sourceFile
        with open(ifile, 'rt', encoding = "ISO-8859-1") as f:
            infile=False
            invars=False
            indetail=False
            inadmin=False
            inloc=False
            indata=False
            detformat=False
            for line in f:
                if infile:
                    if re.match('\s*\$', line) or len(line)==0:
                        infile=False
                    else:
                        splitline=re.split('\s*\:\s*',line.strip(), maxsplit=1)
                        if re.match('START TIME',splitline[0]):
                            stationData['START TIME']=splitline[1]
                            splits=re.split('\s* \s*',splitline[1])
                            stationData['StartTimeZone']=splits[0]
                            date=splits[1]
                            time=splits[2]
                            stationData['StartYear']=date[0:4]
                            stationData['StartMonth']=date[5:7]
                            stationData['StartDay']=date[8:]
                            splitTime=re.split('\:',time)
                            stationData['StartHour']=float(splitTime[0])+float(splitTime[1])/60.0+float(splitTime[2])/3600.0
                        elif re.match('DATA DESCRIPTION',splitline[0]):
                            stationData['DATA DESCRIPTION']=splitline[1]
                if invars:
                    if re.search('\$END', line):
                        invars=False
                    else:
                        test=re.findall("'.*?'",line) # (.*? matches anything but chooses min len match - not greedy)
                        for expr in test:
                            line=re.sub(re.escape(expr),re.sub(' ','_',expr),line) # remove spaces from items in quotes
                        splitline=re.split('\s* \s*',line.strip())
                        if re.match('[0-9]', splitline[0]):
                            varnum=int(splitline[0])
                            cvar=splitline[1]
                            cvar = re.sub('(?<=[0-9])*\.(?=[0-9])','point',cvar) # decimal points -> point
                            cvar = re.sub('\-','',cvar) # remove - from column names
                            cvar = re.sub('\:','_',cvar) # replace : with _
                            cvar = re.sub('\>','gt',cvar) # replace > with gt
                            cvar = re.sub('\<','lt',cvar) # replace < with lt
                            cvar = re.sub('(\'|\.)','',cvar) # remove special characters (' and .)
                            cunits = splitline[2].strip()
                            varNames[varnum]=cvar
                            varUnits[varnum]=cunits
                elif indetail:
                    detcount+=1
                    if re.search('\$END', line):
                        indetail=False
                    elif (detcount==1 and re.match('\s*\!\s*No\s*Pad\s*Start\s*Width', line)):
                        detformat=True
                    else:
                        if (detformat and not re.match('\s*\!',line)):
                            test=re.findall("'.*?'",line) # (.*? matches anything but chooses min len match - not greedy)
                            for expr in test:
                                line=re.sub(re.escape(expr),re.sub(' ','_',expr),line) # remove spaces from items in quotes
                            splitline=re.split('\s* \s*',line.strip())
                            varnum=int(splitline[0])
                            try:
                                varwid=int(splitline[3])
                            except:
                                detformat=False
                            varLens[varnum]=varwid
                elif inadmin:
                    if len(line)==0:
                        inadmin=False
                    else:
                        splitline=re.split('\s*\:\s*',line.strip(), maxsplit=1)
                        if re.match('MISSION',splitline[0]):
                            stationData['MISSION']=splitline[1]
                        elif re.match('AGENCY',splitline[0]):
                            stationData['AGENCY']=splitline[1]
                        elif re.match('COUNTRY',splitline[0]):
                            stationData['COUNTRY']=splitline[1]
                        elif re.match('PROJECT',splitline[0]):
                            stationData['PROJECT']=splitline[1]
                        elif re.match('SCIENTIST',splitline[0]):
                            stationData['SCIENTIST']=splitline[1]
                        elif re.match('PLATFORM',splitline[0]):
                            stationData['PLATFORM']=splitline[1]
                elif inloc:
                    if len(line)==0:
                        inloc=False
                    else:
                        splitline=re.split('\s*\:\s*',line.strip(), maxsplit=1)
                        if re.match('STATION',splitline[0]):
                            try:
                                stationData['STATION']=splitline[1]
                            except:
                                print(line)
                                return()
                        elif re.match('EVENT NUMBER',splitline[0]):
                            stationData['EVENT NUMBER']=splitline[1]
                        elif re.match('LATITUDE',splitline[0]):
                            stationData['LATITUDE']=splitline[1]
                            latparts=re.split('\s* \s*', splitline[1])
                            signdict={'N':1,'E':1,'S':-1,'W':-1}
                            staLat=signdict[latparts[2]]*(float(latparts[0])+float(latparts[1])/60.0)
                            stationData['Lat']=staLat
                        elif re.match('LONGITUDE',splitline[0]):
                            stationData['LONGITUDE']=splitline[1]
                            lonparts=re.split('\s* \s*', splitline[1])
                            signdict={'N':1,'E':1,'S':-1,'W':-1}
                            staLon=signdict[lonparts[2]]*(float(lonparts[0])+float(lonparts[1])/60.0)
                            stationData['Lon']=staLon
                        elif re.match('WATER DEPTH',splitline[0]):
                            stationData['WATER DEPTH']=splitline[1]
                        elif re.match('WDIR',splitline[0]):
                            stationData['WDIR']=re.split('\s* \s*',splitline[1])[0]
                        elif re.match('WSPD',splitline[0]):
                            stationData['WSPD']=re.split('\s* \s*',splitline[1])[0]
                elif (indata and len(line)!=0 and not re.match('\s*\!',line)):
                    if detformat:
                        varVals={}
                        istart=0
                        for ii in range(1,1+max(varNames.keys())):
                            varVal=line[istart:(istart+varLens[ii])]
                            istart+=varLens[ii]
                            if varNames[ii] in varlistu:
                                varVals[varNames[ii]]=varVal.strip()
                            if varNames[ii]+'_units' in varlistu:
                                varVals[varNames[ii]+'_units']=varUnits[ii]
                        varVals['StationTBLID']=stationNo
                        varVals['sourceFile']=sourceFile
                        varVals['ID']=obsNo
                        obsNo=obsNo+1
                        #SEND TO DATABASE
                        #session.execute(ObsTBL.__table__.insert().values(**varVals))
                        for sel in varVals.keys():
                            varVals[sel]=tdictObs[sel](varVals[sel])
                        for sel in set(dfObs.keys())-set(varVals.keys()):
                            varVals[sel]=np.nan
                        dfObs.loc[varVals['ID']]=varVals
                    else:
                        varVals={}
                        splitline=re.split('\s*\ \s*',line.strip())
                        if len(splitline)==max(varNames.keys()):
                            for ii in range(1,1+max(varNames.keys())):
                                if varNames[ii] in varlistu:
                                    varVals[varNames[ii]]=splitline[ii-1].strip()
                                if varNames[ii]+'_units' in varlistu:
                                    varVals[varNames[ii]+'_units']=varUnits[ii]
                            varVals['StationTBLID']=stationNo
                            varVals['sourceFile']=sourceFile
                            varVals['ID']=obsNo
                            obsNo=obsNo+1
                            #SEND TO DATABASE
                            #session.execute(ObsTBL.__table__.insert().values(**varVals))
                            for sel in varVals.keys():
                                varVals[sel]=tdictObs[sel](varVals[sel])
                            for sel in set(dfObs.keys())-set(varVals.keys()):
                                varVals[sel]=np.nan
                            dfObs.loc[varVals['ID']]=varVals
                        else:
                            ferr.write('ERROR: filename:'+sourceFile+' line:'+line)
                if re.match('![- ]*$',line):
                    tem=re.search('(?<=\!)[- ]*$',line)
                    splitline=re.split(r'\s',tem.group(0))
                    for ii in range(1, 1+len(splitline)):
                        varLens[ii]=len(splitline[ii-1])+1
                        detformat=True
                if re.search('\*FILE', line):
                    infile=True
                if re.search('\$TABLE\: CHANNELS', line):
                    invars=True
                if re.search('\$TABLE\: CHANNEL DETAIL', line):
                    indetail=True
                    detcount=0
                if re.search('\*ADMINISTRATION', line):
                    inadmin=True
                if re.search('\*LOCATION', line):
                    inloc=True
                    inadmin=False
                if re.search('\*END OF HEADER', line):
                    indata=True
                    inloc=False
                if re.search('\$END',line):
                    inloc=False
            # SEND TO DATABASE (at file level)
            for sel in stationData.keys():
                stationData[sel]=tdictSta[sel](stationData[sel])
            for sel in set(dfStation.keys())-set(stationData.keys()):
                stationData[sel]=np.nan
            dfStation.loc[stationData['ID']]=stationData
            #session.execute(StationTBL.__table__.insert().values(**stationData))
    fout.close()
    ferr.close()
    return dfStation, dfObs
