"""Export (section 9).  File formats are documented in export/FORMAT.md."""
from __future__ import annotations

import csv
import json
import os
import shutil

from . import names, passes, pd as P
from .config import DATA, EXPORT
from .solver import INVARIANTS, INV_DOM, PIN_COORDS, RULE_FAMILY

MAX_TEXT = 100


def dom_text(d):
    """Statement text of a domain (FORMAT.md, 'statements')."""
    t = d.text()
    if len(t) <= MAX_TEXT:
        return t
    return t[:MAX_TEXT] + '... [digest %s]' % d.digest()


def _dumps(o):
    return json.dumps(o, separators=(',', ':'), sort_keys=True)


def chain_events(events, pin_ids):
    """Ancestor closure of the given event ids (sorted)."""
    seen = set()
    stack = list(pin_ids)
    while stack:
        i = stack.pop()
        if i in seen:
            continue
        seen.add(i)
        stack.extend(events[i]['in'])
    return sorted(seen)


def chain_text(node, pins, pin_event, events, ev_text, cons_by_id):
    """Text of chains/<node>.txt: the union of the chains of all pinned values, numbered, then
    one line per pinned value listing its chain as numbers."""
    per = {}
    for inv in INVARIANTS:
        if inv in pins:
            per[inv] = chain_events(events, [pin_event[inv]])
    union = sorted(set(i for ids in per.values() for i in ids))
    num = {i: k + 1 for k, i in enumerate(union)}
    lines = ['# chains for %s' % node]
    for i in union:
        e = events[i]
        c = cons_by_id[e['c']]
        lines.append('%d. e%d %s nodes=%s par=%s -> %s.%s: %s | in: %s' % (
            num[i], e['id'], e['rule'], ','.join(c['nodes']), _dumps(c.get('par') or {}),
            e['node'], e['dom'], ev_text[i], ','.join(str(num[j]) for j in e['in']) or '-'))
    for inv in INVARIANTS:
        if inv in per:
            lines.append('== %s = %d : pinned at %d ; chain %s' % (
                inv, pins[inv], num[pin_event[inv]], ','.join(str(num[i]) for i in per[inv])))
    return '\n'.join(lines) + '\n'


class Writer:
    """JSONL writer that splits into numbered parts below a size limit."""

    def __init__(self, path, limit=45 * 2 ** 20):
        self.base, self.limit, self.part, self.size = path, limit, 0, 0
        for fn in os.listdir(os.path.dirname(path)):
            stem = os.path.basename(path)
            if fn == stem or (fn.startswith(stem[:-6] + '.') and fn.endswith('.jsonl')):
                os.remove(os.path.join(os.path.dirname(path), fn))
        self.f = open(path, 'w')

    def write(self, obj):
        line = _dumps(obj) + '\n'
        if self.size + len(line) > self.limit:
            self.f.close()
            self.part += 1
            self.f = open(self.base[:-6] + '.%d.jsonl' % self.part, 'w')
            self.size = 0
        self.f.write(line)
        self.size += len(line)

    def close(self):
        self.f.close()


