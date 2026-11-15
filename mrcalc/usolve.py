"""Constraint propagation for the invariants u_Z and u_R (rules N1-N5, RULES_U.md).

The rules were supplied by the user on 2026-11-15 and are used exactly as stated there:

  N1t  u(T(p,q)) = upsilon(T(p,q))                 (value: the formula of rule U7)
  N1a  K alternating        =>  u(K) = sigma(K)/2  (tabulated: KnotInfo alternating, signature)
  N1q  K quasi-alternating  =>  u(K) = sigma(K)/2  (tabulated: KnotInfo quasi_alternating, signature)
  N2s  u(A # B) = u(A) + u(B)
  N2m  u(K*) = -u(K)                               (K = K*: u(K) = 0)
  N2z  K slice  =>  u(K) = 0                       (tabulated: smooth four-genus 0; the unknot)
  N3   K' = K with one right-handed full twist along a disc meeting K in a positive and b negative points,
       l = a - b, m = min(a, b):   -floor(l^2/4) <= u(K') - u(K) <= m - floor((|l|-1)^2/4)
       (a crossing change K+ -> K- is the case a = b = 1)
  N4   D1 = the smoothing of a crossing c of a diagram D0 of K0 that is a diagram of a knot K1,
       e = sign(c) - (writhe(D1) - writhe(D0)):   (e-2)/4 <= u(K1) - u(K0) <= (e+2)/4
  N5   u_Z is an integer (bounds of u_Z are rounded inwards); u_R is real.
  N6   u_M only (user, 2026-11-15: u_M satisfies the rules of u_Z and is mutation invariant):
       K, K' mutants  =>  u_M(K) = u_M(K')   (the mutation edges of the main problem, rule F6's instances)

A domain is an interval [lo, hi] with exact rational ends (None: unbounded).  Only bounds are propagated, so
the result is the range the instantiated rules leave, not a set of values.  Every narrowing is an event
(node, side, value, rule, constraint, input events); an empty interval raises Contradiction.

The nodes and the crossing-change and twist edges are those of the main problem (prepare.Problem); band moves
are read from the passes whose name starts with passes.BAND_PREFIX.
"""
import json
import os
from collections import defaultdict, deque
from fractions import Fraction
from math import ceil, floor

from . import names, passes
from . import rules as R


