"""Ranges of u_Z and u_R (rules N1-N5 of RULES_U.md) by bound propagation.

usage: solve_u.py out=<dir> [noqa]
  noqa   withholds rule N1q (the tabulated quasi-alternating knots that are not alternating)
MRCALC_SKIP_PASSES=a,b withholds passes (main passes and band-move passes alike).

Writes to <dir>:
  u_knots.csv            every node of the core (tiers 0-13): the two ranges
  u_summary.json, U_PINS.md   counts by crossing number
  u_events_Z.jsonl.gz, u_events_R.jsonl.gz    the events behind the bounds of the core nodes
  u_constraints.jsonl.gz the rule instances those events cite, with their pass records
  u_solve.log
Exit status 2 and u_contradiction.json: an empty interval (a bug: stop and report)."""
import collections
import csv
import gzip
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import prepare, usolve  # noqa: E402
from mrcalc.usolve import num_json  # noqa: E402

args = sys.argv[1:]
kv = dict(a.split('=', 1) for a in args if '=' in a)
OUT = kv['out']
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
LOG = open(os.path.join(OUT, 'u_solve.log'), 'w')


def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + '\n')
    LOG.flush()


def con_id(U, con):
    nm = U.names
    if con[0] == 'unary':
        return 'unary:%s:%s' % (nm[con[1]], con[2])
    if con[0] == 'amphichiral':
        return 'amph:%s' % nm[con[1]]
    if con[0] == 'mirror':
        return 'mirror:%s' % nm[con[1]]
    if con[0] == 'sum':
        return 'sum:%s' % nm[U.sums[con[1]][0]] + ':%d' % con[1]
    if con[0] == 'diff':
        return 'diff:%s|%s|%s' % (nm[con[1]], nm[con[2]], ('lo', 'hi')[con[3]])
    if con[0] == 'self':
        return 'self:%s|%s' % (nm[con[1]], ('lo', 'hi')[con[2]])
    raise ValueError(con)


def instance(U, src, rec):
    """The rule instance behind a constraint source: rule, from, to, parameters (u(to) - u(from))."""
    P = U.P
    if src[0] == 'e':
        key = rec['key']
        if len(key) == 2:
            return {'rule': 'N3', 'from': key[0], 'to': key[1], 'par': {'a': 1, 'b': 1, 'h': 1},
                    'note': 'crossing change K+ -> K-', 'record': rec}
        return {'rule': 'N3', 'from': key[0], 'to': key[1], 'par': {'a': key[2], 'b': key[3], 'h': key[4]},
                'record': rec}
    return {'rule': 'N4', 'from': P.canon(rec['src']), 'to': P.canon(rec['dst']), 'par': {'e': rec['e']},
            'record': rec}


def con_json(U, S, con, recs):
    nm = U.names
    out = {'id': con_id(U, con), 'type': con[0]}
    if con[0] == 'unary':
        par = [u for u in U.unary if u[0] == con[1] and u[2] == con[2]][0]
        out.update(node=nm[con[1]], rule=con[2], value=num_json(par[1]), par=par[3])
    elif con[0] == 'amphichiral':
        out.update(node=nm[con[1]], rule='N2m')
    elif con[0] == 'mirror':
        out.update(nodes=[nm[con[1]], nm[U.mirror[con[1]]]], rule='N2m')
    elif con[0] == 'sum':
        n, parts = U.sums[con[1]]
        out.update(node=nm[n], parts=[[nm[p], m] for p, m in parts], rule='N2s')
    elif con[0] == 'diff':
        d = U.diff[(con[1], con[2])]
        src = d[2 + con[3]]
        out.update(nodes=[nm[con[1]], nm[con[2]]], bound=('lo', 'hi')[con[3]], value=num_json(d[con[3]]),
                   instance=instance(U, src, recs[src]))
    elif con[0] == 'self':
        s = U.selfc[con[1]]
        src = s[2 + con[2]]
        out.update(node=nm[con[1]], mirror=nm[U.mirror[con[1]]], bound=('lo', 'hi')[con[2]],
                   value=num_json(s[con[2]]), instance=instance(U, src, recs[src]))
    return out


def width_class(lo, hi):
    if lo is None or hi is None:
        return 'unbounded'
    w = hi - lo
    return '0' if w == 0 else ('<=1' if w <= 1 else ('<=2' if w <= 2 else '>2'))


