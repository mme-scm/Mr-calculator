"""Node names.

  0_1                      the unknot
  8_19, 8_19*              table knot (KnotInfo chirality) and its mirror
  K14n123, K14n123*        census knot (census chirality) and its mirror
  H:<sig>, H:<sig>*        unidentified hyperbolic knot named by the smaller of the two
                           orientation-sensitive isometry signatures of the knot and its mirror
  U:<hash>                 unidentified diagram (never merged)
  T(p,q), T(p,q)*          positive torus knot, p < q, and its mirror
  A#B#C                    connected sum, summands sorted canonically
  C(r,s;K)                 cable (section 3 convention)
"""
import re

from . import knotinfo

_AMPHI_EXTRA = set()      # amphichiral census / H bases registered at run time
_table_index = None


def _tab():
    global _table_index
    if _table_index is None:
        _table_index = {r['name']: (i, r) for i, r in enumerate(knotinfo.table())}
    return _table_index


def register_amphichiral(base):
    _AMPHI_EXTRA.add(base)


def is_table(name):
    return name.rstrip('*') in _tab()


def kind(name):
    if name == '0_1':
        return 'unknot'
    if '#' in name:
        return 'composite'
    if name.startswith('C('):
        return 'cable'
    if name.startswith('T('):
        return 'torus'
    if name.startswith('H:'):
        return 'hyp'
    if name.startswith('U:'):
        return 'unidentified'
    if name.startswith('K1') and name.rstrip('*') not in _tab():
        return 'census'
    if name.rstrip('*') in _tab():
        return 'table'
    return 'construction'


_CABLE = re.compile(r'^C\((-?\d+),(\d+);(.*)\)$')


def parse_cable(name):
    m = _CABLE.match(name)
    return int(m.group(1)), int(m.group(2)), m.group(3)


def cable_name(r, s, companion):
    return 'C(%d,%d;%s)' % (r, s, companion)


_TORUS = re.compile(r'^T\((\d+),(\d+)\)(\*?)$')


def parse_torus(name):
    m = _TORUS.match(name)
    return int(m.group(1)), int(m.group(2)), bool(m.group(3))


def torus_name(p, q, mirror=False):
    p, q = min(p, q), max(p, q)
    return 'T(%d,%d)%s' % (p, q, '*' if mirror else '')


def is_amphichiral(name):
    return mirror_name(name) == name


def mirror_name(name):
    k = kind(name)
    if k == 'unknot':
        return name
    if k == 'composite':
        return composite_name([mirror_name(x) for x in name.split('#')])
    if k == 'cable':
        r, s, comp = parse_cable(name)
        return cable_name(-r, s, mirror_name(comp))
    base = name.rstrip('*')
    if k == 'table' and _tab()[base][1]['amphichiral']:
        return base
    if base in _AMPHI_EXTRA:
        return base
    return base if name.endswith('*') else base + '*'


def with_mirror(name, mir):
    return mirror_name(name) if mir else name


def _summand_key(x):
    base = x.rstrip('*')
    t = _tab().get(base)
    if t is None:
        return (99, 0, base, x.endswith('*'))
    return (t[1]['crossing_number'], t[0], '', x.endswith('*'))


def composite_name(summands):
    flat = []
    for s in summands:
        flat.extend(s.split('#'))
    flat = [s for s in flat if s != '0_1']
    if not flat:
        return '0_1'
    return '#'.join(sorted(flat, key=_summand_key))


def crossing_number(name):
    """Tier crossing number: table knot's crossing number, composite's sum, else None."""
    k = kind(name)
    if k == 'unknot':
        return 0
    if k == 'table':
        return _tab()[name.rstrip('*')][1]['crossing_number']
    if k == 'composite':
        cs = [crossing_number(x) for x in name.split('#')]
        return None if any(c is None for c in cs) else sum(cs)
    if k == 'census':
        return int(name[1:3])
    return None


def file_name(name):
    return name.replace('*', 'm').replace('#', '+').replace('/', '_').replace(':', '_')
