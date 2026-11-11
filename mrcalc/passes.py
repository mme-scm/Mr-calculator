"""Move passes of section 5: diagrams, crossing changes, full twists, mutations.

Pass records are compact (no PD codes): every result diagram is recomputable from the
source diagram record and the move parameters with the functions of mrcalc.pd, and the
export regenerates the PD codes of the edges it lists.

Only diagrams in KnotInfo's chirality are moved.  The diagrams of K* are the mirror images
of the diagrams of K and every move on them is the mirror image of a move on K; the rules
carried by the mirrored edge (F7/C7/U5, F9/U6, F6) are implied by the original edge together
with F3/C3/U4b, so mirrored moves are not recomputed.
"""
from __future__ import annotations

import hashlib
import json
import os

from . import identify as I, names, nodeset, pd as P
from .config import DATA, k_max_for

PASS_DIR = os.path.join(DATA, 'passes')
DIAG_DIR = os.path.join(DATA, 'diagrams')

_idr = None


def identifier():
    global _idr
    if _idr is None:
        _idr = I.Identifier()
    return _idr


def seed_for(name, j):
    return int(hashlib.sha1(('%s|re%d' % (name, j)).encode()).hexdigest()[:8], 16)


def diagrams_for(name, rediagrams=3, braid_ok=None):
    """Diagram records of a core node (KnotInfo chirality / construction diagram)."""
    out = []
    base = nodeset.diagram(name)
    out.append({'id': '%s|pd' % name, 'node': name, 'kind': 'pd', 'pd': P.normalise(base),
                'cert': {'type': 'reference'}})
    if names.kind(name) == 'table':
        from . import knotinfo
        rec = knotinfo.by_name()[name]
        for j, w in enumerate(rec['braids']):
            if braid_ok is not None and not braid_ok.get((name, j), False):
                continue
            out.append({'id': '%s|braid%d' % (name, j), 'node': name, 'kind': 'braid%d' % j,
                        'pd': P.braid_closure(w), 'word': w, 'strands': max(abs(g) for g in w) + 1,
                        'cert': {'type': 'knotinfo-braid', 'checked': 'data/table_checks.jsonl'}})
    elif names.kind(name) == 'torus':
        p, q, mir = names.parse_torus(name)
        out[0]['word'] = P.torus_word(p, q)
        out[0]['strands'] = min(p, q)
    for j in range(1, rediagrams + 1):
        seed = seed_for(name, j)
        new, moves = P.random_rediagram(base, seed)
        out.append({'id': '%s|re%d' % (name, j), 'node': name, 'kind': 're%d' % j, 'pd': new,
                    'seed': seed,
                    'moves': [{k: v for k, v in m.items() if k != 'pd_before'} for m in moves],
                    'cert': {'type': 'reidemeister', 'from': '%s|pd' % name}})
    for d in out:
        D = P.Diagram.from_pd(d['pd'])
        d['writhe'] = D.writhe()
        d['homogeneous'] = D.is_homogeneous()
        d['n'] = D.n
    return out


def _result(new_pd, src_diag):
    idr = identifier()
    r = idr.identify(new_pd)
    out = {'dst': r['name'], 'kind': r['kind'], 'cert': r['cert'], 'n': len(new_pd)}
    try:
        out['hg'] = P.Diagram.from_pd(new_pd).is_homogeneous()
    except P.DiagramError:
        out['hg'] = False
    return out


def cc_records(diag):
    """Crossing changes at every crossing of a diagram record."""
    D = P.Diagram.from_pd(diag['pd'])
    out = []
    for i in range(D.n):
        new = P.crossing_change(diag['pd'], i)
        rec = {'t': 'cc', 'd': diag['id'], 'src': diag['node'], 'i': i, 's': D.sign[i],
               'w0': D.writhe(), 'w1': P.writhe(new)}
        if rec['w1'] - rec['w0'] != -2 * D.sign[i]:
            raise AssertionError('writhe check failed on crossing change')
        rec.update(_result(new, diag))
        if 'word' in diag:
            w = list(diag['word'])
            w[i] = -w[i]
            rec['word'] = w
            rec['strands'] = diag['strands']
        out.append(rec)
    return out


def twist_records(diag, ks, max_imbalance=2):
    D = P.Diagram.from_pd(diag['pd'])
    w0 = D.writhe()
    out = []
    for k in ks:
        for edges, faces, dirs in P.dual_paths(D, k, max_imbalance):
            for h in (1, -1):
                new, a, b, d2 = P.twist(diag['pd'], edges, h)
                w1 = P.writhe(new)
                if (a - b) ** 2 != k + h * (w1 - w0):
                    raise AssertionError('writhe identity failed on twist')
                rec = {'t': 'tw', 'd': diag['id'], 'src': diag['node'], 'e': list(edges),
                       'dirs': list(dirs), 'h': h, 'a': a, 'b': b, 'w0': w0, 'w1': w1}
                rec.update(_result(new, diag))
                out.append(rec)
    return out


def mutation_records(diag):
    D = P.Diagram.from_pd(diag['pd'])
    out = []
    for edges, faces, inside in P.conway_circles(D):
        for axis in ('x', 'y', 'z'):
            try:
                new = P.mutate(diag['pd'], edges, axis)
            except P.DiagramError as e:
                out.append({'t': 'mu', 'd': diag['id'], 'src': diag['node'], 'e': list(edges),
                            'axis': axis, 'dst': None, 'kind': 'error', 'cert': {'type': 'none', 'why': str(e)}})
                continue
            rec = {'t': 'mu', 'd': diag['id'], 'src': diag['node'], 'e': list(edges), 'axis': axis,
                   'w0': D.writhe(), 'w1': P.writhe(new), 'inside': sorted(inside)}
            rec.update(_result(new, diag))
            out.append(rec)
    return out


