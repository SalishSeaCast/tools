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

# Next day
Yearp2=$(date +%Y -d "today + 2 day")
Monthp2=$(date +%m -d "today + 2 day")
Dayp2=$(date +%d -d "today + 2 day")

# copy weather file to orcinus
netfile=ops_y${Year}m${Month}d${Day}.nc
netfilep1=ops_y${Yearp1}m${Monthp1}d${Dayp1}.nc
netfilep2=ops_y${Yearp2}m${Monthp2}d${Dayp2}.nc
cd /ocean/sallen/allen/research/MEOPAR/Operational
scp -p $netfile orcinus:/home/sallen/MEOPAR/GEM2.5/ops/NEMO-atmos/
cd fcst
scp -p $netfilep1 orcinus:/home/sallen/MEOPAR/GEM2.5/ops/NEMO-atmos/fcst/
scp -p $netfilep2 orcinus:/home/sallen/MEOPAR/GEM2.5/ops/NEMO-atmos/fcst/

# copy river file to orcinus
cd /ocean/sallen/allen/research/MEOPAR/Rivers
riverfile=RFraserCElse_y${Yearm1}m${Monthm1}d${Daym1}.nc
scp -p $riverfile orcinus:/home/sallen/MEOPAR/rivers/

# copy ssh files to orcinus
cd /ocean/nsoontie/MEOPAR/sshNeahBay/obs
sshfilem1=ssh_y${Yearm1}m${Monthm1}d${Daym1}.nc
scp -p $sshfilem1 orcinus:/home/sallen/MEOPAR/sshNeahBay/obs/
cd ../fcst
sshfile=ssh_y${Year}m${Month}d${Day}.nc
scp -p $sshfile orcinus:/home/sallen/MEOPAR/sshNeahBay/fcst/
sshfilep1=ssh_y${Yearp1}m${Monthp1}d${Dayp1}.nc
scp -p $sshfilep1 orcinus:/home/sallen/MEOPAR/sshNeahBay/fcst/
sshfilep2=ssh_y${Yearp2}m${Monthp2}d${Dayp2}.nc
scp -p $sshfilep2 orcinus:/home/sallen/MEOPAR/sshNeahBay/fcst/
