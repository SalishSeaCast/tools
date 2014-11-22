# make symbolic links including forecast links for Salish

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

# Next Day
Yearp2=$(date +%Y -d "today + 2 day")
Monthp2=$(date +%m -d "today + 2 day")
Dayp2=$(date +%d -d "today + 2 day")

cd /ocean/sallen/allen/research/MEOPAR/nowcast

# rivers
cd rivers
# ln -s ../../NEMO-forcing/rivers/rivers_month.nc
riverfilem1=RFraserCElse_y${Yearm1}m${Monthm1}d${Daym1}.nc
riverfile=RFraserCElse_y${Year}m${Month}d${Day}.nc
riverfilep1=RFraserCElse_y${Yearp1}m${Monthp1}d${Dayp1}.nc
riverfilep2=RFraserCElse_y${Yearp2}m${Monthp2}d${Dayp2}.nc
rm -f $riverfilem1
ln -s ../../Rivers/$riverfilem1
rm -f $riverfile
ln -s ../../Rivers/$riverfilem1 $riverfile
rm -f $riverfilep1
ln -s ../../Rivers/$riverfilem1 $riverfilep1
rm -f $riverfilep2
ln -s ../../Rivers/$riverfilem1 $riverfilep2

# ssh
cd ../open_boundaries/west/ssh
sshfilem1=ssh_y${Yearm1}m${Monthm1}d${Daym1}.nc
sshfile=ssh_y${Year}m${Month}d${Day}.nc
sshfilep1=ssh_y${Yearp1}m${Monthp1}d${Dayp1}.nc
sshfilep2=ssh_y${Yearp2}m${Monthp2}d${Dayp2}.nc
rm -f $sshfilem1
ln -s /ocean/nsoontie/MEOPAR/sshNeahBay/obs/$sshfilem1
rm -f $sshfile
ln -s /ocean/nsoontie/MEOPAR/sshNeahBay/fcst/$sshfile
rm -f $sshfilep1
ln -s /ocean/nsoontie/MEOPAR/sshNeahBay/fcst/$sshfilep1
rm -f $sshfilep2
ln -s /ocean/nsoontie/MEOPAR/sshNeahBay/fcst/$sshfilep2

# weather
cd ../../../NEMO-atmos
#ln -s ../../NEMO-forcing/atmospheric/no_snow.nc
#ln -s ../../NEMO-forcing/grid/weights-gem2.5-ops.nc
netfilem1=ops_y${Yearm1}m${Monthm1}d${Daym1}.nc
netfile=ops_y${Year}m${Month}d${Day}.nc
netfilep1=ops_y${Yearp1}m${Monthp1}d${Dayp1}.nc
netfilep2=ops_y${Yearp2}m${Monthp2}d${Dayp2}.nc
rm -f $netfilem1
ln -s ../../Operational/$netfilem1
rm -f $netfile
ln -s ../../Operational/$netfile
rm -f $netfilep1
ln -s ../../Operational/fcst/$netfilep1 
rm -f $netfilep2
ln -s ../../Operational/fcst/$netfilep2 

