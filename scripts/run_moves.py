"""Run a move pass on diagram shards chosen by file-name prefix (shards that are not shards of core nodes:
the 'g2' diagrams of adjacent nodes and the re-diagram shards written by scripts/target_diagrams.py).
Same worker as scripts/run_pass.py (passes.shard_task): resumable per shard and per diagram.
usage: run_moves.py <pass-name> <cc|tw> <diagram shard prefix> kinds=<k,k> [kmin=2] [kmax=3] [imb_max=none]
                    [procs=2]"""
import json, multiprocessing as mp, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import config, identify as I, passes
args = sys.argv[1:]
kv = dict(a.split('=', 1) for a in args if '=' in a)
pos = [a for a in args if '=' not in a]
pname, move, prefix = pos
opt = {'move': move, 'params': config.load_params(), 'kinds': kv['kinds'].split(','),
       'kmin': int(kv.get('kmin', 2)), 'kmax': int(kv.get('kmax', 3))}
if 'imb_max' in kv:
    opt['imb_max'] = None if kv['imb_max'] == 'none' else int(kv['imb_max'])
shards = sorted({fn.split('.jsonl')[0] for fn in os.listdir(passes.DIAG_DIR) if fn.startswith(prefix)})
done = passes.done_shards(pname)
todo = [(pname, s, opt) for s in shards if s not in done]
print('%s: %d shards to do' % (pname, len(todo)), flush=True)
t0 = time.time(); nrec = 0
with mp.Pool(int(kv.get('procs', 2)), maxtasksperchild=6) as pool:
    for pn, shard, recs, new_census, errors in pool.imap_unordered(passes.shard_task, todo):
        passes.write_shard(pn, shard, recs, errors)
        passes.remove_partial(pn, shard)
        if new_census:
            with open(I.REF_CENSUS, 'a') as f:
                for r in new_census:
                    f.write(json.dumps(r, separators=(',', ':')) + '\n')
        nrec += len(recs)
        print('  %s %s: %d records, %d errors, %.0fs' % (pname, shard, len(recs), len(errors), time.time() - t0), flush=True)
print('%s done: %d records, %.0fs' % (pname, nrec, time.time() - t0), flush=True)
