"""Operator soundness (section 10): random domains and random rule instances; brute force over a
window of the input domains must never find an admissible value that the operator excluded.
The admissibility predicates below are written directly from the rule statements."""
import itertools
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import solver  # noqa: E402
from mrcalc.domains import Dom2, DomC, DomU, RSet  # noqa: E402
from mrcalc.rules import torus_upsilon  # noqa: E402

MW = range(-40, 41, 4)
RW = range(0, 81, 4)
TW = range(-6, 7)
NW = range(-13, 14)
R0W = range(0, 41)
UW = range(-12, 13)
SLOPES = [(p, q) for q in (1, 2, 3) for p in range(-9, 10) if p and __import__('math').gcd(abs(p), q) == 1]
solver.SLOPES['S'] = SLOPES


def in2(d, M, r):
    if d.items is not None:
        return M in d.items and r in d.items[M]
    mlo, mhi, rlo, absM = d.box
    if M % d.step or r % d.step:
        return False
    return ((mlo is None or M >= mlo) and (mhi is None or M <= mhi) and (rlo is None or r >= rlo)
            and (not absM or r >= abs(M)))


def inc(d, t, n, r):
    if d.items is not None:
        return (t, n) in d.items and r in d.items[(t, n)]
    tlo, thi, nlo, nhi, c4, r0lo = d.box
    return ((tlo is None or t >= tlo) and (thi is None or t <= thi) and (nlo is None or n >= nlo)
            and (nhi is None or n <= nhi) and (not c4 or abs(2 * t - n) <= 1) and (r0lo is None or r >= r0lo))


def inu(d, u):
    return (d.lo is None or u >= d.lo) and (d.hi is None or u <= d.hi)


def tuples(d, kind):
    if kind == 'F':
        return [(M, r) for M in MW for r in RW if in2(d, M, r)]
    if kind == 'C':
        return [(t, n, r) for t in TW for n in NW for r in R0W if inc(d, t, n, r)]
    return [(u,) for u in UW if inu(d, u)]


def member(d, kind, t):
    return in2(d, *t) if kind == 'F' else inc(d, *t) if kind == 'C' else inu(d, *t)


def rand_rset(rng, step, lo, hi):
    vals = [v for v in range(lo, hi + 1, step) if rng.random() < 0.5]
    up = None
    if rng.random() < 0.5:
        up = rng.randrange(lo, hi + 1, step)
    return RSet(vals, up, None, step)


def rand2(rng):
    u = rng.random()
    if u < 0.15:
        return Dom2(4, box=(rng.choice([None, -8, -4]), None, None, True))
    if u < 0.25:
        return Dom2(4, box=(None, rng.choice([4, 8, 12]), rng.choice([None, 4]), True))
    its = {}
    for M in range(-16, 17, 4):
        if rng.random() < 0.55:
            lo = abs(M)
            its[M] = rand_rset(rng, 4, lo, lo + 28)
    return Dom2(4, items=its)


def randc(rng):
    u = rng.random()
    if u < 0.12:
        return DomC(box=(rng.choice([None, -2]), None, None, None, True, rng.choice([0, 3])))
    if u < 0.2:
        return DomC(box=(None, rng.choice([1, 3]), None, None, True, 0))
    its = {}
    for t in range(-3, 4):
        for n in (2 * t - 1, 2 * t, 2 * t + 1):
            if rng.random() < 0.45:
                its[(t, n)] = rand_rset(rng, 1, 0, 14)
    return DomC(items=its)


def randu(rng):
    lo = rng.choice([None, -5, -2, 0, 1])
    hi = rng.choice([None, 4, 2, 0, -1])
    if lo is not None and hi is not None and lo > hi:
        lo, hi = hi, lo
    return DomU(lo, hi)


RAND = {'F': rand2, 'C': randc, 'U': randu}


def phi2(M, p, q):
    return abs(p - q * M) + (2 if (q == 1 and p == M) else 0)


def E2(M, r, p, q):
    return q * r + phi2(M, p, q)


def EC(nu, r, p, q):
    return q * r + abs(p - q * nu)


def sgn(x):
    return (x > 0) - (x < 0)


