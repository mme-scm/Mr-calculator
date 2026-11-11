"""Planar knot diagrams.

A diagram with n crossings is a 4-valent planar map.  Crossing c has four
darts (c, 0..3) in counterclockwise order; darts 0 and 2 are the two ends of
the under strand, darts 1 and 3 the two ends of the over strand.  `adj` is the
fixed-point-free involution pairing the two darts of every edge.

PD convention (KnotInfo): a crossing is [a, b, c, d], a the incoming under
edge, then counterclockwise.  The under strand runs a -> c.  The over strand
runs d -> b at a positive crossing and b -> d at a negative one (right-hand
rule).  Edges are labelled 1..2n along the orientation.

Everything in this module is combinatorial and exact.
"""
from __future__ import annotations

import json
from collections import defaultdict


class DiagramError(Exception):
    pass


def parse_pd(s):
    """Parse a PD code given as a string or nested list into a list of 4-tuples."""
    if isinstance(s, str):
        t = s.replace('PD', '').replace('X', '').replace('(', '[').replace(')', ']')
        s = json.loads(t)
    return [tuple(int(x) for x in c) for c in s]


class Diagram:
    """Oriented knot diagram.  Build with from_pd or from_adj."""

    def __init__(self, n, adj, start=None):
        self.n = n
        self.adj = adj
        if n == 0:
            raise DiagramError('zero-crossing diagram')
        if len(adj) != 4 * n:
            raise DiagramError('adjacency does not cover all darts')
        for d, e in adj.items():
            if adj.get(e) != d or d == e:
                raise DiagramError('adjacency is not a fixed-point-free involution')
        self._orient(start if start is not None else (0, 0))
        self._faces()
        if len(self.faces) != n + 2:
            raise DiagramError('diagram is not planar/connected: %d faces for %d crossings'
                               % (len(self.faces), n))

    # ------------------------------------------------------------------
    @classmethod
    def from_pd(cls, pd):
        pd = parse_pd(pd)
        slots = defaultdict(list)
        for c, x in enumerate(pd):
            if len(x) != 4:
                raise DiagramError('crossing with %d entries' % len(x))
            for i, lab in enumerate(x):
                slots[lab].append((c, i))
        adj = {}
        for lab, ds in slots.items():
            if len(ds) != 2:
                raise DiagramError('label %r occurs %d times' % (lab, len(ds)))
            adj[ds[0]] = ds[1]
            adj[ds[1]] = ds[0]
        D = cls(len(pd), adj, start=(0, 0))
        # keep the given edge labels when they are 1..2n in order along the orientation
        m = 2 * D.n
        off = pd[0][0] - 1
        if all(1 <= pd[c][i] <= m and (D.label[(c, i)] - 1 + off) % m + 1 == pd[c][i]
               for c in range(D.n) for i in range(4)):
            if off:
                D._relabel(off)
        return D

    def _relabel(self, off):
        m = 2 * self.n
        sh = lambda x: (x - 1 + off) % m + 1
        self.label = {d: sh(l) for d, l in self.label.items()}
        self.head = {sh(l): d for l, d in self.head.items()}
        self.tail = {sh(l): d for l, d in self.tail.items()}
        self.left = {sh(l): f for l, f in self.left.items()}
        self.right = {sh(l): f for l, f in self.right.items()}

    # ------------------------------------------------------------------
    def _orient(self, start):
        n, adj = self.n, self.adj
        entry = {}          # dart -> index t of the edge arriving there (0-based)
        order = []
        d = start
        while True:
            if d in entry:
                break
            entry[d] = len(order)
            order.append(d)
            c, i = d
            d = adj[(c, (i + 2) % 4)]
        if d != start or len(order) != 2 * n:
            raise DiagramError('not a knot: traversal visits %d of %d strands' % (len(order), 2 * n))
        self.order = order            # entry darts in traversal order
        self.entry = entry
        self.under_in = [None] * n    # position of the incoming under dart
        self.over_in = [None] * n
        for (c, i) in order:
            if i % 2 == 0:
                if self.under_in[c] is not None:
                    raise DiagramError('under strand traversed twice')
                self.under_in[c] = i
            else:
                if self.over_in[c] is not None:
                    raise DiagramError('over strand traversed twice')
                self.over_in[c] = i
        self.sign = [1 if (self.over_in[c] - self.under_in[c]) % 4 == 3 else -1 for c in range(n)]
        # edge labels 1..2n: edge t+1 arrives at order[t]
        lab = {}
        for t, (c, i) in enumerate(order):
            lab[(c, i)] = t + 1
            lab[(c, (i + 2) % 4)] = (t + 1) % (2 * n) + 1
        self.label = lab
        # head / tail dart of every edge label
        self.head = {}
        self.tail = {}
        for t, (c, i) in enumerate(order):
            self.head[t + 1] = (c, i)
            self.tail[(t + 1) % (2 * n) + 1] = (c, (i + 2) % 4)

    def _faces(self):
        adj = self.adj
        face_of = {}
        faces = []
        for c in range(self.n):
            for i in range(4):
                if (c, i) in face_of:
                    continue
                f = len(faces)
                cyc = []
                d = (c, i)
                while d not in face_of:
                    face_of[d] = f
                    cyc.append(d)
                    cc, ii = d
                    d = adj[(cc, (ii + 1) % 4)]
                faces.append(cyc)
        self.faces = faces
        self.face_of = face_of       # corner (c, i) = wedge between darts i and i+1
        # left / right face of every oriented edge
        self.left = {}
        self.right = {}
        for lab, (c, i) in self.tail.items():
            self.right[lab] = face_of[(c, (i - 1) % 4)]
            self.left[lab] = face_of[(c, i)]

    # ------------------------------------------------------------------
    def pd(self):
        """PD code, crossing order preserved, labels 1..2n along the orientation."""
        out = []
        for c in range(self.n):
            p = self.under_in[c]
            out.append([self.label[(c, (p + j) % 4)] for j in range(4)])
        return out

    def writhe(self):
        return sum(self.sign)

    def edges(self):
        return list(range(1, 2 * self.n + 1))

    def dual_adjacency(self):
        """face -> list of (edge label, other face)."""
        g = defaultdict(list)
        for e in self.edges():
            l, r = self.left[e], self.right[e]
            if l != r:
                g[l].append((e, r))
                g[r].append((e, l))
        return g

    # ------------------------------------------------------------------
    def seifert_graph(self):
        """Return (number of Seifert circles, list of (circle, circle, sign) per crossing)."""
        n = self.n
        # Seifert circle of every edge label: at a crossing the incoming under edge is
        # joined to the outgoing over edge and the incoming over edge to the outgoing under edge.
        nxt = {}
        for c in range(n):
            pu, po = self.under_in[c], self.over_in[c]
            nxt[self.label[(c, pu)]] = self.label[(c, (po + 2) % 4)]
            nxt[self.label[(c, po)]] = self.label[(c, (pu + 2) % 4)]
        circ = {}
        k = 0
        for e in self.edges():
            if e in circ:
                continue
            x = e
            while x not in circ:
                circ[x] = k
                x = nxt[x]
            k += 1
        edges = []
        for c in range(n):
            pu, po = self.under_in[c], self.over_in[c]
            edges.append((circ[self.label[(c, pu)]], circ[self.label[(c, po)]], self.sign[c]))
        return k, edges

    def is_homogeneous(self):
        """Cromwell: every block of the Seifert graph has edges of one sign."""
        import networkx as nx
        k, edges = self.seifert_graph()
        G = nx.Graph()
        G.add_nodes_from(range(k))
        signs = defaultdict(set)
        for a, b, s in edges:
            if a == b:
                raise DiagramError('Seifert graph loop')
            G.add_edge(a, b)
            signs[frozenset((a, b))].add(s)
        for comp in nx.biconnected_component_edges(G):
            ss = set()
            for a, b in comp:
                ss |= signs[frozenset((a, b))]
            if len(ss) > 1:
                return False
        return True

    def is_alternating_diagram(self):
        """Along the knot, over and under passages alternate."""
        kinds = [i % 2 for (c, i) in self.order]
        m = len(kinds)
        return all(kinds[t] != kinds[(t + 1) % m] for t in range(m))


