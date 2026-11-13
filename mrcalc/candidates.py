"""Candidate clusters of the surgery-coincidence step without one Python dict per filling record.

Replaces the part of main() of scripts/find_coincidences.py that holds every record as a dict
(`recs = list(F.iter_fillings())`, `by_p`, the sort and the cluster loop).  Same definition, same result:

    candidates = 'geo' fillings, without the negative slopes of amphichiral table knots;
    grouped by |p|, sorted by volume; a cluster is a maximal run in which consecutive volumes differ by less
    than tol (float64 arithmetic on the recorded volumes, as in the script; the script's VOL_TOL, 1e-8 since
    2026-11-13, 2e-7 before; both were compared with the script); its keys are the sorted set of
    (node, p, q); clusters with fewer than two keys are dropped; rank 2 if the keys involve more than one node
    and all nodes lie in one mutation class, else 0 if a node is in `prio`, else 1; clusters ordered by
    (rank, |p|, keys).

What differs is the representation: records are streamed shard by shard into numeric arrays (16 bytes per
'geo' filling: volume float64, node index int32, p int16, q int16), partitioned by |p| (the first component of
the sort key), each part is sorted with numpy and the runs are found with array operations.  With
spill=<directory> the parts are files, and memory is bounded by the largest part (external partition by |p|,
in-memory sort by volume inside a part).

The result is a ClusterTable (arrays).  ClusterTable.as_tuples() gives the list [(rank, |p|, keys)] of the
script for comparison or for small runs; iter_clusters() yields the same tuples one at a time.

Nothing here decides what a certificate is: this is the search step only.
"""
from __future__ import annotations

import gzip
import json
import os

import numpy as np

REC = np.dtype([('vol', '<f8'), ('node', '<i4'), ('p', '<i2'), ('q', '<i2')])     # 16 bytes
VOL_TOL = 1e-8          # default of scripts/find_coincidences.py (which passes its own value)


# ----------------------------------------------------------------------
# node names <-> integers
# ----------------------------------------------------------------------
class Nodes:
    """Node names in order of first appearance.  (Names of 'H:' nodes are long: they are kept as Python
    strings, never as fixed-width numpy strings.)"""

    def __init__(self, names=()):
        self.names = list(names)
        self.index = {n: i for i, n in enumerate(self.names)}

    def id(self, name):
        i = self.index.get(name)
        if i is None:
            i = self.index[name] = len(self.names)
            self.names.append(name)
        return i

    def __len__(self):
        return len(self.names)

    def name_rank(self):
        """rank[i] = position of names[i] in sorted(names): ordering by rank is ordering by name (str)."""
        order = sorted(range(len(self.names)), key=self.names.__getitem__)
        rank = np.empty(len(order), dtype=np.int64)
        rank[np.array(order, dtype=np.int64)] = np.arange(len(order), dtype=np.int64)
        return rank


# ----------------------------------------------------------------------
# reading shards
# ----------------------------------------------------------------------
def shard_files(fill_dir):
    """The files mrcalc.fillings.iter_fillings() reads, in its order."""
    out = []
    for fn in sorted(os.listdir(fill_dir)):
        if fn.endswith('.jsonl.gz') or fn.endswith('.jsonl'):
            out.append(os.path.join(fill_dir, fn))
    return out


def read_shard(path, nodes, amph=frozenset(), keep_other=None, stats=None):
    """One JSONL shard -> REC array of its candidate-eligible 'geo' records.
    keep_other: a list that receives every record that is not 'geo', as dicts: they are few (0.55 % of the
    present data) and carry the names that parts (b), (c) of find_coincidences.py read.
    stats: a dict whose entry 'records' counts all records read."""
    f = gzip.open(path, 'rt') if path.endswith('.gz') else open(path)
    vols, ids, ps, qs = [], [], [], []
    n = 0
    with f:
        for line in f:
            r = json.loads(line)
            n += 1
            if r['kind'] == 'geo':
                p = r['p']
                if p < 0 and r['node'] in amph:
                    continue
                vols.append(r['vol'])
                ids.append(nodes.id(r['node']))
                ps.append(p)
                qs.append(r['q'])
            elif keep_other is not None:
                keep_other.append(r)
    if stats is not None:
        stats['records'] = stats.get('records', 0) + n
    out = np.empty(len(vols), dtype=REC)
    out['vol'] = vols
    out['node'] = ids
    out['p'] = ps
    out['q'] = qs
    return out


