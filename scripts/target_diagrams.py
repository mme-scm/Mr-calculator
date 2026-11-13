"""Diagram shards for the targeted search (section 5 diagrams of further kinds; no rule is applied).

  g2 <adjacent.jsonl> <shard prefix> [chunk=200]
      Adjacent nodes outside the table (census and 'H:' nodes of the list written by scripts/targets.py): the
      result diagram of the move that first produced the node (mrcalc/node_pd.py), as a diagram record of kind
      'g2' with id '<node>|g2'.  The diagram is certified as a diagram of that node by the identification
      certificate of the move.  Nodes that already have a g2 diagram are skipped.
  re <open.txt> <shard prefix> [n=3] [chunk=40]
      Seeded re-diagrams (Reidemeister moves, passes.diagrams_for) of the listed table knots that have none
      (12-13 crossings were built with 0 re-diagrams), kinds 're1'..'re<n>', ids '<knot>|re<j>'.
Shards are written to data/diagrams/<prefix>-NNNN.jsonl.gz, numbered after the existing ones of the prefix."""
import collections
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import node_pd, passes  # noqa: E402
from mrcalc import pd as P  # noqa: E402


def existing_ids():
    return {d['id'] for d in passes.iter_diagrams()}


def write(prefix, recs, chunk):
    os.makedirs(passes.DIAG_DIR, exist_ok=True)
    have = [fn for fn in os.listdir(passes.DIAG_DIR) if fn.startswith(prefix + '-')]
    k = len(have)
    for i in range(0, len(recs), chunk):
        path = os.path.join(passes.DIAG_DIR, '%s-%04d.jsonl.gz' % (prefix, k))
        with gzip.open(path + '.tmp', 'wt') as f:
            for d in recs[i:i + chunk]:
                f.write(json.dumps(d, separators=(',', ':')) + '\n')
        os.replace(path + '.tmp', path)
        k += 1
    return k - len(have)


def main():
    mode, src, prefix = sys.argv[1:4]
    kv = dict(a.split('=', 1) for a in sys.argv[4:] if '=' in a)
    have = existing_ids()
    out, miss = [], 0
    if mode == 'g2':
        index = node_pd.build_index()
        want = []
        for line in open(src):
            r = json.loads(line)
            if r['kind'] not in ('census', 'hyp'):
                continue
            n = r['node']
            m = n[:-1] if n.endswith('*') else n + '*'
            rep = n if n in index else (m if m in index else None)     # one diagram per mirror pair
            if rep is None:
                miss += 1
            elif '%s|g2' % rep not in have and rep not in want:
                want.append(rep)
        want.sort(key=lambda n: (index[n]['source']['shard'], n))      # one source shard in memory at a time
        for n in want:
            try:
                pd = P.normalise(node_pd.diagram(n, index[n]['source']))
                D = P.Diagram.from_pd(pd)
                out.append({'id': '%s|g2' % n, 'node': n, 'kind': 'g2', 'pd': pd,
                            'cert': {'type': 'move-result', 'source': index[n]['source']},
                            'writhe': D.writhe(), 'homogeneous': D.is_homogeneous(), 'n': D.n})
            except Exception:
                miss += 1
        nsh = write(prefix, out, int(kv.get('chunk', 200)))
    elif mode == 're':
        nre = int(kv.get('n', 3))
        for line in open(src):
            name = line.strip()
            if not name or '%s|re1' % name in have:
                continue
            try:
                out.extend(d for d in passes.diagrams_for(name, rediagrams=nre) if d['kind'].startswith('re'))
            except Exception:
                miss += 1
        nsh = write(prefix, out, int(kv.get('chunk', 40)) * nre)
    else:
        raise SystemExit(__doc__)
    print('%s diagrams: %d records in %d new shards (%d nodes without a diagram); crossings: %s' % (
        mode, len(out), nsh, miss, sorted(collections.Counter(d['n'] for d in out).items())), flush=True)


if __name__ == '__main__':
    main()
