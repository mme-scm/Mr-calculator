#!/bin/sh
# Band moves (rule N4, RULES_U.md): the smoothing that gives a knot, at every crossing of
#   bm1  the KnotInfo PD diagram of every table knot,
#   bm2  the first braid-closure diagram of every table knot,
#   bm3  the re-diagrams and the second braid-closure diagrams built by the targeted search,
#   bm4  the diagrams of the torus nodes outside the table (those of composite nodes would repeat bm1).
# Every step resumes.  The passes are read by scripts/solve_u.py only.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
echo "START U $(date -u +%H:%M)"
$PY scripts/run_moves.py bm1 bm t kinds=pd procs=2 maxtasks=8
echo "bm1 finished $(date -u +%H:%M)"
$PY scripts/run_moves.py bm2 bm t kinds=braid0 procs=2 maxtasks=8
echo "bm2 finished $(date -u +%H:%M)"
$PY scripts/run_moves.py bm3 bm rd kinds=re procs=2 maxtasks=8
$PY scripts/run_moves.py bm3 bm bv kinds=braidv procs=2 maxtasks=8
echo "bm3 finished $(date -u +%H:%M)"
$PY scripts/run_moves.py bm4 bm x-torus kinds=pd,re procs=2 maxtasks=8
echo U_DONE
