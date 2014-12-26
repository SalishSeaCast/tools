cd /ocean/sallen/allen/research/MEOPAR/www_working/salishsea-site/site/storm-surge
oridir=/ocean/sallen/allen/research/MEOPAR/Tools/SalishSeaTools/salishsea_tools/nowcast/www/templates
cp $oridir/forecast.mako forecast.rst
cd ..
make html
rsync -tvhz _build/html/storm-surge/forecast.html ~/public_html/MEOPAR/site/storm-surge/
rsync -rtvhz _build/html/_static/nemo/results_figures/ ~/public_html/MEOPAR/site/_static/nemo/results_figures/
