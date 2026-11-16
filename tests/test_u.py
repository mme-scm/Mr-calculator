"""Rules N1-N5 (RULES_U.md): bounds, band smoothing, bound propagation."""
from fractions import Fraction

import pytest

from mrcalc import knotinfo, pd as P, usolve


def test_n3_bounds_small_cases():
    # right-handed full twist, l = a - b, m = min(a, b):  -floor(l^2/4) <= d <= m - floor((|l|-1)^2/4)
    assert usolve.n3_bounds(1, 1, 1) == (0, 1)        # crossing change K+ -> K-
    assert usolve.n3_bounds(2, 0, 1) == (-1, 0)
    assert usolve.n3_bounds(0, 2, 1) == (-1, 0)
    assert usolve.n3_bounds(2, 1, 1) == (0, 1)
    assert usolve.n3_bounds(3, 0, 1) == (-2, -1)
    assert usolve.n3_bounds(2, 2, 1) == (0, 2)
    assert usolve.n3_bounds(3, 1, 1) == (-1, 1)
    assert usolve.n3_bounds(4, 0, 1) == (-4, -2)
    assert usolve.n3_bounds(5, 0, 1) == (-6, -4)
    for a in range(6):
        for b in range(6):
            lo, hi = usolve.n3_bounds(a, b, 1)
            assert usolve.n3_bounds(a, b, -1) == (-hi, -lo)
            assert usolve.n3_bounds(b, a, 1) == (lo, hi)
            assert lo <= hi


def test_n3_agrees_with_torus_values():
    """A right-handed full twist on p parallel strands takes T(p,q) to T(p,q+p); rule N1t gives both values."""
    from mrcalc.rules import torus_upsilon
    for p, q in ((2, 1), (2, 3), (2, 5), (3, 1), (3, 2), (3, 4), (4, 1), (4, 3), (5, 1), (5, 2)):
        u0 = 0 if q == 1 else torus_upsilon(min(p, q), max(p, q))
        u1 = torus_upsilon(p, q + p)
        lo, hi = usolve.n3_bounds(p, 0, 1)
        assert lo <= u1 - u0 <= hi, (p, q)


def test_n4_bounds():
    assert usolve.n4_bounds(6) == (1, 2)
    assert usolve.n4_bounds(-6) == (-2, -1)
    assert usolve.n4_bounds(0) == (Fraction(-1, 2), Fraction(1, 2))


def test_band_smoothing_trefoil_and_mirror():
    T = knotinfo.by_name()
    pd = T['3_1']['pd']
    w = P.writhe(pd)
    for i in range(3):
        new, s, w0, w1 = P.band_smoothing(pd, i)
        assert len(new) == 2 and w0 == w and s == (1 if w > 0 else -1)
        e = s - (w1 - w0)
        assert abs(e) == 6 and e * w > 0
        # the unknot has u = 0, the trefoil of this chirality u = sigma/2 (N1a)
        lo, hi = usolve.n4_bounds(e)
        assert lo <= 0 - Fraction(T['3_1']['signature'], 2) <= hi
    for nm in ('4_1', '5_2', '8_19', '10_124', '12n_242'):
        pd = T[nm]['pd']
        m = P.mirror(pd)
        for i in range(len(pd)):
            new, s, w0, w1 = P.band_smoothing(pd, i)
            newm, sm, w0m, w1m = P.band_smoothing(m, i)
            assert (sm, w0m, w1m) == (-s, -w0, -w1)
            assert (s - (w1 - w0)) % 2 == 0
            assert len(new) == len(pd) - 1
            P.Diagram.from_pd(new)


def test_band_smoothing_one_crossing():
    new, s, w0, w1 = P.band_smoothing([[1, 2, 2, 1]], 0)
    assert new == [] and w1 == 0 and w0 == s


class Toy:
    """Minimal stand-in for UProblem: nodes 0..n-1."""
    def __init__(self, n, mirror=None):
        self.names = ['n%d' % i for i in range(n)]
        self.mirror = list(mirror) if mirror else list(range(n))
        self.unary, self.sums, self.diff, self.selfc, self.violations = [], [], {}, {}, []


def _solve(U, integer):
    return usolve.USolver(U, integer).run()


def test_propagation_and_integer_rounding():
    # nodes: 0 anchor (=0), 1 its neighbour by N4 with e = 0, 2 = mirror of 3
    U = Toy(4, mirror=[0, 1, 3, 2])
    U.mirror[0] = 9      # not amphichiral in this toy
    U.mirror[1] = 9
    U.names += ['x'] * 6
    U.mirror += [0, 1, 0, 0, 0, 0][:6]
    U.mirror[9] = 9
    U.unary = [(0, 0, 'N2z', {})]
    U.diff[(0, 1)] = [Fraction(-1, 2), Fraction(1, 2), ('b', 0, 0), ('b', 0, 0)]
    U.diff[(1, 2)] = [0, 1, ('e', 0), ('e', 0)]
    Z, Rr = _solve(U, True), _solve(U, False)
    assert (Z.lo[1], Z.hi[1]) == (0, 0)                          # the only integer in [-1/2, 1/2]
    assert (Rr.lo[1], Rr.hi[1]) == (Fraction(-1, 2), Fraction(1, 2))
    assert (Z.lo[2], Z.hi[2]) == (0, 1)
    assert (Rr.lo[2], Rr.hi[2]) == (Fraction(-1, 2), Fraction(3, 2))
    assert (Z.lo[3], Z.hi[3]) == (-1, 0)                         # mirror
    assert (Rr.lo[3], Rr.hi[3]) == (Fraction(-3, 2), Fraction(1, 2))
    # every event of a chain is earlier than the event it supports
    for S in (Z, Rr):
        for k, ev in enumerate(S.events):
            assert all(i < k for i in ev[5])
        ids = S.closure([S.lo_ev[3], S.hi_ev[3]])
        assert ids and ids[-1] in (S.lo_ev[3], S.hi_ev[3])


