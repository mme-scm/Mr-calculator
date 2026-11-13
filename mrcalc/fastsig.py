"""Cheaper unverified isometry signatures of closed (filled) manifolds (the search key of the coincidence step).

What SnapPy 3.3.2 does for Manifold.isometry_signature(verified=False) on a closed manifold
(snappy/isometry_signature.py, isometry_signature_closed):

  1. find_shortest_geodesics: the shortest geodesics (all within systole * (1 + 2^-16), roughly) from
     length_spectrum_alt_gen, a tiling of H^3 by lifted tetrahedra, one tiling per tetrahedron of the
     triangulation, written in Python on Sage number types (snappy/len_spec/tile.py);
  2. each of them is drilled (drill_word; a core curve of the filling is simply unfilled);
  3. canonical retriangulation of the drilled manifold, isomorphism signature, slope of the meridian;
  4. the smallest candidate (signature, slope) is the result.

Step 1 is 85-95% of the time (measured 2026-11-13 on fillings of knots up to 13 crossings), most of it in the
inner loop of the tiling, snappy.len_spec.tile._compute_length_spectrum_tiles_for_tetrahedron.  This module
provides

  * fast_tiles_for_tetrahedron: the same generator with the same operations in the same order on scalars instead
    of Sage vector and matrix objects: Python floats at 53 bits (IEEE doubles; SnapPy's unverified computation
    at 53 bits uses Sage's RealField(53), whose +, -, *, /, sqrt round the same way), the elements of
    RealField(p) at the higher precision SnapPy falls back to (212 bits) when 53 bits are not enough.  A verified
    computation (intervals) is handed to SnapPy's own generator.  tests/test_fastsig.py compares the two streams
    tile by tile.
  * unverified_signature(N, ext=None): the string Manifold.isometry_signature(verified=False) returns, computed
    with that generator.  With ext (an ExteriorInfo of the unfilled one-cusped manifold N was filled from) the
    candidates that come from the core curve of the filling are read off the canonical retriangulation of the
    unfilled manifold, which is computed once per exterior instead of once per filling (step 2 and 3 for a core
    curve are: unfill, make the filling curve the meridian, canonical retriangulation, signature, image of the
    meridian; the retriangulation and the signature do not depend on the slope).

Nothing here is used for a verified signature: the certificate path stays SnapPy's own code.  The patch of
SnapPy's module global is scoped (fast_tiler) and not thread-safe; the workers of the pipeline are single-threaded.
Written against SnapPy 3.3.2: it mirrors snappy/len_spec/tile.py, snappy/len_spec/geometry.py,
snappy/tiling/{hyperboloid_dict,real_hash_dict,floor,dict_based_set,lifted_tetrahedron_set}.py and
snappy/isometry_signature.py of that version; after an upgrade of SnapPy, tests/test_fastsig.py must pass again.
"""
import heapq
import math

import snappy
from snappy import isometry_signature as _IS
from snappy.decorated_isosig import normalized_slope
from snappy.exceptions import InsufficientPrecisionError
from snappy.len_spec import tile as _tile
from snappy.tiling import hyperboloid_dict as _hyperboloid_dict
from snappy.matrix import make_vector
from snappy.sage_helper import _within_sage
from snappy.snap.t3mlite import simplex
from snappy import verify as _verify

GEOMETRIC = 'all tetrahedra positively oriented'
_ORIGINAL_TILER = _tile._compute_length_spectrum_tiles_for_tetrahedron


def _scalars(RF):
    """Number type of the tiling: Python floats at 53 bits (same rounding as RealField(53) for + - * / sqrt),
    otherwise the elements of RF themselves (then only the Sage vector and matrix objects are avoided)."""
    if RF.precision() == 53:
        return float, math.sqrt, math.floor
    return RF, (lambda x: x.sqrt()), (lambda x: int(x.floor()))


