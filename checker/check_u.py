"""Independent check of the output of scripts/solve_u.py (ranges of u_Z and u_R, rules N1-N5 of RULES_U.md).

usage: check_u.py <dir of solve_u.py> [<data dir = data>]

Does not import the pipeline.  Reads the tabulated data (knotinfo.jsonl, knotinfo_qa.json), the cited rule
instances (u_constraints.jsonl.gz) and the events (u_events_Z.jsonl.gz, u_events_R.jsonl.gz) and verifies
  1. every rule instance: the value of an anchor (N1t by the torus formula, N1a/N1q/N2z from the table), the
     bounds of a twist (N3) and of a band move (N4) from its parameters, the record behind it (e = s - (w1-w0),
     twist parameters), mirror pairs and summands of table names;
  2. every event: its value follows from its constraint and the values of its input events, which are earlier
     events on the right nodes and sides (u_Z: rounded inwards, rule N5);
  3. every bound of u_knots.csv is the value of an event on that node (the tightest one in the file).
Exit status 0: all checks pass."""
import csv
import gzip
import importlib.util
import json
import os
import sys
from fractions import Fraction
from math import ceil, floor

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('main_check', os.path.join(HERE, 'check.py'))
_main = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_main)
torus_upsilon = _main.torus_upsilon


def num(s):
    return None if s is None or s == '' else Fraction(s)


