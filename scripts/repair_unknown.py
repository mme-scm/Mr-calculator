"""Re-identify the 'unknown' results of a pass (after an identification-service fix).
usage: repair_unknown.py <pass-name> [procs]"""
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import passes  # noqa: E402


def fix(args):
    pname, shard = args
    recs = passes.read_shard(pname, shard)
    if not any(r.get('kind') == 'unknown' for r in recs):
        passes.rewrite_shard(pname, shard, recs)
        return shard, 0, 0
    diags = {d['id']: d for d in passes.load_diagrams(shard)}
    idr = passes.identifier()
    n = fixed = 0
    for r in recs:
        if r.get('kind') != 'unknown':
            continue
        n += 1
        new = passes.result_pd(diags[r['d']]['pd'], r)
        res = idr.identify(new)
        if res['name'] is not None:
            r['dst'], r['kind'], r['cert'] = res['name'], res['kind'], res['cert']
            fixed += 1
        else:
            r['cert'] = res['cert']
    passes.rewrite_shard(pname, shard, recs)
    return shard, n, fixed


if __name__ == '__main__':
    pname = sys.argv[1]
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    shards = sorted(passes.done_shards(pname))
    tot = totf = 0
    with mp.Pool(procs) as pool:
        for shard, n, fixed in pool.imap_unordered(fix, [(pname, s) for s in shards]):
            tot += n
            totf += fixed
    print('%s: %d unknown results re-examined, %d identified' % (pname, tot, totf))
