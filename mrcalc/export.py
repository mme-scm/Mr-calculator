"""Export (section 9).  File formats are documented in export/FORMAT.md."""
from __future__ import annotations

import csv
import gzip
import io
import json
import lzma
import os
import shutil
import tarfile

from . import names, passes, pd as P
from .config import DATA, EXPORT
from .solver import INVARIANTS, INV_DOM, PIN_COORDS, RULE_FAMILY, con_dict

MAX_TEXT = 100
PART_LIMIT = 40 * 2 ** 20          # size limit of one file of the export (bytes on disk)
XLSX_ROWS = 200000                # rows of peripheral nodes per workbook


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


class _ConIndex:
    """cons_by_id for constraints whose id is their position ('c<i>' at index i)."""

    def __init__(self, cons):
        self.cons = cons

    def __getitem__(self, cid):
        return self.cons[int(cid[1:])]


def con_index(cons):
    if all(c['id'] == 'c%d' % i for i, c in enumerate(cons)):
        return _ConIndex(cons)
    return {c['id']: c for c in cons}


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


def _gz(raw):
    """Deterministic gzip stream (no name, no time stamp)."""
    return gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6)


def _is_part(fn, stem, exts):
    """fn is <stem><ext> or <stem>.<k><ext> for one of the extensions."""
    for ext in exts:
        if fn == stem + ext:
            return True
        if fn.startswith(stem + '.') and fn.endswith(ext) and fn[len(stem) + 1:-len(ext)].isdigit():
            return True
    return False


class Writer:
    """JSONL writer that splits into numbered parts below a size limit (gzip parts by default)."""

    def __init__(self, path, limit=PART_LIMIT, compress=True):
        self.stem, self.limit, self.compress = path[:-len('.jsonl')], limit, compress
        self.part, self.size, self.n = 0, 0, 0
        d, stem = os.path.dirname(path), os.path.basename(self.stem)
        for fn in os.listdir(d):
            if _is_part(fn, stem, ('.jsonl', '.jsonl.gz')):
                os.remove(os.path.join(d, fn))
        self._open()

    def _open(self):
        name = self.stem + ('.%d' % self.part if self.part else '') + '.jsonl' + ('.gz' if self.compress else '')
        self.raw = open(name, 'wb')
        self.f = _gz(self.raw) if self.compress else self.raw
        self.size = 0

    def _close(self):
        if self.compress:
            self.f.close()
        self.raw.close()

    def write(self, obj):
        line = (_dumps(obj) + '\n').encode('utf-8')
        self.n += 1
        if self.compress:
            full = self.n % 500 == 0 and self.raw.tell() > self.limit
        else:
            full = self.size + len(line) > self.limit
        if full:
            self._close()
            self.part += 1
            self._open()
        self.f.write(line)
        self.size += len(line)

    def close(self):
        self._close()


class ChainPack:
    """Chain files as members <file>.txt of the archives chains/chains-NNN.tar.xz (each below the size limit).
    xz because chains share most of their lines: about a third of the size of gzip archives."""

    def __init__(self, directory, limit=PART_LIMIT):
        self.dir, self.limit, self.part, self.tar = directory, limit, 0, None

    def add(self, name, text):
        if self.tar is None:
            self.raw = open(os.path.join(self.dir, 'chains-%03d.tar.xz' % self.part), 'wb')
            self.gz = lzma.LZMAFile(self.raw, 'wb', preset=3)
            self.tar = tarfile.open(fileobj=self.gz, mode='w', format=tarfile.GNU_FORMAT)
        data = text.encode('utf-8')
        ti = tarfile.TarInfo(name)
        ti.size, ti.mtime, ti.mode = len(data), 0, 0o644
        self.tar.addfile(ti, io.BytesIO(data))
        if self.raw.tell() > self.limit:
            self.close()
            self.part += 1

    def close(self):
        if self.tar is not None:
            self.tar.close()
            self.gz.close()
            self.raw.close()
            self.tar = None


def expand_edge(e, r, diag_cache):
    """Full edge record with both PD codes (section 5).  e: prepare.Edge; r: its representative pass record."""
    shard = r['shard']
    if shard not in diag_cache:
        if len(diag_cache) > 50:
            diag_cache.clear()
        diag_cache[shard] = {d['id']: d for d in passes.load_diagrams(shard)}
    d = diag_cache[shard][r['d']]
    out = {'id': e.id, 'type': {'cc': 'crossing change', 'tw': 'twist', 'mu': 'mutation'}[e.t],
           'key': list(e.key), 'count': e.count, 'pass': r['pass'],
           'source_node': d['node'], 'source_diagram': d['id'], 'pd': d['pd'],
           'source_certificate': d['cert'], 'writhe_before': r.get('w0'), 'writhe_after': r.get('w1'),
           'result_certificate': r.get('cert')}
    for k in ('seed', 'moves', 'word', 'strands'):
        if k in d:
            out['diagram_' + k] = d[k]
    mv = {'t': e.t}
    mv.update({k: r[k] for k in ('i', 'e', 'h', 'axis') if k in r})
    new = passes.result_pd(d['pd'], mv)
    out['result_pd'] = new
    out['result_node'] = e.dst if e.t != 'cc' else None
    if e.t == 'cc':
        out['crossing'] = r['i']
        out['sign'] = r['s']
        out['K_plus'], out['K_minus'] = e.key[0], e.key[1]
        out['result_node'] = e.key[1] if r['s'] == 1 else e.key[0]
    elif e.t == 'tw':
        out['circle_edges'] = r['e']
        out['edge_directions'] = r.get('dirs')
        out['a'], out['b'] = r['a'], r['b']
        out['handedness'] = r['h']
        out['insertion'] = 'full-twist braid on the crossed edges, in path order, replacing their arcs'
    else:
        out['circle_edges'] = r['e']
        out['rotation'] = r['axis']
    return out