class _TilingData:
    """The data of an Mcomplex from mcomplex_for_len_spec that the tiling uses, as scalars (see _scalars)."""

    def __init__(self, mcomplex):
        RF = mcomplex.RF
        R, self.sqrt, self.ifloor = _scalars(RF)
        self.R = R

        def f4(v):
            return (R(v[0]), R(v[1]), R(v[2]), R(v[3]))
        self.f4 = f4
        tets = mcomplex.Tetrahedra
        self.adj = {}          # tet index -> [(face, neighbour index, entry face, O13 matrix as 16 scalars, generator)]
        self.tri = {}          # tet index -> 4 triangles (plane, ((bounding plane, edge point 0, edge point 1, -inner), ...))
        self.center = {}
        self.cosh_out = {}
        self.sinh_out = {}
        for tet in tets:
            i = tet.Index
            adj = []
            for f, new_tet in tet.Neighbor.items():
                entry_face = tet.Gluing[f].image(f)
                o = tuple(R(x) for x in new_tet.O13_matrices[entry_face].list())
                adj.append((f, new_tet.Index, entry_face, o, new_tet.GeneratorsInfo[entry_face]))
            self.adj[i] = adj
            tri = []
            for f in simplex.TwoSubsimplices:
                t = tet.R13_triangles[f]
                tri.append((f4(t.plane),
                            tuple((f4(bp), f4(e.points[0]), f4(e.points[1]), R(-e.inner_product))
                                  for bp, e in zip(t.bounding_planes, t.edges))))
            self.tri[i] = tuple(tri)
            self.center[i] = f4(tet.spine_center)
            self.cosh_out[i] = R(tet.cosh_out_radius)
            self.sinh_out[i] = R(tet.sinh_out_radius)
        self.base = f4(mcomplex.R13_baseTetInCenter)
        max_eq, min_distinct = _tile._max_min_prod(mcomplex)
        self.max_eq = R(max_eq)
        self.min_distinct = R(min_distinct)
        self.matrix_space = tets[0].O13_matrices[simplex.F0].parent()
        # snappy/tiling/hyperboloid_dict.py: _hash_function, _compute_epsilon_inverse
        self.weights = (R(RF(1.2003)), R(RF(0.94553)), R(RF(1.431112)), R(RF(1.2342)))
        self.eps_inv = R(_hyperboloid_dict._compute_epsilon_inverse(RF))
        # snappy/len_spec/geometry.py: _compute_epsilon
        self.tri_eps = R(RF(0.5) ** (RF.prec() // 2))
        self.consts = (R(0), R(1), R(0.125), R(0.875), R(1e20))


class _Pending:
    """snappy.len_spec.tile._PendingLiftedTetrahedron on scalars (compared by the lower bound only, as there)."""
    __slots__ = ('k', 'word', 'ti', 'm', 'entry')

    def __init__(self, k, word, ti, m, entry):
        self.k = k
        self.word = word
        self.ti = ti
        self.m = m
        self.entry = entry

    def __lt__(self, other):
        return self.k < other.k


def _lower_bound_cosh_distance(c0, c1, c2, c3, tri, center, cosh_out, sinh_out, tri_eps, sqrt, zero, one, big):
    """snappy.len_spec.geometry.lower_bound_cosh_distance_r13_point_truncated_tetrahedron (verified=False)."""
    best = None
    for (p0, p1, p2, p3), bounding in tri:
        s = -c0 * p0 + c1 * p1 + c2 * p2 + c3 * p3
        if s <= -tri_eps:
            continue
        for (b0, b1, b2, b3), (e0, e1, e2, e3), (g0, g1, g2, g3), neg_inner in bounding:
            if -c0 * b0 + c1 * b1 + c2 * b2 + c3 * b3 > tri_eps:
                p = (-e0 * c0 + e1 * c1 + e2 * c2 + e3 * c3) * (-g0 * c0 + g1 * c1 + g2 * c2 + g3 * c3)
                q = (2 * p) / neg_inner if neg_inner > zero else big
                v = sqrt(q) if q >= zero else zero
                break
        else:
            v = sqrt(s * s + one)
        if best is None or v < best:
            best = v
    if best is None:
        raise InsufficientPrecisionError("Could not verify point outside of tetrahedron.")
    cosh_d = -(-c0 * center[0] + c1 * center[1] + c2 * center[2] + c3 * center[3])
    if not cosh_d > cosh_out:
        return best
    sinh_d = sqrt(cosh_d * cosh_d - one)
    cosh_d_out = cosh_d * cosh_out - sinh_d * sinh_out
    if not cosh_d_out > one:
        return best
    return cosh_d_out if cosh_d_out > best else best


def fast_tiles_for_tetrahedron(mcomplex, initial_tetrahedron):
    """Drop-in for snappy.len_spec.tile._compute_length_spectrum_tiles_for_tetrahedron (unverified case with
    Sage number types; a verified computation, or SnapPy without Sage, is handed to SnapPy's generator)."""
    if mcomplex.verified or not _within_sage:
        yield from _ORIGINAL_TILER(mcomplex, initial_tetrahedron)
        return
    RF = mcomplex.RF
    data = getattr(mcomplex, '_scalar_tiling_data', None)
    if data is None:
        data = mcomplex._scalar_tiling_data = _TilingData(mcomplex)
    R, sqrt, ifloor = data.R, data.sqrt, data.ifloor
    is_float = R is float
    adj, tris, centers, cosh_outs, sinh_outs = data.adj, data.tri, data.center, data.cosh_out, data.sinh_out
    b0, b1, b2, b3 = data.base
    w0, w1, w2, w3 = data.weights
    eps_inv, tri_eps = data.eps_inv, data.tri_eps
    zero, one, c125, c875, big = data.consts
    max_eq, min_distinct = data.max_eq, data.min_distinct
    matrix_space = data.matrix_space
    t0 = initial_tetrahedron.Index
    s0, s1, s2, s3 = data.f4(initial_tetrahedron.spine_center)
    inv_spine_cosh = R(initial_tetrahedron.inv_spine_cosh)
    rf_zero = RF(0)
    Tile = _tile.LengthSpectrumTile
    heappush, heappop = heapq.heappush, heapq.heappop
    lower_bound = _lower_bound_cosh_distance
    buckets = {}
    pending = [_Pending(zero, [], t0, (one, zero, zero, zero, zero, one, zero, zero, zero, zero, one, zero,
                                       zero, zero, zero, one), simplex.T)]
    while True:
        cur = heappop(pending)
        ti = cur.ti
        m = cur.m
        if ti == t0:
            # snappy.len_spec.geometry.lower_bound_geodesic_length
            k = cur.k
            bound = rf_zero
            if k > one:
                q = k * inv_spine_cosh
                if q > one:
                    bound = RF(q).arccosh()
            yield Tile(cur.word, matrix_space([RF(x) for x in m] if is_float else list(m)), bound)
        (m00, m01, m02, m03, m10, m11, m12, m13, m20, m21, m22, m23, m30, m31, m32, m33) = m
        entry = cur.entry
        for f, ni, entry_face, o, g in adj[ti]:
            if f == entry:
                continue
            (o00, o01, o02, o03, o10, o11, o12, o13, o20, o21, o22, o23, o30, o31, o32, o33) = o
            n00 = m00 * o00 + m01 * o10 + m02 * o20 + m03 * o30
            n01 = m00 * o01 + m01 * o11 + m02 * o21 + m03 * o31
            n02 = m00 * o02 + m01 * o12 + m02 * o22 + m03 * o32
            n03 = m00 * o03 + m01 * o13 + m02 * o23 + m03 * o33
            n10 = m10 * o00 + m11 * o10 + m12 * o20 + m13 * o30
            n11 = m10 * o01 + m11 * o11 + m12 * o21 + m13 * o31
            n12 = m10 * o02 + m11 * o12 + m12 * o22 + m13 * o32
            n13 = m10 * o03 + m11 * o13 + m12 * o23 + m13 * o33
            n20 = m20 * o00 + m21 * o10 + m22 * o20 + m23 * o30
            n21 = m20 * o01 + m21 * o11 + m22 * o21 + m23 * o31
            n22 = m20 * o02 + m21 * o12 + m22 * o22 + m23 * o32
            n23 = m20 * o03 + m21 * o13 + m22 * o23 + m23 * o33
            n30 = m30 * o00 + m31 * o10 + m32 * o20 + m33 * o30
            n31 = m30 * o01 + m31 * o11 + m32 * o21 + m33 * o31
            n32 = m30 * o02 + m31 * o12 + m32 * o22 + m33 * o32
            n33 = m30 * o03 + m31 * o13 + m32 * o23 + m33 * o33
            # LiftedTetrahedronSet.add: key new_m * base point, element the index of the tetrahedron
            # (RealHashDict / _Dict / floor_as_integers / hyperboloid_dict._equality_predicate)
            p0 = n00 * b0 + n01 * b1 + n02 * b2 + n03 * b3
            p1 = n10 * b0 + n11 * b1 + n12 * b2 + n13 * b3
            p2 = n20 * b0 + n21 * b1 + n22 * b2 + n23 * b3
            p3 = n30 * b0 + n31 * b1 + n32 * b2 + n33 * b3
            x = (p0 * w0 + p1 * w1 + p2 * w2 + p3 * w3) * eps_inv
            fl = ifloor(x)
            d = x - fl
            if d < c125:
                cks = (fl - 1, fl)
            elif d > c875:
                cks = (fl, fl + 1)
            else:
                cks = (fl,)
            elements = None
            for ck in cks:
                for e in buckets.get(ck, ()):
                    neg = -(-p0 * e[0] + p1 * e[1] + p2 * e[2] + p3 * e[3])
                    if neg < max_eq:
                        elements = e[4]
                        break
                    if neg > min_distinct:
                        continue
                    raise InsufficientPrecisionError(
                        "Could neither verify that the two given tiles are the same nor that they are distinct.\n"
                        "Neg inner product is:     %r.\nMax to be same tile:      %r.\n"
                        "Min to be distinct tiles: %r." % (neg, max_eq, min_distinct))
                if elements is not None:
                    break
            if elements is None:
                elements = set()
                e = (p0, p1, p2, p3, elements)
                for ck in cks:
                    lst = buckets.get(ck)
                    if lst is None:
                        buckets[ck] = [e]
                    else:
                        lst.append(e)
            if ni in elements:
                continue
            elements.add(ni)
            # o13_inverse(new_m) * spine centre of the initial tetrahedron
            c0 = n00 * s0 + -n10 * s1 + -n20 * s2 + -n30 * s3
            c1 = -n01 * s0 + n11 * s1 + n21 * s2 + n31 * s3
            c2 = -n02 * s0 + n12 * s1 + n22 * s2 + n32 * s3
            c3 = -n03 * s0 + n13 * s1 + n23 * s2 + n33 * s3
            heappush(pending, _Pending(
                lower_bound(c0, c1, c2, c3, tris[ni], centers[ni], cosh_outs[ni], sinh_outs[ni],
                            tri_eps, sqrt, zero, one, big),
                cur.word + [-g] if g != 0 else cur.word, ni,
                (n00, n01, n02, n03, n10, n11, n12, n13, n20, n21, n22, n23, n30, n31, n32, n33), entry_face))


class fast_tiler:
    """Context manager: SnapPy's length spectrum uses fast_tiles_for_tetrahedron inside the block."""

    def __enter__(self):
        self._saved = _tile._compute_length_spectrum_tiles_for_tetrahedron
        _tile._compute_length_spectrum_tiles_for_tetrahedron = fast_tiles_for_tetrahedron
        return self

    def __exit__(self, *exc):
        _tile._compute_length_spectrum_tiles_for_tetrahedron = self._saved
        return False


# ----------------------------------------------------------------------------------------------------------
# the signature
# ----------------------------------------------------------------------------------------------------------
class ExteriorInfo:
    """Per-exterior data shared by all its fillings: the isomorphism signature of the canonical retriangulation
    of the (unfilled, one-cusped) manifold E and, for every isomorphism of the retriangulation onto the
    triangulation the signature encodes, the matrix of the map on the peripheral curves (columns: images of the
    meridian and the longitude of E).  Computed on first use; `failed` is set if SnapPy could not compute it."""

    def __init__(self, E):
        self.E = E
        self.isosig = None
        self.cusp_maps = None
        self.failed = False

    def get(self):
        if self.isosig is None and not self.failed:
            try:
                M = self.E.copy()
                if M.num_cusps() != 1 or not all(M.cusp_info('complete?')):
                    raise ValueError('not an unfilled one-cusped manifold')
                retrig = M.canonical_retriangulation(verified=False)
                isosig = retrig.triangulation_isosig(decorated=False, ignore_orientation=True)
                tri = snappy.Triangulation(isosig, remove_finite_vertices=False)
                maps = []
                for iso in retrig.isomorphisms_to(tri):
                    cm, = iso.cusp_maps()
                    maps.append((int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])))
                if not maps:
                    raise ValueError('no isomorphism')
                self.isosig, self.cusp_maps = isosig, maps
            except Exception:
                self.failed = True
        return None if self.failed else (self.isosig, self.cusp_maps)


