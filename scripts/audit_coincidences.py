"""Audit of the coincidence step on small knots, without its shortcuts (validation, section 10).

The coincidence step (scripts/find_coincidences.py) only looks at fillings that (1) got a geometric
solution within a few randomisations, (2) share |p| and volume with another filling, and (3) share the
unverified isometry signature with it; only then is the verified signature computed.  Here, for every
prime knot with at most tmax crossings and every slope of the slope set, the verified isometry signature
is computed directly, with many more attempts and no filter, and Regina gets its full time limit on the
fillings without a geometric solution.  The classes of equal verified signature are then compared with

  a. the coincidences the pipeline has (data/coincidences.jsonl, restricted to these knots);
  b. the volume filter: fillings of one class must have equal volume (and equal |p|);
  c. the unverified-signature filter: fillings of one class must have equal unverified signatures
     (computed by the pipeline's own function);
  d. SnapPy's isometry checker, on pairs with equal |p| and close volume but different verified
     signatures (an isometry found there would mean that the signature separates isometric fillings);
  e. the fillings that stay without a signature or a name.

First result (2026-11-12, knots up to 8 crossings): filters 2 and 3 lost nothing, but 36 fillings were
hyperbolic without a positively oriented solution on any randomisation of the filled triangulation, and
were dropped by step 1.  S.redescriptions (drilling a dual curve) now gives them a geometric description;
this script uses it too, for the fillings its first pass leaves open.

usage: audit_coincidences.py [tmax=8] [procs=3] [dir=<work dir>] [analyse=1] [regina=60]
       analyse=1: no new computation, report on the knots already done.
Output: <work dir>/<knot>.json per knot, data/coincidence_audit.json (summary).
"""
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import knotinfo, nodeset, surgery as S  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

HARD = {'interval_bits_precs': [53, 212, 1000],
        'exact_bits_prec_and_degrees': [(212, 10), (1000, 20), (2000, 20), (4000, 40)]}


def _fatal(e):
    return isinstance(e, (KeyboardInterrupt, SystemExit))


def sig_hash(sig):
    return hashlib.sha256(sig.encode()).hexdigest()[:16]


def verified_signature(E, slope, tries=60):
    """(volume of the first geometric solution or None, verified signature or None, randomisations used)."""
    N = E.copy()
    N.dehn_fill(tuple(slope))
    vol = None
    for t in range(tries):
        try:
            if N.solution_type() == S.GEOMETRIC:
                if vol is None:
                    vol = float(N.volume())
                if N.verify_hyperbolicity()[0]:
                    for kw in ({}, HARD):
                        try:
                            return vol, N.isometry_signature(verified=True, **kw), t
                        except BaseException as e:      # cysignals' SignalError is a BaseException
                            if _fatal(e):
                                raise
            N.randomize()
        except BaseException as e:
            if _fatal(e):
                raise
    if vol is None:                      # no positively oriented solution: another surgery description
        r = S.hyperbolic_signature(E, slope, verified=True, tries=2)
        if r:
            return r['volume'], r['sig'], -1
    return vol, None, tries


def repair(work, nodes):
    """Fillings left without geometric solution and without name by an earlier run of this script: the
    redescription of S.redescriptions is tried (tries = -1 marks a signature found that way)."""
    n = 0
    for node in nodes:
        path = os.path.join(work, node + '.json')
        if not os.path.exists(path):
            continue
        recs = json.load(open(path))
        todo = [r for r in recs if r['vol'] is None and r.get('kind') == 'unknown' and 'redescribed' not in r]
        if not todo:
            continue
        E = S.exterior(nodeset.diagram(node))
        for r in todo:
            try:
                x = S.hyperbolic_signature(E, (r['p'], r['q']), verified=True, tries=2)
            except BaseException as e:
                if _fatal(e):
                    raise
                x = None
            r['redescribed'] = bool(x)
            if x:
                r.update(vol=x['volume'], sig=x['sig'], tries=-1)
                n += 1
        with open(path + '.tmp', 'w') as f:
            json.dump(recs, f)
        os.replace(path + '.tmp', path)
    return n


def node_task(args):
    node, slopes, regina_limit = args
    t0 = time.time()
    E = S.exterior(nodeset.diagram(node))
    out = []
    for p, q in slopes:
        rec = {'node': node, 'p': p, 'q': q}
        vol, sig, used = verified_signature(E, (p, q))
        rec.update(vol=vol, sig=sig, tries=used)
        if vol is None:
            try:
                r = S.regina_recognise(S.filled_string(E, (p, q)), time_limit=regina_limit, visit_cap=10 ** 9)
                rec.update(kind=r['kind'], name=r.get('name'))
            except BaseException as e:
                if _fatal(e):
                    raise
                rec.update(kind='unknown', name=None, error=repr(e))
        out.append(rec)
    return node, out, time.time() - t0


def crossings(name):
    return int(name.split('_')[0].rstrip('an'))


def load(work, nodes):
    recs = []
    for n in nodes:
        p = os.path.join(work, n + '.json')
        if os.path.exists(p):
            recs.extend(json.load(open(p)))
    return recs


