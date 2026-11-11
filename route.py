#!/usr/bin/env python3
"""Print the chain of a pinned value, with the move edges inlined.

usage: route.py <node> <invariant> [export_dir]

<invariant> is one of M, r_2, nu, r_0, tau, upsilon.  Only files of the export directory
(default: the directory `export` next to this file) are read; their formats are described in
export/FORMAT.md.  The output is

  * the numbered lines of chains/<node>.txt that belong to the chain of the invariant,
  * after each line, the details of its constraint's `ref`:
      - an edge id: the edge record of edges.jsonl (type, source and result node, both PD
        codes, the changed crossing / twisting circle / mutation circle, both certificates),
      - an object (certificate of a coincidence, lens filling, construction, ...): its JSON,
        and for the rules S1, S3, S4, F10, F16 the slopes of the constraint,
  * the `== <invariant> = <value> ...` line of the pin (last line of the output).

Exit status: 0 if the chain was printed, 1 if the invariant is not pinned, 2 on errors.
"""
import json
import os
import sys

INVARIANTS = ('M', 'r_2', 'nu', 'r_0', 'tau', 'upsilon')
SLOPE_RULES = ('S1', 'S3', 'S4', 'F10', 'F16')
PAD = '        '


def jsonl_parts(directory, name):
    """Paths X.jsonl, X.1.jsonl, X.2.jsonl, ... that exist, in order."""
    base = os.path.join(directory, name)
    paths = [base] if os.path.exists(base) else []
    k = 1
    while os.path.exists('%s.%d.jsonl' % (base[:-6], k)):
        paths.append('%s.%d.jsonl' % (base[:-6], k))
        k += 1
    return paths


