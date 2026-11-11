#!/bin/sh
# tier <= 11: repair, fillings, coincidences, twists (k=2), mutations
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until ! pgrep -f "run_pass.py cc cc" > /dev/null; do sleep 5; done
$PY scripts/repair_unknown.py cc
$PY scripts/run_fillings.py 3 11
$PY scripts/find_coincidences.py
$PY scripts/run_pass.py tw2 tw 3 11 kinds=pd,braid kmin=2 kmax=2
$PY scripts/run_pass.py mu mu 3 11 kinds=pd,braid
echo CHAIN_T11_DONE
