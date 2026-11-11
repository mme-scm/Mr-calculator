"""Family constructions (section 6) and calculator inputs of constructed core nodes.

  data/constructions.jsonl   one line per family instance: the construction diagram in the
                             chirality required by the rule, its identification, calculator data
  data/hfk_nodes.jsonl       calculator data of non-table nodes (composites, torus knots,
                             constructions that are their own node)
usage: build_constructions.py [families] [composites] [cables <P_cab> <max companion crossings>]
"""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import identify as I, hfk as H, names, nodeset, pd as P, alg  # noqa: E402
from mrcalc.config import DATA, load_params  # noqa: E402

CONS = os.path.join(DATA, 'constructions.jsonl')
HFKN = os.path.join(DATA, 'hfk_nodes.jsonl')
_idr = None


def idr():
    global _idr
    if _idr is None:
        _idr = I.Identifier()
    return _idr


def calc(pd, timeout=120):
    r = H.hfk(pd, timeout=timeout)
    if 'tau' in r:
        r['alex'] = H.alexander(r)
    return r


def one_family(f):
    """Pick the chirality required by the rule, identify, compute calculator data."""
    fam, pd = f['family'], f['pd']
    out = []
    variants = []
    h = calc(pd)
    if 'tau' not in h:
        return [dict(f, pd=pd, error='calculator failed', hfk=h)]
    hm = calc(P.mirror(pd))
    if fam in ('torus', 'pretzel_n3m3'):
        variants = [(pd, h, None)]
    elif fam == 'twist':
        variants = [(pd, h, 'as built'), (P.mirror(pd), hm, 'mirror')]
    elif fam == 'pretzel_m2pq':
        want = (f['params']['p'] + f['params']['q']) // 2
        variants = [(d, x, 'tau=%d' % want) for d, x in ((pd, h), (P.mirror(pd), hm)) if x['tau'] == want]
    elif fam == 'pretzel_odd32':
        variants = [(d, x, 'tau>0') for d, x in ((pd, h), (P.mirror(pd), hm)) if x['tau'] > 0]
    elif fam == 'pretzel_odd':
        for d, x in ((pd, h), (P.mirror(pd), hm)):
            if P.writhe(d) == len(d):
                variants.append((d, x, 'all crossings positive'))
    if not variants:
        return [dict(f, error='no chirality satisfies the rule condition', tau=[h['tau'], hm['tau']])]
    for d, x, note in variants[:2] if fam == 'twist' else variants[:1]:
        r = idr().identify(d)
        rec = dict(f)
        rec['pd'] = d
        rec['chirality'] = note
        rec['hfk'] = x
        rec['writhe'] = P.writhe(d)
        rec['ident'] = r['name']
        rec['cert'] = r['cert']
        rec['kind'] = r['kind']
        if fam == 'pretzel_odd':
            rec['norm'] = sum(abs(c) for c in x['alex'])
        out.append(rec)
    return out


def node_input(args):
    name, pd, timeout = args
    r = calc(pd, timeout)
    r['node'] = name
    r['crossings'] = len(pd)
    return r


def done(path, key):
    out = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                out.add(json.loads(line)[key])
    return out


def main():
    what = sys.argv[1:] or ['families', 'composites']
    params = load_params()
    t0 = time.time()
    if 'families' in what:
        fams = nodeset.family_constructions(params['family_max_crossings'], params['torus_pq_max'])
        recs = []
        with mp.Pool(4) as pool:
            for rs in pool.imap(one_family, fams, chunksize=4):
                recs.extend(rs)
        # constructions that identify with no existing node become nodes of their own;
        # non-hyperbolic ones are added to the Regina pool so that later diagrams can match them
        pool_names = done(I.REF_NONHYP, 'name')
        with open(CONS, 'w') as f, open(I.REF_NONHYP, 'a') as g:
            for r in recs:
                if 'error' not in r and r['ident'] is None:
                    base = r['construction'] if r['chirality'] != 'mirror' else r['construction'] + '*'
                    r['node'] = base
                    r['own_node'] = True
                    if names.kind(base) != 'torus' and base not in pool_names:
                        pr = I.pool_record(base, r['pd'])
                        g.write(json.dumps(pr, separators=(',', ':')) + '\n')
                        pool_names.add(base)
                elif 'error' not in r:
                    r['node'] = r['ident']
                f.write(json.dumps(r, separators=(',', ':')) + '\n')
        print('families: %d records, %.0fs' % (len(recs), time.time() - t0), flush=True)
        import collections
        print(collections.Counter((r['family'], r.get('kind', 'error')) for r in recs))
    if 'composites' in what:
        d = done(HFKN, 'node')
        items = [(n, nodeset.diagram(n), 120) for n in nodeset.composite_names() if n not in d]
        cons = [json.loads(l) for l in open(CONS)]
        for r in cons:
            if r.get('own_node') and r['node'] not in d and names.kind(r['node']) != 'table':
                items.append((r['node'], r['pd'], 120))
                d.add(r['node'])
        for p, q in nodeset.torus_params(params['torus_pq_max']):
            n = names.torus_name(p, q)
            if n not in d:
                items.append((n, P.torus_knot(p, q), 120))
                d.add(n)
        with mp.Pool(4) as pool, open(HFKN, 'a') as f:
            for r in pool.imap_unordered(node_input, items, chunksize=8):
                f.write(json.dumps(r, separators=(',', ':')) + '\n')
        print('node inputs: %d, %.0fs' % (len(items), time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