# ----------------------------------------------------------------------
# partition by |p|
# ----------------------------------------------------------------------
class Parts:
    """REC arrays partitioned by |p|, in memory (spill=None) or in files <spill>/p<|p|>.rec (appended)."""

    def __init__(self, spill=None):
        self.spill = spill
        self.mem = {}
        self.count = {}
        if spill:
            os.makedirs(spill, exist_ok=True)
            for fn in os.listdir(spill):
                if fn.endswith('.rec'):
                    os.remove(os.path.join(spill, fn))

    def add(self, rec):
        if not len(rec):
            return
        ap = np.abs(rec['p'].astype(np.int32))
        order = np.argsort(ap, kind='stable')
        aps = ap[order]
        cuts = np.flatnonzero(np.diff(aps)) + 1
        starts = np.r_[0, cuts]
        ends = np.r_[cuts, len(aps)]
        srt = rec[order]
        for s, e in zip(starts.tolist(), ends.tolist()):
            p = int(aps[s])
            chunk = srt[s:e]
            self.count[p] = self.count.get(p, 0) + (e - s)
            if self.spill:
                with open(os.path.join(self.spill, 'p%d.rec' % p), 'ab') as f:
                    chunk.tofile(f)
            else:
                self.mem.setdefault(p, []).append(chunk.copy())

    def keys(self):
        return sorted(self.count)

    def get(self, p):
        if self.spill:
            return np.fromfile(os.path.join(self.spill, 'p%d.rec' % p), dtype=REC)
        xs = self.mem[p]
        return xs[0] if len(xs) == 1 else np.concatenate(xs)

    def total(self):
        return sum(self.count.values())


# ----------------------------------------------------------------------
# clusters
# ----------------------------------------------------------------------
class ClusterTable:
    """Clusters as arrays.  Cluster c has rank[c], absp[c] and the members offset[c]:offset[c+1] of
    (node, p, q), sorted by (node name, p, q)."""

    def __init__(self, rank, absp, offset, node, p, q, names):
        self.rank, self.absp, self.offset = rank, absp, offset
        self.node, self.p, self.q = node, p, q
        self.names = names

    def __len__(self):
        return len(self.rank)

    def n_candidates(self):
        """Number of distinct (node, p, q) in the clusters (len(cand) of the script)."""
        if not len(self.node):
            return 0
        key = (self.node.astype(np.int64) << 32) | ((self.p.astype(np.int64) & 0xffff) << 16) | (self.q.astype(np.int64) & 0xffff)
        return int(len(np.unique(key)))

    def iter_clusters(self):
        names = self.names
        off = self.offset.tolist()
        nd, ps, qs = self.node.tolist(), self.p.tolist(), self.q.tolist()
        rk, ap = self.rank.tolist(), self.absp.tolist()
        for c in range(len(rk)):
            a, b = off[c], off[c + 1]
            yield rk[c], ap[c], [(names[nd[i]], ps[i], qs[i]) for i in range(a, b)]

    def as_tuples(self):
        return list(self.iter_clusters())

    def save(self, path):
        tmp = path + '.tmp.npz'
        np.savez_compressed(tmp, rank=self.rank, absp=self.absp, offset=self.offset, node=self.node, p=self.p,
                            q=self.q, names=np.frombuffer(json.dumps(self.names).encode(), dtype=np.uint8))
        os.replace(tmp, path)

    @classmethod
    def load(cls, path):
        z = np.load(path)
        return cls(z['rank'], z['absp'], z['offset'], z['node'], z['p'], z['q'], json.loads(z['names'].tobytes().decode()))


