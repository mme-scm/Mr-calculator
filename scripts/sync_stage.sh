#!/bin/sh
# copy staged results into the repository.  usage: sync_stage.sh [all|inputs]
#   all (default): finished pass shards, census references, calculator inputs of peripheral knots
#   inputs: only the census references and calculator inputs (the pass data stay at their last snapshot)
STAGE=/home/user/mrcalc_stage
cd /home/user/Mr-calculator
if [ "${1:-all}" = "all" ]; then
  [ -d $STAGE/passes ] && cp -ru $STAGE/passes/. data/passes/
  find data/passes -name '*.tmp' -delete
fi
[ -f $STAGE/ref_census.jsonl ] && python3 scripts/split_refs.py $STAGE/ref_census.jsonl data/ref_census name
[ -f $STAGE/hfk_peripheral.jsonl ] && python3 scripts/split_refs.py $STAGE/hfk_peripheral.jsonl data/hfk_peripheral node
echo synced
