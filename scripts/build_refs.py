"""Milestone 1: reference tables.

  data/ref_hyp.jsonl       oriented isometry signatures of the verified-hyperbolic table knots
  data/table_checks.jsonl  calculator output on KnotInfo's PD codes, tau check, braid-word
                           chirality check (section 2.5)
  data/ref_nonhyp.jsonl    Regina isosig pool: non-hyperbolic table knots, torus knots,
                           composite nodes
Resumable: finished names are skipped.
"""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import knotinfo, identify as I, hfk as H, pd as P, names, nodeset  # noqa: E402
from mrcalc.config import DATA  # noqa: E402


def done_names(path):
    out = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                r = json.loads(line)
                if 'error' not in r:
                    out.add(r['name'])
    return out


def _ref(rec):
    try:
        return I.build_hyp_reference_one(rec)
    except Exception as e:
        return {'name': rec['name'], 'sig': None, 'sig_mirror': None, 'verified': False, 'error': repr(e)}


_idr = None


def _check(rec):
    global _idr
    if _idr is None:
        _idr = I.Identifier()
    out = {'name': rec['name']}
    h = H.hfk(rec['pd'])
    out['hfk'] = h
    out['tau_ok'] = (rec['tau'] is not None and h.get('tau') == rec['tau'])
    out['genus_ok'] = (h.get('genus') == rec['genus'])
    out['fibered_ok'] = (rec['fibered'] is None or h.get('fibered') == rec['fibered'])
    r0 = _idr.identify(rec['pd'])
    out['pd_ident'] = r0['name']
    out['braids'] = []
    for w in rec['braids']:
        try:
            b = P.braid_closure(w)
            r = _idr.identify(b)
            ok = (r['name'] == rec['name'])
            out['braids'].append({'word': w, 'ok': ok, 'ident': r['name'], 'cert': r['cert'],
                                  'strands': max(abs(g) for g in w) + 1, 'writhe': P.braid_writhe(w)})
        except Exception as e:
            out['braids'].append({'word': w, 'ok': False, 'ident': None, 'error': repr(e)})
    return out


def _pool(args):
    name, pd, amph = args
    try:
        return I.pool_record(name, pd, amphichiral=amph)
    except Exception as e:
        return {'name': name, 'error': repr(e)}


def run(func, items, path, nproc=4, chunk=8):
    t0 = time.time()
    n = 0
    with mp.Pool(nproc) as pool, open(path, 'a') as f:
        for r in pool.imap_unordered(func, items, chunksize=chunk):
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
            n += 1
            if n % 500 == 0:
                f.flush()
                print('  %d/%d  %.0fs' % (n, len(items), time.time() - t0), flush=True)
    print('done %s: %d in %.0fs' % (os.path.basename(path), n, time.time() - t0), flush=True)


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    T = knotinfo.table()
    if what in ('all', 'hyp'):
        d = done_names(I.REF_HYP)
        run(_ref, [r for r in T if r['name'] not in d], I.REF_HYP)
    if what in ('all', 'pool'):
        d = done_names(I.REF_NONHYP)
        hyp = {}
        with open(I.REF_HYP) as f:
            for line in f:
                r = json.loads(line)
                hyp[r['name']] = r
        items = []
        for r in T:
            if not hyp[r['name']]['verified'] and r['name'] not in d:
                items.append((r['name'], r['pd'], r['amphichiral']))
        print('non-hyperbolic table knots:', [x[0] for x in items], flush=True)
        run(_pool, items, I.REF_NONHYP, nproc=2, chunk=1)
        # torus knots that are table knots are aliases, not pool entries
        idr = I.Identifier(use_census=False)
        d = done_names(I.REF_NONHYP)
        items = []
        for name, pd in nodeset.torus_nodes():
            if name in d:
                continue
            r = idr.identify(pd)
            if r['name'] is None:
                items.append((name, pd, False))
            else:
                print('  torus alias', name, '->', r['name'], flush=True)
        for name in nodeset.composite_names():
            if name not in d:
                items.append((name, nodeset.diagram(name), names.is_amphichiral(name)))
        run(_pool, items, I.REF_NONHYP, chunk=2)
    if what in ('all', 'checks'):
        path = os.path.join(DATA, 'table_checks.jsonl')
        d = done_names(path)
        run(_check, [r for r in T if r['name'] not in d], path)


if __name__ == '__main__':
    main()
