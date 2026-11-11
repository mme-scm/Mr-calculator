#!/bin/sh
# copy finished pass shards from the staging directory into the repository
STAGE=/home/user/mrcalc_stage
cd /home/user/Mr-calculator
[ -d $STAGE/passes ] && cp -ru $STAGE/passes/. data/passes/
[ -f $STAGE/ref_census.jsonl ] && cp $STAGE/ref_census.jsonl data/ref_census.jsonl
echo synced
find data/passes -name '*.tmp' -delete
