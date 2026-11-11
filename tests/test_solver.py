"""Solver tests: incremental mode gives the same fixpoint as a full solve; required route test data."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import prepare, solver  # noqa: E402

EDGE_RULES = {'F7', 'C7', 'U5', 'F9', 'U6', 'F6'}


@pytest.fixture(scope='module')
def problem():
    P = prepare.Problem()
    solver.SLOPES.clear()
    solver.SLOPES.update(P.slopes)
    return P


def light_solver():
    """A solver that keeps the state only (no events): the problem is the real one and has millions of
    constraints; with events and their domains two solvers would need more than 10 GB."""
    S = solver.Solver()
    S.keep, S.record = None, False
    return S


def test_incremental_equals_full(problem):
    full = light_solver()
    full.add(problem.cons)
    full.run()
    inc = light_solver()
    base = [c for c in problem.cons if c['rule'] not in EDGE_RULES]
    edges = [c for c in problem.cons if c['rule'] in EDGE_RULES]
    inc.add(base)
    inc.run()
    n0 = inc.napplied
    step = max(1, len(edges) // 7)
    for i in range(0, len(edges), step):
        inc.add(edges[i:i + step])      # one "shard" of edges: re-propagates locally
        inc.run()
    for n in problem.nodes:
        for d in 'FCU':
            assert full.get(n, d) == inc.get(n, d), (n, d)
    # local re-propagation: far fewer applications than a full re-solve per shard
    assert inc.napplied - n0 < 3 * full.napplied


def test_trefoil_and_8_19(problem):
    S = light_solver()
    S.add(problem.cons)
    S.run()
    assert S.pins('3_1') == {'M': 4, 'r_2': 4, 'nu': 1, 'r_0': 1, 'tau': 1, 'upsilon': -1}
    assert S.pins('8_19')['M'] == 8
    assert S.pins('0_1') == {'M': 0, 'r_2': 0, 'nu': 0, 'r_0': 0, 'tau': 0, 'upsilon': 0}
