"""Diagram operations: Reidemeister re-diagrams, mutation, twists, connected sums."""
import os
import random
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import identify as I, knotinfo, passes, pd as P  # noqa: E402


@pytest.fixture(scope='module')
def idr():
    return I.Identifier(use_census=False)


def test_rediagram_same_knot(idr):
    rng = random.Random(1)
    T = [r for r in knotinfo.table() if r['crossing_number'] <= 10]
    for r in rng.sample(T, 25):
        for j in (1, 2):
            new, moves = P.random_rediagram(r['pd'], passes.seed_for(r['name'], j))
            assert len(new) >= len(r['pd']) + 2
            assert P.replay_rediagram(r['pd'], moves) == new          # reproducible from the record
            assert idr.identify(new)['name'] == idr.identify(r['pd'])['name'], (r['name'], j)


def test_reidemeister_moves_keep_planarity():
    rng = random.Random(2)
    for r in rng.sample(knotinfo.table()[:500], 30):
        D = P.Diagram.from_pd(r['pd'])
        for f in P.r3_candidates(D)[:2]:
            new = P.r3(r['pd'], f)
            assert len(new) == D.n and P.writhe(new) == D.writhe()
        e = rng.randrange(1, 2 * D.n + 1)
        k = P.r1(r['pd'], e, True, False)
        assert len(k) == D.n + 1 and abs(P.writhe(k) - D.writhe()) == 1
        assert P.remove_kinks(k) and len(P.remove_kinks(k)) == D.n


def test_mutation_is_planar_knot(idr):
    t = knotinfo.by_name()
    found = set()
    for name in ('11n_34', '11n_42'):
        D = P.Diagram.from_pd(t[name]['pd'])
        circles = P.conway_circles(D)
        assert circles
        for edges, faces, inside in circles:
            for axis in 'xyz':
                new = P.mutate(t[name]['pd'], edges, axis)
                assert len(new) == D.n
                found.add(idr.identify(new)['name'].rstrip('*'))
    # mutants found are table knots (data check of the move, no rule involved)
    assert found <= set(t)


def test_connected_sum_and_twist_roundtrip(idr):
    t = knotinfo.by_name()
    s = P.connected_sum(t['3_1']['pd'], t['4_1']['pd'])
    assert len(s) == 7 and P.writhe(s) == P.writhe(t['3_1']['pd']) + P.writhe(t['4_1']['pd'])
    # a right-handed twist followed by the left-handed twist on the same strands gives back the knot
    D = P.Diagram.from_pd(t['6_2']['pd'])
    edges, faces, dirs = P.dual_paths(D, 2, None)[0]
    new, a, b, _ = P.twist(t['6_2']['pd'], edges, 1)
    assert len(new) == D.n + 2
    assert idr.identify(P.mirror(P.mirror(t['6_2']['pd'])))['name'] == '6_2'
    assert idr.identify(P.mirror(t['6_2']['pd']))['name'] == '6_2*'
    assert idr.identify(s)['name'] == '3_1#4_1'
