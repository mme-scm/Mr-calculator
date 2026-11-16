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
KEYS = ('t', 'd', 'i', 'e', 'h', 'axis', 'a', 'b', 's', 'src', 'dst')


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
    if r['t'] == 'bm':
        return P.band_smoothing(pd0, r['i'])[0]
    return passes.result_pd(pd0, r)


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


def main():
    kv = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
    procs = int(kv.get('procs', 2))
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