def result_pd(diag_pd, rec):
    """Recompute the result diagram of a pass record."""
    if rec['t'] == 'cc':
        return P.crossing_change(diag_pd, rec['i'])
    if rec['t'] == 'tw':
        return P.twist(diag_pd, rec['e'], rec['h'])[0]
    if rec['t'] == 'mu':
        return P.mutate(diag_pd, rec['e'], rec['axis'])
    raise ValueError(rec['t'])


# ----------------------------------------------------------------------
# shards
# ----------------------------------------------------------------------
def shard_nodes(chunk=40):
    """Shards of core nodes (KnotInfo chirality only): {shard id: [node names]}.
    Table knots by crossing number, composites by crossing sum, then torus knots."""
    from . import knotinfo
    out = {}
    by_c = {}
    for r in knotinfo.table():
        by_c.setdefault(r['crossing_number'], []).append(r['name'])
    for c in sorted(by_c):
        ns = by_c[c]
        for j in range(0, len(ns), chunk):
            out['t%02d-%04d' % (c, j // chunk)] = ns[j:j + chunk]
    comp = {}
    for n in nodeset.composite_names():
        if n > names.mirror_name(n):
            continue          # one representative per mirror pair
        comp.setdefault(names.crossing_number(n), []).append(n)
    for c in sorted(comp):
        ns = comp[c]
        for j in range(0, len(ns), chunk):
            out['s%02d-%04d' % (c, j // chunk)] = ns[j:j + chunk]
    tor = [names.torus_name(p, q) for p, q in nodeset.torus_params()]
    for j in range(0, len(tor), chunk):
        out['x-torus-%04d' % (j // chunk)] = tor[j:j + chunk]
    return out


def shard_tier(shard):
    """Tier number of a shard (table/composite crossing number; 99 for constructions)."""
    if shard[0] in 'ts':
        return int(shard[1:3])
    return 99


def diag_path(shard):
    return os.path.join(DIAG_DIR, '%s.jsonl' % shard)


def build_diagram_shard(args):
    shard, node_names, rediagrams, braid_ok = args
    os.makedirs(DIAG_DIR, exist_ok=True)
    out, errors = [], []
    for name in node_names:
        try:
            out.extend(diagrams_for(name, rediagrams=rediagrams, braid_ok=braid_ok))
        except Exception as e:
            errors.append({'node': name, 'error': repr(e)})
    with open(diag_path(shard), 'w') as f:
        for d in out:
            f.write(json.dumps(d, separators=(',', ':')) + '\n')
    return shard, len(out), errors


def load_diagrams(shard):
    with open(diag_path(shard)) as f:
        return [json.loads(l) for l in f]


def shard_task(args):
    """Run one pass on one shard: args = (pass name, shard id, options).
    options: kinds (diagram kinds to move), kmin/kmax (twists), params."""
    pname, shard, opt = args
    params = opt['params']
    recs, errors = [], []
    for d in load_diagrams(shard):
        if not any(d['kind'] == k or d['kind'].startswith(k) for k in opt['kinds']):
            continue
        if opt.get('only_nodes') is not None and d['node'] not in opt['only_nodes']:
            continue
        try:
            if opt['move'] == 'cc':
                recs.extend(cc_records(d))
            elif opt['move'] == 'tw':
                kmax = min(opt['kmax'], k_max_for(d['n'], params))
                recs.extend(twist_records(d, list(range(opt.get('kmin', 2), kmax + 1)),
                                          params['max_imbalance']))
            elif opt['move'] == 'mu':
                recs.extend(mutation_records(d))
        except Exception as e:
            errors.append({'diagram': d['id'], 'error': repr(e)})
    idr = identifier()
    new_census = getattr(idr, 'new_census', [])
    idr.new_census = []
    return pname, shard, recs, new_census, errors


def shard_path(pname, shard):
    return os.path.join(PASS_DIR, pname, '%s.jsonl' % shard)


def done_shards(pname):
    p = os.path.join(PASS_DIR, pname, 'done.txt')
    if not os.path.exists(p):
        return set()
    with open(p) as f:
        return set(l.strip() for l in f if l.strip())


def write_shard(pname, shard, recs, errors):
    os.makedirs(os.path.join(PASS_DIR, pname), exist_ok=True)
    with open(shard_path(pname, shard), 'w') as f:
        for r in recs:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    if errors:
        with open(os.path.join(PASS_DIR, pname, 'errors.jsonl'), 'a') as f:
            for e in errors:
                e['shard'] = shard
                f.write(json.dumps(e) + '\n')
    with open(os.path.join(PASS_DIR, pname, 'done.txt'), 'a') as f:
        f.write(shard + '\n')


def iter_pass_records(pname=None):
    """All records of one pass (or of all passes)."""
    if not os.path.isdir(PASS_DIR):
        return
    for pn in sorted(os.listdir(PASS_DIR)):
        if pname is not None and pn != pname:
            continue
        d = os.path.join(PASS_DIR, pn)
        for fn in sorted(os.listdir(d)):
            if fn.endswith('.jsonl') and fn != 'errors.jsonl':
                with open(os.path.join(d, fn)) as f:
                    for line in f:
                        r = json.loads(line)
                        r['pass'] = pn
                        r['shard'] = fn[:-6]
                        yield r
