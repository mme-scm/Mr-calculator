"""Dehn fillings of knot exteriors: hyperbolic signatures and Regina recognition.

Slopes are with respect to the Seifert framing of the exterior built by spherogram from a
PD code; the convention test (tests/test_conventions.py) checks that +5 and +7 surgery on
KnotInfo's 3_1 are lens spaces and -1 surgery is the (2,3,7) Seifert fibred space.
Everything here is up to orientation of the filling.
"""
from __future__ import annotations

import re
from math import gcd

GEOMETRIC = 'all tetrahedra positively oriented'


def exterior(pd):
    import snappy  # noqa: F401  (registers the exterior constructor)
    import spherogram
    return spherogram.Link([list(c) for c in pd]).exterior()


def geometric_filling(E, slope, tries=12):
    """Return a copy of E filled along slope with a positively oriented solution, or None."""
    N = E.copy()
    N.dehn_fill(tuple(slope))
    for t in range(tries):
        if N.solution_type() == GEOMETRIC:
            return N
        N.randomize()
    return None


def hyperbolic_signature(E, slope, verified=True, tries=12):
    """(isometry signature ignoring orientation, verified flag) of the filling or None.

    The signature is only returned when verify_hyperbolicity succeeds on a triangulation of
    the filling (verified=True) so that it refers to a verified hyperbolic structure."""
    N = E.copy()
    N.dehn_fill(tuple(slope))
    for t in range(tries):
        if N.solution_type() == GEOMETRIC:
            try:
                ok = N.verify_hyperbolicity()[0]
            except Exception:
                ok = False
            if ok:
                try:
                    sig = N.isometry_signature(verified=verified)
                    return {'sig': sig, 'verified': True, 'volume': float(N.volume())}
                except Exception:
                    pass
        N.randomize()
    return None


# ----------------------------------------------------------------------
# Regina names
# ----------------------------------------------------------------------
def norm_lens(p, q):
    p = abs(p)
    if p == 0:
        return 'S2xS1'
    if p == 1:
        return 'S3'
    q %= p
    qi = pow(q, -1, p)
    q0 = min(q, p - q, qi, p - qi)
    return 'L(%d,%d)' % (p, q0)


def norm_sfs_s2(fibres, b=0):
    """Normalised name of the Seifert fibred space over S^2 with the given (alpha, beta)
    fibres and obstruction b, up to orientation.  Returns None if fewer than three
    exceptional fibres remain (lens space or similar; not handled here)."""
    fs = []
    for a, be in fibres:
        if a < 0:
            a, be = -a, -be
        if a == 0:
            return None
        if gcd(a, be) != 1:
            return None
        b += be // a
        be %= a
        if a == 1:
            continue
        fs.append((a, be))
    if len(fs) < 3:
        return None
    k = len(fs)
    f1 = sorted(fs)
    f2 = sorted((a, a - be) for a, be in fs)
    c1 = (f1, b)
    c2 = (f2, -b - k)
    f, bb = min(c1, c2)
    return 'SFS[S2:%s;%d]' % (' '.join('(%d,%d)' % x for x in f), bb)


_LENS_RE = re.compile(r'^L\((\d+),(\d+)\)$')
_SFS_RE = re.compile(r'^SFS \[S2: ((?:\(-?\d+,-?\d+\)\s*)+)\]$')
_FIB_RE = re.compile(r'\((-?\d+),(-?\d+)\)')


def norm_name_string(name):
    """Normalise a Regina manifold name (census or recognition).  Returns (kind, name) with
    kind in {'lens', 'sfs', None}."""
    name = name.split(' : ')[0].strip()
    if name == 'RP3':
        return 'lens', 'L(2,1)'
    if name == 'S3':
        return 'lens', 'S3'
    m = _LENS_RE.match(name)
    if m:
        return 'lens', norm_lens(int(m.group(1)), int(m.group(2)))
    m = _SFS_RE.match(name)
    if m:
        fibres = [(int(a), int(b)) for a, b in _FIB_RE.findall(m.group(1))]
        nm = norm_sfs_s2(fibres, 0)
        if nm:
            return 'sfs', nm
    return None, None


