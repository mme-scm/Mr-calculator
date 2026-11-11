"""Calculator inputs (g, fibered, tau, ...) of the peripheral nodes included in the solver.
One diagram per node: the result diagram of the first recorded move that produced it.
Output: data/hfk_peripheral.jsonl (appended; resumable)."""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import hfk as H, passes, prepare  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

OUT = os.path.join(DATA, 'hfk_peripheral.jsonl')


def task(args):
    node, move, timeout = args
    try:
        diags = {d['id']: d for d in passes.load_diagrams(move['shard'])}
        pd = passes.result_pd(diags[move['d']]['pd'], move)
        r = H.hfk(pd, timeout=timeout)
        if 'tau' in r:
            r['alex'] = H.alexander(r)
        r['crossings'] = len(pd)
    except Exception as e:
        r = {'error': repr(e)}
    r['node'] = node
    r['source'] = {k: move[k] for k in ('pass', 'shard', 'd', 'i', 'e', 'h', 'axis') if k in move}
    return r


def main():
    timeout = float(sys.argv[1]) if len(sys.argv) > 1 else 60
    P = prepare.Problem()
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                done.add(json.loads(line)['node'])
    items = []
    for n, info in P.nodes.items():
        if not info.get('peripheral') or info['calc'] is not None or n in done:
            continue
        mv = P.per_move.get(n)
        if mv is None:
            continue        # only reached as the mirror image of a result
        items.append((n, mv, timeout))
    print('peripheral nodes needing calculator input: %d' % len(items), flush=True)
    t0 = time.time()
    with mp.Pool(4) as pool, open(OUT, 'a') as f:
        for i, r in enumerate(pool.imap_unordered(task, items, chunksize=4)):
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
            if (i + 1) % 500 == 0:
                f.flush()
                print('  %d/%d %.0fs' % (i + 1, len(items), time.time() - t0), flush=True)
    print('done in %.0fs' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
