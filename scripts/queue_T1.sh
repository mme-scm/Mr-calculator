#!/bin/sh
# Targeted search for M, round 1 (2026-11-13; lists data/targets/r1_*: the state after the pilot).
#  1. diagrams of the adjacent nodes outside the table (kind g2) and crossing changes on them (pass g2cc);
#  2. k = 2, 3 twists with every |a-b| on the braid-closure diagrams of the open knots with 12-13 crossings
#     (pass twB).
# Every step resumes (finished shards are skipped, an unfinished shard continues after its last diagram).
export MRCALC_STAGE=/home/user/mrcalc_stage
PY="/home/user/venv_sage/bin/python -W ignore"
cd /home/user/Mr-calculator
echo "START T1 $(date -u +%H:%M)"
$PY scripts/target_diagrams.py g2 data/targets/r1_adjacent.jsonl g2a chunk=500
$PY scripts/run_moves.py g2cc cc g2a kinds=g2 procs=2
$PY scripts/run_pass.py twB tw 12 13 kinds=braid kmin=2 kmax=3 imb_max=none nodes=data/targets/r1_open.txt procs=3 nocomposite=1 skip_conventions=1 shard_timeout=604800
echo T1_DONE
