"""Re-solve and export.
usage: solve.py [upsilon] [ablation] [nochains] [plain] [out=<dir>] [runs=<name,name>]
       solve.py ablate [upsilon] [out=<dir>] [runs=..]   second phase of `ablation` (started by the first)
       solve.py ablate-run=<name> [upsilon] [out=<dir>]  one ablation run; prints its counts as one JSON line

ablation: the full run solves, exports and leaves a table of its pins; then every ablation run is a process
of its own (the problem is built again each time), so that the memory in use is that of one problem.
The runs are the rule families and single rules of section 10 and, for every group of passes of
config.PASS_ABLATIONS that has records, one run without the records of these passes (all rules used).
runs=: only the named ablation runs (tests).

plain: write uncompressed JSONL parts and one file per chain (default: gzip parts and chain archives)."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import export, prepare, solver  # noqa: E402
from mrcalc.config import EXPORT, PASS_ABLATIONS, ROOT  # noqa: E402
from mrcalc.solver import FAMILIES, INVARIANTS, RULE_FAMILY  # noqa: E402


def solve(problem, withheld=(), keep='dom', record=True):
    """keep: what the solver keeps per event for the chain texts ('dom', a text function, or None)."""
    solver.SLOPES.clear()
    solver.SLOPES.update(problem.slopes)
    S = solver.Solver(withheld=withheld)
    S.keep, S.record = keep, record
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
    with open(os.path.join(d, 'events.jsonl'), 'w') as f:
        for i in ids:
            f.write(json.dumps(events[i].to_dict()) + '\n')
    edge_ids = set()
    with open(os.path.join(d, 'constraints.jsonl'), 'w') as f:
        for row in sorted({int(events[i]['c'][1:]) for i in ids}):      # id 'c<row>' in the table of the problem
            c = problem.cons[row]
            f.write(json.dumps(solver.con_dict(c)) + '\n')
            if isinstance(c.get('ref'), str):
                edge_ids.add(c['ref'])
    cache = {}
    with open(os.path.join(d, 'edges.jsonl'), 'w') as f:
        for ed, r in problem.edge_records([problem.edges[int(x[1:])] for x in edge_ids]):
            f.write(json.dumps(export.expand_edge(ed, r, cache)) + '\n')
    with open(os.path.join(d, 'README.txt'), 'w') as f:
        f.write('Empty domain at node %s, domain %s, constraint %s\n' % (
            e.node, e.dom, json.dumps(solver.con_dict(e.cons))))
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
    for c in problem.cons.of_rules(('F4', 'C6')):
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


ABLATION_BASE = 'ablation_base.pkl'      # written by the full run, read by the ablation runs, then removed


def ablation_runs():
    runs = [(fam, list(rules)) for fam, rules in FAMILIES.items()]
    return runs + [(r, [r]) for r in ('F11', 'F12', 'F13', 'F14', 'C11', 'C12', 'C13', 'C14')]


def pass_ablation_runs():
    """Data ablations: the groups of passes of config.PASS_ABLATIONS that have records."""
    from mrcalc import passes
    have = set(pn for pn, shard, path in passes.pass_files())
    return [(name, list(ps)) for name, ps in PASS_ABLATIONS.items() if have & set(ps)]


def _core13(info):
    """Unknot, table knots and composites with at most 13 crossings (the tiers 0-13 of pins_by_tier.json)."""
    return (info is not None and info['kind'] in ('table', 'composite', 'unknot')
            and info['tier'] is not None and info['tier'] <= 13)


def write_ablation_base(problem, full, out_dir):
    """What an ablation run needs from the full run: its pins and, for every pin, the set of rules used by
    its chain (as a bit mask: own rule of every event of the chain)."""
    import pickle
    full_pins = {}
    for n in problem.nodes:
        p = full.pins(n)
        if p:
            full_pins[n] = p
    from array import array
    events = full.events
    bit = {}
    mask = array('Q')
    for e in range(len(events)):
        m = bit.setdefault(events.rule_of(e), 1 << len(bit))
        for i in events.ins_of(e):
            m |= mask[i]
        mask.append(m)
    pin_mask = {n: {inv: mask[full.pin_event[(n, inv)]] for inv in p} for n, p in full_pins.items()}
    with open(os.path.join(out_dir, ABLATION_BASE), 'wb') as f:
        pickle.dump({'pins': full_pins, 'mask': pin_mask, 'bit': bit, 'nodes': len(problem.nodes),
                     'constraints': len(problem.cons)}, f, protocol=4)


def ablation_run(name, out_dir, include_upsilon):
    """One ablation run in a process of its own (section 10): the problem is built again and solved without
    the rules of `name`; only counts are returned.  A lost pin whose chain in the full run uses no withheld
    rule is a violation."""
    import pickle
    t0 = time.time()
    skipped = dict(pass_ablation_runs()).get(name)
    if skipped is not None:
        return pass_ablation_run(name, skipped, out_dir, include_upsilon)
    rules = dict(ablation_runs())[name]
    with open(os.path.join(out_dir, ABLATION_BASE), 'rb') as f:
        base = pickle.load(f)
    problem = prepare.Problem(include_upsilon=include_upsilon)
    if (len(problem.nodes), len(problem.cons)) != (base['nodes'], base['constraints']):
        raise SystemExit('ablation run %s: the problem (%d nodes, %d constraints) is not the problem of the full '
                         'run (%d, %d)' % (name, len(problem.nodes), len(problem.cons), base['nodes'],
                                           base['constraints']))
    try:
        S = solve(problem, withheld=rules, keep=None, record=False)
    except solver.Contradiction as e:
        return {'withheld': name, 'rules': rules, 'error': str(e), 'pins': {i: None for i in INVARIANTS},
                'lost': {i: None for i in INVARIANTS}, 'violations': None}
    pins = pin_counts(problem, S)
    lost = {i: 0 for i in INVARIANTS}
    lost13 = {i: 0 for i in INVARIANTS}
    viol = changed = 0
    rs = 0
    for r in rules:
        rs |= base['bit'].get(r, 0)
    pin_mask = base['mask']
    for n, fp in base['pins'].items():
        now = S.pins(n)
        core = _core13(problem.nodes[n])
        for inv, v in fp.items():
            if inv not in now:
                lost[inv] += 1
                lost13[inv] += core
                if not (pin_mask[n][inv] & rs):
                    viol += 1
            elif now[inv] != v:
                changed += 1
    return {'withheld': name, 'rules': rules, 'pins': pins, 'lost': lost, 'lost_core': lost13, 'violations': viol,
            'changed_values': changed, 'seconds': round(time.time() - t0, 1)}


def pass_ablation_run(name, skipped, out_dir, include_upsilon):
    """Data ablation: the problem is built without the records of the passes `skipped` (fewer edges, and
    fewer peripheral nodes where a node was included because of these records) and solved with all rules.
    lost: pins of the full run that this run does not have.  The constraints of this run are constraints
    of the full run, so each of its pins must be a pin of the full run with the same value: the pins for
    which this fails are counted as violations."""
    import pickle
    t0 = time.time()
    with open(os.path.join(out_dir, ABLATION_BASE), 'rb') as f:
        base = pickle.load(f)
    del base['mask']
    already = set(filter(None, os.environ.get('MRCALC_SKIP_PASSES', '').split(',')))
    os.environ['MRCALC_SKIP_PASSES'] = ','.join(sorted(already | set(skipped)))
    problem = prepare.Problem(include_upsilon=include_upsilon)
    head = {'withheld': name, 'rules': [], 'passes': skipped}
    try:
        S = solve(problem, keep=None, record=False)
    except solver.Contradiction as e:
        return dict(head, error=str(e), pins={i: None for i in INVARIANTS}, lost={i: None for i in INVARIANTS},
                    violations=None)
    pins = pin_counts(problem, S)
    lost = {i: 0 for i in INVARIANTS}
    lost13 = {i: 0 for i in INVARIANTS}
    full = base['pins']
    for n, fp in full.items():
        info = problem.nodes.get(n)
        now = S.pins(n) if info is not None else {}
        core = _core13(info)
        for inv in fp:
            if inv not in now:
                lost[inv] += 1
                lost13[inv] += core
    viol = 0
    for n in problem.nodes:
        fp = full.get(n, {})
        for inv, v in S.pins(n).items():
            if inv not in fp or fp[inv] != v:
                viol += 1
    return dict(head, pins=pins, lost=lost, lost_core=lost13, violations=viol, nodes=len(problem.nodes),
                constraints=len(problem.cons), full_nodes=base['nodes'], full_constraints=base['constraints'],
                seconds=round(time.time() - t0, 1))


def ablation_driver(out_dir, include_upsilon, only=None):
    """Second phase of `solve.py ablation`: the full run has exported and left the process; every ablation
    run is a process of its own, one after the other, so that the memory in use is that of one problem.
    Writes ablation.json and the sheet `ablation` of knots.xlsx.  Exit code 3 if a run died."""
    import subprocess
    out, died = [], 0
    runs = [(name, {'rules': rules}) for name, rules in ablation_runs()]
    runs += [(name, {'rules': [], 'passes': ps}) for name, ps in pass_ablation_runs()]
    for name, head in runs:
        if only is not None and name not in only:
            continue
        t0 = time.time()
        cmd = [sys.executable, '-W', 'ignore', os.path.abspath(__file__), 'ablate-run=' + name, 'out=' + out_dir]
        proc = subprocess.run(cmd + (['upsilon'] if include_upsilon else []), stdout=subprocess.PIPE)
        res = None
        if proc.returncode == 0:
            try:
                res = json.loads(proc.stdout.decode().strip().split('\n')[-1])
            except ValueError:
                res = None
        if res is None:
            died += 1
            res = dict(head, withheld=name, error='run died (exit code %d)' % proc.returncode,
                       pins={i: None for i in INVARIANTS}, lost={i: None for i in INVARIANTS}, violations=None)
        out.append(res)
        print('ablation %-18s pins %s lost %s violations %s (%.0fs)' % (
            name, res['pins'], res['lost'], res['violations'], time.time() - t0), flush=True)
        with open(os.path.join(out_dir, 'ablation.json'), 'w') as f:
            json.dump(out, f, indent=1)
    export.write_ablation_sheet(out_dir, out)
    os.remove(os.path.join(out_dir, ABLATION_BASE))
    print('ablation: %d runs, %d died, %s violations' % (
        len(out), died, sum(r['violations'] or 0 for r in out)), flush=True)
    return 3 if died else 0


def main():
    args = sys.argv[1:]
    kv = dict(a.split('=', 1) for a in args if '=' in a)
    out_dir = kv.get('out', EXPORT)
    upsilon = 'upsilon' in args
    if 'ablate-run' in kv:
        print(json.dumps(ablation_run(kv['ablate-run'], out_dir, upsilon)), flush=True)
        return
    if 'ablate' in args:
        sys.exit(ablation_driver(out_dir, upsilon, kv['runs'].split(',') if 'runs' in kv else None))
    t0 = time.time()
    problem = prepare.Problem(include_upsilon=upsilon)
    print('problem: %d nodes, %d constraints, %d edges (%.0fs)' % (
        len(problem.nodes), len(problem.cons), len(problem.edges), time.time() - t0), flush=True)
    try:
        S = solve(problem, keep=None if 'nochains' in args else export.dom_text)
    except solver.Contradiction as e:
        d = dump_contradiction(problem, e, out_dir)
        print('EMPTY DOMAIN: %s -- minimal event/edge set exported to %s' % (e, d), flush=True)
        sys.exit(2)
    print('solved: %d events (%.0fs)' % (len(S.events), time.time() - t0), flush=True)
    counts = pin_counts(problem, S)
    print('pins:', counts, flush=True)
    abl = None
    if 'ablation' in args:
        write_ablation_base(problem, S, out_dir)
    elif os.path.exists(os.path.join(out_dir, 'ablation.json')):
        abl = json.load(open(os.path.join(out_dir, 'ablation.json')))
    val = validate(problem, S)
    print('validation: mirror violations %d / %d, composite violations %d / %d' % (
        val['n_mirror_violations'], val['mirror_checked'], val['n_composite_violations'], val['composite_checked']),
        flush=True)
    export.export_all(problem, S, out_dir, ablation=abl, write_chains='nochains' not in args,
                      pack='plain' not in args)
    with open(os.path.join(out_dir, 'summary.json'), 'w') as f:
        json.dump({'nodes': len(problem.nodes), 'constraints': len(problem.cons), 'edges': len(problem.edges),
                   'events': len(S.events), 'pins': counts, 'stats': dict(problem.stats), 'validation': val},
                  f, indent=1)
    print('exported to %s (%.0fs)' % (out_dir, time.time() - t0), flush=True)
    if 'ablation' in args:
        # the ablation runs start only after this process has given its memory back
        sys.stdout.flush()
        os.execv(sys.executable, [sys.executable, '-W', 'ignore', os.path.abspath(__file__), 'ablate',
                                  'out=' + out_dir] + (['upsilon'] if upsilon else []) +
                 (['runs=' + kv['runs']] if 'runs' in kv else []))


if __name__ == '__main__':
    main()
