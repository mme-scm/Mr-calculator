"""Write STATE.md and REPORT.md from the export and the pass data.
usage: report.py [final]"""
import collections
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import passes, fillings as F  # noqa: E402
from mrcalc.config import DATA, EXPORT, ROOT  # noqa: E402

INV = ['M', 'r_2', 'nu', 'r_0', 'tau', 'upsilon']


def load(path, default=None):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def pass_progress():
    shards = passes.shard_nodes()
    out = []
    if os.path.isdir(passes.PASS_DIR):
        for pn in sorted(os.listdir(passes.PASS_DIR)):
            done = passes.done_shards(pn)
            tiers = collections.Counter(passes.shard_tier(s) for s in done)
            out.append((pn, len(done), dict(sorted(tiers.items()))))
    fd = F.done_shards()
    out.append(('fillings', len(fd), dict(sorted(collections.Counter(passes.shard_tier(s) for s in fd).items()))))
    return out, len(shards)


def check_set(knots):
    path = os.path.join(DATA, 'check_set.json')
    if not os.path.exists(path):
        return None
    cs = json.load(open(path))
    rows = []
    for c in cs:
        name = c['knot'] + ('*' if c.get('mirror') else '')
        k = knots.get(name) or knots.get(c['knot'] if c.get('mirror') else name)
        if k is None:
            rows.append((name, c, None, 'node not found'))
            continue
        res = []
        for inv, key in (('nu', 'nu_sharp'), ('r_0', 'r_0')):
            if inv in k['pins']:
                res.append('%s: pinned %d, check %d -> %s' % (inv, k['pins'][inv], c[key],
                                                              'agree' if k['pins'][inv] == c[key] else 'DISAGREE'))
            else:
                res.append('%s: not pinned (check %d)' % (inv, c[key]))
        rows.append((name, c, k['pins'], '; '.join(res)))
    return rows


