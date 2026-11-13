#!/bin/sh
# Publishes a full export (solved with chains and verified by the independent checker) to the export repository
# mme-scm/Mr-export, as the branch export/<label> with no earlier history, so that the repository grows by the
# size of the export and no more.  The files are committed and pushed in groups below about 400 MB (one push of
# the whole export would be over 1 GB).  main carries a README that lists the export branches.
# usage: push_export.sh <label> [<export dir, default /home/user/mrcalc_scratch/full>] [<clone, default /home/user/mr-export>]
# Nothing is pushed anywhere else.  A failure leaves the main repository untouched (exit status 1).
LABEL=$1
SRC=${2:-/home/user/mrcalc_scratch/full}
DST=${3:-/home/user/mr-export}
ROOT=/home/user/Mr-calculator
[ -n "$LABEL" ] && [ -f $SRC/knots.jsonl.gz ] && grep -q "RESULT: OK" $SRC/check.log || { echo "push_export: no checked export in $SRC"; exit 1; }
[ -d $DST/.git ] || { echo "push_export: no clone at $DST"; exit 1; }
BR=export/$LABEL
SHA=$(git -C $ROOT rev-parse HEAD)
push() {     # $1 branch
  for w in 0 5 20 60; do
    sleep $w
    git -C $DST -c push.negotiate=true push -q -u origin $1 2>&1 | grep -v "push negotiation failed" | tail -2
    [ "$(git -C $DST rev-parse $1 2>/dev/null)" = "$(git -C $DST rev-parse origin/$1 2>/dev/null)" ] && return 0
  done
  echo "push_export: push of $1 failed"; return 1
}
cd $DST || exit 1
git config user.name > /dev/null || git config user.name "$(git -C $ROOT config user.name)"
git config user.email > /dev/null || git config user.email "$(git -C $ROOT config user.email)"
git checkout -q --orphan $BR 2>/dev/null || { echo "push_export: branch $BR exists already"; exit 1; }
git rm -rq --cached . 2>/dev/null; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
MSGTAIL="
Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GfGHdHRq15nAGeNaZqJMAq"
# --- small files first: the description of the export
cp $ROOT/export/FORMAT.md . 2>/dev/null
for f in parameters.json pins_by_tier.json summary.json solve.log check.log knots.xlsx; do [ -f $SRC/$f ] && cp $SRC/$f .; done
[ -f $ROOT/checkpoints/$LABEL/PINS.md ] && cp $ROOT/checkpoints/$LABEL/PINS.md .
[ -f $ROOT/checkpoints/$LABEL/tests.txt ] && cp $ROOT/checkpoints/$LABEL/tests.txt .
[ -f $SRC/ablation.json ] && cp $SRC/ablation.json .
{
  echo "# Export \`$LABEL\`"
  echo
  echo "Full export of the constraint-propagation run (format: FORMAT.md) at checkpoint \`$LABEL\`,"
  echo "built from mme-scm/Mr-calculator at commit $SHA on $(date -u '+%Y-%m-%d %H:%M') UTC."
  echo
  echo "- $(grep -E '^pins:' solve.log | head -1 | cut -c1-200)"
  echo "- independent check: $(grep RESULT check.log)"
  [ -f tests.txt ] && echo "- tests: $(cat tests.txt)"
  [ -f ablation.json ] && echo "- ablation: ablation.json" || echo "- no ablation was run for this export"
  echo
  [ -f PINS.md ] && sed -n '3,$p' PINS.md
} > README.md
git add -A && git commit -q -m "Export $LABEL: description, parameters, tables$MSGTAIL" && push $BR || exit 1
# --- the large files, in groups
group() {    # $1 name, rest: files relative to $SRC
  name=$1; shift
  n=0
  for f in "$@"; do [ -e "$SRC/$f" ] || continue; mkdir -p "$(dirname "$f")"; cp -r "$SRC/$f" "$f"; n=$((n+1)); done
  [ $n -eq 0 ] && return 0
  git add -A && git commit -q -m "Export $LABEL: $name$MSGTAIL" && push $BR
}
cd $DST
group "nodes" knots.jsonl.gz $(cd $SRC && ls knots*.csv 2>/dev/null) || exit 1
group "peripheral nodes (xlsx)" $(cd $SRC && ls knots_peripheral*.xlsx 2>/dev/null) || exit 1
group "certificates" certificates || exit 1
group "constraints" $(cd $SRC && ls constraints*.jsonl* 2>/dev/null) || exit 1
group "edges" $(cd $SRC && ls edges*.jsonl* 2>/dev/null) || exit 1
group "events" $(cd $SRC && ls events*.jsonl* 2>/dev/null) || exit 1
# chains: archives in groups of about 300 MB
( cd $SRC && ls chains 2>/dev/null ) > /tmp/push_export_chains.$$
size=0; batch=""; k=1
while read f; do
  s=$(du -sm "$SRC/chains/$f" | cut -f1)
  if [ $((size + s)) -gt 300 ] && [ -n "$batch" ]; then group "chains ($k)" $batch || exit 1; batch=""; size=0; k=$((k+1)); fi
  batch="$batch chains/$f"; size=$((size + s))
done < /tmp/push_export_chains.$$
[ -n "$batch" ] && { group "chains ($k)" $batch || exit 1; }
rm -f /tmp/push_export_chains.$$
# --- main: the list of export branches
git checkout -q main 2>/dev/null || git checkout -q --orphan main
git rm -rq --cached . 2>/dev/null; find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
git show origin/main:README.md > README.md 2>/dev/null || {
  echo "# Mr-export"; echo
  echo "Full exports of the run in mme-scm/Mr-calculator, one branch per export (\`export/<label>\`), each without"
  echo "earlier history. The format is described in FORMAT.md on every branch; README.md on a branch says what it holds."
  echo; echo "| branch | built (UTC) | Mr-calculator commit | pins (all nodes) |"; echo "|---|---|---|---|"; } > README.md
echo "| \`$BR\` | $(date -u '+%Y-%m-%d %H:%M') | $(echo $SHA | cut -c1-10) | $(git show $BR:solve.log | grep -E '^pins:' | head -1 | cut -c7-160) |" >> README.md
git add -A && git commit -q -m "Export $LABEL listed$MSGTAIL" && push main || exit 1
echo "push_export: $BR published ($(du -sh $SRC | cut -f1))"
