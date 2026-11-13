"""Surgery coincidences (section 6): S1 certificates from the filling records.

 (a) hyperbolic: fillings with equal |p| and volume (within VOL_TOL = 1e-8; tol=<x> changes it) are candidates; for each
     candidate the hyperbolic structure is verified (verify_hyperbolicity) and the verified
     isometry signature (orientation ignored) is computed; equal signatures certify an
     isometry (a filling whose signature cannot be computed is compared with the other fillings of its
     cluster by SnapPy's isometry checker instead).  Prefilter (budget choice, prefilter=0 switches it off): the unverified isometry
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
are almost all of the candidates (138,378 of 138,752 clusters on the slope set |p| <= 30, q <= 4 of the prime
knots up to 13 crossings); all of them were tested by 2026-11-13 and in none did two signatures agree, while
most of the 374 other clusters contain a coincidence.  Clusters whose knots lie in one mutation class (classes
of the mu pass) are therefore tested last; which=nonmutant leaves them out of a run (signatures already in the
caches are used in any case).
Memory: the filling records are streamed shard by shard into arrays (mrcalc/candidates.py: 16 bytes per
hyperbolic filling instead of a Python dict of about 500); only the records that are not 'geo' (names) are kept
as dicts.  spill=<directory> keeps the arrays in files, one per |p|.
Nodes without a table diagram (census and 'H:' nodes): the diagram is the result diagram of the move that
produced the node (mrcalc/node_pd.py).  systematic=<n>: clusters whose nodes share at least n clusters also get
rank 2 (an order of the search for nodes the mu pass does not cover; on the table knots it marks exactly the
mutation-class clusters).
Scale: with which=nonmutant the rank-2 clusters are counted but not built as Python objects (only their
fillings that already have a verified signature are kept, so that what the caches certify is still written).
The cache of unverified signatures is a set of files data/filling_usig.jsonl, data/filling_usig.<n>.jsonl, each
below 45 MB; all are read, the last one is appended to.  Amphichiral nodes: table knots by the table, other
nodes by the flag of the last export (identification certificate); only their positive slopes are candidates.
usage: find_coincidences.py [budget=<seconds, 0: none>] [procs=4] [prefilter=1] [compute=1] [which=all|nonmutant]
                            [usig=<cache of unverified signatures>] [out=<path>] [spill=<directory>]
                            [systematic=<n, 0: off>] [tol=<volume tolerance>] [fill=<directory of filling shards>]
       compute=0: no new signatures, only the caches are used.
"""
import hashlib
import json
import multiprocessing as mp
import os
import signal
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import candidates as CAND, fillings as F, names, node_pd, nodeset, surgery as S  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

SIG_CACHE = os.path.join(DATA, 'filling_signatures.jsonl')


_ext = {}
_SRC = {}       # node -> the move that produced it, for candidate nodes without a table diagram (filled in main()
                # before the worker processes start)


def _exterior(node):
    """(exterior, per-exterior data of the unverified signatures) of a node; a worker keeps them for the last
    nodes it has seen."""
    if node not in _ext:
        if len(_ext) > 40:
            _ext.clear()
        E = S.exterior(node_pd.diagram(node, _SRC.get(node)))
        _ext[node] = (E, S.exterior_info(E))
    return _ext[node]


def sig_task(keys):
    """Verified isometry signatures of a list of (node, p, q) fillings."""
    out = []
    for node, p, q in keys:
        try:
            r = _twice(_exterior(node)[0], (p, q), True)
        except BaseException as e:           # cysignals' SignalError is a BaseException
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            r = None
        out.append({'node': node, 'p': p, 'q': q, 'sig': r['sig'] if r else None, 'verified': bool(r), 'hard': True})
    return out


def _twice(E, slope, verified, info=None):
    """The signature with the usual effort, then (hard attempt) with 40 randomisations."""
    try:
        r = S.hyperbolic_signature(E, slope, verified=verified, tries=10, info=info)
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        r = None
    return r or S.hyperbolic_signature(E, slope, verified=verified, tries=40, info=info)


USIG_CACHE = os.path.join(DATA, 'filling_usig.jsonl')
# Volumes are recorded to 9 decimals; two descriptions of one filling gave volumes within 1e-13 of each other
# (5e-10 after rounding) in every check made, so 1e-8 keeps all of them together.  Up to 2026-11-13 the
# tolerance was 2e-7; the smaller one removes 80% of the fillings of the accidental clusters and changes no
# cluster that contains a coincidence and no cluster of one mutation class.
VOL_TOL = 1e-8
USIG_LIMIT = 300                     # seconds per filling for the unverified signature (no key: the
#                                      verified step decides for that filling's cluster)


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def sig_hash(sig):
    return hashlib.sha256(sig.encode()).hexdigest()[:16]


