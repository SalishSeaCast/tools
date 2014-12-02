# cron script to run Salish Sea NEMO model nowcast Neah Bay ssh worker.
#
# usage:
#   MEOPAR=/data/dlatorne/MEOPAR
#   NOWCAST_TOOLS=tools/SalishSeaTools/salishsea_toola/nowcast
#   0 10 * * *  ${MEOPAR}/${NOWCAST_TOOLS}/workers/get_NeahBay_ssh.cron.sh

PYTHON=/home/dlatorne/anaconda/envs/nowcast/bin/python
NOWCAST=/home/dlatorne/public_html/MEOPAR/nowcast
CONFIG=${NOWCAST}/nowcast.yaml
${PYTHON} -m salishsea_tools.nowcast.workers.get_NeahBay_ssh ${CONFIG}
