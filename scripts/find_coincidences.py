"""Surgery coincidences (section 6): S1 certificates from the filling records.

 (a) hyperbolic: fillings with equal |p| and volume (within 2e-7) are candidates; for each
     candidate the hyperbolic structure is verified (verify_hyperbolicity) and the verified
     isometry signature (orientation ignored) is computed; equal signatures certify an
     isometry.
 (b) both recognised by Regina with the same normalised Seifert fibred name.
 (c) one side is a torus-knot filling named by S2 (Moser): its Regina name is first checked
     against Moser's fibre orders.
Output: data/coincidences.jsonl (rewritten).
"""
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
    budget = float(kv.get('budget', 1500))     # default time budget for the signature step (seconds)
    # priority: clusters containing a node whose r_2 or r_0 is pinned in the last export
    prio = set()
    kpath = os.path.join(os.path.dirname(DATA), 'export', 'knots.jsonl')
    if os.path.exists(kpath):
        for line in open(kpath):
            k = json.loads(line)
            if 'r_2' in k['pins'] or 'r_0' in k['pins']:
                prio.add(k['node'])
    clusters = []
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
                    clusters.append((0 if any(k[0] in prio for k in keys) else 1, p, keys))
            i = j + 1
    clusters.sort(key=lambda x: (x[0], x[1], x[2]))
    cand = set(k for _, _, keys in clusters for k in keys)
    print('volume-coincidence candidates: %d fillings in %d clusters (%d clusters with a pinned r_2/r_0 node)' % (
        len(cand), len(clusters), sum(1 for x in clusters if x[0] == 0)), flush=True)
    sigs = {}
    if os.path.exists(SIG_CACHE):
        with open(SIG_CACHE) as f:
            for line in f:
                r = json.loads(line)
                sigs[(r['node'], r['p'], r['q'])] = r
    tasks, cur = [], []
    queued = set()
    for _, _, keys in clusters:
        for k in keys:
            if k not in sigs and k not in queued:
                queued.add(k)
                cur.append(k)
        if len(cur) >= 24:
            tasks.append(cur)
            cur = []
    if cur:
        tasks.append(cur)
    t0 = time.time()
    ndone = 0
    if tasks:
        with mp.Pool(4, maxtasksperchild=25) as pool, open(SIG_CACHE, 'a') as f:
            it = pool.imap(sig_task, tasks)
            while True:
                try:
                    out = it.next(timeout=900)
                except StopIteration:
                    break
                except mp.TimeoutError:
                    print('timeout waiting for a worker (a worker died?); continuing with the signatures '
                          'computed so far (rerun to resume)', flush=True)
                    pool.terminate()
                    break
                for r in out:
                    sigs[(r['node'], r['p'], r['q'])] = r
                    f.write(json.dumps(r, separators=(',', ':')) + '\n')
                f.flush()
                ndone += len(out)
                if time.time() - t0 > budget:
                    print('budget reached after %d of %d candidate signatures (priority order); the rest is '
                          'left for a later run' % (ndone, len(queued)), flush=True)
                    pool.terminate()
                    break
    print('signatures: %d computed in %.0fs, %d candidates without signature' % (
        ndone, time.time() - t0, sum(1 for k in cand if k not in sigs)), flush=True)
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
    torus = {}
    for p, q in nodeset.torus_params():
        torus[names.torus_name(p, q)] = (p, q)
    cons = os.path.join(DATA, 'constructions.jsonl')
    if os.path.exists(cons):
        for line in open(cons):
            r = json.loads(line)
            if r.get('family') == 'torus' and 'node' in r:
                torus[r['node']] = (r['params']['p'], r['params']['q'])
    by_name = defaultdict(list)
    moser_bad = []
    for r in recs:
        if r['kind'] != 'sfs' or not r.get('name'):
            continue
        cert = 'b'
        if r['node'] in torus:
            p, q = torus[r['node']]
            kind, orders = S.moser(p, q, r['p'], r['q'])
            if kind != 'sfs' or tuple(orders) != S.sfs_orders(r['name']):
                moser_bad.append((r['node'], r['p'], r['q'], r['name'], kind, orders))
                continue
            cert = 'c'
        by_name[r['name']].append((r['node'], r['p'], r['q'], cert))
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
    with open(os.path.join(DATA, 'coincidences.jsonl'), 'w') as f:
        for c in out:
            f.write(json.dumps(c, separators=(',', ':')) + '\n')
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