# ----------------------------------------------------------------------
# Builder: wire crossings together through real darts and virtual ports
# ----------------------------------------------------------------------
class Builder:
    def __init__(self, n=0):
        self.n = n
        self.conn = defaultdict(list)

    def new_crossing(self):
        self.n += 1
        return self.n - 1

    def connect(self, p, q):
        self.conn[p].append(q)
        self.conn[q].append(p)

    def adjacency(self):
        adj = {}
        for p, qs in self.conn.items():
            if p[0] == 'v':
                if len(qs) != 2:
                    raise DiagramError('virtual port %r has %d connections' % (p, len(qs)))
                continue
            if len(qs) != 1:
                raise DiagramError('dart %r has %d connections' % (p, len(qs)))
            prev, q = p, qs[0]
            steps = 0
            while q[0] == 'v':
                a, b = self.conn[q]
                if a == prev:
                    nxt = b
                elif b == prev:
                    nxt = a
                else:
                    raise DiagramError('inconsistent virtual port')
                prev, q = q, nxt
                steps += 1
                if steps > 10 ** 6:
                    raise DiagramError('virtual loop')
            adj[p] = q
        return adj

    def diagram(self, start=None):
        return Diagram(self.n, self.adjacency(), start=start)


# geometric crossing types for a braid drawn bottom to top
#   'pos': over strand runs bottom-left -> top-right (positive if both strands point up)
#   'neg': over strand runs bottom-right -> top-left
_ENDS = {
    'pos': {'BR': 0, 'TR': 1, 'TL': 2, 'BL': 3},
    'neg': {'BL': 0, 'BR': 1, 'TR': 2, 'TL': 3},
}


