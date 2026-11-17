"""A small chain for one pinned value: the recorded chain of an export, cut down (no rule is added or changed).

The chain files of an export hold, for a pin, every event that fed into it (the whole history of every node
used).  This program looks for a small set of rule instances of the same export that pins the same value:

  extract   reads <export>/constraints*.jsonl.gz once: the rule instances on the nodes within `radius` steps of
            the node (a step: two nodes of one rule instance) and on the nodes of the recorded chain; writes
            them to out=<file.pkl>.  Instances of the upsilon rules (domain U) are left out.
  minimize  solves the extracted instances with the solver of the project (the pin must come out with the
            value of the export); then, `tries` times with a random order: keeps only the instances of the
            chain of the pin until that set no longer shrinks, then drops every instance that can be dropped
            with the pin still coming out (first all instances of a node at once, then one by one).  The result
            is a set from which no single instance can be dropped; the smallest ones found are written as
            chain texts (the format of the chain files) and as JSON.

  miniexport  writes one of the sets found as an export directory of its own (constraints, events, chains,
            node and edge records), which checker/check.py checks and route.py prints.

usage: minimal_chain.py miniexport in=<minimal.json> [set=1] out=<dir>
       minimal_chain.py extract export=<dir> node=<name> chain=<chain file of the node> [radius=2] out=<file.pkl>
       minimal_chain.py minimize in=<file.pkl> inv=M [tries=40] [procs=3] [seed=1] [keep=5] out=<dir>
                        [avoid=<constraint id,...>]   instances that may not be used (for a second chain)
"""
import glob
import gzip
import json
import os
import pickle
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parts(export, stem):
    fs = glob.glob(os.path.join(export, stem + '*.jsonl.gz'))

    def key(f):
        m = re.search(r'\.(\d+)\.jsonl\.gz$', f)
        return int(m.group(1)) if m else 0
    return sorted(fs, key=key)


def extract(kv):
    export, node, radius = kv['export'], kv['node'], int(kv.get('radius', 2))
    t0 = time.time()
    chain_nodes = set()
    with open(kv['chain']) as f:
        for line in f:
            m = re.search(r' nodes=(.*?) par=', line)
            if m:
                chain_nodes.update(_split_nodes(m.group(1)))
    ix, names = {}, []
    pairs = set()
    n = 0
    for fn in parts(export, 'constraints'):
        with gzip.open(fn, 'rt') as f:
            for line in f:
                n += 1
                if '","' not in line.split('"nodes":[', 1)[1].split(']', 1)[0]:
                    continue                                   # one node
                c = json.loads(line)
                if c['dom'] == 'U':
                    continue
                ids = []
                for x in c['nodes']:
                    i = ix.get(x)
                    if i is None:
                        i = ix[x] = len(names)
                        names.append(x)
                    ids.append(i)
                for a in ids:
                    for b in ids:
                        if a < b:
                            pairs.add((a, b))
    print('%d constraints read, %d node pairs (%.0fs)' % (n, len(pairs), time.time() - t0), flush=True)
    adj = {}
    for a, b in pairs:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    del pairs
    ball = {ix[node]}
    frontier = set(ball)
    for d in range(1, radius + 1):
        nxt = set()
        for a in frontier:
            for b in adj.get(a, ()):
                if b not in ball:
                    nxt.add(b)
        ball |= nxt
        frontier = nxt
        print('radius %d: %d nodes' % (d, len(ball)), flush=True)
    keep = {names[i] for i in ball} | chain_nodes
    print('%d nodes of the recorded chain; %d nodes kept' % (len(chain_nodes), len(keep)), flush=True)
    rows = []
    for fn in parts(export, 'constraints'):
        with gzip.open(fn, 'rt') as f:
            for line in f:
                c = json.loads(line)
                if c['dom'] != 'U' and all(x in keep for x in c['nodes']):
                    rows.append(c)
    with open(os.path.join(export, 'parameters.json')) as f:
        par = json.load(f)
    with open(kv['out'], 'wb') as f:
        pickle.dump({'node': node, 'radius': radius, 'export': export, 'constraints': rows,
                     'slope_sets': par['slope_sets'], 'chain_nodes': sorted(chain_nodes)}, f, protocol=4)
    print('EXTRACT_DONE %d constraints on %d nodes -> %s (%.0fs)' % (len(rows), len(keep), kv['out'],
                                                                     time.time() - t0), flush=True)