# admissibility of a tuple (or tuple of tuples) under a constraint, straight from the catalogue
def admissible(c, ts):
    r, p = c['rule'], c.get('par') or {}
    a = ts[0]
    if r == 'F1':
        return a[0] % 4 == 0 and a[1] % 4 == 0 and a[1] >= abs(a[0])
    if r == 'C1':
        return a[2] >= 0
    if r == 'C4':
        return abs(2 * a[0] - a[1]) <= 1
    if r == '0_1':
        return all(x == 0 for x in a)
    if r == 'F5':
        return a[0] == 0
    if r == 'F8':
        bs = [4 * x for x in (p.get('c'), p.get('u')) if x is not None]
        return not bs or abs(a[0]) <= min(bs)
    if r == 'F11':
        P_, Q_ = p['p'], p['q']
        return P_ * Q_ - P_ - Q_ <= a[0] <= -4 * torus_upsilon(P_, Q_) and a[1] == a[0]
    if r == 'F12':
        return a == (4 * p['n'], 4 * p['n'])
    if r == 'F13':
        return a == (4 * p['tau'], 4 * p['m'])
    if r == 'F14':
        return a[0] == 2 * (p['p'] + p['q'] - 2)
    if r == 'F15':
        M, r2 = a
        if r2 == abs(M) != 0:
            fib, tau, g = p.get('fibered'), p.get('tau'), p.get('g')
            if fib is False:
                return False
            if None in (fib, tau, g):
                return True
            return fib and tau == sgn(M) * g and 2 * g <= abs(M)
        return True
    if r == 'F16':
        g = p.get('g')
        ok = a[0] * p['q'] < p['p']
        if g is not None:
            ok = ok and a[0] >= 4 * -((-(2 * g - 1)) // 4)
        return ok
    if r == 'F10':
        if c['dom'] == 'F':
            return E2(a[0], a[1], p['p'], p['q']) == abs(p['p'])
        return EC(a[1], a[2], p['p'], p['q']) == abs(p['p'])
    if r == 'C5':
        if p.get('why') == 'amphichiral':
            return a[0] == 0 and a[1] == 0
        return abs(a[0]) <= p['g4'] and abs(a[1]) <= max(2 * p['g4'] - 1, 0)
    if r == 'C8':
        return a[0] == p['tau']
    if r == 'C9':
        n, w = p['n'], p['w']
        return (w - n + 1) <= 2 * a[0] <= (w + n - 1) and w - n <= a[1] <= w + n
    if r == 'C10':
        if 'named' in p:
            return a[2] == p['named']
        ok = True
        if p.get('ge3'):
            ok = ok and a[2] >= 3
        if p.get('a'):
            ok = ok and not (a[2] + abs(1 - a[1]) == 3)
        if p.get('b'):
            ok = ok and not (a[2] == 3 and abs(a[1]) == 3)
        return ok
    if r == 'C11':
        return a[1] == a[2] == 2 * p['g'] - 1
    if r == 'C12':
        return a[1] == p['tau'] and a[2] == p['m']
    if r == 'C13':
        want = (0, 4) if p['kind'] == 'n3m3' else (2 * p['n'] - 1, 6 * p['n'] - 1)
        return (a[1], a[2]) == want
    if r == 'C14':
        return a[1] == 2 * p['n'] - 1 and 2 * a[2] == p['norm'] + 2 * p['n'] - 3
    if r == 'C15':
        return not any(a[2] + abs(n - a[1]) == n + 2 for n in range(1, 200))
    if r == 'X':
        (M, r2), (t, nu, r0) = ts
        ok = True
        sl = solver.resolve_slopes(p.get('slopes'))[1]
        if p.get('x1'):
            ok = ok and r2 - r0 >= abs(M - nu) and r2 >= r0
            ok = ok and all(E2(M, r2, pp, q) >= EC(nu, r0, pp, q) for pp, q in sl)
        if p.get('x2'):
            ok = ok and r2 > r0
        if p.get('x3_g') is not None:
            g = p['x3_g']
            ok = ok and all(E2(M, r2, pp, q) >= EC(nu, r0, pp, q) + 2 for pp, q in sl
                            if 0 < abs(pp) <= (2 * g - 1) * q)
        if p.get('x4'):
            ok = ok and r2 - r0 + abs(1 - M) - abs(1 - nu) > 0 and r2 - r0 + abs(1 + M) - abs(1 + nu) > 0
        if p.get('x5'):
            ok = ok and r2 - M >= r0 - nu + 2
        if p.get('x5m'):
            ok = ok and r2 + M >= r0 + nu + 2
        return ok
    if r in ('F3', 'C3') or (r == 'U4b' and p.get('kind') == 'mirror'):
        b = ts[1]
        if c['dom'] == 'F':
            return b == (-a[0], a[1])
        if c['dom'] == 'C':
            return b == (-a[0], -a[1], a[2])
        return b == (-a[0],)
    if r == 'F6':
        return ts[1] == a
    if r in ('F4', 'C6') or (r == 'U4b' and p.get('kind') == 'sum'):
        parts = ts[1:]
        m = p['mult']
        if c['dom'] == 'F':
            return a[0] == sum(mi * x[0] for mi, x in zip(m, parts))
        if c['dom'] == 'U':
            return a[0] == sum(mi * x[0] for mi, x in zip(m, parts))
        return (a[0] == sum(mi * x[0] for mi, x in zip(m, parts))
                and abs(a[1] - sum(mi * x[1] for mi, x in zip(m, parts))) <= 1)
    if r in ('F7', 'F9', 'C7', 'U5', 'U6'):
        lo, hi = solver._diff_bounds(c)       # bounds table; checked separately in test_diff_bounds
        xa = a[0]
        if 'coef' in p:
            return lo <= p['coef'] * xa <= hi
        return lo <= ts[1][0] - xa <= hi
    if r in ('S1', 'S3', 'S4'):
        (pA, qA), (pB, qB) = p['sA'], p['sB']
        f = (lambda t, pp, q: E2(t[0], t[1], pp, q)) if c['dom'] == 'F' else (lambda t, pp, q: EC(t[1], t[2], pp, q))
        b = ts[1] if len(ts) > 1 else a
        return p['a'] * f(a, pA, qA) == p['b'] * f(b, pB, qB)
    if r == 'U4a':
        if p.get('why') in ('slice', 'amphichiral', 'unknot'):
            return a[0] == 0
        return abs(a[0]) <= p['g4']
    if r == 'U2a':
        return a[0] == -p['tau']
    if r == 'U3':
        return a[0] == 0
    if r == 'U1':
        return a[0] == p['value']
    if r == 'U7':
        return a[0] == torus_upsilon(p['p'], p['q'])
    raise ValueError(r)


def rand_slope(rng):
    return list(rng.choice(SLOPES))


def rand_constraint(rng, rule):
    c = {'id': 'c0', 'rule': rule, 'nodes': ['A'], 'par': {}}
    p = c['par']
    dom = {'F': 'F', 'C': 'C', 'U': 'U', 'X': 'X', 'S': rng.choice('FC'), '0': rng.choice('FC')}[rule[0]]
    if rule == 'F10':
        dom = rng.choice('FC')
    c['dom'] = dom
    if rule == 'F8':
        p.update(c=rng.choice([None, 1, 2, 3]), u=rng.choice([None, 1, 2, 4]))
    elif rule in ('F11', 'U7'):
        pp, q = rng.choice([(2, 3), (2, 5), (3, 4), (3, 5), (2, 7)])
        p.update(p=pp, q=q)
    elif rule == 'F12':
        p.update(n=rng.randint(1, 4))
    elif rule in ('F13', 'C12'):
        p.update(m=rng.randint(1, 6), tau=rng.randint(-1, 1))
    elif rule == 'F14':
        p.update(p=rng.choice([3, 5]), q=rng.choice([3, 5, 7]))
    elif rule == 'F15':
        p.update(fibered=rng.choice([True, False, None]), tau=rng.choice([None, -2, -1, 0, 1, 2]),
                 g=rng.choice([None, 1, 2, 3]))
    elif rule == 'F16':
        p.update(p=rng.randint(1, 20), q=rng.randint(1, 3), g=rng.choice([None, 1, 2, 3, 4]))
    elif rule == 'F10':
        s = rand_slope(rng)
        p.update(p=s[0], q=s[1])
    elif rule == 'C5':
        if rng.random() < 0.2:
            p.update(why='amphichiral')
        else:
            p.update(g4=rng.randint(0, 3))
    elif rule == 'C8':
        p.update(tau=rng.randint(-2, 2))
    elif rule == 'C9':
        p.update(n=rng.randint(2, 5), w=rng.randint(-6, 6))
    elif rule == 'C10':
        if rng.random() < 0.2:
            p.update(named=rng.choice([1, 2]))
        else:
            p.update(ge3=rng.random() < 0.7, a=rng.random() < 0.7, b=rng.random() < 0.7)
    elif rule == 'C11':
        p.update(g=rng.randint(1, 4))
    elif rule == 'C13':
        p.update(kind=rng.choice(['n3m3', 'odd32']), n=rng.randint(1, 3))
    elif rule == 'C14':
        n = rng.randint(1, 3)
        p.update(n=n, norm=2 * rng.randint(1, 8) + 1)
    elif rule == 'X':
        p.update(x1=rng.random() < 0.8, x2=rng.random() < 0.8, x4=rng.random() < 0.8, x5=rng.random() < 0.5,
                 x5m=rng.random() < 0.5, slopes='S')
        if rng.random() < 0.6:
            p['x3_g'] = rng.randint(1, 4)
    elif rule in ('F3', 'C3', 'F6'):
        c['nodes'] = ['A', 'B']
    elif rule == 'U4b':
        if rng.random() < 0.5:
            c['nodes'] = ['A', 'B']
            p.update(kind='mirror')
        else:
            p.update(kind='sum')
    elif rule in ('F7', 'C7', 'U5', 'F9', 'U6'):
        if rule in ('F9', 'U6'):
            p.update(a=rng.randint(0, 3), b=rng.randint(0, 3), h=rng.choice([1, -1]))
        if rng.random() < 0.25:
            p.update(coef=rng.choice([-2, 2]))
        else:
            c['nodes'] = ['A', 'B']
    elif rule in ('S1', 'S3', 'S4'):
        p.update(sA=rand_slope(rng), sB=rand_slope(rng), a=1, b=rng.choice([1, 1, 2, 3]))
        if rng.random() < 0.75:
            c['nodes'] = ['A', 'B']
    elif rule == 'U4a':
        if rng.random() < 0.3:
            p.update(why=rng.choice(['slice', 'amphichiral', 'unknot']))
        else:
            p.update(g4=rng.randint(0, 4))
    elif rule == 'U2a':
        p.update(tau=rng.randint(-3, 3))
    elif rule == 'U1':
        p.update(value=rng.randint(-3, 3))
    if rule in ('F4', 'C6') or (rule == 'U4b' and p.get('kind') == 'sum'):
        if rng.random() < 0.3:
            c['nodes'] = ['A', 'B']
            p['mult'] = [2]
        else:
            c['nodes'] = ['A', 'B', 'C']
            p['mult'] = [1, 1]
    return c


RULES = ['F1', 'C1', 'C4', '0_1', 'F5', 'F8', 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F10', 'C5', 'C8', 'C9',
         'C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'X', 'F3', 'C3', 'U4b', 'F6', 'F4', 'C6', 'F7', 'C7', 'U5',
         'F9', 'U6', 'S1', 'S3', 'S4', 'U4a', 'U2a', 'U3', 'U1', 'U7']


@pytest.fixture(autouse=True)
def _slopes():
    solver.SLOPES['S'] = SLOPES          # other test modules clear the shared slope table
    yield


@pytest.mark.parametrize('rule', RULES)
def test_operator_sound(rule):
    rng = random.Random(sum(map(ord, rule)) + 11)
    checked = 0
    for trial in range(60):
        c = rand_constraint(rng, rule)
        keys = solver.reads(c)
        doms = {k: RAND[k[1]](rng) for k in keys}
        if rule == 'F1':
            doms = {k: Dom2.top(1) for k in keys}
        if rule == 'C1':
            doms = {k: DomC.top() for k in keys}
        if rule == 'C4':
            doms = {k: DomC(box=(None, None, None, None, False, 0)) if rng.random() < 0.3 else randc(rng) for k in keys}
        out = dict(doms)
        for node, dom, new in solver.apply(c, lambda n, d: doms[(n, d)]):
            out[(node, dom)] = new
        wins = [tuples(doms[k], k[1]) for k in keys]
        if rule in ('F1', 'C1'):
            # TOP: enumerate the whole window (including off-lattice values)
            wins = [[(M, r) for M in range(-9, 10) for r in range(-3, 14)]] if rule == 'F1' else \
                [[(t, n, r) for t in range(-2, 3) for n in range(-4, 5) for r in range(-2, 4)]]
        size = 1
        for w in wins:
            size *= max(len(w), 1)
        if size > 150000:
            wins = [rng.sample(w, min(len(w), 60)) for w in wins]
        for combo in itertools.product(*wins):
            if admissible(c, combo):
                checked += 1
                for k, t in zip(keys, combo):
                    assert member(out[k], k[1], t), (c, k, t, doms[k].to_json(), out[k].to_json())
        # monotone: nothing is added
        for k in keys:
            for t in tuples(out[k], k[1])[:300]:
                assert member(doms[k], k[1], t) or rule in ('F1', 'C1'), (c, k, t)
    assert checked > 0 or rule in ('F12', 'F13', 'F14', 'C11', 'C12', 'C13', 'C14', 'F11', '0_1')


def test_diff_bounds():
    b = solver._diff_bounds
    assert b({'rule': 'F7'}) == (0, 4)
    assert b({'rule': 'C7'}) == (0, 1)
    assert b({'rule': 'U5'}) == (0, 1)
    for a_, b_ in itertools.product(range(4), repeat=2):
        assert b({'rule': 'F9', 'par': {'a': a_, 'b': b_, 'h': 1}}) == (-4 * a_ * b_, (a_ - b_) ** 2)
        assert b({'rule': 'F9', 'par': {'a': a_, 'b': b_, 'h': -1}}) == (-(a_ - b_) ** 2, 4 * a_ * b_)
        t = a_ * (a_ - 1) // 2 + b_ * (b_ - 1) // 2
        assert b({'rule': 'U6', 'par': {'a': a_, 'b': b_, 'h': 1}}) == (-t, a_ * b_)
        assert b({'rule': 'U6', 'par': {'a': a_, 'b': b_, 'h': -1}}) == (-a_ * b_, t)


def test_exact_on_finite():
    """Joint constraints are as precise as joint enumeration when both sides are finite."""
    rng = random.Random(5)
    for rule in ('S1', 'X', 'F7', 'F4', 'C6'):
        for trial in range(40):
            c = rand_constraint(rng, rule)
            keys = solver.reads(c)

            def finite(k):
                for _ in range(50):
                    d = RAND[k[1]](rng)
                    if d.items is not None and all(r.finite() for r in d.items.values()):
                        return d
                return None
            doms = {k: finite(k) for k in keys}
            if any(d is None or d.is_empty() for d in doms.values()):
                continue          # an empty input is a contradiction; nothing to compare
            out = dict(doms)
            for node, dom, new in solver.apply(c, lambda n, d: doms[(n, d)]):
                out[(node, dom)] = new
            wins = [tuples(doms[k], k[1]) for k in keys]
            supported = [set() for _ in keys]
            for combo in itertools.product(*wins):
                if admissible(c, combo):
                    for i, t in enumerate(combo):
                        supported[i].add(t)
            for i, k in enumerate(keys):
                got = set(tuples(out[k], k[1]))
                if rule in ('F7', 'F4', 'C6'):
                    # these rules act on M resp. (tau, nu): compare projections
                    proj = (lambda t: t[0]) if k[1] == 'F' else (lambda t: t[:2])
                    assert {proj(t) for t in got} == {proj(t) for t in supported[i]}, (c, k)
                else:
                    assert got == supported[i], (c, k, doms[k].to_json(), out[k].to_json())
