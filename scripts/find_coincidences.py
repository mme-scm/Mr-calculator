"""Surgery coincidences (section 6): S1 certificates from the filling records.

 (a) hyperbolic: fillings with equal |p| and volume (within 2e-7) are candidates; for each
     candidate the hyperbolic structure is verified (verify_hyperbolicity) and the verified
     isometry signature (orientation ignored) is computed; equal signatures certify an
     isometry.  Prefilter (budget choice, prefilter=0 switches it off): the unverified isometry
     signature is computed first (cached as a hash in data/filling_usig.jsonl) and the verified
     one only for the fillings of a cluster whose unverified signatures agree, or are missing.
 (b) both recognised by Regina with the same normalised Seifert fibred name.
 (c) one side is a torus-knot filling named by S2 (Moser): its Regina name is first checked
     against Moser's fibre orders.
Output: data/coincidences.jsonl (rewritten; out=<path> writes elsewhere).
Orientation: a coincidence is a homeomorphism of the fillings, orientation preserving or not (all three
certificates are up to orientation).  The fillings S_{-p/q}(K*) = -S_{p/q}(K) of the mirror are therefore
the same manifolds; they are never built or compared (fillings exist for one chirality of a knot, with
slopes of both signs), and the equations of the mirror nodes follow from F3/C3.  Records that say nothing
are not written: the same knot under two names at the same slope, and p/q against -p/q on an
amphichiral knot.
Order (budget choice): the fillings of mutant knots at corresponding slopes have equal volume, and such pairs
are almost all of the candidates (55,669 of 56,152 clusters on 2026-11-12); in the 36,128 of them tested by
then no two signatures agreed, while 103 of the 359 other clusters tested had equal signatures.  Clusters whose
knots lie in one mutation class (classes of the mu pass) are therefore tested last; which=nonmutant leaves
them out of a run (signatures already in the caches are used in any case).
usage: find_coincidences.py [budget=<seconds, 0: none>] [procs=4] [prefilter=1] [compute=1] [which=all|nonmutant]
                            [out=<path>]
       compute=0: no new signatures, only the caches are used.
"""
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import fillings as F, names, nodeset, surgery as S  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

SIG_CACHE = os.path.join(DATA, 'filling_signatures.jsonl')


_ext = {}


def sig_task(keys):
    """Verified isometry signatures of a list of (node, p, q) fillings."""
    out = []
    for node, p, q in keys:
        try:
            if node not in _ext:
                if len(_ext) > 40:
                    _ext.clear()
                _ext[node] = S.exterior(nodeset.diagram(node))
            r = S.hyperbolic_signature(_ext[node], (p, q), verified=True, tries=10)
        except BaseException as e:           # cysignals' SignalError is a BaseException
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            r = None
        out.append({'node': node, 'p': p, 'q': q, 'sig': r['sig'] if r else None, 'verified': bool(r)})
    return out


USIG_CACHE = os.path.join(DATA, 'filling_usig.jsonl')


def sig_hash(sig):
    return hashlib.sha256(sig.encode()).hexdigest()[:16]


def usig_task(keys):
    """Hashes of the unverified isometry signatures of a list of (node, p, q) fillings (None: no
    signature found)."""
    out = []
    for node, p, q in keys:
        try:
            if node not in _ext:
                if len(_ext) > 40:
                    _ext.clear()
                _ext[node] = S.exterior(nodeset.diagram(node))
            r = S.hyperbolic_signature(_ext[node], (p, q), verified=False, tries=10)
        except BaseException as e:           # cysignals' SignalError is a BaseException
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            r = None
        out.append({'node': node, 'p': p, 'q': q, 'h': sig_hash(r['sig']) if r else None})
    return out


def run_pool(task, tasks, cache_path, store, procs, budget, t0, what):
    """Runs the tasks, appends the results to the cache file and to store.  Returns (number of
    results, False if stopped by the budget or a worker timeout)."""
    ndone = 0
    if not tasks:
        return 0, True
    with mp.Pool(procs, maxtasksperchild=25) as pool, open(cache_path, 'a') as f:
        it = pool.imap_unordered(task, tasks)
        while True:
            try:
                out = it.next(timeout=1800)
            except StopIteration:
                return ndone, True
            except mp.TimeoutError:
                print('timeout waiting for a worker (a worker died?); continuing with the %s computed '
                      'so far (rerun to resume)' % what, flush=True)
                pool.terminate()
                return ndone, False
            for r in out:
                store[(r['node'], r['p'], r['q'])] = r
                f.write(json.dumps(r, separators=(',', ':')) + '\n')
            f.flush()
            n0 = ndone
            ndone += len(out)
            if ndone // 5000 > n0 // 5000:
                print('  %s: %d in %.0fs' % (what, ndone, time.time() - t0), flush=True)
            if budget and time.time() - t0 > budget:
                print('budget reached after %d %s (priority order); the rest is left for a later run' % (
                    ndone, what), flush=True)
                pool.terminate()
                return ndone, False