def _split_nodes(s):
    """Node names of the `nodes=` field of a chain line (names may contain commas inside brackets)."""
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------------------------------------------------
_G = {}


def _solver(cons, record):
    from mrcalc import solver
    S = solver.Solver()
    S.keep, S.record = ('dom' if record else None), record
    S.add(cons)
    S.run()
    return S


def _pinned(cons):
    from mrcalc import solver
    try:
        S = _solver(cons, False)
    except solver.Contradiction:
        return False
    return S.pins(_G['node']).get(_G['inv']) == _G['value']


def _chain_rows(cons):
    """Indices (into cons) of the instances of the chain of the pin, or None if the pin does not come out."""
    from mrcalc import export
    S = _solver(cons, True)
    if S.pins(_G['node']).get(_G['inv']) != _G['value']:
        return None
    ev = S.pin_event[(_G['node'], _G['inv'])]
    ids = export.chain_events(S.events, [ev])
    return sorted({S.events.c[i] for i in ids})


def _shuffled(cons, rnd):
    """A random order in which the instances of F1 and C1 stay ahead of everything else: these two act on an
    untouched domain only (FORMAT.md 4.1, 4.2), and every solve of the project applies them first."""
    first = [c for c in cons if c['rule'] in ('F1', 'C1')]
    rest = [c for c in cons if c['rule'] not in ('F1', 'C1')]
    rnd.shuffle(rest)
    return first + rest


def one_try(seed):
    rnd = random.Random(seed)
    cons = _shuffled(_G['cons'], rnd)
    while True:                                   # the chain of the pin, until it no longer shrinks
        rows = _chain_rows(cons)
        if rows is None:
            return None
        if len(rows) == len(cons):
            break
        cons = _shuffled([cons[i] for i in rows], rnd)
    # all instances of a node at once (never the node itself), then single instances
    nodes = sorted({x for c in cons for x in c['nodes']} - {_G['node']})
    rnd.shuffle(nodes)
    for x in nodes:
        rest = [c for c in cons if x not in c['nodes']]
        if len(rest) < len(cons) and _pinned(rest):
            cons = rest
    changed = True
    while changed:
        changed = False
        order = list(range(len(cons)))
        rnd.shuffle(order)
        drop = set()
        for i in order:
            rest = [c for k, c in enumerate(cons) if k != i and k not in drop]
            if _pinned(rest):
                drop.add(i)
                changed = True
        cons = [c for k, c in enumerate(cons) if k not in drop]
    return sorted(c['id'] for c in cons)


def _init(G):
    from mrcalc import solver
    _G.update(G)
    solver.SLOPES.clear()
    solver.SLOPES.update({k: [tuple(x) for x in v] for k, v in G['slope_sets'].items()})


def chain_text(cons, node, inv):
    """The chain of the pin in the format of the chain files, from a solve of exactly these instances in
    the order given."""
    from mrcalc import export
    S = _solver(cons, True)
    ev = S.pin_event[(node, inv)]
    ids = export.chain_events(S.events, [ev])
    num = {i: k + 1 for k, i in enumerate(ids)}
    lines = []
    for i in ids:
        e = S.events[i]
        c = S.cons[S.events.c[i]]
        lines.append('%d. %s %s nodes=%s par=%s -> %s.%s: %s | in: %s' % (
            num[i], c['id'], e['rule'], ','.join(c['nodes']), json.dumps(c.get('par') or {}, sort_keys=True,
                                                                         separators=(',', ':')),
            e['node'], e['dom'], S.ev_dom[i].text(), ','.join(str(num[j]) for j in e['in'] if j in num) or '-'))
    lines.append('== %s = %s at %s : pinned at %d' % (inv, S.pins(node)[inv], node, num[ev]))
    return '\n'.join(lines) + '\n', len(ids)


