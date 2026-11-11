#!/bin/sh
# extra coverage made affordable by the faster identification
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until grep -q "TW3B_DONE" logs/tw3b.log 2>/dev/null; do sleep 10; done
$PY scripts/run_pass.py tw4 tw 3 8 kinds=pd kmin=4 kmax=4 procs=2 skip_conventions=1 nocomposite=1
echo TW4_DONE
$PY scripts/run_pass.py cc cc 3 13 kinds=pd,braid,re procs=2 skip_conventions=1 shard_timeout=1800
$PY scripts/run_pass.py mu mu 3 13 kinds=pd,braid procs=2 skip_conventions=1 shard_timeout=1800
echo COMPOSITE_DONE
$PY scripts/run_pass.py ccb cc 12 13 kinds=braid procs=2 skip_conventions=1 nocomposite=1
echo CCB_DONE
$PY scripts/run_pass.py tw23r tw 3 10 kinds=braid,re kmin=2 kmax=3 procs=2 skip_conventions=1 nocomposite=1
echo TW23R_DONE
echo CHAIN_EXTRA_DONE
