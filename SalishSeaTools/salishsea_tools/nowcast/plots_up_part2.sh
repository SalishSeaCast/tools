# copy the mako file over to www_working.  make a date named copy.  make html
# do the rst

# tomorrow
Year=$(date +%y -d tomorrow)
Month=$(date +%b -d tomorrow)
Month=$(echo $Month | tr '[:upper:]' '[:lower:]')
Day=$(date +%d -d tomorrow)

cd /data/dlatorne/MEOPAR/nowcast/www/salishsea-site/site/storm-surge
oridir=/ocean/sallen/allen/research/MEOPAR/Tools/SalishSeaTools/salishsea_tools/nowcast/www/templates
cp $oridir/forecast.mako forecast.rst
cp forecast.rst forecast_${Day}${Month}${Year}.rst

echo 'Now tell Doug to run the push_to_web worker.'
