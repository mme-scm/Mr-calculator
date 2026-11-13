"""Targets of the targeted search for M (search planning; reads an export or a scratch solve, applies no rule).
open knots: nodes of the core (tier <= 13) whose M is not pinned.
adjacent nodes: the other end N of a difference constraint (F7 crossing change, F9 twist) on an open knot K
such that N's own M is open and some value still possible for M(N) would, through that inequality, leave
exactly one of the values still possible for M(K).  Pinning N to such a value decides K.
The lists say where further moves are computed (other diagrams of the open knots, moves from the adjacent
nodes); the records those moves produce are ordinary pass records.
usage: targets.py <export dir> <out prefix> [tmax=13]
writes <out prefix>_open.txt (open knots, one name per mirror pair) and <out prefix>_adjacent.jsonl"""
import collections, glob, gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import solver
X, OUT = sys.argv[1].rstrip("/") + "/", sys.argv[2]
kv = dict(a.split('=', 1) for a in sys.argv[3:] if '=' in a)
tmax = int(kv.get('tmax', 13))
def parts(name):
    for p in sorted(glob.glob(X + name + '*.jsonl.gz'), key=lambda p: (len(p), p)):
        with gzip.open(p, 'rt') as f:
            for line in f:
                yield line
cand, tier, kind = {}, {}, {}
for line in parts('knots'):
    k = json.loads(line)
    F = k['domains']['F']
    cand[k['node']] = [e[0] for e in F.get('e', [])] if isinstance(F, dict) and 'e' in F else None
    tier[k['node']] = k.get('tier'); kind[k['node']] = k['kind']
core = lambda n: isinstance(tier.get(n), int) and tier[n] <= tmax
openK = {n for n in cand if core(n) and cand[n] and len(cand[n]) > 1}
adj = collections.defaultdict(dict)      # N -> {K: [(rule, par, value of M(N), value it leaves for M(K))]}
nedge = 0
for line in parts('constraints'):
    if '"rule":"F9"' not in line and '"rule":"F7"' not in line:
        continue
    c = json.loads(line)
    if 'coef' in (c.get('par') or {}) or len(c['nodes']) != 2:
        continue
    A, B = c['nodes']
    lo, hi = solver._diff_bounds(c)          # lo <= M(B) - M(A) <= hi
    for K, N, sgn in ((A, B, 1), (B, A, -1)):
        if K not in openK or not cand.get(N) or len(cand[N]) < 2:
            continue
        for mN in cand[N]:
            left = [m for m in cand[K] if lo <= sgn * (mN - m) <= hi]
            if 0 < len(left) < len(cand[K]) and len(left) == 1:
                adj[N].setdefault(K, []).append((c['rule'], c.get('par'), mN, left[0]))
                nedge += 1
base = lambda n: n[:-1] if n.endswith('*') else n
openB = sorted({base(n) for n in openK})
with open(OUT + '_open.txt', 'w') as f:
    f.write('\n'.join(openB) + '\n')
with open(OUT + '_adjacent.jsonl', 'w') as f:
    for N in sorted(adj):
        f.write(json.dumps({'node': N, 'kind': kind[N], 'tier': tier[N], 'M': cand[N],
                            'decides': {K: sorted({(v[2], v[3]) for v in vs}) for K, vs in adj[N].items()}}) + '\n')
decided = {K for N in adj for K in adj[N]}
print('open knots (tier <= %d): %d nodes, %d up to mirror' % (tmax, len(openK), len(openB)))
print('open knots with at least one adjacent node that could decide them:', len(decided), '(%d up to mirror)' % len({base(k) for k in decided}))
print('adjacent deciding nodes:', len(adj), dict(collections.Counter(('core' if core(n) else 'larger') for n in adj)))
print('   by kind:', dict(collections.Counter(kind[n] for n in adj)))
per = collections.Counter(min(sum(1 for N in adj if K in adj[N]), 20) for K in decided)
print('   deciding neighbours per open knot (20 = 20 or more):', sorted(per.items()))
c = collections.Counter(tier[k] for k in openK); d = collections.Counter(tier[k] for k in decided)
print('   by tier: open', sorted(c.items()), 'with a deciding neighbour', sorted(d.items()))