def _shortest_geodesics(manifold, bits_prec):
    """snappy.isometry_signature.find_shortest_geodesics(verified=False), returning (word, core curve) pairs:
    core curve is the index of the filled cusp whose core the geodesic is, or None."""
    spectrum = manifold.length_spectrum_alt_gen(bits_prec=bits_prec, verified=False, include_intermediates=True)
    is_first = True
    out = []
    for geodesic in spectrum:
        if is_first:
            if geodesic._is_intermediate:
                continue
            systole = geodesic.length.real()
            cutoff = _IS.compute_cutoff(systole)
            is_first = False
        r = geodesic.length.real()
        if r > cutoff:
            break
        if geodesic._is_intermediate:
            continue
        if r < cutoff:
            out.append((geodesic.word, geodesic.core_curve))
            continue
        raise InsufficientPrecisionError("Could not determine whether geodesic length is less or greater than cutoff.")
    return out


def _shortest_geodesics_precisions(manifold, bits_precs):
    err = ValueError("bits_precs was empty.")
    for bits_prec in bits_precs:
        try:
            return _shortest_geodesics(manifold, bits_prec)
        except (InsufficientPrecisionError, ValueError, RuntimeError) as e:
            err = e
    raise err


def _geodesics(N, retries, stats):
    """(M, shortest geodesics of M): M is N or a randomised copy of it.

    SnapPy's sequence is 53 bits, then 212 bits on the same triangulation.  The 53-bit tiling fails on some
    triangulations (rounding errors of long matrix products: "Could neither verify that the two given tiles
    are the same nor that they are distinct"), and the 212-bit computation costs several times more, so up to
    `retries` randomised copies of the triangulation are tried at 53 bits first."""
    bits_precs = list(_verify.default_interval_bits_precs)
    M = N
    for attempt in range(retries + 1):
        try:
            with fast_tiler():
                return M, _shortest_geodesics(M, bits_precs[0])
        except (InsufficientPrecisionError, ValueError, RuntimeError):
            if stats is not None:
                stats['failed_53'] = stats.get('failed_53', 0) + 1
        if attempt == retries:
            break
        M = M.copy()
        M.randomize()
        for t in range(4):
            if M.solution_type() == GEOMETRIC:
                break
            M.randomize()
        else:
            break
    if stats is not None:
        stats['higher_precision'] = 1
    with fast_tiler():
        return N, _shortest_geodesics_precisions(N, bits_precs[1:])


