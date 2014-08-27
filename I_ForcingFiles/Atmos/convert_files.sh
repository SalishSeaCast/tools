#/bin/bash

DIR=/home/dlatorne/MEOPAR/CGRF/NEMO-atmos/slp_y*
SAV=/home/dlatorne/MEOPAR/CGRF/NEMO-atmos/

for i in $( ls $DIR ); do
    PRE=$i
    TMP=${i/slp_/t2_}
    
    python correct_pressure.py $PRE $TMP $SAV
done