def _braid(b, cur, word):
    """Stack braid generators on the open ends cur[0..k-1] (left to right); returns new open ends."""
    cur = list(cur)
    for g in word:
        j = abs(g) - 1
        if g == 0 or j + 1 >= len(cur):
            raise DiagramError('bad braid generator %r' % g)
        x = b.new_crossing()
        e = _ENDS['pos' if g > 0 else 'neg']
        b.connect(cur[j], (x, e['BL']))
        b.connect(cur[j + 1], (x, e['BR']))
        cur[j] = (x, e['TL'])
        cur[j + 1] = (x, e['TR'])
    return cur


def from_adj_copy(D):
    b = Builder(D.n)
    seen = set()
    for d, e in D.adj.items():
        if d in seen:
            continue
        seen.add(d)
        seen.add(e)
        b.connect(d, e)
    return b


# ----------------------------------------------------------------------
# elementary operations on PD codes
# ----------------------------------------------------------------------
def normalise(pd):
    return Diagram.from_pd(pd).pd()


def writhe(pd):
    return Diagram.from_pd(pd).writhe()


def signs(pd):
    return list(Diagram.from_pd(pd).sign)


def _rotated(D, which, start_old=None):
    """Swap over/under at the crossings in `which` (a set of crossing indices)."""
    def new(d):
        c, i = d
        return (c, (i - 1) % 4) if c in which else d
    adj = {new(d): new(e) for d, e in D.adj.items()}
    start = new(D.order[0]) if start_old is None else new(start_old)
    return Diagram(D.n, adj, start=start)


def crossing_change(pd, idx):
    """Switch crossing number idx of the PD list; crossing order is preserved."""
    D = Diagram.from_pd(pd)
    return _rotated(D, {idx}).pd()


def mirror(pd):
    D = Diagram.from_pd(pd)
    return _rotated(D, set(range(D.n))).pd()


def braid_closure(word, strands=None):
    """PD code of the closure of a braid word (list of nonzero ints, sigma_i positive crossing)."""
    word = [int(g) for g in word]
    k = strands or (max(abs(g) for g in word) + 1)
    b = Builder()
    bottoms = [('v', 'b', j) for j in range(k)]
    tops = _braid(b, bottoms, word)
    for j in range(k):
        if tops[j] == bottoms[j]:
            raise DiagramError('braid strand %d has no crossing' % j)
        b.connect(tops[j], bottoms[j])
    D = b.diagram()
    return D.pd()