def export_all(problem, solver, out_dir=EXPORT, ablation=None, extra=None, write_chains=True, pack=True):
    """pack: gzip parts for the JSONL files and tar archives for the chain files (FORMAT.md, section 1)."""
    os.makedirs(out_dir, exist_ok=True)
    cons_by_id = con_index(solver.cons)
    events = solver.events
    if write_chains:      # statement text per event: kept by the solver (keep = dom_text), or from the domains
        ev_text = solver.ev_text if len(solver.ev_text) == len(events) else [dom_text(d) for d in solver.ev_dom]
    # --- events
    w = Writer(os.path.join(out_dir, 'events.jsonl'), compress=pack)
    for e in events:
        w.write(e.to_dict())
    w.close()
    # --- constraints
    w = Writer(os.path.join(out_dir, 'constraints.jsonl'), compress=pack)
    for c in solver.cons:
        c2 = con_dict(c)
        c2['fam'] = RULE_FAMILY.get(c['rule'], '?')
        w.write(c2)
    w.close()
    # --- edges
    w = Writer(os.path.join(out_dir, 'edges.jsonl'), compress=pack)
    cache = {}
    for e, r in problem.edge_records(problem.edges):      # in reading order of the pass records, not by id
        w.write(expand_edge(e, r, cache))
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
    chpack = ChainPack(chdir) if (write_chains and pack) else None
    rows = []
    f = Writer(os.path.join(out_dir, 'knots.jsonl'), compress=pack)
    if True:
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
            f.write(rec)
            rows.append(table_row(rec, solver, n))
            if pins and write_chains:
                text = chain_text(n, pins, pe, events, ev_text, cons_by_id)
                if chpack:
                    chpack.add(names.file_name(n) + '.txt', text)
                else:
                    with open(os.path.join(chdir, names.file_name(n) + '.txt'), 'w') as g:
                        g.write(text)
    f.close()
    if chpack:
        chpack.close()
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
           'max_statement_text': MAX_TEXT, 'packed': bool(pack)}
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


def _row_size(r):
    return sum(len(str(v)) for v in r.values()) + len(r) + 1


def write_csv(rows, out_dir, limit=PART_LIMIT):
    """knots.csv, continued in knots.1.csv, knots.2.csv, ... (each with the header line) below the size limit."""
    for fn in os.listdir(out_dir):
        if _is_part(fn, 'knots', ('.csv',)):
            os.remove(os.path.join(out_dir, fn))
    part, f, size = 0, None, 0
    for r in rows:
        n = _row_size(r)
        if f is None or size + n > limit:
            if f:
                f.close()
                part += 1
            f = open(os.path.join(out_dir, 'knots%s.csv' % ('.%d' % part if part else '')), 'w', newline='',
                     encoding='utf-8')
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            size = 0
        w.writerow(r)
        size += n
    if f:
        f.close()


def write_tables(rows, out_dir, problem, ablation=None):
    """knots.csv (all nodes); knots.xlsx (sheets knots, pins, ablation, parameters; the sheet knots has the
    nodes that are not peripheral); knots_peripheral[.k].xlsx (peripheral nodes, XLSX_ROWS per workbook)."""
    write_csv(rows, out_dir)
    from openpyxl import Workbook
    for fn in os.listdir(out_dir):
        if _is_part(fn, 'knots_peripheral', ('.xlsx',)):
            os.remove(os.path.join(out_dir, fn))
    core = [r for r in rows if not r['kind'].endswith('/peripheral')]
    peri = [r for r in rows if r['kind'].endswith('/peripheral')]
    for k in range(0, len(peri), XLSX_ROWS):
        wb = Workbook(write_only=True)
        ws = wb.create_sheet('knots')
        ws.append(COLUMNS)
        for r in peri[k:k + XLSX_ROWS]:
            ws.append([r[c] for c in COLUMNS])
        wb.save(os.path.join(out_dir, 'knots_peripheral%s.xlsx' % ('.%d' % (k // XLSX_ROWS) if k else '')))
    wb = Workbook(write_only=True)
    ws = wb.create_sheet('knots')
    ws.append(COLUMNS)
    for r in core:
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
