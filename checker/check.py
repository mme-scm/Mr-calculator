#!/usr/bin/env python3
"""Independent checker of an export directory (format: export/FORMAT.md).

usage: check.py [export_dir] [--max-errors N] [--no-chains] [--strict]

The program reads ONLY files below the export directory and uses only the Python standard
library.  It does not import the solver package: the domains, the operators and the replay
are re-implemented here from FORMAT.md.

What is checked
  a. constraints.jsonl, events.jsonl, knots.jsonl (with continuation parts; each part plain or gzip,
     suffix .gz) and parameters.json load;
  b. replay of all events from TOP domains: every event is produced by applying its constraint to
     the current domains, its target changes, the digest of the new target equals `dg`, and `in`
     equals the latest earlier events of the domains read;
  c. final domains, pins, pin events (and last events, chain file names) of knots.jsonl;
  d. every chains/<node>.txt (a file, or a member of an archive chains/*.tar.xz) is rebuilt from the
     replay and compared byte for byte;
  e. knots.csv agrees with knots.jsonl (node, <inv>_pin, <inv>_lo, <inv>_hi);
  f. every edge id used as `ref` by the constraint of an event exists in edges.jsonl;
  g. a summary is printed; the exit status is 0 only if everything agrees.

Data model (all values immutable and canonical, so that equality is equality of the JSON):
  RSet      (vals, up, dn)      vals: increasing tuple; up / dn: start of the rays or None
  F domain  ('b', s, mlo, mhi, rlo, absM)  |  ('e', s, ((M, RSet), ...))
  C domain  ('b', tlo, thi, nlo, nhi, c4, r0lo)  |  ('e', ((tau, nu, RSet), ...))
  U domain  ('u', lo, hi)
"""
import argparse
import csv
import gzip
import hashlib
import json
import os
import sys
import tarfile
import time
from itertools import product

INVARIANTS = ('M', 'r_2', 'nu', 'r_0', 'tau', 'upsilon')
INV_DOM = {'M': 'F', 'r_2': 'F', 'nu': 'C', 'r_0': 'C', 'tau': 'C', 'upsilon': 'U'}
DOM_INVS = {'F': ('M', 'r_2'), 'C': ('nu', 'r_0', 'tau'), 'U': ('upsilon',)}


class Undefined(Exception):
    """The export asks for something FORMAT.md does not define."""


# Counters of situations that FORMAT.md defines in a way that deserves attention (see FORMAT_NOTES.md).
WARN = {'lossy_intersect': 0, 'mixed_lattice': 0}


# ======================================================================================
# integers
# ======================================================================================
def fdiv(a, b):
    """floor(a / b)"""
    return a // b