def usig_task(keys):
    """Hashes of the unverified isometry signatures of a list of (node, p, q) fillings (None: no
    signature found)."""
    out = []
    for node, p, q in keys:
        try:
            E, info = _exterior(node)
            signal.signal(signal.SIGALRM, _alarm)
            signal.alarm(USIG_LIMIT)         # the tiling of the length spectrum can run away on a triangulation
            try:
                r = _twice(E, (p, q), False, info)
            finally:
                signal.alarm(0)
        except BaseException as e:           # cysignals' SignalError is a BaseException
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            r = None
        out.append({'node': node, 'p': p, 'q': q, 'h': sig_hash(r['sig']) if r else None, 'hard': True})
    return out


def run_pool(task, tasks, cache_path, store, procs, budget, t0, what):
    """Runs the tasks, appends the results to the cache (its last file; a new one is started at CACHE_PART
    bytes) and to store.  Returns (number of results, False if stopped by the budget or a worker timeout)."""
    ndone = 0
    if not tasks:
        return 0, True
    cache_path = cache_parts(cache_path)[-1]
    f = open(cache_path, 'a')
    try:
        with mp.Pool(procs, maxtasksperchild=25) as pool:
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
                if f.tell() > CACHE_PART:        # next file (no file above 50 MB in the repository)
                    f.close()
                    cache_path = next_part(cache_path)
                    f = open(cache_path, 'a')
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
    finally:
        f.close()


CACHE_PART = 45 * 1000 * 1000


def cache_parts(path):
    """The files of a cache: path, then path with .1, .2, ... before the extension (those that exist; at least
    [path])."""
    root, ext = os.path.splitext(path)
    out, i = [path], 1
    while os.path.exists('%s.%d%s' % (root, i, ext)):
        out.append('%s.%d%s' % (root, i, ext))
        i += 1
    return out


def next_part(path):
    """The cache file after `path` (a member of cache_parts())."""
    root, ext = os.path.splitext(path)
    base, _, n = root.rpartition('.')
    if base and n.isdigit():
        return '%s.%d%s' % (base, int(n) + 1, ext)
    return '%s.1%s' % (root, ext)


def chunks(keys, n=24):
    return [keys[i:i + n] for i in range(0, len(keys), n)]


ISO_CACHE = os.path.join(DATA, 'filling_isometries.jsonl')


