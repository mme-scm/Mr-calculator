"""What is left of M at given nodes when rules are withheld (section 10 on single nodes).

The problem is built as in the full run and solved without the rules of one family (mrcalc/solver.py FAMILIES)
or without the rules named; for every node asked for, the M candidates that remain are printed next to the
pins of the full run (from the ablation base of the full run, if given).  Nothing is exported.

usage: ablate_nodes.py withheld=<family | rule,rule,...> nodes=<name,name,... | @file> [upsilon]
                       [base=<ablation_base.pkl>] [out=<file.json>]
"""
import json
import os
import pickle
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import solve as S0  # noqa: E402
from mrcalc import prepare  # noqa: E402
from mrcalc.solver import FAMILIES  # noqa: E402


def m_candidates(dom):
    """The M values of a Dom2: a sorted list, or the interval [lo, hi] (None: unbounded) of a box."""
    if dom is None:
        return {'M': 'unconstrained'}
    if dom.items is not None:
        return {'M': sorted(dom.items)}
    mlo, mhi, rlo, absM = dom.box
    return {'M in': [mlo, mhi]}


def main():
    kv = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
    w = kv['withheld']
    rules = list(FAMILIES[w]) if w in FAMILIES else w.split(',')
    nodes = kv['nodes']
    if nodes.startswith('@'):
        with open(nodes[1:]) as f:
            nodes = [x.strip() for x in f if x.strip()]
    else:
        nodes = nodes.split(',')
    base = None
    if 'base' in kv:
        with open(kv['base'], 'rb') as f:
            base = pickle.load(f)
    t0 = time.time()
    problem = prepare.Problem(include_upsilon='upsilon' in sys.argv[1:])
    if base is not None and (len(problem.nodes), len(problem.cons)) != (base['nodes'], base['constraints']):
        raise SystemExit('the problem (%d nodes, %d constraints) is not the problem of the base (%d, %d)'
                         % (len(problem.nodes), len(problem.cons), base['nodes'], base['constraints']))
    S = S0.solve(problem, withheld=rules, keep=None, record=False)
    rows = []
    for n in nodes:
        if n not in problem.nodes:
            rows.append({'node': n, 'error': 'not a node'})
            continue
        row = {'node': n, 'withheld': m_candidates(S.state.get((n, 'F'))), 'withheld_pins': S.pins(n)}
        if base is not None:
            row['full_pins'] = base['pins'].get(n, {})
        rows.append(row)
    out = {'withheld': w, 'rules': rules, 'nodes': len(problem.nodes), 'constraints': len(problem.cons),
           'seconds': round(time.time() - t0, 1), 'rows': rows}
    if 'out' in kv:
        with open(kv['out'], 'w') as f:
            json.dump(out, f, indent=1)
    for r in rows:
        print(json.dumps(r, separators=(',', ':')), flush=True)
    lost = [r['node'] for r in rows if 'M' in r.get('full_pins', {}) and 'M' not in r.get('withheld_pins', {})]
    print('ABLATE_NODES_DONE withheld %s: %d nodes asked, M pinned in the full run and not here: %s (%.0fs)'
          % (w, len(rows), ', '.join(lost) or 'none', time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
