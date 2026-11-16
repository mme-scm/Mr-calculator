"""Nodes with M pinned and u_M not determined (a join of two solves; no rule is applied).

usage: m_vs_u.py base=<ablation_base.pkl of the full run> u=<u_nodes.csv.gz of solve_u.py allnodes>
                 [lost=<json of ablate_nodes.py withheld=coincidence nodes=all lost>] [out=<file.csv.gz>]

For every node with M pinned in the full run: the range of u_M (and u_Z), and two marks for "surgery decided M":
  chain   the chain of the M pin in the full run uses a rule of the coincidence family (S1-S4, F10)
  needed  M is not pinned when the coincidence family is withheld (only with lost=)
Prints counts; out= lists the nodes with M pinned and u_M not determined.
"""
import collections
import csv
import gzip
import json
import os
import pickle
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc.solver import FAMILIES  # noqa: E402


def num(s):
    return None if s in ('', None) else Fraction(s)


def width_class(lo, hi):
    if lo is None and hi is None:
        return 'unbounded'
    if lo is None or hi is None:
        return 'one end'
    w = hi - lo
    return 'determined' if w == 0 else 'width 1' if w == 1 else 'width 2' if w == 2 else 'width > 2'


def group(kind, tier):
    if kind in ('table', 'composite', 'unknot') and tier not in ('', None) and int(tier) <= 13:
        return 'knots <= 13 crossings'
    return {'census': 'peripheral', 'hyp': 'peripheral'}.get(kind, 'other (14-15 crossings, cables, torus)')


def main():
    kv = dict(a.split('=', 1) for a in sys.argv[1:] if '=' in a)
    with open(kv['base'], 'rb') as f:
        base = pickle.load(f)
    coin = 0
    for r in FAMILIES['coincidence']:
        coin |= base['bit'].get(r, 0)
    needed = None
    if 'lost' in kv:
        with open(kv['lost']) as f:
            needed = {r['node'] for r in json.load(f)['rows']}
    cols = ['M pinned', 'u_M determined', 'width 1', 'width 2', 'width > 2', 'one end', 'unbounded']
    tabs = collections.OrderedDict((k, collections.defaultdict(collections.Counter)) for k in
                                   ['all nodes with M pinned', 'chain of M uses a coincidence rule',
                                    'M not pinned without coincidences'])
    zm = collections.Counter()
    rows = []
    seen = 0
    with gzip.open(kv['u'], 'rt', newline='') as f:
        for r in csv.DictReader(f):
            n = r['node']
            p = base['pins'].get(n)
            if not p or 'M' not in p:
                continue
            seen += 1
            lo, hi = num(r['uM_lo']), num(r['uM_hi'])
            zlo, zhi = num(r['uZ_lo']), num(r['uZ_hi'])
            wc = width_class(lo, hi)
            g = group(r['kind'], r['crossings'])
            chain = bool(base['mask'][n]['M'] & coin)
            need = needed is not None and n in needed
            for name, yes in (('all nodes with M pinned', True), ('chain of M uses a coincidence rule', chain),
                              ('M not pinned without coincidences', need)):
                if yes:
                    for gg in (g, 'all'):
                        tabs[name][gg]['M pinned'] += 1
                        tabs[name][gg]['u_M determined' if wc == 'determined' else wc] += 1
            zm[(width_class(zlo, zhi) == 'determined', wc == 'determined')] += 1
            if wc != 'determined':
                rows.append([n, r['kind'], r['crossings'], p['M'], r['uM_lo'], r['uM_hi'], r['uZ_lo'], r['uZ_hi'],
                             int(chain), '' if needed is None else int(need)])
    total = sum(1 for p in base['pins'].values() if 'M' in p)
    if seen != total:
        raise SystemExit('%d nodes with M pinned in the base, %d of them in the u table' % (total, seen))
    for name, tab in tabs.items():
        if name.startswith('M not pinned') and needed is None:
            continue
        print('\n%s\n' % name)
        print('| nodes | ' + ' | '.join(cols) + ' |\n|' + '---|' * (len(cols) + 1))
        for g in ['knots <= 13 crossings', 'other (14-15 crossings, cables, torus)', 'peripheral', 'all']:
            print('| %s | ' % g + ' | '.join(str(tab[g].get(c, 0)) for c in cols) + ' |')
    print('\nu_Z determined / u_M determined among the nodes with M pinned: both %d, u_M only %d, u_Z only %d, '
          'neither %d' % (zm[(True, True)], zm[(False, True)], zm[(True, False)], zm[(False, False)]))
    if 'out' in kv:
        with gzip.open(kv['out'], 'wt', newline='') as f:
            w = csv.writer(f)
            w.writerow(['node', 'kind', 'crossings', 'M', 'uM_lo', 'uM_hi', 'uZ_lo', 'uZ_hi',
                        'chain_uses_coincidence', 'M_needs_coincidence'])
            w.writerows(rows)
        print('\n%s: %d nodes with M pinned and u_M not determined' % (kv['out'], len(rows)))


if __name__ == '__main__':
    main()
