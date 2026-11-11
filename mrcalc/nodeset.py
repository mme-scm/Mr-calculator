"""Core node set of section 4 and the family constructions of section 6."""
from itertools import combinations_with_replacement
from math import gcd

from . import knotinfo, names, pd as P


def diagram(name):
    """Construction / reference diagram of a node name (None if there is none)."""
    k = names.kind(name)
    if k == 'table':
        base = name.rstrip('*')
        d = knotinfo.by_name()[base]['pd']
        return P.mirror(d) if name.endswith('*') else [list(c) for c in d]
    if k == 'composite':
        parts = name.split('#')
        d = diagram(parts[0])
        for x in parts[1:]:
            d = P.connected_sum(d, diagram(x))
        return d
    if k == 'torus':
        p, q, mir = names.parse_torus(name)
        d = P.torus_knot(p, q)
        return P.mirror(d) if mir else d
    if k == 'cable':
        r, s, comp = names.parse_cable(name)
        return P.cable(diagram(comp), r, s)
    return None


def chiral_versions(rec):
    return [rec['name']] if rec['amphichiral'] else [rec['name'], rec['name'] + '*']


def torus_params(pq_max=60):
    out = []
    for p in range(2, pq_max):
        for q in range(p + 1, pq_max):
            if p * q <= pq_max and gcd(p, q) == 1:
                out.append((p, q))
    return out


def torus_nodes(pq_max=60):
    """Positive torus knots (mirrors are implied)."""
    return [(names.torus_name(p, q), P.torus_knot(p, q)) for p, q in torus_params(pq_max)]


def composite_names(max_sum=13, triple_max=5):
    T = knotinfo.table()
    vers = []
    for r in T:
        if r['crossing_number'] <= max_sum - 3:
            for v in chiral_versions(r):
                vers.append((r['crossing_number'], v))
    out = set()
    for (c1, a), (c2, b) in combinations_with_replacement(vers, 2):
        if c1 + c2 <= max_sum:
            out.add(names.composite_name([a, b]))
    small = [v for c, v in vers if c <= triple_max]
    for tr in combinations_with_replacement(small, 3):
        out.add(names.composite_name(list(tr)))
    return sorted(out, key=lambda n: (names.crossing_number(n), n))


def composite_nodes(max_sum=13, triple_max=5):
    return [(n, diagram(n)) for n in composite_names(max_sum, triple_max)]


def cable_names(p_cab=15, max_companion=8, strands=(2, 3)):
    out = []
    for r in knotinfo.table():
        if r['crossing_number'] > max_companion:
            continue
        for v in chiral_versions(r):
            for s in strands:
                for rr in range(-p_cab, p_cab + 1):
                    if gcd(abs(rr), s) == 1:
                        out.append(names.cable_name(rr, s, v))
    return out


# ----------------------------------------------------------------------
# family constructions (construction diagrams with at most max_cr crossings)
# ----------------------------------------------------------------------
def twist_knot(m):
    """Twist knot with m half-twists: numerator closure of the rational tangle (2m+1)/2."""
    import snappy  # noqa: F401
    import spherogram
    L = spherogram.RationalTangle(2 * m + 1, 2).numerator_closure()
    return P.normalise(L.PD_code(min_strand_index=1))


def _necklaces(seq_list):
    """Representatives of sequences up to cyclic rotation and reversal."""
    seen = set()
    out = []
    for s in seq_list:
        k = len(s)
        forms = []
        for t in (s, s[::-1]):
            for i in range(k):
                forms.append(tuple(t[i:] + t[:i]))
        key = min(forms)
        if key not in seen:
            seen.add(key)
            out.append(tuple(s))
    return out


def odd_pretzel_params(max_cr=15):
    """C14: P(2a_1+1,...,2a_{2n+1}+1), n >= 1, a_i >= 0, at most n+1 nonzero."""
    out = []

    def comps(k, total_extra):
        # sequences of k non-negative ints with sum <= total_extra
        if k == 0:
            yield ()
            return
        for a in range(total_extra + 1):
            for rest in comps(k - 1, total_extra - a):
                yield (a,) + rest

    for n in range(1, (max_cr - 1) // 2 + 1):
        k = 2 * n + 1
        if k > max_cr:
            break
        extra = (max_cr - k) // 2
        seqs = [tuple(2 * a + 1 for a in c) for c in comps(k, extra)
                if sum(1 for a in c if a > 0) <= n + 1]
        for s in _necklaces(seqs):
            out.append((n, s))
    return out


def family_constructions(max_cr=15, pq_max=60):
    """List of dicts {family, construction, params, pd} (diagrams in the stated convention;
    chirality conditions are checked later on the diagram)."""
    out = []
    for p, q in torus_params(pq_max):
        out.append({'family': 'torus', 'construction': names.torus_name(p, q), 'params': {'p': p, 'q': q},
                    'pd': P.torus_knot(p, q)})
    for m in range(1, max_cr - 1):
        out.append({'family': 'twist', 'construction': 'Tw(%d)' % m, 'params': {'m': m}, 'pd': twist_knot(m)})
    for p in range(3, max_cr, 2):
        for q in range(p, max_cr, 2):
            if 2 + p + q <= max_cr:
                out.append({'family': 'pretzel_m2pq', 'construction': 'P(-2,%d,%d)' % (p, q),
                            'params': {'p': p, 'q': q}, 'pd': P.pretzel([-2, p, q])})
    for n in range(-(max_cr - 6), max_cr - 6 + 1):
        out.append({'family': 'pretzel_n3m3', 'construction': 'P(%d,3,-3)' % n, 'params': {'n': n},
                    'pd': P.pretzel([n, 3, -3])})
    for n in range(1, 50):
        if 2 * n - 1 + 5 > max_cr:
            break
        out.append({'family': 'pretzel_odd32', 'construction': 'P(%d,3,2)' % (2 * n - 1), 'params': {'n': n},
                    'pd': P.pretzel([2 * n - 1, 3, 2])})
    for n, s in odd_pretzel_params(max_cr):
        out.append({'family': 'pretzel_odd', 'construction': 'P(%s)' % ','.join(map(str, s)),
                    'params': {'n': n, 'cols': list(s)}, 'pd': P.pretzel(list(s))})
    return out