def _cluster_part(rec, name_rank, tol=VOL_TOL):
    """Clusters of one |p| part.  Returns (members REC array sorted by cluster then (name, p, q), duplicates
    of a key inside a cluster removed; counts per cluster)."""
    if len(rec) < 2:
        return rec[:0], np.zeros(0, dtype=np.int64)
    vol = rec['vol']
    if np.isnan(vol).any():
        raise ValueError("a 'geo' record without volume")
    order = np.argsort(vol, kind='stable')
    v = vol[order]
    link = (v[1:] - v[:-1]) < tol                       # the test of the script, in float64
    if not link.any():
        return rec[:0], np.zeros(0, dtype=np.int64)
    # run id of every sorted position: a new run starts where the link to the previous position is missing
    run = np.empty(len(v), dtype=np.int64)
    run[0] = 0
    np.cumsum(~link, out=run[1:])
    inrun = np.empty(len(v), dtype=bool)                # position belongs to a run of length > 1
    inrun[0] = link[0]
    inrun[-1] = link[-1]
    inrun[1:-1] = link[1:] | link[:-1]
    idx = order[inrun]
    m = rec[idx]
    r = run[inrun]
    nr = name_rank[m['node']]
    # sort members by (run, name, p, q) and drop repeated keys within a run (the script builds a set)
    o = np.lexsort((m['q'], m['p'], nr, r))
    m, r, nr = m[o], r[o], nr[o]
    same = (r[1:] == r[:-1]) & (m['node'][1:] == m['node'][:-1]) & (m['p'][1:] == m['p'][:-1]) & (m['q'][1:] == m['q'][:-1])
    if same.any():
        keep = np.r_[True, ~same]
        m, r = m[keep], r[keep]
    # runs with at least two keys
    start = np.flatnonzero(np.r_[True, r[1:] != r[:-1]])
    cnt = np.diff(np.r_[start, len(r)])
    good = cnt > 1
    if not good.all():
        keepm = np.repeat(good, cnt)
        m = m[keepm]
        cnt = cnt[good]
    return m, cnt


def _part_table(rec, absp, name_rank, names, mclass_id=None, prio=None, tol=VOL_TOL):
    """Clusters of one |p| part, ordered as the script orders them inside one |p|: by (rank, keys).
    Returns (rank per cluster, member count per cluster, node, p, q of the members) or None."""
    m, cnt = _cluster_part(rec, name_rank, tol)
    if not len(cnt):
        return None
    off = np.zeros(len(cnt) + 1, dtype=np.int64)
    np.cumsum(cnt, out=off[1:])
    first = off[:-1]
    node = m['node']
    rank = np.ones(len(cnt), dtype=np.uint8)
    if prio is not None:
        rank[np.logical_or.reduceat(np.asarray(prio, dtype=bool)[node], first)] = 0
    if mclass_id is not None:
        mc = np.asarray(mclass_id)[node]
        one_class = np.minimum.reduceat(mc, first) == np.maximum.reduceat(mc, first)
        several_nodes = np.minimum.reduceat(node, first) != np.maximum.reduceat(node, first)
        rank[one_class & several_nodes] = 2
    # order by (rank, keys): members are sorted inside a cluster, so the first key decides unless two
    # clusters of one rank share their first key (possible only with a filling recorded twice)
    f_nr, f_p, f_q = name_rank[node[first]], m['p'][first], m['q'][first]
    o = np.lexsort((f_q, f_p, f_nr, rank))
    tie = ((rank[o][1:] == rank[o][:-1]) & (f_nr[o][1:] == f_nr[o][:-1]) & (f_p[o][1:] == f_p[o][:-1])
           & (f_q[o][1:] == f_q[o][:-1]))
    if tie.any():                                        # general case: compare the whole key lists
        full = [(int(rank[c]), [(names[int(node[i])], int(m['p'][i]), int(m['q'][i]))
                                for i in range(int(off[c]), int(off[c + 1]))]) for c in range(len(cnt))]
        o = np.array(sorted(range(len(cnt)), key=full.__getitem__), dtype=np.int64)
    cnt_o = cnt[o]
    off_o = np.zeros(len(cnt) + 1, dtype=np.int64)
    np.cumsum(cnt_o, out=off_o[1:])
    src = np.repeat(first[o] - off_o[:-1], cnt_o)
    src += np.arange(int(off_o[-1]), dtype=np.int64)
    return rank[o], cnt_o, m['node'][src], m['p'][src], m['q'][src]


