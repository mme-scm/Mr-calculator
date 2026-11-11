"""Assemble nodes and rule instances (constraints) from the data files.

Sources: KnotInfo table and its checks, family constructions, calculator inputs of
non-table nodes, pass records (moves), fillings and coincidences, upsilon data.
Nothing here narrows a domain: it only instantiates rules of the catalogue with data.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from math import gcd

from . import knotinfo, names, nodeset, passes
from .config import DATA, iter_census_refs, iter_hfk_peripheral, load_params

E_LIST = {'9_42', '10_125', '10_130', '10_132', '10_136', '10_141'}
REFERENCE_KNOTS = ['3_1', '4_1', '5_1', '5_2', '8_19']


def _jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def mirror_ranks(ranks):
    return sorted([-a, -m, v] for a, m, v in ranks)


class Problem:
    def __init__(self, max_tier=99, include_upsilon=False, verbose=False):
        self.params = load_params()
        self.max_tier = max_tier
        self.include_upsilon = include_upsilon
        self.nodes = {}            # name -> info dict
        self.alias = {}            # construction name -> node name
        self.cons = []
        self.edges = []            # deduplicated edge records (representative move)
        self.stats = defaultdict(int)
        self.log = []
        self._cid = 0
        self._load_table()
        self._load_constructions()
        self._core_nodes()
        self._load_passes()
        self._load_fillings()
        self._predicates()
        self._unary()
        self._families()
        self._structure()
        self._edges_to_constraints()
        self._surgery_constraints()
        if include_upsilon:
            self._upsilon()

    # ------------------------------------------------------------------
    def con(self, rule, dom, nodes, par=None, ref=None):
        c = {'id': 'c%d' % self._cid, 'rule': rule, 'dom': dom, 'nodes': list(nodes)}
        if par:
            c['par'] = par
        if ref is not None:
            c['ref'] = ref
        self._cid += 1
        self.cons.append(c)
        return c

    def canon(self, name):
        """Canonical node name of a (possibly constructed) name."""
        if name in self.alias:
            return self.alias[name]
        m = names.mirror_name(name) if names.kind(name) != 'construction' else None
        if m is not None and m in self.alias:
            return names.mirror_name(self.alias[m])
        return name

    def mirror(self, name):
        if name in self.nodes and self.nodes[name].get('mirror'):
            return self.nodes[name]['mirror']
        k = names.kind(name)
        if k == 'construction':
            return name[:-1] if name.endswith('*') else name + '*'
        return self.canon(names.mirror_name(name))

    # ------------------------------------------------------------------
    def _load_table(self):
        self.table = knotinfo.by_name()
        self.checks = {r['name']: r for r in _jsonl(os.path.join(DATA, 'table_checks.jsonl'))}
        for nm in REFERENCE_KNOTS:
            ch = self.checks[nm]
            if not ch['tau_ok'] or not all(b['ok'] for b in ch['braids']):
                raise RuntimeError('reference knot %s fails the section 2.5 checks: run blocked' % nm)
        t = self.table
        if not (t['3_1']['signature'] == -2 and t['3_1']['tau'] == 1 and t['5_1']['tau'] == 2
                and t['5_2']['tau'] == 1):
            raise RuntimeError('chirality reference values of section 3 do not hold')
        self.ref_ranks = {}
        for nm in ('3_1', '4_1', '5_1', '5_2'):
            self.ref_ranks[nm] = self.checks[nm]['hfk']['ranks']
            self.ref_ranks[nm + '*'] = mirror_ranks(self.checks[nm]['hfk']['ranks'])
        self.ref_ranks['0_1'] = [[0, 0, 1]]

    def _table_info(self, name):
        base = name.rstrip('*')
        mir = name.endswith('*')
        r = self.table[base]
        ch = self.checks[base]
        sgn = -1 if mir else 1
        h = ch['hfk']
        tab_ok = ch['tau_ok'] and all(b['ok'] for b in ch['braids'])
        if not tab_ok:
            self.log.append('table check failed for %s: tabulated tau/sigma/quasipositive unknown' % base)
        tau = sgn * (r['tau'] if tab_ok else h['tau'])
        info = {
            'kind': 'table', 'tier': r['crossing_number'], 'crossing_number': r['crossing_number'],
            'cert': 'reference' if not mir else 'mirror of reference',
            'aliases': [], 'mirror': base if r['amphichiral'] else (base if mir else base + '*'),
            'amphichiral': r['amphichiral'],
            'ki': {'g4': r['g4'], 'signature': None if (r['signature'] is None or not tab_ok) else sgn * r['signature'],
                   'tau': None if not tab_ok else sgn * r['tau'], 'genus': r['genus'], 'fibered': r['fibered'],
                   'alternating': r['alternating'], 'symmetry_type': r['symmetry_type'],
                   'u': r['u'], 'c4': r['c4'],
                   'quasipositive': (r['quasipositive'] if (not mir and tab_ok) else None)},
            'calc': {'tau': sgn * h['tau'], 'nu': None if mir else h['nu'], 'epsilon': sgn * h['epsilon'],
                     'genus': h['genus'], 'fibered': h['fibered'], 'lspace': h['lspace'] if not mir else None},
            'g': r['genus'], 'g4hi': r['g4'][1] if r['g4'] else None, 'fibered': r['fibered'], 'tau': tau,
            'slice': r['slice'], 'ranks': mirror_ranks(h['ranks']) if mir else h['ranks'],
            'identified': True,
        }
        return info

    def _load_constructions(self):
        self.constructions = [r for r in _jsonl(os.path.join(DATA, 'constructions.jsonl')) if 'error' not in r]
        self.hfk_nodes = {r['node']: r for r in _jsonl(os.path.join(DATA, 'hfk_nodes.jsonl'))}
        for r in iter_census_refs(staged=False):
            if r.get('sig') and r['sig'] == r.get('sig_mirror'):
                names.register_amphichiral(r['name'])
        for r in self.constructions:
            cname = r['construction'] + ('*' if r.get('chirality') == 'mirror' else '')
            if r['node'] != cname:
                self.alias[cname] = r['node']
            if (r.get('cert') or {}).get('amphichiral'):
                names.register_amphichiral(r['node'])
            if names.kind(r['node']) != 'table' and 'tau' in r.get('hfk', {}):
                self.hfk_nodes.setdefault(r['node'], dict(r['hfk'], node=r['node']))
        for r in _jsonl(os.path.join(DATA, 'cables.jsonl')):
            if r.get('ident') and r['ident'] != r['node']:
                self.alias[r['node']] = r['ident']
        for r in _jsonl(os.path.join(DATA, 'cables_hfk.jsonl')):
            if 'hfk' in r and 'tau' in r['hfk']:
                self.hfk_nodes.setdefault(r['node'], dict(r['hfk'], node=r['node'], crossings=r.get('crossings')))

    def _calc_info(self, name, kind, tier=None):
        """Node info for a non-table node from calculator data (possibly of its mirror)."""
        h = self.hfk_nodes.get(name)
        sgn = 1
        if h is None or 'tau' not in h:
            m = names.mirror_name(name) if kind != 'construction' else (name[:-1] if name.endswith('*') else name + '*')
            h2 = self.hfk_nodes.get(m)
            if h2 is not None and 'tau' in h2:
                h, sgn = h2, -1
            else:
                h = None
        info = {'kind': kind, 'tier': tier if tier is not None else 99, 'crossing_number': names.crossing_number(name),
                'cert': 'construction' if kind in ('composite', 'torus', 'cable', 'construction') else 'isometry',
                'aliases': [], 'ki': None, 'calc': None, 'g': None, 'g4hi': None, 'fibered': None, 'tau': None,
                'slice': False, 'ranks': None, 'identified': kind in ('census',)}
        if kind == 'construction':
            info['mirror'] = name[:-1] if name.endswith('*') else name + '*'
        else:
            info['mirror'] = names.mirror_name(name)
        info['amphichiral'] = info['mirror'] == name
        if h is not None:
            info['calc'] = {'tau': sgn * h['tau'], 'nu': h['nu'] if sgn == 1 else None,
                            'epsilon': sgn * h['epsilon'], 'genus': h['genus'], 'fibered': h['fibered'],
                            'lspace': h['lspace'] if sgn == 1 else None}
            info['g'] = h['genus']
            info['g4hi'] = h['genus']          # g replaces g_4 for non-table nodes
            info['fibered'] = h['fibered']
            info['tau'] = sgn * h['tau']
            info['ranks'] = h['ranks'] if sgn == 1 else mirror_ranks(h['ranks'])
        return info

    def add_node(self, name, kind=None, tier=None):
        if name in self.nodes:
            return self.nodes[name]
        k = kind or names.kind(name)
        if k == 'unknot':
            info = {'kind': 'unknot', 'tier': 0, 'crossing_number': 0, 'cert': 'reference', 'aliases': [],
                    'mirror': '0_1', 'amphichiral': True, 'ki': None, 'calc': None, 'g': 0, 'g4hi': 0,
                    'fibered': None, 'tau': 0, 'slice': True, 'ranks': [[0, 0, 1]], 'identified': True}
        elif k == 'table':
            info = self._table_info(name)
        else:
            info = self._calc_info(name, k, tier if tier is not None else names.crossing_number(name))
        self.nodes[name] = info
        return info

    def _core_nodes(self):
        self.add_node('0_1')
        for base, r in self.table.items():
            self.add_node(base)
            if not r['amphichiral']:
                self.add_node(base + '*')
        for n in nodeset.composite_names():
            self.add_node(n, 'composite')
        for p, q in nodeset.torus_params(self.params['torus_pq_max']):
            for n in (names.torus_name(p, q), names.torus_name(p, q, True)):
                c = self.canon(n)
                if c == n:
                    self.add_node(n, 'torus')
                else:
                    self.nodes[c]['aliases'].append(n)
        self.cable_nodes = []
        for r in _jsonl(os.path.join(DATA, 'cables.jsonl')):
            n = r['node']
            c = self.canon(n)
            if c == n:
                self.add_node(n, 'cable')
            else:
                if c not in self.nodes:
                    self.add_node(c)
                self.nodes[c]['aliases'].append(n)
            self.cable_nodes.append(n)
        for r in self.constructions:
            cname = r['construction'] + ('*' if r.get('chirality') == 'mirror' else '')
            n = r['node']
            if n not in self.nodes:
                self.add_node(n)
                self.nodes[n]['peripheral'] = True
                m = self.mirror(n)
                if m not in self.nodes:
                    self.add_node(m)
                    self.nodes[m]['peripheral'] = True
            if cname != n and cname not in self.nodes[n]['aliases']:
                self.nodes[n]['aliases'].append(cname)

    # ------------------------------------------------------------------
    def _load_passes(self):
        """Deduplicate pass records into edges; collect homogeneous-diagram and braid evidence."""
        self.homog = {}        # node -> reference (diagram id or move)
        self.braids = defaultdict(dict)   # node -> {(n, w): ref}
        cc, tw, mu = {}, {}, {}
        per = defaultdict(set)
        self.per_move = {}
        nrec = 0
        for d in passes.iter_diagrams():
            node = self.canon(d['node'])
            if d.get('homogeneous') and node not in self.homog:
                self.homog[node] = {'diagram': d['id']}
            if 'word' in d:
                w = sum(1 if g > 0 else -1 for g in d['word'])
                self.braids[node].setdefault((d['strands'], w), {'diagram': d['id']})
        skip = set(filter(None, os.environ.get('MRCALC_SKIP_PASSES', '').split(',')))
        for r in passes.iter_pass_records():
            if r['pass'] in skip:
                continue
            nrec += 1
            if r.get('dst') is None:
                self.stats['unidentified results'] += 1
                continue
            if r['cert'].get('amphichiral'):
                names.register_amphichiral(r['dst'])
            src, dst = self.canon(r['src']), self.canon(r['dst'])
            move = {k: r[k] for k in ('pass', 'shard', 't', 'd', 'i', 'e', 'h', 'axis') if k in r}
            if dst not in self.nodes and dst not in self.per_move:
                self.per_move[dst] = move
            if r.get('hg') and dst not in self.homog:
                self.homog[dst] = {'move': move}
            if 'word' in r:
                w = sum(1 if g > 0 else -1 for g in r['word'])
                self.braids[dst].setdefault((r['strands'], w), {'move': move})
            if r['t'] == 'cc':
                kp, km = (src, dst) if r['s'] == 1 else (dst, src)
                if kp == km:
                    self.stats['trivial edges'] += 1
                    continue
                key = (kp, km)
                tgt = cc
            elif r['t'] == 'tw':
                if src == dst:
                    self.stats['trivial edges'] += 1
                    continue
                key = (src, dst, max(r['a'], r['b']), min(r['a'], r['b']), r['h'])
                tgt = tw
            else:
                if src == dst:
                    self.stats['trivial edges'] += 1
                    continue
                key = tuple(sorted((src, dst)))
                tgt = mu
            if key in tgt:
                tgt[key]['count'] += 1
            else:
                tgt[key] = {'t': r['t'], 'key': key, 'src': src, 'dst': dst, 'move': move, 'count': 1,
                            'rec': {k: r[k] for k in ('s', 'a', 'b', 'h', 'w0', 'w1', 'cert', 'kind', 'dirs', 'i', 'e', 'axis')
                                    if k in r}}
            per[dst].add(src)
        self.stats['pass records'] = nrec
        self._raw_edges = {'cc': cc, 'tw': tw, 'mu': mu}
        # peripheral nodes: results that are not core nodes
        self.peripheral_adj = defaultdict(set)
        for dst, srcs in per.items():
            if dst not in self.nodes:
                base = min(dst, self._mirror_free(dst))
                self.peripheral_adj[base] |= srcs
        self.per_hfk = {r['node']: r for r in iter_hfk_peripheral(staged=False) if 'tau' in r}
        included = set()
        for base, srcs in self.peripheral_adj.items():
            m = self._mirror_free(base)
            keep = len(srcs) >= 2 or base in self.homog or m in self.homog
            if keep:
                included.add(base)
                included.add(m)
        self.stats['peripheral candidates'] = len(self.peripheral_adj)
        for n in sorted(included):
            if n in self.nodes:
                continue
            h = self.per_hfk.get(n)
            if h is not None:
                self.hfk_nodes.setdefault(n, h)
            self.add_node(n)
            self.nodes[n]['peripheral'] = True
        self.stats['peripheral included'] = sum(1 for n in self.nodes.values() if n.get('peripheral'))

    def _mirror_free(self, name):
        k = names.kind(name)
        if k == 'construction':
            return name[:-1] if name.endswith('*') else name + '*'
        return names.mirror_name(name)

    # ------------------------------------------------------------------
    def _load_fillings(self):
        from .surgery import moser, slope_set
        self.lens = []          # (node, p, q, ref)
        self.coincidences = _jsonl(os.path.join(DATA, 'coincidences.jsonl'))
        P = self.params
        self.slopes = {'G': slope_set(P['slope_p'], P['slope_q']),
                       'T': slope_set(P['slope_p'], P['slope_q'], P['torus_integer_p'])}
        for p, q in nodeset.torus_params(P['torus_pq_max']):
            node = self.canon(names.torus_name(p, q))
            if node not in self.nodes:
                continue
            for m, n in self.slopes['T']:
                kind, nm = moser(p, q, m, n)
                if kind == 'lens':
                    self.lens.append((node, m, n, {'S2': [p, q, m, n], 'name': nm, 'cert': 'S2'}))
        from . import fillings as FL
        for r in FL.iter_fillings():
            if r.get('kind') == 'lens' and r.get('name') not in (None, 'S3', 'S2xS1'):
                self.lens.append((self.canon(r['node']), r['p'], r['q'],
                                  {'filling': [r['node'], r['p'], r['q']], 'name': r['name'],
                                   'cert': r.get('how', 'regina')}))

    # ------------------------------------------------------------------
    def differs_from(self, name, others):
        """Certified K != X for every X in others (section 2 preamble)."""
        info = self.nodes[name]
        if info['kind'] in ('table', 'census', 'unknot'):
            return name not in others
        if info.get('ranks') is None:
            return False
        return all(info['ranks'] != self.ref_ranks[x] for x in others)

    def _predicates(self):
        self.certL = {}
        lens_pos = defaultdict(list)
        for node, p, q, ref in self.lens:
            if p > 0:
                lens_pos[node].append((p, q, ref))
            else:
                lens_pos[self.mirror(node)].append((-p, q, ref))
        self.lens_pos = lens_pos
        for n, info in self.nodes.items():
            info['nontrivial'] = self.differs_from(n, ['0_1'])
            g, fib = info['g'], info['fibered']
            notL = False
            if fib is False:
                notL = True
            elif g is not None and g <= 2 and self.differs_from(n, ['0_1', '3_1', '3_1*', '5_1', '5_1*']):
                notL = True
            info['notL'] = notL
        for n in lens_pos:
            if n in self.nodes and self.nodes[n]['nontrivial']:
                self.certL[n] = {'why': 'lens space surgery', 'slope': lens_pos[n][0][:2]}
        self.torus_node = {}
        for p, q in nodeset.torus_params(self.params['torus_pq_max']):
            n = self.canon(names.torus_name(p, q))
            self.torus_node[(p, q)] = n
            if n in self.nodes:
                self.certL.setdefault(n, {'why': 'positive torus knot', 'pq': [p, q]})
        changed = True
        while changed:
            changed = False
            for cn in self.cable_nodes:
                node = self.canon(cn)
                if node in self.certL or node not in self.nodes:
                    continue
                r, s, comp = names.parse_cable(cn)
                comp = self.canon(comp)
                ci = self.nodes.get(comp)
                if ci is None or comp not in self.certL or not ci['nontrivial'] or ci['g'] is None:
                    continue
                if r > s * (2 * ci['g'] - 1) and self.nodes[node]['nontrivial']:
                    self.certL[node] = {'why': 'cable of certified L', 'cable': cn}
                    changed = True
        for n, info in self.nodes.items():
            info['certL'] = n in self.certL
            if info['certL'] and info['notL']:
                raise RuntimeError('node %s certified both L and not L' % n)

    # ------------------------------------------------------------------
    def slope_id(self, name):
        info = self.nodes[name]
        return info.get('slopes', 'G')

    def _unary(self):
        P = self.params
        for n, info in self.nodes.items():
            if n == '0_1':
                self.con('0_1', 'F', [n])
                self.con('0_1', 'C', [n])
                self.con('U4a', 'U', [n], {'why': 'unknot'})
                continue
            ki = info['ki']
            # --- (M, r_2)
            self.con('F1', 'F', [n])
            if info['slice']:
                self.con('F5', 'F', [n], {'why': 'slice'})
            if info['amphichiral']:
                self.con('F5', 'F', [n], {'why': 'amphichiral'})
            if ki is not None and (ki['c4'] or ki['u']):
                self.con('F8', 'F', [n], {'c': ki['c4'][1] if ki['c4'] else None, 'u': ki['u'][1] if ki['u'] else None})
            self.con('F15', 'F', [n], {'fibered': info['fibered'], 'tau': info['tau'], 'g': info['g']})
            # --- (tau, nu, r_0)
            self.con('C1', 'C', [n])
            self.con('C4', 'C', [n])
            if info['g4hi'] is not None:
                self.con('C5', 'C', [n], {'g4': info['g4hi'], 'src': 'KnotInfo g4' if ki else 'calculator g'})
            if info['amphichiral']:
                self.con('C5', 'C', [n], {'why': 'amphichiral'})
            # C8
            why = None
            ref = None
            if info['tau'] is not None:
                if ki is not None and ki['alternating']:
                    why = 'alternating'
                elif ki is not None and ki['quasipositive']:
                    why = 'quasipositive'
                elif ki is not None and info['crossing_number'] <= 10 and n.rstrip('*') not in E_LIST:
                    why = 'prime, at most 10 crossings, not in E'
                elif n in self.homog:
                    why, ref = 'homogeneous diagram', self.homog[n]
            if why:
                self.con('C8', 'C', [n], {'tau': info['tau'], 'why': why}, ref)
            words = dict(self.braids.get(n, {}))
            if ki is not None and not n.endswith('*'):
                for j, b in enumerate(self.checks[n]['braids']):
                    if b.get('ok'):
                        words.setdefault((b['strands'], b['writhe']), {'knotinfo_braid': j})
            for (strands, w), ref in sorted(words.items()):
                self.con('C9', 'C', [n], {'n': strands, 'w': w}, ref)
            # C10
            if n in ('3_1', '3_1*'):
                self.con('C10', 'C', [n], {'named': 1})
            elif n == '4_1':
                self.con('C10', 'C', [n], {'named': 2})
            par = {}
            if self.differs_from(n, ['0_1', '3_1', '3_1*', '4_1']):
                par['ge3'] = True
            if self.differs_from(n, ['3_1', '3_1*', '4_1', '5_2', '5_2*']):
                par['a'] = True
            if self.differs_from(n, ['5_1', '5_1*']):
                par['b'] = True
            if par:
                self.con('C10', 'C', [n], par)
            if info['notL'] and self.differs_from(n, ['4_1', '5_2', '5_2*']) and \
                    (info['fibered'] is False or info['g'] == 1):
                self.con('C15', 'C', [n])
            if info['certL'] and info['g'] is not None:
                self.con('C11', 'C', [n], {'g': info['g']}, self.certL[n])
            # coupling
            x = {'x1': True, 'slopes': self.slope_id(n)}
            if info['nontrivial']:
                x['x2'] = True
                x['x4'] = True
                if info['g'] is not None:
                    x['x3_g'] = info['g']
            if info['notL']:
                x['x5'] = True
                x['x5m'] = True
            self.con('X', 'X', [n], x)
            # upsilon (cheap rules)
            if info['slice']:
                self.con('U4a', 'U', [n], {'why': 'slice'})
            if info['amphichiral']:
                self.con('U4a', 'U', [n], {'why': 'amphichiral'})
            if info['g4hi'] is not None:
                self.con('U4a', 'U', [n], {'g4': info['g4hi']})
            if ki is not None and ki['alternating'] and ki['tau'] is not None:
                self.con('U2a', 'U', [n], {'tau': ki['tau']})

    # ------------------------------------------------------------------
    def _families(self):
        for (p, q), n in sorted(self.torus_node.items()):
            if n not in self.nodes:
                continue
            ref = {'construction': names.torus_name(p, q)}
            self.con('F11', 'F', [n], {'p': p, 'q': q}, ref)
            if p == 2:
                self.con('F12', 'F', [n], {'n': (q - 1) // 2}, ref)
            self.con('U7', 'U', [n], {'p': p, 'q': q}, ref)
            self.nodes[n]['slopes'] = 'T'
            m = self.mirror(n)
            if m in self.nodes:
                self.nodes[m]['slopes'] = 'T'
        for r in self.constructions:
            n = r['node']
            if n not in self.nodes:
                continue
            fam, par = r['family'], r['params']
            cname = r['construction'] + ('*' if r.get('chirality') == 'mirror' else '')
            ref = {'construction': cname, 'cert': r.get('cert')}
            tau = r['hfk']['tau']
            if fam == 'twist':
                self.con('F13', 'F', [n], {'m': par['m'], 'tau': tau}, ref)
                self.con('C12', 'C', [n], {'m': par['m'], 'tau': tau}, ref)
            elif fam == 'pretzel_m2pq':
                self.con('F14', 'F', [n], {'p': par['p'], 'q': par['q']}, ref)
            elif fam == 'pretzel_n3m3':
                self.con('C13', 'C', [n], {'kind': 'n3m3', 'n': par['n']}, ref)
            elif fam == 'pretzel_odd32':
                self.con('C13', 'C', [n], {'kind': 'odd32', 'n': par['n']}, ref)
            elif fam == 'pretzel_odd':
                self.con('C14', 'C', [n], {'n': par['n'], 'norm': r['norm']}, ref)

    # ------------------------------------------------------------------
    def _structure(self):
        done = set()
        for n, info in self.nodes.items():
            m = info['mirror']
            if m == n or m not in self.nodes or (m, n) in done:
                continue
            done.add((n, m))
            self.con('F3', 'F', [n, m])
            self.con('C3', 'C', [n, m])
            self.con('U4b', 'U', [n, m], {'kind': 'mirror'})
        for n, info in self.nodes.items():
            if info['kind'] != 'composite':
                continue
            parts = n.split('#')
            splits = set()
            if len(parts) == 2:
                splits.add((parts[0], parts[1]))
            else:
                for i in range(len(parts)):
                    rest = parts[:i] + parts[i + 1:]
                    splits.add((names.composite_name(rest), parts[i]))
            for a, b in sorted(splits):
                a, b = self.canon(a), self.canon(b)
                if a not in self.nodes or b not in self.nodes:
                    continue
                if a == b:
                    ns, mult = [n, a], [2]
                else:
                    ns, mult = [n, a, b], [1, 1]
                self.con('F4', 'F', ns, {'mult': mult})
                self.con('C6', 'C', ns, {'mult': mult})
                self.con('U4b', 'U', ns, {'kind': 'sum', 'mult': mult})

    # ------------------------------------------------------------------
    def _edge(self, e):
        e = dict(e)
        e['id'] = 'e%d' % len(self.edges)
        e['key'] = list(e['key'])
        self.edges.append(e)
        return e['id']

    def _diff(self, rule, dom, A, B, par, ref):
        """x(B) - x(A) in the bounds of the rule; handle an end being the mirror of the other."""
        par = dict(par)
        if A == B:
            return
        if A not in self.nodes or B not in self.nodes:
            return
        if self.nodes[A]['mirror'] == B:
            par['coef'] = -2          # x(B) = -x(A)
            self.con(rule, dom, [A], par, ref)
        else:
            self.con(rule, dom, [A, B], par, ref)

    def _edges_to_constraints(self):
        for key in sorted(self._raw_edges['cc']):
            e = self._raw_edges['cc'][key]
            kp, km = key
            if kp not in self.nodes or km not in self.nodes:
                self.stats['edges to excluded peripheral nodes'] += 1
                continue
            eid = self._edge(e)
            self._diff('F7', 'F', km, kp, {}, eid)
            self._diff('C7', 'C', km, kp, {}, eid)
            self._diff('U5', 'U', kp, km, {}, eid)
        for key in sorted(self._raw_edges['tw']):
            e = self._raw_edges['tw'][key]
            src, dst, a, b, h = key
            if src not in self.nodes or dst not in self.nodes:
                self.stats['edges to excluded peripheral nodes'] += 1
                continue
            eid = self._edge(e)
            par = {'a': a, 'b': b, 'h': h}
            self._diff('F9', 'F', src, dst, par, eid)
            self._diff('U6', 'U', src, dst, par, eid)
        for key in sorted(self._raw_edges['mu']):
            e = self._raw_edges['mu'][key]
            a, b = key
            if a not in self.nodes or b not in self.nodes:
                continue
            eid = self._edge(e)
            self.con('F6', 'F', [a, b], None, eid)

    # ------------------------------------------------------------------
    def _surgery_constraints(self):
        seen = set()
        for node, p, q, ref in self.lens:
            if node not in self.nodes:
                continue
            if (node, p, q) not in seen:
                seen.add((node, p, q))
                self.con('F10', 'F', [node], {'p': p, 'q': q}, ref)
                self.con('F10', 'C', [node], {'p': p, 'q': q}, ref)
        f16 = set()
        for n, lst in self.lens_pos.items():
            if n not in self.nodes:
                continue
            for p, q, ref in lst:
                if (n, p, q) in f16:
                    continue
                f16.add((n, p, q))
                self.con('F16', 'F', [n], {'p': p, 'q': q, 'g': self.nodes[n]['g']}, ref)
        # cables: S3 and S4
        for cn in self.cable_nodes:
            node = self.canon(cn)
            r, s, comp = names.parse_cable(cn)
            comp = self.canon(comp)
            if node not in self.nodes or comp not in self.nodes:
                continue
            extra = []
            for sg in (1, -1):
                p = r * s + sg
                self._eq('S3', node, (p, 1), 1, comp, (p, s * s), 1, {'cable': cn})
                extra.append([p, 1])
            self._eq('S4', node, (r * s, 1), 1, comp, (r, s), s, {'cable': cn})
            extra.append([r * s, 1])
            sl = self.nodes[node].get('slopes', 'G')
            if isinstance(sl, str):
                sl = {'base': sl, 'extra': []}
            sl['extra'] = sorted({tuple(x) for x in sl['extra'] + extra})
            sl['extra'] = [list(x) for x in sl['extra']]
            self.nodes[node]['slopes'] = sl
        for c in self.cons:
            if c['rule'] == 'X':
                c['par']['slopes'] = self.nodes[c['nodes'][0]].get('slopes', 'G')
        for co in self.coincidences:
            A, B = self.canon(co['A']), self.canon(co['B'])
            if A not in self.nodes or B not in self.nodes:
                continue
            self._eq('S1', A, tuple(co['sA']), 1, B, tuple(co['sB']), 1,
                     {'coincidence': co.get('id'), 'cert': co.get('cert')})

    def _eq(self, rule, A, sA, a, B, sB, b, ref):
        par = {'sA': list(sA), 'sB': list(sB), 'a': a, 'b': b}
        for dom in ('F', 'C'):
            if A == B:
                if tuple(sA) == tuple(sB) and a == b:
                    continue
                self.con(rule, dom, [A], par, ref)
            else:
                self.con(rule, dom, [A, B], par, ref)

    # ------------------------------------------------------------------
    def _upsilon(self):
        for r in _jsonl(os.path.join(DATA, 'upsilon.jsonl')):
            n = self.canon(r['node'])
            if n not in self.nodes:
                continue
            if r.get('epsilon') == 0:
                self.con('U3', 'U', [n], None, {'calculator': r.get('source')})
            if r.get('exact') and r.get('upsilon') is not None:
                self.con('U1', 'U', [n], {'value': r['upsilon'], 'why': r.get('why')}, {'calculator': r.get('source')})
            if r.get('upsilon') is not None and not r.get('exact'):
                self.nodes[n]['upsilon_unverified'] = r['upsilon']
                m = self.nodes[n]['mirror']
                if m in self.nodes and m != n:
                    self.nodes[m]['upsilon_unverified'] = -r['upsilon']   # tagged, never used by a rule