def braid_writhe(word):
    return sum(1 if g > 0 else -1 for g in word)


def torus_word(p, q):
    """Braid word of the positive torus knot T(p,q) on min(p,q) strands."""
    p, q = max(p, q), min(p, q)
    return [i for _ in range(p) for i in range(1, q)]


def torus_knot(p, q):
    return braid_closure(torus_word(p, q))


def connected_sum(pd1, pd2):
    D1, D2 = Diagram.from_pd(pd1), Diagram.from_pd(pd2)
    b = Builder(D1.n + D2.n)
    off = D1.n
    t1, h1 = D1.tail[1], D1.head[1]
    t2, h2 = D2.tail[1], D2.head[1]
    for d, e in D1.adj.items():
        if d < e and {d, e} != {t1, h1}:
            b.connect(d, e)
    sh = lambda d: (d[0] + off, d[1])
    for d, e in D2.adj.items():
        if d < e and {d, e} != {t2, h2}:
            b.connect(sh(d), sh(e))
    if t1 == h1 or t2 == h2:
        raise DiagramError('degenerate edge')
    b.connect(t1, sh(h2))
    b.connect(sh(t2), h1)
    return b.diagram(start=D1.order[0]).pd()


def pretzel(cols, positive_type='neg'):
    """P(a_1,...,a_k): vertical columns of a_i half-twists.

    positive_type is the geometric crossing type (in the column, drawn bottom to top) of a
    positive half-twist; it is fixed by the convention test P(1,1,1) = right-handed trefoil.
    """
    k = len(cols)
    b = Builder()
    for i, a in enumerate(cols):
        typ = positive_type if a > 0 else ('pos' if positive_type == 'neg' else 'neg')
        cur = [('v', 'bl', i), ('v', 'br', i)]
        cur = _braid(b, cur, [1 if typ == 'pos' else -1] * abs(a))
        b.connect(cur[0], ('v', 'tl', i))
        b.connect(cur[1], ('v', 'tr', i))
    for i in range(k):
        j = (i + 1) % k
        b.connect(('v', 'tr', i), ('v', 'tl', j))
        b.connect(('v', 'br', i), ('v', 'bl', j))
    return b.diagram().pd()


def cable(pd, r, s):
    """C_{r,s}(K): the curve r*mu + s*lambda (Seifert longitude) on the boundary of a
    neighbourhood of the knot with diagram pd; s >= 2 strands, gcd(r, s) = 1."""
    from math import gcd
    if s < 2 or gcd(r, s) != 1:
        raise DiagramError('bad cable parameters')
    D = Diagram.from_pd(pd)
    n, w = D.n, D.writhe()
    m = r - s * w
    b = Builder()
    X = [[[b.new_crossing() for _ in range(s)] for _ in range(s)] for _ in range(n)]  # X[c][i][j]
    # port of copy q of the edge with a given label at its head / tail crossing
    head_port, tail_port = {}, {}
    for c in range(n):
        pu, po = D.under_in[c], D.over_in[c]
        positive = D.sign[c] == 1
        # local frame: under strand south -> north; darts of a grid crossing:
        # 0 south, 1 east, 2 north, 3 west.  under copy i (west->east), over copy j.
        for i in range(s):
            js = list(range(s - 1, -1, -1)) if positive else list(range(s))   # south -> north
            for a_, b_ in zip(js, js[1:]):
                b.connect((X[c][i][a_], 2), (X[c][i][b_], 0))
            head_port[(D.label[(c, pu)], i)] = (X[c][i][js[0]], 0)
            tail_port[(D.label[(c, (pu + 2) % 4)], i)] = (X[c][i][js[-1]], 2)
        for j in range(s):
            for i in range(s - 1):
                b.connect((X[c][i][j], 1), (X[c][i + 1][j], 3))
            if positive:     # over strand runs west -> east
                head_port[(D.label[(c, po)], j)] = (X[c][0][j], 3)
                tail_port[(D.label[(c, (po + 2) % 4)], j)] = (X[c][s - 1][j], 1)
            else:            # east -> west
                head_port[(D.label[(c, po)], j)] = (X[c][s - 1][j], 1)
                tail_port[(D.label[(c, (po + 2) % 4)], j)] = (X[c][0][j], 3)
    for e in D.edges():
        if e == 1:
            unit = list(range(1, s)) if m > 0 else [-i for i in range(s - 1, 0, -1)]
            cur = _braid(b, [tail_port[(e, q)] for q in range(s)], unit * abs(m))
            for q in range(s):
                b.connect(cur[q], head_port[(e, q)])
        else:
            for q in range(s):
                b.connect(tail_port[(e, q)], head_port[(e, q)])
    return b.diagram().pd()


