"""Tests of the independent checker (checker/check.py) and of route.py.

tests/tiny_export is a small export in the format of export/FORMAT.md (9 nodes, about 100 events,
with crossing-change edges, a connected sum and mirror applications that emit two events).  It was
written by the solver and the export functions of mrcalc, not by the checker; see
tests/make_tiny_export.py.  The corruption tests work on a temporary copy of it.

The last test compares the operators of the checker with those of the solver on random domains.
It is the only test of the operators that the current export does not exercise (S1/S3/S4, F9, U6,
F6, F10, F16, U1, U3).  It imports mrcalc; the checker itself never does.
"""
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, 'checker', 'check.py')
ROUTE = os.path.join(ROOT, 'route.py')
EXPORT = os.path.join(ROOT, 'export')
TINY = os.path.join(ROOT, 'tests', 'tiny_export')

needs_export = pytest.mark.skipif(not (os.path.exists(os.path.join(EXPORT, 'events.jsonl')) or
                                       os.path.exists(os.path.join(EXPORT, 'events.jsonl.gz'))),
                                  reason='export/ is not present')
PACK = os.path.join(ROOT, 'scripts', 'export_pack.py')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope='module')
def check():
    return load(CHECK, 'checker_check')


@pytest.fixture(scope='module')
def route():
    return load(ROUTE, 'route_module')


def run(script, *args):
    p = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def summary(out):
    """label -> first integer of the summary lines of check.py"""
    res = {}
    for line in out.split('SUMMARY', 1)[1].split('\n'):
        m = re.match(r'\s+(.*?)\s*:\s*(\d+)', line)
        if m:
            res[m.group(1)] = int(m.group(2))
    return res


ZERO = ['digest mismatches', '`in` mismatches', 'targets that do not change', 'other event/constraint errors',
        'empty domains', 'final-domain mismatches', 'pin mismatches', 'pin-event mismatches',
        'last-event mismatches', 'chain-name mismatches', 'chain files different', 'csv mismatches',
        'unresolved edges']


def assert_only(out, want=()):
    """Every counter of the summary is 0 except the given ones (label -> value, None: any value > 0)."""
    s = summary(out)
    want = dict(want)
    assert set(want) <= set(ZERO)
    for label in ZERO:
        if label in want:
            if want[label] is None:
                assert s[label] > 0, (label, out)
            else:
                assert s[label] == want[label], (label, out)
        else:
            assert s[label] == 0, (label, out)


# --------------------------------------------------------------------------------------
# (i) the real export
# --------------------------------------------------------------------------------------
@pytest.mark.slow
@needs_export
def test_checker_accepts_export():
    code, out = run(CHECK, EXPORT)
    assert code == 0, out[-4000:]
    assert 'RESULT: OK' in out
    assert_only(out)
    s = summary(out)
    with open(os.path.join(EXPORT, 'summary.json')) as f:
        info = json.load(f)
    assert s['events checked'] == info['events'] > 0
    assert s['chain files identical'] > 0


# --------------------------------------------------------------------------------------
# (ii) route.py
# --------------------------------------------------------------------------------------
@needs_export
def test_route_8_19_M():
    code, out = run(ROUTE, '8_19', 'M')
    assert code == 0, out
    lines = out.rstrip('\n').split('\n')
    assert lines[-1].startswith('== M = 8 : pinned at '), lines[-1]
    # the numbered lines printed are exactly the chain listed in the pin line
    listed = [int(x) for x in lines[-1].split('; chain ')[1].split(',')]
    printed = [int(l.split('.', 1)[0]) for l in lines if l[:1].isdigit()]
    assert printed == listed
    assert int(lines[-1].split('pinned at ')[1].split()[0]) == printed[-1]


