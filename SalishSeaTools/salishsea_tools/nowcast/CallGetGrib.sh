#python -m GetGrib 06
python -m GetGrib 18
python -m gribTnetcdf
python -m getNBshh

./deflate.sh
./upload.sh


