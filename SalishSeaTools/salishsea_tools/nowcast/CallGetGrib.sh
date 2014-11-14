# python -m GetGrib 06  --- now done by a worker

# python -m getNBssh   --- now done by a worker

# python -m GetGrib 18  --- now done by a worker

# python -m gribTnetcdf --- now done by a worker

# ./deflate.sh --- now done by a grib_to_netcddf worker

./upload.sh
ssh orcinus MEOPAR/tools/SalishSeaTools/salishsea_tools/nowcast/makelinks.sh

