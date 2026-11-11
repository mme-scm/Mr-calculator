#!/bin/sh
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until grep -q "CHAIN_EXTRA_DONE" logs/chain_extra.log 2>/dev/null; do sleep 10; done
$PY scripts/run_pass.py tw2 tw 12 12 kinds=pd kmin=2 kmax=2 procs=4 skip_conventions=1 nocomposite=1
echo TW2_12_DONE
$PY scripts/run_pass.py tw2 tw 13 13 kinds=pd kmin=2 kmax=2 procs=4 skip_conventions=1 nocomposite=1 budget=2400
echo CHAIN_EXTRA2_DONE
