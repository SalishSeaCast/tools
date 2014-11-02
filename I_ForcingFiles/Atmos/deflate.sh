# deflate file
cd ../../../Operational
Year=$(date +%Y)
Month=$(date +%m)
Day=$(date +%d)
netfile=ops_y${Year}m${Month}d${Day}.nc
echo $netfile
ncks -4 -L4 -O $netfile $netfile
