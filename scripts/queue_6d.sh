#!/bin/sh
# Replaces queue_6c.sh (2026-11-12): the tw6 run of queue_A.sh stopped after 5 of 13 shards because a
# shard of 8-10 crossings takes longer than the default shard_timeout of run_pass.py (5400 s).
# Every run below resumes (only missing shards are computed) and waits up to a week for a shard (the largest tw6 shard has 68,668 records).
# Order: stage 6c passes, the rest of stage 6b (tw6), marker A7C_DONE, stage 7.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
while pgrep -f "scripts/run_pass.py" > /dev/null; do sleep 5; done
run() { echo "START $1 $(date -u +%H:%M)"; shift; $PY scripts/run_pass.py "$@" procs=4 nocomposite=1 skip_conventions=1 shard_timeout=604800 maxtasks=1; }
run tw3x-le13 tw3x tw 3 13 kinds=pd kmin=3 kmax=3 imb_min=3 imb_max=none
run tw4x-le13 tw4x tw 3 13 kinds=pd kmin=4 kmax=4 imb_min=3 imb_max=none
run tw5x-le11 tw5x tw 3 11 kinds=pd kmin=5 kmax=5 imb_min=3 imb_max=none
run tw6x-le10 tw6x tw 3 10 kinds=pd kmin=6 kmax=6 imb_min=3 imb_max=none
run tw6-le10-resume tw6 tw 3 10 kinds=pd kmin=6 kmax=6
if [ "$(ls $MRCALC_STAGE/passes/tw6/*.jsonl.gz | wc -l)" -lt 13 ]; then echo "6D: tw6 incomplete; stopping"; exit 1; fi
echo A7C_DONE
run tw4-12-13 tw4 tw 12 13 kinds=pd kmin=4 kmax=4
echo A8_DONE
echo QUEUE_A_DONE
