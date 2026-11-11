"""Worklist propagation to a fixpoint (section 8).

A constraint is {id, rule, dom, nodes, par, ref} (class Con).  `rule` is the catalogue ID; the
operator is selected by the rule.  Every narrowing is an event {id, c, rule, node, dom, in, dg}.
An empty domain raises Contradiction (the run stops, section 0).

Constraints and events are kept as columns (ConTable, EvTable): the problems have millions of both,
and an object each does not fit in memory.  Con and Ev objects are built when one is read.
"""
from __future__ import annotations

import json
import sys
from array import array
from collections import deque

from . import rules as R
from .domains import Dom2, DomC, DomU

FAMILIES = {
    'I': ['F1', 'C1', 'C4', 'C5', 'F8', 'F11', 'F12', 'F13', 'F14', 'C10', 'C11', 'C12', 'C13', 'C14',
          '0_1', 'F5', 'U1', 'U2', 'U3', 'U4a', 'U7'],
    'unary': ['F15', 'F16', 'C8', 'C9', 'C15', 'U2a'],
    'cc': ['F7', 'C7', 'U5'],
    'twist': ['F9', 'U6'],
    'coincidence': ['S1', 'S2', 'S3', 'S4', 'F10'],
    'coupling': ['X1', 'X2', 'X3', 'X4', 'X5', 'X'],
    'mutation': ['F6'],
    'mirror_composite': ['F3', 'C3', 'F4', 'C6', 'U4b'],
}
RULE_FAMILY = {r: f for f, rs in FAMILIES.items() for r in rs}


PIN_COORDS = {'F': (('M', 'M'), ('r_2', 'r')), 'C': (('nu', 'nu'), ('r_0', 'r'), ('tau', 'tau')),
              'U': (('upsilon', 'upsilon'),)}
INVARIANTS = ['M', 'r_2', 'nu', 'r_0', 'tau', 'upsilon']
INV_DOM = {'M': 'F', 'r_2': 'F', 'nu': 'C', 'r_0': 'C', 'tau': 'C', 'upsilon': 'U'}


class Con:
    """One rule instance.  Read like the dict it replaces (c['rule'], c.get('par'), 'ref' in c)."""
    __slots__ = ('id', 'rule', 'dom', 'nodes', 'par', 'ref')

    def __init__(self, id, rule, dom, nodes, par=None, ref=None):
        self.id, self.rule, self.dom, self.nodes, self.par, self.ref = id, rule, dom, tuple(nodes), par, ref

    def __getitem__(self, k):
        v = getattr(self, k)
        if v is None:
            raise KeyError(k)
        return v

    def get(self, k, default=None):
        v = getattr(self, k, None)
        return default if v is None else v

    def __contains__(self, k):
        return getattr(self, k, None) is not None

    def to_dict(self):
        d = {'id': self.id, 'rule': self.rule, 'dom': self.dom, 'nodes': list(self.nodes)}
        if self.par is not None:
            d['par'] = self.par
        if self.ref is not None:
            d['ref'] = self.ref
        return d


def con_dict(c):
    """A constraint (Con or dict) as a dict."""
    return c.to_dict() if isinstance(c, Con) else dict(c)


DOMS = ('F', 'C', 'U', 'X')
DOM_CODE = {'F': 0, 'C': 1, 'U': 2, 'X': 3}
_EDGE_REF = 0x80000000
assert array('I').itemsize == 4 and array('i').itemsize == 4 and array('Q').itemsize == 8