def norm_manifold(m):
    """Normalise a regina Manifold object."""
    import regina
    if m is None:
        return None, None
    if isinstance(m, regina.LensSpace):
        return 'lens', norm_lens(m.p(), m.q())
    if isinstance(m, regina.SFSpace):
        ls = m.isLensSpace()
        if ls is not None:
            return 'lens', norm_lens(ls.p(), ls.q())
        if (m.baseClass() == regina.SFSpace.o1 and m.baseGenus() == 0 and m.punctures() == 0
                and m.reflectors() == 0):
            fibres = [(m.fibre(i).alpha, m.fibre(i).beta) for i in range(m.fibreCount())]
            nm = norm_sfs_s2(fibres, m.obstruction())
            if nm:
                return 'sfs', nm
    return None, None


def regina_recognise(tri_string, effort=2):
    """Recognise a closed 3-manifold given as a SnapPea-format triangulation string.
    Returns {'kind': 'lens'|'sfs'|'unknown', 'name': ..., 'how': ...}."""
    import regina
    T = regina.Triangulation3(tri_string)
    T.intelligentSimplify()
    seen = set()

    def attempt(T):
        st = regina.StandardTriangulation.recognise(T)
        if st is not None:
            try:
                m = st.manifold()
            except Exception:
                m = None
            kind, nm = norm_manifold(m)
            if kind:
                return {'kind': kind, 'name': nm, 'how': 'recognise', 'regina_name': m.name(),
                        'isosig': T.isoSig()}
        for h in regina.Census.lookup(T.isoSig()):
            kind, nm = norm_name_string(h.name())
            if kind:
                return {'kind': kind, 'name': nm, 'how': 'census', 'regina_name': h.name(),
                        'isosig': T.isoSig()}
        return None

    r = attempt(T)
    if r:
        return r
    for round_ in range(effort * 8):
        U = regina.Triangulation3(T)
        for _ in range(4 + round_):
            # random 2-3 moves then simplify
            import random
            tris = [t for t in U.triangles() if U.pachner(t, True, False)]
            if not tris:
                break
            U.pachner(random.choice(tris), False, True)
        U.intelligentSimplify()
        s = U.isoSig()
        if s in seen:
            continue
        seen.add(s)
        r = attempt(U)
        if r:
            return r
    return {'kind': 'unknown', 'name': None, 'how': 'none', 'isosig': T.isoSig()}


def filled_string(E, slope):
    N = E.copy()
    N.dehn_fill(tuple(slope))
    return N.filled_triangulation()._to_string()


# ----------------------------------------------------------------------
# S2 (Moser)
# ----------------------------------------------------------------------
def moser(r, s, m, n):
    """Filling of the positive torus knot T(r,s) along m/n.
    Returns ('lens', name) | ('reducible', None) | ('sfs', (r, s, |delta|))."""
    delta = r * s * n - m
    if abs(delta) == 1:
        return 'lens', norm_lens(abs(m), (n * s * s) % abs(m))
    if delta == 0:
        return 'reducible', None
    return 'sfs', tuple(sorted((r, s, abs(delta))))


def sfs_orders(name):
    """Orders of the exceptional fibres of a normalised SFS name."""
    return tuple(sorted(int(a) for a, b in _FIB_RE.findall(name)))


def slope_set(pmax=30, qmax=4, extra_integer=0):
    out = []
    for q in range(1, qmax + 1):
        for p in range(-pmax, pmax + 1):
            if p != 0 and gcd(abs(p), q) == 1:
                out.append((p, q))
    for p in range(-extra_integer, extra_integer + 1):
        if p != 0 and (p, 1) not in out:
            out.append((p, 1))
    return out
