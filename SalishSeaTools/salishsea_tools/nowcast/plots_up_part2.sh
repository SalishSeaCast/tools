# copy the mako file over to www_working.  make a date named copy.  make html 
# do the rst

# tomorrow
Year=$(date +%y -d tomorrow)
Month=$(date +%b -d tomorrow)
Month=$(echo $Month | tr '[:upper:]' '[:lower:]')
Day=$(date +%d -d tomorrow)

cd /ocean/sallen/allen/research/MEOPAR/www_working/salishsea-site/site/storm-surge
oridir=/ocean/sallen/allen/research/MEOPAR/Tools/SalishSeaTools/salishsea_tools/nowcast/www/templates
cp $oridir/forecast.mako forecast.rst
cp forecast.rst forecast_${Day}${Month}${Year}.rst

cd ..
make html
rsync -rtvhz _build/html/storm-surge/ ~/public_html/MEOPAR/site/storm-surge/
rsync -rtvhz _build/html/_static/nemo/results_figures/ ~/public_html/MEOPAR/site/_static/nemo/results_figures/