def classes_of(pairs):
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for a, b in pairs:
        a, b = find(a), find(b)
        if a != b:
            par[a] = b
    g = defaultdict(set)
    for x in par:
        g[find(x)].add(x)
    return {frozenset(v) for v in g.values() if len(v) > 1}


def analyse(work, nodes, torus, amph):
    import snappy
    recs = load(work, nodes)
    done = sorted({r['node'] for r in recs}, key=lambda n: (crossings(n), n))
    rep = {'knots': done, 'fillings': len(recs)}
    hyp = [r for r in recs if r['node'] not in torus]

    def fold(r):          # -p/q on an amphichiral knot is p/q up to orientation: one key for both
        p = abs(r['p']) if r['node'] in amph else r['p']
        return (r['node'], p, r['q'])
    # ---- ground truth: classes of equal verified signature
    by_sig = defaultdict(set)
    key_recs = defaultdict(list)
    for r in hyp:
        key_recs[fold(r)].append(r)
        if r['sig']:
            by_sig[r['sig']].add(fold(r))
    truth = {frozenset(v) for v in by_sig.values() if len(v) > 1}
    rep['hyperbolic fillings with a verified signature'] = sum(1 for r in hyp if r['sig'])
    rep['of these, only through a redescription (no positively oriented filled triangulation)'] = sum(
        1 for r in hyp if r['sig'] and r.get('tries') == -1)
    rep['classes of equal verified signature (two or more fillings)'] = len(truth)
    rep['independent equations in them'] = sum(len(c) - 1 for c in truth)
    # ---- a. the pipeline's coincidences on these knots
    ks = set(done)
    pipe_pairs = []
    with open(os.path.join(DATA, 'coincidences.jsonl')) as f:
        for line in f:
            c = json.loads(line)
            if c['cert'] == 'a':
                pipe_pairs.append((fold({'node': c['A'], 'p': c['sA'][0], 'q': c['sA'][1]}),
                                   fold({'node': c['B'], 'p': c['sB'][0], 'q': c['sB'][1]})))
    # classes over all knots first (a class may be linked through a larger knot), then these knots only
    pipe = {c for c in (frozenset(k for k in c0 if k[0] in ks) for c0 in classes_of(pipe_pairs)) if len(c) > 1}
    cls_of = {k: c for c in pipe for k in c}
    missing, extra = [], []
    for c in truth:                              # every pair of a true class must be in one pipeline class
        parts = {cls_of.get(k, frozenset([k])) for k in c}
        if len(parts) > 1:
            missing.append(sorted(c))
    tcls = {k: c for c in truth for k in c}
    for c in pipe:
        parts = {tcls.get(k, frozenset([k])) for k in c}
        if len(parts) > 1:
            extra.append(sorted(c))
    rep['a. pipeline classes on these knots'] = len(pipe)
    rep['a. true classes the pipeline does not have (in full)'] = sorted(missing)
    rep['a. pipeline classes not confirmed here'] = sorted(extra)
    # ---- b. the volume filter
    spread = 0.0
    bad_p = []
    for c in truth:
        vols = [r['vol'] for k in c for r in key_recs[k] if r['vol'] is not None]
        spread = max(spread, max(vols) - min(vols))
        if len({abs(k[1]) for k in c}) > 1:
            bad_p.append(sorted(c))
    rep['b. largest volume difference inside a class'] = spread
    rep['b. classes with different |p|'] = bad_p
    # ---- c. the unverified-signature filter, with the pipeline's function
    ext = {}
    bad_u, none_u, n_u = [], [], 0
    for c in sorted(truth, key=sorted):
        hs = {}
        for k in sorted(c):
            node, p, q = k
            if node not in ext:
                ext[node] = S.exterior(nodeset.diagram(node))
            try:
                r = S.hyperbolic_signature(ext[node], (p, q), verified=False, tries=10)
            except BaseException as e:
                if _fatal(e):
                    raise
                r = None
            n_u += 1
            hs[k] = sig_hash(r['sig']) if r else None
        if None in hs.values():
            none_u.append(sorted(k for k, h in hs.items() if h is None))
        if len({h for h in hs.values() if h}) > 1:
            bad_u.append(sorted(c))
    rep['c. unverified signatures computed'] = n_u
    rep['c. classes split by the unverified signature'] = bad_u
    rep['c. fillings of a class without unverified signature (sent to the verified step)'] = none_u
    # ---- d. isometry checker on near misses
    by_p = defaultdict(list)
    for r in hyp:
        if r['vol'] is not None and r['sig']:
            by_p[abs(r['p'])].append(r)
    near, iso_found, errors = 0, [], 0
    for p, lst in by_p.items():
        lst.sort(key=lambda r: r['vol'])
        for i, a in enumerate(lst):
            for b in lst[i + 1:]:
                if b['vol'] - a['vol'] > 1e-6:
                    break
                if a['sig'] == b['sig'] or fold(a) == fold(b):
                    continue
                near += 1
                try:
                    Ma, Mb = (S.geometric_filling(ext.setdefault(x['node'], S.exterior(nodeset.diagram(x['node']))),
                                                  (x['p'], x['q']), tries=40) for x in (a, b))
                    if Ma is not None and Mb is not None and Ma.is_isometric_to(Mb):
                        iso_found.append([fold(a), fold(b)])
                except BaseException as e:
                    if _fatal(e):
                        raise
                    errors += 1
    rep['d. pairs with equal |p|, volumes within 1e-6, different verified signatures'] = near
    rep['d. such pairs that SnapPy finds isometric'] = iso_found
    rep['d. errors of the isometry checker'] = errors
    # ---- e. what stays open
    rep['e. geometric solution but no verified signature'] = sorted(fold(r) for r in hyp if r['vol'] is not None
                                                                   and not r['sig'])
    nongeo = [r for r in hyp if r['vol'] is None]
    rep['e. no geometric solution: Regina kinds'] = dict(Counter(r.get('kind') for r in nongeo))
    rep['e. no geometric solution, not recognised'] = sorted((r['node'], r['p'], r['q']) for r in nongeo
                                                            if r.get('kind') == 'unknown')
    # pipeline records of the fillings that are hyperbolic here
    from mrcalc import fillings as F
    kind = {}
    for r in F.iter_fillings():
        if r['node'] in ks:
            kind[(r['node'], r['p'], r['q'])] = r['kind']
    rep['e. hyperbolic here, not geometric in data/fillings'] = sorted(
        (r['node'], r['p'], r['q']) for r in hyp if r['sig'] and kind.get((r['node'], r['p'], r['q'])) != 'geo')
    # ---- names (fillings without geometric solution), all knots
    by_name = defaultdict(set)
    for r in recs:
        if r['vol'] is None and r.get('kind') in ('lens', 'sfs') and r.get('name'):
            by_name[r['name']].add(fold(r))
    tname = {frozenset(v) for v in by_name.values() if len(v) > 1}
    npairs = []
    with open(os.path.join(DATA, 'coincidences.jsonl')) as f:
        for line in f:
            c = json.loads(line)
            if c['cert'] != 'a':
                npairs.append((fold({'node': c['A'], 'p': c['sA'][0], 'q': c['sA'][1]}),
                               fold({'node': c['B'], 'p': c['sB'][0], 'q': c['sB'][1]})))
    pname = {c for c in (frozenset(k for k in c0 if k[0] in ks) for c0 in classes_of(npairs)) if len(c) > 1}
    pc = {k: c for c in pname for k in c}
    rep['names: classes of equal Regina name here'] = len(tname)
    rep['names: classes the pipeline does not have (in full)'] = sorted(
        sorted(c) for c in tname if len({pc.get(k, frozenset([k])) for k in c}) > 1)
    rep['names: pipeline classes on these knots'] = len(pname)
    _ = snappy
    return rep


