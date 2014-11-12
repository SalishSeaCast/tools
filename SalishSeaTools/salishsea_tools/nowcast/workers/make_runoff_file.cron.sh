# cron script to run Salish Sea NEMO model nowcast make runoff file worker.
#
# usage:
#   MEOPAR=/data/dlatorne/MEOPAR
#   NOWCAST_TOOLS=tools/SalishSeaTools/salishsea_toola/nowcast
#   0 10 * * *  ${MEOPAR}/${NOWCAST_TOOLS}/workers/make_runoff_file.cron.sh

PYTHON=/home/dlatorne/anaconda/bin/python
NOWCAST=/home/dlatorne/public_html/MEOPAR/nowcast
CONFIG=${NOWCAST}/nowcast.yaml
${PYTHON} -m salishsea_tools.nowcast.workers.make_runoff_file ${CONFIG}
