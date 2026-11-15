"""What given nodes lose when rules are withheld (re-solves of the current data; nothing is exported).

usage: ablate_nodes.py <file with node names> out=<json> [sets=<name>:<rule>+<rule>,<name>:...]
Default sets: the surgery rules together and in groups:
  surgery: S1 S2 S3 S4 F10;  S1 (certified homeomorphic fillings);  cables: S3 S4;  lens: S2 F10.
For every node of the file: the values of M and r_2 still possible in the full solve and in each run."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mrcalc import prepare, solver  # noqa: E402

args = sys.argv[1:]
kv = dict(a.split('=', 1) for a in args if '=' in a)
names = [l.strip() for l in open([a for a in args if '=' not in a][0]) if l.strip()]
sets = [('surgery', ['S1', 'S2', 'S3', 'S4', 'F10']), ('S1', ['S1']), ('cables', ['S3', 'S4']), ('lens', ['S2', 'F10'])]
if 'sets' in kv:
    sets = [(x.split(':')[0], x.split(':')[1].split('+')) for x in kv['sets'].split(',')]
t0 = time.time()
P = prepare.Problem(include_upsilon=True)
print('problem: %d nodes (%.0fs)' % (len(P.nodes), time.time() - t0), flush=True)
out = {'nodes': names, 'runs': {}}


def run(label, withheld):
    solver.SLOPES.clear()
    solver.SLOPES.update(P.slopes)
    S = solver.Solver(withheld=withheld)
    S.keep, S.record = None, False
    S.add(P.cons)
    S.run()
    res = {}
    for n in names:
        d = S.get(n, 'F')
        pins = S.pins(n)
        res[n] = {'M': sorted(d.m_set()) if d.is_enum() else list(d.m_bounds()), 'M_pinned': pins.get('M'),
                  'r_2_pinned': pins.get('r_2')}
    out['runs'][label] = {'withheld': list(withheld), 'nodes': res}
    with open(kv['out'], 'w') as f:
        json.dump(out, f, indent=1)
    print('%s: M pinned on %d of %d nodes (%.0fs)' % (label, sum(1 for r in res.values() if r['M_pinned'] is not None),
                                                      len(names), time.time() - t0), flush=True)


run('full', ())
for label, rules in sets:
    run('without ' + label, rules)
print('ABLATE_DONE', flush=True)