def test_sum_and_contradiction():
    U = Toy(3)
    U.mirror = [0, 1, 2]
    for i in range(3):
        U.mirror[i] = 3 + i
    U.names += ['m0', 'm1', 'm2']
    U.mirror += [0, 1, 2]
    U.unary = [(0, 2, 'N1a', {}), (2, 5, 'N1a', {})]
    U.sums = [(2, [(0, 1), (1, 1)])]
    S = _solve(U, False)
    assert (S.lo[1], S.hi[1]) == (3, 3)
    assert (S.lo[4], S.hi[4]) == (-3, -3)
    U.diff[(0, 1)] = [-1, 0, ('e', 0), ('e', 0)]             # x1 - x0 <= 0 contradicts x1 = 3, x0 = 2
    with pytest.raises(usolve.Contradiction):
        _solve(U, False)


def test_torus_and_alternating_anchors_agree():
    """N1t and N1a on the alternating torus knots T(2,n) of the table (convention test for rule N1)."""
    from mrcalc.rules import torus_upsilon
    T = knotinfo.by_name()
    for nm, n in (('3_1', 3), ('5_1', 5), ('7_1', 7), ('9_1', 9)):
        s = T[nm]['signature']
        assert abs(s) == n - 1
        assert torus_upsilon(2, n) == -(n - 1) // 2


def test_alternating_anchors_outside_the_table():
    """Rule N1a for knots outside the table (scripts/alt_anchors.py rows): the knot of the row gets sigma/2,
    its mirror image -sigma/2, a table knot is left to the table; the checker's own signature (spherogram)
    and alternation test agree with the pipeline's on an alternating and a non-alternating diagram."""
    import collections
    import importlib.util
    import os
    from mrcalc import alg

    class Stub:
        canon = staticmethod(lambda n: n)

    U = usolve.UProblem.__new__(usolve.UProblem)
    U.P, U.unary, U.stats = Stub(), [], collections.defaultdict(int)
    U.ix = {'K14a1': 0, 'K14a1*': 1, 'K15a7*': 2, '3_1': 3}
    T = knotinfo.by_name()
    pd = T['7_2']['pd']
    rows = [{'node': 'K14a1', 'signature': -4, 'by': 'census name', 'pd': pd, 'ref': {'dst': 'K14a1'}},
            {'node': 'K15a7', 'signature': 2, 'by': 'alternating diagram', 'pd': pd, 'ref': {'dst': 'K15a7'}},
            {'node': '3_1', 'signature': -2, 'by': 'census name', 'pd': pd, 'ref': {'dst': '3_1'}}]
    U._alt_anchors(rows)
    got = {u[0]: (u[1], u[2], u[3]['mirror'], u[3]['signature']) for u in U.unary}
    assert got == {0: (-2, 'N1a', False, -4), 1: (2, 'N1a', True, 4), 2: (-1, 'N1a', True, -2)}
    with pytest.raises(ValueError):
        U._alt_anchors([{'node': 'K14a2', 'signature': 3, 'by': 'census name', 'pd': pd, 'ref': {}}])

    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location('check_u', os.path.join(here, '..', 'checker', 'check_u.py'))
    cu = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cu)
    C = cu.Check('.', os.path.join(here, '..', 'data'))
    for nm in ('7_2', '8_19', '10_124', '12n_242', '9_42'):
        d = T[nm]['pd']
        assert C.alternating_pd(d) == bool(P.Diagram.from_pd(d).is_alternating_diagram())
        s = C.signature(d)
        assert s is None or s == alg.signature(d) == T[nm]['signature']
    assert C.alternating_pd(T['7_2']['pd']) and not C.alternating_pd(T['8_19']['pd'])
    # a full anchor record through the checker: good, wrong signature, non-alternating diagram
    s = T['7_2']['signature']
    con = {'id': 'x', 'type': 'unary', 'rule': 'N1a', 'node': 'K14a1', 'value': str(Fraction(s, 2)),
           'par': {'signature': s, 'by': 'alternating diagram', 'mirror': False, 'pd': T['7_2']['pd'],
                   'ref': {'dst': 'K14a1'}}}
    C.check_constraint(con)
    assert not C.err
    C.check_constraint(dict(con, par=dict(con['par'], pd=T['8_19']['pd'])))
    assert C.err