def main():
    P = prepare.Problem(include_upsilon=False)
    say('main problem: %d nodes, %d edges (%.0fs)' % (len(P.nodes), len(P.edges), time.time() - T0))
    qa = [] if 'noqa' in args else usolve.load_qa()
    U = usolve.UProblem(P, qa=qa)
    say('u problem: %d nodes, %d anchors, %d node pairs with a difference constraint, %d mirror-pair constraints, '
        '%d sums (%.0fs)' % (len(U.names), len(U.unary), len(U.diff), len(U.selfc), len(U.sums), time.time() - T0))
    say('stats: %s' % json.dumps(dict(U.stats), sort_keys=True))
    say('anchors by rule: %s' % json.dumps(collections.Counter(u[2] for u in U.unary), sort_keys=True))
    if U.violations:
        say('CONTRADICTION: %d constraints between a node and itself do not hold' % len(U.violations))
        recs = U.sources([v[3] for v in U.violations[:20]])
        with open(os.path.join(OUT, 'u_contradiction.json'), 'w') as f:
            json.dump({'kind': 'self-constraint', 'violations': [
                {'node': v[0], 'lo': v[1], 'hi': v[2], 'instance': instance(U, v[3], recs[v[3]])}
                for v in U.violations[:20]], 'count': len(U.violations)}, f, indent=1)
        sys.exit(2)
    solvers = {}
    for tag, integer in (('Z', True), ('R', False)):
        S = usolve.USolver(U, integer)
        try:
            S.run()
        except usolve.Contradiction as e:
            say('CONTRADICTION (u_%s): %s' % (tag, e))
            ids = S.closure(e.events)
            cons = {S.events[i][4] for i in ids}
            recs = U.sources({S.source_of(c) for c in cons} - {None})
            with open(os.path.join(OUT, 'u_contradiction.json'), 'w') as f:
                json.dump({'kind': 'empty interval', 'invariant': 'u_' + tag, 'node': e.node,
                           'events': [{'id': i, 'node': U.names[S.events[i][0]], 'side': ('lo', 'hi')[S.events[i][1]],
                                       'value': num_json(S.events[i][2]), 'rule': S.events[i][3],
                                       'con': con_id(U, S.events[i][4]), 'ins': list(S.events[i][5])} for i in ids],
                           'constraints': [con_json(U, S, c, recs) for c in sorted(cons, key=str)]}, f, indent=1)
            sys.exit(2)
        say('u_%s solved: %d events, %d queue steps (%.0fs)' % (tag, len(S.events), S.steps, time.time() - T0))
        solvers[tag] = S
    # ---- core table
    core = [n for n, info in P.nodes.items()
            if info['kind'] in ('table', 'composite', 'unknot') and info['tier'] is not None and info['tier'] <= 13]
    anchor = {}
    for n, v, rule, par in U.unary:
        anchor.setdefault(n, rule)
    Z, Rr = solvers['Z'], solvers['R']
    tiers = collections.defaultdict(lambda: collections.Counter())
    with open(os.path.join(OUT, 'u_knots.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['node', 'kind', 'crossings', 'anchor', 'uZ_lo', 'uZ_hi', 'uR_lo', 'uR_hi'])
        for n in core:
            i = U.ix[n]
            info = P.nodes[n]
            w.writerow([n, info['kind'], info['tier'], anchor.get(i, ''), num_json(Z.lo[i]), num_json(Z.hi[i]),
                        num_json(Rr.lo[i]), num_json(Rr.hi[i])])
            t = tiers[info['tier']]
            t['nodes'] += 1
            t['anchored'] += 1 if i in anchor or U.mirror[i] in anchor or U.mirror[i] == i else 0
            t['Z ' + width_class(Z.lo[i], Z.hi[i])] += 1
            t['R ' + width_class(Rr.lo[i], Rr.hi[i])] += 1
    summary = {str(t): dict(c) for t, c in sorted(tiers.items())}
    with open(os.path.join(OUT, 'u_summary.json'), 'w') as f:
        json.dump({'tiers': summary, 'stats': dict(U.stats), 'band_passes': sorted({b[0] for b in U.band_files}),
                   'quasi_alternating_used': len(qa)}, f, indent=1, sort_keys=True)
    cols = ['nodes', 'anchored', 'Z 0', 'Z <=1', 'Z <=2', 'Z >2', 'Z unbounded', 'R 0', 'R <=1', 'R <=2', 'R >2',
            'R unbounded']
    with open(os.path.join(OUT, 'U_PINS.md'), 'w') as f:
        f.write('Ranges of u_Z and u_R by crossing number (a knot and its mirror count separately; composites by '
                'crossing sum).\n"anchored": value given by rule N1 or N2 alone.  "Z 0" / "R 0": determined; the '
                'other columns: width of the range.\n\n')
        f.write('| cr | ' + ' | '.join(cols) + ' |\n|' + '---|' * (len(cols) + 1) + '\n')
        tot = collections.Counter()
        for t, c in sorted(tiers.items()):
            f.write('| %d | ' % t + ' | '.join(str(c.get(k, 0)) for k in cols) + ' |\n')
            tot.update(c)
        f.write('| all | ' + ' | '.join(str(tot.get(k, 0)) for k in cols) + ' |\n')
    say(open(os.path.join(OUT, 'U_PINS.md')).read())
    # ---- where further moves could decide an open core node (search planning; no rule is applied):
    # a node N joined to an open core node K by an instance of N3 or N4 such that some integer still possible
    # for u_Z(N) would leave one integer for u_Z(K)
    from math import ceil, floor
    open_set = {U.ix[n] for n in core if Z.lo[U.ix[n]] != Z.hi[U.ix[n]]}
    adj = {}
    for (a, b), d in U.diff.items():
        for K, N, l_, h_ in ((a, b, -d[1], -d[0]), (b, a, d[0], d[1])):       # l_ <= x(K) - x(N) <= h_
            if K not in open_set or (Z.lo[N] is not None and Z.lo[N] == Z.hi[N]):
                continue
            klo, khi = Z.lo[K], Z.hi[K]
            if klo is None or khi is None:
                continue
            vlo, vhi = ceil(klo - h_), floor(khi - l_)
            if Z.lo[N] is not None:
                vlo = max(vlo, Z.lo[N])
            if Z.hi[N] is not None:
                vhi = min(vhi, Z.hi[N])
            dec = []
            for v in range(vlo, vhi + 1):
                x, y = max(klo, ceil(v + l_)), min(khi, floor(v + h_))
                if x == y:
                    dec.append([v, x])
            if dec:
                adj.setdefault(N, {})[U.names[K]] = dec
    with open(os.path.join(OUT, 'u_adjacent.jsonl'), 'w') as f:
        for N in sorted(adj, key=lambda n: (-len(adj[n]), U.names[n])):
            info = P.nodes.get(U.names[N])
            f.write(json.dumps({'node': U.names[N], 'kind': info['kind'] if info else 'band-only',
                                'tier': info['tier'] if info else None, 'uZ': [num_json(Z.lo[N]), num_json(Z.hi[N])],
                                'decides': adj[N]}, separators=(',', ':')) + '\n')
    with open(os.path.join(OUT, 'u_open.txt'), 'w') as f:
        for n in core:
            if U.ix[n] in open_set and not n.endswith('*'):
                f.write(n + '\n')
    say('%d open core nodes; %d nodes joined to one of them whose value could decide it (%s)'
        % (len(open_set), len(adj), json.dumps(collections.Counter(
            (P.nodes[U.names[N]]['kind'] if U.names[N] in P.nodes else 'band-only') for N in adj))))
    # ---- the same with rule N4, or rule N1q, withheld (counts only)
    abl = {}
    for label, opt in (('without band moves (N4)', {'qa': qa, 'bands': False}),
                       ('without the tabulated quasi-alternating knots (N1q)', {'qa': [], 'bands': True})):
        if label.endswith('(N1q)') and not qa:
            continue
        U2 = usolve.UProblem(P, **opt)
        cnt = collections.Counter()
        for tag, integer in (('Z', True), ('R', False)):
            S2 = usolve.USolver(U2, integer).run()
            for n in core:
                i = U2.ix[n]
                if S2.lo[i] is not None and S2.lo[i] == S2.hi[i]:
                    cnt[tag] += 1
        abl[label] = dict(cnt)
        say('%s: determined u_Z %d, u_R %d of %d core nodes' % (label, cnt['Z'], cnt['R'], len(core)))
    with open(os.path.join(OUT, 'u_summary.json')) as f:
        sm = json.load(f)
    sm['withheld'] = abl
    with open(os.path.join(OUT, 'u_summary.json'), 'w') as f:
        json.dump(sm, f, indent=1, sort_keys=True)
    with open(os.path.join(OUT, 'U_PINS.md'), 'a') as f:
        f.write('\nDetermined (u_Z, u_R) of %d nodes when a rule is withheld:\n' % len(core))
        for label, c in abl.items():
            f.write('- %s: %d, %d\n' % (label, c.get('Z', 0), c.get('R', 0)))
    # ---- events behind the core bounds, and the constraints they cite
    cons = set()
    for tag, S in solvers.items():
        roots = []
        for n in core:
            i = U.ix[n]
            roots += [S.lo_ev[i], S.hi_ev[i]]
        ids = S.closure(roots)
        with gzip.open(os.path.join(OUT, 'u_events_%s.jsonl.gz' % tag), 'wt') as f:
            for k in ids:
                n, side, v, rule, con, ins = S.events[k]
                cons.add(con)
                f.write(json.dumps({'id': k, 'node': U.names[n], 'side': ('lo', 'hi')[side], 'value': num_json(v),
                                    'rule': rule, 'con': con_id(U, con), 'ins': list(ins)},
                                   separators=(',', ':')) + '\n')
        say('u_%s: %d events behind the bounds of the %d core nodes' % (tag, len(ids), len(core)))
    S = solvers['Z']
    recs = U.sources({S.source_of(c) for c in cons} - {None})
    with gzip.open(os.path.join(OUT, 'u_constraints.jsonl.gz'), 'wt') as f:
        for c in sorted(cons, key=lambda c: con_id(U, c)):
            f.write(json.dumps(con_json(U, S, c, recs), separators=(',', ':')) + '\n')
    say('%d constraints written (%.0fs)' % (len(cons), time.time() - T0))


main()
