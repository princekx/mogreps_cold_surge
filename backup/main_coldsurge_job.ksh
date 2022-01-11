#!/bin/ksh
#
#
# Load scitools
module load scitools

# retrieve analysis
cd ~hadpx/MJO/Monitoring/

# Retrieve mogreps data
python mogreps_cold_surge/retrieve_mogreps_data.py

# Cold surge monitor
python mogreps_cold_surge/MOGREPS_ColdSurge_monitor.py

