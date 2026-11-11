"""Domains of the solver (section 8).

RSet   a set of integers on the lattice step*Z: finitely many explicit values, optionally
       an upward ray {up, up+step, ...} and a downward ray {down, down-step, ...}.
Dom2   admissible (M, r_2) pairs.   'box' mode: M in [mlo, mhi] on the lattice (ends may be
       infinite), r_2 >= rlo (None: unbounded below) and r_2 >= |M| if absM.
       'enum' mode: finitely many M, each with an RSet of r_2 values.
DomC   admissible (tau^#, nu^#, r_0) triples.  'box' mode: intervals for tau and nu (ends may
       be infinite), |2 tau - nu| <= 1 if c4, r_0 >= r0lo (None: unbounded below).
       'enum' mode: finitely many (tau, nu), each with an RSet of r_0 values.
DomU   interval of integers for upsilon (ends may be infinite).
All objects are immutable; None encodes an infinite end.
"""
from __future__ import annotations

import hashlib
import json


def _up(x, step):
    """Smallest lattice point >= x."""
    return -((-x) // step) * step


def _dn(x, step):
    return (x // step) * step


class RSet:
    __slots__ = ('vals', 'up', 'down', 'step')

    def __init__(self, vals=(), up=None, down=None, step=1):
        vs = sorted(set(vals))
        if up is not None:
            vs = [v for v in vs if v < up]
        if down is not None:
            vs = [v for v in vs if v > down]
        s = set(vs)
        if up is not None:
            while up - step in s:
                up -= step
                s.discard(up)
        if down is not None:
            while down + step in s:
                down += step
                s.discard(down)
        if up is not None and down is not None and down + step >= up:
            up, down, s = 0, -step, set()
        self.vals = tuple(sorted(s))
        self.up = up
        self.down = down
        self.step = step

    # -- queries -------------------------------------------------------
    def __contains__(self, v):
        if v % self.step:
            return False
        if self.up is not None and v >= self.up:
            return True
        if self.down is not None and v <= self.down:
            return True
        return v in self.vals

    def is_empty(self):
        return not self.vals and self.up is None and self.down is None

    def finite(self):
        return self.up is None and self.down is None

    def size(self):
        return len(self.vals) if self.finite() else None

    def min(self):
        """Minimum (None if unbounded below); undefined on the empty set."""
        if self.down is not None:
            return None
        if self.vals:
            return self.vals[0]
        return self.up

    def max(self):
        if self.up is not None:
            return None
        if self.vals:
            return self.vals[-1]
        return self.down

    def __eq__(self, o):
        return (self.vals, self.up, self.down, self.step) == (o.vals, o.up, o.down, o.step)

    def __hash__(self):
        return hash((self.vals, self.up, self.down, self.step))

    # -- narrowing -----------------------------------------------------
    def ge(self, lo):
        if lo is None:
            return self
        lo = _up(lo, self.step)
        vals = [v for v in self.vals if v >= lo]
        up = self.up if self.up is None else max(self.up, lo)
        down = self.down
        if down is not None:
            vals += list(range(lo, down + 1, self.step))
            down = None
        return RSet(vals, up, down, self.step)

    def le(self, hi):
        if hi is None:
            return self
        hi = _dn(hi, self.step)
        vals = [v for v in self.vals if v <= hi]
        down = self.down if self.down is None else min(self.down, hi)
        up = self.up
        if up is not None:
            vals += list(range(up, hi + 1, self.step))
            up = None
        return RSet(vals, up, down, self.step)

    def only(self, values):
        """Intersection with a finite set of values."""
        return RSet([v for v in values if v in self], None, None, self.step)

    def remove(self, v):
        if v not in self:
            return self
        vals = [x for x in self.vals if x != v]
        up, down = self.up, self.down
        if up is not None and v >= up:
            vals += list(range(up, v, self.step))
            up = v + self.step
        elif down is not None and v <= down:
            vals += list(range(v + self.step, down + 1, self.step))
            down = v - self.step
        return RSet(vals, up, down, self.step)

    def intersect(self, o):
        vals = [v for v in self.vals if v in o] + [v for v in o.vals if v in self]
        up = None
        if self.up is not None and o.up is not None:
            up = max(self.up, o.up)
        down = None
        if self.down is not None and o.down is not None:
            down = min(self.down, o.down)
        return RSet(vals, up, down, self.step)

    def union(self, o):
        vals = list(self.vals) + list(o.vals)
        ups = [x for x in (self.up, o.up) if x is not None]
        downs = [x for x in (self.down, o.down) if x is not None]
        up = min(ups) if ups else None
        down = max(downs) if downs else None
        return RSet(vals, up, down, self.step)

    # -- io ------------------------------------------------------------
    def to_json(self):
        d = {'v': list(self.vals)}
        if self.up is not None:
            d['up'] = self.up
        if self.down is not None:
            d['dn'] = self.down
        return d

    @classmethod
    def from_json(cls, d, step):
        return cls(d.get('v', ()), d.get('up'), d.get('dn'), step)

    def text(self):
        parts = []
        if self.down is not None:
            parts.append('<=%d' % self.down)
        parts += [str(v) for v in self.vals]
        if self.up is not None:
            parts.append('>=%d' % self.up)
        return '{' + ','.join(parts) + '}'


EMPTY = 'empty'


def _digest(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:12]


def _imin(a, b):          # lower ends: None = -inf
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def _imax(a, b):          # upper ends: None = +inf
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)


# ----------------------------------------------------------------------
class Dom2:
    """Domain of (M, r_2)."""
    __slots__ = ('step', 'box', 'items')
    kind = 'F'

    def __init__(self, step, box=None, items=None):
        self.step = step
        self.box = box
        self.items = items
        if box is not None:
            mlo, mhi, rlo, absM = box
            if mlo is not None and mhi is not None:
                its = {}
                for m in range(_up(mlo, step), mhi + 1, step):
                    its[m] = self._ray(m, rlo, absM)
                self.box = None
                self.items = its
        if self.items is not None:
            self.items = {m: r for m, r in sorted(self.items.items()) if not r.is_empty()}

    def _ray(self, m, rlo, absM):
        lo = rlo
        if absM:
            lo = abs(m) if lo is None else max(lo, abs(m))
        if lo is None:
            return RSet((), 0, -self.step, self.step)
        return RSet((), _up(lo, self.step), None, self.step)

    @classmethod
    def top(cls, step=1):
        return cls(step, box=(None, None, None, False))

    def is_empty(self):
        return self.items is not None and not self.items

    def is_enum(self):
        return self.items is not None

    def m_bounds(self):
        if self.items is not None:
            ks = list(self.items)
            return (ks[0], ks[-1]) if ks else (0, -1)
        return self.box[0], self.box[1]

    def m_set(self):
        return list(self.items) if self.items is not None else None

    def tighten_m(self, lo=None, hi=None):
        if self.items is not None:
            return Dom2(self.step, items={m: r for m, r in self.items.items()
                                          if (lo is None or m >= lo) and (hi is None or m <= hi)})
        mlo, mhi, rlo, absM = self.box
        nlo, nhi = _imin(mlo, lo), _imax(mhi, hi)
        if nlo is not None:
            nlo = _up(nlo, self.step)
        if nhi is not None:
            nhi = _dn(nhi, self.step)
        if nlo is not None and nhi is not None and nlo > nhi:
            return Dom2(self.step, items={})
        return Dom2(self.step, box=(nlo, nhi, rlo, absM))

    def restrict_m(self, ms):
        """Keep only M values in the finite set ms (enum mode) or tighten the box to its hull."""
        ms = sorted(set(m for m in ms if m % self.step == 0))
        if self.items is not None:
            s = set(ms)
            return Dom2(self.step, items={m: r for m, r in self.items.items() if m in s})
        if not ms:
            return Dom2(self.step, items={})
        mlo, mhi, rlo, absM = self.box
        its = {}
        for m in ms:
            if (mlo is None or m >= mlo) and (mhi is None or m <= mhi):
                its[m] = self._ray(m, rlo, absM)
        return Dom2(self.step, items=its)

    def map_r(self, f):
        """Enum mode: replace the RSet of every M by f(M, RSet)."""
        return Dom2(self.step, items={m: f(m, r) for m, r in self.items.items()})

    def __eq__(self, o):
        return self.to_json() == o.to_json()

    def to_json(self):
        if self.items is not None:
            return {'s': self.step, 'e': [[m, r.to_json()] for m, r in self.items.items()]}
        mlo, mhi, rlo, absM = self.box
        return {'s': self.step, 'b': [mlo, mhi, rlo, bool(absM)]}

    @classmethod
    def from_json(cls, d):
        if 'e' in d:
            return cls(d['s'], items={m: RSet.from_json(r, d['s']) for m, r in d['e']})
        mlo, mhi, rlo, absM = d['b']
        return cls(d['s'], box=(mlo, mhi, rlo, absM))

    def digest(self):
        return _digest(self.to_json())

    # projections -------------------------------------------------------
    def pin(self, coord):
        if self.items is None or not self.items:
            return None
        if coord == 'M':
            return next(iter(self.items)) if len(self.items) == 1 else None
        vals = set()
        for r in self.items.values():
            if not r.finite():
                return None
            vals.update(r.vals)
        return next(iter(vals)) if len(vals) == 1 else None

    def bounds(self, coord):
        """(lo, hi) of the projection, None for infinite ends."""
        if coord == 'M':
            if self.items is not None:
                return self.m_bounds() if self.items else (None, None)
            return self.box[0], self.box[1]
        if self.items is None:
            mlo, mhi, rlo, absM = self.box
            lo = rlo
            if absM:
                lo = 0 if lo is None else max(lo, 0)
            return lo, None
        if not self.items:
            return None, None
        los = [r.min() for r in self.items.values()]
        his = [r.max() for r in self.items.values()]
        return (None if any(x is None for x in los) else min(los),
                None if any(x is None for x in his) else max(his))

    def tuples(self, limit=20):
        """Finite joint domain as a list of pairs, or None if infinite or larger than limit."""
        if self.items is None:
            return None
        out = []
        for m, r in self.items.items():
            if not r.finite():
                return None
            out.extend((m, v) for v in r.vals)
            if len(out) > limit:
                return None
        return out

    def text(self):
        if self.items is None:
            mlo, mhi, rlo, absM = self.box
            return 'M in [%s,%s]; r_2 >= %s%s' % ('-inf' if mlo is None else mlo, 'inf' if mhi is None else mhi,
                                                  '-inf' if rlo is None else rlo, ', |M|' if absM else '')
        if not self.items:
            return 'EMPTY'
        return ' '.join('M=%d:r_2%s' % (m, r.text()) for m, r in self.items.items())


# ----------------------------------------------------------------------
class DomC:
    """Domain of (tau^#, nu^#, r_0)."""
    __slots__ = ('box', 'items')
    kind = 'C'

    def __init__(self, box=None, items=None):
        self.box = box
        self.items = items
        if box is not None:
            tlo, thi, nlo, nhi, c4, r0lo = box
            if c4:
                # propagate between tau and nu:  2 tau - 1 <= nu <= 2 tau + 1
                if tlo is not None:
                    nlo = _imin(nlo, 2 * tlo - 1)
                if thi is not None:
                    nhi = _imax(nhi, 2 * thi + 1)
                if nlo is not None:
                    tlo = _imin(tlo, -((-(nlo - 1)) // 2))
                if nhi is not None:
                    thi = _imax(thi, (nhi + 1) // 2)
            self.box = (tlo, thi, nlo, nhi, c4, r0lo)
            if None not in (tlo, thi, nlo, nhi):
                its = {}
                ray = RSet((), 0, -1, 1) if r0lo is None else RSet((), r0lo, None, 1)
                for t in range(tlo, thi + 1):
                    for n in range(nlo, nhi + 1):
                        if not c4 or abs(2 * t - n) <= 1:
                            its[(t, n)] = ray
                self.box = None
                self.items = its
        if self.items is not None:
            self.items = {k: r for k, r in sorted(self.items.items()) if not r.is_empty()}

    @classmethod
    def top(cls):
        return cls(box=(None, None, None, None, False, None))

    def is_empty(self):
        return self.items is not None and not self.items

    def is_enum(self):
        return self.items is not None

    def tighten(self, tlo=None, thi=None, nlo=None, nhi=None):
        if self.items is not None:
            return DomC(items={(t, n): r for (t, n), r in self.items.items()
                               if (tlo is None or t >= tlo) and (thi is None or t <= thi)
                               and (nlo is None or n >= nlo) and (nhi is None or n <= nhi)})
        a, b, c, d, c4, r0lo = self.box
        a, b, c, d = _imin(a, tlo), _imax(b, thi), _imin(c, nlo), _imax(d, nhi)
        if (a is not None and b is not None and a > b) or (c is not None and d is not None and c > d):
            return DomC(items={})
        return DomC(box=(a, b, c, d, c4, r0lo))

    def filter_keys(self, pred):
        return DomC(items={k: r for k, r in self.items.items() if pred(k)})

    def map_r(self, f):
        return DomC(items={k: f(k, r) for k, r in self.items.items()})

    def tau_bounds(self):
        if self.items is not None:
            ts = [t for t, n in self.items]
            return (min(ts), max(ts)) if ts else (None, None)
        return self.box[0], self.box[1]

    def nu_bounds(self):
        if self.items is not None:
            ns = [n for t, n in self.items]
            return (min(ns), max(ns)) if ns else (None, None)
        return self.box[2], self.box[3]

    def __eq__(self, o):
        return self.to_json() == o.to_json()

    def to_json(self):
        if self.items is not None:
            return {'e': [[t, n, r.to_json()] for (t, n), r in self.items.items()]}
        tlo, thi, nlo, nhi, c4, r0lo = self.box
        return {'b': [tlo, thi, nlo, nhi, bool(c4), r0lo]}

    @classmethod
    def from_json(cls, d):
        if 'e' in d:
            return cls(items={(t, n): RSet.from_json(r, 1) for t, n, r in d['e']})
        tlo, thi, nlo, nhi, c4, r0lo = d['b']
        return cls(box=(tlo, thi, nlo, nhi, c4, r0lo))

    def digest(self):
        return _digest(self.to_json())

    def pin(self, coord):
        if self.items is None or not self.items:
            return None
        if coord == 'tau':
            s = {t for t, n in self.items}
            return next(iter(s)) if len(s) == 1 else None
        if coord == 'nu':
            s = {n for t, n in self.items}
            return next(iter(s)) if len(s) == 1 else None
        vals = set()
        for r in self.items.values():
            if not r.finite():
                return None
            vals.update(r.vals)
        return next(iter(vals)) if len(vals) == 1 else None

    def bounds(self, coord):
        if coord == 'tau':
            return self.tau_bounds()
        if coord == 'nu':
            return self.nu_bounds()
        if self.items is None:
            return self.box[5], None
        if not self.items:
            return None, None
        los = [r.min() for r in self.items.values()]
        his = [r.max() for r in self.items.values()]
        return (None if any(x is None for x in los) else min(los),
                None if any(x is None for x in his) else max(his))

    def tuples(self, limit=20):
        if self.items is None:
            return None
        out = []
        for (t, n), r in self.items.items():
            if not r.finite():
                return None
            out.extend((t, n, v) for v in r.vals)
            if len(out) > limit:
                return None
        return out

    def text(self):
        if self.items is None:
            f = lambda x, s: s if x is None else str(x)
            tlo, thi, nlo, nhi, c4, r0lo = self.box
            return 'tau in [%s,%s]; nu in [%s,%s]%s; r_0 >= %s' % (
                f(tlo, '-inf'), f(thi, 'inf'), f(nlo, '-inf'), f(nhi, 'inf'),
                '; |2tau-nu|<=1' if c4 else '', f(r0lo, '-inf'))
        if not self.items:
            return 'EMPTY'
        return ' '.join('(tau=%d,nu=%d):r_0%s' % (t, n, r.text()) for (t, n), r in self.items.items())


# ----------------------------------------------------------------------
class DomU:
    """Interval domain of upsilon."""
    __slots__ = ('lo', 'hi')
    kind = 'U'

    def __init__(self, lo=None, hi=None):
        self.lo, self.hi = lo, hi

    @classmethod
    def top(cls):
        return cls(None, None)

    def is_empty(self):
        return self.lo is not None and self.hi is not None and self.lo > self.hi

    def tighten(self, lo=None, hi=None):
        return DomU(_imin(self.lo, lo), _imax(self.hi, hi))

    def __eq__(self, o):
        return (self.lo, self.hi) == (o.lo, o.hi)

    def to_json(self):
        return {'u': [self.lo, self.hi]}

    @classmethod
    def from_json(cls, d):
        return cls(d['u'][0], d['u'][1])

    def digest(self):
        return _digest(self.to_json())

    def pin(self, coord='upsilon'):
        return self.lo if (self.lo is not None and self.lo == self.hi) else None

    def bounds(self, coord='upsilon'):
        return self.lo, self.hi

    def text(self):
        if self.is_empty():
            return 'EMPTY'
        return 'upsilon in [%s,%s]' % ('-inf' if self.lo is None else self.lo, 'inf' if self.hi is None else self.hi)


def dom_from_json(kind, d):
    return {'F': Dom2, 'C': DomC, 'U': DomU}[kind].from_json(d)


COORDS = {'M': ('F', 'M'), 'r_2': ('F', 'r'), 'nu': ('C', 'nu'), 'r_0': ('C', 'r'), 'tau': ('C', 'tau'),
          'upsilon': ('U', 'upsilon')}