def expand_edge(e, diag_cache):
    """Full edge record with both PD codes (section 5)."""
    mv = e['move']
    shard = mv['shard']
    if shard not in diag_cache:
        if len(diag_cache) > 50:
            diag_cache.clear()
        diag_cache[shard] = {d['id']: d for d in passes.load_diagrams(shard)}
    d = diag_cache[shard][mv['d']]
    rec = e['rec']
    out = {'id': e['id'], 'type': {'cc': 'crossing change', 'tw': 'twist', 'mu': 'mutation'}[e['t']],
           'key': e['key'], 'count': e['count'], 'pass': mv['pass'],
           'source_node': d['node'], 'source_diagram': d['id'], 'pd': d['pd'],
           'source_certificate': d['cert'], 'writhe_before': rec.get('w0'), 'writhe_after': rec.get('w1'),
           'result_certificate': rec.get('cert')}
    for k in ('seed', 'moves', 'word', 'strands'):
        if k in d:
            out['diagram_' + k] = d[k]
    r = {'t': e['t']}
    r.update({k: mv[k] for k in ('i', 'e', 'h', 'axis') if k in mv})
    new = passes.result_pd(d['pd'], r)
    out['result_pd'] = new
    out['result_node'] = e['dst'] if e['t'] != 'cc' else None
    if e['t'] == 'cc':
        out['crossing'] = mv['i']
        out['sign'] = rec['s']
        out['K_plus'], out['K_minus'] = e['key'][0], e['key'][1]
        out['result_node'] = e['key'][1] if rec['s'] == 1 else e['key'][0]
    elif e['t'] == 'tw':
        out['circle_edges'] = mv['e']
        out['edge_directions'] = rec.get('dirs')
        out['a'], out['b'] = rec['a'], rec['b']
        out['handedness'] = mv['h']
        out['insertion'] = 'full-twist braid on the crossed edges, in path order, replacing their arcs'
    else:
        out['circle_edges'] = mv['e']
        out['rotation'] = mv['axis']
    return out


def export_all(problem, solver, out_dir=EXPORT, ablation=None, extra=None, write_chains=True):
    os.makedirs(out_dir, exist_ok=True)
    cons_by_id = {c['id']: c for c in solver.cons}
    events = solver.events
    ev_text = [dom_text(d) for d in solver.ev_dom]
    # --- events
    w = Writer(os.path.join(out_dir, 'events.jsonl'))
    for e in events:
        w.write(e)
    w.close()
    # --- constraints
    w = Writer(os.path.join(out_dir, 'constraints.jsonl'))
    for c in solver.cons:
        c2 = dict(c)
        c2['fam'] = RULE_FAMILY.get(c['rule'], '?')
        w.write(c2)
    w.close()
    # --- edges
    w = Writer(os.path.join(out_dir, 'edges.jsonl'))
    cache = {}
    for e in problem.edges:
        w.write(expand_edge(e, cache))
    w.close()
    # --- certificates
    cdir = os.path.join(out_dir, 'certificates')
    os.makedirs(cdir, exist_ok=True)
    with open(os.path.join(cdir, 'coincidences.jsonl'), 'w') as f:
        for co in problem.coincidences:
            f.write(_dumps(co) + '\n')
    with open(os.path.join(cdir, 'lens_fillings.jsonl'), 'w') as f:
        for node, p, q, ref in problem.lens:
            f.write(_dumps({'node': node, 'p': p, 'q': q, 'certificate': ref}) + '\n')
    with open(os.path.join(cdir, 'constructions.jsonl'), 'w') as f:
        for r in problem.constructions:
            f.write(_dumps({k: r[k] for k in ('family', 'construction', 'params', 'pd', 'chirality', 'node',
                                               'cert', 'kind') if k in r}) + '\n')
    with open(os.path.join(cdir, 'certified_L.jsonl'), 'w') as f:
        for n in sorted(problem.certL):
            f.write(_dumps({'node': n, 'certificate': problem.certL[n]}) + '\n')
    # --- knots and chains
    chdir = os.path.join(out_dir, 'chains')
    if write_chains:
        if os.path.isdir(chdir):
            shutil.rmtree(chdir)
        os.makedirs(chdir)
    rows = []
    with open(os.path.join(out_dir, 'knots.jsonl'), 'w') as f:
        for n in sorted(problem.nodes, key=lambda x: (problem.nodes[x]['tier'] if problem.nodes[x]['tier'] is not None else 99, x)):
            info = problem.nodes[n]
            pins = solver.pins(n)
            pe = {inv: solver.pin_event[(n, inv)] for inv in pins}
            rec = {
                'node': n, 'aliases': info['aliases'], 'kind': info['kind'], 'mirror': info['mirror'],
                'mirror_flag': n.endswith('*'), 'amphichiral': info['amphichiral'],
                'peripheral': bool(info.get('peripheral')),
                'tier': info['tier'], 'crossing_number': info['crossing_number'], 'cert': info['cert'],
                'knotinfo': info['ki'], 'calculator': info['calc'],
                'used': {'g': info['g'], 'g4_upper': info['g4hi'], 'fibered': info['fibered'], 'tau': info['tau'],
                         'slice': info['slice'], 'nontrivial': info['nontrivial'], 'certified_L': info['certL'],
                         'certified_not_L': info['notL'], 'slopes': info.get('slopes', 'G')},
                'domains': {k: solver.get(n, k).to_json() for k in ('F', 'C', 'U')},
                'pins': pins, 'pin_events': pe,
                'last_events': {k: solver.last[(n, k)] for k in ('F', 'C', 'U') if (n, k) in solver.last},
                'upsilon_unverified': info.get('upsilon_unverified'),
                'chain': ('chains/%s.txt' % names.file_name(n)) if pins else None,
            }
            f.write(_dumps(rec) + '\n')
            rows.append(table_row(rec, solver, n))
            if pins and write_chains:
                with open(os.path.join(chdir, names.file_name(n) + '.txt'), 'w') as g:
                    g.write(chain_text(n, pins, pe, events, ev_text, cons_by_id))
    # --- parameters
    import importlib.metadata as md
    versions = {}
    for pkg in ('snappy', 'spherogram', 'snappy_manifolds', 'snappy_15_knots', 'regina', 'database_knotinfo',
                'knot_floer_homology', 'passagemath-standard', 'networkx', 'openpyxl'):
        try:
            versions[pkg] = md.version(pkg)
        except Exception:
            versions[pkg] = None
    par = {'scope': problem.params, 'slope_sets': {k: [list(x) for x in v] for k, v in problem.slopes.items()},
           'versions': versions, 'stats': dict(problem.stats), 'log': problem.log,
           'max_statement_text': MAX_TEXT}
    if extra:
        par.update(extra)
    with open(os.path.join(out_dir, 'parameters.json'), 'w') as f:
        json.dump(par, f, indent=1, sort_keys=True)
    write_tables(rows, out_dir, problem, ablation)
    return rows


