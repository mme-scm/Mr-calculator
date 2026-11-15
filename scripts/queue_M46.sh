#!/bin/sh
# M at the knots whose u_Z is not determined (user, 2026-11-15: use what M has and u_Z has not, mutation and
# surgery coincidences).  The 46 knots of data/targets/u1_open.txt with M open have 2,434 neighbours whose M
# would decide one of them (data/targets/m46_adjacent.jsonl, from the targets of round 4).  For those
# neighbours outside the table, on the result diagram of the move that produced them (kind g2):
#   g2mu  mutations (rule F6 edges to their mutants),
#   g2cc  crossing changes,
#   g2tw  k = 2, 3 twists with every |a-b|, no limit on the diagram's crossings.
# The surgery fillings of the same nodes are computed separately (scratch; data/targets/m46_fill_index.jsonl).
# Starts after the chirality re-verification (scripts/verify_chirality.py) has finished.  Every step resumes.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
until grep -q "^CHECK_DONE" /home/user/mrcalc_scratch/repair/chir_main.log 2>/dev/null; do sleep 60; done
echo "START M46 $(date -u +%H:%M)"
A=data/targets/m46_adjacent.txt
ls data/diagrams | grep -q "^g2m-" || $PY scripts/target_diagrams.py g2 data/targets/m46_adjacent.jsonl g2m chunk=250
$PY scripts/run_moves.py g2mu mu g2 kinds=g2 only=$A procs=3 maxtasks=4
echo "M46 mutations done $(date -u +%H:%M)"
$PY scripts/run_moves.py g2cc cc g2m kinds=g2 procs=3 maxtasks=4
$PY scripts/run_moves.py g2tw tw g2 kinds=g2 kmin=2 kmax=3 imb_max=none kbig=3 only=$A procs=3 maxtasks=1
echo M46_MOVES_DONE
