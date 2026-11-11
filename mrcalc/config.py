"""Paths and scope parameters (the values actually used are written to the export)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
EXPORT = os.path.join(ROOT, 'export')

# Scope parameters of section 4 (spec values) -------------------------------------------
SPEC = {
    'P_cab': 15,
    'k_max': {'<=10': 6, '11': 5, '12-20': 4, '>20': 0},
    'max_imbalance': 2,
    'slope_p': 30, 'slope_q': 4, 'torus_integer_p': 60,
    'recognition_time_limit_s': 60,
    'rediagrams': 3,
    'max_cable_companion_crossings': 8,
    'torus_pq_max': 60,
    'family_max_crossings': 15,
}

_PARAM_FILE = os.path.join(DATA, 'parameters.json')


def load_params():
    """Scope parameters actually used (data/parameters.json overrides the spec values)."""
    p = json.loads(json.dumps(SPEC))
    if os.path.exists(_PARAM_FILE):
        with open(_PARAM_FILE) as f:
            p.update(json.load(f))
    return p


def save_params(p):
    with open(_PARAM_FILE, 'w') as f:
        json.dump(p, f, indent=1, sort_keys=True)


def k_max_for(crossings, params):
    km = params['k_max']
    if crossings <= 10:
        return km['<=10']
    if crossings == 11:
        return km['11']
    if crossings <= 20:
        return km['12-20']
    return km['>20']