def cable_of_unknot(r, s):
    if r > 0:
        return torus_knot(r, s) if min(r, s) >= 2 else None
    return mirror(torus_knot(-r, s)) if min(-r, s) >= 2 else None


# ----------------------------------------------------------------------
# full twists along dual-graph paths
# ----------------------------------------------------------------------
def dual_paths(D, k, max_imbalance=None):
    """Simple paths in the dual graph crossing k edges, up to reversal.
    Yields (edges, faces, dirs) with dirs[i] = +1 if edge i runs left-to-right relative to the
    path and -1 if right-to-left."""
    g = D.dual_adjacency()
    out = []

    def rec(faces, edges):
        if len(edges) == k:
            if faces[0] < faces[-1] or (faces[0] == faces[-1]):
                out.append((tuple(edges), tuple(faces)))
            return
        for e, f in g[faces[-1]]:
            if f in faces:
                continue
            faces.append(f)
            edges.append(e)
            rec(faces, edges)
            faces.pop()
            edges.pop()

    for f0 in range(len(D.faces)):
        rec([f0], [])
    res = []
    seen = set()
    for edges, faces in out:
        key = min((edges, faces), (edges[::-1], faces[::-1]))
        if key in seen:
            continue
        seen.add(key)
        dirs = path_dirs(D, edges, faces)
        if max_imbalance is not None and abs(sum(dirs)) > max_imbalance:
            continue
        res.append((edges, faces, dirs))
    return res


def path_dirs(D, edges, faces):
    dirs = []
    for i, e in enumerate(edges):
        fa, fb = faces[i], faces[i + 1]
        if D.left[e] == fa and D.right[e] == fb:
            dirs.append(-1)      # head on the left of the path: right-to-left
        elif D.right[e] == fa and D.left[e] == fb:
            dirs.append(+1)      # left-to-right
        else:
            raise DiagramError('edge %d does not separate faces %d, %d' % (e, fa, fb))
    return tuple(dirs)


def path_faces(D, edges):
    """Recover the face sequence of a dual path from its ordered edge labels."""
    k = len(edges)
    cands = []
    for f0 in (D.left[edges[0]], D.right[edges[0]]):
        faces = [f0]
        ok = True
        for e in edges:
            l, r = D.left[e], D.right[e]
            if faces[-1] == l and r != l:
                faces.append(r)
            elif faces[-1] == r and r != l:
                faces.append(l)
            else:
                ok = False
                break
        if ok and len(set(faces)) == k + 1:
            cands.append(tuple(faces))
    if len(cands) != 1:
        raise DiagramError('edge sequence does not determine a simple dual path')
    return cands[0]


def full_twist_word(k, handed):
    unit = list(range(1, k)) if handed > 0 else [-i for i in range(1, k)]
    return unit * k


def twist(pd, edges, handed):
    """Full twist (handed = +1 right-handed, -1 left-handed) along the dual path crossing the
    listed edge labels in order.  Returns (new pd, a, b, dirs)."""
    D = Diagram.from_pd(pd)
    edges = tuple(edges)
    faces = path_faces(D, edges)
    dirs = path_dirs(D, edges, faces)
    k = len(edges)
    b = Builder(D.n)
    cut = set(edges)
    for e in D.edges():
        if e not in cut:
            b.connect(D.tail[e], D.head[e])
    bottoms, tops = [], []
    for e, d in zip(edges, dirs):
        if d == -1:     # right-to-left: tail below the path (path's right), head above
            bottoms.append(D.tail[e])
            tops.append(D.head[e])
        else:
            bottoms.append(D.head[e])
            tops.append(D.tail[e])
    cur = _braid(b, bottoms, full_twist_word(k, handed))
    for j in range(k):
        b.connect(cur[j], tops[j])
    # keep the orientation: start at an entry dart of an uncut edge if possible, else any
    start = None
    for e in D.edges():
        if e not in cut:
            start = D.head[e]
            break
    if start is None:
        e = edges[0]
        start = D.head[e] if dirs[0] == -1 else None
    newD = b.diagram(start=start) if start is not None else b.diagram()
    a = sum(1 for d in dirs if d == 1)
    bb = k - a
    return newD.pd(), a, bb, dirs