def test_route_inlines_edges():
    code, out = run(ROUTE, '10_44', 'M', TINY)
    assert code == 0, out
    lines = out.rstrip('\n').split('\n')
    assert lines[-1].startswith('== M = 4 : pinned at ')
    assert any('edge e767: crossing change   source 10_44 -> result 0_1' in l for l in lines)
    with open(os.path.join(TINY, 'edges.jsonl')) as f:
        edge = next(e for e in map(json.loads, f) if e['id'] == 'e767')
    compact = lambda o: json.dumps(o, separators=(',', ':'))
    pd_line = next(l for l in lines if 'pd        = ' in l)
    assert '*%s*' % compact(edge['pd'][edge['crossing']]) in pd_line          # the changed crossing is flagged
    assert pd_line.replace('*', '').replace(' ', '').endswith('pd=' + compact(edge['pd']))
    assert any(l.replace(' ', '').endswith('result_pd=' + compact(edge['result_pd'])) for l in lines)
    assert any('changed crossing: index %d, sign %+d' % (edge['crossing'], edge['sign']) in l for l in lines)
    assert any('source certificate (10_44): ' + compact(edge['source_certificate']) in l for l in lines)
    assert any('result certificate (0_1): ' + compact(edge['result_certificate']) in l for l in lines)
    # a certificate object is printed as JSON
    assert any('| ref {"construction":"T(2,3)"}' in l for l in lines)


def test_route_not_pinned_and_errors():
    code, out = run(ROUTE, '3_1#4_1', 'r_2', TINY)
    assert code == 1 and 'not pinned' in out
    code, out = run(ROUTE, 'no_such_knot', 'M', TINY)
    assert code == 2
    code, out = run(ROUTE, '3_1', 'sigma', TINY)
    assert code == 2


def test_route_twist_mutation_and_slopes(route):
    twist = {'id': 'e1', 'type': 'twist', 'source_node': 'A', 'result_node': 'B', 'pd': [[1, 2, 3, 4]],
             'result_pd': [[4, 3, 2, 1]], 'circle_edges': [3, 7], 'edge_directions': [1, -1], 'a': 1, 'b': 1,
             'handedness': -1, 'insertion': 'text', 'source_certificate': {'type': 's'},
             'result_certificate': {'type': 'r'}}
    text = '\n'.join(route.edge_lines(twist))
    for piece in ('edge e1: twist   source A -> result B', '[3,7]', '[1,-1]', 'a = 1, b = 1, handedness -1',
                  'pd        = [[1,2,3,4]]', 'result_pd = [[4,3,2,1]]', '{"type":"s"}', '{"type":"r"}'):
        assert piece in text, piece
    mut = dict(twist, type='mutation', circle_edges=[1, 4, 6, 9], rotation='y')
    text = '\n'.join(route.edge_lines(mut))
    assert '[1,4,6,9]' in text and 'rotation y' in text
    con = {'rule': 'S1', 'nodes': ['A', 'B'], 'par': {'sA': [5, 1], 'sB': [7, 2], 'a': 1, 'b': 2},
           'ref': {'cert': 'x'}}
    lines = route.ref_lines(con, {})
    assert lines[0] == 'ref {"cert":"x"}'
    assert '5/1 on A' in lines[1] and '7/2 on B' in lines[1]
    con = {'rule': 'F16', 'nodes': ['A'], 'par': {'p': 5, 'q': 1, 'g': 1}, 'ref': {'name': 'L(5,1)'}}
    assert route.ref_lines(con, {})[1] == 'slope: 5/1 on A'


# --------------------------------------------------------------------------------------
# (iii) the checker on a small export, intact and corrupted
# --------------------------------------------------------------------------------------
@pytest.fixture
def tiny(tmp_path):
    d = str(tmp_path / 'export')
    shutil.copytree(TINY, d)
    return d


def edit_jsonl(directory, name, fn):
    """Rewrite a JSONL file with fn(list of records) -> list of records (or None: edited in place)."""
    path = os.path.join(directory, name)
    with open(path) as f:
        recs = [json.loads(l) for l in f]
    out = fn(recs)
    with open(path, 'w') as f:
        for r in (recs if out is None else out):
            f.write(json.dumps(r, separators=(',', ':'), sort_keys=True) + '\n')


def test_tiny_export_is_accepted(tiny):
    code, out = run(CHECK, tiny)
    assert code == 0, out
    assert_only(out)
    s = summary(out)
    assert s['events checked'] == sum(1 for _ in open(os.path.join(tiny, 'events.jsonl')))
    assert s['chain files identical'] == len(os.listdir(os.path.join(tiny, 'chains'))) > 0
    assert 'applications: 102' in out                    # two applications emit two events each


