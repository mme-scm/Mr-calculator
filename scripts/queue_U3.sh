#!/bin/sh
# Moves from the neighbours whose value would decide one of the 46 knots with u open (data/targets/
# u2_adjacent.jsonl, from the solve of 2026-11-16) and from the mutants of neighbours (g2x diagrams):
#   bm5   band moves (rule N4) on their g2 diagrams (band moves had only been computed on diagrams of table knots),
#   g2mv  mutations of the neighbours the M search did not cover (pass g2mu covered the M neighbours),
#   g2cc, g2tw  crossing changes and k = 2, 3 twists from the diagrams built here (g2u).
# Every step resumes.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
echo "START U3 $(date -u +%H:%M)"
ls data/diagrams | grep -q "^g2u-" || $PY scripts/target_diagrams.py g2 data/targets/u2_adjacent.jsonl g2u chunk=250
$PY scripts/run_moves.py bm5 bm g2 kinds=g2 only=data/targets/u2_band_nodes.txt procs=2 maxtasks=8
echo "U3 band moves done $(date -u +%H:%M)"
$PY scripts/run_moves.py g2mv mu g2 kinds=g2 only=data/targets/u2_adjacent_new.txt procs=2 maxtasks=4
$PY scripts/run_moves.py g2cc cc g2u kinds=g2 procs=2 maxtasks=4
$PY scripts/run_moves.py g2tw tw g2u kinds=g2 kmin=2 kmax=3 imb_max=none kbig=3 procs=2 maxtasks=1
echo U3_DONE
