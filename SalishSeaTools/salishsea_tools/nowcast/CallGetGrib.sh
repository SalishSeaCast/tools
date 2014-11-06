#python -m GetGrib 06  --- now done by a worker

python -m getNBssh

#python -m GetGrib 18  --- now done by a worker

python -m gribTnetcdf
./deflate.sh

./upload.sh


