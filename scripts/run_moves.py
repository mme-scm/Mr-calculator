"""Run a move pass on diagram shards chosen by file-name prefix (shards that are not shards of core nodes:
the 'g2' diagrams of adjacent nodes and the re-diagram shards written by scripts/target_diagrams.py).
Same worker as scripts/run_pass.py (passes.shard_task): resumable per shard and per diagram.
usage: run_moves.py <pass-name> <cc|tw> <diagram shard prefix> kinds=<k,k> [kmin=2] [kmax=3] [imb_max=none]
                    [procs=2] [maxtasks=2] [only=<file of node names>] [nmin=<crossings>] [kbig=<k>]
only= restricts the pass to the diagrams of the listed nodes (a name or its mirror), nmin= to diagrams with at
least that many crossings; shards without such a diagram are left out.  A shard done with a restriction stays
done for that pass name, so a later, wider selection needs a new pass name.
kbig= replaces the scope parameter k_max['>20'] (specification value 0: no twists on diagrams with more than
20 crossings) for this pass; the widening is reported in the run notes."""
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
if 'only' in kv:
    names = {l.strip() for l in open(kv['only']) if l.strip()}
    opt['only_nodes'] = names | {n[:-1] if n.endswith('*') else n + '*' for n in names}
if 'nmin' in kv:
    opt['n_min'] = int(kv['nmin'])
if 'kbig' in kv:
    opt['params'] = dict(opt['params'], k_max=dict(opt['params']['k_max'], **{'>20': int(kv['kbig'])}))
shards = sorted({fn.split('.jsonl')[0] for fn in os.listdir(passes.DIAG_DIR) if fn.startswith(prefix)})
done = passes.done_shards(pname)
if 'only_nodes' in opt or 'n_min' in opt:
    def wanted(d):
        return (any(d['kind'] == k or d['kind'].startswith(k) for k in opt['kinds'])
                and ('only_nodes' not in opt or d['node'] in opt['only_nodes'])
                and ('n_min' not in opt or d['n'] >= opt['n_min']))
    shards = [s for s in shards if s in done or any(wanted(d) for d in passes.load_diagrams(s))]
todo = [(pname, s, opt) for s in shards if s not in done]
print('%s: %d shards to do' % (pname, len(todo)), flush=True)
t0 = time.time(); nrec = 0
with mp.Pool(int(kv.get('procs', 2)), maxtasksperchild=int(kv.get('maxtasks', 2))) as pool:
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
