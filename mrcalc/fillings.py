"""Surgery pass (section 6): fillings of core nodes.

Per node and slope one record
  {'node', 'p', 'q', 'kind': 'geo' | 'lens' | 'sfs' | 'unknown', ...}
'geo' means SnapPy found a positively oriented solution on a triangulation of the filling
(volume recorded); verification and the isometry signature are computed in the coincidence
step for the fillings whose (|p|, volume) agrees with a filling of another node, which is a
budget choice: fillings with no volume partner cannot enter an S1(a) certificate.
"""
import gzip
import hashlib
import json
import os

from . import names, node_pd, nodeset, passes, surgery as S
from .config import DATA

FILL_DIR = os.path.join(DATA, 'fillings')
# progress of unfinished shards, one line per node (never inside FILL_DIR: its .jsonl files are all read as shards)
JOURNAL_DIR = os.path.join(passes.PARTIAL_DIR, 'fillings')


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
            N = S.geometric_filling(E, (p, q), tries=4, redescribe=False)
            if N is None:                  # another surgery description of the filling (S.redescriptions)
                N = S.geometric_filling(E, (p, q), tries=0)
                if N is not None:
                    rec['how'] = 'drill'
            if N is not None:
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


def retry_geometric(node, pd, slopes, tries=40):
    """Fillings recorded as 'unknown': look again for a positively oriented solution, with more
    randomisations.  Returns 'geo' records for the slopes where one is found."""
    E = S.exterior(pd)
    out = []
    for p, q in slopes:
        try:
            N = S.geometric_filling(E, (p, q), tries=tries)
            if N is not None:
                out.append({'node': node, 'p': p, 'q': q, 'kind': 'geo', 'vol': round(float(N.volume()), 9),
                            'how': 'retry'})
        except BaseException as e:          # cysignals' SignalError is a BaseException
            if _fatal(e):
                raise
    return out


def node_task(args):
    """Fillings of one node (run in a short-lived worker).  With opt['extend'] = {'missing': slopes,
    'retry': slopes} only the missing slopes are filled and the 'unknown' ones are retried."""
    shard, n, opt = args
    try:
        pd = node_pd.diagram(n, opt.get('source'))     # source: the move that produced a node without a table diagram
        ext = opt.get('extend')
        if ext is not None:
            rs = node_fillings(n, pd, [tuple(x) for x in ext['missing']], opt.get('time_limit', 2.0)) \
                if ext['missing'] else []
            if ext['retry']:
                rs += retry_geometric(n, pd, [tuple(x) for x in ext['retry']], opt.get('geo_tries', 40))
            return shard, n, rs, None
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


def write_shard(shard, recs, out_dir=None, nodes=None):
    """Writes a shard to data/fillings and marks it done; with out_dir, writes it there instead
    (atomically, done.txt untouched).  nodes: the node list of a shard that is not one of
    passes.shard_nodes() (recorded in shard_nodes.txt, see done_nodes)."""
    d = out_dir or FILL_DIR
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, '%s.jsonl.gz' % shard)
    with gzip.open(path + '.tmp', 'wt') as f:
        for r in recs:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    os.replace(path + '.tmp', path)
    if nodes is not None:
        with open(os.path.join(d, 'shard_nodes.txt'), 'a') as f:
            f.write('%s\t%s\n' % (shard, json.dumps(list(nodes), separators=(',', ':'))))
    if out_dir is None:
        with open(os.path.join(FILL_DIR, 'done.txt'), 'a') as f:
            f.write(shard + '\n')


def done_nodes(out_dir=None):
    """Nodes of the shards written with a node list (shards of nodes given by an index, not by tier)."""
    p = os.path.join(out_dir or FILL_DIR, 'shard_nodes.txt')
    out = set()
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                if line.endswith('\n') and '\t' in line:
                    out.update(json.loads(line.split('\t', 1)[1]))
    return out


def node_shards(index, have, chunk=1000):
    """Shards for the nodes of an index (node -> {'source': move}) that are not in have: ordered by the diagram
    shard of the source move (a worker then reads one diagram shard after the other), chunk nodes per shard.
    The shard id contains a hash of the node list, so a name always means the same nodes."""
    todo = sorted((n for n in index if n not in have), key=lambda n: (index[n]['source']['shard'], n))
    out = {}
    for j in range(0, len(todo), chunk):
        ns = todo[j:j + chunk]
        h = hashlib.sha256(json.dumps(ns).encode()).hexdigest()[:10]
        out['p-%s-%s' % (index[ns[0]]['source']['shard'], h)] = ns
    return out


# ----------------------------------------------------------------------
# journal of unfinished shards: a restart loses only the nodes that were being computed
# ----------------------------------------------------------------------
def journal_key(opt, extend=False):
    """What the records of a node depend on (a journal of another setting is not used)."""
    x = [opt['slopes_G'], opt['slopes_T'], opt.get('time_limit'), opt.get('time_limit_torus'), bool(extend),
         opt.get('geo_tries')]
    return hashlib.sha256(json.dumps(x).encode()).hexdigest()[:16]


def journal_path(shard):
    return os.path.join(JOURNAL_DIR, '%s.jsonl' % shard)


def journal_open(shard, key):
    """({node: records} recovered from the journal of the shard, file open for appending).  The journal is
    rewritten without a line cut off by the restart."""
    path = journal_path(shard)
    have = {}
    if os.path.exists(path):
        with open(path) as f:
            lines = f.read().split('\n')
        try:
            ok = json.loads(lines[0]).get('key') == key
        except Exception:
            ok = False
        for line in lines[1:] if ok else []:
            try:
                e = json.loads(line)
                have[e['node']] = e['recs']
            except Exception:
                continue
    os.makedirs(JOURNAL_DIR, exist_ok=True)
    with open(path + '.tmp', 'w') as f:
        f.write(json.dumps({'key': key}) + '\n')
        for n, rs in have.items():
            f.write(json.dumps({'node': n, 'recs': rs}, separators=(',', ':')) + '\n')
    os.replace(path + '.tmp', path)
    return have, open(path, 'a')


def journal_add(f, node, recs):
    f.write(json.dumps({'node': node, 'recs': recs}, separators=(',', ':')) + '\n')
    f.flush()
    os.fsync(f.fileno())


def journal_close(shard, f):
    f.close()
    try:
        os.remove(journal_path(shard))
    except OSError:
        pass


def read_shard(shard):
    with gzip.open(os.path.join(FILL_DIR, '%s.jsonl.gz' % shard), 'rt') as f:
        return [json.loads(line) for line in f]


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


def iter_fillings(only=None):
    """All filling records; with only=<kind>, the records of that kind (lines that do not contain the word
    are skipped before they are parsed: almost all records are 'geo')."""
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
                if only is None:
                    yield json.loads(line)
                elif only in line:
                    r = json.loads(line)
                    if r.get('kind') == only:
                        yield r


def done_shards():
    p = os.path.join(FILL_DIR, 'done.txt')
    if not os.path.exists(p):
        return set()
    with open(p) as f:
        return set(l.strip() for l in f if l.strip())