def test_corrupt_digest(tiny):
    def f(recs):
        d = recs[40]['dg']
        recs[40]['dg'] = ('0' if d[0] != '0' else '1') + d[1:]
    edit_jsonl(tiny, 'events.jsonl', f)
    code, out = run(CHECK, tiny)
    assert code == 1 and 'RESULT: FAILED' in out
    assert_only(out, {'digest mismatches': 1})
    assert 'MISMATCH [digest] event 40:' in out


def test_corrupt_chain_file(tiny):
    path = os.path.join(tiny, 'chains', '10_44.txt')
    with open(path) as f:
        text = f.read()
    with open(path, 'w') as f:
        f.write(text.replace('r_2{>=8}', 'r_2{>=4}', 1))
    code, out = run(CHECK, tiny)
    assert code == 1
    assert_only(out, {'chain files different': 1})
    assert summary(out)['chain files identical'] == len(os.listdir(os.path.join(tiny, 'chains'))) - 1
    # the chain step can be skipped
    code, out = run(CHECK, tiny, '--no-chains')
    assert code == 0 and 'not compared' in out


def test_packed_export(tiny, tmp_path):
    """gzip parts and chain archives (FORMAT.md, section 1) are read like the plain files."""
    packed, plain = str(tmp_path / 'packed'), str(tmp_path / 'plain')
    code, out = run(PACK, 'pack', tiny, packed)
    assert code == 0, out
    assert not os.path.exists(os.path.join(packed, 'events.jsonl'))
    assert os.listdir(os.path.join(packed, 'chains')) == ['chains-000.tar.xz']
    code, out = run(CHECK, packed)
    assert code == 0, out
    assert_only(out)
    assert summary(out)['chain files identical'] == len(os.listdir(os.path.join(tiny, 'chains')))
    code, out2 = run(ROUTE, '10_44', 'M', packed)
    assert code == 0 and out2 == run(ROUTE, '10_44', 'M', tiny)[1]
    # unpacking gives the plain export back, byte for byte
    code, out = run(PACK, 'unpack', packed, plain)
    assert code == 0, out
    for d, _, files in os.walk(tiny):
        for fn in files:
            a = os.path.join(d, fn)
            with open(a, 'rb') as f, open(os.path.join(plain, os.path.relpath(a, tiny)), 'rb') as g:
                assert f.read() == g.read(), fn
    # a chain file that differs inside an archive is found; a file in two places is reported
    path = os.path.join(tiny, 'chains', '10_44.txt')
    with open(path) as f:
        text = f.read()
    with open(path, 'w') as f:
        f.write(text.replace('r_2{>=8}', 'r_2{>=4}', 1))
    bad = str(tmp_path / 'bad')
    assert run(PACK, 'pack', tiny, bad)[0] == 0
    code, out = run(CHECK, bad)
    assert code == 1
    assert_only(out, {'chain files different': 1})
    shutil.copy(os.path.join(TINY, 'chains', '4_1.txt'), os.path.join(packed, 'chains', '4_1.txt'))
    code, out = run(CHECK, packed)
    assert code == 1 and 'occurs twice' in out


def test_split_parts(tiny):
    """Continuation parts: events.1.jsonl (plain next to a gzip first part) and knots.1.csv."""
    import gzip
    path = os.path.join(tiny, 'events.jsonl')
    with open(path) as f:
        lines = f.readlines()
    os.remove(path)
    with gzip.open(path + '.gz', 'wt') as f:
        f.writelines(lines[:30])
    with open(os.path.join(tiny, 'events.1.jsonl'), 'w') as f:
        f.writelines(lines[30:])
    path = os.path.join(tiny, 'knots.csv')
    with open(path) as f:
        rows = f.readlines()
    with open(path, 'w') as f:
        f.writelines(rows[:4])
    with open(os.path.join(tiny, 'knots.1.csv'), 'w') as f:
        f.writelines(rows[:1] + rows[4:])
    code, out = run(CHECK, tiny)
    assert code == 0, out
    assert_only(out)
    assert summary(out)['events checked'] == len(lines)
    assert 'rows: %d' % (len(rows) - 1) in out


