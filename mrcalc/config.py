"""Paths and scope parameters (the values actually used are written to the export)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# MRCALC_DATA: read the inputs from another directory (a frozen copy of data/, used to compare two versions
# of the code on the same input while the passes go on).
DATA = os.environ.get('MRCALC_DATA') or os.path.join(ROOT, 'data')
EXPORT = os.path.join(ROOT, 'export')

# Census reference signatures.  In the repository they are kept in parts below 50 MB
# (data/ref_census/*.jsonl); a staged pass (MRCALC_STAGE) appends to one growing file.
REF_CENSUS_DIR = os.path.join(DATA, 'ref_census')
REF_CENSUS = os.path.join(os.environ['MRCALC_STAGE'], 'ref_census.jsonl') if os.environ.get('MRCALC_STAGE') \
    else os.path.join(REF_CENSUS_DIR, 'zz-new.jsonl')


def census_ref_files(staged=True):
    """Files holding the census reference records, in reading order."""
    if staged and os.environ.get('MRCALC_STAGE'):
        return [REF_CENSUS] if os.path.exists(REF_CENSUS) else []
    if not os.path.isdir(REF_CENSUS_DIR):
        return []
    return [os.path.join(REF_CENSUS_DIR, f) for f in sorted(os.listdir(REF_CENSUS_DIR)) if f.endswith('.jsonl')]


def iter_census_refs(staged=True):
    for path in census_ref_files(staged):
        with open(path) as f:
            for line in f:
                if line.endswith('\n') and line.strip():
                    yield json.loads(line)

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

# Groups of passes that the ablation also withholds as data: one extra ablation run per group that has
# records, solved with all rules but without the records of these passes (scripts/solve.py).
# stage6c: twists with |a - b| > 2 (k = 3, 4, 5 on diagrams with at most 11 crossings, k = 6 with at most 10).
# MRCALC_PASS_ABLATIONS="name=pass+pass,name=pass" replaces the table (tests).
PASS_ABLATIONS = {'stage6c': ['tw3x', 'tw4x', 'tw5x', 'tw6x']}
if os.environ.get('MRCALC_PASS_ABLATIONS'):
    PASS_ABLATIONS = {kv.split('=')[0]: kv.split('=')[1].split('+')
                      for kv in os.environ['MRCALC_PASS_ABLATIONS'].split(',')}

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


# Calculator inputs of peripheral nodes: same storage scheme as the census references.
HFK_PERIPHERAL_DIR = os.path.join(DATA, 'hfk_peripheral')
HFK_PERIPHERAL = os.path.join(os.environ['MRCALC_STAGE'], 'hfk_peripheral.jsonl') if os.environ.get('MRCALC_STAGE') \
    else os.path.join(HFK_PERIPHERAL_DIR, 'zz-new.jsonl')


def iter_hfk_peripheral(staged=True):
    if staged and os.environ.get('MRCALC_STAGE'):
        files = [HFK_PERIPHERAL] if os.path.exists(HFK_PERIPHERAL) else []
    elif os.path.isdir(HFK_PERIPHERAL_DIR):
        files = [os.path.join(HFK_PERIPHERAL_DIR, f) for f in sorted(os.listdir(HFK_PERIPHERAL_DIR))
                 if f.endswith('.jsonl')]
    else:
        files = []
    for path in files:
        with open(path) as f:
            for line in f:
                if line.endswith('\n') and line.strip():
                    yield json.loads(line)
