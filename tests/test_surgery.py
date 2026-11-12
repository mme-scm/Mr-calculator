"""Recognition of fillings: name normalisation, Moser (S2) against Regina, the two Regina routes."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import nodeset, surgery as S  # noqa: E402


def test_name_normalisation():
    assert S.norm_lens(5, 4) == 'L(5,1)' and S.norm_lens(7, 2) == S.norm_lens(7, 4) == S.norm_lens(7, 3) == 'L(7,2)'
    a = S.norm_sfs_s2([(2, 1), (3, 1), (7, -6)])
    b = S.norm_sfs_s2([(3, 1), (7, 1), (2, 1)], -1)
    c = S.norm_sfs_s2([(2, -1), (3, -1), (7, 6)])          # orientation reversed
    assert a == b == c
    assert S.norm_sfs_s2([(2, 1), (3, 1)]) is None          # fewer than three exceptional fibres
    assert S.norm_name_string('SFS [S2: (2,1) (3,1) (7,-6)] : #1') == ('sfs', a)
    assert S.norm_name_string('L(18,5) : #1') == ('lens', 'L(18,5)')
    assert S.norm_name_string('Hyp_1.2') == (None, None)


def test_moser_against_regina():
    for (r, s) in ((2, 3), (2, 5), (3, 4)):
        E = S.exterior(nodeset.diagram('T(%d,%d)' % (r, s)))
        for m, n in ((r * s + 1, 1), (r * s - 1, 1), (2 * r * s + 1, 2), (1, 1), (-1, 1), (3, 1)):
            kind, nm = S.moser(r, s, m, n)
            rec = S.regina_recognise(S.filled_string(E, (m, n)), time_limit=5)
            if kind == 'lens':
                assert rec['kind'] == 'lens' and rec['name'] == nm, (r, s, m, n, rec, nm)
            elif kind == 'sfs' and rec['kind'] == 'sfs':
                assert S.sfs_orders(rec['name']) == nm, (r, s, m, n, rec, nm)


def test_regina_routes_agree():
    import regina
    n = 0
    for node in ('3_1', '4_1', '8_20'):
        E = S.exterior(nodeset.diagram(node))
        for p, q in S.slope_set(8, 2):
            T = regina.Triangulation3(S.filled_string(E, (p, q)))
            T.intelligentSimplify()
            st = regina.StandardTriangulation.recognise(T)
            a = S.norm_manifold(st.manifold()) if st is not None else (None, None)
            b = None
            for h in regina.Census.lookup(T.isoSig()):
                k, nm = S.norm_name_string(h.name())
                if k:
                    b = (k, nm)
                    break
            if a[0] and b:
                n += 1
                assert a == b, (node, p, q, a, b)
    assert n >= 5


def test_mirror_fillings_coincide():
    """S_{-p/q}(K*) = -S_{p/q}(K), and the certificates are up to orientation: the filling p/q of K and the
    filling -p/q of the mirror get the same verified signature and the same normalised name, while the
    fillings p/q of K and of the mirror (chiral knots, slopes chosen for the test) do not."""
    import regina
    from mrcalc import pd as PD
    for node, slope in (('8_20', (7, 2)), ('10_139', (3, 1)), ('5_2', (-7, 1))):
        d = nodeset.diagram(node)
        E, Em = S.exterior(d), S.exterior(PD.mirror(d))
        p, q = slope
        a = S.hyperbolic_signature(E, (p, q))
        b = S.hyperbolic_signature(Em, (-p, q))
        c = S.hyperbolic_signature(Em, (p, q))
        assert a and b and a['sig'] == b['sig'], (node, slope)
        assert c is None or c['sig'] != a['sig'], (node, slope)

    def name(E, slope):
        T = regina.Triangulation3(S.filled_string(E, slope))
        T.intelligentSimplify()
        st = regina.StandardTriangulation.recognise(T)
        return S.norm_manifold(st.manifold()) if st is not None else (None, None)
    d = nodeset.diagram('3_1')
    E, Em = S.exterior(d), S.exterior(PD.mirror(d))
    n = 0
    for p, q in ((1, 1), (-1, 1), (2, 1), (-2, 1), (7, 2), (-7, 2), (4, 1), (-4, 1)):
        a, b, c = name(E, (p, q)), name(Em, (-p, q)), name(Em, (p, q))
        if a[0] and b[0]:
            n += 1
            assert a == b, (p, q, a, b)
            if c[0]:
                assert c != a, (p, q, a, c)
    assert n >= 4