# ----------------------------------------------------------------------
# tabular export
# ----------------------------------------------------------------------
COLUMNS = ['node', 'aliases', 'kind', 'mirror_flag', 'crossing_number', 'certificate_type',
           'ki_g4_lower', 'ki_g4_upper', 'ki_signature', 'ki_tau', 'ki_genus', 'ki_fibered', 'ki_alternating',
           'ki_symmetry_type',
           'calc_tau', 'calc_nu', 'calc_epsilon', 'calc_genus', 'calc_fibered', 'calc_lspace']
for _inv in INVARIANTS:
    COLUMNS += ['%s_pin' % _inv, '%s_lo' % _inv, '%s_hi' % _inv]
    if _inv == 'r_2':
        COLUMNS.append('M_r2_joint')
    if _inv == 'tau':
        COLUMNS.append('tau_nu_r0_joint')
COLUMNS += ['upsilon_unverified', 'chain_file']


def _b(x):
    return '' if x is None else ('Y' if x is True else 'N' if x is False else x)


def table_row(rec, solver, n):
    ki, ca = rec['knotinfo'] or {}, rec['calculator'] or {}
    row = {'node': n, 'aliases': ';'.join(rec['aliases']), 'kind': rec['kind'] + ('/peripheral' if rec['peripheral'] else ''),
           'mirror_flag': _b(rec['mirror_flag']),
           'crossing_number': _b(rec['crossing_number']), 'certificate_type': rec['cert'],
           'ki_g4_lower': _b(ki['g4'][0]) if ki.get('g4') else '', 'ki_g4_upper': _b(ki['g4'][1]) if ki.get('g4') else '',
           'ki_signature': _b(ki.get('signature')), 'ki_tau': _b(ki.get('tau')), 'ki_genus': _b(ki.get('genus')),
           'ki_fibered': _b(ki.get('fibered')), 'ki_alternating': _b(ki.get('alternating')),
           'ki_symmetry_type': ki.get('symmetry_type') or '',
           'calc_tau': _b(ca.get('tau')), 'calc_nu': _b(ca.get('nu')), 'calc_epsilon': _b(ca.get('epsilon')),
           'calc_genus': _b(ca.get('genus')), 'calc_fibered': _b(ca.get('fibered')), 'calc_lspace': _b(ca.get('lspace'))}
    for inv in INVARIANTS:
        d = solver.get(n, INV_DOM[inv])
        co = dict(PIN_COORDS[INV_DOM[inv]])[inv]
        lo, hi = d.bounds(co)
        row['%s_pin' % inv] = _b(rec['pins'].get(inv))
        row['%s_lo' % inv] = _b(lo)
        row['%s_hi' % inv] = _b(hi)
    t = solver.get(n, 'F').tuples(20)
    row['M_r2_joint'] = '' if t is None else json.dumps([list(x) for x in t], separators=(',', ':'))
    t = solver.get(n, 'C').tuples(20)
    row['tau_nu_r0_joint'] = '' if t is None else json.dumps([list(x) for x in t], separators=(',', ':'))
    uu = rec.get('upsilon_unverified')
    row['upsilon_unverified'] = '' if uu is None else '%d (unverified)' % uu
    row['chain_file'] = rec['chain'] or ''
    return row


