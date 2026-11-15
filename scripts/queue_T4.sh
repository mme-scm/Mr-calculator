#!/bin/sh
# Targeted search, round 4 (after round 3, scripts/queue_T3.sh): targets from a light check-in that contains
# round 3, then, with a light check-in requested after each step so that each step's yield can be read off:
#  0. k = 2, 3 twists with every |a-b| from a diagram of the 3,000 adjacent nodes outside the table that
#     decide the most M-open knots (pass g2tw; so far only the pilot at <= 11 crossings ran it).  First,
#     because round 3's twists on the second braid closures with at most 20 crossings pinned no M in the core.
#  1. k = 4 twists with every |a-b| on the two braid-closure diagrams (braid0, braidv0; at most 20 crossings)
#     of the knots whose M is open (pass twB4).  Until now k = 4 used the KnotInfo PD diagram only (stage 7).
#  2. k = 2, 3 twists with every |a-b| on the second braid-closure diagrams with more than 20 crossings (pass
#     twL).  The scope parameter k_max['>20'] = 0 kept the twist passes of rounds 1-3 off every diagram with
#     more than 20 crossings (906 of the 1,600 second braid closures, 2,051 of the 7,506 re-diagrams).
#  3. as step 0 on the re-diagrams with more than 20 crossings of the M-open knots (pass twL).
#  4. k = 4 twists on the re-diagrams (at most 20 crossings) of the M-open knots (pass twB4).
# Every step resumes.  The selections are budget choices (run notes).
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
SCR=/home/user/mrcalc_scratch
cd /home/user/Mr-calculator
light() {
  n0=$(ls $SCR/flags | grep -c "^light_")
  touch $SCR/flags/request_light
  until [ "$(ls $SCR/flags | grep -c '^light_')" != "$n0" ]; do sleep 60; done
}
until grep -q "^T3_DONE" logs/queue_T3.log 2>/dev/null; do sleep 60; done
echo "START T4 $(date -u +%H:%M)"
if [ ! -f data/targets/r4_sel.txt ]; then
  light
  for inv in M tau upsilon; do
    /home/user/venv/bin/python scripts/targets.py $SCR/checkin data/targets/r4_$inv tmax=13 inv=$inv || exit 1
  done
  cat data/targets/r4_M_open.txt data/targets/r4_tau_open.txt data/targets/r4_upsilon_open.txt | sort -u > data/targets/r4_open_all.txt
  /home/user/venv/bin/python scripts/select_adjacent.py data/targets/r4_M_adjacent.jsonl data/targets/r4_sel n=3000 || exit 1
fi
O=data/targets/r4_M_open.txt
A=data/targets/r4_open_all.txt
$PY scripts/target_diagrams.py g2 data/targets/r4_sel.jsonl g2c chunk=250
$PY scripts/run_moves.py g2tw tw g2 kinds=g2 kmin=2 kmax=3 imb_max=none only=data/targets/r4_sel.txt procs=2 maxtasks=1
echo "T4 step 0 done $(date -u +%H:%M)"; light
$PY scripts/run_moves.py twB4 tw bv1 kinds=braidv kmin=4 kmax=4 imb_max=none only=$O procs=2 maxtasks=1
$PY scripts/run_moves.py twB4 tw t kinds=braid0 kmin=4 kmax=4 imb_max=none only=$O procs=2 maxtasks=4
echo "T4 step 1 done $(date -u +%H:%M)"; light
$PY scripts/run_moves.py twL tw bv1 kinds=braidv kmin=2 kmax=3 imb_max=none nmin=21 kbig=3 only=$A procs=2 maxtasks=1
echo "T4 step 2 done $(date -u +%H:%M)"; light
$PY scripts/run_moves.py twL tw rd kinds=re kmin=2 kmax=3 imb_max=none nmin=21 kbig=3 only=$O procs=2 maxtasks=1
echo "T4 step 3 done $(date -u +%H:%M)"; light
$PY scripts/run_moves.py twB4 tw rd kinds=re kmin=4 kmax=4 imb_max=none only=$O procs=2 maxtasks=1
echo T4_DONE
touch $SCR/flags/request_light
