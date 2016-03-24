#/bin/bash

DIR=/ocean/sallen/allen/research/Meopar/Operational/ops_y2012m12*.nc
SAV=/ocean/nsoontie/MEOPAR/GEM2.5/ops/

for i in $( ls $DIR ); do
    PRE=$i
    TMP=$i
    
    python correct_pressure_ops.py $PRE $TMP $SAV
done