def main():
    final = 'final' in sys.argv
    # state=<dir>: write only STATE.md, from the pin counts of a scratch re-solve (REPORT.md stays tied
    # to the last exported checkpoint in export/)
    state_dir = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('state=')), None)
    # label=<name>: the re-solve is a checkpoint (checked by the independent checker; small tables in
    # checkpoints/<name>/)
    label = next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('label=')), None)
    summary = load(os.path.join(EXPORT, 'summary.json'), {})
    tiers = load(os.path.join(state_dir or EXPORT, 'pins_by_tier.json'), {})
    abl = load(os.path.join(EXPORT, 'ablation.json'))
    par = load(os.path.join(EXPORT, 'parameters.json'), {})
    notes = load(os.path.join(DATA, 'run_notes.json'), {})
    prog, nshards = pass_progress()
    lines = ['# STATE', '', 'Updated %s UTC.' % time.strftime('%Y-%m-%d %H:%M', time.gmtime()), '',
             '## Pinned values per invariant', '',
             '| tier | nodes | ' + ' | '.join(INV) + ' |', '|---|---|' + '---|' * len(INV)]

    def tkey(t):
        return (0, int(t)) if t.lstrip('-').isdigit() else (1, t)
    tot = collections.Counter()
    for t in sorted(tiers, key=tkey):
        d = tiers[t]
        lines.append('| %s | %d | ' % (t, d.get('nodes', 0)) + ' | '.join(str(d[i]) for i in INV) + ' |')
        for i in INV:
            tot[i] += d[i]
        tot['nodes'] += d.get('nodes', 0)
    lines.append('| total | %d | ' % tot['nodes'] + ' | '.join(str(tot[i]) for i in INV) + ' |')
    lines += ['', '## Pass progress (shards done out of %d; by tier)' % nshards, '']
    for pn, n, tr in prog:
        lines.append('- `%s`: %d shards %s' % (pn, n, tr))
    # ---- taper tracking: pins on knots with at most 13 crossings after each re-solve
    hpath = os.path.join(DATA, 'pin_history.jsonl')
    hist = []
    if os.path.exists(hpath):
        with open(hpath) as f:
            hist = [json.loads(l) for l in f if l.strip()]
    core = {i: sum(d[i] for t, d in tiers.items() if t.lstrip('-').isdigit() and int(t) <= 13) for i in INV}
    shards = {pn: n for pn, n, _ in prog}
    if tiers and (not hist or hist[-1]['core'] != core or hist[-1]['shards'] != shards):
        hist.append({'time': time.strftime('%Y-%m-%d %H:%M', time.gmtime()), 'shards': shards, 'core': core,
                     'all': {i: tot[i] for i in INV}, 'nodes': tot['nodes']})
        with open(hpath, 'a') as f:
            f.write(json.dumps(hist[-1], sort_keys=True) + '\n')
    lines += ['', '## Taper tracking: pins on knots with at most 13 crossings', '',
              'Taper = a notable decrease in new pins on knots with at most 13 crossings (prime knots, mirrors and '
              'composites of the node set; peripheral knots are not counted). One row per re-solve; the pass column '
              'lists the shards added since the previous row.', '',
              '| time (UTC) | passes added | ' + ' | '.join(INV) + ' | new pins |', '|---|---|' + '---|' * (len(INV) + 1)]
    prev = None
    for h in hist:
        if prev is None:
            added, new = 'start of tracking', ''
        else:
            added = ', '.join('%s +%d' % (pn, n - prev['shards'].get(pn, 0)) for pn, n in sorted(h['shards'].items())
                              if n != prev['shards'].get(pn, 0)) or 'inputs only'
            new = ' / '.join('%+d' % (h['core'][i] - prev['core'][i]) for i in INV)
        lines.append('| %s | %s | ' % (h['time'], added) + ' | '.join(str(h['core'][i]) for i in INV) + ' | %s |' % new)
        prev = h
    lines += ['', '## Notes', '']
    for k, v in (notes.get('state') or {}).items():
        lines.append('- %s: %s' % (k, v))
    if state_dir and label:
        lines.insert(3, 'Pin counts below are those of the checkpoint `%s`: solved with chains and verified by the '
                        'independent checker (checkpoints/%s/: knots.xlsx, pins_by_tier.json, summary.json, check.log, '
                        'tests.txt). Checkpoints carry no ablation and no packed export; export/ and REPORT.md are '
                        'the last full export.' % (label, label))
        lines.insert(4, '')
    elif state_dir:
        lines.insert(3, 'Pin counts below are from a re-solve on all pass data synced so far (not exported and not '
                        'checked; the last checked checkpoint is in checkpoints/, the last full export in export/ '
                        'and REPORT.md).')
        lines.insert(4, '')
    with open(os.path.join(ROOT, 'STATE.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    if state_dir:
        print('STATE.md written')
        return
    # ---------------- REPORT
    knots = {}
    kinds = collections.Counter()
    open_sizes = {i: collections.Counter() for i in INV}
    sys.path.insert(0, os.path.join(ROOT, 'checker'))
    import check as _chk                      # only its file readers (parts, gzip)
    if _chk.jsonl_parts(EXPORT, 'knots.jsonl'):
        for k in _chk.read_jsonl(EXPORT, 'knots.jsonl'):
            knots[k['node']] = k
            kinds[k['kind'] + (' (peripheral)' if k['peripheral'] else '')] += 1
    import csv
    for cpath in _chk.file_parts(EXPORT, 'knots.csv'):
        with _chk.open_text(cpath, newline='') as f:
            for row in csv.DictReader(f):
                for i in INV:
                    if row['%s_pin' % i] != '':
                        continue
                    lo, hi = row['%s_lo' % i], row['%s_hi' % i]
                    if lo == '' or hi == '':
                        open_sizes[i]['unbounded'] += 1
                    else:
                        step = 4 if i in ('M', 'r_2') else 1
                        n = (int(hi) - int(lo)) // step + 1
                        open_sizes[i]['<= %d values' % n if n <= 5 else '> 5 values'] += 1
    R = ['# REPORT', '', ('Final report.' if final else 'Interim report.') +
         ' Generated %s UTC from `export/`.' % time.strftime('%Y-%m-%d %H:%M', time.gmtime()), '']
    R += ['## Nodes by kind', '', '| kind | nodes |', '|---|---|']
    for k, n in sorted(kinds.items()):
        R.append('| %s | %d |' % (k, n))
    R += ['', 'Constraints (rule instances): %s; move edges: %s; events: %s.' % (
        summary.get('constraints'), summary.get('edges'), summary.get('events')), '']
    R += ['## Pinned values per invariant', '']
    R += lines[lines.index('| tier | nodes | ' + ' | '.join(INV) + ' |'):lines.index('| total | %d | ' % tot['nodes'] + ' | '.join(str(tot[i]) for i in INV) + ' |') + 1]
    R += ['', '## Open domains (projection hull sizes of the unpinned values)', '',
          '| invariant | ' + ' | '.join(['<= 2 values', '<= 3 values', '<= 4 values', '<= 5 values', '> 5 values', 'unbounded']) + ' |',
          '|---|---|---|---|---|---|---|']
    for i in INV:
        c = open_sizes[i]
        R.append('| %s | ' % i + ' | '.join(str(c.get(k, 0)) for k in
                 ['<= 2 values', '<= 3 values', '<= 4 values', '<= 5 values', '> 5 values', 'unbounded']) + ' |')
    R += ['', 'Sizes are the number of lattice points between the lower and upper end of the projection '
          '(M, r_2 on 4Z); the exact finite joint domains are in `export/knots.csv`.', '']
    R += ['## Ablation', '']
    if abl:
        R += ['| withheld | pins ' + ' / '.join(INV) + ' | lost ' + ' / '.join(INV) +
              ' | of these on knots up to 13 crossings | check |', '|---|---|---|---|---|']
        for a in abl:
            what = a['withheld'] + (' (passes %s)' % ', '.join(a['passes']) if a.get('passes') else '')
            if a.get('error'):
                R.append('| %s | error: %s | | | |' % (what, a['error']))
                continue
            core = a.get('lost_core')
            R.append('| %s | %s | %s | %s | %s |' % (
                what, ' / '.join(str(a['pins'][i]) for i in INV), ' / '.join(str(a['lost'][i]) for i in INV),
                ' / '.join(str(core[i]) for i in INV) if core else '', a['violations']))
        R += ['', 'Rule rows: the rules of a family (or one rule) are withheld; check = lost pins whose chain in '
              'the full run uses no withheld rule (must be 0).  Pass rows: the records of the named passes are '
              'withheld and all rules are used; check = pins of that run that are not pins of the full run with '
              'the same value (must be 0).']
    else:
        R.append('Not run yet.')
    R += ['', '## Check set (section 2.6)', '']
    cs = check_set(knots)
    if cs is None:
        R.append('`data/check_set.json` is absent: comparison skipped.')
    else:
        R += ['| knot | check | result |', '|---|---|---|']
        for name, c, pins, res in cs:
            R.append('| %s | nu=%s r_0=%s | %s |' % (name, c.get('nu_sharp'), c.get('r_0'), res))
    R += ['', '## Scope parameters used', '', '```json', json.dumps(par.get('scope'), indent=1, sort_keys=True), '```', '']
    for k, v in (notes.get('scope') or {}).items():
        R.append('- %s: %s' % (k, v))
    R += ['', '## Pass progress', '']
    for pn, n, tr in prog:
        R.append('- `%s`: %d shards done, by tier %s' % (pn, n, tr))
    R += ['', '## Tests failed / passes skipped', '']
    for item in notes.get('failed_or_skipped') or ['(nothing recorded yet)']:
        R.append('- ' + item)
    R += ['', '## Software versions', '', '```json', json.dumps(par.get('versions'), indent=1, sort_keys=True), '```', '']
    for sec, items in (notes.get('sections') or {}).items():
        R += ['## ' + sec, '']
        R += ['- ' + x for x in items]
        R.append('')
    with open(os.path.join(ROOT, 'REPORT.md'), 'w') as f:
        f.write('\n'.join(R) + '\n')
    print('STATE.md and REPORT.md written')


if __name__ == '__main__':
    main()
