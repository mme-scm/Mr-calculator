#!/bin/sh
# copy finished pass shards from the staging directory into the repository
STAGE=/home/user/mrcalc_stage
cd /home/user/Mr-calculator
[ -d $STAGE/passes ] && cp -ru $STAGE/passes/. data/passes/
[ -f $STAGE/ref_census.jsonl ] && python3 scripts/split_refs.py $STAGE/ref_census.jsonl data/ref_census name
[ -f $STAGE/hfk_peripheral.jsonl ] && python3 scripts/split_refs.py $STAGE/hfk_peripheral.jsonl data/hfk_peripheral node
echo synced
find data/passes -name '*.tmp' -delete
