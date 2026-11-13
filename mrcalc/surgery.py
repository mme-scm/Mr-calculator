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


def redescriptions(N, max_curves=6):
    """Other surgery descriptions of the closed manifold N (a one-cusped manifold with a filling).

    A short curve of the dual 1-skeleton is drilled (Manifold.drill; the old cusp keeps its filling), the old
    cusp is filled for good, and the new cusp is filled along its meridian (1,0), which gives N back
    (convention of SnapPy's drilling, tested in tests/test_surgery.py and mrcalc/conventions.py).  For small
    closed hyperbolic manifolds the filled triangulation of a knot exterior often has no positively oriented
    solution under any randomisation, while such a description has one.  Yields one-cusped filled manifolds."""
    try:
        n = min(len(N.dual_curves()), max_curves)
    except Exception:
        return
    for i in range(n):
        try:
            F = N.drill(i).filled_triangulation()
            if F.num_cusps() != 1:
                continue
            F.dehn_fill((1, 0), 0)
        except Exception:
            continue
        yield F


def _redescribed_geometric(N, tries=4):
    """A redescription of N with a positively oriented solution, or None.  N must have a solution (negatively
    oriented tetrahedra allowed) of volume above 0.5; the result is kept only if it has the homology of N and
    the same volume up to 1e-6 (guard against a wrong description)."""
    try:
        if N.solution_type() in ('contains degenerate tetrahedra', 'no solution found', 'not attempted'):
            return None
        vol = float(N.volume())
        if vol < 0.5:
            return None
        hom = str(N.homology())
    except Exception:
        return None
    for F in redescriptions(N):
        try:
            for t in range(tries):
                if F.solution_type() == GEOMETRIC:
                    if str(F.homology()) == hom and abs(float(F.volume()) - vol) < 1e-6:
                        return F
                    break
                F.randomize()
        except Exception:
            continue
    return None


def geometric_filling(E, slope, tries=12, redescribe=True):
    """Return the filling of E along slope with a positively oriented solution, or None: a filled copy of E,
    or (redescribe) another surgery description of the same closed manifold, see redescriptions()."""
    N = E.copy()
    N.dehn_fill(tuple(slope))
    for t in range(tries):
        if N.solution_type() == GEOMETRIC:
            return N
        N.randomize()
    return _redescribed_geometric(N) if redescribe else None


def hyperbolic_signature(E, slope, verified=True, tries=12):
    """(isometry signature ignoring orientation, verified flag) of the filling or None.

    The signature is only returned when verify_hyperbolicity succeeds on a triangulation of
    the filling (verified=True) so that it refers to a verified hyperbolic structure."""
    N = E.copy()
    N.dehn_fill(tuple(slope))
    for t in range(tries):
        if N.solution_type() == GEOMETRIC:
            r = _signature(N, verified)
            if r:
                return r
        N.randomize()
    # no signature from the filled triangulation (no positively oriented solution on it, or the signature
    # computation failed on those found): another surgery description of the same closed manifold
    F = _redescribed_geometric(N)
    for t in range(4 if F is not None else 0):
        if F.solution_type() == GEOMETRIC:
            r = _signature(F, verified)
            if r:
                return r
        F.randomize()
    return None


# second attempt of the verified signature: more interval precision and higher degrees of the exact fields
_HARD = {'interval_bits_precs': [53, 212, 1000],
         'exact_bits_prec_and_degrees': [(212, 10), (1000, 20), (2000, 20), (4000, 40)]}


def _signature(N, verified):
    try:
        if not N.verify_hyperbolicity()[0]:
            return None
    except BaseException as e:            # cysignals' SignalError is a BaseException
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        return None
    for kw in (({}, _HARD) if verified else ({},)):
        try:
            return {'sig': N.isometry_signature(verified=verified, **kw), 'verified': True,
                    'volume': float(N.volume())}
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
    return None


def verified_filling(E, slope, tries=40):
    """A description of the filling with a positively oriented solution on which verify_hyperbolicity
    succeeds, or None."""
    N = geometric_filling(E, slope, tries=tries)
    for t in range(12 if N is not None else 0):
        try:
            if N.solution_type() == GEOMETRIC and N.verify_hyperbolicity()[0]:
                return N
            N.randomize()
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
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


def regina_recognise(tri_string, time_limit=3.0, height=2, visit_cap=5000):
    """Recognise a closed 3-manifold given as a SnapPea-format triangulation string.
    Returns {'kind': 'lens'|'sfs'|'unknown', 'name': ..., 'how': ...}.  The search over
    retriangulations stops at the time limit (seconds) or after visit_cap triangulations."""
    import time
    import regina
    T = regina.Triangulation3(tri_string)
    T.intelligentSimplify()
    t0 = time.time()

    def attempt(T, sig=None):
        st = regina.StandardTriangulation.recognise(T)
        if st is not None:
            try:
                m = st.manifold()
            except Exception:
                m = None
            kind, nm = norm_manifold(m)
            if kind:
                return {'kind': kind, 'name': nm, 'how': 'regina-recognise', 'regina_name': m.name()}
        for h in regina.Census.lookup(sig or T.isoSig()):
            kind, nm = norm_name_string(h.name())
            if kind:
                return {'kind': kind, 'name': nm, 'how': 'regina-census', 'regina_name': h.name()}
        return None

    r = attempt(T)
    if r:
        return r
    res = {}
    cnt = [0]

    def act(sig, tri):
        cnt[0] += 1
        x = attempt(tri, sig)
        if x:
            res['r'] = x
            return True
        return cnt[0] >= visit_cap or (time.time() - t0) > time_limit

    if time_limit > 0:
        try:
            T.retriangulate(height, 1, act)
        except Exception:
            pass
    if 'r' in res:
        return res['r']
    out = {'kind': 'unknown', 'name': None, 'how': 'none', 'visited': cnt[0]}
    if cnt[0] < visit_cap and (time.time() - t0) > time_limit:
        out['timeout'] = True
    return out


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
