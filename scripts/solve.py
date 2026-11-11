"""Re-solve and export.
usage: solve.py [upsilon] [ablation] [nochains] [out=<dir>]"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import export, prepare, solver  # noqa: E402
from mrcalc.config import EXPORT, ROOT  # noqa: E402
from mrcalc.solver import FAMILIES, INVARIANTS, RULE_FAMILY  # noqa: E402


def solve(problem, withheld=()):
    solver.SLOPES.clear()
    solver.SLOPES.update(problem.slopes)
    S = solver.Solver(withheld=withheld)
    S.add(problem.cons)
    S.run()
    return S


def pin_counts(problem, S):
    c = {inv: 0 for inv in INVARIANTS}
    for n in problem.nodes:
        for k in S.pins(n):
            c[k] += 1
    return c


def dump_contradiction(problem, e, out_dir):
    """Section 0: export the minimal set of events and edges that produced an empty domain."""
    d = os.path.join(out_dir, 'contradiction')
    os.makedirs(d, exist_ok=True)
    events = e.events
    ids = export.chain_events(events, [len(events) - 1])
    cons = {c['id']: c for c in problem.cons}
    with open(os.path.join(d, 'events.jsonl'), 'w') as f:
        for i in ids:
            f.write(json.dumps(events[i]) + '\n')
    edge_ids = set()
    with open(os.path.join(d, 'constraints.jsonl'), 'w') as f:
        for cid in sorted({events[i]['c'] for i in ids}, key=lambda x: int(x[1:])):
            f.write(json.dumps(cons[cid]) + '\n')
            if isinstance(cons[cid].get('ref'), str):
                edge_ids.add(cons[cid]['ref'])
    cache = {}
    with open(os.path.join(d, 'edges.jsonl'), 'w') as f:
        for ed in problem.edges:
            if ed['id'] in edge_ids:
                f.write(json.dumps(export.expand_edge(ed, cache)) + '\n')
    with open(os.path.join(d, 'README.txt'), 'w') as f:
        f.write('Empty domain at node %s, domain %s, constraint %s\n' % (e.node, e.dom, json.dumps(e.cons)))
    return d


def validate(problem, S):
    """Section 10: mirror consistency and composite consistency of the final domains."""
    from mrcalc import rules as R
    bad_mirror = []
    for n, info in problem.nodes.items():
        m = info['mirror']
        if m not in problem.nodes:
            continue
        if S.get(m, 'F') != R.mirror2(S.get(n, 'F')) or S.get(m, 'C') != R.mirrorC(S.get(n, 'C')):
            bad_mirror.append(n)
            continue
        u, v = S.get(n, 'U'), S.get(m, 'U')
        if (v.lo, v.hi) != (None if u.hi is None else -u.hi, None if u.lo is None else -u.lo):
            bad_mirror.append(n)

    def proj(d, co):
        """finite projection as a set, or None if not enumerable"""
        if d.items is None:
            return None
        if co == 'M':
            return set(d.items)
        return {k[0 if co == 'tau' else 1] for k in d.items}
    bad_comp = []
    ncomp = 0
    for c in problem.cons:
        if c['rule'] not in ('F4', 'C6'):
            continue
        N, parts, mult = c['nodes'][0], c['nodes'][1:], c['par']['mult']
        dom = c['dom']
        for co, slack in ((('M', 0),) if dom == 'F' else (('tau', 0), ('nu', 1))):
            pn = proj(S.get(N, dom), co)
            ps = [proj(S.get(p, dom), co) for p in parts]
            if pn is None or any(p is None for p in ps):
                continue
            ncomp += 1
            if len(parts) == 1:
                sums = {mult[0] * x for x in ps[0]}
            else:
                sums = {x + y for x in ps[0] for y in ps[1]}
            allowed = {x + d for x in sums for d in range(-slack, slack + 1)}
            if not pn <= allowed:
                bad_comp.append((N, co))
    return {'mirror_checked': len(problem.nodes), 'mirror_violations': bad_mirror[:20],
            'n_mirror_violations': len(bad_mirror), 'composite_checked': ncomp,
            'composite_violations': bad_comp[:20], 'n_composite_violations': len(bad_comp)}


def ablation(problem, full):
    """Section 10: withhold one family at a time, and the listed family rules one at a time."""
    base = pin_counts(problem, full)
    full_pins = {n: full.pins(n) for n in problem.nodes}
    events = full.events
    anc_cache = {}

    def chain_rules(n, inv):
        key = full.pin_event[(n, inv)]
        if key not in anc_cache:
            anc_cache[key] = {events[i]['rule'] for i in export.chain_events(events, [key])}
        return anc_cache[key]
    runs = [(fam, rules) for fam, rules in FAMILIES.items()]
    runs += [(r, [r]) for r in ('F11', 'F12', 'F13', 'F14', 'C11', 'C12', 'C13', 'C14')]
    out = []
    for name, rules in runs:
        t0 = time.time()
        try:
            S = solve(problem, withheld=rules)
        except solver.Contradiction as e:
            out.append({'withheld': name, 'rules': rules, 'error': str(e), 'pins': {i: None for i in INVARIANTS},
                        'lost': {i: None for i in INVARIANTS}, 'violations': None})
            continue
        pins = pin_counts(problem, S)
        lost = {i: 0 for i in INVARIANTS}
        viol = 0
        changed = 0
        rs = set(rules)
        for n in problem.nodes:
            now = S.pins(n)
            for inv, v in full_pins[n].items():
                if inv not in now:
                    lost[inv] += 1
                    if not (chain_rules(n, inv) & rs):
                        viol += 1
                elif now[inv] != v:
                    changed += 1
        out.append({'withheld': name, 'rules': rules, 'pins': pins, 'lost': lost, 'violations': viol,
                    'changed_values': changed, 'seconds': round(time.time() - t0, 1)})
        print('ablation %-18s pins %s lost %s violations %d (%.0fs)' % (name, pins, lost, viol, time.time() - t0),
              flush=True)
    return out


def main():
    args = sys.argv[1:]
    kv = dict(a.split('=', 1) for a in args if '=' in a)
    out_dir = kv.get('out', EXPORT)
    t0 = time.time()
    problem = prepare.Problem(include_upsilon='upsilon' in args)
    print('problem: %d nodes, %d constraints, %d edges (%.0fs)' % (
        len(problem.nodes), len(problem.cons), len(problem.edges), time.time() - t0), flush=True)
    try:
        S = solve(problem)
    except solver.Contradiction as e:
        d = dump_contradiction(problem, e, out_dir)
        print('EMPTY DOMAIN: %s -- minimal event/edge set exported to %s' % (e, d), flush=True)
        sys.exit(2)
    print('solved: %d events (%.0fs)' % (len(S.events), time.time() - t0), flush=True)
    counts = pin_counts(problem, S)
    print('pins:', counts, flush=True)
    abl = None
    if 'ablation' in args:
        abl = ablation(problem, S)
        with open(os.path.join(out_dir, 'ablation.json'), 'w') as f:
            json.dump(abl, f, indent=1)
    elif os.path.exists(os.path.join(out_dir, 'ablation.json')):
        abl = json.load(open(os.path.join(out_dir, 'ablation.json')))
    val = validate(problem, S)
    print('validation: mirror violations %d / %d, composite violations %d / %d' % (
        val['n_mirror_violations'], val['mirror_checked'], val['n_composite_violations'], val['composite_checked']),
        flush=True)
    export.export_all(problem, S, out_dir, ablation=abl, write_chains='nochains' not in args)
    with open(os.path.join(out_dir, 'summary.json'), 'w') as f:
        json.dump({'nodes': len(problem.nodes), 'constraints': len(problem.cons), 'edges': len(problem.edges),
                   'events': len(S.events), 'pins': counts, 'stats': dict(problem.stats), 'validation': val},
                  f, indent=1)
    print('exported to %s (%.0fs)' % (out_dir, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
