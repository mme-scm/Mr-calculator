"""Knot Floer calculator wrapper (knot_floer_homology.pd_to_hfk) with a time limit.

Returned record: tau, nu, epsilon, genus, fibered, lspace, total_rank, ranks (list of
[A, M, rank]) and, when requested, the UV=0 complex (generators, differentials)."""
import hashlib
import json


def pd_key(pd):
    return hashlib.sha1(json.dumps([list(c) for c in pd], separators=(',', ':')).encode()).hexdigest()[:20]


UNKNOT = {'tau': 0, 'nu': 0, 'epsilon': 0, 'genus': 0, 'fibered': True, 'lspace': True, 'total_rank': 1,
          'ranks': [[0, 0, 1]], 'note': 'diagram reduces to the round circle by Reidemeister 1 moves'}


def _run(pd, want_complex):
    import knot_floer_homology as kfh
    from .pd import remove_kinks
    pd = remove_kinks(pd)        # the calculator rejects diagrams with Reidemeister-1 kinks
    if not pd:
        out = dict(UNKNOT)
        if want_complex:
            out['generators'] = [[0, 0, 0]]
            out['differentials'] = []
        return out
    r = kfh.pd_to_hfk([tuple(c) for c in pd], complex=want_complex)
    out = {
        'tau': int(r['tau']), 'nu': int(r['nu']), 'epsilon': int(r['epsilon']),
        'genus': int(r['seifert_genus']), 'fibered': bool(r['fibered']),
        'lspace': bool(r['L_space_knot']), 'total_rank': int(r['total_rank']),
        'ranks': sorted([int(a), int(m), int(v)] for (a, m), v in r['ranks'].items()),
    }
    if want_complex:
        gens = r['generators']
        out['generators'] = [[int(g), int(gens[g][0]), int(gens[g][1])] for g in sorted(gens)]
        out['differentials'] = sorted([int(a), int(b)] for (a, b), v in r['differentials'].items() if v % 2)
    return out


def hfk(pd, want_complex=False, timeout=None, inline_below=26):
    """Run the calculator.  Small diagrams run inline; large ones in a separate interpreter
    with a time limit.  Returns the record or {'timeout': True} / {'error': ...}."""
    if timeout is None or len(pd) < inline_below:
        try:
            return _run(pd, want_complex)
        except Exception as e:
            return {'error': repr(e)}
    import os
    import subprocess
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code = ('import sys, json; sys.path.insert(0, %r); from mrcalc.hfk import _run; '
            'd = json.load(sys.stdin); print(json.dumps(_run(d["pd"], d["c"])))' % root)
    try:
        r = subprocess.run([sys.executable, '-W', 'ignore', '-c', code],
                           input=json.dumps({'pd': [list(c) for c in pd], 'c': bool(want_complex)}),
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'timeout': True}
    if r.returncode != 0:
        return {'error': r.stderr[-300:]}
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {'error': repr(e)}


def ranks_dict(rec):
    return {(a, m): v for a, m, v in rec['ranks']}


def mirror_ranks(ranks):
    """HFK ranks of the mirror: (A, M) -> (-A, -M)."""
    return sorted([-a, -m, v] for a, m, v in ranks)


def alexander(rec):
    from .alg import alexander_from_hfk_ranks
    return alexander_from_hfk_ranks(ranks_dict(rec))
