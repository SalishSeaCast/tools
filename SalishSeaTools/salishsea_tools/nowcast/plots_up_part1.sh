# copy the files over and put me in the correct directory to edit .mako

# today
Year=$(date +%Y)
Month=$(date +%b)
Month=$(echo $Month | tr '[:upper:]' '[:lower:]')
Day=$(date +%d)

dir=${Day}${Month}${Year}

# origin
cd /ocean/sallen/allen/research/MEOPAR/SalishSea/forecast/$dir

# destination
destdir=/ocean/sallen/allen/research/MEOPAR/www_working/salishsea-site/site/_static/nemo/results_figures/forecast/$dir
echo $destdir
mkdir $destdir
cp * $destdir

echo 'Now go to www/templates and change the dates in the .mako file'