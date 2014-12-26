# copy the forecast file into the day file

# today
Year=$(date +%Y)
Month=$(date +%b)
Month=$(echo $Month | tr '[:upper:]' '[:lower:]')
Day=$(date +%d)

cd ~/public_html/MEOPAR/site/storm-surge
cp forecast.html forecast_${Day}${Month}${Year}.html

echo 'Now edit /home/dlatorne/public_html/MEOPAR/nowcast/index.html to include your file'
