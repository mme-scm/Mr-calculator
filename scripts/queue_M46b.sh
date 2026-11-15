#!/bin/sh
# Mutants of the neighbours of the 46 knots (pass g2mu, diagrams g2x-*): crossing changes and k = 2, 3 twists
# from the mutant's diagram.  Rule F6 ties M and r_2 of a mutant to the neighbour.  Every step resumes.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
echo "START M46b $(date -u +%H:%M)"
$PY scripts/run_moves.py g2cc cc g2x kinds=g2 procs=2 maxtasks=4
$PY scripts/run_moves.py g2tw tw g2x kinds=g2 kmin=2 kmax=3 imb_max=none kbig=3 procs=2 maxtasks=1
echo M46B_DONE