def iter_part_tables(parts, nodes, mclass_id=None, prio=None, tol=VOL_TOL):
    """(|p|, rank, count, node, p, q) per part with clusters; memory: one part at a time."""
    name_rank = nodes.name_rank()
    for p in parts.keys():
        t = _part_table(parts.get(p), p, name_rank, nodes.names, mclass_id, prio, tol)
        if t is not None:
            yield (p,) + t


def cluster(parts, nodes, mclass_id=None, prio=None, tol=VOL_TOL):
    """ClusterTable of the parts, in the order of the script: (rank, |p|, keys).  mclass_id: int array per node
    id (equal values = one mutation class); prio: bool array per node id.  Without them every cluster has rank 1.
    tol: consecutive volumes of a cluster differ by less than tol.
    Memory: the parts one at a time, plus 8 bytes per cluster member and 11 per cluster for the table."""
    tabs = list(iter_part_tables(parts, nodes, mclass_id, prio, tol))
    R, A, N, NO, PP, QQ = [], [], [], [], [], []
    for r in (0, 1, 2):                                   # rank-major, then |p| ascending (parts.keys() order)
        for p, rank, cnt, node, pp, qq in tabs:
            lo, hi = np.searchsorted(rank, r, 'left'), np.searchsorted(rank, r, 'right')
            if hi == lo:
                continue
            a = int(cnt[:lo].sum())
            b = a + int(cnt[lo:hi].sum())
            R.append(rank[lo:hi])
            A.append(np.full(hi - lo, p, dtype=np.int16))
            N.append(cnt[lo:hi])
            NO.append(node[a:b])
            PP.append(pp[a:b])
            QQ.append(qq[a:b])
    if not R:
        z = np.zeros(0, dtype=np.int64)
        return ClusterTable(z.astype(np.uint8), z.astype(np.int16), np.zeros(1, dtype=np.int64), z.astype(np.int32),
                            z.astype(np.int16), z.astype(np.int16), nodes.names)
    cnt = np.concatenate(N)
    off = np.zeros(len(cnt) + 1, dtype=np.int64)
    np.cumsum(cnt, out=off[1:])
    return ClusterTable(np.concatenate(R), np.concatenate(A), off, np.concatenate(NO), np.concatenate(PP),
                        np.concatenate(QQ), nodes.names)


# ----------------------------------------------------------------------
# front ends
# ----------------------------------------------------------------------
def load_parts(fill_dir, amph=frozenset(), spill=None, keep_other=None, nodes=None, files=None, stats=None):
    """Streams the shards of fill_dir into Parts.  Returns (parts, nodes)."""
    nodes = nodes or Nodes()
    parts = Parts(spill)
    for path in (files if files is not None else shard_files(fill_dir)):
        parts.add(read_shard(path, nodes, amph, keep_other, stats))
    return parts, nodes


def class_ids(nodes, mclass):
    """mclass: the function returned by find_coincidences.mutation_classes().  -> int array per node id."""
    reps = {}
    out = np.empty(len(nodes), dtype=np.int64)
    for i, n in enumerate(nodes.names):
        out[i] = reps.setdefault(mclass(n), len(reps))
    return out


def prio_flags(nodes, prio):
    return np.fromiter((n in prio for n in nodes.names), dtype=bool, count=len(nodes))


