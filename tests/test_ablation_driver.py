"""The ablation driver of scripts/solve.py: runs as processes of their own, several at a time."""
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _solve_module():
    spec = importlib.util.spec_from_file_location('solve_script', os.path.join(ROOT, 'scripts', 'solve.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_ablation_driver_runs_in_parallel_and_keeps_order(tmp_path, monkeypatch):
    S = _solve_module()
    names = ['a', 'b', 'c', 'd', 'e']
    monkeypatch.setattr(S, 'ablation_runs', lambda: [(n, ['R' + n]) for n in names])
    monkeypatch.setattr(S, 'pass_ablation_runs', lambda: [('p', ['x'])])
    real = subprocess.Popen
    started = []

    def fake(cmd, **kw):
        name = [a for a in cmd if a.startswith('ablate-run=')][0].split('=')[1]
        started.append((name, time.time()))
        if name == 'c':                              # a run that dies
            code = 'import sys; sys.exit(7)'
        else:
            res = {'withheld': name, 'pins': {i: 1 for i in S.INVARIANTS}, 'lost': {i: 0 for i in S.INVARIANTS},
                   'violations': 0}
            code = 'import time, json; time.sleep(%s); print("noise"); print(%r)' % (
                2 if name == 'a' else 0.2, json.dumps(res))
        return real([sys.executable, '-c', code], **kw)

    monkeypatch.setattr(subprocess, 'Popen', fake)
    out = str(tmp_path)
    open(os.path.join(out, S.ABLATION_BASE), 'w').close()
    rc = S.ablation_driver(out, True, only=None, procs=2)
    assert rc == 3                                    # one run died
    res = json.load(open(os.path.join(out, 'ablation.json')))
    assert [r['withheld'] for r in res] == names + ['p']          # the order of the run table, not of completion
    assert 'error' in res[2] and all('error' not in r for i, r in enumerate(res) if i != 2)
    assert not os.path.exists(os.path.join(out, S.ABLATION_BASE))
    # 'b' started while the slow run 'a' was still going (two at a time)
    t = dict(started)
    assert t['b'] - t['a'] < 1.5 and len(started) == 6
    # `only` restricts the runs
    open(os.path.join(out, S.ABLATION_BASE), 'w').close()
    assert S.ablation_driver(out, True, only=['b', 'p'], procs=1) == 0
    assert [r['withheld'] for r in json.load(open(os.path.join(out, 'ablation.json')))] == ['b', 'p']
