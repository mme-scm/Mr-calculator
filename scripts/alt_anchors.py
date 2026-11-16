"""Alternating knots outside the KnotInfo table, for rule N1a of RULES_U.md (u = sigma/2 on alternating knots).

Rule N1a needs two facts about a node: that the knot is alternating, and its signature.  Inside the table both
are tabulated.  Outside it they are computed here from the pass records that produced the node:

  alternating   by the census name (K14a..., K15a...: the 'a' of the census table, as rule C8 of the main
                problem uses it; the identity of the node with the census knot is the record's certificate), or
                by an alternating diagram: the result diagram of a record whose result is the node
  signature     exact, from the Seifert matrix of the result diagram of a record whose result is the node
                (mrcalc/alg.py; the sign convention of section 3): the record with the smallest diagram; for a
                sample of the knots a second record of the knot or its mirror image, which must agree (mirror
                image: opposite sign).  checker/check_u.py recomputes the signatures it meets with spherogram.

usage: alt_anchors.py [procs=2] [out=data/alt_anchors.jsonl]  (stored gzipped: data/alt_anchors.jsonl.gz) [check=10] [hyp]
  check=k  one knot in k gets its signature from a second record as well (default 10)
  hyp      also looks for alternating result diagrams of unnamed hyperbolic knots (slow, few)
       alt_anchors.py certify file=<rows, .jsonl or .jsonl.gz> [procs=2]
  rows whose record diagram is not alternating get an alternating diagram of the knot where one is found
Output, one line per knot (the chirality of the first record):
  {"node", "signature", "by": "census name" | "alternating diagram", "pd": the diagram the signature is from,
   "alt_diagram": that diagram is alternating, "ref": the record, "agree": number of further records checked}
A disagreement between two records of one knot is an error: nothing is written and the exit status is 2.
"""
import json
import multiprocessing as mp
import os
import re
import sys
import time
import zlib
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import alg, names, passes  # noqa: E402
from mrcalc import pd as P  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

RX_CENSUS = re.compile(r'"dst":"(K\d+a\d+\*?)"')
RX_HYP = re.compile(r'"dst":"(H:[^"]+)"')
RX_N = re.compile(r'"n":(\d+)')
KEYS = ('t', 'd', 'i', 'e', 'h', 'axis', 'a', 'b', 's', 'r2', 'src', 'dst')


def scan(args):
    """Per knot, the occurrence with the smallest result diagram in one pass shard: census-alternating results
    and, with hyp, unnamed hyperbolic results whose result diagram is homogeneous (an alternating diagram is
    homogeneous)."""
    pn, shard, path, hyp = args
    seen = {}
    with passes._open(path) as f:
        for li, line in enumerate(f):
            m = RX_CENSUS.search(line)
            if m is None:
                if not hyp or '"hg":true' not in line:
                    continue
                m = RX_HYP.search(line)
                if m is None:
                    continue
            name = m.group(1)
            k = RX_N.search(line)
            n = int(k.group(1)) if k else 999
            base = name.rstrip('*')
            if base not in seen or n < seen[base][0]:
                seen[base] = (n, li, name)
    return pn, shard, path, seen


def result_pd(pd0, r):
    return passes.result_pd(pd0, r)          # band moves included (passes.band_pd)


def compute(args):
    pn, shard, path, lines = args
    want = set(lines)
    diags = {d['id']: d for d in passes.load_diagrams(shard)}
    out = []
    with passes._open(path) as f:
        for li, line in enumerate(f):
            if li not in want:
                continue
            r = json.loads(line)
            pd1 = result_pd(diags[r['d']]['pd'], r)
            out.append({'node': r['dst'], 'signature': alg.signature(pd1),
                        'alt_diagram': bool(P.Diagram.from_pd(pd1).is_alternating_diagram()), 'pd': pd1,
                        'ref': dict({k: r[k] for k in KEYS if k in r}, **{'pass': pn, 'shard': shard, 'line': li})})
    return out


def alternating_diagram(row, tries=40):
    """An alternating diagram of the knot of a row whose record diagram is not alternating: the record diagram
    is simplified by spherogram (Reidemeister moves; random backtracking between attempts) until it is
    alternating.  It is accepted when the identifier names it as the same knot (same chirality) and its
    signature is the one of the record diagram.  Returns the PD code or None."""
    import spherogram
    L = spherogram.Link([list(x) for x in row['pd']])
    for k in range(tries):
        L.simplify('global')
        pd2 = [list(x) for x in L.PD_code(min_strand_index=1)]
        if pd2 and P.Diagram.from_pd(pd2).is_alternating_diagram():
            if alg.signature(pd2) != row['signature']:
                return None
            res = passes.identifier().identify(pd2)
            return pd2 if res['name'] == row['node'] else None
        L.backtrack(steps=10 + 2 * k)
    return None


def certify_task(row):
    try:
        return row['node'], alternating_diagram(row)
    except BaseException as e:                       # cysignals errors are BaseExceptions
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        return row['node'], None


