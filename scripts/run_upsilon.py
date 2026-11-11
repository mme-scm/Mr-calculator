"""Milestone 7: calculator complexes for the nodes whose upsilon domain is not yet a singleton
(rules U1-U3).  Output: data/upsilon.jsonl (cached, resumable).
usage: run_upsilon.py [timeout seconds] [max crossings]"""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import hfk as H, names, nodeset, passes, prepare, solver, upsilon as U  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

OUT = os.path.join(DATA, 'upsilon.jsonl')


def task(args):
    node, src, timeout = args
    try:
        if src[0] == 'diagram':
            pd = nodeset.diagram(node)
        elif src[0] == 'pd':
            pd = src[1]
        else:
            mv = src[1]
            diags = {d['id']: d for d in passes.load_diagrams(mv['shard'])}
            pd = passes.result_pd(diags[mv['d']]['pd'], mv)
        h = H.hfk(pd, want_complex=True, timeout=timeout)
        if 'tau' not in h:
            return {'node': node, 'error': h.get('error') or 'timeout'}
        r = U.upsilon_record(h)
        r['node'] = node
        r['crossings'] = len(pd)
        r['source'] = src[0] if src[0] != 'move' else {k: src[1][k] for k in ('pass', 'shard', 'd', 'i', 'e', 'h') if k in src[1]}
        return r
    except Exception as e:
        return {'node': node, 'error': repr(e)}


def main():
    timeout = float(sys.argv[1]) if len(sys.argv) > 1 else 60
    maxcr = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    P = prepare.Problem()
    solver.SLOPES.clear()
    solver.SLOPES.update(P.slopes)
    S = solver.Solver()
    S.keep, S.record = None, False          # only the final domains are needed here
    S.add(P.cons)
    S.run()
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                done.add(json.loads(line)['node'])
    cons = {}
    for r in P.constructions:
        cons.setdefault(r['node'], r['pd'])
    items = []
    seen = set()
    for n, info in P.nodes.items():
        if n == '0_1' or S.get(n, 'U').pin() is not None or n in done:
            continue
        m = info['mirror']
        if m in seen or m in done:
            continue            # the mirror image is handled through U4b
        k = info['kind']
        if k == 'table':
            base = n.rstrip('*')
            if base in done or base in seen:
                continue
            n = base
            src = ('diagram',)
        elif k in ('composite', 'torus'):
            src = ('diagram',)
        elif n in cons:
            src = ('pd', cons[n])
        elif n in P.per_move:
            # peripheral: a complex only where U1 can be exact (Floer-thin or L-space flag, rule U2)
            ranks = info.get('ranks')
            thin = bool(ranks) and len({mm - a for a, mm, _ in ranks}) == 1
            if not (thin or (info['calc'] or {}).get('lspace')):
                continue
            src = ('move', P.per_move[n])
        elif k == 'cable' and (P.hfk_nodes.get(n) or {}).get('crossings', 999) <= maxcr:
            src = ('diagram',)
        else:
            continue
        seen.add(n)
        items.append((n, src, timeout))
    print('upsilon: %d nodes without a pinned upsilon need a complex' % len(items), flush=True)
    t0 = time.time()
    with mp.Pool(4) as pool, open(OUT, 'a') as f:
        for i, r in enumerate(pool.imap_unordered(task, items, chunksize=8)):
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
            if (i + 1) % 1000 == 0:
                f.flush()
                print('  %d/%d %.0fs' % (i + 1, len(items), time.time() - t0), flush=True)
    print('upsilon done in %.0fs' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
