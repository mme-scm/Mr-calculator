"""The knots with u open, one line each: range of u (the same for u_Z, u_R, u_M) and the values left for M.
usage: u_open_table.py <dir of solve_u.py> <export dir>   (prints the lines)"""
import csv
import glob
import os
import sys

udir, edir = sys.argv[1], sys.argv[2]
u = {}
with open(os.path.join(udir, 'u_knots.csv')) as f:
    for r in csv.DictReader(f):
        if r['node'].endswith('*') or r['uZ_lo'] == r['uZ_hi']:
            continue
        if (r['uZ_lo'], r['uZ_hi']) != (r['uR_lo'], r['uR_hi']) or (r['uZ_lo'], r['uZ_hi']) != (r['uM_lo'], r['uM_hi']):
            raise SystemExit('the ranges of u_Z, u_R, u_M differ on %s' % r['node'])
        u[r['node']] = (r['uZ_lo'], r['uZ_hi'])
m = {}
for path in sorted(glob.glob(os.path.join(edir, 'knots*.csv'))):
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            if r['node'] in u:
                m[r['node']] = 'M = %s' % r['M_pin'] if r['M_pin'] != '' else 'M in {%s, %s}' % (r['M_lo'], r['M_hi'])


def key(n):
    a, b = n.split('_')
    return int(''.join(c for c in a if c.isdigit())), int(b)


for n in sorted(u, key=key):
    print('%s: u in [%s, %s]; %s' % (n, u[n][0], u[n][1], m.get(n, 'M: not in the export')))
