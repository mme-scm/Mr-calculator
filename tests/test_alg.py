"""Alexander polynomial from a Seifert matrix: the fast route (characteristic polynomial, Sage integers) gives
the same list as the plain one (determinants at integer points, interpolation)."""
import pytest

from mrcalc import alg


def _matrices():
    import snappy  # noqa: F401
    import spherogram
    out = []
    for name in ('3_1', '4_1', '8_19', '10_124', '10_130', 'K12n242', 'K13n4587', 'K14n1000'):
        L = spherogram.Link(name)
        out.append((name, [list(map(int, r)) for r in L.seifert_matrix()]))
    import random
    random.seed(3)
    for i in range(6):                       # larger matrices: random 5-strand braid closures that are knots
        while True:
            w = [random.choice([1, -1]) * random.randint(1, 4) for _ in range(44)]
            L = spherogram.Link(braid_closure=w)
            if len(L.link_components) == 1:
                break
        out.append(('braid%d' % i, [list(map(int, r)) for r in L.seifert_matrix()]))
    return out


def test_routes_agree():
    pytest.importorskip('sage.all')
    sizes = []
    for name, V in _matrices():
        if not V:
            continue
        plain = alg.alexander_from_seifert(V, route='plain')
        fast = alg.alexander_from_seifert(V, route='charpoly')
        assert plain == fast, name
        assert alg._coeffs_plain(V) == alg._coeffs_charpoly(V), name      # before normalisation as well
        assert alg.alexander_from_seifert(V) == plain, name
        sizes.append(len(V))
    assert max(sizes) > alg._PLAIN_N                                    # the default takes both routes here


def test_known_values():
    import spherogram
    V = [list(map(int, r)) for r in spherogram.Link('3_1').seifert_matrix()]
    assert alg.alexander_from_seifert(V) == [1, -1, 1]
    V = [list(map(int, r)) for r in spherogram.Link('4_1').seifert_matrix()]
    assert alg.alexander_from_seifert(V) == [1, -3, 1]
    assert alg.alexander_from_seifert([]) == [1]
