#!/bin/sh
# More diagrams of the knots whose u_Z / u_R is not determined (data/targets/u1_open.txt, from the solve of
# 2026-11-15), with all three kinds of moves on them: re-diagrams re1..re12 (those that do not exist yet) and a
# second braid closure of any length up to 60; crossing changes (ccR), k = 2, 3 twists with every |a-b| and no
# limit on the diagram's crossings (twB), band moves (bm3).  46 of the 48 knots also have M open.
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
O=data/targets/u1_open.txt
echo "START U2 $(date -u +%H:%M)"
ls data/diagrams | grep -q "^rdu-" || $PY scripts/target_diagrams.py re $O rdu n=12 chunk=40
ls data/diagrams | grep -q "^bvu-" || $PY scripts/target_diagrams.py bv $O bvu maxlen=60 chunk=60
for pre in rdu bvu; do
  k=re; [ $pre = bvu ] && k=braidv
  $PY scripts/run_moves.py bm3 bm $pre kinds=$k procs=2 maxtasks=8
  $PY scripts/run_moves.py ccR cc $pre kinds=$k procs=2 maxtasks=8
  $PY scripts/run_moves.py twB tw $pre kinds=$k kmin=2 kmax=3 imb_max=none kbig=3 procs=2 maxtasks=1
done
echo U2_DONE
