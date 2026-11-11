"""Prebuild orientation-sensitive isometry signatures of census knots (14 or 15 crossings) so that the
identification service finds them by a dictionary hit.  Appends to the census reference file.
usage: build_census_refs.py <crossings> [procs]"""
import json
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import identify as I  # noqa: E402


def one(name):
    import snappy
    try:
        C = snappy.Manifold(name)
        if not I.verified(C):
            return {'name': name, 'sig': None, 'sig_mirror': None, 'verified': False}
        return {'name': name, 'sig': I.oriented_sig(C), 'sig_mirror': I.mirror_sig(C), 'verified': True}
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        return {'name': name, 'sig': None, 'sig_mirror': None, 'verified': False, 'error': repr(e)}


def main():
    import snappy
    cr = int(sys.argv[1])
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    have = set()
    if os.path.exists(I.REF_CENSUS):
        with open(I.REF_CENSUS) as f:
            for line in f:
                have.add(json.loads(line)['name'])
    names = [M.name() for M in snappy.HTLinkExteriors(crossings=cr, knots_vs_links='knots')]
    names = [n for n in names if n not in have]
    print('census knots with %d crossings to do: %d' % (cr, len(names)), flush=True)
    t0 = time.time()
    with mp.Pool(procs, maxtasksperchild=2000) as pool, open(I.REF_CENSUS, 'a') as f:
        for i, r in enumerate(pool.imap(one, names, chunksize=50)):
            f.write(json.dumps(r, separators=(',', ':')) + '\n')
            if (i + 1) % 5000 == 0:
                f.flush()
                print('  %d/%d %.0fs' % (i + 1, len(names), time.time() - t0), flush=True)
    print('done in %.0fs' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
