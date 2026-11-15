#!/bin/sh
# After the moves, mutations and fillings for the neighbours of the 46 knots (queue_M46, queue_M46b, the
# coincidence run) and the chirality re-verification have finished: apply the chirality corrections, put the
# new coincidence records into the data, ask the orchestrator for a light check-in, then solve u_Z / u_R on
# the synced data and check the result.
cd /home/user/Mr-calculator
S=/home/user/mrcalc_scratch
PY="/home/user/venv_sage/bin/python -W ignore"
until grep -q "^M46_MOVES_DONE" logs/queue_M46.log 2>/dev/null && grep -q "^M46B_DONE" logs/queue_M46b.log 2>/dev/null \
   && grep -q "^COINC_X_DONE" $S/coincMx.log 2>/dev/null && grep -q "^U2_DONE" logs/queue_U2.log 2>/dev/null \
   && grep -q "^CHECK_DONE" $S/repair/chir_main.log 2>/dev/null; do sleep 60; done
echo "CHAIN start $(date -u +%H:%M)"
MRCALC_STAGE=/home/user/mrcalc_stage $PY scripts/verify_chirality.py apply $S/repair/chir_main.jsonl
for f in coincidences.jsonl filling_usig.jsonl filling_signatures.jsonl filling_isometries.jsonl; do
  cp $S/coincM/$f data/$f.tmp && mv data/$f.tmp data/$f
done
wc -l data/coincidences.jsonl
n0=$(ls $S/flags | grep -c "^light_")
touch $S/flags/request_light
until [ "$(ls $S/flags | grep -c '^light_')" != "$n0" ]; do sleep 60; done
echo "CHAIN light check-in done $(date -u +%H:%M)"
rm -rf $S/u2
$PY scripts/solve_u.py out=$S/u2 > $S/u2.log 2>&1
echo "solve_u exit $?"
/home/user/venv/bin/python checker/check_u.py $S/u2 > $S/u2/u_check.log 2>&1
echo "check_u exit $?"
echo CHAIN_M46_DONE