# ----------------------------------------------------------------------
# mutation
# ----------------------------------------------------------------------
def conway_circles(D, min_side=2):
    """Simple 4-cycles of the dual graph with at least min_side crossings on each side.
    Returns list of (edges (e1..e4 in cyclic order), faces (f0..f3), inside crossing set)
    where 'inside' is the side on the left of the cycle."""
    g = D.dual_adjacency()
    res = []
    seen = set()
    for f0 in range(len(D.faces)):
        for e1, f1 in g[f0]:
            if f1 <= f0:
                continue
            for e2, f2 in g[f1]:
                if f2 <= f0 or f2 == f1:
                    continue
                for e3, f3 in g[f2]:
                    if f3 <= f0 or f3 in (f1, f2):
                        continue
                    for e4, f4 in g[f3]:
                        if f4 != f0:
                            continue
                        edges = (e1, e2, e3, e4)
                        key = frozenset(edges)
                        if key in seen or len(key) != 4:
                            continue
                        seen.add(key)
                        side = circle_sides(D, edges, (f0, f1, f2, f3))
                        if side is None:
                            continue
                        left = {c for c, s in side.items() if s == 0}
                        right = {c for c, s in side.items() if s == 1}
                        if len(left) >= min_side and len(right) >= min_side:
                            res.append((edges, (f0, f1, f2, f3), left))
    return res


def circle_sides(D, edges, faces):
    """Side (0 = left of the cycle, 1 = right) of every crossing, or None if inconsistent."""
    side = {}
    cut = set(edges)
    k = len(edges)
    for i, e in enumerate(edges):
        fa, fb = faces[i], faces[(i + 1) % k]
        if D.left[e] == fa and D.right[e] == fb:
            l, r = D.head[e][0], D.tail[e][0]
        elif D.right[e] == fa and D.left[e] == fb:
            l, r = D.tail[e][0], D.head[e][0]
        else:
            return None
        for c, s in ((l, 0), (r, 1)):
            if side.get(c, s) != s:
                return None
            side[c] = s
    stack = list(side)
    while stack:
        c = stack.pop()
        for i in range(4):
            if D.label[(c, i)] in cut:
                continue
            c2 = D.adj[(c, i)][0]
            if c2 in side:
                if side[c2] != side[c]:
                    return None
            else:
                side[c2] = side[c]
                stack.append(c2)
    if len(side) != D.n:
        return None
    return side


_FLIP = [1, 0, 3, 2]
_MUT_PERM = {'z': [2, 3, 0, 1], 'x': [1, 0, 3, 2], 'y': [3, 2, 1, 0]}


