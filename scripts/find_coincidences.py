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


def sig_task(args):
    node, slopes = args
    out = []
    try:
        E = S.exterior(nodeset.diagram(node))
    except Exception as e:
        return [{'node': node, 'p': p, 'q': q, 'sig': None, 'error': repr(e)} for p, q in slopes]
    for p, q in slopes:
        r = S.hyperbolic_signature(E, (p, q), verified=True, tries=10)
        out.append({'node': node, 'p': p, 'q': q, 'sig': r['sig'] if r else None,
                    'verified': bool(r)})
    return out


def main():
    recs = []
    for fn in sorted(os.listdir(F.FILL_DIR)):
        if fn.endswith('.jsonl'):
            with open(os.path.join(F.FILL_DIR, fn)) as f:
                recs.extend(json.loads(l) for l in f)
    print('fillings:', len(recs), flush=True)
    # ---- (a) hyperbolic candidates
    by_p = defaultdict(list)
    for r in recs:
        if r['kind'] == 'geo':
            by_p[abs(r['p'])].append(r)
    cand = set()
    for p, lst in by_p.items():
        lst.sort(key=lambda r: r['vol'])
        i = 0
        while i < len(lst):
            j = i
            while j + 1 < len(lst) and lst[j + 1]['vol'] - lst[j]['vol'] < 2e-7:
                j += 1
            if j > i:
                for r in lst[i:j + 1]:
                    cand.add((r['node'], r['p'], r['q']))
            i = j + 1
    print('volume-coincidence candidates:', len(cand), flush=True)
    sigs = {}
    if os.path.exists(SIG_CACHE):
        with open(SIG_CACHE) as f:
            for line in f:
                r = json.loads(line)
                sigs[(r['node'], r['p'], r['q'])] = r
    todo = defaultdict(list)
    for key in cand:
        if key not in sigs:
            todo[key[0]].append((key[1], key[2]))
    t0 = time.time()
    if todo:
        with mp.Pool(4) as pool, open(SIG_CACHE, 'a') as f:
            for out in pool.imap_unordered(sig_task, sorted(todo.items()), chunksize=4):
                for r in out:
                    sigs[(r['node'], r['p'], r['q'])] = r
                    f.write(json.dumps(r, separators=(',', ':')) + '\n')
    print('signatures computed for %d nodes in %.0fs' % (len(todo), time.time() - t0), flush=True)
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
