"""The cache of unverified signatures is a set of files (none above 50 MB): scripts/find_coincidences.py."""
import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _script():
    spec = importlib.util.spec_from_file_location('find_coincidences',
                                                  os.path.join(ROOT, 'scripts', 'find_coincidences.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_cache_parts(tmp_path):
    fc = _script()
    p = str(tmp_path / 'filling_usig.jsonl')
    assert fc.cache_parts(p) == [p]                      # nothing exists yet: the first file
    p1, p2 = str(tmp_path / 'filling_usig.1.jsonl'), str(tmp_path / 'filling_usig.2.jsonl')
    assert fc.next_part(p) == p1 and fc.next_part(p1) == p2
    for q in (p, p1):
        open(q, 'w').close()
    assert fc.cache_parts(p) == [p, p1]
    live = str(tmp_path / 'filling_usig.live.jsonl')     # a name with a dot that is not a part number
    assert fc.cache_parts(live) == [live]
    assert fc.next_part(live) == str(tmp_path / 'filling_usig.live.1.jsonl')


def _echo(keys):
    return [{'node': n, 'p': p, 'q': q, 'h': 'x' * 16, 'hard': True} for n, p, q in keys]


def test_run_pool_rolls_over(tmp_path, monkeypatch):
    fc = _script()
    monkeypatch.setattr(fc, 'CACHE_PART', 200)
    p = str(tmp_path / 'c.jsonl')
    store = {}
    tasks = [[('k%d' % i, i, 1)] for i in range(40)]
    n, complete = fc.run_pool(_echo, tasks, p, store, 1, 0, 0.0, 'test')
    assert (n, complete) == (40, True) and len(store) == 40
    parts = fc.cache_parts(p)
    assert len(parts) > 2
    lines = [line for q in parts for line in open(q)]
    assert len(lines) == 40                              # every result in exactly one file
    assert all(os.path.getsize(q) < 400 for q in parts)