def minimize(kv):
    import multiprocessing as mp
    from mrcalc import solver
    with open(kv['in'], 'rb') as f:
        D = pickle.load(f)
    inv, tries, procs = kv.get('inv', 'M'), int(kv.get('tries', 40)), int(kv.get('procs', 3))
    seed0, keep = int(kv.get('seed', 1)), int(kv.get('keep', 5))
    avoid = set(filter(None, kv.get('avoid', '').split(',')))
    cons = [solver.Con(c['id'], c['rule'], c['dom'], c['nodes'], c.get('par'), c.get('ref'))
            for c in D['constraints'] if c['id'] not in avoid]
    G = {'node': D['node'], 'inv': inv, 'value': None, 'cons': cons, 'slope_sets': D['slope_sets']}
    _init(G)
    t0 = time.time()
    S = _solver(cons, False)
    value = S.pins(D['node']).get(inv)
    print('%d instances: %s = %r at %s (%.0fs)' % (len(cons), inv, value, D['node'], time.time() - t0), flush=True)
    if value is None:
        raise SystemExit('the value is not pinned by the extracted instances')
    G['value'] = _G['value'] = value
    os.makedirs(kv['out'], exist_ok=True)
    found = {}
    with mp.Pool(procs, initializer=_init, initargs=(G,)) as pool:
        for k, ids in enumerate(pool.imap_unordered(one_try, range(seed0, seed0 + tries))):
            if ids is not None:
                found.setdefault(tuple(ids), 0)
                found[tuple(ids)] += 1
            best = min(len(x) for x in found) if found else None
            print('  try %d: %s instances; smallest so far %s; %d different sets (%.0fs)'
                  % (k + 1, len(ids) if ids else None, best, len(found), time.time() - t0), flush=True)
    by_id = {c['id']: c for c in cons}
    ranked = sorted(found, key=lambda x: (len(x), len({n for i in x for n in by_id[i]['nodes']}), x))
    out = []
    for r, ids in enumerate(ranked[:keep]):
        sub = sorted((by_id[i] for i in ids), key=lambda c: int(c['id'][1:]))
        if not _pinned(sub):
            raise SystemExit('a minimal set does not pin the value in the order of the export')
        text, nev = chain_text(sub, D['node'], inv)
        head = '# %s = %s at %s: %d rule instances on %d nodes, %d events; set %d of %d found (%d of %d tries)\n' % (
            inv, value, D['node'], len(ids), len({n for c in sub for n in c['nodes']}), nev, r + 1, len(found),
            found[ids], tries)
        with open(os.path.join(kv['out'], 'chain_%d.txt' % (r + 1)), 'w') as f:
            f.write(head + text)
        out.append({'instances': [c.to_dict() for c in sub], 'events': nev, 'found_in_tries': found[ids]})
        print(head.strip(), flush=True)
    with open(os.path.join(kv['out'], 'minimal.json'), 'w') as f:
        json.dump({'node': D['node'], 'inv': inv, 'value': value, 'export': D['export'], 'radius': D['radius'],
                   'instances_searched': len(cons), 'avoid': sorted(avoid), 'tries': tries, 'seed': seed0,
                   'sizes_found': sorted(len(x) for x in found), 'sets': out}, f, indent=1)
    print('MINIMIZE_DONE %d sets, sizes %s (%.0fs)' % (len(found), sorted(len(x) for x in found)[:10],
                                                       time.time() - t0), flush=True)


