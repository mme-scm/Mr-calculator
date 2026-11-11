"""Convention tests of section 3.  run_all() returns [(name, ok, detail)]; the pass drivers call
assert_all() before every pass."""
from __future__ import annotations

import random

from . import alg, hfk as H, knotinfo, pd as P, surgery as S

_cache = {}


def _idr():
    from . import identify as I
    if 'idr' not in _cache:
        _cache['idr'] = I.Identifier(use_census=False)
    return _cache['idr']


def t_chirality_reference():
    t = knotinfo.by_name()
    ok = t['3_1']['signature'] == -2 and t['3_1']['tau'] == 1 and t['5_1']['tau'] == 2 and t['5_2']['tau'] == 1
    calc = [H.hfk(t[n]['pd'])['tau'] for n in ('3_1', '5_1', '5_2')]
    return ok and calc == [1, 2, 1], 'KnotInfo tau %s, calculator %s' % (
        [t[n]['tau'] for n in ('3_1', '5_1', '5_2')], calc)


def t_trefoil_unit():
    """M(3_1)=4, r_2=4, nu=r_0=1, tau^#=1 must come out of F12, C11, C8."""
    from . import solver
    cons = [
        {'id': 'c0', 'rule': 'F1', 'dom': 'F', 'nodes': ['3_1']},
        {'id': 'c1', 'rule': 'F12', 'dom': 'F', 'nodes': ['3_1'], 'par': {'n': 1}},
        {'id': 'c2', 'rule': 'C1', 'dom': 'C', 'nodes': ['3_1']},
        {'id': 'c3', 'rule': 'C4', 'dom': 'C', 'nodes': ['3_1']},
        {'id': 'c4', 'rule': 'C8', 'dom': 'C', 'nodes': ['3_1'], 'par': {'tau': knotinfo.by_name()['3_1']['tau']}},
        {'id': 'c5', 'rule': 'C11', 'dom': 'C', 'nodes': ['3_1'], 'par': {'g': knotinfo.by_name()['3_1']['genus']}},
    ]
    s = solver.Solver()
    s.add(cons)
    s.run()
    pins = s.pins('3_1')
    want = {'M': 4, 'r_2': 4, 'nu': 1, 'r_0': 1, 'tau': 1}
    return pins == want, str(pins)


def t_crossing_sign():
    t = knotinfo.by_name()['3_1']['pd']
    D = P.Diagram.from_pd(t)
    b = P.braid_closure([1, 1, 1])
    Db = P.Diagram.from_pd(b)
    ok = D.sign == [1, 1, 1] and Db.sign == [1, 1, 1] and H.hfk(b)['tau'] == 1 and alg.signature(b) == -2
    bn = P.braid_closure([-1, -1, -1])
    ok = ok and P.Diagram.from_pd(bn).sign == [-1, -1, -1] and H.hfk(bn)['tau'] == -1
    return ok, 'signs %s %s' % (D.sign, Db.sign)


def t_twist_signs_and_writhe():
    """Right-handed full twist: new crossings between coherently oriented strands positive,
    between oppositely oriented strands negative; writhe identity (a-b)^2 = k + s (w' - w)."""
    rng = random.Random(7)
    T = knotinfo.table()
    n = 0
    for r in rng.sample(T[:800], 12):
        D = P.Diagram.from_pd(r['pd'])
        for k in (2, 3, 4):
            paths = P.dual_paths(D, k, None)
            for edges, faces, dirs in rng.sample(paths, min(4, len(paths))):
                for h in (1, -1):
                    new, a, b, d2 = P.twist(r['pd'], edges, h)
                    w0, w1 = D.writhe(), P.writhe(new)
                    if (a - b) ** 2 != k + h * (w1 - w0):
                        return False, 'writhe identity fails on %s %s' % (r['name'], edges)
                    Dn = P.Diagram.from_pd(new)
                    # new crossings are the last k(k-1) ones
                    pos = sum(1 for s in Dn.sign[D.n:] if s == 1)
                    neg = sum(1 for s in Dn.sign[D.n:] if s == -1)
                    coh = a * (a - 1) + b * (b - 1)
                    opp = 2 * a * b
                    want = (coh, opp) if h == 1 else (opp, coh)
                    if (pos, neg) != want or Dn.sign[:D.n] != D.sign:
                        return False, 'twist crossing signs wrong on %s %s' % (r['name'], edges)
                    n += 1
    return True, '%d twists' % n