def cdiv(a, b):
    """ceil(a / b)"""
    return -((-a) // b)


def lat_up(x, s):
    """smallest multiple of s that is >= x"""
    return -((-x) // s) * s


def lat_dn(x, s):
    """largest multiple of s that is <= x"""
    return (x // s) * s


def lo_max(a, b):
    """the stronger of two lower ends (None = no bound)"""
    if a is None:
        return b
    if b is None:
        return a
    return a if a >= b else b


def hi_min(a, b):
    """the stronger of two upper ends (None = no bound)"""
    if a is None:
        return b
    if b is None:
        return a
    return a if a <= b else b


def add_end(acc, k, x):
    """acc + k*x with None absorbing"""
    if acc is None or x is None:
        return None
    return acc + k * x


def sub_end(a, b):
    if a is None or b is None:
        return None
    return a - b


# ======================================================================================
# RSet (FORMAT.md 2.1)
# ======================================================================================
R_NONE = ((), None, None)


def r_all(step):
    return ((), 0, -step)


def r_make(values, up, dn, step):
    """Canonical RSet of  values + {up, up+step, ...} + {dn, dn-step, ...}."""
    vs = sorted(set(values))
    if up is not None:
        while vs and vs[-1] >= up:
            vs.pop()
        while vs and vs[-1] == up - step:
            up = vs.pop()
    if dn is not None:
        k, n = 0, len(vs)
        while k < n and vs[k] <= dn:
            k += 1
        while k < n and vs[k] == dn + step:
            dn = vs[k]
            k += 1
        if k:
            vs = vs[k:]
        if up is not None and dn + step >= up:
            return ((), 0, -step)
    return (tuple(vs), up, dn)


def r_has(r, x, step):
    if x % step:
        return False
    vals, up, dn = r
    if up is not None and x >= up:
        return True
    if dn is not None and x <= dn:
        return True
    return x in vals


def r_min(r):
    """minimum, None if unbounded below (the set is not empty)"""
    vals, up, dn = r
    if dn is not None:
        return None
    return vals[0] if vals else up


def r_max(r):
    vals, up, dn = r
    if up is not None:
        return None
    return vals[-1] if vals else dn


def r_ge(r, lo, step):
    if lo is None:
        return r
    vals, up, dn = r
    lo = lat_up(lo, step)
    if dn is None and (up is None or up >= lo) and (not vals or vals[0] >= lo):
        return r
    keep = [v for v in vals if v >= lo]
    if dn is not None:
        keep.extend(range(lo, dn + 1, step))
    if up is not None and up < lo:
        up = lo
    return r_make(keep, up, None, step)


def r_le(r, hi, step):
    if hi is None:
        return r
    vals, up, dn = r
    hi = lat_dn(hi, step)
    if up is None and (dn is None or dn <= hi) and (not vals or vals[-1] <= hi):
        return r
    keep = [v for v in vals if v <= hi]
    if up is not None:
        keep.extend(range(up, hi + 1, step))
    if dn is not None and dn > hi:
        dn = hi
    return r_make(keep, None, dn, step)


def r_only(r, values, step):
    return (tuple(sorted({v for v in values if r_has(r, v, step)})), None, None)


def r_remove(r, x, step):
    if not r_has(r, x, step):
        return r
    vals, up, dn = r
    keep = [v for v in vals if v != x]
    if up is not None and x >= up:
        keep.extend(range(up, x, step))
        up = x + step
    elif dn is not None and x <= dn:
        keep.extend(range(x + step, dn + 1, step))
        dn = x - step
    return r_make(keep, up, dn, step)


def r_coarsen(r, s_from, s_to):
    """Members of r (on the lattice s_from) lying on the coarser lattice s_to (FORMAT.md 4.6)."""
    if s_from == s_to:
        return r
    v, u, d = r
    return r_make([x for x in v if x % s_to == 0], None if u is None else lat_up(u, s_to),
                  None if d is None else lat_dn(d, s_to), s_to)


def r_intersect(a, b, sa, sb):
    """FORMAT.md 2.1 `intersect`: the set intersection of two RSets on the same lattice."""
    if sa != sb:
        raise ValueError('r_intersect: operands on different lattices')
    if a == b:
        return a
    av, au, ad = a
    bv, bu, bd = b
    keep = [v for v in av if r_has(b, v, sb)]
    keep.extend(v for v in bv if r_has(a, v, sa))
    for u, d in ((au, bd), (bu, ad)):
        if u is not None and d is not None and u <= d:
            keep.extend(range(u, d + 1, sa))
    up = max(au, bu) if (au is not None and bu is not None) else None
    dn = min(ad, bd) if (ad is not None and bd is not None) else None
    return r_make(keep, up, dn, sa)


def r_text(r):
    vals, up, dn = r
    parts = []
    if dn is not None:
        parts.append('<=%d' % dn)
    parts.extend(str(v) for v in vals)
    if up is not None:
        parts.append('>=%d' % up)
    return '{' + ','.join(parts) + '}'


_canon_r_memo = {}


def r_canon(r):
    """JSON text of an RSet with sorted keys and no spaces."""
    t = _canon_r_memo.get(r)
    if t is None:
        vals, up, dn = r
        t = '{'
        if dn is not None:
            t += '"dn":%d,' % dn
        if up is not None:
            t += '"up":%d,' % up
        t += '"v":[' + ','.join(map(str, vals)) + ']}'
        if len(_canon_r_memo) < 200000:
            _canon_r_memo[r] = t
    return t


# ======================================================================================
# F domain (M, r_2)   (FORMAT.md 2.2)
# ======================================================================================
F_TOP = ('b', 1, None, None, None, False)


def f_ray(s, m, rlo, absM):
    lo = rlo
    if absM:
        lo = abs(m) if lo is None else max(lo, abs(m))
    if lo is None:
        return r_all(s)
    return ((), lat_up(lo, s), None)


def f_box(s, mlo, mhi, rlo, absM):
    """A box; converted to enum at once when both ends of M are finite."""
    if mlo is not None and mhi is not None:
        return ('e', s, tuple((m, f_ray(s, m, rlo, absM)) for m in range(lat_up(mlo, s), mhi + 1, s)))
    return ('b', s, mlo, mhi, rlo, bool(absM))


def f_enum(s, pairs):
    """Enum from (M, RSet) pairs with distinct M, in any order; empty RSets are dropped."""
    ps = [p for p in pairs if p[1] != R_NONE]
    ps.sort(key=lambda p: p[0])
    return ('e', s, tuple(ps))


def f_empty(s):
    return ('e', s, ())


def f_mbounds(d):
    """(lo, hi) of M; None = infinite.  Only for boxes and non-empty enums."""
    if d[0] == 'e':
        return d[2][0][0], d[2][-1][0]
    return d[2], d[3]


def f_tighten_m(d, lo, hi):
    if d[0] == 'e':
        ents = d[2]
        keep = tuple(p for p in ents if (lo is None or p[0] >= lo) and (hi is None or p[0] <= hi))
        return d if len(keep) == len(ents) else ('e', d[1], keep)
    _, s, mlo, mhi, rlo, absM = d
    nlo, nhi = lo_max(mlo, lo), hi_min(mhi, hi)
    if nlo is not None:
        nlo = lat_up(nlo, s)
    if nhi is not None:
        nhi = lat_dn(nhi, s)
    if nlo is not None and nhi is not None and nlo > nhi:
        return f_empty(s)
    return f_box(s, nlo, nhi, rlo, absM)


def f_restrict_m(d, ms):
    """Keep only the M in the finite set ms (members off the lattice of d are ignored)."""
    s = d[1]
    want = {m for m in ms if m % s == 0}
    if d[0] == 'e':
        ents = d[2]
        keep = tuple(p for p in ents if p[0] in want)
        return d if len(keep) == len(ents) else ('e', s, keep)
    _, _, mlo, mhi, rlo, absM = d
    return ('e', s, tuple((m, f_ray(s, m, rlo, absM)) for m in sorted(want)
                          if (mlo is None or m >= mlo) and (mhi is None or m <= mhi)))


def f_map(d, fn):
    """Enum: replace the RSet at every M by fn(M, RSet); empty ones are dropped."""
    out = []
    same = True
    for m, r in d[2]:
        r2 = fn(m, r)
        if r2 is not r:
            same = False
        if r2 != R_NONE:
            out.append((m, r2))
    return d if same else ('e', d[1], tuple(out))


def f_mirror(d):
    if d[0] == 'e':
        return ('e', d[1], tuple((-m, r) for m, r in reversed(d[2])))
    _, s, mlo, mhi, rlo, absM = d
    return f_box(s, None if mhi is None else -mhi, None if mlo is None else -mlo, rlo, absM)


def f_coarsen(d, s):
    if d[1] == s:
        return d
    if d[0] == 'e':
        return f_enum(s, [(m, r_coarsen(r, d[1], s)) for m, r in d[2] if m % s == 0])
    return f_box(s, d[2], d[3], d[4], d[5])


def f_intersect(a, b):
    """FORMAT.md 4.6 intersection.  Operands on different lattices are first restricted to the
    coarser lattice."""
    if a[1] != b[1]:
        s = max(a[1], b[1])
        if s % min(a[1], b[1]):
            raise ValueError('incompatible lattices')
        a, b = f_coarsen(a, s), f_coarsen(b, s)
    sa, sb = a[1], b[1]
    if a[0] == 'e' and b[0] == 'e':
        other = dict(b[2])
        return f_enum(sa, [(m, r_intersect(r, other[m], sa, sb)) for m, r in a[2] if m in other])
    if a[0] == 'b' and b[0] == 'b':
        lo, hi = lo_max(a[2], b[2]), hi_min(a[3], b[3])
        if lo is not None and hi is not None and lo > hi:
            return f_empty(sa)
        return f_box(sa, lo, hi, lo_max(a[4], b[4]), a[5] or b[5])
    en, bx = (a, b) if a[0] == 'e' else (b, a)
    _, _, mlo, mhi, rlo, absM = bx
    se = en[1]
    out = []
    for m, r in en[2]:
        if (mlo is not None and m < mlo) or (mhi is not None and m > mhi):
            continue
        low = rlo
        if absM:
            low = abs(m) if low is None else max(low, abs(m))
        out.append((m, r_ge(r, low, se)))
    return f_enum(sa, out)


def f_pins(d):
    """(pin of M, pin of r_2), None where the projection is not a singleton."""
    if d[0] != 'e' or not d[2]:
        return None, None
    ents = d[2]
    pm = ents[0][0] if len(ents) == 1 else None
    return pm, _r_pin(r for _, r in ents)


def _r_pin(rsets):
    seen = None
    for vals, up, dn in rsets:
        if up is not None or dn is not None or len(vals) > 1:
            return None
        if vals:
            if seen is None:
                seen = vals[0]
            elif seen != vals[0]:
                return None
    return seen


def f_canon(d):
    if d[0] == 'e':
        return '{"e":[' + ','.join(['[%d,%s]' % (m, r_canon(r)) for m, r in d[2]]) + '],"s":%d}' % d[1]
    return '{"b":[%s,%s,%s,%s],"s":%d}' % (_j(d[2]), _j(d[3]), _j(d[4]), 'true' if d[5] else 'false', d[1])


def f_text(d, limit):
    if d[0] == 'b':
        _, s, mlo, mhi, rlo, absM = d
        return 'M in [%s,%s]; r_2 >= %s%s' % ('-inf' if mlo is None else mlo, 'inf' if mhi is None else mhi,
                                              '-inf' if rlo is None else rlo, ', |M|' if absM else '')
    if not d[2]:
        return 'EMPTY'
    return _join_limited(('M=%d:r_2%s' % (m, r_text(r)) for m, r in d[2]), limit)


# ======================================================================================
# C domain (tau, nu, r_0)   (FORMAT.md 2.3)
# ======================================================================================
C_TOP = ('b', None, None, None, None, False, None)
C_EMPTY = ('e', ())


def c_box(tlo, thi, nlo, nhi, c4, r0lo):
    if c4:
        if tlo is not None:
            nlo = lo_max(nlo, 2 * tlo - 1)
        if thi is not None:
            nhi = hi_min(nhi, 2 * thi + 1)
        if nlo is not None:
            tlo = lo_max(tlo, cdiv(nlo - 1, 2))
        if nhi is not None:
            thi = hi_min(thi, fdiv(nhi + 1, 2))
    if tlo is not None and thi is not None and nlo is not None and nhi is not None:
        ray = r_all(1) if r0lo is None else ((), r0lo, None)
        return ('e', tuple((t, n, ray) for t in range(tlo, thi + 1) for n in range(nlo, nhi + 1)
                           if not c4 or abs(2 * t - n) <= 1))
    return ('b', tlo, thi, nlo, nhi, bool(c4), r0lo)


def c_enum(triples):
    ts = [x for x in triples if x[2] != R_NONE]
    ts.sort(key=lambda x: (x[0], x[1]))
    return ('e', tuple(ts))


def c_tighten(d, tlo=None, thi=None, nlo=None, nhi=None):
    if d[0] == 'e':
        ents = d[1]
        keep = tuple(x for x in ents
                     if (tlo is None or x[0] >= tlo) and (thi is None or x[0] <= thi)
                     and (nlo is None or x[1] >= nlo) and (nhi is None or x[1] <= nhi))
        return d if len(keep) == len(ents) else ('e', keep)
    _, a, b, c, e, c4, r0lo = d
    a, b, c, e = lo_max(a, tlo), hi_min(b, thi), lo_max(c, nlo), hi_min(e, nhi)
    if (a is not None and b is not None and a > b) or (c is not None and e is not None and c > e):
        return C_EMPTY
    return c_box(a, b, c, e, c4, r0lo)


def c_filter(d, pred):
    ents = d[1]
    keep = tuple(x for x in ents if pred(x[0], x[1]))
    return d if len(keep) == len(ents) else ('e', keep)


def c_map(d, fn):
    """Enum: replace the RSet at every key by fn(tau, nu, RSet); empty ones are dropped."""
    out = []
    same = True
    for t, n, r in d[1]:
        r2 = fn(t, n, r)
        if r2 is not r:
            same = False
        if r2 != R_NONE:
            out.append((t, n, r2))
    return d if same else ('e', tuple(out))


def c_tau_bounds(d):
    """(lo, hi) of tau; an empty enum gives (None, None)."""
    if d[0] == 'e':
        if not d[1]:
            return None, None
        return d[1][0][0], d[1][-1][0]
    return d[1], d[2]


def c_nu_bounds(d):
    if d[0] == 'e':
        if not d[1]:
            return None, None
        ns = [x[1] for x in d[1]]
        return min(ns), max(ns)
    return d[3], d[4]


def c_mirror(d):
    if d[0] == 'e':
        return c_enum([(-t, -n, r) for t, n, r in d[1]])
    _, tlo, thi, nlo, nhi, c4, r0lo = d
    neg = lambda x: None if x is None else -x
    return c_box(neg(thi), neg(tlo), neg(nhi), neg(nlo), c4, r0lo)


def c_intersect(a, b):
    if a[0] == 'e' and b[0] == 'e':
        other = {(t, n): r for t, n, r in b[1]}
        return c_enum([(t, n, r_intersect(r, other[(t, n)], 1, 1)) for t, n, r in a[1] if (t, n) in other])
    if a[0] == 'b' and b[0] == 'b':
        tlo, thi = lo_max(a[1], b[1]), hi_min(a[2], b[2])
        nlo, nhi = lo_max(a[3], b[3]), hi_min(a[4], b[4])
        if (tlo is not None and thi is not None and tlo > thi) or \
                (nlo is not None and nhi is not None and nlo > nhi):
            return C_EMPTY
        return c_box(tlo, thi, nlo, nhi, a[5] or b[5], lo_max(a[6], b[6]))
    en, bx = (a, b) if a[0] == 'e' else (b, a)
    _, tlo, thi, nlo, nhi, c4, r0lo = bx
    out = []
    for t, n, r in en[1]:
        if (tlo is not None and t < tlo) or (thi is not None and t > thi):
            continue
        if (nlo is not None and n < nlo) or (nhi is not None and n > nhi):
            continue
        if c4 and abs(2 * t - n) > 1:
            continue
        out.append((t, n, r_ge(r, r0lo, 1)))
    return c_enum(out)


def c_pins(d):
    """(pin of nu, pin of r_0, pin of tau)"""
    if d[0] != 'e' or not d[1]:
        return None, None, None
    ents = d[1]
    t0, n0 = ents[0][0], ents[0][1]
    pt = t0 if ents[-1][0] == t0 else None
    pn = n0
    for x in ents:
        if x[1] != n0:
            pn = None
            break
    return pn, _r_pin(x[2] for x in ents), pt


def c_canon(d):
    if d[0] == 'e':
        return '{"e":[' + ','.join(['[%d,%d,%s]' % (t, n, r_canon(r)) for t, n, r in d[1]]) + ']}'
    return '{"b":[%s,%s,%s,%s,%s,%s]}' % (_j(d[1]), _j(d[2]), _j(d[3]), _j(d[4]),
                                          'true' if d[5] else 'false', _j(d[6]))


def c_text(d, limit):
    if d[0] == 'b':
        _, tlo, thi, nlo, nhi, c4, r0lo = d
        f = lambda x, s: s if x is None else str(x)
        return 'tau in [%s,%s]; nu in [%s,%s]%s; r_0 >= %s' % (
            f(tlo, '-inf'), f(thi, 'inf'), f(nlo, '-inf'), f(nhi, 'inf'),
            '; |2tau-nu|<=1' if c4 else '', f(r0lo, '-inf'))
    if not d[1]:
        return 'EMPTY'
    return _join_limited(('(tau=%d,nu=%d):r_0%s' % (t, n, r_text(r)) for t, n, r in d[1]), limit)


# ======================================================================================
# U domain   (FORMAT.md 2.4)
# ======================================================================================
U_TOP = ('u', None, None)


def u_tighten(d, lo, hi):
    return ('u', lo_max(d[1], lo), hi_min(d[2], hi))


def u_canon(d):
    return '{"u":[%s,%s]}' % (_j(d[1]), _j(d[2]))


def u_text(d, limit):
    if d[1] is not None and d[2] is not None and d[1] > d[2]:
        return 'EMPTY'
    return 'upsilon in [%s,%s]' % ('-inf' if d[1] is None else d[1], 'inf' if d[2] is None else d[2])


# ======================================================================================
# generic helpers on domains
# ======================================================================================
TOP = {'F': F_TOP, 'C': C_TOP, 'U': U_TOP}
CANON = {'F': f_canon, 'C': c_canon, 'U': u_canon}
TEXT = {'F': f_text, 'C': c_text, 'U': u_text}


def _j(x):
    return 'null' if x is None else '%d' % x


def _join_limited(pieces, limit):
    """' '.join(pieces), but stop producing text once it is longer than limit (None: no limit)."""
    out = []
    size = -1
    for p in pieces:
        out.append(p)
        size += len(p) + 1
        if limit is not None and size > limit:
            break
    return ' '.join(out)


def digest(kind, d):
    return hashlib.sha1(CANON[kind](d).encode()).hexdigest()[:12]


def statement(kind, d, limit, dg=None):
    """Statement text of FORMAT.md section 5."""
    t = TEXT[kind](d, limit)
    if len(t) <= limit:
        return t
    return t[:limit] + '... [digest %s]' % (dg or digest(kind, d))


def is_empty(kind, d):
    if kind == 'U':
        return d[1] is not None and d[2] is not None and d[1] > d[2]
    return d[0] == 'e' and not d[-1]


def pins_of(kind, d):
    """dict invariant -> pinned value for one domain"""
    if kind == 'F':
        vals = f_pins(d)
    elif kind == 'C':
        vals = c_pins(d)
    else:
        vals = (d[1] if (d[1] is not None and d[1] == d[2]) else None,)
    return {inv: v for inv, v in zip(DOM_INVS[kind], vals) if v is not None}


def from_json(kind, j):
    """Domain from its JSON encoding (already canonical in a correct export)."""
    if kind == 'U':
        return ('u', j['u'][0], j['u'][1])
    if kind == 'F':
        s = j['s']
        if 'e' in j:
            return ('e', s, tuple((m, (tuple(r.get('v', ())), r.get('up'), r.get('dn'))) for m, r in j['e']))
        mlo, mhi, rlo, absM = j['b']
        return ('b', s, mlo, mhi, rlo, bool(absM))
    if 'e' in j:
        return ('e', tuple((t, n, (tuple(r.get('v', ())), r.get('up'), r.get('dn'))) for t, n, r in j['e']))
    tlo, thi, nlo, nhi, c4, r0lo = j['b']
    return ('b', tlo, thi, nlo, nhi, bool(c4), r0lo)


def projection(kind, d, inv):
    """(lo, hi) of the projection of a domain onto one invariant; None = unbounded.
    An empty domain gives (None, None)."""
    if kind == 'U':
        return d[1], d[2]
    if kind == 'F':
        if d[0] == 'e':
            if not d[2]:
                return None, None
            if inv == 'M':
                return d[2][0][0], d[2][-1][0]
            return _r_hull(r for _, r in d[2])
        _, s, mlo, mhi, rlo, absM = d
        mlo = None if mlo is None else lat_up(mlo, s)
        mhi = None if mhi is None else lat_dn(mhi, s)
        if inv == 'M':
            return mlo, mhi
        low = rlo
        if absM:
            # smallest |M| on the M-range (a box has at least one infinite end)
            if mlo is not None and mlo > 0:
                least = mlo
            elif mhi is not None and mhi < 0:
                least = -mhi
            else:
                least = 0
            low = least if low is None else max(low, least)
        return (None if low is None else lat_up(low, s)), None
    if d[0] == 'e':
        if not d[1]:
            return None, None
        if inv == 'tau':
            return d[1][0][0], d[1][-1][0]
        if inv == 'nu':
            return c_nu_bounds(d)
        return _r_hull(x[2] for x in d[1])
    if inv == 'tau':
        return d[1], d[2]
    if inv == 'nu':
        return d[3], d[4]
    return d[6], None


def _r_hull(rsets):
    lo = hi = None
    lo_inf = hi_inf = False
    for r in rsets:
        a, b = r_min(r), r_max(r)
        if a is None:
            lo_inf = True
        elif lo is None or a < lo:
            lo = a
        if b is None:
            hi_inf = True
        elif hi is None or b > hi:
            hi = b
    return (None if lo_inf else lo), (None if hi_inf else hi)


# ======================================================================================
# upsilon of torus knots, as stated in rule F11
# ======================================================================================
_ups_memo = {}


def _divide_by_tk_minus_1(a, k):
    """Exact quotient of the polynomial a (list of coefficients, a[i] of t^i) by t^k - 1."""
    b = [0] * len(a)
    for i in range(len(a)):
        b[i] = (b[i - k] if i >= k else 0) - a[i]
    if any(b[len(a) - k:]):
        raise ArithmeticError('division by t^%d - 1 is not exact' % k)
    return b[:len(a) - k]


def torus_upsilon(p, q):
    key = (p, q)
    if key in _ups_memo:
        return _ups_memo[key]
    if p < 1 or q < 1:
        raise Undefined('upsilon(T(%d,%d)): parameters must be positive' % (p, q))
    # (t^{pq} - 1)(t - 1)
    num = [0] * (p * q + 2)
    num[0] += 1
    num[1] -= 1
    num[p * q] -= 1
    num[p * q + 1] += 1
    quo = _divide_by_tk_minus_1(_divide_by_tk_minus_1(num, p), q)
    deg = (p - 1) * (q - 1)
    if len(quo) != deg + 1 or deg % 2:
        raise ArithmeticError('Alexander polynomial of T(%d,%d): unexpected degree' % (p, q))
    exps = []
    prev = 0
    for i in range(deg, -1, -1):
        c = quo[i]
        if c == 0:
            continue
        if c not in (1, -1) or c == prev:
            raise ArithmeticError('Alexander polynomial of T(%d,%d): coefficients are not alternating +-1' % (p, q))
        prev = c
        exps.append(i - deg // 2)
    if len(exps) % 2 == 0:
        raise ArithmeticError('Alexander polynomial of T(%d,%d): even number of terms' % (p, q))
    m = 0
    best = None
    for i in range(len(exps)):
        if i % 2 == 0:
            v = m - exps[i]
            if best is None or v > best:
                best = v
            if i + 1 < len(exps):
                m = m - 2 * (exps[i] - exps[i + 1]) + 1
        else:
            m = m - 1
    _ups_memo[key] = best
    return best


# ======================================================================================
# surgery expressions
# ======================================================================================
def phi2(M, p, q):
    return abs(p - q * M) + (2 if (q == 1 and p == M) else 0)


def phic(nu, p, q):
    return abs(p - q * nu)


def f_bound_E(d, p, q, vmax):
    """Box step of F10 (4.1): E_2 <= vmax on a box.  Returns d itself if no bound is available."""
    _, s, mlo, mhi, rlo, absM = d
    rmin = rlo
    if absM:
        rmin = 0 if rmin is None else max(rmin, 0)
    if rmin is None:
        return d
    B = vmax - q * rmin
    if B < 0:
        return f_empty(s)
    return f_tighten_m(d, cdiv(p - B, q), fdiv(p + B, q))


def c_bound_E(d, p, q, vmax):
    """Box step of F10 (4.2): E_C <= vmax on a box."""
    r0lo = d[6]
    if r0lo is None:
        return d
    B = vmax - q * r0lo
    if B < 0:
        return C_EMPTY
    return c_tighten(d, nlo=cdiv(p - B, q), nhi=fdiv(p + B, q))


# ======================================================================================
# operators.  Every operator takes (con, doms) with doms the current domains of con.keys and
# returns the list of new domains in the same order (= the operator's output order).
# ======================================================================================
class Con(object):
    __slots__ = ('cid', 'rule', 'dom', 'nodes', 'par', 'ref', 'keys', 'op', 'partext')

    def __init__(self, rec):
        self.cid = rec['id']
        self.rule = rec['rule']
        self.dom = rec['dom']
        self.nodes = tuple(rec['nodes'])
        self.par = rec.get('par') or {}
        self.ref = rec.get('ref')
        if not self.nodes:
            raise ValueError('constraint without nodes')
        if self.rule == 'X':
            n = self.nodes[0]
            self.keys = ((n, 'F'), (n, 'C'))
        elif self.dom in TOP:
            self.keys = tuple((n, self.dom) for n in self.nodes)
        else:
            raise ValueError('dom %r' % (self.dom,))
        self.op = None
        self.partext = None

    def describe(self):
        return json.dumps({'id': self.cid, 'rule': self.rule, 'dom': self.dom, 'nodes': list(self.nodes),
                           'par': self.par}, sort_keys=True, separators=(',', ':'))


def _one(fn):
    """Lift a unary operator (par, d) -> d'."""
    def op(con, doms):
        if len(doms) != 1:
            raise Undefined('rule %s takes one node' % con.rule)
        return [fn(con.par, doms[0])]
    return op


def _f_const(d, value):
    """enum only: every RSet becomes only({value})"""
    if d[0] != 'e':
        return d
    s = d[1]
    return f_map(d, lambda m, r: r_only(r, (value,), s))


def _c_const(d, value):
    if d[0] != 'e':
        return d
    return c_map(d, lambda t, n, r: r_only(r, (value,), 1))


# ---- 4.1 unary, F -----------------------------------------------------------------------
def u_F1(par, d):
    return f_box(4, None, None, None, True) if d == F_TOP else d


def u_unknot_F(par, d):
    return _f_const(f_tighten_m(d, 0, 0), 0)


def u_F5(par, d):
    return f_tighten_m(d, 0, 0)


def u_F8(par, d):
    ends = [x for x in (par.get('c'), par.get('u')) if x is not None]
    if not ends:
        return d
    B = 4 * min(ends)
    return f_tighten_m(d, -B, B)


def u_F11(par, d):
    p, q = par['p'], par['q']
    d = f_tighten_m(d, p * q - p - q, -4 * torus_upsilon(p, q))
    if d[0] != 'e':
        return d
    s = d[1]
    return f_map(d, lambda m, r: r_only(r, (m,), s))


def u_F12(par, d):
    v = 4 * par['n']
    return _f_const(f_tighten_m(d, v, v), v)


def u_F13(par, d):
    v = 4 * par['tau']
    return _f_const(f_tighten_m(d, v, v), 4 * par['m'])


def u_F14(par, d):
    v = 2 * (par['p'] + par['q'] - 2)
    return f_tighten_m(d, v, v)


def u_F15(par, d):
    if d[0] != 'e':
        return d
    fib, tau, g = par.get('fibered'), par.get('tau'), par.get('g')
    known = fib is not None and tau is not None and g is not None
    s = d[1]

    def f(m, r):
        if m == 0:
            return r
        if known:
            ok = bool(fib) and tau == (g if m > 0 else -g) and 2 * g <= abs(m)
            return r if ok else r_remove(r, abs(m), s)
        if fib is False:
            return r_remove(r, abs(m), s)
        return r
    return f_map(d, f)


def u_F16(par, d):
    p, q, g = par['p'], par['q'], par.get('g')
    lo = None if g is None else 4 * cdiv(2 * g - 1, 4)
    return f_tighten_m(d, lo, cdiv(p, q) - 1)


def u_F10_F(par, d):
    p, q = par['p'], par['q']
    v = abs(p)
    if d[0] == 'b':
        d = f_bound_E(d, p, q, v)
        if d[0] == 'b':
            return d
    s = d[1]

    def f(m, r):
        x = v - phi2(m, p, q)
        return r_only(r, (x // q,) if x % q == 0 else (), s)
    return f_map(d, f)


# ---- 4.2 unary, C -----------------------------------------------------------------------
def u_C1(par, d):
    return c_box(None, None, None, None, False, 0) if d == C_TOP else d


def u_C4(par, d):
    if d[0] == 'b':
        if d[5]:
            return d
        return c_box(d[1], d[2], d[3], d[4], True, d[6])
    return c_filter(d, lambda t, n: abs(2 * t - n) <= 1)


def u_unknot_C(par, d):
    return _c_const(c_tighten(d, 0, 0, 0, 0), 0)


def u_C5(par, d):
    if par.get('why') == 'amphichiral':
        return c_tighten(d, 0, 0, 0, 0)
    g4 = par['g4']
    nb = max(2 * g4 - 1, 0)
    return c_tighten(d, -g4, g4, -nb, nb)


def u_C8(par, d):
    return c_tighten(d, par['tau'], par['tau'])


def u_C9(par, d):
    n, w = par['n'], par['w']
    return c_tighten(d, cdiv(w - n + 1, 2), fdiv(w + n - 1, 2), w - n, w + n)


def u_C10(par, d):
    if 'named' in par:
        return _c_const(d, par['named'])
    ge3, ea, eb = bool(par.get('ge3')), bool(par.get('a')), bool(par.get('b'))
    if d[0] == 'b':
        if not ge3 or (d[6] is not None and d[6] >= 3):
            return d
        return c_box(d[1], d[2], d[3], d[4], d[5], 3)

    def f(t, n, r):
        if ge3:
            r = r_ge(r, 3, 1)
        if ea:
            r = r_remove(r, 3 - abs(1 - n), 1)
        if eb and abs(n) == 3:
            r = r_remove(r, 3, 1)
        return r
    return c_map(d, f)


def _c_nu_r0(d, nu, r0):
    """`applied as C11`: nu = nu, then (enum only) r_0 = r0"""
    return _c_const(c_tighten(d, nlo=nu, nhi=nu), r0)


def u_C11(par, d):
    v = 2 * par['g'] - 1
    return _c_nu_r0(d, v, v)


def u_C12(par, d):
    return _c_nu_r0(d, par['tau'], par['m'])


def u_C13(par, d):
    kind = par['kind']
    if kind == 'n3m3':
        return _c_nu_r0(d, 0, 4)
    if kind == 'odd32':
        n = par['n']
        return _c_nu_r0(d, 2 * n - 1, 6 * n - 1)
    raise Undefined('C13: kind %r is not defined in FORMAT.md' % (kind,))


def u_C14(par, d):
    n = par['n']
    num = par['norm'] + 2 * n - 3
    if num % 2:
        raise ArithmeticError('C14: r_0 = (norm + 2n - 3)/2 is not an integer')
    return _c_nu_r0(d, 2 * n - 1, num // 2)


def u_C15(par, d):
    if d[0] != 'e':
        return d

    def f(t, n, r):
        bad = {n + 2}
        for k in range(1, n):
            bad.add(2 * k + 2 - n)
        for v in sorted(bad):
            if v >= 0:
                r = r_remove(r, v, 1)
        return r
    return c_map(d, f)


def u_F10_C(par, d):
    p, q = par['p'], par['q']
    v = abs(p)
    if d[0] == 'b':
        d = c_bound_E(d, p, q, v)
        if d[0] == 'b':
            return d

    def f(t, n, r):
        x = v - phic(n, p, q)
        return r_only(r, (x // q,) if x % q == 0 else (), 1)
    return c_map(d, f)


# ---- 4.3 unary, U -----------------------------------------------------------------------
def u_U4a(par, d):
    if par.get('why') in ('slice', 'amphichiral', 'unknot'):
        return u_tighten(d, 0, 0)
    g4 = par['g4']
    return u_tighten(d, -g4, g4)


def u_U2a(par, d):
    return u_tighten(d, -par['tau'], -par['tau'])


def u_U3(par, d):
    return u_tighten(d, 0, 0)


def u_U1(par, d):
    return u_tighten(d, par['value'], par['value'])


def u_U7(par, d):
    v = torus_upsilon(par['p'], par['q'])
    return u_tighten(d, v, v)


# ---- 4.4 coupling X ---------------------------------------------------------------------
SLOPE_SETS = {}          # filled from parameters.json
_slope_memo = {}
_delta_memo = {}


def resolve_slopes(spec):
    """(hashable key, list of (p, q)) of a slope specification."""
    if spec is None:
        return None, ()
    if isinstance(spec, str):
        if spec not in SLOPE_SETS:
            raise Undefined('slope set %r is not in parameters.json' % spec)
        return spec, SLOPE_SETS[spec]
    key = (spec['base'], tuple((p, q) for p, q in spec['extra']))
    if key not in _slope_memo:
        if spec['base'] not in SLOPE_SETS:
            raise Undefined('slope set %r is not in parameters.json' % (spec['base'],))
        lst = list(SLOPE_SETS[spec['base']])
        have = set(lst)
        for s in key[1]:
            if s not in have:
                lst.append(s)
        _slope_memo[key] = lst
    return key, _slope_memo[key]


def _x_delta(M, nu, slopes, x1, x2, g, x4, x5, x5m):
    best = None
    if x1:
        best = abs(M - nu)          # >= 0
        for p, q in slopes:
            v = cdiv(abs(p - q * nu) - phi2(M, p, q), q)
            if v > best:
                best = v
    if x2 and (best is None or best < 1):
        best = 1
    if g is not None:
        lim = 2 * g - 1
        for p, q in slopes:
            if abs(p) <= lim * q:
                v = cdiv(abs(p - q * nu) + 2 - phi2(M, p, q), q)
                if best is None or v > best:
                    best = v
    if x4:
        for v in (abs(1 - nu) - abs(1 - M) + 1, abs(1 + nu) - abs(1 + M) + 1):
            if best is None or v > best:
                best = v
    if x5:
        v = M - nu + 2
        if best is None or v > best:
            best = v
    if x5m:
        v = nu - M + 2
        if best is None or v > best:
            best = v
    return best


def op_X(con, doms):
    F, C = doms
    if F[0] != 'e' or C[0] != 'e' or not F[2] or not C[1]:
        return [F, C]
    par = con.par
    x1, x2, x4 = bool(par.get('x1')), bool(par.get('x2')), bool(par.get('x4'))
    x5, x5m, g = bool(par.get('x5')), bool(par.get('x5m')), par.get('x3_g')
    if not (x1 or x2 or x4 or x5 or x5m or g is not None):
        return [F, C]
    skey, slopes = resolve_slopes(par.get('slopes'))
    mkey = (skey, x1, x2, g, x4, x5, x5m)
    memo = _delta_memo.get(mkey)
    if memo is None:
        memo = _delta_memo[mkey] = {}

    def delta(m, n):
        # Delta(M, nu); None if nothing contributes (e.g. only x3 and no slope qualifies)
        if (m, n) not in memo:
            memo[(m, n)] = _x_delta(m, n, slopes, x1, x2, g, x4, x5, x5m)
        return memo[(m, n)]

    s = F[1]
    cmin = {}                      # nu -> min r_0, None if unbounded below
    for t, n, r in C[1]:
        v = r_min(r)
        if n not in cmin:
            cmin[n] = v
        elif cmin[n] is not None:
            cmin[n] = None if v is None else min(cmin[n], v)
    nus = sorted(cmin)
    rmax = [(m, r_max(r)) for m, r in F[2]]

    newF = F
    if all(v is not None for v in cmin.values()):
        def ff(m, r):
            low = None
            for n in nus:
                dl = delta(m, n)
                if dl is None:
                    return r
                v = cmin[n] + dl
                if low is None or v < low:
                    low = v
            return r_ge(r, low, s)
        newF = f_map(F, ff)
    newC = C
    if all(v is not None for _, v in rmax):
        his = {}
        for n in nus:
            high = None
            for m, v in rmax:
                dl = delta(m, n)
                if dl is None:
                    high = None
                    break
                if high is None or v - dl > high:
                    high = v - dl
            his[n] = high
        newC = c_map(C, lambda t, n, r: r if his[n] is None else r_le(r, his[n], 1))
    return [newF, newC]


# ---- 4.5 difference rules ---------------------------------------------------------------
def diff_bounds(con):
    r, par = con.rule, con.par
    if r == 'F7':
        return 0, 4
    if r in ('C7', 'U5'):
        return 0, 1
    a, b, h = par['a'], par['b'], par['h']
    if r == 'F9':
        return (-4 * a * b, (a - b) ** 2) if h > 0 else (-(a - b) ** 2, 4 * a * b)
    if r == 'U6':
        t = a * (a - 1) // 2 + b * (b - 1) // 2
        return (-t, a * b) if h > 0 else (-a * b, t)
    raise Undefined('no difference bounds for rule %s' % r)


def _coef_range(c, lo, hi):
    """integer x with lo <= c*x <= hi"""
    if c > 0:
        return cdiv(lo, c), fdiv(hi, c)
    return cdiv(hi, c), fdiv(lo, c)


def _f_narrow(d, o, l, h):
    """narrow d against o with M(o) - M(d) in [l, h]"""
    if o[0] == 'e' and not o[2]:
        return f_empty(d[1])
    olo, ohi = f_mbounds(o)
    d = f_tighten_m(d, sub_end(olo, h), sub_end(ohi, l))
    if d[0] == 'e' and o[0] == 'e':
        oms = [m for m, _ in o[2]]
        d = f_restrict_m(d, [m for m, _ in d[2] if any(l <= x - m <= h for x in oms)])
    return d


def _c_narrow(d, o, l, h):
    if o[0] == 'e' and not o[1]:
        return C_EMPTY
    olo, ohi = c_tau_bounds(o)
    d = c_tighten(d, tlo=sub_end(olo, h), thi=sub_end(ohi, l))
    if d[0] == 'e' and o[0] == 'e':
        ots = sorted({x[0] for x in o[1]})
        ok = {}

        def pred(t, n):
            v = ok.get(t)
            if v is None:
                v = ok[t] = any(l <= x - t <= h for x in ots)
            return v
        d = c_filter(d, pred)
    return d


def op_diff(con, doms):
    lo, hi = diff_bounds(con)
    dom = con.dom
    if {'F7': 'F', 'F9': 'F', 'C7': 'C', 'U5': 'U', 'U6': 'U'}[con.rule] != dom:
        raise Undefined('rule %s on domain %s' % (con.rule, dom))
    if 'coef' in con.par:
        if len(doms) != 1:
            raise Undefined('difference rule with `coef` and %d nodes' % len(doms))
        c = con.par['coef']
        d = doms[0]
        if dom == 'U':
            a, b = _coef_range(c, lo, hi)
            return [u_tighten(d, a, b)]
        if d[0] == 'b':
            a, b = _coef_range(c, lo, hi)
            return [f_tighten_m(d, a, b) if dom == 'F' else c_tighten(d, tlo=a, thi=b)]
        if dom == 'F':
            return [f_restrict_m(d, [m for m, _ in d[2] if lo <= c * m <= hi])]
        return [c_filter(d, lambda t, n: lo <= c * t <= hi)]
    if len(doms) != 2:
        raise Undefined('difference rule with %d nodes' % len(doms))
    A, B = doms
    if dom == 'U':
        A2 = u_tighten(A, sub_end(B[1], hi), sub_end(B[2], lo))
        B2 = u_tighten(B, None if A2[1] is None else A2[1] + lo, None if A2[2] is None else A2[2] + hi)
        return [A2, B2]
    narrow = _f_narrow if dom == 'F' else _c_narrow
    A2 = narrow(A, B, lo, hi)
    B2 = narrow(B, A2, -hi, -lo)
    return [A2, B2]


# ---- 4.6 mirror, 4.7 mutation -----------------------------------------------------------
def op_mirror(con, doms):
    if len(doms) != 2:
        raise Undefined('mirror rule with %d nodes' % len(doms))
    A, B = doms
    dom = con.dom
    if dom == 'U':
        neg = lambda x: None if x is None else -x
        A2 = u_tighten(A, neg(B[2]), neg(B[1]))
        B2 = u_tighten(B, neg(A2[2]), neg(A2[1]))
        return [A2, B2]
    inter, mirror = (f_intersect, f_mirror) if dom == 'F' else (c_intersect, c_mirror)
    A2 = inter(A, mirror(B))
    B2 = inter(B, mirror(A2))
    return [A2, B2]


def op_F6(con, doms):
    if len(doms) != 2 or con.dom != 'F':
        raise Undefined('F6 needs two nodes and domain F')
    n = f_intersect(doms[0], doms[1])
    return [n, n]


# ---- 4.8 connected sum ------------------------------------------------------------------
def _mults(con, parts):
    mult = con.par['mult']
    if len(mult) != len(parts) or not parts:
        raise Undefined('sum rule: %d parts but mult = %r' % (len(parts), mult))
    if len(parts) > 2 or (len(parts) == 2 and tuple(mult) != (1, 1)):
        raise Undefined('sum rule: FORMAT.md defines two parts with multiplicities 1, or one part')
    return mult


def op_sum_F(con, doms):
    N, parts = doms[0], list(doms[1:])
    mult = _mults(con, parts)
    if any(d[0] == 'e' and not d[2] for d in doms):
        return [f_empty(N[1])] + parts
    if all(d[0] == 'e' for d in parts):
        sums = {}
        for combo in product(*[[m for m, _ in d[2]] for d in parts]):
            sums.setdefault(sum(k * m for k, m in zip(mult, combo)), []).append(combo)
        N2 = f_restrict_m(N, sums)
        if N2[0] != 'e':
            return [N2] + parts
        used = [set() for _ in parts]
        for m, _ in N2[2]:
            for combo in sums.get(m, ()):
                for i, x in enumerate(combo):
                    used[i].add(x)
        return [N2] + [f_restrict_m(d, used[i]) for i, d in enumerate(parts)]
    lo = hi = 0
    for d, k in zip(parts, mult):
        a, b = f_mbounds(d)
        lo, hi = add_end(lo, k, a), add_end(hi, k, b)
    N2 = f_tighten_m(N, lo, hi)
    if N2[0] == 'e' and not N2[2]:
        return [N2] + parts
    a, b = f_mbounds(N2)
    if len(parts) == 1:
        k = mult[0]
        return [N2, f_tighten_m(parts[0], None if a is None else cdiv(a, k), None if b is None else fdiv(b, k))]
    out = [N2]
    for i in range(2):
        oa, ob = f_mbounds(parts[1 - i])
        out.append(f_tighten_m(parts[i], sub_end(a, ob), sub_end(b, oa)))
    return out


def op_sum_C(con, doms):
    N, parts = doms[0], list(doms[1:])
    mult = _mults(con, parts)
    if any(d[0] == 'e' and not d[1] for d in doms):
        return [C_EMPTY] + parts
    if all(d[0] == 'e' for d in parts):
        combos = list(product(*[[(t, n) for t, n, _ in d[1]] for d in parts]))
        tn = [(sum(k * c[0] for k, c in zip(mult, co)), sum(k * c[1] for k, c in zip(mult, co))) for co in combos]
        if N[0] == 'b':
            ts = [x[0] for x in tn]
            ns = [x[1] for x in tn]
            N = c_tighten(N, min(ts), max(ts), min(ns) - 1, max(ns) + 1)
            if N[0] == 'b':
                return [N] + parts
        have = {(t, n) for t, n, _ in N[1]}
        keepN = set()
        used = [set() for _ in parts]
        for co, (t, n) in zip(combos, tn):
            hit = False
            for dn in (-1, 0, 1):
                if (t, n + dn) in have:
                    keepN.add((t, n + dn))
                    hit = True
            if hit:
                for i, x in enumerate(co):
                    used[i].add(x)
        return [c_filter(N, lambda t, n: (t, n) in keepN)] + \
               [c_filter(d, lambda t, n, u=used[i]: (t, n) in u) for i, d in enumerate(parts)]
    tlo = thi = nlo = nhi = 0
    for d, k in zip(parts, mult):
        a, b = c_tau_bounds(d)
        c, e = c_nu_bounds(d)
        tlo, thi, nlo, nhi = add_end(tlo, k, a), add_end(thi, k, b), add_end(nlo, k, c), add_end(nhi, k, e)
    N2 = c_tighten(N, tlo, thi, None if nlo is None else nlo - 1, None if nhi is None else nhi + 1)
    a, b = c_tau_bounds(N2)
    if len(parts) == 1:
        k = mult[0]
        return [N2, c_tighten(parts[0], None if a is None else cdiv(a, k), None if b is None else fdiv(b, k))]
    out = [N2]
    for i in range(2):
        oa, ob = c_tau_bounds(parts[1 - i])
        out.append(c_tighten(parts[i], sub_end(a, ob), sub_end(b, oa)))
    return out


def op_sum_U(con, doms):
    N, parts = doms[0], list(doms[1:])
    mult = _mults(con, parts)
    lo = hi = 0
    for d, k in zip(parts, mult):
        lo, hi = add_end(lo, k, d[1]), add_end(hi, k, d[2])
    N2 = u_tighten(N, lo, hi)
    a, b = N2[1], N2[2]
    if len(parts) == 1:
        k = mult[0]
        return [N2, u_tighten(parts[0], None if a is None else cdiv(a, k), None if b is None else fdiv(b, k))]
    out = [N2]
    for i in range(2):
        o = parts[1 - i]
        out.append(u_tighten(parts[i], sub_end(a, o[2]), sub_end(b, o[1])))
    return out


# ---- 4.9 surgery equations --------------------------------------------------------------
def _s_items(dom, d, p, q):
    """(list of (phi, RSet), lattice step) of an enum domain for the slope p/q"""
    if dom == 'F':
        return [(phi2(m, p, q), r) for m, r in d[2]], d[1]
    return [(phic(n, p, q), r) for t, n, r in d[1]], 1


def _s_rebuild(dom, d, rsets):
    if dom == 'F':
        return f_enum(d[1], [(m, r) for (m, _), r in zip(d[2], rsets)])
    return c_enum([(t, n, r) for (t, n, _), r in zip(d[1], rsets)])


def _s_max(items, q, fac):
    """max of fac*E over the items; None if unbounded above or there is no item"""
    best = None
    for ph, r in items:
        m = r_max(r)
        if m is None:
            return None
        v = fac * (q * m + ph)
        if best is None or v > best:
            best = v
    return best


def _s_support(items, q, fac, step):
    vals = set()
    progs = []
    down = False
    for ph, r in items:
        for v in r[0]:
            vals.add(fac * (q * v + ph))
        if r[1] is not None:
            progs.append((fac * (q * r[1] + ph), fac * q * step))
        if r[2] is not None:
            down = True
    return vals, progs, down


def _s_narrow(items, q, fac, step, support):
    """new RSets of one side, given the support of the other side"""
    vals, progs, down = support
    if down:
        return [r for _, r in items]
    ray_min = min(st for st, _ in progs) if progs else None
    out = []
    for ph, r in items:
        rv, up, dn = r
        keep = []
        for v in rv:
            e = fac * (q * v + ph)
            if e in vals:
                keep.append(v)
                continue
            for st, sp in progs:
                if e >= st and (e - st) % sp == 0:
                    keep.append(v)
                    break
        if up is not None:
            cand = set()
            for e in vals:
                if e % fac == 0:
                    w = e // fac - ph
                    if w % q == 0:
                        v = w // q
                        if v >= up and v % step == 0:
                            cand.add(v)
            if ray_min is None:
                keep.extend(cand)
                up = None
            else:
                u2 = max(up, lat_up(cdiv(cdiv(ray_min, fac) - ph, q), step))
                keep.extend(v for v in cand if v < u2)
                up = u2
        out.append(r_make(keep, up, dn, step))
    return out


def op_S(con, doms):
    par, dom = con.par, con.dom
    if dom not in ('F', 'C'):
        raise Undefined('surgery equation on domain %s' % dom)
    (pA, qA), (pB, qB) = par['sA'], par['sB']
    a, b = par['a'], par['b']
    phi = phi2 if dom == 'F' else phic
    if len(doms) == 1:
        d = doms[0]
        if d[0] != 'e':
            return [d]
        c = a * qA - b * qB

        def solve(x, r, step):
            rhs = b * phi(x, pB, qB) - a * phi(x, pA, qA)
            if c == 0:
                return r if rhs == 0 else R_NONE
            if rhs % c:
                return R_NONE
            return r_only(r, (rhs // c,), step)
        if dom == 'F':
            s = d[1]
            return [f_map(d, lambda m, r: solve(m, r, s))]
        return [c_map(d, lambda t, n, r: solve(n, r, 1))]
    if len(doms) != 2:
        raise Undefined('surgery equation with %d nodes' % len(doms))
    A, B = doms
    bound = f_bound_E if dom == 'F' else c_bound_E
    for _ in range(2):
        if A[0] == 'b' and B[0] == 'e':
            mx = _s_max(_s_items(dom, B, pB, qB)[0], qB, b)
            if mx is not None:
                A = bound(A, pA, qA, fdiv(mx, a))
        if B[0] == 'b' and A[0] == 'e':
            mx = _s_max(_s_items(dom, A, pA, qA)[0], qA, a)
            if mx is not None:
                B = bound(B, pB, qB, fdiv(mx, b))
    if A[0] == 'b' or B[0] == 'b':
        return [A, B]
    iA, sA = _s_items(dom, A, pA, qA)
    iB, sB = _s_items(dom, B, pB, qB)
    nA = _s_narrow(iA, qA, a, sA, _s_support(iB, qB, b, sB))
    iA2 = [(ph, r) for (ph, _), r in zip(iA, nA)]
    nB = _s_narrow(iB, qB, b, sB, _s_support(iA2, qA, a, sA))
    return [_s_rebuild(dom, A, nA), _s_rebuild(dom, B, nB)]


# ---- dispatch ---------------------------------------------------------------------------
UNARY = {
    ('F1', 'F'): u_F1, ('0_1', 'F'): u_unknot_F, ('F5', 'F'): u_F5, ('F8', 'F'): u_F8, ('F11', 'F'): u_F11,
    ('F12', 'F'): u_F12, ('F13', 'F'): u_F13, ('F14', 'F'): u_F14, ('F15', 'F'): u_F15, ('F16', 'F'): u_F16,
    ('F10', 'F'): u_F10_F,
    ('C1', 'C'): u_C1, ('C4', 'C'): u_C4, ('0_1', 'C'): u_unknot_C, ('C5', 'C'): u_C5, ('C8', 'C'): u_C8,
    ('C9', 'C'): u_C9, ('C10', 'C'): u_C10, ('C11', 'C'): u_C11, ('C12', 'C'): u_C12, ('C13', 'C'): u_C13,
    ('C14', 'C'): u_C14, ('C15', 'C'): u_C15, ('F10', 'C'): u_F10_C,
    ('U4a', 'U'): u_U4a, ('U2a', 'U'): u_U2a, ('U3', 'U'): u_U3, ('U1', 'U'): u_U1, ('U7', 'U'): u_U7,
}
UNARY_OPS = {k: _one(f) for k, f in UNARY.items()}


def operator_of(con):
    """The operator of a constraint (FORMAT.md section 4)."""
    r, dom = con.rule, con.dom
    if r == 'X':
        if dom != 'X' or len(con.nodes) != 1:
            raise Undefined('rule X needs dom X and one node')
        return op_X
    op = UNARY_OPS.get((r, dom))
    if op is not None:
        return op
    if r in ('F7', 'F9', 'C7', 'U5', 'U6'):
        return op_diff
    kind = con.par.get('kind')
    if (r, dom) in (('F3', 'F'), ('C3', 'C')) or (r == 'U4b' and dom == 'U' and kind == 'mirror'):
        return op_mirror
    if (r, dom) == ('F4', 'F'):
        return op_sum_F
    if (r, dom) == ('C6', 'C'):
        return op_sum_C
    if r == 'U4b' and dom == 'U' and kind == 'sum':
        return op_sum_U
    if r == 'F6':
        return op_F6
    if r in ('S1', 'S3', 'S4'):
        return op_S
    raise Undefined('no operator for rule %r on domain %r in FORMAT.md section 4' % (r, dom))


def apply_constraint(con, doms):
    op = con.op
    if op is None:
        op = con.op = operator_of(con)
    return op(con, doms)


# ======================================================================================
# convention tests (run before anything is replayed)
# ======================================================================================
def convention_tests():
    """Checks stated in rule F11 and a few properties of the encoding.  Returns a list of failures."""
    bad = []
    for (p, q), want in (((2, 3), -1), ((3, 4), -2), ((3, 5), -3)):
        try:
            got = torus_upsilon(p, q)
        except Exception as ex:          # pragma: no cover
            got = 'error: %s' % ex
        if got != want:
            bad.append('upsilon(T(%d,%d)) = %r, expected %d' % (p, q, got, want))
    samples = [('F', F_TOP), ('F', f_box(4, None, None, None, True)), ('F', f_box(4, -8, 8, None, True)),
               ('F', f_box(1, 0, 0, None, False)), ('C', C_TOP), ('C', c_box(None, None, None, None, True, 0)),
               ('C', c_box(-1, 1, None, None, True, 0)), ('C', c_box(0, 0, 0, 0, False, None)),
               ('U', U_TOP), ('U', ('u', -2, 3))]
    for kind, d in samples:
        text = CANON[kind](d)
        j = json.loads(text)
        if json.dumps(j, sort_keys=True, separators=(',', ':')) != text:
            bad.append('canonical JSON text of %r is not sorted/compact' % (d,))
        if from_json(kind, j) != d:
            bad.append('JSON round trip of %r' % (d,))
    if digest('F', F_TOP) != hashlib.sha1(b'{"b":[null,null,null,false],"s":1}').hexdigest()[:12]:
        bad.append('digest of TOP')
    if r_make([1, 3, 5], 6, 0, 1) != ((3,), 5, 1) or r_make([4], 8, 0, 4) != ((), 0, -4):
        bad.append('RSet canonical form')
    return bad


# ======================================================================================
# files
# ======================================================================================
def _part(stem, ext, k):
    """Path of part k of a file (plain, or gzip with the further suffix .gz), or None."""
    base = stem + ('.%d' % k if k else '') + ext
    for path in (base, base + '.gz'):
        if os.path.exists(path):
            return path
    return None


def file_parts(directory, name):
    """Paths X.ext, X.1.ext, X.2.ext, ... that exist, in order (each plain or with the suffix .gz)."""
    stem, ext = os.path.splitext(os.path.join(directory, name))
    first = _part(stem, ext, 0)
    paths = [first] if first else []
    k = 1
    while _part(stem, ext, k):
        paths.append(_part(stem, ext, k))
        k += 1
    return paths


def jsonl_parts(directory, name):
    return file_parts(directory, name)


def open_text(path, newline=None):
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8', newline=newline)
    return open(path, encoding='utf-8', newline=newline)


def read_jsonl(directory, name):
    paths = jsonl_parts(directory, name)
    if not paths:
        raise IOError('missing file %s' % os.path.join(directory, name))
    for path in paths:
        with open_text(path) as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def chain_sources(cdir):
    """(file name, bytes) of every chain file: the files of chains/ and the members of the archives
    chains/*.tar.xz (or .tar.gz)."""
    if not os.path.isdir(cdir):
        return
    for fn in sorted(os.listdir(cdir)):
        path = os.path.join(cdir, fn)
        if fn.endswith(('.tar.xz', '.tar.gz')):
            with tarfile.open(path, 'r:*') as tar:
                for m in tar:
                    if m.isfile():
                        yield m.name, tar.extractfile(m).read()
        else:
            with open(path, 'rb') as f:
                yield fn, f.read()


def chain_file_name(node):
    return node.replace('*', 'm').replace('#', '+').replace('/', '_').replace(':', '_')


# ======================================================================================
# report
# ======================================================================================
class Report(object):
    def __init__(self, max_errors):
        self.max = max_errors
        self.count = {}

    def err(self, cat, msg):
        n = self.count.get(cat, 0) + 1
        self.count[cat] = n
        if n <= self.max:
            print('MISMATCH [%s] %s' % (cat, msg() if callable(msg) else msg))
        elif n == self.max + 1:
            print('MISMATCH [%s] ... further mismatches of this kind are not printed' % cat)

    def n(self, cat):
        return self.count.get(cat, 0)

    def total(self):
        return sum(self.count.values())


def short(text, n=400):
    return text if len(text) <= n else text[:n] + '... (%d characters)' % len(text)


# ======================================================================================
# the replay
# ======================================================================================
class Replay(object):
    def __init__(self, cons, limit, rep, keep_text=True):
        self.cons = cons               # constraint id -> Con
        self.limit = limit             # max_statement_text
        self.rep = rep
        self.keep_text = keep_text
        self.state = {}                # (node, dom) -> domain   (absent: TOP)
        self.last = {}                 # (node, dom) -> id of the latest event
        self.pin_event = {}            # (node, invariant) -> event id
        self.ev_con = []               # per event: Con (or None)
        self.ev_key = []               # per event: (node, dom)
        self.ev_in = []                # per event: tuple of input event ids (from the replay)
        self.ev_text = []              # per event: statement text
        self.applications = 0
        self.used_cons = set()

    def run(self, events):
        """events: list of (c, rule, node, dom, in, dg), index = event id"""
        rep, cons, state, last = self.rep, self.cons, self.state, self.last
        n = len(events)
        i = 0
        while i < n:
            cid, rule, node, dom, ins, dg = events[i]
            con = cons.get(cid)
            if con is None:
                rep.err('event', 'event %d: unknown constraint %r' % (i, cid))
                self._record(i, None, (node, dom), tuple(sorted({last[k] for k in [(node, dom)] if k in last})), None)
                last[(node, dom)] = i
                i += 1
                continue
            keys = con.keys
            cur = [state.get(k) or TOP[k[1]] for k in keys]
            failed = False
            try:
                new = apply_constraint(con, cur)
                if len(new) != len(keys):
                    raise Undefined('operator returned %d domains for %d keys' % (len(new), len(keys)))
            except Exception as ex:
                rep.err('event', 'event %d: constraint %s cannot be applied: %s: %s; inputs: %s'
                        % (i, con.describe(), type(ex).__name__, ex, self._inputs(keys, cur)))
                new = cur
                failed = True
            self.applications += 1
            self.used_cons.add(cid)
            changed = [j for j in range(len(keys)) if new[j] != cur[j]]
            want_in = sorted({last[k] for k in keys if k in last})
            # the events of this application: same constraint, same `in`, at most one per output
            j = i + 1
            stop = min(n, i + len(keys))
            while j < stop and events[j][0] == cid and events[j][4] == ins:
                j += 1
            group = range(i, j)
            mine = [keys[k] for k in changed]
            theirs = [(events[e][2], events[e][3]) for e in group]
            pairs = []                 # (event id, index into keys or None)
            if failed:
                pairs = [(e, None) for e in group]
            elif mine == theirs:
                pairs = list(zip(group, changed))
            else:
                index = {}
                for k in changed:
                    index[keys[k]] = k
                for e in group:
                    key = (events[e][2], events[e][3])
                    if key not in keys:
                        rep.err('event', 'event %d: target %s.%s is not a domain of constraint %s'
                                % (e, key[0], key[1], con.describe()))
                        pairs.append((e, None))
                    elif key not in index:
                        rep.err('unchanged', lambda e=e, key=key: (
                            'event %d: applying %s does not change %s.%s (expected digest %s); inputs: %s'
                            % (e, con.describe(), key[0], key[1], events[e][5], self._inputs(keys, cur))))
                        pairs.append((e, None))
                    else:
                        pairs.append((e, index[key]))
                for k in changed:
                    if keys[k] not in theirs:
                        rep.err('event', lambda k=k: (
                            'after event %d: applying %s changes %s.%s to %s but there is no event for it'
                            % (i, con.describe(), keys[k][0], keys[k][1], short(CANON[keys[k][1]](new[k])))))
                if sorted(mine) == sorted(theirs):
                    rep.err('event', 'events %d..%d: order %r differs from the operator output order %r'
                            % (i, j - 1, theirs, mine))
            tin = tuple(want_in)
            for e, k in pairs:
                ecid, erule, enode, edom, eins, edg = events[e]
                if erule != con.rule:
                    rep.err('event', 'event %d: rule %r but constraint %s has rule %r' % (e, erule, cid, con.rule))
                if eins != want_in:
                    rep.err('in', 'event %d (%s on %s.%s): in = %r, latest events of the domains read = %r'
                            % (e, cid, enode, edom, eins, want_in))
                got = None
                if k is not None:
                    kind = keys[k][1]
                    got = digest(kind, new[k])
                    if got != edg:
                        rep.err('digest', lambda e=e, k=k, got=got, edg=edg: (
                            'event %d: constraint %s, target %s.%s: digest %s expected, %s obtained; '
                            'obtained domain: %s; inputs: %s'
                            % (e, con.describe(), keys[k][0], keys[k][1], edg, got,
                               short(CANON[keys[k][1]](new[k])), self._inputs(keys, cur))))
                    if is_empty(kind, new[k]):
                        rep.err('empty', 'event %d: constraint %s makes %s.%s empty'
                                % (e, con.describe(), keys[k][0], keys[k][1]))
                self._record(e, con, (enode, edom), tin, (new[k], got) if k is not None else None)
            for k in changed:
                state[keys[k]] = new[k]
            for e, k in pairs:
                key = (events[e][2], events[e][3])
                last[key] = e
                if k is not None:
                    d = new[k]
                    found = pins_of(key[1], d)
                    for inv in found:
                        if (key[0], inv) not in self.pin_event:
                            self.pin_event[(key[0], inv)] = e
            i = j
        return self

    def _record(self, e, con, key, tin, new):
        self.ev_con.append(con)
        self.ev_key.append(key)
        self.ev_in.append(tin)
        if self.keep_text:
            if new is None:
                d = self.state.get(key) or TOP.get(key[1], U_TOP)
                self.ev_text.append(statement(key[1], d, self.limit) if key[1] in TOP else '?')
            else:
                self.ev_text.append(statement(key[1], new[0], self.limit, new[1]))

    def _inputs(self, keys, cur):
        return '; '.join('%s.%s = %s' % (k[0], k[1], short(CANON[k[1]](d))) for k, d in zip(keys, cur))

    def domain(self, node, kind):
        return self.state.get((node, kind)) or TOP[kind]

    def pins(self, node):
        out = {}
        for kind in ('F', 'C', 'U'):
            d = self.state.get((node, kind))
            if d is not None:
                out.update(pins_of(kind, d))
        return out

    # ---- chains ---------------------------------------------------------------------
    def closure(self, event):
        """sorted ancestor closure of an event through `in`"""
        ev_in = self.ev_in
        seen = {event}
        stack = [event]
        while stack:
            for j in ev_in[stack.pop()]:
                if j not in seen:
                    seen.add(j)
                    stack.append(j)
        return sorted(seen)

    def chain_text(self, node, pins):
        per = {}
        memo = {}
        for inv in INVARIANTS:
            if inv in pins:
                pe = self.pin_event[(node, inv)]
                if pe not in memo:
                    memo[pe] = self.closure(pe)
                per[inv] = memo[pe]
        union = sorted(set().union(*memo.values())) if memo else []
        num = {e: k + 1 for k, e in enumerate(union)}
        lines = ['# chains for %s' % node]
        for e in union:
            con = self.ev_con[e]
            if con is None:
                rule, nodes, par = '?', '?', '{}'
            else:
                if con.partext is None:
                    con.partext = json.dumps(con.par, sort_keys=True, separators=(',', ':'))
                rule, nodes, par = con.rule, ','.join(con.nodes), con.partext
            key = self.ev_key[e]
            lines.append('%d. e%d %s nodes=%s par=%s -> %s.%s: %s | in: %s' % (
                num[e], e, rule, nodes, par, key[0], key[1], self.ev_text[e],
                ','.join(str(num[j]) for j in self.ev_in[e]) or '-'))
        for inv in INVARIANTS:
            if inv in per:
                lines.append('== %s = %d : pinned at %d ; chain %s' % (
                    inv, pins[inv], num[self.pin_event[(node, inv)]], ','.join(str(num[e]) for e in per[inv])))
        return '\n'.join(lines) + '\n'


# ======================================================================================
# the individual checks
# ======================================================================================
def load_constraints(directory, rep):
    cons = {}
    for rec in read_jsonl(directory, 'constraints.jsonl'):
        try:
            con = Con(rec)
        except Exception as ex:
            rep.err('constraint', 'malformed constraint %s: %s' % (short(json.dumps(rec), 200), ex))
            continue
        if con.cid in cons:
            rep.err('constraint', 'duplicate constraint id %s' % con.cid)
        cons[con.cid] = con
    return cons


def load_events(directory, rep):
    events = []
    intern = sys.intern
    for rec in read_jsonl(directory, 'events.jsonl'):
        if rec.get('id') != len(events):
            rep.err('event', 'event ids are not consecutive from 0: line %d has id %r' % (len(events), rec.get('id')))
        events.append((rec['c'], rec['rule'], intern(rec['node']), intern(rec['dom']), rec['in'], rec['dg']))
    return events


def check_knots(directory, replay, rep):
    """c. final domains, pins, pin events, last events, chain names.  Returns the node records
    reduced to what the later checks need: node -> (domains json, pins, chain)."""
    knots = {}
    order = []
    for rec in read_jsonl(directory, 'knots.jsonl'):
        node = rec['node']
        if node in knots:
            rep.err('knots', 'node %s occurs twice in knots.jsonl' % node)
            continue
        order.append(node)
        doms = rec.get('domains') or {}
        knots[node] = (doms, rec.get('pins') or {}, rec.get('chain'))
        for kind in ('F', 'C', 'U'):
            mine = json.loads(CANON[kind](replay.domain(node, kind)))
            if doms.get(kind) != mine:
                rep.err('final', lambda kind=kind, mine=mine: (
                    '%s.%s: knots.jsonl has %s, the replay ends with %s'
                    % (node, kind, short(json.dumps(doms.get(kind), sort_keys=True, separators=(',', ':'))),
                       short(json.dumps(mine, sort_keys=True, separators=(',', ':'))))))
        pins = replay.pins(node)
        if (rec.get('pins') or {}) != pins:
            rep.err('pin', '%s: pins %r in knots.jsonl, %r from the replay' % (node, rec.get('pins'), pins))
        pev = {inv: replay.pin_event.get((node, inv)) for inv in pins}
        if (rec.get('pin_events') or {}) != pev:
            rep.err('pin_event', '%s: pin_events %r in knots.jsonl, %r from the replay'
                    % (node, rec.get('pin_events'), pev))
        lev = {kind: replay.last[(node, kind)] for kind in ('F', 'C', 'U') if (node, kind) in replay.last}
        if (rec.get('last_events') or {}) != lev:
            rep.err('last_event', '%s: last_events %r in knots.jsonl, %r from the replay'
                    % (node, rec.get('last_events'), lev))
        want = ('chains/%s.txt' % chain_file_name(node)) if pins else None
        if rec.get('chain') != want:
            rep.err('chain_name', '%s: chain %r in knots.jsonl, expected %r' % (node, rec.get('chain'), want))
    for (node, kind) in replay.state:
        if node not in knots:
            rep.err('final', 'node %s has events on %s but is not in knots.jsonl' % (node, kind))
    return knots, order


def check_chains(directory, replay, order, rep):
    """d. rebuild every chain file and compare byte for byte."""
    cdir = os.path.join(directory, 'chains')
    same = different = extra = 0
    expected = {}
    for node in order:
        if not replay.pins(node):
            continue
        fn = chain_file_name(node) + '.txt'
        if fn in expected:
            rep.err('chain', 'nodes %s and %s share the chain file %s' % (expected[fn], node, fn))
            different += 1
            continue
        expected[fn] = node
    seen = set()
    for fn, data in chain_sources(cdir):
        if fn in seen:
            rep.err('chain', 'chain file %s occurs twice' % fn)
            different += 1
            continue
        seen.add(fn)
        node = expected.get(fn)
        if node is None:
            rep.err('chain', 'chain file %s does not belong to a node with a pin' % fn)
            extra += 1
            continue
        try:
            text = replay.chain_text(node, replay.pins(node)).encode('utf-8')
        except KeyError as ex:
            rep.err('chain', 'chain of %s cannot be built: no pin event %s' % (node, ex))
            different += 1
            continue
        if data == text:
            same += 1
        else:
            different += 1
            rep.err('chain', lambda fn=fn, data=data, text=text:
                    'chain file %s differs from the replay: %s' % (fn, first_difference(data, text)))
    for fn in sorted(set(expected) - seen):
        rep.err('chain', 'chain file %s of node %s is missing' % (fn, expected[fn]))
        different += 1
    return same, different, extra


def first_difference(data, text):
    a = data.decode('utf-8', 'replace').split('\n')
    b = text.decode('utf-8', 'replace').split('\n')
    for k in range(max(len(a), len(b))):
        x = a[k] if k < len(a) else '<end of file>'
        y = b[k] if k < len(b) else '<end of file>'
        if x != y:
            return 'line %d: file has %r, rebuilt %r' % (k + 1, short(x, 200), short(y, 200))
    return 'same lines, different bytes'


def check_csv(directory, knots, rep):
    """e. knots.csv against knots.jsonl."""
    paths = file_parts(directory, 'knots.csv')
    if not paths:
        rep.err('csv', 'knots.csv is missing')
        return 0
    rows = 0
    seen = set()
    for path in paths:
        rows += check_csv_part(path, knots, seen, rep)
    for node in knots:
        if node not in seen:
            rep.err('csv', 'node %s of knots.jsonl is not in knots.csv' % node)
    return rows


def check_csv_part(path, knots, seen, rep):
    rows = 0
    with open_text(path, newline='') as f:
        rd = csv.DictReader(f)
        need = ['node'] + ['%s_%s' % (inv, x) for inv in INVARIANTS for x in ('pin', 'lo', 'hi')]
        missing = [c for c in need if c not in (rd.fieldnames or [])]
        if missing:
            rep.err('csv', '%s has no column(s) %s' % (os.path.basename(path), ', '.join(missing)))
            return 0
        for row in rd:
            rows += 1
            node = row['node']
            if node in seen:
                rep.err('csv', 'node %s occurs twice in knots.csv' % node)
                continue
            seen.add(node)
            if node not in knots:
                rep.err('csv', 'node %s of knots.csv is not in knots.jsonl' % node)
                continue
            doms, pins, _ = knots[node]
            cache = {}
            for inv in INVARIANTS:
                kind = INV_DOM[inv]
                if kind not in cache:
                    try:
                        cache[kind] = from_json(kind, doms[kind])
                    except Exception:
                        cache[kind] = None
                if cache[kind] is None:
                    rep.err('csv', '%s: domain %s of knots.jsonl cannot be read' % (node, kind))
                    continue
                lo, hi = projection(kind, cache[kind], inv)
                for col, want in (('%s_pin' % inv, pins.get(inv)), ('%s_lo' % inv, lo), ('%s_hi' % inv, hi)):
                    cell = row[col]
                    try:
                        got = None if cell == '' else int(cell)
                    except ValueError:
                        got = cell
                    if got != want:
                        rep.err('csv', '%s: column %s is %r, knots.jsonl gives %r' % (node, col, cell, want))
                if inv in pins and (lo != pins[inv] or hi != pins[inv]):
                    rep.err('csv', '%s: pin %s = %r but the projection of the domain is [%r, %r]'
                            % (node, inv, pins[inv], lo, hi))
    return rows


def check_edges(directory, cons, used, rep):
    """f. edge ids used as `ref`."""
    ids = set()
    if jsonl_parts(directory, 'edges.jsonl'):
        for rec in read_jsonl(directory, 'edges.jsonl'):
            if rec.get('id') in ids:
                rep.err('edge', 'duplicate edge id %r' % rec.get('id'))
            ids.add(rec.get('id'))
    refs = 0
    unused_bad = 0
    for cid, con in cons.items():
        if isinstance(con.ref, str):
            if cid in used:
                refs += 1
                if con.ref not in ids:
                    rep.err('edge', 'constraint %s (used by an event) refers to edge %r, not in edges.jsonl'
                            % (cid, con.ref))
            elif con.ref not in ids:
                unused_bad += 1
    return len(ids), refs, unused_bad


# ======================================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description='Independent checker of an export directory (see FORMAT.md).')
    ap.add_argument('export_dir', nargs='?', default=None, help='export directory (default: ../export next to '
                    'this file, or ./export)')
    ap.add_argument('--max-errors', type=int, default=20, metavar='N',
                    help='print at most N individual mismatches of each kind (default 20)')
    ap.add_argument('--no-chains', action='store_true', help='skip the rebuild of the chain files (step d)')
    ap.add_argument('--strict', action='store_true', help='treat the warnings as failures')
    args = ap.parse_args(argv)
    directory = args.export_dir
    if directory is None:
        here = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'export')
        directory = 'export' if os.path.isdir('export') else here
    if not os.path.isdir(directory):
        print('error: %s is not a directory' % directory)
        return 2
    t0 = time.time()
    rep = Report(max(args.max_errors, 0))
    print('checking %s' % directory)

    bad = convention_tests()
    if bad:
        for b in bad:
            print('CONVENTION TEST FAILED: %s' % b)
        return 2

    try:
        with open(os.path.join(directory, 'parameters.json'), encoding='utf-8') as f:
            params = json.load(f)
        limit = params['max_statement_text']
        SLOPE_SETS.clear()
        for k, v in (params.get('slope_sets') or {}).items():
            SLOPE_SETS[k] = [(p, q) for p, q in v]
        cons = load_constraints(directory, rep)
        events = load_events(directory, rep)
    except (IOError, OSError, KeyError, ValueError) as ex:
        print('error: cannot load the export: %s: %s' % (type(ex).__name__, ex))
        return 2
    print('loaded %d constraints, %d events (%.1f s)' % (len(cons), len(events), time.time() - t0))

    replay = Replay(cons, limit, rep, keep_text=not args.no_chains).run(events)
    print('replayed %d events in %d applications (%.1f s)' % (len(events), replay.applications, time.time() - t0))

    try:
        knots, order = check_knots(directory, replay, rep)
    except (IOError, OSError, KeyError, ValueError) as ex:
        print('error: cannot load knots.jsonl: %s: %s' % (type(ex).__name__, ex))
        return 2
    print('compared %d nodes of knots.jsonl (%.1f s)' % (len(knots), time.time() - t0))

    same = different = extra = 0
    if not args.no_chains:
        same, different, extra = check_chains(directory, replay, order, rep)
        print('compared %d chain files (%.1f s)' % (same + different, time.time() - t0))
    rows = check_csv(directory, knots, rep)
    n_edges, n_refs, unused_bad = check_edges(directory, cons, replay.used_cons, rep)

    npins = sum(len(replay.pins(n)) for n in order)
    print()
    print('SUMMARY')
    print('  events checked                : %d (constraints: %d, used by events: %d, applications: %d)'
          % (len(events), len(cons), len(replay.used_cons), replay.applications))
    print('  digest mismatches             : %d' % rep.n('digest'))
    print('  `in` mismatches               : %d' % rep.n('in'))
    print('  targets that do not change    : %d' % rep.n('unchanged'))
    print('  other event/constraint errors : %d' % (rep.n('event') + rep.n('constraint')))
    print('  empty domains                 : %d' % rep.n('empty'))
    print('  final-domain mismatches       : %d (nodes: %d)' % (rep.n('final') + rep.n('knots'), len(knots)))
    print('  pin mismatches                : %d (pins: %d)' % (rep.n('pin'), npins))
    print('  pin-event mismatches          : %d' % rep.n('pin_event'))
    print('  last-event mismatches         : %d' % rep.n('last_event'))
    print('  chain-name mismatches         : %d' % rep.n('chain_name'))
    if args.no_chains:
        print('  chain files                   : not compared (--no-chains)')
    else:
        print('  chain files identical         : %d' % same)
        print('  chain files different         : %d (missing or different: %d, unexpected files: %d)'
              % (different + extra, different, extra))
    print('  csv mismatches                : %d (rows: %d)' % (rep.n('csv'), rows))
    print('  unresolved edges              : %d (edge refs of event constraints: %d, edges: %d)'
          % (rep.n('edge'), n_refs, n_edges))
    warnings = 0
    if not (unused_bad or WARN['lossy_intersect'] or WARN['mixed_lattice']):
        print('  warnings                      : 0')
    if unused_bad:
        warnings += 1
        print('  WARNING: %d constraints that no event uses refer to edges missing from edges.jsonl' % unused_bad)
    if WARN['lossy_intersect']:
        warnings += 1
        print('  WARNING: %d RSet intersections where the documented rule (FORMAT.md 2.1) drops values common '
              'to both sets (an up-ray overlapping a down-ray)' % WARN['lossy_intersect'])
    ok = rep.total() == 0 and not (args.strict and warnings)
    print('  time                          : %.1f s' % (time.time() - t0))
    print('RESULT: %s' % ('OK' if ok else 'FAILED'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
