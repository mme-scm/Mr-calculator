"""KnotInfo table (database_knotinfo package) restricted to the fields of section 2.5."""
import json
import os

from .config import DATA

TABLE_FILE = os.path.join(DATA, 'knotinfo.jsonl')


def _interval(s):
    s = (s or '').strip()
    if not s:
        return None
    if s.startswith('['):
        a, b = json.loads(s)
        return [int(a), int(b)]
    return [int(s), int(s)]


def _int(s):
    s = (s or '').strip()
    return int(s) if s not in ('', 'unknown') else None


def _braids(s):
    """KnotInfo lists one braid word, or two (minimal index and minimal length)."""
    s = (s or '').strip()
    if not s:
        return []
    w = json.loads(s)
    if w and isinstance(w[0], list):
        return [[int(g) for g in x] for x in w]
    return [[int(g) for g in w]]


def _yn(s):
    s = (s or '').strip()
    return True if s == 'Y' else False if s == 'N' else None


def build_table():
    from database_knotinfo import link_list
    import importlib.metadata as md
    rows = link_list()
    out = []
    for k in rows[1:]:
        name = k['name']
        cn = int(k['crossing_number'])
        if cn > 13:
            continue
        if name == '0_1':
            continue
        sym = (k.get('symmetry_type') or '').strip()
        rec = {
            'name': name,
            'crossing_number': cn,
            'pd': json.loads(k['pd_notation']),
            'braids': _braids(k.get('braid_notation')),
            'signature': _int(k.get('signature')),
            'tau': _int(k.get('ozsvath_szabo_tau_invariant')),
            'genus': _int(k.get('three_genus')),
            'g4': _interval(k.get('smooth_four_genus')),
            'u': _interval(k.get('unknotting_number')),
            'c4': _interval(k.get('fd_clasp_number')),
            'alternating': _yn(k.get('alternating')),
            'quasipositive': _yn(k.get('quasipositive')),
            'symmetry_type': sym,
            'amphichiral': 'amphicheiral' in sym,
            'fibered': _yn(k.get('fibered')),
        }
        rec['slice'] = rec['g4'] == [0, 0]
        out.append(rec)
    os.makedirs(DATA, exist_ok=True)
    with open(TABLE_FILE, 'w') as f:
        for r in out:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    with open(os.path.join(DATA, 'knotinfo_version.json'), 'w') as f:
        json.dump({'database_knotinfo': md.version('database_knotinfo'), 'knots': len(out)}, f)
    return out


_cache = None


def table():
    global _cache
    if _cache is None:
        if not os.path.exists(TABLE_FILE):
            build_table()
        with open(TABLE_FILE) as f:
            _cache = [json.loads(l) for l in f]
    return _cache


def by_name():
    return {r['name']: r for r in table()}
