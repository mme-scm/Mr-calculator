"""Re-verify the chirality of non-hyperbolic move results (repair after the calculator defect of 2026-11-15).

A non-hyperbolic result is matched to a reference knot up to mirror image by a Regina isomorphism signature;
its chirality was then decided by the sign of tau from one unchecked run of the knot Floer calculator
(identify._chirality, 'chirality_by': 'tau' or 'hfk').  The calculator sometimes returns the homology of
something else (mrcalc/hfk.py), so those decisions are repeated here without it where possible:

  reference with signature != 0:  the signature of the recomputed result diagram (Seifert matrix, exact)
  otherwise:                      identify._chirality with the checked calculator (mrcalc/hfk.py)

usage: verify_chirality.py check out=<report.jsonl> [procs=3] [passes=a,b]
           one line per pass shard: records checked and the records whose stored chirality is not confirmed
       verify_chirality.py apply <report.jsonl> [dirs=<pass dir>,<pass dir>]
           rewrites those records (the other chirality, or no result when it cannot be decided) in the given
           pass directories (default: the staging directory and data/passes) and appends them to
           data/corrections/chirality.jsonl
"""
import gzip
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import alg, names, passes  # noqa: E402
from mrcalc import pd as P  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

KEYS = ('t', 'd', 'i', 'e', 'h', 'axis', 'a', 'b', 's', 'r2')


def result_pd(pd0, r):
    return passes.result_pd(pd0, r)          # band moves included (passes.band_pd)


def check_shard(args):
    pn, shard, path = args
    idr = passes.identifier()
    diags = None
    n = 0
    bad = []
    methods = {}
    with passes._open(path) as f:
        for li, line in enumerate(f):
            if '"chirality_by"' not in line:
                continue
            r = json.loads(line)
            cert = r.get('cert') or {}
            if cert.get('chirality_by') not in ('tau', 'hfk') or r.get('dst') is None:
                continue
            if diags is None:
                diags = {d['id']: d for d in passes.load_diagrams(shard)}
            ref = idr.pool[cert['ref']]
            status, mir, how = 'ok', None, None
            try:
                pd1 = result_pd(diags[r['d']]['pd'], r)
                if ref.get('sigma'):
                    s = alg.signature(pd1)
                    how = 'sigma'
                    if abs(s) != abs(ref['sigma']):
                        status = 'signature of the result is not that of the reference up to sign'
                    else:
                        mir = (s > 0) != (ref['sigma'] > 0)
                else:
                    mir, how = idr._chirality(pd1, ref)
                    if mir is None:
                        status = 'chirality not decided by the checked calculator'
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                status = 'error: %r' % (e,)
            n += 1
            methods[how] = methods.get(how, 0) + 1
            if status == 'ok' and mir == cert['mirror']:
                continue
            new = names.with_mirror(cert['ref'], mir) if status == 'ok' else None
            bad.append({'line': li, 'old': r['dst'], 'new': new, 'how': how, 'status': status,
                        'was_by': cert['chirality_by'], 'src': r['src'], 'move': {k: r[k] for k in KEYS if k in r}})
    return {'pass': pn, 'shard': shard, 'checked': n, 'methods': methods, 'bad': bad}


def check(kv):
    out = kv['out']
    only = set(kv['passes'].split(',')) if 'passes' in kv else None
    done = set()
    if os.path.exists(out):
        with open(out) as f:
            for line in f:
                if line.endswith('\n'):
                    r = json.loads(line)
                    done.add((r['pass'], r['shard']))
    files = [x for x in passes.pass_files() + passes.pass_files(bands=True)
             if (only is None or x[0] in only) and (x[0], x[1]) not in done]
    print('%d pass shards to check' % len(files), flush=True)
    t0 = time.time()
    n = nb = 0
    with mp.Pool(int(kv.get('procs', 3)), maxtasksperchild=40) as pool, open(out, 'a') as f:
        for k, r in enumerate(pool.imap_unordered(check_shard, files)):
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
            f.flush()
            n += r['checked']
            nb += len(r['bad'])
            if (k + 1) % 50 == 0 or k + 1 == len(files):
                print('  %d/%d shards, %d records checked, %d not confirmed, %.0fs'
                      % (k + 1, len(files), n, nb, time.time() - t0), flush=True)
    print('CHECK_DONE %d records checked, %d not confirmed' % (n, nb), flush=True)


def apply(report, dirs):
    fixes = {}
    with open(report) as f:
        for line in f:
            r = json.loads(line)
            if r['bad']:
                fixes[(r['pass'], r['shard'])] = {b['line']: b for b in r['bad']}
    os.makedirs(os.path.join(DATA, 'corrections'), exist_ok=True)
    log = open(os.path.join(DATA, 'corrections', 'chirality.jsonl'), 'a')
    logged = set()
    for d in dirs:
        nfix = 0
        for (pn, shard), bad in sorted(fixes.items()):
            path = None
            for ext in ('.jsonl.gz', '.jsonl'):
                p = os.path.join(d, pn, shard + ext)
                if os.path.exists(p):
                    path = p
            if path is None:
                continue
            op = gzip.open if path.endswith('.gz') else open
            with op(path, 'rt') as f:
                lines = f.readlines()
            for li, b in bad.items():
                r = json.loads(lines[li])
                if r.get('dst') != b['old'] or any(r.get(k) != v for k, v in b['move'].items()):
                    if r.get('dst') == b['new'] or (b['new'] is None and r.get('dst') is None):
                        continue                        # already repaired
                    raise RuntimeError('%s %s line %d is not the record of the report' % (pn, shard, li))
                cert = dict(r['cert'])
                if b['new'] is None:
                    r['dst'], r['kind'] = None, 'unknown'
                    r['cert'] = {'type': 'none', 'why': 'matched %s up to mirror; %s (repair 2026-11-15)'
                                                        % (cert['ref'], b['status']), 'isosig': cert.get('isosig')}
                else:
                    r['dst'] = b['new']
                    cert['mirror'] = not cert['mirror']
                    cert['chirality_by'] = b['how']
                    cert['repaired'] = '2026-11-15: was %s by an unchecked calculator run' % b['old']
                    r['cert'] = cert
                lines[li] = json.dumps(r, separators=(',', ':')) + '\n'
                nfix += 1
                if (pn, shard, li) not in logged:
                    logged.add((pn, shard, li))
                    log.write(json.dumps(dict(b, **{'pass': pn, 'shard': shard}), separators=(',', ':')) + '\n')
            with op(path + '.tmp', 'wt') as f:
                f.writelines(lines)
            os.replace(path + '.tmp', path)
        print('%s: %d records rewritten' % (d, nfix), flush=True)
    log.close()


def main():
    kv = dict(a.split('=', 1) for a in sys.argv[2:] if '=' in a)
    pos = [a for a in sys.argv[2:] if '=' not in a]
    if sys.argv[1] == 'check':
        check(kv)
    else:
        dirs = kv['dirs'].split(',') if 'dirs' in kv else ['/home/user/mrcalc_stage/passes', os.path.join(DATA, 'passes')]
        apply(pos[0], dirs)


if __name__ == '__main__':
    main()
