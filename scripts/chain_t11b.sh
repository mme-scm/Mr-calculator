#!/bin/sh
# tier <= 11 after crossing changes: fillings, coincidences, twists (k=2, KnotInfo diagrams), mutations,
# then the composite crossing-change shards that were interrupted
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until ! pgrep -f "repair_unknown.py cc" > /dev/null; do sleep 5; done
echo REPAIR_DONE
$PY scripts/run_fillings.py 3 11 time_limit=1.5
$PY scripts/find_coincidences.py
echo M4_DATA_DONE
$PY scripts/run_pass.py tw2 tw 3 11 kinds=pd kmin=2 kmax=2 skip_conventions=1
echo TW2_DONE
$PY scripts/run_pass.py mu mu 3 11 kinds=pd,braid skip_conventions=1
echo MU_DONE
$PY scripts/run_pass.py cc cc 3 11 kinds=pd,braid,re skip_conventions=1
echo CHAIN_T11B_DONE