def n3(a, b, h):
    l, m = abs(a - b), min(a, b)
    lo = -((l * l) // 4)
    hi = m - (((l - 1) * (l - 1)) // 4)
    return (Fraction(lo), Fraction(hi)) if h > 0 else (Fraction(-hi), Fraction(-lo))


def n4(e):
    return Fraction(e - 2, 4), Fraction(e + 2, 4)


class Check:
    def __init__(self, out, data):
        self.out, self.data = out, data
        self.err = []
        self.count = {}
        self.table = {}
        with open(os.path.join(data, 'knotinfo.jsonl')) as f:
            for line in f:
                r = json.loads(line)
                self.table[r['name']] = r
        qa = os.path.join(data, 'knotinfo_qa.json')
        self.qa = set(json.load(open(qa))['names']) if os.path.exists(qa) else set()
        self.unchecked = {}

    def bad(self, msg):
        if len(self.err) < 50:
            self.err.append(msg)
        self.count['errors'] = self.count.get('errors', 0) + 1

    def tick(self, k):
        self.count[k] = self.count.get(k, 0) + 1

    def skip(self, k):
        self.unchecked[k] = self.unchecked.get(k, 0) + 1

    # ---- names of table knots
    def tab(self, name):
        base = name.rstrip('*')
        r = self.table.get(base)
        if r is None or name.count('*') > 1:
            return None, 1
        return r, (-1 if name.endswith('*') else 1)

    def mirror_name(self, name):
        if name == '0_1':
            return name
        if '#' in name:
            return None
        r, s = self.tab(name)
        if r is None:
            return None
        if r['amphichiral']:
            return name.rstrip('*')
        return name[:-1] if name.endswith('*') else name + '*'

    # ---- 1. rule instances
    def instance_bounds(self, c):
        """(from, to, lo, hi) of u(to) - u(from) for the instance of a diff / self constraint."""
        ins = c['instance']
        par, rec = ins['par'], ins.get('record') or {}
        # direction of the record: a twist or band record goes from its source to its result; a crossing-change
        # record goes from K+ to K- when it changes a positive crossing (s = 1), from K- to K+ otherwise
        if rec.get('src') is not None and rec.get('dst') is not None:
            want = (rec['src'], rec['dst'])
            if rec.get('t') == 'cc' and rec.get('s') == -1:
                want = (rec['dst'], rec['src'])
            if set(want) == {ins['from'], ins['to']} and want[0] != want[1]:
                if want != (ins['from'], ins['to']):
                    self.bad('%s: the record runs the other way' % c['id'])
                self.tick('record directions checked')
            else:
                self.skip('record directions (the record names a node by an alias)')
        if ins['rule'] == 'N3':
            lo, hi = n3(par['a'], par['b'], par['h'])
            if rec.get('t') == 'tw':
                if sorted((rec['a'], rec['b'])) != sorted((par['a'], par['b'])) or rec['h'] != par['h']:
                    self.bad('%s: twist record does not match the parameters' % c['id'])
                if (rec['a'] - rec['b']) ** 2 != (rec['a'] + rec['b']) + rec['h'] * (rec['w1'] - rec['w0']):
                    self.bad('%s: writhe identity of the twist record fails' % c['id'])
            elif rec.get('t') == 'cc':
                if (par['a'], par['b'], par['h']) != (1, 1, 1):
                    self.bad('%s: crossing change with other parameters than a = b = 1, right-handed' % c['id'])
                if rec['w1'] - rec['w0'] != -2 * rec['s']:
                    self.bad('%s: writhe change of the crossing-change record' % c['id'])
                # the record goes from K+ to K- when it changes a positive crossing
                self.tick('crossing-change records')
            else:
                self.bad('%s: N3 instance without a twist or crossing-change record' % c['id'])
        elif ins['rule'] == 'N4':
            if rec.get('t') != 'bm' or rec['e'] != par['e'] or rec['e'] != rec['s'] - (rec['w1'] - rec['w0']):
                self.bad('%s: band record does not give e' % c['id'])
            if rec.get('s') not in (1, -1) or rec['e'] % 2:
                self.bad('%s: band record with a bad sign or parity' % c['id'])
            lo, hi = n4(par['e'])
        else:
            self.bad('%s: unknown rule %r' % (c['id'], ins['rule']))
            return None
        return ins['from'], ins['to'], lo, hi

    def check_constraint(self, c):
        t = c['type']
        self.tick('constraints: ' + t)
        if t == 'unary':
            v, par, n = num(c['value']), c['par'], c['node']
            r, sgn = self.tab(n)
            if c['rule'] == 'N1t':
                if v != torus_upsilon(par['p'], par['q']):
                    self.bad('%s: torus value' % c['id'])
            elif c['rule'] in ('N1a', 'N1q'):
                if r is None:
                    self.bad('%s: not a table knot' % c['id'])
                    return
                if r['signature'] is None or sgn * r['signature'] != par['signature'] or v != Fraction(par['signature'], 2):
                    self.bad('%s: signature' % c['id'])
                if c['rule'] == 'N1a' and r['alternating'] is not True:
                    self.bad('%s: not tabulated as alternating' % c['id'])
                if c['rule'] == 'N1q' and r['name'] not in self.qa:
                    self.bad('%s: not tabulated as quasi-alternating' % c['id'])
            elif c['rule'] == 'N2z':
                if v != 0 or not (n == '0_1' or (r is not None and r.get('slice') is True)):
                    self.bad('%s: slice' % c['id'])
            else:
                self.bad('%s: unknown anchor rule' % c['id'])
        elif t == 'amphichiral':
            m = self.mirror_name(c['node'])
            if m is None:
                self.skip('amphichiral nodes outside the table (certificate in the main export)')
            elif m != c['node']:
                self.bad('%s: not amphichiral' % c['id'])
        elif t == 'mirror':
            a, b = c['nodes']
            m = self.mirror_name(a)
            if m is None:
                # composite of table knots: mirror summand by summand
                if '#' in a and all(self.mirror_name(x) for x in a.split('#')):
                    if sorted(self.mirror_name(x) for x in a.split('#')) != sorted(b.split('#')):
                        self.bad('%s: mirror of a composite' % c['id'])
                elif a.rstrip('*') == b.rstrip('*') and a != b:
                    self.skip('mirror pairs outside the table checked by name only')
                else:
                    self.skip('mirror pairs outside the table (names differ: alias in the main export)')
            elif m != b:
                self.bad('%s: mirror' % c['id'])
        elif t == 'sum':
            parts = []
            for p, m in c['parts']:
                parts += [p] * m
            if all(self.tab(x)[0] is not None for x in c['node'].split('#')):
                if sorted('#'.join(parts).split('#')) != sorted(c['node'].split('#')):
                    self.bad('%s: summands' % c['id'])
            else:
                self.skip('sums with a summand outside the table')
        elif t in ('diff', 'self'):
            b = self.instance_bounds(c)
            if b is None:
                return
            frm, to, lo, hi = b
            v = num(c['value'])
            if t == 'diff':
                A, B = c['nodes']
                if (frm, to) == (A, B):
                    l2, h2 = lo, hi
                elif (frm, to) == (B, A):
                    l2, h2 = -hi, -lo
                else:
                    self.bad('%s: the instance joins other nodes' % c['id'])
                    return
            else:
                A, M = c['node'], c['mirror']
                if (frm, to) == (A, M):          # u(M) - u(A) = -2 u(A)
                    l2, h2 = -hi / 2, -lo / 2
                elif (frm, to) == (M, A):        # u(A) - u(M) = 2 u(A)
                    l2, h2 = lo / 2, hi / 2
                else:
                    self.bad('%s: the instance joins other nodes' % c['id'])
                    return
            if v != (l2 if c['bound'] == 'lo' else h2):
                self.bad('%s: bound %s is %s, the instance gives %s' % (c['id'], c['bound'], v, (l2, h2)))
        else:
            self.bad('%s: unknown constraint type' % c['id'])

    # ---- 2. events
    def check_events(self, tag, cons):
        integer = tag == 'Z'
        ev = {}
        best = {}
        path = os.path.join(self.out, 'u_events_%s.jsonl.gz' % tag)
        with gzip.open(path, 'rt') as f:
            for line in f:
                e = json.loads(line)
                k, n, side, v = e['id'], e['node'], e['side'], num(e['value'])
                c = cons.get(e['con'])
                if c is None:
                    self.bad('event %s %d: constraint %s is missing' % (tag, k, e['con']))
                    continue
                ins = []
                ok = True
                for i in e['ins']:
                    if i not in ev or i >= k:
                        self.bad('event %s %d: input event %d is not an earlier event' % (tag, k, i))
                        ok = False
                    else:
                        ins.append(ev[i])
                if not ok:
                    continue
                want = self.derive(c, n, side, ins)
                if want is None:
                    self.bad('event %s %d (%s): inputs do not fit the constraint %s' % (tag, k, n, e['con']))
                else:
                    if integer:
                        want = Fraction(ceil(want)) if side == 'lo' else Fraction(floor(want))
                    if want != v:
                        self.bad('event %s %d (%s %s): value %s, derived %s' % (tag, k, n, side, v, want))
                ev[k] = (n, side, v)
                b = best.setdefault(n, [None, None])
                if side == 'lo':
                    b[0] = v if b[0] is None else max(b[0], v)
                else:
                    b[1] = v if b[1] is None else min(b[1], v)
                self.tick('events ' + tag)
        return best

    def derive(self, c, n, side, ins):
        t = c['type']
        if t == 'unary':
            return num(c['value']) if (n == c['node'] and not ins) else None
        if t == 'amphichiral':
            return Fraction(0) if (n == c['node'] and not ins) else None
        if t == 'self':
            return num(c['value']) if (n == c['node'] and c['bound'] == side and not ins) else None
        if t == 'mirror':
            if len(ins) != 1 or set(c['nodes']) != {n, ins[0][0]} or ins[0][1] == side:
                return None
            return -ins[0][2]
        if t == 'diff':
            A, B = c['nodes']
            v = num(c['value'])
            if len(ins) != 1 or ins[0][1] != side:
                return None
            m, x = ins[0][0], ins[0][2]
            if n == B and m == A and c['bound'] == side:        # x(B) >= x(A) + l ;  x(B) <= x(A) + h
                return x + v
            if n == A and m == B and c['bound'] != side:        # x(A) >= x(B) - h ;  x(A) <= x(B) - l
                return x - v
            return None
        if t == 'sum':
            N, parts = c['node'], c['parts']
            if n == N:
                if [(i[0], i[1]) for i in ins] != [(p, side) for p, _ in parts]:
                    return None
                return sum(m * i[2] for (p, m), i in zip(parts, ins))
            js = [j for j, (p, m) in enumerate(parts) if p == n]
            if len(js) != 1 or not ins:
                return None
            j = js[0]
            others = parts[:j] + parts[j + 1:]
            opp = 'hi' if side == 'lo' else 'lo'
            if (ins[0][0], ins[0][1]) != (N, side) or [(i[0], i[1]) for i in ins[1:]] != [(p, opp) for p, _ in others]:
                return None
            return (ins[0][2] - sum(m * i[2] for (p, m), i in zip(others, ins[1:]))) / parts[j][1]
        return None

    def run(self):
        cons = {}
        with gzip.open(os.path.join(self.out, 'u_constraints.jsonl.gz'), 'rt') as f:
            for line in f:
                c = json.loads(line)
                if c['id'] in cons:
                    self.bad('constraint id %s twice' % c['id'])
                cons[c['id']] = c
                self.check_constraint(c)
        best = {tag: self.check_events(tag, cons) for tag in ('Z', 'R')}
        with open(os.path.join(self.out, 'u_knots.csv')) as f:
            for row in csv.DictReader(f):
                for tag in ('Z', 'R'):
                    b = best[tag].get(row['node'], [None, None])
                    if [num(row['u%s_lo' % tag]), num(row['u%s_hi' % tag])] != b:
                        self.bad('%s: u_%s range %s..%s is not that of the events %s' % (
                            row['node'], tag, row['u%s_lo' % tag], row['u%s_hi' % tag], b))
                    if tag == 'Z' and any(x is not None and x.denominator != 1 for x in b):
                        self.bad('%s: u_Z bound is not an integer' % row['node'])
                self.tick('core nodes')
        return self


def main():
    out = sys.argv[1]
    data = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(HERE), 'data')
    C = Check(out, data).run()
    for k, v in sorted(C.count.items()):
        print('%-40s %d' % (k, v))
    for k, v in sorted(C.unchecked.items()):
        print('not checked here: %s: %d' % (k, v))
    for m in C.err:
        print('ERROR', m)
    print('RESULT: %s' % ('OK' if not C.err else 'FAILED (%d errors)' % C.count.get('errors', 0)))
    sys.exit(0 if not C.err else 1)


if __name__ == '__main__':
    main()
