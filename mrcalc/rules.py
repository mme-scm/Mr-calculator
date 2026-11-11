"""Narrowing operators, one per rule of the catalogue (section 2).

Every operator is monotone (it only removes values) and sound on unbounded parts: where a
domain is in 'box' mode or carries a ray, the operator either reasons exactly about the ray
or leaves it alone.  On finite parts the operators are exact (joint enumeration).
Operators return new domain objects; an unchanged domain is returned as the same object.
"""
from __future__ import annotations

from .domains import Dom2, DomC, DomU, RSet, _up, _dn


def _cdiv(a, b):
    return -((-a) // b)


# ----------------------------------------------------------------------
# surgery expressions
# ----------------------------------------------------------------------
def phi2(M, p, q):
    return abs(p - q * M) + (2 if (q == 1 and p == M) else 0)


def phic(nu, p, q):
    return abs(p - q * nu)


def E2(M, r, p, q):
    return q * r + phi2(M, p, q)


def EC(nu, r, p, q):
    return q * r + phic(nu, p, q)


# ----------------------------------------------------------------------
# helpers on domains
# ----------------------------------------------------------------------
def same(a, b):
    return a is b or a == b


def intersect2(a, b):
    """Intersection of two Dom2 on the same lattice."""
    if a.items is not None and b.items is not None:
        return Dom2(a.step, items={m: r.intersect(b.items[m]) for m, r in a.items.items() if m in b.items})
    if a.items is None and b.items is None:
        alo, ahi, arlo, aabs = a.box
        blo, bhi, brlo, babs = b.box
        lo = alo if blo is None else blo if alo is None else max(alo, blo)
        hi = ahi if bhi is None else bhi if ahi is None else min(ahi, bhi)
        rlo = arlo if brlo is None else brlo if arlo is None else max(arlo, brlo)
        if lo is not None and hi is not None and lo > hi:
            return Dom2(a.step, items={})
        return Dom2(a.step, box=(lo, hi, rlo, aabs or babs))
    e, bx = (a, b) if a.items is not None else (b, a)
    lo, hi, rlo, absM = bx.box
    its = {}
    for m, r in e.items.items():
        if (lo is not None and m < lo) or (hi is not None and m > hi):
            continue
        l2 = rlo
        if absM:
            l2 = abs(m) if l2 is None else max(l2, abs(m))
        its[m] = r.ge(l2)
    return Dom2(a.step, items=its)


def mirror2(a):
    if a.items is not None:
        return Dom2(a.step, items={-m: r for m, r in a.items.items()})
    lo, hi, rlo, absM = a.box
    return Dom2(a.step, box=(None if hi is None else -hi, None if lo is None else -lo, rlo, absM))


def intersectC(a, b):
    if a.items is not None and b.items is not None:
        return DomC(items={k: r.intersect(b.items[k]) for k, r in a.items.items() if k in b.items})
    if a.items is None and b.items is None:
        f = lambda x, y, pick: x if y is None else y if x is None else pick(x, y)
        a0, a1, a2, a3, ac4, ar = a.box
        b0, b1, b2, b3, bc4, br = b.box
        box = (f(a0, b0, max), f(a1, b1, min), f(a2, b2, max), f(a3, b3, min), ac4 or bc4, f(ar, br, max))
        if (box[0] is not None and box[1] is not None and box[0] > box[1]) or \
                (box[2] is not None and box[3] is not None and box[2] > box[3]):
            return DomC(items={})
        return DomC(box=box)
    e, bx = (a, b) if a.items is not None else (b, a)
    tlo, thi, nlo, nhi, c4, r0lo = bx.box
    its = {}
    for (t, n), r in e.items.items():
        if (tlo is not None and t < tlo) or (thi is not None and t > thi):
            continue
        if (nlo is not None and n < nlo) or (nhi is not None and n > nhi):
            continue
        if c4 and abs(2 * t - n) > 1:
            continue
        its[(t, n)] = r.ge(r0lo)
    return DomC(items=its)


def mirrorC(a):
    if a.items is not None:
        return DomC(items={(-t, -n): r for (t, n), r in a.items.items()})
    tlo, thi, nlo, nhi, c4, r0lo = a.box
    neg = lambda x: None if x is None else -x
    return DomC(box=(neg(thi), neg(tlo), neg(nhi), neg(nlo), c4, r0lo))


def keep(old, new):
    """Return old if nothing changed (so that the solver can detect no-ops cheaply)."""
    return old if new == old else new


# ----------------------------------------------------------------------
# initialisers and unary rules on (M, r_2)
# ----------------------------------------------------------------------
def init_f1():
    """F1: M, r_2 in 4Z, r_2 >= |M|."""
    return Dom2(4, box=(None, None, None, True))


def op_f1(d):
    """F1 applied to an arbitrary domain (TOP in practice)."""
    if d.step == 1 and d.items is None and d.box == (None, None, None, False):
        return init_f1()
    return d


def op_m_range(d, lo, hi):
    return keep(d, d.tighten_m(lo, hi))


def op_r2_value(d, how, value=None):
    """Restrict r_2: how = 'eq' (r_2 = value) or 'eqM' (r_2 = M)."""
    if d.items is None:
        return d
    if how == 'eq':
        return keep(d, d.map_r(lambda m, r: r.only([value])))
    return keep(d, d.map_r(lambda m, r: r.only([m])))


def op_f15(d, fibered, tau, g):
    """F15: (M, r_2) with r_2 = |M| != 0 admissible only if fibered, tau = sign(M) g, 2g <= |M|.
    Unknown inputs (None) never exclude."""
    if d.items is None:
        return d

    def f(m, r):
        if m == 0:
            return r
        if fibered is None or tau is None or g is None:
            if fibered is False:
                return r.remove(abs(m))
            return r
        ok = fibered and tau == (1 if m > 0 else -1) * g and 2 * g <= abs(m)
        return r if ok else r.remove(abs(m))
    return keep(d, d.map_r(f))


def op_f16(d, p, q, g):
    """F16: lens space surgery p/q > 0:  p/q > M >= 4 ceil((2g-1)/4)."""
    hi = _cdiv(p, q) - 1
    lo = None if g is None else 4 * _cdiv(2 * g - 1, 4)
    return keep(d, d.tighten_m(lo, hi))


def op_e2_values(d, p, q, values):
    """E_2(K; p/q) lies in the finite set `values` (F10: {|p|})."""
    values = sorted(set(values))
    if not values:
        return Dom2(d.step, items={})
    if d.items is None:
        mlo, mhi, rlo, absM = d.box
        rmin = rlo
        if absM:
            rmin = 0 if rmin is None else max(rmin, 0)
        if rmin is None:
            return d
        B = values[-1] - q * rmin
        if B < 0:
            return Dom2(d.step, items={})
        d = d.tighten_m(_cdiv(p - B, q), (p + B) // q)
        if d.items is None:
            return d

    def f(m, r):
        ph = phi2(m, p, q)
        return r.only([(v - ph) // q for v in values if (v - ph) % q == 0])
    return d.map_r(f)


# ----------------------------------------------------------------------
# initialisers and unary rules on (tau, nu, r_0)
# ----------------------------------------------------------------------
def init_c1c4():
    """C1 and C4: integers, r_0 >= 0, |2 tau - nu| <= 1."""
    return DomC(box=(None, None, None, None, True, 0))


def op_c_range(d, tlo=None, thi=None, nlo=None, nhi=None):
    return keep(d, d.tighten(tlo, thi, nlo, nhi))


def op_r0(d, how, value=None):
    """Restrict r_0: 'eq' value, 'ge' value, 'eq_nu' (r_0 = nu)."""
    if d.items is None:
        if how == 'ge':
            tlo, thi, nlo, nhi, c4, r0lo = d.box
            new = value if r0lo is None else max(r0lo, value)
            return d if new == r0lo else DomC(box=(tlo, thi, nlo, nhi, c4, new))
        return d
    if how == 'eq':
        return keep(d, d.map_r(lambda k, r: r.only([value])))
    if how == 'ge':
        return keep(d, d.map_r(lambda k, r: r.ge(value)))
    return keep(d, d.map_r(lambda k, r: r.only([k[1]])))


def c10_excluded_a(nu, r0):
    return r0 + abs(1 - nu) == 3


def c10_excluded_b(nu, r0):
    return r0 == 3 and abs(nu) == 3


def c15_excluded_values(nu):
    """All r_0 with r_0 + |n - nu| = n + 2 for some integer n >= 1."""
    out = {nu + 2}                       # n >= max(1, nu)
    for n in range(1, max(nu, 1)):       # 1 <= n < nu
        out.add(2 * n + 2 - nu)
    return sorted(v for v in out if v >= 0)


def op_c10(d, ge3, excl_a, excl_b):
    if d.items is None:
        return op_r0(d, 'ge', 3) if ge3 else d

    def f(k, r):
        nu = k[1]
        if ge3:
            r = r.ge(3)
        if excl_a:
            r = r.remove(3 - abs(1 - nu))
        if excl_b and abs(nu) == 3:
            r = r.remove(3)
        return r
    return keep(d, d.map_r(f))


def op_c15(d):
    if d.items is None:
        return d

    def f(k, r):
        for v in c15_excluded_values(k[1]):
            r = r.remove(v)
        return r
    return keep(d, d.map_r(f))


def op_ec_values(d, p, q, values):
    """E_C(K; p/q) lies in the finite set `values`."""
    values = sorted(set(values))
    if not values:
        return DomC(items={})
    if d.items is None:
        tlo, thi, nlo, nhi, c4, r0lo = d.box
        if r0lo is None:
            return d
        B = values[-1] - q * r0lo
        if B < 0:
            return DomC(items={})
        d = d.tighten(nlo=_cdiv(p - B, q), nhi=(p + B) // q)
        if d.items is None:
            return d

    def f(k, r):
        ph = phic(k[1], p, q)
        return r.only([(v - ph) // q for v in values if (v - ph) % q == 0])
    return d.map_r(f)


# ----------------------------------------------------------------------
# coupling X1-X5 (one node, both domains)
# ----------------------------------------------------------------------
def x_delta(M, nu, x):
    """Smallest admissible r_2 - r_0 for given (M, nu) under the X rules listed in x.
    x: dict with keys slopes (list of [p,q]) , x1 (bool), x2, x3_g (genus or None), x4,
    x5 (K certified not L), x5m (K* certified not L)."""
    d = None

    def up(v):
        nonlocal d
        if d is None or v > d:
            d = v
    if x.get('x1'):
        up(abs(M - nu))
        up(0)
        for p, q in x['slopes']:
            up(_cdiv(phic(nu, p, q) - phi2(M, p, q), q))
    if x.get('x2'):
        up(1)
    g = x.get('x3_g')
    if g is not None:
        lim = 2 * g - 1
        for p, q in x['slopes']:
            if abs(p) <= lim * q:
                up(_cdiv(phic(nu, p, q) + 2 - phi2(M, p, q), q))
    if x.get('x4'):
        up(abs(1 - nu) - abs(1 - M) + 1)
        up(abs(1 + nu) - abs(1 + M) + 1)
    if x.get('x5'):
        up(M - nu + 2)
    if x.get('x5m'):
        up(nu - M + 2)
    return d


def op_x(d2, dc, x):
    """Joint narrowing of both domains of one node by the conjunction of the X rules."""
    if d2.items is None or dc.items is None or not d2.items or not dc.items:
        return d2, dc
    nus = sorted({n for t, n in dc.items})
    delta = {(m, n): x_delta(m, n, x) for m in d2.items for n in nus}
    if all(v is None for v in delta.values()):
        return d2, dc
    cmin = {}
    for (t, n), r in dc.items.items():
        v = r.min()
        if n not in cmin:
            cmin[n] = v
        elif cmin[n] is not None:
            cmin[n] = None if v is None else min(cmin[n], v)
    new2 = {}
    for m, r in d2.items.items():
        lo = None
        unbounded = False
        for n in nus:
            dl = delta[(m, n)]
            if dl is None or cmin[n] is None:
                unbounded = True
                break
            v = cmin[n] + dl
            lo = v if lo is None else min(lo, v)
        new2[m] = r if unbounded else r.ge(lo)
    newc = {}
    for (t, n), r in dc.items.items():
        hi = None
        unbounded = False
        for m, r2 in d2.items.items():
            dl = delta[(m, n)]
            mx = r2.max()
            if dl is None or mx is None:
                unbounded = True
                break
            v = mx - dl
            hi = v if hi is None else max(hi, v)
        newc[(t, n)] = r if unbounded else r.le(hi)
    return keep(d2, Dom2(d2.step, items=new2)), keep(dc, DomC(items=newc))


# ----------------------------------------------------------------------
# difference constraints   lo <= x(B) - x(A) <= hi   (F7, F9, C7)
# ----------------------------------------------------------------------
def _diff_sets(A, B, lo, hi):
    """A, B: (list or None, lo bound, hi bound).  Returns new (lo, hi, allowed set or None) for A
    given B - A in [lo, hi]."""
    Bset, Blo, Bhi = B
    nlo = None if Blo is None else Blo - hi
    nhi = None if Bhi is None else Bhi - lo
    return nlo, nhi, Bset


def op_diff_m(dA, dB, lo, hi):
    """lo <= M(B) - M(A) <= hi."""
    def narrow(d, other, lo_, hi_):       # x(other) - x(d) in [lo_, hi_]
        olo, ohi = other.m_bounds() if other.items is not None else (other.box[0], other.box[1])
        if other.items is not None and not other.items:
            return Dom2(d.step, items={})
        nlo = None if olo is None else olo - hi_
        nhi = None if ohi is None else ohi - lo_
        d2 = d.tighten_m(nlo, nhi)
        if d2.items is not None and other.items is not None:
            oset = list(other.items)
            d2 = d2.restrict_m([m for m in d2.items if any(lo_ <= o - m <= hi_ for o in oset)])
        return keep(d, d2)
    nA = narrow(dA, dB, lo, hi)
    nB = narrow(dB, nA, -hi, -lo)
    return nA, nB


def op_self_m(d, coef, lo, hi):
    """lo <= coef * M <= hi (edge between a node and its own mirror: coef = -2)."""
    if d.items is None:
        if coef > 0:
            return keep(d, d.tighten_m(_cdiv(lo, coef), hi // coef))
        return keep(d, d.tighten_m(_cdiv(hi, coef), lo // coef))
    return keep(d, d.restrict_m([m for m in d.items if lo <= coef * m <= hi]))


def op_diff_tau(dA, dB, lo, hi):
    """lo <= tau(B) - tau(A) <= hi."""
    def narrow(d, other, lo_, hi_):
        olo, ohi = other.tau_bounds()
        if other.items is not None and not other.items:
            return DomC(items={})
        nlo = None if olo is None else olo - hi_
        nhi = None if ohi is None else ohi - lo_
        d2 = d.tighten(tlo=nlo, thi=nhi)
        if d2.items is not None and other.items is not None:
            oset = {t for t, n in other.items}
            d2 = d2.filter_keys(lambda k: any(lo_ <= o - k[0] <= hi_ for o in oset))
        return keep(d, d2)
    nA = narrow(dA, dB, lo, hi)
    nB = narrow(dB, nA, -hi, -lo)
    return nA, nB


def op_self_tau(d, coef, lo, hi):
    if d.items is None:
        if coef > 0:
            return keep(d, d.tighten(tlo=_cdiv(lo, coef), thi=hi // coef))
        return keep(d, d.tighten(tlo=_cdiv(hi, coef), thi=lo // coef))
    return keep(d, d.filter_keys(lambda k: lo <= coef * k[0] <= hi))


def op_diff_u(dA, dB, lo, hi):
    """lo <= upsilon(B) - upsilon(A) <= hi."""
    nA = dA.tighten(None if dB.lo is None else dB.lo - hi, None if dB.hi is None else dB.hi - lo)
    nB = dB.tighten(None if nA.lo is None else nA.lo + lo, None if nA.hi is None else nA.hi + hi)
    return keep(dA, nA), keep(dB, nB)


def op_self_u(d, coef, lo, hi):
    if coef > 0:
        return keep(d, d.tighten(_cdiv(lo, coef), hi // coef))
    return keep(d, d.tighten(_cdiv(hi, coef), lo // coef))


# ----------------------------------------------------------------------
# mirror (F3, C3, U4b) and mutation (F6)
# ----------------------------------------------------------------------
def op_mirror2(dA, dB):
    nA = keep(dA, intersect2(dA, mirror2(dB)))
    nB = keep(dB, intersect2(dB, mirror2(nA)))
    return nA, nB


def op_mirrorC(dA, dB):
    nA = keep(dA, intersectC(dA, mirrorC(dB)))
    nB = keep(dB, intersectC(dB, mirrorC(nA)))
    return nA, nB


def op_mirrorU(dA, dB):
    neg = lambda x: None if x is None else -x
    nA = keep(dA, dA.tighten(neg(dB.hi), neg(dB.lo)))
    nB = keep(dB, dB.tighten(neg(nA.hi), neg(nA.lo)))
    return nA, nB


def op_equal2(dA, dB):
    n = intersect2(dA, dB)
    return keep(dA, n), keep(dB, n)


# ----------------------------------------------------------------------
# connected sum (F4, C6, U4b):  N = sum of parts with multiplicities
# ----------------------------------------------------------------------
def _combos(doms, mults, keyf):
    """All tuples of keys (one per distinct part)."""
    import itertools
    return itertools.product(*[keyf(d) for d in doms])


def op_sum_m(dN, parts):
    """M(N) = sum mult_i * M(K_i); parts = [(Dom2, mult), ...]."""
    doms = [d for d, m in parts]
    mults = [m for d, m in parts]
    if any(d.items is not None and not d.items for d in doms + [dN]):
        return Dom2(dN.step, items={}), doms
    if all(d.items is not None for d in doms):
        import itertools
        sums = {}
        for combo in itertools.product(*[list(d.items) for d in doms]):
            sums.setdefault(sum(c * m for c, m in zip(combo, mults)), []).append(combo)
        nN = dN.restrict_m(list(sums))
        if nN.items is None:
            return keep(dN, nN), doms
        used = [set() for _ in doms]
        for s in nN.items:
            for combo in sums.get(s, ()):
                for i, c in enumerate(combo):
                    used[i].add(c)
        nd = [keep(d, d.restrict_m(used[i])) for i, d in enumerate(doms)]
        return keep(dN, nN), nd
    # interval reasoning
    lo = hi = 0
    for d, m in parts:
        a, b = d.m_bounds() if d.items is not None else (d.box[0], d.box[1])
        if a is None or lo is None:
            lo = None
        else:
            lo += m * a
        if b is None or hi is None:
            hi = None
        else:
            hi += m * b
    nN = keep(dN, dN.tighten_m(lo, hi))
    nd = list(doms)
    if len(parts) == 1:
        a, b = nN.m_bounds() if nN.items is not None else (nN.box[0], nN.box[1])
        m = mults[0]
        nd[0] = keep(doms[0], doms[0].tighten_m(None if a is None else _cdiv(a, m), None if b is None else b // m))
    else:
        a, b = nN.m_bounds() if nN.items is not None else (nN.box[0], nN.box[1])
        for i in range(2):
            o = doms[1 - i]
            oa, ob = o.m_bounds() if o.items is not None else (o.box[0], o.box[1])
            l2 = None if (a is None or ob is None) else a - ob
            h2 = None if (b is None or oa is None) else b - oa
            nd[i] = keep(doms[i], doms[i].tighten_m(l2, h2))
    return nN, nd


def op_sum_c(dN, parts):
    """C6: tau(N) = sum tau_i, |nu(N) - sum nu_i| <= 1 (parts with multiplicities, total 2)."""
    doms = [d for d, m in parts]
    mults = [m for d, m in parts]
    if any(d.items is not None and not d.items for d in doms + [dN]):
        return DomC(items={}), doms
    if all(d.items is not None for d in doms):
        import itertools
        combos = list(itertools.product(*[list(d.items) for d in doms]))
        if dN.items is None:
            ts = [sum(c[0] * m for c, m in zip(co, mults)) for co in combos]
            ns = [sum(c[1] * m for c, m in zip(co, mults)) for co in combos]
            nN = dN.tighten(min(ts), max(ts), min(ns) - 1, max(ns) + 1)
            if nN.items is None:
                return keep(dN, nN), doms
        else:
            nN = dN
        used = [set() for _ in doms]
        keepN = set()
        for co in combos:
            t = sum(c[0] * m for c, m in zip(co, mults))
            n = sum(c[1] * m for c, m in zip(co, mults))
            hit = False
            for dn in (-1, 0, 1):
                if (t, n + dn) in nN.items:
                    keepN.add((t, n + dn))
                    hit = True
            if hit:
                for i, c in enumerate(co):
                    used[i].add(c)
        nN2 = nN.filter_keys(lambda k: k in keepN)
        nd = [keep(d, d.filter_keys(lambda k, u=used[i]: k in u)) for i, d in enumerate(doms)]
        return keep(dN, nN2), nd
    # interval reasoning on tau and nu
    tlo = thi = nlo = nhi = 0
    for d, m in parts:
        a, b = d.tau_bounds()
        c, e = d.nu_bounds()
        tlo = None if (a is None or tlo is None) else tlo + m * a
        thi = None if (b is None or thi is None) else thi + m * b
        nlo = None if (c is None or nlo is None) else nlo + m * c
        nhi = None if (e is None or nhi is None) else nhi + m * e
    nN = keep(dN, dN.tighten(tlo, thi, None if nlo is None else nlo - 1, None if nhi is None else nhi + 1))
    nd = list(doms)
    a, b = nN.tau_bounds()
    if len(parts) == 1:
        m = mults[0]
        nd[0] = keep(doms[0], doms[0].tighten(None if a is None else _cdiv(a, m), None if b is None else b // m))
    else:
        for i in range(2):
            oa, ob = doms[1 - i].tau_bounds()
            l2 = None if (a is None or ob is None) else a - ob
            h2 = None if (b is None or oa is None) else b - oa
            nd[i] = keep(doms[i], doms[i].tighten(l2, h2))
    return nN, nd


def op_sum_u(dN, parts):
    lo = hi = 0
    for d, m in parts:
        lo = None if (d.lo is None or lo is None) else lo + m * d.lo
        hi = None if (d.hi is None or hi is None) else hi + m * d.hi
    nN = keep(dN, dN.tighten(lo, hi))
    doms = [d for d, m in parts]
    nd = list(doms)
    if len(parts) == 1:
        m = parts[0][1]
        nd[0] = keep(doms[0], doms[0].tighten(None if nN.lo is None else _cdiv(nN.lo, m),
                                              None if nN.hi is None else nN.hi // m))
    else:
        for i in range(2):
            o = doms[1 - i]
            l2 = None if (nN.lo is None or o.hi is None) else nN.lo - o.hi
            h2 = None if (nN.hi is None or o.lo is None) else nN.hi - o.lo
            nd[i] = keep(doms[i], doms[i].tighten(l2, h2))
    return nN, nd


# ----------------------------------------------------------------------
# surgery equations  a * E(K; p/q) = b * E(K'; p'/q')   (S1, S3, S4)
# ----------------------------------------------------------------------
def _e_items(d, p, q, which):
    """List of (key, phi, RSet) for an enum domain."""
    if which == 'F':
        return [(m, phi2(m, p, q), r) for m, r in d.items.items()]
    return [(k, phic(k[1], p, q), r) for k, r in d.items.items()]


def _support(itemsB, qB, b):
    """Values of b*E on side B: (explicit set, list of (start, step) upward progressions,
    has_down_ray)."""
    vals = set()
    rays = []
    down = False
    for key, ph, r in itemsB:
        for v in r.vals:
            vals.add(b * (qB * v + ph))
        if r.up is not None:
            rays.append((b * (qB * r.up + ph), b * qB * r.step))
        if r.down is not None:
            down = True
    return vals, rays, down


def _narrow_eq(itemsA, qA, a, supp):
    vals, rays, down = supp
    out = {}
    if down:
        return {key: r for key, ph, r in itemsA}
    ray_min = min((s for s, st in rays), default=None)
    for key, ph, r in itemsA:
        def supported(v):
            e = a * (qA * v + ph)
            if e in vals:
                return True
            return any(e >= s and (e - s) % st == 0 for s, st in rays)
        newvals = [v for v in r.vals if supported(v)]
        up = r.up
        if up is not None:
            # explicit supports inside the ray
            cand = set()
            for e in vals:
                if e % a == 0 and (e // a - ph) % qA == 0:
                    v = (e // a - ph) // qA
                    if v in r and v >= up:
                        cand.add(v)
            if ray_min is None:
                newvals += sorted(cand)
                up = None
            else:
                # e = a (qA v + ph) >= ray_min  =>  v >= ceil((ray_min/a - ph)/qA)
                lo = _cdiv(_cdiv(ray_min, a) - ph, qA)
                new_up = max(up, _up(lo, r.step))
                newvals += [v for v in cand if v < new_up]
                up = new_up
        out[key] = RSet(newvals, up, r.down, r.step)
    return out


def _finite_max(items, q, b):
    """Max of b*E over the items if finite, else None."""
    mx = None
    for key, ph, r in items:
        if r.max() is None:
            return None
        if r.is_empty():
            continue
        v = b * (q * r.max() + ph)
        mx = v if mx is None else max(mx, v)
    return mx


def op_eq(dA, sA, a, dB, sB, b, which):
    """a * E(A; sA) = b * E(B; sB) on the domains of kind `which` ('F' or 'C')."""
    (pA, qA), (pB, qB) = sA, sB
    cls = Dom2 if which == 'F' else DomC
    # box sides: try to make them finite from the other side
    for _ in range(2):
        if dA.items is None and dB.items is not None:
            mx = _finite_max(_e_items(dB, pB, qB, which), qB, b)
            if mx is not None:
                dA = _box_bound(dA, pA, qA, mx // a, which)
        if dB.items is None and dA.items is not None:
            mx = _finite_max(_e_items(dA, pA, qA, which), qA, a)
            if mx is not None:
                dB = _box_bound(dB, pB, qB, mx // b, which)
    if dA.items is None or dB.items is None:
        return dA, dB
    iA = _e_items(dA, pA, qA, which)
    iB = _e_items(dB, pB, qB, which)
    nA = _narrow_eq(iA, qA, a, _support(iB, qB, b))
    iA2 = [(k, ph, nA[k]) for k, ph, r in iA]
    nB = _narrow_eq(iB, qB, b, _support(iA2, qA, a))
    if which == 'F':
        return keep(dA, Dom2(dA.step, items=nA)), keep(dB, Dom2(dB.step, items=nB))
    return keep(dA, DomC(items=nA)), keep(dB, DomC(items=nB))


def _box_bound(d, p, q, vmax, which):
    """Make a box domain finite using E(K; p/q) <= vmax (needs a lower bound on r)."""
    if which == 'F':
        mlo, mhi, rlo, absM = d.box
        rmin = rlo
        if absM:
            rmin = 0 if rmin is None else max(rmin, 0)
        if rmin is None:
            return d
        B = vmax - q * rmin
        if B < 0:
            return Dom2(d.step, items={})
        return d.tighten_m(_cdiv(p - B, q), (p + B) // q)
    tlo, thi, nlo, nhi, c4, r0lo = d.box
    if r0lo is None:
        return d
    B = vmax - q * r0lo
    if B < 0:
        return DomC(items={})
    return d.tighten(nlo=_cdiv(p - B, q), nhi=(p + B) // q)


def op_eq_self(d, s1, a, s2, b, which):
    """a * E(K; s1) = b * E(K; s2) on a single node (both fillings of the same knot)."""
    (p1, q1), (p2, q2) = s1, s2
    if d.items is None:
        return d

    def f(key, r):
        x = key if which == 'F' else key[1]
        ph1 = phi2(x, p1, q1) if which == 'F' else phic(x, p1, q1)
        ph2 = phi2(x, p2, q2) if which == 'F' else phic(x, p2, q2)
        # a (q1 r + ph1) = b (q2 r + ph2)
        c = a * q1 - b * q2
        rhs = b * ph2 - a * ph1
        if c == 0:
            return r if rhs == 0 else RSet((), None, None, r.step)
        if rhs % c:
            return RSet((), None, None, r.step)
        return r.only([rhs // c])
    return keep(d, d.map_r(f))


# ----------------------------------------------------------------------
# upsilon
# ----------------------------------------------------------------------
def op_u_range(d, lo, hi):
    return keep(d, d.tighten(lo, hi))


# ----------------------------------------------------------------------
# F11 upsilon of torus knots
# ----------------------------------------------------------------------
def torus_alexander_exponents(p, q):
    """Exponents n_0 > n_1 > ... > n_2k of the symmetrised Alexander polynomial of T(p,q)."""
    # (t^{pq}-1)(t-1) / ((t^p-1)(t^q-1)) by exact polynomial division
    def mul(a, b):
        out = [0] * (len(a) + len(b) - 1)
        for i, x in enumerate(a):
            if x:
                for j, y in enumerate(b):
                    out[i + j] += x * y
        return out

    def poly(n):          # t^n - 1
        c = [0] * (n + 1)
        c[0] = -1
        c[n] = 1
        return c
    num = mul(poly(p * q), poly(1))
    den = mul(poly(p), poly(q))
    quo = [0] * (len(num) - len(den) + 1)
    rem = num[:]
    for i in range(len(quo) - 1, -1, -1):
        c = rem[i + len(den) - 1] // den[-1]
        quo[i] = c
        if c:
            for j, y in enumerate(den):
                rem[i + j] -= c * y
    if any(rem):
        raise ArithmeticError('torus Alexander polynomial division failed')
    deg = len(quo) - 1
    if deg != (p - 1) * (q - 1):
        raise ArithmeticError('degree mismatch')
    exps = []
    last = None
    for i in range(deg, -1, -1):
        c = quo[i]
        if c == 0:
            continue
        if abs(c) != 1 or (last is not None and c == last):
            raise ArithmeticError('coefficients are not alternating +-1')
        last = c
        exps.append(i - deg // 2 if deg % 2 == 0 else None)
    if deg % 2:
        raise ArithmeticError('odd degree')
    return exps


def torus_upsilon(p, q):
    """upsilon(T(p,q)) as in F11."""
    n = torus_alexander_exponents(p, q)
    m = [0]
    for i in range(len(n) - 1):
        if i % 2 == 0:
            m.append(m[i] - 2 * (n[i] - n[i + 1]) + 1)
        else:
            m.append(m[i] - 1)
    return max(m[i] - n[i] for i in range(0, len(n), 2))
