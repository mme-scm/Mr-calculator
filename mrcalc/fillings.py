"""Surgery pass (section 6): fillings of core nodes.

Per node and slope one record
  {'node', 'p', 'q', 'kind': 'geo' | 'lens' | 'sfs' | 'unknown', ...}
'geo' means SnapPy found a positively oriented solution on a triangulation of the filling
(volume recorded); verification and the isometry signature are computed in the coincidence
step for the fillings whose (|p|, volume) agrees with a filling of another node, which is a
budget choice: fillings with no volume partner cannot enter an S1(a) certificate.
"""
import json
import os

from . import names, nodeset, passes, surgery as S
from .config import DATA

FILL_DIR = os.path.join(DATA, 'fillings')


def node_fillings(node, pd, slopes, time_limit=2.0, regina_nonhyp=True):
    E = S.exterior(pd)
    out = []
    for p, q in slopes:
        rec = {'node': node, 'p': p, 'q': q}
        N = E.copy()
        N.dehn_fill((p, q))
        geo = False
        for t in range(4):
            if N.solution_type() == S.GEOMETRIC:
                geo = True
                break
            N.randomize()
        if geo:
            rec['kind'] = 'geo'
            rec['vol'] = round(float(N.volume()), 9)
        elif regina_nonhyp:
            try:
                r = S.regina_recognise(S.filled_string(E, (p, q)), time_limit=time_limit)
            except Exception as e:
                r = {'kind': 'unknown', 'name': None, 'how': 'error: %r' % (e,)}
            rec.update({k: r[k] for k in ('kind', 'name', 'how', 'regina_name', 'timeout') if k in r})
        else:
            rec['kind'] = 'unknown'
            rec['how'] = 'skipped'
        out.append(rec)
    return out


def shard_task(args):
    shard, node_names, opt = args
    recs, errors = [], []
    for n in node_names:
        try:
            pd = nodeset.diagram(n)
            kind = names.kind(n)
            if kind == 'torus' or opt.get('torus_like', {}).get(n):
                slopes = opt['slopes_T']
                tl = opt.get('time_limit_torus', 20.0)
            else:
                slopes = opt['slopes_G']
                tl = opt.get('time_limit', 2.0)
            recs.extend(node_fillings(n, pd, slopes, tl))
        except Exception as e:
            errors.append({'node': n, 'error': repr(e)})
    os.makedirs(FILL_DIR, exist_ok=True)
    with open(os.path.join(FILL_DIR, '%s.jsonl' % shard), 'w') as f:
        for r in recs:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    return shard, len(recs), errors


def done_shards():
    p = os.path.join(FILL_DIR, 'done.txt')
    if not os.path.exists(p):
        return set()
    with open(p) as f:
        return set(l.strip() for l in f if l.strip())
