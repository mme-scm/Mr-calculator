"""Surgery pass (section 6): fillings of core nodes.

Per node and slope one record
  {'node', 'p', 'q', 'kind': 'geo' | 'lens' | 'sfs' | 'unknown', ...}
'geo' means SnapPy found a positively oriented solution on a triangulation of the filling
(volume recorded); verification and the isometry signature are computed in the coincidence
step for the fillings whose (|p|, volume) agrees with a filling of another node, which is a
budget choice: fillings with no volume partner cannot enter an S1(a) certificate.
"""
import gzip
import json
import os

from . import names, nodeset, passes, surgery as S
from .config import DATA

FILL_DIR = os.path.join(DATA, 'fillings')


def _fatal(e):
    return isinstance(e, (KeyboardInterrupt, SystemExit))


def node_fillings(node, pd, slopes, time_limit=2.0, regina_nonhyp=True, torus=None):
    """torus = (r, s) for the positive torus knot T(r,s): S2 (Moser) decides lens / reducible /
    Seifert fibred; only the Seifert fibred fillings are sent to Regina (for their names)."""
    E = S.exterior(pd)
    out = []
    for p, q in slopes:
        rec = {'node': node, 'p': p, 'q': q}
        try:
            if torus is not None:
                kind, nm = S.moser(torus[0], torus[1], p, q)
                if kind == 'lens':
                    rec.update(kind='lens', name=nm, how='S2')
                    out.append(rec)
                    continue
                if kind == 'reducible':
                    rec.update(kind='reducible', how='S2')
                    out.append(rec)
                    continue
                r = S.regina_recognise(S.filled_string(E, (p, q)), time_limit=time_limit)
                rec.update({k: r[k] for k in ('kind', 'name', 'how', 'regina_name', 'timeout') if k in r})
                rec['moser_orders'] = list(nm)
                out.append(rec)
                continue
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
                r = S.regina_recognise(S.filled_string(E, (p, q)), time_limit=time_limit)
                rec.update({k: r[k] for k in ('kind', 'name', 'how', 'regina_name', 'timeout') if k in r})
            else:
                rec['kind'] = 'unknown'
                rec['how'] = 'skipped'
        except BaseException as e:          # cysignals' SignalError is a BaseException
            if _fatal(e):
                raise
            rec['kind'] = 'unknown'
            rec['how'] = 'error: %r' % (e,)
        out.append(rec)
    return out


def node_task(args):
    """Fillings of one node (run in a short-lived worker)."""
    shard, n, opt = args
    try:
        pd = nodeset.diagram(n)
        tor = opt.get('torus_like', {}).get(n)
        if tor:
            return shard, n, node_fillings(n, pd, opt['slopes_T'], opt.get('time_limit_torus', 0.5),
                                           torus=tuple(tor)), None
        return shard, n, node_fillings(n, pd, opt['slopes_G'], opt.get('time_limit', 2.0)), None
    except BaseException as e:
        if _fatal(e):
            raise
        return shard, n, [], repr(e)


def worker_loop(task_q, res_q):
    """Worker of the crash-tolerant scheduler in scripts/run_fillings.py."""
    import os as _os
    pid = _os.getpid()
    while True:
        t = task_q.get()
        if t is None:
            return
        res_q.put(('start', pid, t[0], t[1]))
        shard, node, rs, err = node_task(t)
        res_q.put(('done', pid, shard, node, rs, err))


def write_shard(shard, recs):
    os.makedirs(FILL_DIR, exist_ok=True)
    with gzip.open(os.path.join(FILL_DIR, '%s.jsonl.gz' % shard), 'wt') as f:
        for r in recs:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    with open(os.path.join(FILL_DIR, 'done.txt'), 'a') as f:
        f.write(shard + '\n')


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
    with gzip.open(os.path.join(FILL_DIR, '%s.jsonl.gz' % shard), 'wt') as f:
        for r in recs:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    return shard, len(recs), errors


def iter_fillings():
    """All filling records."""
    if not os.path.isdir(FILL_DIR):
        return
    for fn in sorted(os.listdir(FILL_DIR)):
        if fn.endswith('.jsonl.gz'):
            f = gzip.open(os.path.join(FILL_DIR, fn), 'rt')
        elif fn.endswith('.jsonl'):
            f = open(os.path.join(FILL_DIR, fn))
        else:
            continue
        with f:
            for line in f:
                yield json.loads(line)


def done_shards():
    p = os.path.join(FILL_DIR, 'done.txt')
    if not os.path.exists(p):
        return set()
    with open(p) as f:
        return set(l.strip() for l in f if l.strip())
