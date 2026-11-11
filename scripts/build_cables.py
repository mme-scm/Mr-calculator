"""Cable nodes C_{r,s}(K) (section 4): construction diagrams, identification with table knots,
calculator inputs under a time limit, Regina pool entries for small diagrams.
usage: build_cables.py [P_cab] [max companion crossings] [calculator timeout s] [max crossings for calculator]
Output: data/cables.jsonl (resumable), data/ref_nonhyp.jsonl (appended)."""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import identify as I, hfk as H, names, nodeset, config  # noqa: E402
from mrcalc.config import DATA  # noqa: E402

OUT = os.path.join(DATA, 'cables.jsonl')
_idr = None


def task(args):
    global _idr
    name, timeout, maxcr = args
    out = {'node': name}
    try:
        pd = nodeset.diagram(name)
        out['crossings'] = len(pd)
        if len(pd) <= 16:
            if _idr is None:
                _idr = I.Identifier()
            r = _idr.identify(pd)
            out['ident'], out['cert'] = r['name'], r['cert']
        if len(pd) <= maxcr:
            h = H.hfk(pd, timeout=timeout)
            if 'tau' in h:
                h['alex'] = H.alexander(h)
            out['hfk'] = h
        else:
            out['hfk'] = {'skipped': 'diagram has more than %d crossings' % maxcr}
        if len(pd) <= 40 and not out.get('ident'):
            try:
                out['pool'] = I.pool_record(name, pd, amphichiral=False, cap=200)
            except Exception as e:
                out['pool_error'] = repr(e)
    except Exception as e:
        out['error'] = repr(e)
    return out


def main():
    P = config.load_params()
    p_cab = int(sys.argv[1]) if len(sys.argv) > 1 else P['P_cab']
    maxc = int(sys.argv[2]) if len(sys.argv) > 2 else P['max_cable_companion_crossings']
    timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
    maxcr = int(sys.argv[4]) if len(sys.argv) > 4 else 70
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                done.add(json.loads(line)['node'])
    items = [(n, timeout, maxcr) for n in nodeset.cable_names(p_cab, maxc) if n not in done]
    items.sort(key=lambda x: (len(x[0]), x[0]))
    print('cables to do: %d' % len(items), flush=True)
    t0 = time.time()
    with mp.Pool(4) as pool, open(OUT, 'a') as f, open(I.REF_NONHYP, 'a') as g:
        for i, r in enumerate(pool.imap_unordered(task, items, chunksize=2)):
            pr = r.pop('pool', None)
            if pr is not None:
                g.write(json.dumps(pr, separators=(',', ':')) + '\n')
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
            if (i + 1) % 100 == 0:
                f.flush()
                print('  %d/%d %.0fs' % (i + 1, len(items), time.time() - t0), flush=True)
    print('cables done in %.0fs' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