def lines_of(directory, name):
    for path in jsonl_parts(directory, name):
        with open(path, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    yield line


def compact(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def find_node(directory, node):
    """The record of a node in knots.jsonl, or None."""
    needle = '"node":%s' % json.dumps(node)
    for line in lines_of(directory, 'knots.jsonl'):
        if needle in line:
            rec = json.loads(line)
            if rec.get('node') == node:
                return rec
    for line in lines_of(directory, 'knots.jsonl'):      # other JSON spelling of the name
        rec = json.loads(line)
        if rec.get('node') == node:
            return rec
    return None


def find_events(directory, ids):
    """event id -> record, for the wanted ids (event k is the k-th line)."""
    out = {}
    if not ids:
        return out
    last = max(ids)
    for k, line in enumerate(lines_of(directory, 'events.jsonl')):
        if k in ids:
            rec = json.loads(line)
            out[rec['id']] = rec
        if k >= last:
            break
    missing = [i for i in ids if i not in out]
    if missing:                                           # ids not equal to line numbers
        for line in lines_of(directory, 'events.jsonl'):
            rec = json.loads(line)
            if rec['id'] in ids:
                out[rec['id']] = rec
    return out


def find_constraints(directory, ids):
    """constraint id -> record, for the wanted ids."""
    out = {}
    for line in lines_of(directory, 'constraints.jsonl'):
        a = line.find('"id":"')
        if a >= 0:
            b = line.find('"', a + 6)
            if line[a + 6:b] not in ids:
                continue
        rec = json.loads(line)
        if rec.get('id') in ids:
            out[rec['id']] = rec
            if len(out) == len(ids):
                break
    return out


def find_edges(directory, ids):
    out = {}
    if ids:
        for line in lines_of(directory, 'edges.jsonl'):
            rec = json.loads(line)
            if rec.get('id') in ids:
                out[rec['id']] = rec
    return out


def pd_text(pd, flag=None):
    """PD code on one line; the crossing with index `flag` is wrapped in asterisks."""
    if not isinstance(pd, list):
        return compact(pd)
    return '[' + ', '.join(('*%s*' if k == flag else '%s') % compact(x) for k, x in enumerate(pd)) + ']'


def edge_lines(e):
    """Text lines describing an edge record of edges.jsonl."""
    t = e.get('type')
    out = ['edge %s: %s   source %s -> result %s' % (e.get('id'), t, e.get('source_node'), e.get('result_node'))]
    extra = ['%s=%s' % (k, compact(e[k])) for k in ('key', 'count', 'pass', 'source_diagram') if k in e]
    extra += ['%s=%s' % (k, compact(e[k])) for k in sorted(e) if k.startswith('diagram_')]
    if e.get('writhe_before') is not None or e.get('writhe_after') is not None:
        extra.append('writhe %s -> %s' % (e.get('writhe_before'), e.get('writhe_after')))
    if extra:
        out.append('  ' + '  '.join(extra))
    if t == 'crossing change':
        i = e.get('crossing')
        out.append('  K_plus = %s, K_minus = %s' % (e.get('K_plus'), e.get('K_minus')))
        out.append('  changed crossing: index %s, sign %s (marked * in pd)' % (i, _signed(e.get('sign'))))
        out.append('  pd        = %s' % pd_text(e.get('pd'), i))
    else:
        out.append('  pd        = %s' % pd_text(e.get('pd')))
    out.append('  result_pd = %s' % pd_text(e.get('result_pd')))
    if t == 'twist':
        h = e.get('handedness')
        hand = {1: ' (right-handed)', -1: ' (left-handed)'}.get(h, '')
        out.append('  twisting circle: crosses the edges %s, directions %s (+1 left-to-right, -1 right-to-left)'
                   % (compact(e.get('circle_edges')), compact(e.get('edge_directions'))))
        out.append('  a = %s, b = %s, handedness %s%s' % (e.get('a'), e.get('b'), _signed(h), hand))
        if e.get('insertion') is not None:
            out.append('  insertion: %s' % e.get('insertion'))
    elif t == 'mutation':
        out.append('  mutation circle: crosses the edges %s (cyclic order), rotation %s'
                   % (compact(e.get('circle_edges')), e.get('rotation')))
    out.append('  source certificate (%s): %s' % (e.get('source_node'), compact(e.get('source_certificate'))))
    out.append('  result certificate (%s): %s' % (e.get('result_node'), compact(e.get('result_certificate'))))
    return out


def _signed(x):
    return '%+d' % x if isinstance(x, int) and not isinstance(x, bool) else str(x)


def slope_lines(con):
    """Slopes of a surgery constraint, from its parameters."""
    par = con.get('par') or {}
    nodes = con.get('nodes') or []
    if 'sA' in par or 'sB' in par:
        a, b = par.get('sA'), par.get('sB')
        na = nodes[0] if nodes else '?'
        nb = nodes[1] if len(nodes) > 1 else na
        fmt = lambda s: '%s/%s' % (s[0], s[1]) if isinstance(s, list) and len(s) == 2 else compact(s)
        return ['slopes: %s on %s, %s on %s   (factors a = %s, b = %s)'
                % (fmt(a), na, fmt(b), nb, par.get('a'), par.get('b'))]
    if 'p' in par and 'q' in par:
        return ['slope: %s/%s on %s' % (par['p'], par['q'], nodes[0] if nodes else '?')]
    return []


def ref_lines(con, edges):
    """Lines printed below a chain line for the `ref` of its constraint."""
    ref = con.get('ref')
    out = []
    if isinstance(ref, str):
        if ref in edges:
            out.extend(edge_lines(edges[ref]))
        else:
            out.append('ref %s: not found in edges.jsonl' % ref)
    elif ref is not None:
        out.append('ref %s' % compact(ref))
    if con.get('rule') in SLOPE_RULES:
        out.extend(slope_lines(con))
    return out


def main(argv):
    if len(argv) not in (3, 4) or argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        return 2
    node, inv = argv[1], argv[2]
    directory = argv[3] if len(argv) == 4 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'export')
    if inv not in INVARIANTS:
        print('error: unknown invariant %r (one of %s)' % (inv, ', '.join(INVARIANTS)))
        return 2
    if not jsonl_parts(directory, 'knots.jsonl'):
        print('error: no knots.jsonl in %s' % directory)
        return 2
    rec = find_node(directory, node)
    if rec is None:
        print('error: node %r is not in knots.jsonl' % node)
        return 2
    pins = rec.get('pins') or {}
    if inv not in pins:
        print('%s: %s is not pinned' % (node, inv))
        return 1
    if not rec.get('chain'):
        print('error: %s has pins but no chain file' % node)
        return 2
    path = os.path.join(directory, rec['chain'])
    try:
        with open(path, encoding='utf-8') as f:
            lines = f.read().split('\n')
    except (IOError, OSError) as ex:
        print('error: cannot read %s: %s' % (path, ex))
        return 2
    head = '== %s = ' % inv
    pin_line = next((l for l in lines if l.startswith(head)), None)
    if pin_line is None or '; chain ' not in pin_line:
        print('error: %s has no line "%s..."' % (path, head))
        return 2
    wanted = {int(x) for x in pin_line.split('; chain ', 1)[1].split(',') if x.strip()}
    chain = []                       # (line, event id)
    for l in lines:
        if l[:1].isdigit():
            num, rest = l.split('.', 1)
            if int(num) in wanted:
                chain.append((l, int(rest.split()[0][1:])))
    events = find_events(directory, {e for _, e in chain})
    cons = find_constraints(directory, {ev['c'] for ev in events.values()})
    edges = find_edges(directory, {c['ref'] for c in cons.values() if isinstance(c.get('ref'), str)})

    print('# chain of %s = %s for %s   (%s, %d of its lines)' % (inv, pins[inv], node, rec['chain'], len(chain)))
    for l, e in chain:
        print(l)
        ev = events.get(e)
        con = cons.get(ev['c']) if ev else None
        if con is None:
            print(PAD + '| constraint of event %d not found' % e)
            continue
        for x in ref_lines(con, edges):
            print(PAD + '| ' + x)
    print(pin_line)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