class ConTable:
    """Constraints stored as columns; a Con is built when one is asked for (t[i], iteration).

    A constraint held as an object costs about 250 bytes (object, id, node tuple) and 130 more in the
    index of the solver; a row here costs 18 bytes.  Equal parameter dicts are stored once; a reference
    that is an edge id 'e<k>' is stored as the number k, any other reference as its JSON text."""

    def __init__(self):
        self.rule = array('B')          # index into rules
        self.dom = array('B')           # DOM_CODE
        self.n0 = array('I')            # first node (index into names)
        self.n1 = array('i')            # -1: no further node; >= 0: second node; <= -2: more[-v - 2]
        self.par = array('I')           # index into pars (0: none)
        self.ref = array('I')           # 0: none; _EDGE_REF | k: 'e<k>'; else index into refs
        self.rules, self.rule_ix = [], {}
        self.names, self.name_ix = [], {}
        self.pars, self.par_ix = [None], {}
        self.refs, self.ref_ix = [None], {}
        self.more = []                  # node indices after the first, for constraints on 3 or more nodes
        self.orig = None                # array: row -> row of the table this one is a part of (ids follow it)
        self.ids = None                 # list of ids, when they are not 'c<row>'

    def __len__(self):
        return len(self.rule)

    # ---- writing
    def node_index(self, name):
        i = self.name_ix.get(name)
        if i is None:
            i = self.name_ix[name] = len(self.names)
            self.names.append(name)
        return i

    def par_index(self, par, share=True):
        if not par:
            return 0
        if share:
            key = json.dumps(par, sort_keys=True)
            i = self.par_ix.get(key)
            if i is not None:
                return i
            self.par_ix[key] = len(self.pars)
        self.pars.append(par)
        return len(self.pars) - 1

    def ref_index(self, ref):
        if ref is None:
            return 0
        if isinstance(ref, str):
            k = ref[1:]
            if ref[:1] == 'e' and k.isdigit() and ref == 'e%d' % int(k) and int(k) < _EDGE_REF:
                return _EDGE_REF | int(k)
            key = ref
        elif isinstance(ref, bytes):         # JSON text prepared by the caller
            key = ref
        else:
            key = json.dumps(ref, separators=(',', ':')).encode('utf-8')
        i = self.ref_ix.get(key)
        if i is None:
            i = self.ref_ix[key] = len(self.refs)
            self.refs.append(key)
        return i

    def append(self, rule, dom, nodes, par=None, ref=None, share_par=True, id=None):
        i = len(self.rule)
        r = self.rule_ix.get(rule)
        if r is None:
            r = self.rule_ix[rule] = len(self.rules)
            self.rules.append(sys.intern(rule))
        ix = [self.node_index(n) for n in nodes]
        self.rule.append(r)
        self.dom.append(DOM_CODE[dom])
        self.n0.append(ix[0])
        if len(ix) == 1:
            self.n1.append(-1)
        elif len(ix) == 2:
            self.n1.append(ix[1])
        else:
            self.more.append(tuple(ix[1:]))
            self.n1.append(-len(self.more) - 1)
        self.par.append(self.par_index(par, share_par))
        self.ref.append(self.ref_index(ref))
        if self.orig is not None:
            raise RuntimeError('a part of another table cannot be extended')
        if self.ids is not None:
            self.ids.append(id if id is not None else 'c%d' % i)
        elif id is not None and id != 'c%d' % i:
            self.ids = ['c%d' % k for k in range(i)] + [id]
        return i

    def share_par(self, i):
        """Store the parameters of row i with the equal ones.  For a row appended with share_par=False
        (its dict is its own), after the dict was completed in place."""
        old = self.par[i]
        new = self.par_ix.setdefault(json.dumps(self.pars[old], sort_keys=True), old)
        if new != old:
            self.par[i] = new
            self.pars[old] = None

    # ---- reading
    def id_of(self, i):
        if self.ids is not None:
            return self.ids[i]
        return 'c%d' % (self.orig[i] if self.orig is not None else i)

    def nodes_of(self, i):
        names, b = self.names, self.n1[i]
        if b == -1:
            return (names[self.n0[i]],)
        if b >= 0:
            return (names[self.n0[i]], names[b])
        return (names[self.n0[i]],) + tuple(names[k] for k in self.more[-b - 2])

    def ref_of(self, i):
        v = self.ref[i]
        if v & _EDGE_REF:
            return 'e%d' % (v & 0x7fffffff)
        v = self.refs[v]
        return json.loads(v) if isinstance(v, bytes) else v

    def light(self, i):
        """Row i without id and reference (what an operator reads)."""
        return Con(None, self.rules[self.rule[i]], DOMS[self.dom[i]], self.nodes_of(i), self.pars[self.par[i]])

    def __getitem__(self, i):
        if i < 0:
            i += len(self.rule)
        return Con(self.id_of(i), self.rules[self.rule[i]], DOMS[self.dom[i]], self.nodes_of(i),
                   self.pars[self.par[i]], self.ref_of(i))

    def __iter__(self):
        for i in range(len(self.rule)):
            yield self[i]

    def rows_of(self, rules):
        """Rows whose rule is one of `rules`, in order."""
        codes = {self.rule_ix[r] for r in rules if r in self.rule_ix}
        if codes:
            col = self.rule
            for i in range(len(col)):
                if col[i] in codes:
                    yield i

    def of_rules(self, rules):
        for i in self.rows_of(rules):
            yield self[i]

    def without(self, rules):
        """The rows whose rule is not in `rules`: a table that shares names, parameters and references
        with this one and keeps the ids."""
        t = ConTable()
        t.rules, t.rule_ix, t.names, t.name_ix = self.rules, self.rule_ix, self.names, self.name_ix
        t.pars, t.par_ix, t.refs, t.ref_ix, t.more = self.pars, self.par_ix, self.refs, self.ref_ix, self.more
        drop = {self.rule_ix[r] for r in rules if r in self.rule_ix}
        t.orig = array('I')
        if self.ids is not None:
            t.ids = []
        for i in range(len(self.rule)):
            r = self.rule[i]
            if r in drop:
                continue
            t.rule.append(r)
            t.dom.append(self.dom[i])
            t.n0.append(self.n0[i])
            t.n1.append(self.n1[i])
            t.par.append(self.par[i])
            t.ref.append(self.ref[i])
            t.orig.append(self.orig[i] if self.orig is not None else i)
            if self.ids is not None:
                t.ids.append(self.ids[i])
        return t


