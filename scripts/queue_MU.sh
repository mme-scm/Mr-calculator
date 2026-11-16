#!/bin/sh
# Mutants of the knots with u open themselves: mutations (Conway circles) on every other diagram of them
# (re-diagrams, both braid closures); the mu pass used the KnotInfo PD diagram only.  Pass muR.  Resumes.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
O=data/targets/u2_open.txt
echo "START MU $(date -u +%H:%M)"
for pre in rdu bvu rd1 rd2 bv1; do
  k=re; case $pre in bv*) k=braidv;; esac
  $PY scripts/run_moves.py muR mu $pre kinds=$k only=$O procs=1 maxtasks=8
done
$PY scripts/run_moves.py muR mu t kinds=braid0 only=$O procs=1 maxtasks=8
echo MU_DONE