def t_trefoil_twist_unknot():
    """Right-handed trefoil, right-handed full twist on the two oppositely oriented strands at
    one crossing: the unknot."""
    t = knotinfo.by_name()['3_1']['pd']
    D = P.Diagram.from_pd(t)
    found = 0
    for edges, faces, dirs in P.dual_paths(D, 2, None):
        if sum(dirs) != 0:
            continue
        # both edges at one crossing: they share a crossing end
        ends = [set((D.head[e][0], D.tail[e][0])) for e in edges]
        if not (ends[0] & ends[1]):
            continue
        new, a, b, _ = P.twist(t, edges, 1)
        r = _idr().identify(new)
        if r['name'] != '0_1':
            return False, 'twist along %s gives %s' % (edges, r['name'])
        found += 1
    return found > 0, '%d crossing circles' % found


def t_writhe_crossing_change():
    rng = random.Random(3)
    for r in rng.sample(knotinfo.table()[:3000], 40):
        D = P.Diagram.from_pd(r['pd'])
        i = rng.randrange(D.n)
        if P.writhe(P.crossing_change(r['pd'], i)) - D.writhe() != -2 * D.sign[i]:
            return False, r['name']
    return True, ''


def t_mirror_sigma_tau():
    t = knotinfo.by_name()
    for n in ('3_1', '5_2', '8_19', '9_42', '10_132'):
        pd = t[n]['pd']
        m = P.mirror(pd)
        if alg.signature(m) != -alg.signature(pd) or H.hfk(m)['tau'] != -H.hfk(pd)['tau']:
            return False, n
        if alg.signature(pd) != t[n]['signature'] or H.hfk(pd)['tau'] != t[n]['tau']:
            return False, n + ' (table)'
    return True, ''


def t_f11_upsilon():
    from .rules import torus_upsilon
    v = [torus_upsilon(2, 3), torus_upsilon(3, 4), torus_upsilon(3, 5)]
    return v == [-1, -2, -3], str(v)


def t_braid_chirality():
    t = knotinfo.by_name()
    for n in ('3_1', '4_1', '5_1', '5_2', '8_19'):
        r1 = _idr().identify(t[n]['pd'])['name']
        r2 = _idr().identify(P.braid_closure(t[n]['braids'][0]))['name']
        if r1 != n or r2 != n:
            return False, '%s: pd -> %s, braid -> %s' % (n, r1, r2)
    return True, ''


def t_cable():
    t = knotinfo.by_name()
    # C_{r,s}(0_1) = T(r,s): cable a one-crossing diagram of the unknot (both kink signs)
    for kink in ([[1, 1, 2, 2]], [[1, 2, 2, 1]]):
        for (r, s), want in (((3, 2), '3_1'), ((5, 2), '5_1'), ((4, 3), '8_19'), ((-3, 2), '3_1*')):
            c = P.cable(kink, r, s)
            got = _idr().identify(c)['name']
            if got != want:
                return False, 'C_{%d,%d}(unknot %s) -> %s' % (r, s, kink, got)
    g = H.hfk(P.cable(t['3_1']['pd'], 5, 2))['genus']
    return g == 4, 'genus of C_{5,2}(3_1) = %s' % g


def t_pretzel():
    r = _idr().identify(P.pretzel([1, 1, 1]))['name']
    return r == '3_1', 'P(1,1,1) -> %s' % r


def t_twist_knots():
    from .nodeset import twist_knot
    a = _idr().identify(twist_knot(1))['name']
    b = _idr().identify(twist_knot(2))['name']
    return a in ('3_1', '3_1*') and b == '4_1', 'm=1 -> %s, m=2 -> %s' % (a, b)


def t_surgery_mirror():
    t = knotinfo.by_name()
    pd = t['5_2']['pd']
    E, Em = S.exterior(pd), S.exterior(P.mirror(pd))
    n = 0
    for s in [(7, 2), (-9, 1), (11, 3), (-13, 4)]:
        a = S.hyperbolic_signature(E, s)
        b = S.hyperbolic_signature(Em, s)
        c = S.hyperbolic_signature(E, (-s[0], s[1]))
        if not (a and b and c):
            continue
        n += 1
        if b['sig'] != c['sig'] or b['sig'] == a['sig']:
            return False, 'slope %s' % (s,)
    return n >= 3, '%d slopes with verified hyperbolic fillings' % n