def certify(path, procs):
    """Rows that rest on the census name get an alternating diagram where one is found (fields pd, alt_diagram,
    alt_from: the record diagram was simplified and identified again)."""
    import gzip
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt') as f:
        rows = [json.loads(line) for line in f]
    todo = [r for r in rows if not r['alt_diagram']]
    print('%d rows, %d without an alternating diagram' % (len(rows), len(todo)), flush=True)
    t0 = time.time()
    found = {}
    with mp.Pool(procs, maxtasksperchild=200) as pool:
        for k, (node, pd2) in enumerate(pool.imap_unordered(certify_task, todo, chunksize=8)):
            if pd2 is not None:
                found[node] = pd2
            if (k + 1) % 500 == 0:
                print('  %d/%d, %d found, %.0fs' % (k + 1, len(todo), len(found), time.time() - t0), flush=True)
    for r in rows:
        if r['node'] in found:
            r['pd'], r['alt_diagram'] = found[r['node']], True
            r['alt_from'] = 'the record diagram simplified by spherogram; identified as the same knot'
    with op(path + '.tmp', 'wt') as f:
        for r in rows:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    os.replace(path + '.tmp', path)
    print('CERTIFY_DONE %d of %d now have an alternating diagram, %.0fs' % (len(found), len(todo), time.time() - t0),
          flush=True)


def main():
    kv = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
    procs = int(kv.get('procs', 2))
    if 'certify' in sys.argv[1:]:
        return certify(kv['file'], procs)
    out = kv.get('out', os.path.join(DATA, 'alt_anchors.jsonl'))
    hyp = 'hyp' in sys.argv[1:]
    check = int(kv.get('check', 10))
    files = [f + (hyp,) for f in passes.pass_files() + passes.pass_files(bands=True)]
    t0 = time.time()
    refs = defaultdict(list)                       # knot (no mirror mark) -> [(crossings, pass, shard, path, line)]
    with mp.Pool(procs) as pool:
        for pn, shard, path, seen in pool.imap_unordered(scan, files, chunksize=8):
            for base, (n, li, name) in seen.items():
                refs[base].append((n, pn, shard, path, li))
        print('%d pass shards read, %d knots (%d by census name), %.0fs'
              % (len(files), len(refs), sum(1 for b in refs if b.startswith('K')), time.time() - t0), flush=True)
        todo = defaultdict(list)
        for base, lst in refs.items():
            lst.sort()
            # the smallest diagram; for one knot in `check`, a second record from another pass shard
            take = lst[:2] if zlib.crc32(base.encode()) % check == 0 else lst[:1]
            for n, pn, shard, path, li in take:
                todo[(pn, shard, path)].append(li)
        tasks = [k + (v,) for k, v in sorted(todo.items())]
        print('%d records to compute in %d pass shards' % (sum(len(t[3]) for t in tasks), len(tasks)), flush=True)
        got = defaultdict(list)
        for k, res in enumerate(pool.imap_unordered(compute, tasks, chunksize=2)):
            for r in res:
                got[r['node'].rstrip('*')].append(r)
            if (k + 1) % 200 == 0:
                print('  %d/%d shards, %.0fs' % (k + 1, len(tasks), time.time() - t0), flush=True)
    bad = []
    rows = []
    for base in sorted(got):
        lst = sorted(got[base], key=lambda r: (len(r['pd']), r['ref']['pass'], r['ref']['shard'], r['ref']['line']))
        census = base.startswith('K')
        if not census:
            lst = [r for r in lst if r['alt_diagram']] + [r for r in lst if not r['alt_diagram']]
            if not lst[0]['alt_diagram']:
                continue                              # no alternating diagram among the records looked at
        first = lst[0]
        for r in lst[1:]:
            s = r['signature'] if r['node'] == first['node'] else -r['signature']
            if s != first['signature']:
                bad.append({'knot': base, 'records': [first['ref'], r['ref']],
                            'signatures': [first['signature'], r['signature']], 'nodes': [first['node'], r['node']]})
        if first['signature'] % 2:
            bad.append({'knot': base, 'odd signature': first['signature'], 'record': first['ref']})
        rows.append({'node': first['node'], 'signature': first['signature'],
                     'by': 'census name' if census else 'alternating diagram', 'alt_diagram': first['alt_diagram'],
                     'pd': first['pd'], 'ref': first['ref'], 'agree': len(lst) - 1})
    print('%d knots with a signature (%d by census name, %d by an alternating diagram; %d of the census knots '
          'with an alternating result diagram), %d knots checked on a second record, %.0fs'
          % (len(rows), sum(1 for r in rows if r['by'] == 'census name'),
             sum(1 for r in rows if r['by'] != 'census name'),
             sum(1 for r in rows if r['by'] == 'census name' and r['alt_diagram']),
             sum(1 for r in rows if r['agree']), time.time() - t0), flush=True)
    if bad:
        with open(out + '.disagreements', 'w') as f:
            for b in bad:
                f.write(json.dumps(b, separators=(',', ':')) + '\n')
        print('ERROR: %d disagreements, see %s.disagreements; nothing written' % (len(bad), out), flush=True)
        sys.exit(2)
    with open(out + '.tmp', 'w') as f:
        for r in rows:
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
    os.replace(out + '.tmp', out)
    print('ALT_ANCHORS_DONE %s' % out, flush=True)


if __name__ == '__main__':
    main()
