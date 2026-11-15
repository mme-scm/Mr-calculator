#!/bin/sh
# Follow-up of the work on the neighbours of the 46 knots, in two phases.
#  Phase 1, when the chirality re-verification, the mutant passes (queue_M46b) and the second coincidence run
#  have finished: apply the chirality corrections, put the new coincidence records into the data, ask the
#  orchestrator for a light check-in, then solve u_Z / u_R on the synced data and check the result (scratch u2).
#  Phase 2, when the twists from the neighbours (queue_M46) and the extra diagrams of the 48 knots (queue_U2)
#  have finished: another light check-in and u solve (scratch u3).
cd /home/user/Mr-calculator
S=/home/user/mrcalc_scratch
PY="/home/user/venv_sage/bin/python -W ignore"
light() {
  n0=$(ls $S/flags | grep -c "^light_")
  touch $S/flags/request_light
  until [ "$(ls $S/flags | grep -c '^light_')" != "$n0" ]; do sleep 60; done
}
usolve() {
  rm -rf $S/$1
  $PY scripts/solve_u.py out=$S/$1 > $S/$1.log 2>&1
  echo "solve_u $1 exit $?"
  /home/user/venv/bin/python checker/check_u.py $S/$1 > $S/$1/u_check.log 2>&1
  echo "check_u $1 exit $?"
}
if ! grep -q "^PHASE1_DONE" logs/chain_M46.log 2>/dev/null; then
  until grep -q "^M46B_DONE" logs/queue_M46b.log 2>/dev/null && grep -q "^COINC_X_DONE" $S/coincMx.log 2>/dev/null \
     && grep -q "^CHECK_DONE" $S/repair/chir_main.log 2>/dev/null; do sleep 60; done
  echo "CHAIN phase 1 start $(date -u +%H:%M)"
  MRCALC_STAGE=/home/user/mrcalc_stage $PY scripts/verify_chirality.py apply $S/repair/chir_main.jsonl
  for f in coincidences.jsonl filling_usig.jsonl filling_signatures.jsonl filling_isometries.jsonl; do
    cp $S/coincM/$f data/$f.tmp && mv data/$f.tmp data/$f
  done
  wc -l data/coincidences.jsonl
  light
  echo "CHAIN phase 1 check-in done $(date -u +%H:%M)"
  usolve u2
  echo PHASE1_DONE
fi
until grep -q "^M46_MOVES_DONE" logs/queue_M46.log 2>/dev/null && grep -q "^U2_DONE" logs/queue_U2.log 2>/dev/null; do sleep 60; done
echo "CHAIN phase 2 start $(date -u +%H:%M)"
light
echo "CHAIN phase 2 check-in done $(date -u +%H:%M)"
usolve u3
echo CHAIN_M46_DONE