def pins_by_tier(problem, rows):
    out = {}
    for r in rows:
        info = problem.nodes[r['node']]
        t = info['tier'] if info['kind'] in ('table', 'composite', 'unknot') else 'constructions'
        if info.get('peripheral'):
            t = 'peripheral'
        d = out.setdefault(t, {inv: 0 for inv in INVARIANTS})
        d['nodes'] = d.get('nodes', 0) + 1
        for inv in INVARIANTS:
            if r['%s_pin' % inv] != '':
                d[inv] += 1
    return out


def write_tables(rows, out_dir, problem, ablation=None):
    with open(os.path.join(out_dir, 'knots.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    from openpyxl import Workbook
    wb = Workbook(write_only=True)
    ws = wb.create_sheet('knots')
    ws.append(COLUMNS)
    for r in rows:
        ws.append([r[c] for c in COLUMNS])
    ws = wb.create_sheet('pins')
    ws.append(['tier', 'nodes'] + INVARIANTS)
    pt = pins_by_tier(problem, rows)
    tot = {inv: 0 for inv in INVARIANTS}
    totn = 0
    for t in sorted(pt, key=lambda x: (isinstance(x, str), x)):
        ws.append([t, pt[t]['nodes']] + [pt[t][inv] for inv in INVARIANTS])
        totn += pt[t]['nodes']
        for inv in INVARIANTS:
            tot[inv] += pt[t][inv]
    ws.append(['total', totn] + [tot[inv] for inv in INVARIANTS])
    ws = wb.create_sheet('ablation')
    ws.append(['withheld', 'rules'] + ['pins_%s' % i for i in INVARIANTS] + ['lost_%s' % i for i in INVARIANTS] +
              ['lost pins whose full-run chain lacks the withheld family'])
    for a in ablation or []:
        ws.append([a['withheld'], ' '.join(a['rules'])] + [a['pins'][i] for i in INVARIANTS] +
                  [a['lost'][i] for i in INVARIANTS] + [a['violations']])
    ws = wb.create_sheet('parameters')
    ws.append(['parameter', 'value'])
    for k, v in sorted(problem.params.items()):
        ws.append([k, json.dumps(v)])
    for k, v in sorted(problem.stats.items()):
        ws.append(['stat: ' + k, v])
    wb.save(os.path.join(out_dir, 'knots.xlsx'))
    with open(os.path.join(out_dir, 'pins_by_tier.json'), 'w') as f:
        json.dump({str(k): v for k, v in pt.items()}, f, indent=1, sort_keys=True)
