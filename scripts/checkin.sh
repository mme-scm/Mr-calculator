#!/bin/sh
# periodic check-in: sync staged pass shards into data/, re-solve (no chains, scratch export), update STATE.md
cd /home/user/Mr-calculator
PY="/home/user/venv_sage/bin/python -W ignore"
SCR=/home/user/mrcalc_scratch/checkin
mkdir -p $SCR
sh scripts/sync_stage.sh > /dev/null
$PY scripts/solve.py upsilon nochains out=$SCR > $SCR/solve.log 2>&1
$PY scripts/report.py state=$SCR > /dev/null 2>&1
grep -E "pins:|validation|EMPTY" $SCR/solve.log | cut -c1-220
grep -E "START|_DONE" logs/queue_A.log | tail -3
tail -1 logs/queue_A.log | cut -c1-120
