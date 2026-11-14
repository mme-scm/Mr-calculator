#!/bin/sh
# Targeted search, round 3 (after round 2, scripts/queue_T2.sh): targets for M, tau and upsilon from a light
# check-in that contains round 2, then
#  1. a second braid-closure diagram (kind braidv0: the braid word spherogram derives from the KnotInfo PD
#     diagram) of every open knot, crossing changes on it (pass ccR) and k = 2, 3 twists with every |a-b|
#     (pass twB).  Braid closures were the most productive diagrams of rounds 1 and 2;
#  2. three further re-diagrams (re4..re6) of the knots whose M is open, with the same two passes.
# Every step resumes.  No solve is started here: the orchestrator is asked for a light check-in.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
SCR=/home/user/mrcalc_scratch
cd /home/user/Mr-calculator
until grep -q "^T2_DONE" logs/queue_T2.log 2>/dev/null; do sleep 60; done
echo "START T3 $(date -u +%H:%M)"
if [ ! -f data/targets/r3_upsilon_open.txt ]; then
  n0=$(ls $SCR/flags | grep -c "^light_")
  touch $SCR/flags/request_light
  until [ "$(ls $SCR/flags | grep -c '^light_')" != "$n0" ]; do sleep 60; done
  for inv in M tau upsilon; do
    /home/user/venv/bin/python scripts/targets.py $SCR/checkin data/targets/r3_$inv tmax=13 inv=$inv || exit 1
  done
fi
cat data/targets/r3_M_open.txt data/targets/r3_tau_open.txt data/targets/r3_upsilon_open.txt | sort -u > data/targets/r3_open_all.txt
$PY scripts/target_diagrams.py bv data/targets/r3_open_all.txt bv1 maxlen=32 chunk=120
$PY scripts/run_moves.py ccR cc bv1 kinds=braidv procs=3
$PY scripts/run_moves.py twB tw bv1 kinds=braidv kmin=2 kmax=3 imb_max=none procs=3
$PY scripts/target_diagrams.py re data/targets/r3_M_open.txt rd2 n=6 chunk=40
$PY scripts/run_moves.py ccR cc rd2 kinds=re procs=3
$PY scripts/run_moves.py twB tw rd2 kinds=re kmin=2 kmax=3 imb_max=none procs=3
echo T3_DONE
