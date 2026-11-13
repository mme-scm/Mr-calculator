#!/bin/bash
# Watches the pass queue (logs/queue_A.log) and runs, without supervision:
#   * a full checkpoint (convention tests, calculator inputs, milestone 7, solve, ablation, packed export,
#     independent check, report, commit) at the milestones agreed with the user on 2026-11-11:
#     end of stage 3, of stages 4 and 5, of stage 6a, of stage 6b, of stage 7.  Stage 6c (twists with
#     |a - b| > 2, added 2026-11-12, scripts/queue_6c.sh) runs between 6b and 7 and belongs to the stage 6b
#     checkpoint, which therefore waits for A7C_DONE instead of A7_DONE;
#   * a light check-in (sync, commit of the pass data, re-solve without export, STATE.md) at the other
#     stage ends and every 3 hours, so that pass data are never more than 3 hours from being pushed.
# 2026-11-13: an extra full checkpoint (A6C_DONE, written by hand) after stage 6c and the repair of the surgery
# coincidences, because stage 6b lost 9 hours to a restart of the machine.
# An empty domain or a failed convention test stops this script (section 0): the minimal event/edge set is
# copied to export/contradiction, a flag file is written, nothing else is exported.
cd /home/user/Mr-calculator
PY="/home/user/venv_sage/bin/python -W ignore"
SCR=/home/user/mrcalc_scratch
FLAGS=$SCR/flags
BRANCH=claude/dreamy-hamilton-8i8dfx
mkdir -p $FLAGS
export MRCALC_STAGE_DIR=/home/user/mrcalc_stage
say() { echo "$(date -u '+%m-%d %H:%M') $*"; }

commit() {   # commit everything and push (retries on network failure)
  git add -A
  git diff --cached --quiet && return 0
  git commit -q -m "$1

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GfGHdHRq15nAGeNaZqJMAq"
  for w in 0 2 4 8 16; do sleep $w; git push -q -u origin $BRANCH && return 0; done
  say "PUSH FAILED"; return 1
}

conventions() {
  $PY -c "import sys; sys.path.insert(0,'.'); from mrcalc import conventions; conventions.assert_all(verbose=False); print('CONVENTIONS_OK')" \
     > $SCR/conventions.log 2>&1
  grep -q CONVENTIONS_OK $SCR/conventions.log
}

halt() {     # $1 label, $2 reason, $3 directory of the failed solve (optional)
  say "HALT $1: $2"
  if [ -n "$3" ] && [ -d "$3/contradiction" ]; then
    rm -rf export/contradiction; cp -r "$3/contradiction" export/contradiction
    conventions && echo "convention tests after the empty domain: all passed" > export/contradiction/conventions.txt \
                || cp $SCR/conventions.log export/contradiction/conventions.txt
    commit "Empty domain at $1: minimal event and edge set exported (export/contradiction); pipeline stopped"
  fi
  echo "$2" > $FLAGS/HALT_$1
  exit 1
}

light() {    # $1 label
  say "light check-in $1"
  sh scripts/sync_stage.sh all > /dev/null
  commit "Check-in ($1): pass data"
  conventions || halt $1 "convention tests failed"
  mkdir -p $SCR/checkin; rm -rf $SCR/checkin/contradiction
  $PY scripts/solve.py upsilon nochains out=$SCR/checkin > $SCR/checkin/solve.log 2>&1
  rc=$?
  [ $rc -eq 2 ] && halt $1 "empty domain" $SCR/checkin
  if [ $rc -eq 0 ]; then
    $PY scripts/report.py state=$SCR/checkin > /dev/null 2>&1
    commit "STATE after $1"
    say "light $1: $(grep pins: $SCR/checkin/solve.log | cut -c1-160)"
  else
    say "light $1: solve failed with exit $rc (not an empty domain)"
  fi
  date +%s > $FLAGS/last_sync
  echo ok > $FLAGS/light_$1
}