def test_missing_and_unexpected_chain_file(tiny):
    os.rename(os.path.join(tiny, 'chains', '4_1.txt'), os.path.join(tiny, 'chains', '4_2.txt'))
    code, out = run(CHECK, tiny)
    assert code == 1
    assert_only(out, {'chain files different': 2})


def test_corrupt_in(tiny):
    def f(recs):
        e = next(e for e in recs if len(e['in']) == 2)
        e['in'] = e['in'][:1]
    edit_jsonl(tiny, 'events.jsonl', f)
    code, out = run(CHECK, tiny)
    assert code == 1
    assert_only(out, {'`in` mismatches': 1})


def test_event_that_changes_nothing(tiny):
    # a second copy of an event: the constraint is applied again and does not change its target
    def f(recs):
        k = next(i for i, e in enumerate(recs) if e['rule'] == 'C8')
        dup = dict(recs[k], **{'in': [recs[k]['id']]})
        out = recs[:k + 1] + [dup] + recs[k + 1:]
        for i, e in enumerate(out):                      # renumber
            shift = lambda x: x + 1 if x > k else x
            e['in'] = [shift(x) for x in e['in']] if i != k + 1 else e['in']
            e['id'] = i
        return out
    edit_jsonl(tiny, 'events.jsonl', f)
    code, out = run(CHECK, tiny, '--no-chains')
    assert code == 1
    assert summary(out)['targets that do not change'] == 1


def test_missing_second_event_of_an_application(tiny):
    def f(recs):
        k = next(i for i in range(1, len(recs))
                 if recs[i]['c'] == recs[i - 1]['c'] and recs[i]['in'] == recs[i - 1]['in'])
        return recs[:k] + recs[k + 1:]
    edit_jsonl(tiny, 'events.jsonl', f)
    code, out = run(CHECK, tiny, '--no-chains')
    assert code == 1
    assert summary(out)['other event/constraint errors'] > 0


def test_corrupt_knots_jsonl(tiny):
    def f(recs):
        r = next(r for r in recs if r['node'] == '3_1')
        r['domains']['U']['u'][1] += 1                    # final domain
        r = next(r for r in recs if r['node'] == '4_1')
        r['pin_events']['M'] += 1
        r = next(r for r in recs if r['node'] == '7_7')
        del r['pins']['tau']
        del r['pin_events']['tau']
    edit_jsonl(tiny, 'knots.jsonl', f)
    code, out = run(CHECK, tiny)
    assert code == 1
    # the csv is compared with knots.jsonl, so it disagrees too (3_1: upsilon_hi; 7_7: tau_pin)
    assert_only(out, {'final-domain mismatches': 1, 'pin-event mismatches': 2, 'pin mismatches': 1,
                      'csv mismatches': None})


def test_corrupt_csv(tiny):
    import csv
    path = os.path.join(tiny, 'knots.csv')
    with open(path, newline='') as f:
        rows = list(csv.reader(f))
    row = next(r for r in rows if r[0] == '4_1')
    assert row[rows[0].index('r_2_hi')] == '8'
    row[rows[0].index('r_2_hi')] = '12'
    with open(path, 'w', newline='') as f:
        csv.writer(f).writerows(rows)
    code, out = run(CHECK, tiny)
    assert code == 1
    assert_only(out, {'csv mismatches': 1})
    assert "4_1: column r_2_hi is '12', knots.jsonl gives 8" in out


def test_unresolved_edge(tiny):
    edit_jsonl(tiny, 'edges.jsonl', lambda recs: [e for e in recs if e['id'] != 'e767'])
    code, out = run(CHECK, tiny)
    assert code == 1
    assert_only(out, {'unresolved edges': 1})


def test_constraint_without_operator(tiny):
    def f(recs):
        c = next(c for c in recs if c['rule'] == 'C8')
        c['rule'] = 'C99'
    edit_jsonl(tiny, 'constraints.jsonl', f)
    code, out = run(CHECK, tiny, '--no-chains')
    assert code == 1
    assert 'no operator for rule' in out
    assert summary(out)['other event/constraint errors'] > 0