def unverified_signature(N, ext=None, slope=None, stats=None, retries=2):
    """Manifold.isometry_signature(verified=False) of the closed manifold N (a one-cusped manifold with a
    filling), computed with the scalar tiling.

    ext, slope: N is ext.E (or a triangulation obtained from it by Pachner moves, e.g. randomize) filled along
    slope = (p, q) in the peripheral curves of ext.E.  Then a shortest geodesic that is the core curve of the
    filling is not drilled: its candidates are (ext.isosig, normalised image of the slope).
    stats: optional dict, receives 'geodesics', 'core' (number of core-curve geodesics), 'shortcut',
    'failed_53', 'higher_precision'."""
    bits_precs = _verify.default_interval_bits_precs
    if any(N.cusp_info('complete?')) or not N.is_orientable():
        with fast_tiler():
            return N.isometry_signature(verified=False)
    N, geodesics = _geodesics(N, retries, stats)
    info = ext.get() if (ext is not None and slope is not None) else None
    if stats is not None:
        stats['geodesics'] = len(geodesics)
        stats['core'] = sum(1 for w, c in geodesics if c is not None)
        stats['shortcut'] = 0
    potential = []
    for word, core in geodesics:
        if core is not None and info is not None and N.num_cusps() == 1:
            isosig, maps = info
            p, q = slope
            for a, b, c, d in maps:
                potential.append((isosig, normalized_slope(make_vector([a * p + b * q, c * p + d * q]))))
            if stats is not None:
                stats['shortcut'] += 1
            continue
        drilled = _IS.drill_manifold_precisions(N, word, bits_precs=bits_precs, verified=False, verbose=False)
        if not all(drilled.cusp_info('complete?')):
            drilled = drilled.filled_triangulation()
        try:
            retrig = drilled.canonical_retriangulation(verified=False)
        except Exception as e:
            raise RuntimeError("Could not compute canonical retriangulation of drilled manifold. "
                               "Geodesic was: %s." % word) from e
        isosig = retrig.triangulation_isosig(decorated=False, ignore_orientation=True)
        for s in _IS.compute_meridian_slopes(isosig, retrig):
            potential.append((isosig, s))
    isosig, (m, l) = min(potential, key=_IS.key_signature)
    return '%s(%d,%d)' % (isosig, m, l)