def miniexport(kv):
    """An export directory (FORMAT.md) that holds one of the sets of minimal.json and nothing else: its rule
    instances as they are in the export, the events of a solve of exactly these, the records of its nodes and
    edges.  checker/check.py and route.py read it like any export."""
    import csv
    from mrcalc import export as E, names, solver
    with open(kv['in']) as f:
        D = json.load(f)
    src, out = D['export'], kv['out']
    cons = D['sets'][int(kv.get('set', 1)) - 1]['instances']
    ids = {c['id'] for c in cons}
    full = []
    for fn in parts(src, 'constraints'):
        with gzip.open(fn, 'rt') as f:
            for line in f:
                if line.split('"id":"', 1)[1].split('"', 1)[0] in ids:
                    full.append(json.loads(line))
    assert len(full) == len(ids)
    with open(os.path.join(src, 'parameters.json')) as f:
        params = json.load(f)
    solver.SLOPES.clear()
    solver.SLOPES.update({k: [tuple(x) for x in v] for k, v in params['slope_sets'].items()})
    sol = solver.Solver()
    sol.add([{k: v for k, v in c.items() if k != 'fam'} for c in full])
    sol.run()
    os.makedirs(os.path.join(out, 'chains'), exist_ok=True)
    dumps = lambda o: json.dumps(o, separators=(',', ':'), sort_keys=True)   # noqa: E731
    with open(os.path.join(out, 'constraints.jsonl'), 'w') as f:
        for c in full:
            f.write(dumps(c) + '\n')
    with open(os.path.join(out, 'events.jsonl'), 'w') as f:
        for e in sol.events:
            f.write(dumps(e.to_dict()) + '\n')
    refs = {c['ref'] for c in full if isinstance(c.get('ref'), str)}
    with open(os.path.join(out, 'edges.jsonl'), 'w') as f:
        for fn in (parts(src, 'edges') if refs else []):
            with gzip.open(fn, 'rt') as g:
                for line in g:
                    if line.split('"id":"', 1)[1].split('"', 1)[0] in refs:
                        f.write(line)
    par = {'max_statement_text': E.MAX_TEXT, 'slope_sets': params['slope_sets'], 'scope': params['scope'],
           'versions': params['versions'], 'stats': {}, 'log': []}
    with open(os.path.join(out, 'parameters.json'), 'w') as f:
        f.write(dumps(par) + '\n')
    nodes = []
    for c in full:
        for n in c['nodes']:
            if n not in nodes:
                nodes.append(n)
    recs = {}
    for fn in parts(src, 'knots'):
        with gzip.open(fn, 'rt') as f:
            for line in f:
                if line.split('"node":"', 1)[1].split('"', 1)[0] in nodes:
                    r = json.loads(line)
                    recs[r['node']] = r
    cons_by_id = {c['id']: c for c in sol.cons}
    ev_text = [E.dom_text(d) for d in sol.ev_dom]
    rows = []
    with open(os.path.join(out, 'knots.jsonl'), 'w') as f:
        for n in nodes:
            rec = recs[n]
            pins = sol.pins(n)
            pe = {inv: sol.pin_event[(n, inv)] for inv in pins}
            rec['domains'] = {k: sol.get(n, k).to_json() for k in ('F', 'C', 'U')}
            rec['pins'] = pins
            rec['pin_events'] = pe
            rec['last_events'] = {k: sol.last[(n, k)] for k in ('F', 'C', 'U') if (n, k) in sol.last}
            rec['chain'] = ('chains/%s.txt' % names.file_name(n)) if pins else None
            f.write(dumps(rec) + '\n')
            rows.append(E.table_row(rec, sol, n))
            if pins:
                with open(os.path.join(out, 'chains', names.file_name(n) + '.txt'), 'w') as g:
                    g.write(E.chain_text(n, pins, pe, sol.events, ev_text, cons_by_id))
    with open(os.path.join(out, 'knots.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=E.COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print('MINIEXPORT_DONE %s: %d nodes, %d constraints, %d events; pins of %s: %s'
          % (out, len(nodes), len(full), len(sol.events), D['node'], sol.pins(D['node'])), flush=True)


if __name__ == '__main__':
    kv = dict(a.split('=', 1) for a in sys.argv[2:] if '=' in a)
    {'extract': extract, 'minimize': minimize, 'miniexport': miniexport}[sys.argv[1]](kv)
