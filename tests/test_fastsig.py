"""mrcalc.fastsig: the unverified signature is the string SnapPy's isometry_signature(verified=False) returns,
and the scalar tiling yields the tiles of SnapPy's generator (words, matrices, bounds)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import fastsig, nodeset, surgery as S  # noqa: E402

# fillings whose shortest geodesic is the core curve of the filling (5_2, 7_4) and is not (4_1, 6_2)
CASES = (('5_2', (-2, 3)), ('7_4', (-1, 2)), ('4_1', (5, 1)), ('6_2', (5, 1)))


def _filling(node, slope):
    E = S.exterior(nodeset.diagram(node))
    N = S.geometric_filling(E, slope, redescribe=False)
    assert N is not None, (node, slope)
    return E, N


def test_unverified_signature_is_snappys():
    shortcut = 0
    for node, slope in CASES:
        E, N = _filling(node, slope)
        info = S.exterior_info(E)
        ref = N.isometry_signature(verified=False)
        assert fastsig.unverified_signature(N) == ref, (node, slope)
        stats = {}
        assert fastsig.unverified_signature(N, info, slope, stats) == ref, (node, slope)
        shortcut += stats['shortcut']
        r = S.hyperbolic_signature(E, slope, verified=False, info=info)
        assert r and r['sig'] == ref and r['verified'] is False, (node, slope)
        v = S.hyperbolic_signature(E, slope, verified=True)
        assert v and v['sig'] == ref and v['verified'] is True, (node, slope)
    assert shortcut >= 1                      # the per-exterior shortcut for core curves was exercised


def test_tiles_are_snappys():
    from snappy.len_spec.geometric_structure import mcomplex_for_len_spec

    def read(gen, bound):
        out = []
        try:
            for tile in gen:
                out.append((tile.word, tile.o13_matrix, tile.lower_bound_geodesic_length))
                if tile.lower_bound_geodesic_length > bound:
                    break
        except Exception as e:                # both generators must fail at the same place
            out.append(type(e).__name__)
        return out
    n = 0
    for bits, bound in ((53, 0.9), (212, 0.5)):
        for node, slope in CASES[1:3]:
            E, N = _filling(node, slope)
            mc = mcomplex_for_len_spec(N, bits_prec=bits, verified=False)
            for tet in mc.Tetrahedra:
                a = read(fastsig._ORIGINAL_TILER(mc, tet), bound)
                b = read(fastsig.fast_tiles_for_tetrahedron(mc, tet), bound)
                assert a == b, (bits, node, slope, tet.Index)
                n += len(a)
    assert n > 50
