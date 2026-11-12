#!/bin/sh
# Stage 6c (requested 2026-11-12): full twists with |a - b| > 2, k = 5 on diagrams with at most 11
# crossings and k = 6 on diagrams with at most 10 crossings (passes tw5x, tw6x; the passes tw5, tw6 of
# stages 6a, 6b keep |a - b| <= 2).  Inserted between stage 6b and stage 7: waits for A7_DONE, stops
# queue_A.sh (which has just started stage 7; passes are resumable), runs the two passes, writes A7C_DONE
# and then runs stage 7 itself.  Output is appended to logs/queue_A.log, which the orchestrator watches.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until grep -q "^A7_DONE" logs/queue_A.log; do sleep 5; done
pkill -TERM -f "sh scripts/queue_A.sh"
sleep 3
pkill -TERM -f "run_pass.py tw4 tw 12 13"; sleep 5; pkill -KILL -f "run_pass.py tw4 tw 12 13"
sleep 2
if pgrep -f "scripts/queue_A.sh|scripts/run_pass.py" > /dev/null; then echo "6C: queue A still running; not started"; exit 1; fi
run() { echo "START $1 $(date -u +%H:%M)"; shift; $PY scripts/run_pass.py "$@" procs=4 nocomposite=1; }
run tw5x-le11 tw5x tw 3 11 kinds=pd kmin=5 kmax=5 imb_min=3 imb_max=none
run tw6x-le10 tw6x tw 3 10 kinds=pd kmin=6 kmax=6 imb_min=3 imb_max=none skip_conventions=1
echo A7C_DONE
run tw4-12-13 tw4 tw 12 13 kinds=pd kmin=4 kmax=4 skip_conventions=1
echo A8_DONE
echo QUEUE_A_DONE
