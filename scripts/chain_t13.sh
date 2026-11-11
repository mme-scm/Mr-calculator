#!/bin/sh
# tiers 12-13 and constructions: crossing changes, fillings (reduced slope set), coincidences, mutations,
# peripheral calculator inputs, cables
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until grep -q "CHAIN_T11B_DONE" logs/chain_t11b.log 2>/dev/null; do sleep 10; done
$PY scripts/run_pass.py cc cc 12 13 kinds=pd,braid
echo CC13_DONE
$PY scripts/run_pass.py cc cc 99 99 kinds=pd,re skip_conventions=1
$PY scripts/run_fillings.py 99 99
$PY scripts/run_pass.py mu mu 12 13 kinds=pd skip_conventions=1
echo MU13_DONE
$PY scripts/run_fillings.py 12 13 q=2 time_limit=0.3
$PY scripts/find_coincidences.py
echo FILL13_DONE
$PY scripts/node_inputs.py 30
$PY scripts/build_cables.py 15 8 20 60
echo CHAIN_T13_DONE
