"""PD codes for nodes that mrcalc.nodeset.diagram() does not cover (census 'K14...', 'K15...' and 'H:' nodes).

nodeset.diagram(name) returns None for these kinds, so the fillings pass cannot run on them as it is.  A
diagram exists for every such node that a move produced: the result diagram of the move.  The pass records hold
no PD codes; they are recomputed with passes.result_pd from the source diagram (data/diagrams/<shard>.jsonl[.gz])
and the move parameters, as scripts/node_inputs.py and mrcalc/export.py do.

    index = build_index()                # node -> {'crossings', 'source'}; one pass over data/hfk_peripheral
    pd = diagram(name, index[name]['source'])

The index uses data/hfk_peripheral/part-*.jsonl, which records for every peripheral node the move that first
produced it (written by scripts/node_inputs.py from prepare.Problem.move_of) and the crossing number of the
result diagram.  One representative per mirror pair is kept (the unstarred name if both were produced), which
is what the fillings pass needs: fillings exist for one chirality, with slopes of both signs.  The diagram is
the diagram of the node AS NAMED (for a name ending in '*' the move produced that mirror image; nothing is
mirrored here).  Tasks should be ordered by source shard: one diagram shard is kept in memory.
"""
import json
import os

_DIAGS = {}


def move_type(mv):
    """Record type of a source move ('t' is not stored in data/hfk_peripheral): mutation records have an
    axis, crossing changes a crossing index, twists the crossed edges and a handedness."""
    if 'axis' in mv:
        return 'mu'
    if 'i' in mv:
        return 'cc'
    return 'tw'


def diagram(name, source=None):
    """PD code of a node: nodeset.diagram for the kinds it covers, else the result diagram of the move."""
    from mrcalc import nodeset, passes
    if source is None:
        return nodeset.diagram(name)
    if source['shard'] not in _DIAGS:
        _DIAGS.clear()
        _DIAGS[source['shard']] = {x['id']: x for x in passes.load_diagrams(source['shard'])}
    return passes.result_pd(_DIAGS[source['shard']][source['d']]['pd'], dict(source, t=move_type(source)))


def build_index(data_dir=None):
    """{node: {'crossings': n, 'source': move}}, one node per mirror pair."""
    if data_dir is None:
        from mrcalc.config import DATA as data_dir
    d = os.path.join(data_dir, 'hfk_peripheral')
    src = {}
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.jsonl'):
            continue
        with open(os.path.join(d, fn)) as f:
            for line in f:
                if not line.endswith('\n'):
                    continue                    # a line being written
                r = json.loads(line)
                if 'source' in r and 'crossings' in r:
                    src.setdefault(r['node'], {'crossings': r['crossings'], 'source': r['source']})
    out = {}
    for n in sorted(src):
        if n.endswith('*') and n[:-1] in src:
            continue
        out[n] = src[n]
    return out


def load_index(path):
    out = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            out[r['node']] = {'crossings': r['crossings'], 'source': r['source']}
    return out


class Resolver:
    """Convenience wrapper: Resolver(index).diagram(name)."""

    def __init__(self, index):
        self.index = index

    def diagram(self, name):
        e = self.index.get(name)
        return diagram(name, e['source'] if e else None)
