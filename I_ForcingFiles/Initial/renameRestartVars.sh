#!/bin/sh
# first ARG ($1) is name of restart file
# 2nd ARG ($2) is name of output file

cp $1 $2

# use ncrename to change old to new var names:
ncrename -v sbc_DOC_b,sbc_DON_b $2
ncrename -v sbc_POC_b,sbc_PON_b $2
ncrename -v TRBPHY2,TRBDIAT $2
ncrename -v TRNPHY2,TRNDIAT $2
ncrename -v TRNDOC,TRNDON $2
ncrename -v TRNPOC,TRNPON $2
ncrename -v TRBPOC,TRBPON $2
ncrename -v TRBDOC,TRBDON $2
ncrename -v rnf_pis_PHY2_b,rnf_pis_DIAT_b $2
ncrename -v rnf_pis_DOC_b,rnf_pis_DON_b $2
ncrename -v rnf_pis_POC_b,rnf_pis_PON_b $2
ncrename -v sbc_PHY2_b,sbc_DIAT_b $2
ncrename -v sbc_O2_b,sbc_TRA_b $2
ncrename -v rnf_pis_O2_b,rnf_pis_TRA_b $2
ncrename -v TRNO2,TRNTRA $2
ncrename -v TRBO2,TRBTRA $2