def t_moser():
    t = knotinfo.by_name()
    E = S.exterior(t['3_1']['pd'])
    out = []
    for p in (5, 7):
        r = S.regina_recognise(S.filled_string(E, (p, 1)))
        kind, nm = S.moser(2, 3, p, 1)
        out.append((p, r['name'], nm))
        if r['kind'] != 'lens' or kind != 'lens' or r['name'] != nm or not nm.startswith('L(%d,' % p):
            return False, str(out)
    r = S.regina_recognise(S.filled_string(E, (-1, 1)))
    kind, orders = S.moser(2, 3, -1, 1)
    ok = r['kind'] == 'sfs' and kind == 'sfs' and S.sfs_orders(r['name']) == orders == (2, 3, 7)
    return ok, '%s; -1: %s vs %s' % (out, r.get('name'), orders)


def t_cable_surgery_identity():
    """Sanity of the cable convention: S^3_{rs+-1}(C_{r,s}(K)) and S^3_{(rs+-1)/s^2}(K) have equal
    volume and homology, and equal isometry signatures whenever SnapPy finds a geometric
    triangulation of the cable filling (K = 4_1, 5_2)."""
    import snappy
    t = knotinfo.by_name()
    nsig = nvol = 0
    for name, r, s in (('4_1', 1, 2), ('4_1', -3, 2), ('5_2', 3, 2), ('4_1', 2, 3)):
        pd = t[name]['pd']
        C = S.exterior(P.cable(pd, r, s))
        K = S.exterior(pd)
        for sg in (1, -1):
            p = r * s + sg
            N = C.copy()
            N.dehn_fill((p, 1))
            M = snappy.Manifold(N.filled_triangulation())
            for _ in range(10):
                if M.solution_type() == S.GEOMETRIC:
                    break
                M.randomize()
            Kf = K.copy()
            Kf.dehn_fill((p, s * s))
            if str(M.homology()) != str(Kf.homology()):
                return False, '%s r=%d s=%d sign %d: homology differs' % (name, r, s, sg)
            if M.solution_type() == S.GEOMETRIC and Kf.solution_type() == S.GEOMETRIC:
                if abs(float(M.volume()) - float(Kf.volume())) > 1e-6:
                    return False, '%s r=%d s=%d sign %d: volume differs' % (name, r, s, sg)
            nvol += 1
            b = S.hyperbolic_signature(K, (p, s * s))
            if M.solution_type() == S.GEOMETRIC and b:
                try:
                    a = M.isometry_signature(verified=True)
                except Exception:
                    continue
                nsig += 1
                if a != b['sig']:
                    return False, '%s r=%d s=%d sign %d: signatures differ' % (name, r, s, sg)
    return nvol == 8 and nsig >= 1, '%d homology agreements, %d signature agreements' % (nvol, nsig)


TESTS = [
    ('chirality reference (KnotInfo 3_1, 5_1, 5_2)', t_chirality_reference),
    ('trefoil unit test (F12, C11, C8)', t_trefoil_unit),
    ('crossing sign / positive braid generator', t_crossing_sign),
    ('full twist signs and writhe identity', t_twist_signs_and_writhe),
    ('trefoil + right-handed twist on crossing circle = unknot', t_trefoil_twist_unknot),
    ('crossing change changes writhe by -2 sign', t_writhe_crossing_change),
    ('mirror negates sigma and tau', t_mirror_sigma_tau),
    ('F11 upsilon values', t_f11_upsilon),
    ('braid word and PD same chirality (3_1,4_1,5_1,5_2,8_19)', t_braid_chirality),
    ('cable convention', t_cable),
    ('pretzel convention', t_pretzel),
    ('twist knots', t_twist_knots),
    ('surgery on mirror', t_surgery_mirror),
    ('Moser test', t_moser),
    ('cable surgery identity (sanity)', t_cable_surgery_identity),
]


def run_all(verbose=False):
    out = []
    for name, f in TESTS:
        try:
            ok, detail = f()
        except Exception as e:      # pragma: no cover
            ok, detail = False, 'exception %r' % (e,)
        out.append((name, bool(ok), detail))
        if verbose:
            print('%s  %s  %s' % ('ok  ' if ok else 'FAIL', name, detail), flush=True)
    return out


def assert_all(verbose=True):
    res = run_all(verbose)
    bad = [r for r in res if not r[1]]
    if bad:
        raise RuntimeError('convention tests failed: %s' % bad)
    return res