def main():
    kv = dict(x.split('=', 1) for x in sys.argv[1:] if '=' in x)
    tmax = int(kv.get('tmax', 8))
    procs = int(kv.get('procs', 3))
    work = kv.get('dir', '/home/user/mrcalc_scratch/audit')
    regina_limit = float(kv.get('regina', 60))
    os.makedirs(work, exist_ok=True)
    info = knotinfo.by_name()
    amph = {n for n, r in info.items() if r['amphichiral']}
    torus = set()
    for line in open(os.path.join(DATA, 'constructions.jsonl')):
        r = json.loads(line)
        if r.get('family') == 'torus' and 'node' in r:
            torus.add(r['node'])
    nodes = sorted((n for n in info if crossings(n) <= tmax), key=lambda n: (n in torus, crossings(n), n))
    slopes = S.slope_set(30, 4)
    if kv.get('analyse') != '1':
        todo = [(n, slopes, 10.0 if n in torus else regina_limit) for n in nodes
                if not os.path.exists(os.path.join(work, n + '.json'))]
        print('audit: %d knots with at most %d crossings, %d to do, %d slopes each' % (
            len(nodes), tmax, len(todo), len(slopes)), flush=True)
        t0 = time.time()
        with mp.Pool(procs, maxtasksperchild=1) as pool:
            it = pool.imap_unordered(node_task, todo)
            for _ in todo:
                node, out, dt = it.next(timeout=6 * 3600)
                with open(os.path.join(work, node + '.json.tmp'), 'w') as f:
                    json.dump(out, f)
                os.replace(os.path.join(work, node + '.json.tmp'), os.path.join(work, node + '.json'))
                print('  %s %.0fs (total %.0fs)' % (node, dt, time.time() - t0), flush=True)
    n = repair(work, nodes)
    if n:
        print('redescribed: %d fillings without geometric solution now have a verified signature' % n, flush=True)
    rep = analyse(work, nodes, torus, amph)
    rep['tmax'] = tmax
    with open(os.path.join(DATA, 'coincidence_audit.json'), 'w') as f:
        json.dump(rep, f, indent=1)
    for k, v in rep.items():
        s = json.dumps(v)
        print('%s: %s' % (k, s if len(s) < 600 else s[:600] + ' ...'), flush=True)


if __name__ == '__main__':
    main()