def test_max_errors(tiny):
    def f(recs):
        for e in recs:
            e['dg'] = 'x' + e['dg'][1:]
    edit_jsonl(tiny, 'events.jsonl', f)
    code, out = run(CHECK, tiny, '--max-errors', '3')
    assert code == 1
    assert summary(out)['digest mismatches'] == sum(1 for _ in open(os.path.join(tiny, 'events.jsonl')))
    assert len(re.findall(r'^MISMATCH \[digest\] event', out, re.M)) == 3


def test_continuation_parts(tiny):
    # FORMAT.md: X.jsonl may be continued in X.1.jsonl, X.2.jsonl, ...
    for name, cut in (('events.jsonl', 50), ('constraints.jsonl', 80), ('knots.jsonl', 4)):
        path = os.path.join(tiny, name)
        with open(path) as f:
            lines = f.readlines()
        with open(path, 'w') as f:
            f.writelines(lines[:cut])
        with open(path[:-6] + '.1.jsonl', 'w') as f:
            f.writelines(lines[cut:cut + 20])
        with open(path[:-6] + '.2.jsonl', 'w') as f:
            f.writelines(lines[cut + 20:])
    code, out = run(CHECK, tiny)
    assert code == 0, out
    code, out = run(ROUTE, '10_44', 'M', tiny)
    assert code == 0 and out.rstrip('\n').split('\n')[-1].startswith('== M = 4 ')


# --------------------------------------------------------------------------------------
# units of the checker
# --------------------------------------------------------------------------------------
def test_torus_upsilon_checks_of_rule_F11(check):
    assert check.torus_upsilon(2, 3) == -1
    assert check.torus_upsilon(3, 4) == -2
    assert check.torus_upsilon(3, 5) == -3
    assert check.convention_tests() == []


def test_canonical_json_and_digest(check):
    import hashlib
    with open(os.path.join(TINY, 'knots.jsonl')) as f:
        for rec in map(json.loads, f):
            for kind, j in rec['domains'].items():
                d = check.from_json(kind, j)
                text = json.dumps(j, sort_keys=True, separators=(',', ':'))
                assert check.CANON[kind](d) == text
                assert check.digest(kind, d) == hashlib.sha1(text.encode()).hexdigest()[:12]


def test_intersect_is_the_set_intersection(check):
    # FORMAT.md 2.1: where an up-ray of one operand overlaps the down-ray of the other, the common
    # values are kept (ALL intersected with {>= -8} on 4Z is {>= -8})
    assert check.r_intersect(((), 0, -4), ((), -8, None), 4, 4) == ((), -8, None)
    assert check.r_intersect(((4,), 12, None), ((), 4, None), 4, 4) == ((4,), 12, None)
    assert check.r_intersect(((), 8, -8), ((), -4, None), 4, 4) == ((), 8, None) or \
        check.r_intersect(((), 8, -8), ((), -4, None), 4, 4) == ((), 8, None)
    # brute force on a window
    import itertools
    import random
    rnd = random.Random(4)
    for _ in range(300):
        def rs():
            vals = [rnd.randint(-6, 6) for _ in range(rnd.randint(0, 4))]
            up = rnd.randint(-6, 8) if rnd.random() < 0.5 else None
            dn = rnd.randint(-8, 6) if rnd.random() < 0.5 else None
            return check.r_make(vals, up, dn, 1)
        a, b = rs(), rs()
        c = check.r_intersect(a, b, 1, 1)
        for x in range(-12, 13):
            assert check.r_has(c, x, 1) == (check.r_has(a, x, 1) and check.r_has(b, x, 1)), (a, b, c, x)


def test_checker_does_not_import_the_solver():
    with open(CHECK) as f:
        src = f.read()
    assert not re.search(r'^\s*(import|from)\s+mrcalc', src, re.M)
    with open(ROUTE) as f:
        assert not re.search(r'^\s*(import|from)\s+mrcalc', f.read(), re.M)


