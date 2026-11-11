"""Worklist propagation to a fixpoint (section 8).

A constraint is a dict {id, rule, fam, dom, nodes, par, ref}.  `rule` is the catalogue ID; the
operator is selected by the rule.  Every narrowing is an event {id, c, rule, node, dom, in, dg}.
An empty domain raises Contradiction (the run stops, section 0).
"""
from __future__ import annotations

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


class Contradiction(Exception):
    def __init__(self, node, dom, cons, events):
        super().__init__('empty domain %s/%s by constraint %s' % (node, dom, cons.get('id')))
        self.node, self.dom, self.cons, self.events = node, dom, cons, events


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
    r, p = c['rule'], c['par']
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
        d2, dc = R.op_x(get(n0, 'F'), get(n0, 'C'), p)
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
        self.events = []
        self.cons = []
        self.watch = {}
        self.queue = deque()
        self.queued = set()
        self.withheld = set(withheld)
        self.napplied = 0

    def get(self, node, dom):
        d = self.state.get((node, dom))
        if d is None:
            d = top(dom)
            self.state[(node, dom)] = d
        return d

    def add(self, constraints):
        """Add constraints (incremental mode: only the new ones are queued)."""
        for c in constraints:
            if c['rule'] in self.withheld:
                continue
            i = len(self.cons)
            self.cons.append(c)
            for key in reads(c):
                self.watch.setdefault(key, []).append(i)
            self.queue.append(i)
            self.queued.add(i)

    def run(self):
        cons, state, last, events = self.cons, self.state, self.last, self.events
        while self.queue:
            i = self.queue.popleft()
            self.queued.discard(i)
            c = cons[i]
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
            ins = sorted({last[k] for k in keys if k in last})
            for node, dom, new in changed:
                ev = {'id': len(events), 'c': c['id'], 'rule': c['rule'], 'node': node, 'dom': dom,
                      'in': ins, 'dg': new.digest()}
                events.append(ev)
                state[(node, dom)] = new
                if new.is_empty():
                    raise Contradiction(node, dom, c, events)
            for node, dom, new in changed:
                last[(node, dom)] = [e['id'] for e in events[-len(changed):]
                                     if e['node'] == node and e['dom'] == dom][-1]
            for node, dom, new in changed:
                for j in self.watch.get((node, dom), ()):
                    if j not in self.queued:      # includes the constraint itself (idempotence check)
                        self.queue.append(j)
                        self.queued.add(j)
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
