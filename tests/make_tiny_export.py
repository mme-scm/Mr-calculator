"""Regenerate tests/tiny_export, the small export used by tests/test_checker.py.

usage: python tests/make_tiny_export.py [output_dir]

Not a test.  The files are produced by the solver and the export functions of `mrcalc` (not by
the checker) from real records of export/: the constraints of a few nodes (at most two C9, F10,
F16 per node, to keep the files small) are solved again, and events, knots.jsonl, chains,
knots.csv, edges.jsonl and parameters.json are written in the format of export/FORMAT.md.
Run it again when the export format changes.
"""
import collections
import csv
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from mrcalc import export as E, names, solver as S  # noqa: E402

# 7_7 / 7_7*: mirror applications that emit two events; 10_44: crossing-change edges;
# 3_1#4_1: connected sum.
NODES = ['0_1', '3_1', '3_1*', '4_1', '3_1#4_1', '7_7', '7_7*', '10_44', '10_44*']


def dumps(o):
    return json.dumps(o, separators=(',', ':'), sort_keys=True)


def main(out):
    src = os.path.join(ROOT, 'export')
    keep = set(NODES)
    cons = []
    seen = collections.Counter()
    with open(os.path.join(src, 'constraints.jsonl')) as f:
        for line in f:
            c = json.loads(line)
            if not set(c['nodes']) <= keep:
                continue
            if c['rule'] in ('C9', 'F10', 'F16'):
                k = (c['nodes'][0], c['rule'], c['dom'])
                seen[k] += 1
                if seen[k] > 2:
                    continue
            cons.append(c)
    with open(os.path.join(src, 'parameters.json')) as f:
        params = json.load(f)
    S.SLOPES.clear()
    S.SLOPES.update({k: [tuple(x) for x in v] for k, v in params['slope_sets'].items()})
    sol = S.Solver()
    sol.add([{k: v for k, v in c.items() if k != 'fam'} for c in cons])
    sol.run()
    events = sol.events

    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, 'chains'))
    with open(os.path.join(out, 'constraints.jsonl'), 'w') as f:
        for c in cons:
            f.write(dumps(c) + '\n')
    with open(os.path.join(out, 'events.jsonl'), 'w') as f:
        for e in events:
            f.write(dumps(e.to_dict()) + '\n')
    refs = {c['ref'] for c in cons if isinstance(c.get('ref'), str)}
    with open(os.path.join(out, 'edges.jsonl'), 'w') as f, open(os.path.join(src, 'edges.jsonl')) as g:
        for line in g:
            if json.loads(line)['id'] in refs:
                f.write(line)
    par = {'max_statement_text': E.MAX_TEXT, 'slope_sets': params['slope_sets'], 'scope': params['scope'],
           'versions': params['versions'], 'stats': {}, 'log': []}
    with open(os.path.join(out, 'parameters.json'), 'w') as f:
        f.write(dumps(par) + '\n')
    cons_by_id = {c['id']: c for c in sol.cons}
    ev_text = [E.dom_text(d) for d in sol.ev_dom]
    recs = {}
    with open(os.path.join(src, 'knots.jsonl')) as f:
        for line in f:
            r = json.loads(line)
            if r['node'] in keep:
                recs[r['node']] = r
    rows = []
    with open(os.path.join(out, 'knots.jsonl'), 'w') as f:
        for n in NODES:
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
                    g.write(E.chain_text(n, pins, pe, events, ev_text, cons_by_id))
    with open(os.path.join(out, 'knots.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=E.COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print('%s: %d nodes, %d constraints, %d events' % (out, len(NODES), len(cons), len(events)))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'tests', 'tiny_export'))