# --------------------------------------------------------------------------------------
# operators of the checker against the operators of the solver, on random domains
# --------------------------------------------------------------------------------------
def _random_cases(rnd, D):
    """Yield (constraint, {key: solver domain}) forever."""
    ri = rnd.randint

    def rset(step, lo=-3, hi=12, rays=True, down=True):
        vals = [step * ri(lo, hi) for _ in range(ri(0, 5))]
        up = step * ri(lo, hi) if rays and rnd.random() < 0.5 else None
        dn = step * ri(lo - 4, lo + 2) if rays and down and rnd.random() < 0.12 else None
        r = D.RSet(vals, up, dn, step)
        return D.RSet([step * ri(0, 5)], None, None, step) if r.is_empty() else r

    def rand_F(step):
        t = rnd.random()
        if t < 0.12:
            return D.Dom2.top(1)
        if t < 0.3:
            lo = step * ri(-5, 5) if rnd.random() < 0.4 else None
            hi = None if lo is not None else (step * ri(-5, 5) if rnd.random() < 0.5 else None)
            return D.Dom2(step, box=(lo, hi, rnd.choice([None, None, None, 0, 4, 8]), rnd.random() < 0.7))
        mode = rnd.random()
        return D.Dom2(step, items={step * m: rset(step, rays=mode < 0.7, down=mode < 0.15)
                                   for m in {ri(-6, 6) for _ in range(ri(1, 7))}})

    def rand_C():
        t = rnd.random()
        if t < 0.1:
            return D.DomC.top()
        if t < 0.3:
            e = [None] * 4
            for i in rnd.sample(range(4), ri(0, 2)):
                e[i] = ri(-5, 5)
            return D.DomC(box=(e[0], e[1], e[2], e[3], rnd.random() < 0.5, rnd.choice([None, 0, 0, 3])))
        mode = rnd.random()
        keys = {(t_, 2 * t_ + ri(-1, 1)) for t_ in [ri(-4, 4) for _ in range(ri(1, 8))]}
        return D.DomC(items={k: rset(1, lo=0, hi=14, rays=mode < 0.7, down=mode < 0.1) for k in keys})

    def rand_U():
        lo = ri(-6, 6) if rnd.random() < 0.8 else None
        hi = (lo if lo is not None else 0) + ri(0, 6) if rnd.random() < 0.8 else None
        return D.DomU(lo, hi)

    def slope():
        return [ri(-30, 40), rnd.choice([1, 1, 1, 2, 3, 4])]

    torus = [(2, 3), (2, 5), (3, 4), (3, 5), (2, 7), (3, 7), (4, 5), (5, 6), (5, 3), (7, 2)]
    surgery = lambda: {'sA': slope(), 'sB': slope(), 'a': rnd.choice([1, 1, 2, 3]), 'b': rnd.choice([1, 1, 2])}
    twist = lambda: {'a': ri(0, 3), 'b': ri(0, 3), 'h': rnd.choice([1, -1])}
    AB, ABC = ['A', 'B'], ['A', 'B', 'C']
    makers = [
        lambda: ('F1', 'F', ['A'], {}), lambda: ('0_1', 'F', ['A'], {}), lambda: ('0_1', 'C', ['A'], {}),
        lambda: ('F5', 'F', ['A'], {'why': 'slice'}),
        lambda: ('F8', 'F', ['A'], {'c': rnd.choice([None, 1, 2, 3]), 'u': rnd.choice([None, 1, 2, 4])}),
        lambda: ('F11', 'F', ['A'], dict(zip('pq', rnd.choice(torus)))),
        lambda: ('F12', 'F', ['A'], {'n': ri(-3, 3)}),
        lambda: ('F13', 'F', ['A'], {'m': ri(0, 4), 'tau': ri(-2, 2)}),
        lambda: ('F14', 'F', ['A'], {'p': ri(1, 5), 'q': ri(1, 5)}),
        lambda: ('F15', 'F', ['A'], {'fibered': rnd.choice([True, False, None]), 'g': rnd.choice([None, 1, 2, 3, 4]),
                                     'tau': rnd.choice([None, -2, -1, 0, 1, 2, 3])}),
        lambda: ('F16', 'F', ['A'], {'p': ri(1, 40), 'q': ri(1, 4), 'g': rnd.choice([None, 1, 2, 3, 5])}),
        lambda: ('F10', 'F', ['A'], dict(zip('pq', slope()))), lambda: ('F10', 'C', ['A'], dict(zip('pq', slope()))),
        lambda: ('C1', 'C', ['A'], {}), lambda: ('C4', 'C', ['A'], {}),
        lambda: ('C5', 'C', ['A'], rnd.choice([{'why': 'amphichiral'}, {'g4': ri(0, 4)}])),
        lambda: ('C8', 'C', ['A'], {'tau': ri(-4, 4)}), lambda: ('C9', 'C', ['A'], {'n': ri(1, 6), 'w': ri(-8, 8)}),
        lambda: ('C10', 'C', ['A'], {'named': ri(0, 6)} if rnd.random() < 0.2 else
                 {k: True for k in ('ge3', 'a', 'b') if rnd.random() < 0.6}),
        lambda: ('C11', 'C', ['A'], {'g': ri(0, 4)}), lambda: ('C12', 'C', ['A'], {'m': ri(0, 6), 'tau': ri(-3, 3)}),
        lambda: ('C13', 'C', ['A'], rnd.choice([{'kind': 'n3m3', 'n': 3}, {'kind': 'odd32', 'n': ri(-2, 3)}])),
        lambda: ('C14', 'C', ['A'], {'n': ri(-2, 3), 'norm': 2 * ri(0, 6) + 1}), lambda: ('C15', 'C', ['A'], {}),
        lambda: ('U4a', 'U', ['A'], rnd.choice([{'why': 'slice'}, {'why': 'unknot'}, {'g4': ri(0, 5)}])),
        lambda: ('U2a', 'U', ['A'], {'tau': ri(-4, 4)}), lambda: ('U3', 'U', ['A'], {}),
        lambda: ('U1', 'U', ['A'], {'value': ri(-4, 4)}),
        lambda: ('U7', 'U', ['A'], dict(zip('pq', rnd.choice(torus)))),
        lambda: ('F7', 'F', AB, {}), lambda: ('C7', 'C', AB, {}), lambda: ('U5', 'U', AB, {}),
        lambda: ('F9', 'F', AB, twist()), lambda: ('U6', 'U', AB, twist()),
        lambda: ('F7', 'F', ['A'], {'coef': rnd.choice([-2, -2, 2, 1, -1, 3])}),
        lambda: ('C7', 'C', ['A'], {'coef': rnd.choice([-2, -2, 2, 1, -1, 3])}),
        lambda: ('U5', 'U', ['A'], {'coef': rnd.choice([-2, -2, 2, 1, -1, 3])}),
        lambda: ('F9', 'F', ['A'], dict(twist(), coef=rnd.choice([-2, 2]))),
        lambda: ('U6', 'U', ['A'], dict(twist(), coef=rnd.choice([-2, 2]))),
        lambda: ('F3', 'F', AB, {}), lambda: ('C3', 'C', AB, {}), lambda: ('U4b', 'U', AB, {'kind': 'mirror'}),
        lambda: ('F6', 'F', AB, {}),
        lambda: ('F4', 'F', ABC, {'mult': [1, 1]}), lambda: ('F4', 'F', AB, {'mult': [2]}),
        lambda: ('C6', 'C', ABC, {'mult': [1, 1]}), lambda: ('C6', 'C', AB, {'mult': [2]}),
        lambda: ('U4b', 'U', ABC, {'kind': 'sum', 'mult': [1, 1]}),
        lambda: ('U4b', 'U', AB, {'kind': 'sum', 'mult': [2]}),
        lambda: ('S1', 'F', AB, surgery()), lambda: ('S1', 'C', AB, surgery()), lambda: ('S3', 'F', AB, surgery()),
        lambda: ('S4', 'C', AB, surgery()), lambda: ('S1', 'F', ['A'], surgery()),
        lambda: ('S3', 'C', ['A'], surgery()),
    ]

    def x_par():
        par = {k: True for k in ('x1', 'x2', 'x4', 'x5', 'x5m') if rnd.random() < 0.6}
        if rnd.random() < 0.6:
            par['x3_g'] = ri(1, 5)
        t = rnd.random()
        if t < 0.4:
            par['slopes'] = rnd.choice(['G', 'T'])
        elif t < 0.8:
            par['slopes'] = {'base': rnd.choice(['G', 'T']), 'extra': [slope() for _ in range(ri(0, 3))]}
        return par
    makers += [lambda: ('X', 'X', ['A'], x_par())] * 3
    while True:
        rule, dom, nodes, par = rnd.choice(makers)()
        con = {'id': 'c0', 'rule': rule, 'dom': dom, 'nodes': nodes}
        if par:
            con['par'] = par
        step = rnd.choice([4, 4, 4, 1])                  # usually one lattice per case
        keys = [('A', 'F'), ('A', 'C')] if rule == 'X' else [(n, dom) for n in nodes]
        doms = {k: rand_F(step if rnd.random() < 0.95 else rnd.choice([1, 4])) if k[1] == 'F'
                else rand_C() if k[1] == 'C' else rand_U() for k in keys}
        yield con, doms