def mutate(pd, edges, axis):
    """Mutation along the Conway circle crossing `edges` (cyclic order); the tangle on the
    left of the cycle is rotated by pi about `axis` in {'x','y','z'} ('z' perpendicular to
    the plane)."""
    D = Diagram.from_pd(pd)
    edges = tuple(edges)
    faces = None
    for f0 in (D.left[edges[0]], D.right[edges[0]]):
        fs = [f0]
        ok = True
        for e in edges:
            l, r = D.left[e], D.right[e]
            if fs[-1] == l and l != r:
                fs.append(r)
            elif fs[-1] == r and l != r:
                fs.append(l)
            else:
                ok = False
                break
        if ok and fs[-1] == fs[0] and len(set(fs[:-1])) == 4:
            cand = tuple(fs[:-1])
            side = circle_sides(D, edges, cand)
            if side is not None:
                faces = cand
                break
    if faces is None:
        raise DiagramError('edges do not form a Conway circle')
    side = circle_sides(D, edges, faces)
    inside = {c for c, s in side.items() if s == 0}
    flip = axis in ('x', 'y')

    def new(d):
        c, i = d
        if c in inside and flip:
            return (c, _FLIP[i])
        return d
    b = Builder(D.n)
    cut = set(edges)
    for e in D.edges():
        if e not in cut:
            b.connect(new(D.tail[e]), new(D.head[e]))
    ins, outs = [], []
    for e in edges:
        t, h = D.tail[e], D.head[e]
        if t[0] in inside and h[0] not in inside:
            ins.append(t)
            outs.append(h)
        elif h[0] in inside and t[0] not in inside:
            ins.append(h)
            outs.append(t)
        else:
            raise DiagramError('cut edge does not cross the circle')
    perm = _MUT_PERM[axis]
    for i in range(4):
        b.connect(outs[i], new(ins[perm[i]]))
    start = None
    for c in range(D.n):
        if c not in inside:
            start = (c, D.under_in[c])
            break
    return b.diagram(start=start).pd()


# ----------------------------------------------------------------------
# Reidemeister moves (crossing-increasing R1, R2 and R3), recorded
# ----------------------------------------------------------------------
def r1(pd, edge, under_first, loop_ccw):
    D = Diagram.from_pd(pd)
    b = from_adj_copy(D)
    t, h = D.tail[edge], D.head[edge]
    b.conn[t].remove(h)
    b.conn[h].remove(t)
    x = b.new_crossing()
    i = 0 if under_first else 1
    b.connect(t, (x, i))
    if loop_ccw:
        b.connect((x, (i + 2) % 4), (x, (i + 1) % 4))
        b.connect((x, (i + 3) % 4), h)
    else:
        b.connect((x, (i + 2) % 4), (x, (i + 3) % 4))
        b.connect((x, (i + 1) % 4), h)
    return b.diagram(start=D.order[0]).pd()


def face_boundary(D, f):
    """Boundary walk of face f (face on the right): list of (start dart, end dart) per edge."""
    out = []
    for (c, i) in D.faces[f]:
        s = (c, (i + 1) % 4)
        out.append((s, D.adj[s]))
    return out


def r2(pd, face, i, j, over):
    """Push a finger of the i-th boundary edge of `face` across the j-th boundary edge."""
    D = Diagram.from_pd(pd)
    bd = face_boundary(D, face)
    (es, ee), (fs, fe) = bd[i], bd[j]
    if len({es, ee, fs, fe}) != 4:
        raise DiagramError('R2: edges not distinct')
    b = from_adj_copy(D)
    for p, q in ((es, ee), (fs, fe)):
        b.conn[p].remove(q)
        b.conn[q].remove(p)
    x, y = b.new_crossing(), b.new_crossing()
    if over:      # finger (west-east) passes over: 0 south, 1 east, 2 north, 3 west
        S, E, N, W = 0, 1, 2, 3
    else:         # finger passes under: 0 west, 1 south, 2 east, 3 north
        W, S, E, N = 0, 1, 2, 3
    b.connect(es, (x, W))
    b.connect((x, E), (y, E))
    b.connect((y, W), ee)
    b.connect(fe, (x, S))
    b.connect((x, N), (y, S))
    b.connect((y, N), fs)
    return b.diagram().pd()


def r3_candidates(D):
    """Triangular faces on which an R3 move can be performed."""
    out = []
    for f, cyc in enumerate(D.faces):
        if len(cyc) != 3:
            continue
        cs = [c for c, _ in cyc]
        if len(set(cs)) != 3:
            continue
        bd = face_boundary(D, f)
        # each side is an inner edge; the strand of a side is over at both ends, under at both, or mixed
        kinds = []
        for s, e in bd:
            kinds.append((s[1] % 2, e[1] % 2))
        if any(a == b for a, b in kinds):
            out.append(f)
    return out