class Ev:
    """One narrowing event.  Read like the dict it replaces."""
    __slots__ = ('id', 'c', 'rule', 'node', 'dom', 'ins', 'dg')

    def __init__(self, id, c, rule, node, dom, ins, dg):
        self.id, self.c, self.rule, self.node, self.dom, self.ins, self.dg = id, c, rule, node, dom, ins, dg

    def __getitem__(self, k):
        return self.ins if k == 'in' else getattr(self, k)

    def to_dict(self):
        return {'id': self.id, 'c': self.c, 'rule': self.rule, 'node': self.node, 'dom': self.dom,
                'in': list(self.ins), 'dg': self.dg}


class EvTable:
    """Events stored as columns; an Ev is built when one is asked for.  The rule of an event is the rule of
    its constraint; the id is the position."""

    def __init__(self, cons):
        self.cons = cons                # ConTable of the solver
        self.c = array('I')             # row of the constraint
        self.node = array('I')          # index into cons.names
        self.dom = array('B')
        self.dg = array('Q')            # digest (12 hex digits) as a number
        self.off = array('Q', [0])      # ins[off[i]:off[i+1]]: input events of event i
        self.ins = array('I')

    def __len__(self):
        return len(self.c)

    def add(self, c, node, dom, ins, dg):
        if len(dg) != 12:
            raise ValueError('digest %r' % (dg,))
        self.c.append(c)
        self.node.append(node)
        self.dom.append(dom)
        self.dg.append(int(dg, 16))
        self.ins.extend(ins)
        self.off.append(len(self.ins))
        return len(self.c) - 1

    def ins_of(self, i):
        return tuple(self.ins[self.off[i]:self.off[i + 1]])

    def rule_of(self, i):
        t = self.cons
        return t.rules[t.rule[self.c[i]]]

    def __getitem__(self, i):
        if i < 0:
            i += len(self.c)
        t, c = self.cons, self.c[i]
        return Ev(i, t.id_of(c), t.rules[t.rule[c]], t.names[self.node[i]], DOMS[self.dom[i]], self.ins_of(i),
                  '%012x' % self.dg[i])

    def __iter__(self):
        for i in range(len(self.c)):
            yield self[i]


class Contradiction(Exception):
    def __init__(self, node, dom, cons, events):
        super().__init__('empty domain %s/%s by constraint %s' % (node, dom, cons.get('id')))
        self.node, self.dom, self.cons, self.events = node, dom, cons, events


SLOPES = {}          # slope set id -> list of (p, q); filled by the problem / parameters
_slope_cache = {}