def isometric(a, b):
    """True if SnapPy finds an isometry between the fillings a, b = (node, p, q), both with a verified
    hyperbolic structure; False if it finds none; None if a structure or the comparison is not available."""
    try:
        Ms = []
        for node, p, q in (a, b):
            M = S.verified_filling(S.exterior(node_pd.diagram(node, _SRC.get(node))), (p, q))
            if M is None:
                return None
            Ms.append(M)
        return bool(Ms[0].is_isometric_to(Ms[1]))
    except BaseException as e:               # cysignals' SignalError is a BaseException
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        return None


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
    kv = dict(x.split('=', 1) for x in sys.argv[1:] if '=' in x)
    # ---- (a) hyperbolic candidates
    # For an amphichiral node the fillings p/q and -p/q are the same manifold up to orientation; the
    # resulting S1 equations E(K; p/q) = E(K; -p/q) are implied by M = 0 (F5) and nu = 0 (C5), so only the
    # positive slopes of amphichiral table knots are kept as candidates (budget choice, nothing is lost).
    from mrcalc import knotinfo
    amph = {n for n, r in knotinfo.by_name().items() if r['amphichiral']}
    # priority: clusters containing a node whose r_2 or r_0 is pinned in the last export; the export also flags
    # the amphichiral nodes that are not table knots (certificate of their identification)
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
            if k.get('amphichiral'):
                amph.add(k['node'])
    recs = []                                  # the records that are not 'geo' (read by parts (b), (c) below)
    stats = {}
    parts, fnodes = CAND.load_parts(kv.get('fill', F.FILL_DIR), amph, spill=kv.get('spill'), keep_other=recs,
                                    stats=stats)
    print('fillings:', stats.get('records', 0), flush=True)
    budget = float(kv.get('budget', 0))        # time budget for the signature steps (seconds); 0: none
    procs = int(kv.get('procs', 4))
    prefilter = kv.get('prefilter', '1') != '0'
    compute = kv.get('compute', '1') != '0'
    usig_cache = kv.get('usig', USIG_CACHE)    # a long run appends to a copy outside the repository
    out_path = kv.get('out', os.path.join(DATA, 'coincidences.jsonl'))
    which = kv.get('which', 'all')
    vol_tol = float(kv.get('tol', VOL_TOL))
    mclass = mutation_classes()
    # (rank, |p|, keys) in the order (rank, |p|, keys); rank 0: pinned r_2/r_0 node, 2: one mutation class.
    # Same clusters as sorting each |p| by volume and chaining gaps below vol_tol (mrcalc/candidates.py).
    sigs = {}
    if os.path.exists(SIG_CACHE):
        with open(SIG_CACHE) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:                           # a line cut off by a restart of the machine
                    continue
                if r.get('sig') or r.get('hard'):          # an earlier failure without the hard attempt: again
                    sigs[(r['node'], r['p'], r['q'])] = r
                else:
                    sigs.pop((r['node'], r['p'], r['q']), None)
    T = CAND.cluster_ranked(parts, fnodes, CAND.class_ids(fnodes, mclass), CAND.prio_flags(fnodes, prio),
                            int(kv.get('systematic', 0)), vol_tol)
    del parts, fnodes                          # nothing large is left for the worker processes to inherit
    ncand, nrank = T.n_candidates(), [int((T.rank == i).sum()) for i in (0, 1, 2)]
    # The clusters as Python objects: all of them, or (which=nonmutant) those of rank 0 and 1, and of the
    # others the fillings that have a verified signature already (what the caches certify is always written).
    clusters = []
    for c in T.iter_clusters():
        if which != 'all' and c[0] == 2:
            keys = [k for k in c[2] if k in sigs]
            if not keys:
                continue
            c = (c[0], c[1], keys)
        clusters.append(c)
    del T
    cand = set(k for _, _, keys in clusters for k in keys)
    odd = {k[0] for k in cand if names.kind(k[0]) in ('census', 'hyp')}
    if odd:                                    # diagrams of nodes that nodeset.diagram() does not cover
        index = node_pd.build_index()
        _SRC.update({n: index[n]['source'] for n in odd if n in index})
        del index
    print('volume-coincidence candidates: %d fillings in %d clusters (%d clusters with a pinned r_2/r_0 node, '
          '%d others, %d within one mutation class)' % (ncand, sum(nrank), nrank[0], nrank[1], nrank[2]), flush=True)
    work = [x for x in clusters if which == 'all' or x[0] < 2]        # the clusters this run computes
    t0 = time.time()
    need = None                       # fillings that need a verified signature (None: all candidates)
    if prefilter:
        usig = {}
        for part in cache_parts(usig_cache):
            if not os.path.exists(part):
                continue
            with open(part) as f:
                for line in f:
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if r.get('h') or r.get('hard'):
                        usig[(r['node'], r['p'], r['q'])] = r
                    else:
                        usig.pop((r['node'], r['p'], r['q']), None)
        todo, seen = [], set()
        for _, _, keys in work:                # priority order, one task per cluster group
            for k in keys:
                if k not in sigs and k not in usig and k not in seen:
                    seen.add(k)
                    todo.append(k)
        if not compute:
            todo = []
        nu, complete = run_pool(usig_task, chunks(todo), usig_cache, usig, procs, budget, t0,
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
    # Fillings of a tested cluster that still have no verified signature: the certificate as S1(a) states it,
    # SnapPy finds an isometry between two fillings with verified hyperbolic structures (either orientation).
    iso = {}
    if os.path.exists(ISO_CACHE):
        with open(ISO_CACHE) as f:
            for line in f:
                r = json.loads(line)
                iso[(tuple(r['A']), tuple(r['B']))] = r['iso']
    nosig = {k for k in cand if k in sigs and not sigs[k].get('sig')}
    niso = 0
    with open(ISO_CACHE, 'a') as f:
        for _, _, keys in work:
            for a in keys:
                if a not in nosig:
                    continue
                for b in keys:
                    if b == a or (b in nosig and b < a):
                        continue
                    if (a, b) not in iso:
                        if not compute:
                            continue
                        iso[(a, b)] = isometric(a, b)
                        f.write(json.dumps({'A': list(a), 'B': list(b), 'iso': iso[(a, b)]}) + '\n')
                        f.flush()
                    if iso[(a, b)]:
                        niso += 1
                        out.append({'A': a[0], 'sA': [a[1], a[2]], 'B': b[0], 'sB': [b[1], b[2]], 'cert': 'a',
                                    'method': 'SnapPy is_isometric_to on verified hyperbolic fillings',
                                    'verified': True, 'orientation': 'isometry of either orientation'})
    print('fillings of tested clusters without verified signature: %d; isometries found by SnapPy: %d' % (
        sum(1 for _, _, keys in work for k in keys if k in nosig), niso), flush=True)
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