def r3(pd, face):
    D = Diagram.from_pd(pd)
    if face not in r3_candidates(D):
        raise DiagramError('R3 not applicable')
    bd = face_boundary(D, face)
    inner = set()
    sub = {}
    sides = []
    for s, e in bd:
        inner.add(s)
        inner.add(e)
    for s, e in bd:
        os_ = (s[0], (s[1] + 2) % 4)
        oe = (e[0], (e[1] + 2) % 4)
        sub[os_] = e
        sub[oe] = s
        sides.append((os_, oe))
    if len(sub) != 6:
        raise DiagramError('R3 degenerate')
    b = Builder(D.n)
    done = set()
    for d, e in D.adj.items():
        if d in inner or e in inner or d in done:
            continue
        done.add(d)
        done.add(e)
        b.connect(sub.get(d, d), sub.get(e, e))
    for p, q in sides:
        b.connect(p, q)
    return b.diagram().pd()


def random_rediagram(pd, seed, min_extra=2, steps=6):
    """Random crossing-increasing Reidemeister moves from a fixed seed.
    Returns (new pd, list of move records).  The result has at least min_extra more
    crossings than pd."""
    import random
    rng = random.Random(seed)
    cur = normalise(pd)
    n0 = len(cur)
    moves = []
    t = 0
    while t < steps or len(cur) < n0 + min_extra:
        t += 1
        if t > 200:
            raise DiagramError('re-diagram did not terminate')
        D = Diagram.from_pd(cur)
        u = rng.random()
        try:
            if u < 0.45:
                f = rng.randrange(len(D.faces))
                m = len(D.faces[f])
                if m < 2:
                    continue
                i, j = rng.sample(range(m), 2)
                over = rng.random() < 0.5
                new = r2(cur, f, i, j, over)
                rec = {'move': 'R2', 'face_corner': list(D.faces[f][0]), 'face': f, 'i': i, 'j': j,
                       'over': over}
            elif u < 0.85:
                cands = r3_candidates(D)
                if not cands:
                    continue
                f = rng.choice(cands)
                new = r3(cur, f)
                rec = {'move': 'R3', 'face': f}
            else:
                e = rng.randrange(1, 2 * D.n + 1)
                uf = rng.random() < 0.5
                ccw = rng.random() < 0.5
                new = r1(cur, e, uf, ccw)
                rec = {'move': 'R1', 'edge': e, 'under_first': uf, 'loop_ccw': ccw}
        except DiagramError:
            continue
        rec['pd_before'] = cur
        moves.append(rec)
        cur = new
    return cur, moves


def replay_rediagram(pd, moves):
    cur = normalise(pd)
    for m in moves:
        if m['move'] == 'R2':
            cur = r2(cur, m['face'], m['i'], m['j'], m['over'])
        elif m['move'] == 'R3':
            cur = r3(cur, m['face'])
        else:
            cur = r1(cur, m['edge'], m['under_first'], m['loop_ccw'])
    return cur


def remove_kinks(pd):
    """Remove Reidemeister-1 kinks (monogon faces) repeatedly.  Returns a PD code, or [] if
    the diagram reduces to the round circle."""
    pd = [list(c) for c in pd]
    while True:
        if not pd:
            return []
        D = Diagram.from_pd(pd)
        kink = None
        for c in range(D.n):
            for i in range(4):
                if D.adj[(c, i)] == (c, (i + 1) % 4):
                    kink = (c, i)
                    break
            if kink:
                break
        if kink is None:
            return D.pd()
        c, i = kink
        a, b = D.adj[(c, (i + 2) % 4)], D.adj[(c, (i + 3) % 4)]
        if a[0] == c or b[0] == c:
            return []                      # a one-crossing diagram of the unknot
        adj = {}
        ren = lambda d: (d[0] - (1 if d[0] > c else 0), d[1])
        for d, e in D.adj.items():
            if d[0] == c or e[0] == c:
                continue
            adj[ren(d)] = ren(e)
        adj[ren(a)] = ren(b)
        adj[ren(b)] = ren(a)
        if D.n == 1:
            return []
        start = next((ren(d) for d in D.order if d[0] != c), None)
        pd = Diagram(D.n - 1, adj, start=start).pd()
