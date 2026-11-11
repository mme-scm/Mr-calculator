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
