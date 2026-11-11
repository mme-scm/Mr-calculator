"""Run a move pass over shards (resumable).

usage: run_pass.py diagrams <tier-lo> <tier-hi>
       run_pass.py <pass-name> <move: cc|tw|mu> <tier-lo> <tier-hi> [kinds=pd,braid,re] [kmin=2] [kmax=2]
                   [nodes=<file with node names>] [procs=4] [budget=<seconds>]
Pass records go to data/passes/<pass-name>/<shard>.jsonl; finished shards are listed in done.txt.
"""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import config, identify as I, passes  # noqa: E402
from mrcalc.config import DATA  # noqa: E402


def braid_ok_map():
    out = {}
    p = os.path.join(DATA, 'table_checks.jsonl')
    with open(p) as f:
        for line in f:
            r = json.loads(line)
            for j, b in enumerate(r['braids']):
                out[(r['name'], j)] = bool(b.get('ok'))
    return out


def main():
    args = sys.argv[1:]
    kv = dict(a.split('=', 1) for a in args if '=' in a)
    pos = [a for a in args if '=' not in a]
    params = config.load_params()
    shards = passes.shard_nodes()
    procs = int(kv.get('procs', 4))
    budget = float(kv.get('budget', 1e9))
    t0 = time.time()
    if pos[0] == 'diagrams':
        lo, hi = int(pos[1]), int(pos[2])
        bok = braid_ok_map()
        todo = [(s, ns, int(kv.get('rediagrams', params['rediagrams'])), bok) for s, ns in shards.items()
                if lo <= passes.shard_tier(s) <= hi and not os.path.exists(passes.diag_path(s))]
        with mp.Pool(procs) as pool:
            for shard, n, errors in pool.imap_unordered(passes.build_diagram_shard, todo):
                if errors:
                    print('errors in', shard, errors[:3], flush=True)
        print('diagrams: %d shards in %.0fs' % (len(todo), time.time() - t0), flush=True)
        return
    pname, move, lo, hi = pos[0], pos[1], int(pos[2]), int(pos[3])
    opt = {'move': move, 'params': params, 'kinds': kv.get('kinds', 'pd,braid,re').split(','),
           'kmin': int(kv.get('kmin', 2)), 'kmax': int(kv.get('kmax', 2))}
    if 'nodes' in kv:
        with open(kv['nodes']) as f:
            opt['only_nodes'] = set(l.strip() for l in f if l.strip())
    done = passes.done_shards(pname)
    todo = [(pname, s, opt) for s in shards
            if lo <= passes.shard_tier(s) <= hi and s not in done and os.path.exists(passes.diag_path(s))]
    if 'only_nodes' in opt:
        todo = [t for t in todo if any(n in opt['only_nodes'] for n in shards[t[1]])]
    print('%s: %d shards to do' % (pname, len(todo)), flush=True)
    n = 0
    nrec = 0
    with mp.Pool(procs, maxtasksperchild=20) as pool:
        for pn, shard, recs, new_census, errors in pool.imap_unordered(passes.shard_task, todo):
            passes.write_shard(pn, shard, recs, errors)
            if new_census:
                with open(I.REF_CENSUS, 'a') as f:
                    for r in new_census:
                        f.write(json.dumps(r, separators=(',', ':')) + '\n')
            n += 1
            nrec += len(recs)
            if n % 5 == 0 or n == len(todo):
                print('  %s %d/%d shards, %d records, %.0fs' % (pname, n, len(todo), nrec, time.time() - t0),
                      flush=True)
            if time.time() - t0 > budget:
                print('budget reached, stopping', flush=True)
                pool.terminate()
                break
    print('%s done: %d shards, %d records, %.0fs' % (pname, n, nrec, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