def chunks(keys, n=24):
    return [keys[i:i + n] for i in range(0, len(keys), n)]


def mutation_classes():
    """Representative of the mutation class of a table knot (mirror ignored), from the records of the mu pass."""
    import glob
    import gzip
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for fn in sorted(glob.glob(os.path.join(DATA, 'passes', 'mu', '*.jsonl.gz'))):
        with gzip.open(fn, 'rt') as f:
            for line in f:
                r = json.loads(line)
                if r.get('kind') == 'table' and r.get('dst'):
                    a, b = find(r['src'].rstrip('*')), find(r['dst'].rstrip('*'))
                    if a != b:
                        par[a] = b
    return find


def main():
    recs = list(F.iter_fillings())
    print('fillings:', len(recs), flush=True)
    # ---- (a) hyperbolic candidates
    # For an amphichiral node the fillings p/q and -p/q are the same manifold up to orientation; the
    # resulting S1 equations E(K; p/q) = E(K; -p/q) are implied by M = 0 (F5) and nu = 0 (C5), so only the
    # positive slopes of amphichiral table knots are kept as candidates (budget choice, nothing is lost).
    from mrcalc import knotinfo
    amph = {n for n, r in knotinfo.by_name().items() if r['amphichiral']}
    by_p = defaultdict(list)
    for r in recs:
        if r['kind'] == 'geo' and not (r['node'] in amph and r['p'] < 0):
            by_p[abs(r['p'])].append(r)
    kv = dict(x.split('=', 1) for x in sys.argv[1:] if '=' in x)
    budget = float(kv.get('budget', 0))        # time budget for the signature steps (seconds); 0: none
    procs = int(kv.get('procs', 4))
    prefilter = kv.get('prefilter', '1') != '0'
    compute = kv.get('compute', '1') != '0'
    out_path = kv.get('out', os.path.join(DATA, 'coincidences.jsonl'))
    # priority: clusters containing a node whose r_2 or r_0 is pinned in the last export
    prio = set()
    kpath = os.path.join(os.path.dirname(DATA), 'export', 'knots.jsonl')
    if os.path.exists(kpath + '.gz'):
        import gzip
        kopen, kpath = (lambda q: gzip.open(q, 'rt')), kpath + '.gz'
    else:
        kopen = open
    if os.path.exists(kpath):
        for line in kopen(kpath):
            k = json.loads(line)
            if 'r_2' in k['pins'] or 'r_0' in k['pins']:
                prio.add(k['node'])
    which = kv.get('which', 'all')
    mclass = mutation_classes()
    clusters = []                              # (rank, |p|, keys); rank 0: pinned r_2/r_0 node, 2: one mutation class
    for p, lst in by_p.items():
        lst.sort(key=lambda r: r['vol'])
        i = 0
        while i < len(lst):
            j = i
            while j + 1 < len(lst) and lst[j + 1]['vol'] - lst[j]['vol'] < 2e-7:
                j += 1
            if j > i:
                keys = sorted({(r['node'], r['p'], r['q']) for r in lst[i:j + 1]})
                if len(keys) > 1:
                    nodes = {k[0] for k in keys}
                    if len(nodes) > 1 and len({mclass(n) for n in nodes}) == 1:
                        rank = 2
                    else:
                        rank = 0 if any(k[0] in prio for k in keys) else 1
                    clusters.append((rank, p, keys))
            i = j + 1
    clusters.sort(key=lambda x: (x[0], x[1], x[2]))
    cand = set(k for _, _, keys in clusters for k in keys)
    print('volume-coincidence candidates: %d fillings in %d clusters (%d clusters with a pinned r_2/r_0 node, '
          '%d others, %d within one mutation class)' % (
              len(cand), len(clusters), sum(1 for x in clusters if x[0] == 0), sum(1 for x in clusters if x[0] == 1),
              sum(1 for x in clusters if x[0] == 2)), flush=True)
    work = [x for x in clusters if which == 'all' or x[0] < 2]        # the clusters this run computes
    sigs = {}
    if os.path.exists(SIG_CACHE):
        with open(SIG_CACHE) as f:
            for line in f:
                r = json.loads(line)
                sigs[(r['node'], r['p'], r['q'])] = r
    t0 = time.time()
    need = None                       # fillings that need a verified signature (None: all candidates)
    if prefilter:
        usig = {}
        if os.path.exists(USIG_CACHE):
            with open(USIG_CACHE) as f:
                for line in f:
                    r = json.loads(line)
                    usig[(r['node'], r['p'], r['q'])] = r
        todo, seen = [], set()
        for _, _, keys in work:                # priority order, one task per cluster group
            for k in keys:
                if k not in sigs and k not in usig and k not in seen:
                    seen.add(k)
                    todo.append(k)
        if not compute:
            todo = []
        nu, complete = run_pool(usig_task, chunks(todo), USIG_CACHE, usig, procs, budget, t0,
                                'unverified signatures')

        def h_of(k):
            if k in sigs:
                return sig_hash(sigs[k]['sig']) if sigs[k].get('sig') else None
            return usig[k]['h'] if k in usig else None
        need = set()
        nfail = 0
        for _, _, keys in work:
            if any(k not in sigs and k not in usig for k in keys):
                continue                       # not prefiltered yet (budget): left for a later run
            hs = [h_of(k) for k in keys]
            if None in hs:                     # no unverified signature: let the verified step decide
                nfail += 1
                need.update(keys)
                continue
            for k, h in zip(keys, hs):
                if hs.count(h) > 1:
                    need.add(k)
        print('prefilter: %d unverified signatures computed in %.0fs%s; %d fillings in clusters with equal '
              'unverified signatures or without one (%d clusters without one)' % (
                  nu, time.time() - t0, '' if complete else ' (incomplete)', len(need), nfail), flush=True)
    todo, queued = [], set()
    for _, _, keys in work:
        for k in keys:
            if k not in sigs and k not in queued and (need is None or k in need):
                queued.add(k)
                todo.append(k)
    if not compute:
        todo = []
    t1 = time.time()
    ndone, _complete = run_pool(sig_task, chunks(todo), SIG_CACHE, sigs, procs,
                                max(1.0, budget - (t1 - t0)) if budget else 0, t1, 'verified signatures')
    print('signatures: %d computed in %.0fs, %d candidates without signature' % (
        ndone, time.time() - t1, sum(1 for k in cand if k not in sigs)), flush=True)
    groups = defaultdict(list)
    for key in cand:
        r = sigs.get(key)
        if r and r.get('sig') and r.get('verified'):
            groups[r['sig']].append(key)
    out = []
    for sig, members in sorted(groups.items()):
        members = sorted(set(members))
        if len(members) < 2:
            continue
        a = members[0]
        for b in members[1:]:
            out.append({'A': a[0], 'sA': [a[1], a[2]], 'B': b[0], 'sB': [b[1], b[2]], 'cert': 'a',
                        'signature': sig, 'verified': True,
                        'orientation': 'isometry signature computed ignoring orientation'})
    na = len(out)
    # ---- (b), (c) Regina names
    torus, same = {}, {}                       # same: torus-knot node -> table node of the same knot
    for p, q in nodeset.torus_params():
        torus[names.torus_name(p, q)] = (p, q)
    cons = os.path.join(DATA, 'constructions.jsonl')
    if os.path.exists(cons):
        for line in open(cons):
            r = json.loads(line)
            if r.get('family') == 'torus' and 'node' in r:
                torus[r['node']] = (r['params']['p'], r['params']['q'])
                if r.get('chirality') != 'mirror' and r['construction'] != r['node']:
                    same[r['construction']] = r['node']
    by_name = defaultdict(list)
    moser_bad = []
    for r in recs:
        if r['kind'] != 'sfs' or not r.get('name'):
            continue
        if r['node'] in amph and r['p'] < 0:   # as in (a): -p/q on an amphichiral knot is p/q up to orientation
            continue
        cert = 'b'
        if r['node'] in torus:
            p, q = torus[r['node']]
            kind, orders = S.moser(p, q, r['p'], r['q'])
            if kind != 'sfs' or tuple(orders) != S.sfs_orders(r['name']):
                moser_bad.append((r['node'], r['p'], r['q'], r['name'], kind, orders))
                continue
            cert = 'c'
        by_name[r['name']].append((same.get(r['node'], r['node']), r['p'], r['q'], cert))
    for name, members in sorted(by_name.items()):
        members = sorted(set(members))
        if len(members) < 2:
            continue
        a = members[0]
        for b in members[1:]:
            cert = 'c' if 'c' in (a[3], b[3]) else 'b'
            out.append({'A': a[0], 'sA': [a[1], a[2]], 'B': b[0], 'sB': [b[1], b[2]], 'cert': cert,
                        'regina_name': name, 'orientation': 'names normalised up to orientation'})
    for i, c in enumerate(out):
        c['id'] = 's1-%d' % i
    with open(out_path + '.tmp', 'w') as f:
        for c in out:
            f.write(json.dumps(c, separators=(',', ':')) + '\n')
    os.replace(out_path + '.tmp', out_path)
    print('coincidences: %d hyperbolic (a), %d by Regina name (b/c); Moser/Regina disagreements: %d' % (
        na, len(out) - na, len(moser_bad)), flush=True)
    if moser_bad:
        print('  disagreements:', moser_bad[:10], flush=True)
    # data check: Regina lens names of torus fillings against Moser
    bad = 0
    for r in recs:
        if r['node'] in torus and r['kind'] == 'lens':
            p, q = torus[r['node']]
            kind, nm = S.moser(p, q, r['p'], r['q'])
            if kind != 'lens' or nm != r['name']:
                bad += 1
    print('torus lens fillings: Regina vs Moser disagreements: %d' % bad, flush=True)


if __name__ == '__main__':
    main()
