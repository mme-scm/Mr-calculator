#!/bin/sh
# tiers 12-13 and constructions at the shrunk scope (see REPORT.md)
PY="/home/user/venv_sage/bin/python -W ignore"
PYN="/home/user/venv/bin/python -W ignore"
cd /home/user/Mr-calculator
$PY scripts/run_pass.py cc cc 12 13 kinds=pd
echo CC13_DONE
$PY scripts/run_pass.py cc cc 99 99 kinds=pd skip_conventions=1 shard_timeout=1200
echo CCTORUS_DONE
$PY scripts/run_pass.py mu mu 12 13 kinds=pd skip_conventions=1 nocomposite=1
echo MU13_DONE
$PYN scripts/run_fillings.py 12 12 q=2 time_limit=0.3 skip_conventions=1
$PYN scripts/run_fillings.py 13 13 q=1 time_limit=0.2 skip_conventions=1
echo FILL13_DONE
$PY scripts/find_coincidences.py budget=1200
echo COINC13_DONE
$PY scripts/node_inputs.py 30
$PY scripts/build_cables.py phase2 15 8 10 40
echo CHAIN_T13B_DONE