def resolve_slopes(spec):
    """(key, list) of a slope-set specification: an id, or {'base': id, 'extra': [[p,q],...]}."""
    if spec is None:
        return ('none', ())
    if isinstance(spec, str):
        return (spec, SLOPES[spec])
    key = (spec['base'], tuple(tuple(x) for x in spec['extra']))
    if key not in _slope_cache:
        base = list(SLOPES[spec['base']])
        have = set(map(tuple, base))
        _slope_cache[key] = (key, base + [tuple(x) for x in spec['extra'] if tuple(x) not in have])
    return _slope_cache[key]


def top(dom):
    if dom == 'F':
        return Dom2.top(1)
    if dom == 'C':
        return DomC.top()
    return DomU.top()


def reads(c):
    """(node, dom) pairs read (and possibly narrowed) by a constraint."""
    if c['rule'] == 'X':
        n = c['nodes'][0]
        return [(n, 'F'), (n, 'C')]
    return [(n, c['dom']) for n in c['nodes']]


def _diff_bounds(c):
    """Bounds lo <= x(B) - x(A) <= hi for the difference rules; nodes = [A, B]."""
    r, p = c['rule'], c.get('par') or {}
    if r in ('F7',):          # nodes [K-, K+]
        return 0, 4
    if r == 'C7':
        return 0, 1
    if r == 'U5':             # nodes [K+, K-]: upsilon(K-) - upsilon(K+) in [0, 1]
        return 0, 1
    a, b, h = p['a'], p['b'], p['h']
    if r == 'F9':             # nodes [K, K']
        return (-4 * a * b, (a - b) ** 2) if h > 0 else (-(a - b) ** 2, 4 * a * b)
    if r == 'U6':
        t = a * (a - 1) // 2 + b * (b - 1) // 2
        return (-t, a * b) if h > 0 else (-a * b, t)
    raise ValueError(r)