def candidate_clusters(fill_dir, amph=frozenset(), mclass=None, prio=None, spill=None, keep_other=None, tol=VOL_TOL):
    """The clusters of scripts/find_coincidences.py, as a ClusterTable."""
    parts, nodes = load_parts(fill_dir, amph, spill, keep_other)
    return cluster(parts, nodes, class_ids(nodes, mclass) if mclass is not None else None,
                   prio_flags(nodes, prio) if prio is not None else None, tol)


# ----------------------------------------------------------------------
# ordering without mutation classes (nodes the mu pass does not cover)
# ----------------------------------------------------------------------
def systematic_components(T, min_shared=10):
    """Component id per node id (int array over T.names) of the relation 'the two nodes share at least
    min_shared clusters of the ClusterTable T'; a node in no such pair has an id of its own (negative)."""
    cnt = np.diff(T.offset)
    first = T.offset[:-1]
    node = T.node.astype(np.int64)
    nmax = len(T.names)
    comp = -np.arange(1, nmax + 1, dtype=np.int64)
    # unordered pairs of distinct nodes inside each cluster (clusters are small; the loops are over the size)
    pairs = []
    for size in np.unique(cnt).tolist():
        cl = np.flatnonzero(cnt == size)
        base = first[cl]
        for i in range(size):
            for j in range(i + 1, size):
                a, b = node[base + i], node[base + j]
                d = a != b
                pairs.append(np.minimum(a[d], b[d]) * nmax + np.maximum(a[d], b[d]))
    if not pairs:
        return comp
    u, c = np.unique(np.concatenate(pairs), return_counts=True)
    del pairs
    strong = u[c >= min_shared]
    par = {}

    def find(x):
        par.setdefault(x, x)
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for k in strong.tolist():
        a, b = find(k // nmax), find(k % nmax)
        if a != b:
            par[a] = b
    for x in list(par):
        comp[x] = find(x)
    return comp


def systematic_flags(T, min_shared=10):
    """bool per cluster of T: the cluster has several nodes and all of them lie in one component of
    systematic_components(T, min_shared).

    Use: a work order for nodes without mutation classes (rank 2 of find_coincidences.py needs the classes of
    the mu pass, which exist for table knots only).  On the present data the flag is exactly rank 2
    (scripts/m5b_systematic_pairs.py: 138,008 clusters both, none either way).  It is a heuristic for the
    ORDER of the search only: nothing is dropped, and what counts as a certificate is untouched."""
    if not len(T):
        return np.zeros(0, dtype=bool)
    first = T.offset[:-1]
    cm = systematic_components(T, min_shared)[T.node]
    one = np.minimum.reduceat(cm, first) == np.maximum.reduceat(cm, first)
    several = np.minimum.reduceat(T.node, first) != np.maximum.reduceat(T.node, first)
    return one & several


def merge_class_ids(a, b):
    """Class ids (int arrays per node id) of the equivalence generated by two classifications."""
    par = list(range(len(a)))

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x
    for ids in (a, b):
        firstof = {}
        for i, c in enumerate(np.asarray(ids).tolist()):
            j = firstof.setdefault(c, i)
            if j != i:
                ra, rb = find(i), find(j)
                if ra != rb:
                    par[ra] = rb
    return np.array([find(i) for i in range(len(par))], dtype=np.int64)


def cluster_ranked(parts, nodes, mclass_id=None, prio=None, systematic=0, tol=VOL_TOL):
    """cluster(); with systematic = n > 0, rank 2 is also given to the clusters whose nodes are tied by
    sharing at least n clusters (two passes over the parts: the first finds the pairs)."""
    if not systematic:
        return cluster(parts, nodes, mclass_id, prio, tol)
    comp = systematic_components(cluster(parts, nodes, tol=tol), systematic)
    cls = comp if mclass_id is None else merge_class_ids(np.asarray(mclass_id), comp)
    return cluster(parts, nodes, cls, prio, tol)
