#!/bin/sh
# Face bands (rule N4 after a Reidemeister II move: passes.face_band_records) on the diagrams of the knots
# with u open (data/targets/u2_open.txt): pass bm6 on the KnotInfo PD diagrams and first braid closures,
# then on the re-diagrams and second braid closures of the targeted search.  Every step resumes.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
O=data/targets/u2_open.txt
cd /home/user/Mr-calculator
echo "START FB $(date -u +%H:%M)"
$PY scripts/run_moves.py bm6 fb t kinds=pd,braid0 only=$O procs=2 maxtasks=8
echo "FB table diagrams done $(date -u +%H:%M)"
for pk in "rdu re" "bvu b" "rd1 re" "rd2 re" "bv1 b"; do
  set -- $pk
  $PY scripts/run_moves.py bm6 fb $1 kinds=$2 only=$O procs=2 maxtasks=8
done
echo FB_DONE
