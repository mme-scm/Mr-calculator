"""Budget selection among the adjacent nodes of scripts/targets.py (search planning; no rule is applied).
Keeps the n nodes outside the table that decide the most open knots (ties: fewer values left, then name).
usage: select_adjacent.py <adjacent.jsonl> <out prefix> [n=3000] [inv=M]
writes <out prefix>.jsonl (the kept lines, for target_diagrams.py g2) and <out prefix>.txt (their names)"""
import json, sys
src, out = sys.argv[1:3]
kv = dict(a.split('=', 1) for a in sys.argv[3:] if '=' in a)
n, inv = int(kv.get('n', 3000)), kv.get('inv', 'M')
rows = [json.loads(l) for l in open(src)]
rows = [r for r in rows if r['kind'] in ('census', 'hyp')]
rows.sort(key=lambda r: (-len(r['decides']), len(r[inv]), r['node']))
keep = rows[:n]
with open(out + '.jsonl', 'w') as f:
    for r in keep:
        f.write(json.dumps(r, separators=(',', ':')) + '\n')
with open(out + '.txt', 'w') as f:
    for r in keep:
        f.write(r['node'] + '\n')
print('%d of %d adjacent nodes outside the table kept; they decide between %d and %d open knots each'
      % (len(keep), len(rows), len(keep[-1]['decides']) if keep else 0, len(keep[0]['decides']) if keep else 0))