def n3_bounds(a, b, h):
    """Bounds of u(K') - u(K) for a full twist (h > 0 right-handed) on a + b strands."""
    l, m = abs(a - b), min(a, b)
    lo, hi = -(l * l // 4), m - ((l - 1) ** 2) // 4
    return (lo, hi) if h > 0 else (-hi, -lo)


def n4_bounds(e):
    """Bounds of u(K1) - u(K0) for a band move with the number e."""
    return Fraction(e - 2, 4), Fraction(e + 2, 4)


RULE_OF = {'e': 'N3', 'b': 'N4', 'm': 'N6'}      # rule of a constraint source


def _num(x):
    """Exact number: int when integral, Fraction otherwise."""
    if isinstance(x, Fraction) and x.denominator == 1:
        return x.numerator
    return x


def num_json(x):
    if x is None:
        return None
    x = _num(x)
    return x if isinstance(x, int) else '%d/%d' % (x.numerator, x.denominator)


def num_parse(s):
    if s is None or isinstance(s, int):
        return s
    return _num(Fraction(s))


class Contradiction(Exception):
    def __init__(self, node, events):
        Exception.__init__(self, 'empty interval at %s' % node)
        self.node, self.events = node, events


class UProblem:
    """Nodes and instantiated rules.  A constraint source is
         ('e', row)            crossing-change or twist edge of the main problem (rule N3)
         ('b', file, line)     band-move record (rule N4)
       and is turned into its record by sources()."""

    def __init__(self, P, qa=None, log=None, bands=True, mutation=False):
        self.P = P
        self.log = log or (lambda *a: None)
        self.names = []
        self.ix = {}
        self.mirror = []                 # node index -> index of the mirror node (itself if amphichiral)
        self.unary = []                  # (node, value, rule, parameters)
        self.sums = []                   # (node, [(part, multiplicity)])
        self.diff = {}                   # (a, b), a < b: [l, h, src_l, src_h]:  l <= x(b) - x(a) <= h
        self.selfc = {}                  # a: [lo, hi, src_lo, src_hi] from a constraint between a and its mirror
        self.violations = []             # a constraint between a node and itself that does not hold
        self.stats = defaultdict(int)
        self._skip = set(filter(None, os.environ.get('MRCALC_SKIP_PASSES', '').split(',')))
        self.qa = set(qa or ())
        self.mutation = mutation
        self._main_nodes()
        self._anchors()
        self._main_edges()
        self.band_files = [f for f in passes.pass_files(bands=True) if f[0] not in self._skip] if bands else []
        self._bands()
        self._structure()

    # ------------------------------------------------------------------
    def node(self, name):
        i = self.ix.get(name)
        if i is None:
            i = self.ix[name] = len(self.names)
            self.names.append(name)
            self.mirror.append(-1)
        return i

    def _main_nodes(self):
        P = self.P
        for n in P.nodes:
            self.node(n)
        for n, info in P.nodes.items():
            m = info['mirror']
            if m in P.nodes:
                self.mirror[self.ix[n]] = self.ix[m]
        self.n_main = len(self.names)

    def _add_extra(self, name):
        """A node that only band moves reach (and its mirror, and the summands of a connected sum)."""
        if name in self.ix:
            return self.ix[name]
        i = self.node(name)
        m = self.P.canon(names.mirror_name(name))
        j = i if m == name else self._add_extra(m)
        self.mirror[i] = j
        self.mirror[j] = i if self.mirror[j] in (-1, i) else self.mirror[j]
        self.stats['nodes reached by band moves only'] += 1
        if names.kind(name) == 'composite':
            for part in name.split('#'):
                self._add_extra(self.P.canon(part))
        return i

    # ------------------------------------------------------------------
    def _anchors(self):
        P = self.P
        for c in P.cons.of_rules(['U7']):
            p = c['par']
            self.unary.append((self.ix[c['nodes'][0]], R.torus_upsilon(p['p'], p['q']), 'N1t',
                               {'p': p['p'], 'q': p['q']}))
        for c in P.cons.of_rules(['U4a']):
            why = (c.get('par') or {}).get('why')
            if why in ('slice', 'unknot'):
                self.unary.append((self.ix[c['nodes'][0]], 0, 'N2z', {'why': why}))
        for n, info in P.nodes.items():
            ki = info.get('ki')
            if not ki or ki.get('signature') is None:
                continue
            base = n.rstrip('*')
            if ki.get('alternating'):
                rule = 'N1a'
            elif base in self.qa:
                rule = 'N1q'
            else:
                continue
            s = ki['signature']
            if s % 2:
                raise ValueError('odd signature tabulated for %s' % n)
            self.unary.append((self.ix[n], s // 2, rule, {'signature': s}))

    def _constraint(self, a, b, lo, hi, src):
        """lo <= x(b) - x(a) <= hi for node indices a, b."""
        if a == b:
            self.stats['constraints between a node and itself'] += 1
            if not lo <= 0 <= hi:
                self.violations.append((self.names[a], num_json(lo), num_json(hi), src))
            return
        if self.mirror[a] == b:                    # x(b) = -x(a):  -hi/2 <= x(a) <= -lo/2
            for n, l2, h2 in ((a, Fraction(-hi, 2), Fraction(-lo, 2)), (b, Fraction(lo, 2), Fraction(hi, 2))):
                s = self.selfc.get(n)
                if s is None:
                    self.selfc[n] = [l2, h2, src, src]
                else:
                    if l2 > s[0]:
                        s[0], s[2] = l2, src
                    if h2 < s[1]:
                        s[1], s[3] = h2, src
            return
        if a > b:
            a, b, lo, hi = b, a, -hi, -lo
        d = self.diff.get((a, b))
        if d is None:
            self.diff[(a, b)] = [lo, hi, src, src]
        else:
            if lo > d[0]:
                d[0], d[2] = lo, src
            if hi < d[1]:
                d[1], d[3] = hi, src

    def _main_edges(self):
        E = self.P.edges
        nm = E.names
        ix = self.ix
        for i in range(len(E)):
            t = E.t[i]
            if t == 0:                             # key (K+, K-): the case a = b = 1, right-handed
                lo, hi = n3_bounds(1, 1, 1)
            elif t == 1:                           # key (source, result, a, b, h)
                lo, hi = n3_bounds(E.a[i], E.b[i], E.h[i])
            elif self.mutation:                    # key: the sorted pair of mutants (rule N6, u_M only)
                self._constraint(ix[nm[E.k0[i]]], ix[nm[E.k1[i]]], 0, 0, ('m', i))
                self.stats['N6 instances'] += 1
                continue
            else:
                continue
            self._constraint(ix[nm[E.k0[i]]], ix[nm[E.k1[i]]], lo, hi, ('e', i))
            self.stats['N3 instances'] += 1

    def _bands(self):
        P = self.P
        for fi, (pn, shard, path) in enumerate(self.band_files):
            for li, r in enumerate(passes.iter_file_records(pn, shard, path)):
                self.stats['band records'] += 1
                if r.get('dst') is None:
                    self.stats['band records with an unidentified result'] += 1
                    continue
                if r['e'] != r['s'] - (r['w1'] - r['w0']):
                    raise ValueError('band record with a wrong e: %r' % (r,))
                if (r.get('cert') or {}).get('amphichiral'):
                    names.register_amphichiral(r['dst'])
                src, dst = P.canon(r['src']), P.canon(r['dst'])
                if names.kind(dst) == 'unidentified':
                    self.stats['band records with an unidentified result'] += 1
                    continue
                a = self.ix.get(src)
                if a is None:
                    a = self._add_extra(src)
                b = self.ix.get(dst)
                if b is None:
                    b = self._add_extra(dst)
                lo, hi = n4_bounds(r['e'])
                self._constraint(a, b, lo, hi, ('b', fi, li))
                self.stats['N4 instances'] += 1

    def _structure(self):
        """Mirror pairs and connected sums of the nodes that only band moves reach; those of the main nodes are
        read from the main problem (rule U4b rows carry the same structure)."""
        P = self.P
        for c in P.cons.of_rules(['U4b']):
            p = c['par']
            if p['kind'] == 'sum':
                ns = [self.ix[n] for n in c['nodes']]
                self.sums.append((ns[0], list(zip(ns[1:], p['mult']))))
        for i in range(self.n_main, len(self.names)):
            n = self.names[i]
            if names.kind(n) != 'composite':
                continue
            cnt = defaultdict(int)
            for part in n.split('#'):
                cnt[self.ix[P.canon(part)]] += 1
            self.sums.append((i, sorted(cnt.items())))
        for i, m in enumerate(self.mirror):
            if m == -1:
                raise ValueError('node %s without a mirror' % self.names[i])

    # ------------------------------------------------------------------
    def sources(self, srcs):
        """{source: record} for constraint sources (the representative pass records are read again)."""
        out = {}
        P = self.P
        es = sorted({s[1] for s in srcs if s[0] in ('e', 'm')})
        tag = {s[1]: s[0] for s in srcs if s[0] in ('e', 'm')}
        if es:
            for e, r in P.edge_records([P.edges[i] for i in es]):
                keep = {k: r[k] for k in ('pass', 'shard', 't', 'd', 'src', 'dst', 'i', 's', 'e', 'dirs', 'h', 'a', 'b',
                                           'w0', 'w1', 'cert', 'n', 'axis') if k in r}
                out[(tag[int(e.id[1:])], int(e.id[1:]))] = dict(keep, edge=e.id, key=list(e.key))
        bs = sorted(s for s in srcs if s[0] == 'b')
        by_file = defaultdict(set)
        for _, fi, li in bs:
            by_file[fi].add(li)
        for fi, lines in by_file.items():
            pn, shard, path = self.band_files[fi]
            for li, r in enumerate(passes.iter_file_records(pn, shard, path)):
                if li in lines:
                    out[('b', fi, li)] = {k: r[k] for k in ('pass', 'shard', 't', 'd', 'src', 'dst', 'i', 's', 'w0', 'w1',
                                                            'e', 'cert', 'n') if k in r}
        return out


class USolver:
    """Bound propagation.  integer=True: u_Z (rule N5), integer=False: u_R."""

    def __init__(self, U, integer):
        self.U = U
        self.integer = integer
        n = len(U.names)
        self.lo = [None] * n
        self.hi = [None] * n
        self.lo_ev = [-1] * n
        self.hi_ev = [-1] * n
        self.events = []        # (node, side, value, rule, constraint, input events)
        self.queue = deque()
        self.queued = bytearray(n)
        self.adj = None

    # value rounding of rule N5
    def _lo(self, v):
        return ceil(v) if self.integer else _num(v)

    def _hi(self, v):
        return floor(v) if self.integer else _num(v)

    def _set(self, n, side, v, rule, con, ins):
        if side == 0:
            v = self._lo(v)
            cur = self.lo[n]
            if cur is not None and v <= cur:
                return
            self.lo[n] = v
            self.lo_ev[n] = len(self.events)
        else:
            v = self._hi(v)
            cur = self.hi[n]
            if cur is not None and v >= cur:
                return
            self.hi[n] = v
            self.hi_ev[n] = len(self.events)
        self.events.append((n, side, v, rule, con, tuple(ins)))
        if self.lo[n] is not None and self.hi[n] is not None and self.lo[n] > self.hi[n]:
            raise Contradiction(self.U.names[n], [self.lo_ev[n], self.hi_ev[n]])
        if not self.queued[n]:
            self.queued[n] = 1
            self.queue.append(n)

    def _index(self):
        U = self.U
        adj = [[] for _ in U.names]
        for (a, b), d in U.diff.items():
            adj[a].append((0, b, d))            # x(b) - x(a) in [d0, d1]
            adj[b].append((1, a, d))            # x(a) - x(b) in [-d1, -d0]
        for k, (n, parts) in enumerate(U.sums):
            adj[n].append((2, k, None))
            for p, _ in parts:
                adj[p].append((2, k, None))
        self.adj = adj

    def _sum(self, k):
        U = self.U
        n, parts = U.sums[k]
        lo, hi, lo_ev, hi_ev = self.lo, self.hi, self.lo_ev, self.hi_ev
        con = ('sum', k)
        # the sum from its parts
        if all(lo[p] is not None for p, _ in parts):
            self._set(n, 0, sum(m * lo[p] for p, m in parts), 'N2s', con, [lo_ev[p] for p, _ in parts])
        if all(hi[p] is not None for p, _ in parts):
            self._set(n, 1, sum(m * hi[p] for p, m in parts), 'N2s', con, [hi_ev[p] for p, _ in parts])
        # a part from the sum and the other parts
        for j, (p, m) in enumerate(parts):
            others = parts[:j] + parts[j + 1:]
            if lo[n] is not None and all(hi[q] is not None for q, _ in others):
                v = Fraction(lo[n] - sum(mq * hi[q] for q, mq in others), m)
                self._set(p, 0, v, 'N2s', con, [lo_ev[n]] + [hi_ev[q] for q, _ in others])
            if hi[n] is not None and all(lo[q] is not None for q, _ in others):
                v = Fraction(hi[n] - sum(mq * lo[q] for q, mq in others), m)
                self._set(p, 1, v, 'N2s', con, [hi_ev[n]] + [lo_ev[q] for q, _ in others])

    def run(self):
        U = self.U
        if U.violations:
            raise Contradiction(U.violations[0][0], [])
        self._index()
        for n, v, rule, par in U.unary:
            self._set(n, 0, v, rule, ('unary', n, rule), ())
            self._set(n, 1, v, rule, ('unary', n, rule), ())
        for n, m in enumerate(U.mirror):
            if m == n:
                self._set(n, 0, 0, 'N2m', ('amphichiral', n), ())
                self._set(n, 1, 0, 'N2m', ('amphichiral', n), ())
        for n, s in U.selfc.items():
            self._set(n, 0, s[0], 'N2m+' + RULE_OF[s[2][0]], ('self', n, 0), ())
            self._set(n, 1, s[1], 'N2m+' + RULE_OF[s[3][0]], ('self', n, 1), ())
        lo, hi, lo_ev, hi_ev = self.lo, self.hi, self.lo_ev, self.hi_ev
        queue, queued, adj, mirror = self.queue, self.queued, self.adj, U.mirror
        steps = 0
        while queue:
            n = queue.popleft()
            queued[n] = 0
            steps += 1
            m = mirror[n]
            if m != n:
                if hi[n] is not None:
                    self._set(m, 0, -hi[n], 'N2m', ('mirror', min(n, m)), (hi_ev[n],))
                if lo[n] is not None:
                    self._set(m, 1, -lo[n], 'N2m', ('mirror', min(n, m)), (lo_ev[n],))
            for kind, x, d in adj[n]:
                if kind == 0:               # x(x) - x(n) in [d0, d1]
                    if lo[n] is not None:
                        self._set(x, 0, lo[n] + d[0], RULE_OF[d[2][0]], ('diff', n, x, 0), (lo_ev[n],))
                    if hi[n] is not None:
                        self._set(x, 1, hi[n] + d[1], RULE_OF[d[3][0]], ('diff', n, x, 1), (hi_ev[n],))
                elif kind == 1:             # x(n) - x(x) in [d0, d1]:  x(x) in [x(n) - d1, x(n) - d0]
                    if lo[n] is not None:
                        self._set(x, 0, lo[n] - d[1], RULE_OF[d[3][0]], ('diff', x, n, 1), (lo_ev[n],))
                    if hi[n] is not None:
                        self._set(x, 1, hi[n] - d[0], RULE_OF[d[2][0]], ('diff', x, n, 0), (hi_ev[n],))
                else:
                    self._sum(x)
        self.steps = steps
        return self

    # ------------------------------------------------------------------
    def source_of(self, con):
        """The constraint source (pass record reference) behind a constraint id of an event, or None."""
        U = self.U
        if con[0] == 'diff':
            return U.diff[(con[1], con[2])][2 + con[3]]
        if con[0] == 'self':
            return U.selfc[con[1]][2 + con[2]]
        return None

    def closure(self, roots):
        """Event ids needed for the given events, in increasing order."""
        seen = set()
        stack = [e for e in roots if e >= 0]
        while stack:
            e = stack.pop()
            if e in seen:
                continue
            seen.add(e)
            stack.extend(self.events[e][5])
        return sorted(seen)


def load_qa():
    """Names of the table knots tabulated as quasi-alternating and not alternating (data/knotinfo_qa.json)."""
    from .config import DATA
    p = os.path.join(DATA, 'knotinfo_qa.json')
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return json.load(f)['names']
