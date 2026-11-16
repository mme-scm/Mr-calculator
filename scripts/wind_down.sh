#!/bin/sh
# Wind-down of 2026-11-16 (the user: a taper by any definition).  No further passes are run.
#  1. final checkpoint `final` (scripts/orchestrate.sh full): sync of the staged data, convention tests,
#     calculator inputs, complexes, solve with chains, independent check, tests, STATE.md, commit; the full
#     export is published to mme-scm/Mr-export as the branch export/final.  The solve leaves the ablation base
#     in $ABL.
#  2. the ablation runs (after the fact; section 10 and the pass groups of config.PASS_ABLATIONS), started when
#     the solve of step 1 has exported: one at a time while the checkpoint is checked and tested, two at a time
#     afterwards.
#  3. final solve of u_Z, u_R, u_M on the same data, checked (checkpoints/u_final).
#  4. ablation.json and the ablation sheet of knots.xlsx are added to the export branch; REPORT.md (final);
#     commit.
# Log: logs/wind_down.log.  Markers: CHECKPOINT_DONE, U_DONE, ABLATION_DONE, WIND_DOWN_DONE / WIND_DOWN_FAILED.
cd /home/user/Mr-calculator
PY="/home/user/venv_sage/bin/python -W ignore"
SCR=/home/user/mrcalc_scratch
FLAGS=$SCR/flags
ABL=$SCR/abl
OUT=$SCR/full
EXP=/home/user/mr-export
BRANCH=claude/dreamy-hamilton-8i8dfx
TAIL="

Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GfGHdHRq15nAGeNaZqJMAq"
say() { echo "$(date -u '+%m-%d %H:%M') $*"; }
fail() { say "WIND_DOWN_FAILED $*"; exit 1; }
commit() {
  git add -A
  git diff --cached --quiet && return 0
  git commit -q -m "$1$TAIL"
  for w in 0 2 4 8 16; do sleep $w; git push -q -u origin $BRANCH && return 0; done
  say "PUSH FAILED"; return 1
}

say "wind-down started"
# ---- 1. final checkpoint
if [ ! -f $FLAGS/full_final ]; then
  rm -rf $ABL; mkdir -p $ABL; echo 1 > $ABL/procs
  touch $FLAGS/push_export
  SOLVE_EXTRA="ablation-base=$ABL" bash scripts/orchestrate.sh full final \
    "final checkpoint (wind-down): all pass data; every search stopped" >> logs/orchestrate.log 2>&1 &
  CKPID=$!
  until { [ -f $OUT/summary.json ] && [ -f $ABL/ablation_base.pkl ]; } || ! kill -0 $CKPID 2>/dev/null; do sleep 20; done
else
  CKPID=
fi
# ---- 2. ablation runs (resumes: the driver is not restarted when ablation.json is complete)
ABPID=
if [ ! -f $ABL/ABLATION_DONE ]; then
  [ -f $ABL/ablation_base.pkl ] || fail "no ablation base (the final solve did not finish)"
  say "final solve exported; ablation runs start"
  $PY scripts/solve.py ablate upsilon out=$ABL procs=1 > logs/ablation_final.log 2>&1 &
  ABPID=$!
fi
[ -n "$CKPID" ] && wait $CKPID
[ -f $FLAGS/full_final ] || fail "checkpoint final did not complete (logs/orchestrate.log)"
say "CHECKPOINT_DONE $(grep 'checkpoint final done' logs/orchestrate.log | tail -1 | cut -c13-200)"
[ -f $FLAGS/pushed_final ] && say "export published: mme-scm/Mr-export, branch export/final" \
                           || say "export NOT published (logs/push_export.log)"
# ---- 3. u_Z, u_R, u_M on the final data
if [ ! -f checkpoints/u_final/u_check.log ] || ! grep -q "RESULT: OK" checkpoints/u_final/u_check.log; then
  $PY scripts/solve_u.py out=$SCR/u_final > logs/solve_u_final.log 2>&1 || fail "u solve (logs/solve_u_final.log)"
  $PY checker/check_u.py $SCR/u_final > $SCR/u_final/u_check.log 2>&1 || fail "u checker ($SCR/u_final/u_check.log)"
  mkdir -p checkpoints/u_final
  for f in U_PINS.md u_check.log u_constraints.jsonl.gz u_constraints_M.jsonl.gz u_events_M.jsonl.gz \
           u_events_R.jsonl.gz u_events_Z.jsonl.gz u_knots.csv u_solve.log u_summary.json u_open.txt; do
    cp $SCR/u_final/$f checkpoints/u_final/
  done
  python3 scripts/u_open_table.py $SCR/u_final $OUT > checkpoints/u_final/u_open_ranges.txt || fail "u open table"
  commit "u_Z, u_R, u_M on the final data (checkpoints/u_final): $(grep -c . checkpoints/u_final/u_open_ranges.txt) knots open, checker OK"
fi
say "U_DONE $(grep -c . checkpoints/u_final/u_open_ranges.txt) knots open; $(grep RESULT checkpoints/u_final/u_check.log)"
# ---- 2b. the rest of the ablation, two runs at a time
echo 2 > $ABL/procs
if [ -n "$ABPID" ]; then
  wait $ABPID
  rc=$?
  [ $rc -eq 0 ] || say "ablation driver exit $rc (a run died: see logs/ablation_final.log)"
  touch $ABL/ABLATION_DONE
fi
[ -f $ABL/ablation.json ] || fail "no ablation.json"
say "ABLATION_DONE $(tail -1 logs/ablation_final.log)"
# ---- 4. ablation into the export, report, commit
cp $ABL/ablation.json $OUT/ablation.json
cp $ABL/ablation.json checkpoints/final/ablation.json
$PY -c "
import json, sys
sys.path.insert(0, '.')
from mrcalc import export
export.write_ablation_sheet('$OUT', json.load(open('$OUT/ablation.json')))
" || say "ablation sheet of knots.xlsx not written"
if [ -f $FLAGS/pushed_final ] && [ -d $EXP/.git ]; then
  ( cd $EXP && git checkout -q export/final && cp $OUT/ablation.json $OUT/knots.xlsx . \
    && sed -i 's/^- no ablation was run for this export$/- ablation (run after the export was first published): ablation.json and the sheet `ablation` of knots.xlsx/' README.md \
    && git add -A && git commit -q -m "Export final: ablation (ablation.json, sheet of knots.xlsx)$TAIL" \
    && for w in 0 5 20 60; do sleep $w; git push -q -u origin export/final && break; done \
    && [ "$(git rev-parse export/final)" = "$(git ls-remote origin refs/heads/export/final | cut -f1)" ] ) \
    && say "ablation added to the export branch" || say "ablation NOT added to the export branch"
fi
$PY scripts/report.py final export=$OUT "source=the export \`final\` (repository mme-scm/Mr-export, branch export/final; small tables in checkpoints/final/)" \
  > logs/report_final.log 2>&1 || say "report.py failed (logs/report_final.log)"
commit "Final report: ablation after the fact, REPORT.md and STATE.md from the final export"
say "WIND_DOWN_DONE"
