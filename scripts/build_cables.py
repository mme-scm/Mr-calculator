"""Cable nodes C_{r,s}(K) (section 4).

Phase 1 (fast): data/cables.jsonl, one record per cable node: number of crossings of the construction
diagram and, for diagrams with at most 16 crossings, the identification with table knots.
Phase 2 (slow, resumable): data/cables_hfk.jsonl, calculator inputs under a time limit for construction
diagrams with at most <max crossings> crossings, and Regina pool entries for small diagrams.
usage: build_cables.py [phase1|phase2] [P_cab] [max companion crossings] [calculator timeout s] [max crossings]
"""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import identify as I, hfk as H, names, nodeset, config, pd as P, knotinfo  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

OUT = os.path.join(DATA, 'cables.jsonl')
OUT2 = os.path.join(DATA, 'cables_hfk.jsonl')
_idr = None


def crossings(name):
    r, s, comp = names.parse_cable(name)
    base = comp.rstrip('*')
    rec = knotinfo.by_name()[base]
    w = P.writhe(rec['pd']) * (-1 if comp.endswith('*') else 1)
    return s * s * rec['crossing_number'] + (s - 1) * abs(r - s * w)


def phase1(name):
    global _idr
    out = {'node': name, 'crossings': crossings(name)}
    if out['crossings'] <= 16:
        try:
            if _idr is None:
                _idr = I.Identifier()
            r = _idr.identify(nodeset.diagram(name))
            out['ident'], out['cert'] = r['name'], r['cert']
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            out['error'] = repr(e)
    return out


def phase2(args):
    name, timeout = args
    out = {'node': name}
    try:
        pd = nodeset.diagram(name)
        out['crossings'] = len(pd)
        h = H.hfk(pd, timeout=timeout, inline_below=0)
        if 'tau' in h:
            h['alex'] = H.alexander(h)
        out['hfk'] = h
        if len(pd) <= 25:
            try:
                out['pool'] = I.pool_record(name, pd, amphichiral=False, cap=200)
            except Exception as e:
                out['pool_error'] = repr(e)
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        out['error'] = repr(e)
    return out


def done(path):
    s = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                s.add(json.loads(line)['node'])
    return s


def main():
    P_ = config.load_params()
    args = sys.argv[1:]
    phase = args[0] if args else 'phase1'
    p_cab = int(args[1]) if len(args) > 1 else P_['P_cab']
    maxc = int(args[2]) if len(args) > 2 else P_['max_cable_companion_crossings']
    timeout = float(args[3]) if len(args) > 3 else 10.0
    maxcr = int(args[4]) if len(args) > 4 else 40
    allnames = nodeset.cable_names(p_cab, maxc)
    t0 = time.time()
    if phase == 'phase1':
        d = done(OUT)
        items = [n for n in allnames if n not in d]
        with mp.Pool(4) as pool, open(OUT, 'a') as f:
            for r in pool.imap(phase1, items, chunksize=16):
                f.write(json.dumps(r, separators=(',', ':')) + '\n')
        print('cables phase 1: %d nodes in %.0fs' % (len(items), time.time() - t0), flush=True)
        return
    d = done(OUT2)
    ident = {}
    for line in open(OUT):
        r = json.loads(line)
        ident[r['node']] = r
    items = [(n, timeout) for n in allnames if n not in d and ident[n]['crossings'] <= maxcr
             and not ident[n].get('ident')]
    items.sort(key=lambda x: ident[x[0]]['crossings'])
    print('cables phase 2: %d diagrams with at most %d crossings' % (len(items), maxcr), flush=True)
    with mp.Pool(4) as pool, open(OUT2, 'a') as f, open(I.REF_NONHYP, 'a') as g:
        for i, r in enumerate(pool.imap_unordered(phase2, items, chunksize=2)):
            pr = r.pop('pool', None)
            if pr is not None:
                g.write(json.dumps(pr, separators=(',', ':')) + '\n')
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
            if (i + 1) % 100 == 0:
                f.flush()
                print('  %d/%d %.0fs' % (i + 1, len(items), time.time() - t0), flush=True)
    print('cables phase 2 done in %.0fs' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
