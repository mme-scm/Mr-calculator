#!/bin/sh
# Round A: twists on KnotInfo PD diagrams at the specification values (k_max 6/5/4), cheapest first.
# Staged: output goes to /home/user/mrcalc_stage and is synced into data/ at check-ins.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until grep -q "PASSES_DONE" logs/chain_last.log 2>/dev/null; do sleep 10; done
mkdir -p $MRCALC_STAGE
mkdir -p $MRCALC_STAGE/passes && cp -r data/passes/. $MRCALC_STAGE/passes/
cp data/ref_census.jsonl $MRCALC_STAGE/ref_census.jsonl
run() { echo "START $1 $(date -u +%H:%M)"; shift; $PY scripts/run_pass.py "$@" procs=4 nocomposite=1; }
run tw3-12 tw3 tw 12 12 kinds=pd kmin=3 kmax=3
echo A1_DONE
run tw2-12-13 tw2 tw 12 13 kinds=pd kmin=2 kmax=2 skip_conventions=1
echo A2_DONE
run tw3-13 tw3 tw 13 13 kinds=pd kmin=3 kmax=3 skip_conventions=1
echo A3_DONE
run tw4-9-11 tw4 tw 9 11 kinds=pd kmin=4 kmax=4 skip_conventions=1
echo A4_DONE
run ccb-12-13 ccb cc 12 13 kinds=braid skip_conventions=1
$PY scripts/run_pass.py cc cc 3 13 kinds=pd,braid,re procs=4 skip_conventions=1 shard_timeout=3600
$PY scripts/run_pass.py mu mu 3 13 kinds=pd,braid procs=4 skip_conventions=1 shard_timeout=3600
echo A5_DONE
run tw5-le11 tw5 tw 3 11 kinds=pd kmin=5 kmax=5 skip_conventions=1
echo A6_DONE
run tw6-le10 tw6 tw 3 10 kinds=pd kmin=6 kmax=6 skip_conventions=1
echo A7_DONE
run tw4-12-13 tw4 tw 12 13 kinds=pd kmin=4 kmax=4 skip_conventions=1
echo A8_DONE
echo QUEUE_A_DONE