full() {     # $1 label, $2 description for the commit message
  say "full checkpoint $1"
  sh scripts/sync_stage.sh all > /dev/null
  commit "Checkpoint $1: pass data"
  date +%s > $FLAGS/last_sync
  conventions || halt $1 "convention tests failed"
  # calculator inputs of new peripheral knots (staged, resumable), then milestone 7 (capped at 90 minutes)
  MRCALC_STAGE=/home/user/mrcalc_stage $PY scripts/node_inputs.py timeout=60 procs=2 > logs/node_inputs_$1.log 2>&1
  sh scripts/sync_stage.sh inputs > /dev/null
  timeout -k 30 5400 $PY scripts/run_upsilon.py 60 60 > logs/upsilon_$1.log 2>&1
  commit "Checkpoint $1: calculator inputs and complexes"
  OUT=$SCR/full
  rm -rf $OUT; mkdir -p $OUT
  $PY scripts/solve.py upsilon ablation out=$OUT > $OUT/solve.log 2>&1
  rc=$?
  [ $rc -eq 2 ] && halt $1 "empty domain" $OUT
  [ $rc -ne 0 ] && { say "full $1: solve failed with exit $rc"; echo "solve exit $rc" > $FLAGS/FAILED_$1; return 1; }
  python3 checker/check.py $OUT > $OUT/check.log 2>&1
  rc=$?
  if [ $rc -ne 0 ] || ! grep -q "RESULT: OK" $OUT/check.log; then
    say "full $1: independent check FAILED (export not replaced)"; tail -25 $OUT/check.log
    echo "checker exit $rc" > $FLAGS/FAILED_$1; return 1
  fi
  cp export/FORMAT.md $OUT/FORMAT.md
  rm -rf export; cp -r $OUT export
  $PY -m pytest -q tests -x > $SCR/pytest_$1.log 2>&1; tail -1 $SCR/pytest_$1.log > export/tests.txt
  $PY scripts/report.py > /dev/null 2>&1
  commit "Checkpoint $1: $2

$(grep -E 'problem:|pins:|validation' export/solve.log | cut -c1-200)
independent check: $(grep RESULT export/check.log); tests: $(cat export/tests.txt)"
  say "full $1 done: $(grep pins: export/solve.log | cut -c1-160)"
  echo ok > $FLAGS/full_$1
}

handle() {   # marker name
  case $1 in
    A2_DONE) light stage2 ;;
    A3_DONE) full stage3 "end of stage 3 (k=3 twists on 13 crossings)" ;;
    A4_DONE) light stage4 ;;
    A5_DONE) full stage5 "end of stages 4 and 5 (k=4 on 9-11 crossings; braid-closure crossing changes, composites)" ;;
    A6_DONE) full stage6a "end of stage 6a (k=5 twists up to 11 crossings)" ;;
    A6C_DONE) full stage6c "end of stage 6c (twists with |a-b| > 2, k = 3..6); surgery coincidences repaired (full slope set, drilled redescriptions)" ;;
    A7C_DONE) full stage6b "end of stages 6b and 6c (k=6 twists up to 10 crossings; k=5, 6 twists with |a-b| > 2)" ;;
    A8_DONE) full stage7 "end of stage 7 (k=4 twists on 12-13 crossings)" ;;
  esac
}

[ -f $FLAGS/last_sync ] || date +%s > $FLAGS/last_sync
say "orchestrator started"
while true; do
  for m in A2_DONE A3_DONE A4_DONE A5_DONE A6_DONE A6C_DONE A7C_DONE A8_DONE; do
    if grep -q "^$m" logs/queue_A.log && [ ! -f $FLAGS/seen_$m ]; then
      touch $FLAGS/seen_$m
      handle $m
    fi
  done
  [ -f $FLAGS/seen_A8_DONE ] && { say "queue finished; orchestrator exits"; echo ok > $FLAGS/ALL_DONE; exit 0; }
  if [ $(( $(date +%s) - $(cat $FLAGS/last_sync) )) -gt 10800 ]; then
    light "$(date -u +%d-%H%M)"
  fi
  sleep 30
done
