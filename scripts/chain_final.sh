#!/bin/sh
# last round of passes before the final solve (time-boxed)
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until grep -q "TW4_DONE" logs/chain_extra.log 2>/dev/null; do sleep 10; done
pkill -f chain_extra.sh
pkill -f "run_pass.py cc cc 3 13"
$PY scripts/run_pass.py tw3 tw 12 12 kinds=pd kmin=3 kmax=3 procs=4 skip_conventions=1 nocomposite=1 budget=2100
echo TW3_12_DONE
$PY scripts/run_pass.py tw2 tw 12 12 kinds=pd kmin=2 kmax=2 procs=4 skip_conventions=1 nocomposite=1 budget=900
echo TW2_12_DONE
$PY scripts/run_pass.py cc cc 3 13 kinds=pd,braid,re procs=4 skip_conventions=1 shard_timeout=900 budget=600
$PY scripts/run_pass.py mu mu 3 13 kinds=pd,braid procs=4 skip_conventions=1 shard_timeout=900 budget=300
echo COMPOSITE_DONE
$PY scripts/run_pass.py ccb cc 12 13 kinds=braid procs=4 skip_conventions=1 nocomposite=1 budget=900
echo CHAIN_FINAL_DONE
