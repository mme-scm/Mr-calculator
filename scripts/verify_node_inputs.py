"""Check the stored calculator inputs of the nodes outside the table against the diagrams they were computed
from (repair after the calculator defect of 2026-11-15, mrcalc/hfk.py): the Euler characteristic of the stored
knot Floer ranks must be the Alexander polynomial of the node's diagram (Seifert matrix, exact).

usage: verify_node_inputs.py out=<report.jsonl> [procs=3]
One line per block of nodes: {'checked': n, 'bad': [{'node', 'stored', 'seifert', 'source'}]}; resumable.
A node whose stored record fails is listed; its record is to be recomputed with the checked calculator."""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import alg, node_pd  # noqa: E402
from mrcalc import pd as P  # noqa: E402
from mrcalc.config import iter_hfk_peripheral  # noqa: E402


def block(items):
    bad = []
    n = 0
    for node, ranks, source in items:
        try:
            pd = P.remove_kinks(node_pd.diagram(node, source))
            want = alg.alexander_from_seifert(alg.seifert_matrix(pd)) if pd else [1]
            got = alg.alexander_from_hfk_ranks({(a, m): v for a, m, v in ranks})
            if got != want:
                bad.append({'node': node, 'stored': got, 'seifert': want, 'source': source})
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            bad.append({'node': node, 'error': repr(e), 'source': source})
        n += 1
    return {'first': items[0][0], 'checked': n, 'bad': bad}


def main():
    kv = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
    out = kv['out']
    done = set()
    if os.path.exists(out):
        with open(out) as f:
            for line in f:
                if line.endswith('\n'):
                    done.add(json.loads(line)['first'])
    items = []
    for r in iter_hfk_peripheral():
        if 'ranks' in r and 'source' in r:
            items.append((r['node'], r['ranks'], r['source']))
    items.sort(key=lambda x: (x[2]['shard'], x[0]))            # one diagram shard at a time per worker
    blocks = [items[i:i + 400] for i in range(0, len(items), 400)]
    blocks = [b for b in blocks if b[0][0] not in done]
    print('%d nodes with stored ranks, %d blocks to check' % (len(items), len(blocks)), flush=True)
    del items
    t0 = time.time()
    n = nb = 0
    with mp.Pool(int(kv.get('procs', 3)), maxtasksperchild=20) as pool, open(out, 'a') as f:
        for k, r in enumerate(pool.imap_unordered(block, blocks)):
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
            f.flush()
            n += r['checked']
            nb += len(r['bad'])
            if (k + 1) % 25 == 0 or k + 1 == len(blocks):
                print('  %d/%d blocks, %d nodes checked, %d fail, %.0fs' % (k + 1, len(blocks), n, nb, time.time() - t0),
                      flush=True)
    print('NODE_CHECK_DONE %d checked, %d fail' % (n, nb), flush=True)


if __name__ == '__main__':
    main()
