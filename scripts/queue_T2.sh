#!/bin/sh
# Targeted search, round 2 (after round 1, scripts/queue_T1.sh): targets for M, tau and upsilon from a light
# check-in that contains round 1, then
#  1. diagrams (kind g2) and crossing changes (pass g2cc) for the adjacent nodes outside the table that have
#     no diagram yet;
#  2. three seeded re-diagrams of every open knot that has none (12-13 crossings), crossing changes on them
#     (pass ccR) and k = 2, 3 twists with every |a-b| (pass twB).
# Every step resumes.  No solve is started here (memory): the orchestrator is asked for a light check-in.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
SCR=/home/user/mrcalc_scratch
cd /home/user/Mr-calculator
until grep -q "^T1_DONE" logs/queue_T1.log 2>/dev/null; do sleep 60; done
echo "START T2 $(date -u +%H:%M)"
if [ ! -f data/targets/r2_upsilon_open.txt ]; then
  n0=$(ls $SCR/flags | grep -c "^light_")
  touch $SCR/flags/request_light
  until [ "$(ls $SCR/flags | grep -c '^light_')" != "$n0" ]; do sleep 60; done
  for inv in M tau upsilon; do
    /home/user/venv/bin/python scripts/targets.py $SCR/checkin data/targets/r2_$inv tmax=13 inv=$inv || exit 1
  done
fi
for inv in M tau upsilon; do $PY scripts/target_diagrams.py g2 data/targets/r2_${inv}_adjacent.jsonl g2b chunk=500; done
$PY scripts/run_moves.py g2cc cc g2b kinds=g2 procs=2
cat data/targets/r2_M_open.txt data/targets/r2_tau_open.txt data/targets/r2_upsilon_open.txt | sort -u > data/targets/r2_open_all.txt
$PY scripts/target_diagrams.py re data/targets/r2_open_all.txt rd1 n=3 chunk=40
$PY scripts/run_moves.py ccR cc rd1 kinds=re procs=3
$PY scripts/run_moves.py twB tw rd1 kinds=re kmin=2 kmax=3 imb_max=none procs=3
echo T2_DONE