def apply(c, get):
    """Apply a constraint.  get(node, dom) -> current domain.  Returns [(node, dom, new)] for
    every domain the operator computed (unchanged ones are filtered by the caller)."""
    r, p, dom, ns = c['rule'], c.get('par') or {}, c['dom'], c['nodes']
    n0 = ns[0]
    if r == 'X':
        d2, dc = R.op_x(get(n0, 'F'), get(n0, 'C'), p, resolve_slopes(p.get('slopes')))
        return [(n0, 'F', d2), (n0, 'C', dc)]
    d = get(n0, dom)
    if r == 'F1':
        return [(n0, 'F', R.op_f1(d))]
    if r == 'C1':
        if d.items is None and d.box == (None, None, None, None, False, None):
            return [(n0, 'C', DomC(box=(None, None, None, None, False, 0)))]
        return [(n0, 'C', d)]
    if r == 'C4':
        if d.items is None:
            tlo, thi, nlo, nhi, c4, r0lo = d.box
            return [(n0, 'C', d if c4 else DomC(box=(tlo, thi, nlo, nhi, True, r0lo)))]
        return [(n0, 'C', R.keep(d, d.filter_keys(lambda k: abs(2 * k[0] - k[1]) <= 1)))]
    if r == '0_1':
        if dom == 'F':
            return [(n0, 'F', R.op_r2_value(R.op_m_range(d, 0, 0), 'eq', 0))]
        return [(n0, 'C', R.op_r0(R.op_c_range(d, 0, 0, 0, 0), 'eq', 0))]
    if r == 'F5':
        return [(n0, 'F', R.op_m_range(d, 0, 0))]
    if r == 'F8':
        bs = [4 * x for x in (p.get('c'), p.get('u')) if x is not None]
        if not bs:
            return [(n0, 'F', d)]
        return [(n0, 'F', R.op_m_range(d, -min(bs), min(bs)))]
    if r == 'F11':
        pp, q = p['p'], p['q']
        d = R.op_m_range(d, pp * q - pp - q, -4 * R.torus_upsilon(pp, q))
        return [(n0, 'F', R.op_r2_value(d, 'eqM'))]
    if r == 'F12':
        return [(n0, 'F', R.op_r2_value(R.op_m_range(d, 4 * p['n'], 4 * p['n']), 'eq', 4 * p['n']))]
    if r == 'F13':
        return [(n0, 'F', R.op_r2_value(R.op_m_range(d, 4 * p['tau'], 4 * p['tau']), 'eq', 4 * p['m']))]
    if r == 'F14':
        v = 2 * (p['p'] + p['q'] - 2)
        return [(n0, 'F', R.op_m_range(d, v, v))]
    if r == 'F15':
        return [(n0, 'F', R.op_f15(d, p.get('fibered'), p.get('tau'), p.get('g')))]
    if r == 'F16':
        return [(n0, 'F', R.op_f16(d, p['p'], p['q'], p.get('g')))]
    if r == 'F10':
        if dom == 'F':
            return [(n0, 'F', R.keep(d, R.op_e2_values(d, p['p'], p['q'], [abs(p['p'])])))]
        return [(n0, 'C', R.keep(d, R.op_ec_values(d, p['p'], p['q'], [abs(p['p'])])))]
    if r == 'C5':
        if p.get('why') == 'amphichiral':
            return [(n0, 'C', R.op_c_range(d, 0, 0, 0, 0))]
        g4 = p['g4']
        nb = max(2 * g4 - 1, 0)
        return [(n0, 'C', R.op_c_range(d, -g4, g4, -nb, nb))]
    if r == 'C8':
        return [(n0, 'C', R.op_c_range(d, p['tau'], p['tau']))]
    if r == 'C9':
        n, w = p['n'], p['w']
        return [(n0, 'C', R.op_c_range(d, R._cdiv(w - n + 1, 2), (w + n - 1) // 2, w - n, w + n))]
    if r == 'C10':
        if 'named' in p:
            return [(n0, 'C', R.op_r0(d, 'eq', p['named']))]
        return [(n0, 'C', R.op_c10(d, p.get('ge3', False), p.get('a', False), p.get('b', False)))]
    if r == 'C11':
        v = 2 * p['g'] - 1
        return [(n0, 'C', R.op_r0(R.op_c_range(d, nlo=v, nhi=v), 'eq', v))]
    if r == 'C12':
        return [(n0, 'C', R.op_r0(R.op_c_range(d, nlo=p['tau'], nhi=p['tau']), 'eq', p['m']))]
    if r == 'C13':
        if p['kind'] == 'n3m3':
            nu, r0 = 0, 4
        else:
            nu, r0 = 2 * p['n'] - 1, 6 * p['n'] - 1
        return [(n0, 'C', R.op_r0(R.op_c_range(d, nlo=nu, nhi=nu), 'eq', r0))]
    if r == 'C14':
        nu = 2 * p['n'] - 1
        num = p['norm'] + 2 * p['n'] - 3
        if num % 2:
            raise ArithmeticError('C14: non-integer r_0')
        return [(n0, 'C', R.op_r0(R.op_c_range(d, nlo=nu, nhi=nu), 'eq', num // 2))]
    if r == 'C15':
        return [(n0, 'C', R.op_c15(d))]
    if r in ('F3', 'C3') or (r == 'U4b' and p.get('kind') == 'mirror'):
        e = get(ns[1], dom)
        f = {'F': R.op_mirror2, 'C': R.op_mirrorC, 'U': R.op_mirrorU}[dom]
        a, b = f(d, e)
        return [(ns[0], dom, a), (ns[1], dom, b)]
    if r in ('F4', 'C6') or (r == 'U4b' and p.get('kind') == 'sum'):
        parts = [(get(n, dom), m) for n, m in zip(ns[1:], p['mult'])]
        f = {'F': R.op_sum_m, 'C': R.op_sum_c, 'U': R.op_sum_u}[dom]
        nN, nd = f(d, parts)
        return [(n0, dom, nN)] + [(n, dom, x) for n, x in zip(ns[1:], nd)]
    if r == 'F6':
        a, b = R.op_equal2(d, get(ns[1], 'F'))
        return [(ns[0], 'F', a), (ns[1], 'F', b)]
    if r in ('F7', 'F9', 'C7', 'U5', 'U6'):
        lo, hi = _diff_bounds(c)
        if 'coef' in p:           # the other end is the mirror image of this node
            f = {'F': R.op_self_m, 'C': R.op_self_tau, 'U': R.op_self_u}[dom]
            return [(n0, dom, f(d, p['coef'], lo, hi))]
        e = get(ns[1], dom)
        f = {'F': R.op_diff_m, 'C': R.op_diff_tau, 'U': R.op_diff_u}[dom]
        a, b = f(d, e, lo, hi)
        return [(ns[0], dom, a), (ns[1], dom, b)]
    if r in ('S1', 'S3', 'S4'):
        sA, sB = tuple(p['sA']), tuple(p['sB'])
        if len(ns) == 1:
            return [(n0, dom, R.op_eq_self(d, sA, p['a'], sB, p['b'], dom))]
        a, b = R.op_eq(d, sA, p['a'], get(ns[1], dom), sB, p['b'], dom)
        return [(ns[0], dom, a), (ns[1], dom, b)]
    if r in ('U4a', 'U2a', 'U3', 'U1', 'U7'):
        if r == 'U4a':
            if p.get('why') in ('slice', 'amphichiral', 'unknot'):
                return [(n0, 'U', R.op_u_range(d, 0, 0))]
            return [(n0, 'U', R.op_u_range(d, -p['g4'], p['g4']))]
        if r == 'U2a':
            return [(n0, 'U', R.op_u_range(d, -p['tau'], -p['tau']))]
        if r == 'U3':
            return [(n0, 'U', R.op_u_range(d, 0, 0))]
        if r == 'U1':
            return [(n0, 'U', R.op_u_range(d, p['value'], p['value']))]
        v = R.torus_upsilon(p['p'], p['q'])
        return [(n0, 'U', R.op_u_range(d, v, v))]
    raise ValueError('unknown rule %r' % r)


class Solver:
    def __init__(self, withheld=()):
        self.state = {}
        self.last = {}          # (node, dom) -> last event id
        self.cons = ConTable()
        self.events = EvTable(self.cons)
        self._shared = False    # cons is the table of the problem (not to be extended)
        # work list: the constraints fresh.. (never applied, in order) come first, then the queue
        self.fresh = 0
        self.queue = deque()
        self.queued = bytearray()       # per constraint: 1 while it waits (fresh or in the queue)
        self._woff = self._wtgt = None  # index (node, dom) -> constraints reading it, as two arrays
        self._windexed = -1
        self.withheld = set(withheld)
        self.napplied = 0
        self.pin_event = {}     # (node, coordinate) -> id of the event that pinned it
        # what is kept per event for the export: 'dom' the domain after the event (ev_dom), a function
        # domain -> text (ev_text; much smaller), or None
        self.keep = 'dom'
        self.ev_dom = []
        self.ev_text = []
        self._text = {}         # equal statement texts are stored once
        self.record = True      # False: no events (final domains and pins only; used by the ablation runs)

    def get(self, node, dom):
        d = self.state.get((node, dom))
        if d is None:
            d = top(dom)
            self.state[(node, dom)] = d
        return d

    def add(self, constraints):
        """Add constraints (incremental mode: only the new ones are queued).  The table of a problem is
        taken as it is (without the withheld rules), not copied row by row."""
        t = self.cons
        if isinstance(constraints, ConTable) and len(t) == 0 and not self._shared:
            t = constraints.without(self.withheld) if self.withheld else constraints
            self.cons = self.events.cons = t
            self._shared = True
        else:
            if self._shared:
                raise RuntimeError('constraints cannot be added to the table of a problem')
            for c in constraints:
                if c['rule'] in self.withheld:
                    continue
                t.append(c['rule'], c['dom'], c['nodes'], c.get('par'), c.get('ref'), id=c.get('id'))
        self.queued.extend(b'\x01' * (len(t) - len(self.queued)))

    def _index(self):
        """For every (node, dom) the constraints that read it, in increasing order: the rows
        wtgt[woff[k]:woff[k+1]] for k = 4 * (index of the node) + DOM_CODE."""
        t = self.cons
        n, K = len(t), 4 * len(t.names)
        rule, dom, n0, n1, more = t.rule, t.dom, t.n0, t.n1, t.more
        xr = t.rule_ix.get('X', -1)
        off = array('I', bytes(4 * (K + 1)))
        for i in range(n):
            a = n0[i] * 4
            if rule[i] == xr:
                off[a + 1] += 1
                off[a + 2] += 1
                continue
            d = dom[i] + 1
            off[a + d] += 1
            b = n1[i]
            if b >= 0:
                off[b * 4 + d] += 1
            elif b < -1:
                for m in more[-b - 2]:
                    off[m * 4 + d] += 1
        tot = 0
        for k in range(1, K + 1):
            tot += off[k]
            off[k] = tot
        pos = array('I', off)
        tgt = array('I', bytes(4 * tot))
        for i in range(n):
            a = n0[i] * 4
            if rule[i] == xr:
                tgt[pos[a]] = i
                pos[a] += 1
                tgt[pos[a + 1]] = i
                pos[a + 1] += 1
                continue
            d = dom[i]
            tgt[pos[a + d]] = i
            pos[a + d] += 1
            b = n1[i]
            if b >= 0:
                tgt[pos[b * 4 + d]] = i
                pos[b * 4 + d] += 1
            elif b < -1:
                for m in more[-b - 2]:
                    tgt[pos[m * 4 + d]] = i
                    pos[m * 4 + d] += 1
        self._woff, self._wtgt, self._windexed = off, tgt, n

    def run(self):
        t, state, last, events = self.cons, self.state, self.last, self.events
        if self._windexed != len(t):
            self._index()
        woff, wtgt, name_ix = self._woff, self._wtgt, t.name_ix
        queue, queued, n = self.queue, self.queued, len(t)
        text = self._text
        while True:
            if self.fresh < n:          # the fresh constraints are ahead of everything queued again
                i = self.fresh
                self.fresh += 1
            elif queue:
                i = queue.popleft()
            else:
                break
            queued[i] = 0
            c = t.light(i)
            self.napplied += 1
            keys = reads(c)
            before = {k: self.get(*k) for k in keys}
            out = apply(c, self.get)
            changed = []
            for node, dom, new in out:
                old = before[(node, dom)]
                if new is old or new == old:
                    continue
                changed.append((node, dom, new))
            if not changed:
                continue
            if not self.record:
                for node, dom, new in changed:
                    state[(node, dom)] = new
                    if new.is_empty():
                        raise Contradiction(node, dom, t[i], events)
            else:
                ins = tuple(sorted({last[k] for k in keys if k in last}))
                keep = self.keep
                first = len(events)
                for node, dom, new in changed:
                    ev = events.add(i, name_ix[node], DOM_CODE[dom], ins, new.digest())
                    if keep == 'dom':
                        self.ev_dom.append(new)
                    elif keep is not None:
                        x = keep(new)
                        self.ev_text.append(text.setdefault(x, x))
                    state[(node, dom)] = new
                    if new.is_empty():
                        raise Contradiction(node, dom, t[i], events)
                    for coord, co in PIN_COORDS[dom]:
                        if (node, coord) not in self.pin_event and new.pin(co) is not None:
                            self.pin_event[(node, coord)] = ev
                for k, (node, dom, new) in enumerate(changed):     # the last event of this application on it
                    last[(node, dom)] = first + k
            for node, dom, new in changed:
                k = name_ix[node] * 4 + DOM_CODE[dom]
                for p in range(woff[k], woff[k + 1]):
                    j = wtgt[p]
                    if not queued[j]:           # includes the constraint itself (idempotence check)
                        queued[j] = 1
                        queue.append(j)
        return self

    # ------------------------------------------------------------------
    def pins(self, node):
        out = {}
        f = self.state.get((node, 'F'))
        c = self.state.get((node, 'C'))
        u = self.state.get((node, 'U'))
        if f is not None:
            for name, co in (('M', 'M'), ('r_2', 'r')):
                v = f.pin(co)
                if v is not None:
                    out[name] = v
        if c is not None:
            for name, co in (('nu', 'nu'), ('r_0', 'r'), ('tau', 'tau')):
                v = c.pin(co)
                if v is not None:
                    out[name] = v
        if u is not None:
            v = u.pin()
            if v is not None:
                out['upsilon'] = v
        return out
