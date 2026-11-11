"""Surgery pass over shards (resumable).
usage: run_fillings.py <tier-lo> <tier-hi> [procs=4] [p=30] [q=4] [time_limit=2] [budget=sec]"""
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import config, fillings as F, passes, prepare, surgery as S  # noqa: E402


def main():
    args = sys.argv[1:]
    kv = dict(a.split('=', 1) for a in args if '=' in a)
    pos = [a for a in args if '=' not in a]
    lo, hi = int(pos[0]), int(pos[1])
    from mrcalc import conventions
    if kv.get('skip_conventions') != '1':
        conventions.assert_all(verbose=False)
        print('convention tests passed', flush=True)
    P = config.load_params()
    pm, qm = int(kv.get('p', P['slope_p'])), int(kv.get('q', P['slope_q']))
    opt = {'slopes_G': S.slope_set(pm, qm), 'slopes_T': S.slope_set(pm, qm, P['torus_integer_p']),
           'time_limit': float(kv.get('time_limit', 2.0)), 'time_limit_torus': 20.0}
    # table knots that are torus knots get the torus slope set
    pr = prepare.Problem.__new__(prepare.Problem)
    import json
    tl = {}
    for line in open(os.path.join(config.DATA, 'constructions.jsonl')):
        r = json.loads(line)
        if r.get('family') == 'torus' and 'node' in r:
            tl[r['node']] = True
    opt['torus_like'] = tl
    shards = passes.shard_nodes()
    done = F.done_shards()
    todo = [(s, ns, opt) for s, ns in shards.items() if lo <= passes.shard_tier(s) <= hi and s not in done
            and (s[0] != 's' or kv.get('composites') == '1')]
    print('fillings: %d shards, %d generic slopes' % (len(todo), len(opt['slopes_G'])), flush=True)
    t0 = time.time()
    budget = float(kv.get('budget', 1e9))
    n = 0
    with mp.Pool(int(kv.get('procs', 4)), maxtasksperchild=10) as pool:
        for shard, nrec, errors in pool.imap_unordered(F.shard_task, todo):
            with open(os.path.join(F.FILL_DIR, 'done.txt'), 'a') as f:
                f.write(shard + '\n')
            n += 1
            if errors:
                print('errors', shard, errors[:2], flush=True)
            if n % 5 == 0 or n == len(todo):
                print('  %d/%d shards %.0fs' % (n, len(todo), time.time() - t0), flush=True)
            if time.time() - t0 > budget:
                pool.terminate()
                break
    print('fillings done: %d shards %.0fs' % (n, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
