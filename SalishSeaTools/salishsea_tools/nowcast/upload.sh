# upload weather data to orcinus

# today
Year=$(date +%Y)
Month=$(date +%m)
Day=$(date +%d)

# Yesterday
Yearm1=$(date +%Y -d yesterday)
Monthm1=$(date +%m -d yesterday)
Daym1=$(date +%d -d yesterday)

# Tomorrow
Yearp1=$(date +%Y -d tomorrow)
Monthp1=$(date +%m -d tomorrow)
Dayp1=$(date +%d -d tomorrow)


# copy weather file to orcinus
netfile=ops_y${Year}m${Month}d${Day}.nc
cd /ocean/sallen/allen/research/MEOPAR/Operational
scp -p $netfile sallen@orcinus:MEOPAR/GEM2.5/ops/NEMO-atmos/

# copy river file to orcinus
cd ../Tools/I_ForcingFiles/Rivers
riverfile=RFraserCElse_y${Yearm1}m${Monthm1}d${Daym1}.nc
scp -p $riverfile sallen@orcinus:MEOPAR/rivers/

# copy ssh files to orcinus
cd /ocean/nsoontie/MEOPAR/sshNeahBay/obs
sshfile=ssh_y${Yearm1}m${Monthm1}d${Daym1}.nc
scp -p $sshfile sallen@orcinus:MEOPAR/sshNeahBay/obs/
cd ../fcst
sshfile=ssh_y${Year}m${Month}d${Day}.nc
scp -p $sshfile sallen@orcinus:MEOPAR/sshNeahBay/fcst/
sshfile=ssh_y${Yearp1}m${Monthp1}d${Dayp1}.nc
scp -p $sshfile sallen@orcinus:MEOPAR/sshNeahBay/fcst/