def test_operators_agree_with_the_solver(check):
    sys.path.insert(0, ROOT)
    S = pytest.importorskip('mrcalc.solver')
    D = pytest.importorskip('mrcalc.domains')
    with open(os.path.join(TINY, 'parameters.json')) as f:
        slopes = {k: [tuple(x) for x in v] for k, v in json.load(f)['slope_sets'].items()}
    old = dict(S.SLOPES)
    S.SLOPES.clear()
    S.SLOPES.update(slopes)
    check.SLOPE_SETS.clear()
    check.SLOPE_SETS.update(slopes)
    canon = lambda kind, d: json.loads(check.CANON[kind](d))
    rules_changed = set()
    try:
        cases = _random_cases(random.Random(20261111), D)
        done = 0
        while done < 30000:
            con_rec, ref = next(cases)
            if any(d.is_empty() for d in ref.values()):
                continue
            if con_rec['rule'] in ('F3', 'F6') and len({d.step for d in ref.values()}) > 1:
                continue                                 # not defined in FORMAT.md (FORMAT_NOTES.md, note 16)
            done += 1
            con = check.Con(con_rec)
            mine = [check.from_json(k[1], ref[k].to_json()) for k in con.keys]
            for k, m in zip(con.keys, mine):             # encoding, digest, statement text, pins
                assert canon(k[1], m) == ref[k].to_json()
                assert check.digest(k[1], m) == ref[k].digest()
                assert check.TEXT[k[1]](m, None) == ref[k].text()
                pins = {name: ref[k].pin(co) for name, co in S.PIN_COORDS[k[1]] if ref[k].pin(co) is not None}
                assert check.pins_of(k[1], m) == pins
            try:
                ref_out = S.apply(con_rec, lambda n, d: ref[(n, d)])
            except Exception:
                with pytest.raises(Exception):
                    check.apply_constraint(con, mine)
                continue
            my_out = check.apply_constraint(con, mine)
            # the events the solver would emit: changed outputs in order, up to the first empty one
            ref_ev = []
            for node, dom, new in ref_out:
                if new is ref[(node, dom)] or new == ref[(node, dom)]:
                    continue
                ref_ev.append((node, dom, new.to_json()))
                if new.is_empty():
                    break
            my_ev = []
            for k, o, new in zip(con.keys, mine, my_out):
                if new == o:
                    continue
                my_ev.append((k[0], k[1], canon(k[1], new)))
                if check.is_empty(k[1], new):
                    break
            assert my_ev == ref_ev, (con_rec, {'%s.%s' % k: d.to_json() for k, d in ref.items()})
            if ref_ev:
                rules_changed.add((con_rec['rule'], con_rec['dom'], len(con_rec['nodes'])))
    finally:
        S.SLOPES.clear()
        S.SLOPES.update(old)
    # the operators that the current export does not exercise did narrow something
    for key in (('S1', 'F', 2), ('S1', 'C', 2), ('S3', 'F', 2), ('S4', 'C', 2), ('S1', 'F', 1), ('S3', 'C', 1),
                ('F9', 'F', 2), ('U6', 'U', 2), ('F6', 'F', 2), ('F10', 'F', 1), ('F10', 'C', 1), ('F16', 'F', 1),
                ('U1', 'U', 1), ('U3', 'U', 1), ('X', 'X', 1)):
        assert key in rules_changed, key
