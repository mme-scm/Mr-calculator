"""Surgery pass over shards (resumable).
usage: run_fillings.py <tier-lo> <tier-hi> [procs=4] [p=30] [q=4] [time_limit=2] [budget=sec]
       run_fillings.py <tier-lo> <tier-hi> extend=1 outdir=<dir> [geo_tries=40] [...]
       run_fillings.py 0 0 nodes=peripheral|<index file> [chunk=1000] [...]
nodes=...: fillings of the nodes that have no table diagram (census and 'H:' nodes), one per mirror pair, from
the result diagram of the move that produced them (mrcalc/node_pd.py); nodes that already have a shard are
skipped; the new shards hold chunk nodes each.
journal=0 switches the journal off (logs/partial/fillings/<shard>.jsonl: the records of every finished node of
an unfinished shard, so that a restart loses only the nodes that were being computed).
extend=1: for the table shards already in data/fillings, the slopes of the slope set that are missing are
filled and the fillings recorded as 'unknown' (no geometric solution, not recognised) are tried again for a
geometric solution with more randomisations; the completed shards are written to outdir (same file names;
shards already there are skipped), data/fillings is not touched."""
import multiprocessing as mp
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc import config, fillings as F, passes, prepare, surgery as S  # noqa: E402


def main():
    args = sys.argv[1:]
    kv = dict(a.split('=', 1) for a in args if '=' in a)
    pos = [a for a in args if '=' not in a]
    lo, hi = int(pos[0]), int(pos[1])
    from mrcalc import conventions
    if kv.get('skip_conventions') != '1':
        conventions.assert_all(verbose=False)
        print('convention tests passed', flush=True)
    P = config.load_params()
    pm, qm = int(kv.get('p', P['slope_p'])), int(kv.get('q', P['slope_q']))
    opt = {'slopes_G': S.slope_set(pm, qm), 'slopes_T': S.slope_set(pm, qm, P['torus_integer_p']),
           'time_limit': float(kv.get('time_limit', 2.0)),
           'time_limit_torus': float(kv.get('time_limit_torus', 0.5))}
    # table knots that are torus knots get the torus slope set
    pr = prepare.Problem.__new__(prepare.Problem)
    import json
    tl = {}
    for line in open(os.path.join(config.DATA, 'constructions.jsonl')):
        r = json.loads(line)
        if r.get('family') == 'torus' and 'node' in r:
            tl[r['node']] = [r['params']['p'], r['params']['q']]
    opt['torus_like'] = tl
    shards = passes.shard_nodes()
    # table knots that are torus knots are slow (every slope goes to Regina, torus slope set): they
    # get a shard of their own (tier 99) and are left out of the table shards
    from mrcalc import names
    tab_torus = sorted((n for n in tl if names.kind(n) == 'table'), key=lambda n: (len(n), n))
    shards = {s: [n for n in ns if n not in tab_torus] for s, ns in shards.items()}
    shards['x-tabletorus-0000'] = tab_torus
    done = F.done_shards()
    extend = kv.get('extend') == '1'
    outdir = kv.get('outdir')
    by_index = kv.get('nodes')
    if by_index:
        from mrcalc import node_pd
        index = node_pd.build_index() if by_index == 'peripheral' else node_pd.load_index(by_index)
        pshards = F.node_shards(index, F.done_nodes(), int(kv.get('chunk', 1000)))
        todo = [(s, ns, opt) for s, ns in pshards.items() if s not in done]
        print('fillings: %d shards of %d nodes without a table diagram, %d generic slopes' % (
            len(todo), sum(len(ns) for _, ns, _ in todo), len(opt['slopes_G'])), flush=True)
        tasks = [(s, n, dict(opt, torus_like={}, source=index[n]['source'])) for s, ns, _ in todo for n in ns]
    elif extend:
        assert outdir, 'extend=1 needs outdir=<dir>'
        opt['geo_tries'] = int(kv.get('geo_tries', 40))
        have = set(fn[:-9] for fn in os.listdir(outdir) if fn.endswith('.jsonl.gz')) if os.path.isdir(outdir) else set()
        todo = [(s, ns, opt) for s, ns in shards.items() if lo <= passes.shard_tier(s) <= hi and s in done
                and s[0] == 't' and ns and s not in have]
        full = set(opt['slopes_G'])
        tasks = []
        nmiss = nretry = 0
        for s, ns, _ in todo:
            by_node = {}
            for r in F.read_shard(s):
                by_node.setdefault(r['node'], []).append(r)
            for nd in ns:
                rs = by_node.get(nd, [])
                seen = {(r['p'], r['q']) for r in rs}
                ext = {'missing': sorted(full - seen, key=lambda x: (x[1], x[0])) if rs else [],
                       'retry': [(r['p'], r['q']) for r in rs if r['kind'] == 'unknown'
                                 and not str(r.get('how', '')).startswith('error')]}
                nmiss += len(ext['missing'])
                nretry += len(ext['retry'])
                tasks.append((s, nd, dict(opt, extend=ext, torus_like={})))
        print('fillings (extend): %d shards, %d missing slopes, %d unknown fillings to retry' % (
            len(todo), nmiss, nretry), flush=True)
    else:
        todo = [(s, ns, opt) for s, ns in shards.items() if lo <= passes.shard_tier(s) <= hi and s not in done
                and ns and (s[0] != 's' or kv.get('composites') == '1')]
        print('fillings: %d shards, %d generic slopes' % (len(todo), len(opt['slopes_G'])), flush=True)
        tasks = [(s, n, opt) for s, ns, _ in todo for n in ns]
    t0 = time.time()
    budget = float(kv.get('budget', 1e9))
    pending = {s: set(ns) for s, ns, _ in todo}
    recs = {s: {} for s, ns, _ in todo}
    order = {s: list(ns) for s, ns, _ in todo}
    n = 0
    crashed = []

    jfiles = {}                              # shard -> journal file

    def finish(shard, node, rs, from_journal=False):
        nonlocal n
        recs[shard][node] = rs
        pending[shard].discard(node)
        if shard in jfiles and not from_journal:
            F.journal_add(jfiles[shard], node, rs)
        if not pending[shard]:
            if extend:                         # old records (a retried 'unknown' is replaced), then the new ones
                old = {}                       # node order of the file (it may hold nodes that are not tasks)
                for r in F.read_shard(shard):
                    old.setdefault(r['node'], []).append(r)
                out = []
                for nd in old:
                    new = recs[shard].get(nd, [])
                    geo = {(x['p'], x['q']): x for x in new if x.get('how') == 'retry'}
                    out += [geo.get((x['p'], x['q']), x) for x in old[nd]]
                    out += [x for x in new if x.get('how') != 'retry']
                F.write_shard(shard, out, out_dir=outdir)
            else:
                F.write_shard(shard, [x for nd in order[shard] for x in recs[shard].get(nd, [])],
                              nodes=order[shard] if by_index else None)
            del recs[shard]
            if shard in jfiles:
                F.journal_close(shard, jfiles.pop(shard))
            n += 1
            if n % 5 == 0 or n == len(todo):
                print('  %d/%d shards %.0fs' % (n, len(todo), time.time() - t0), flush=True)

    if kv.get('journal', '1') != '0':          # nodes finished before a restart are not computed again
        jkey = F.journal_key(opt, extend)
        nrec = 0
        for s, ns, _ in todo:
            have, jfiles[s] = F.journal_open(s, jkey)
            for nd in ns:
                if nd in have:
                    nrec += 1
                    finish(s, nd, have[nd], from_journal=True)
        tasks = [t for t in tasks if t[0] in pending and t[1] in pending[t[0]]]
        if nrec:
            print('journal: %d nodes recovered, %d left' % (nrec, len(tasks)), flush=True)
    # Own scheduler: every worker announces the node it starts; if a worker dies in a native library
    # (hard crash), only that node is lost: it is recorded as an error and a new worker is started.
    ctx = mp.get_context('fork')
    task_q, res_q = ctx.Queue(), ctx.Queue()
    for t in tasks:
        task_q.put(t)
    nproc = int(kv.get('procs', 4))
    for _ in range(nproc):
        task_q.put(None)
    procs = {}

    def spawn():
        p = ctx.Process(target=F.worker_loop, args=(task_q, res_q))
        p.start()
        procs[p.pid] = [p, None, time.time()]

    for _ in range(nproc):
        spawn()
    import queue
    node_timeout = float(kv.get('node_timeout', 1500))
    outstanding = {(t[0], t[1]) for t in tasks}
    taskmap = {(t[0], t[1]): t for t in tasks}

    def handle(msg):
        if msg[0] == 'start':
            if msg[1] in procs:
                procs[msg[1]][1] = (msg[2], msg[3])
                procs[msg[1]][2] = time.time()
            return
        _, pid, shard, node, rs, err = msg
        if pid in procs:
            procs[pid][1] = None
        if err:
            print('error', shard, node, err, flush=True)
        if (shard, node) in outstanding:
            outstanding.discard((shard, node))
            finish(shard, node, rs)

    def drain(timeout):
        try:
            handle(res_q.get(timeout=timeout))
            while True:
                handle(res_q.get_nowait())
        except queue.Empty:
            return

    rounds = 0
    while outstanding:
        drain(5)
        if any(not v[0].is_alive() for v in procs.values()):
            drain(0.5)                     # what a worker sent before it ended is read first
        for pid in list(procs):
            p, cur, started = procs[pid]
            dead = not p.is_alive()
            hung = cur is not None and time.time() - started > node_timeout
            if hung:
                p.terminate()
                p.join(5)
                dead = True
            if dead:
                del procs[pid]
                if cur is not None and cur in outstanding:
                    crashed.append(cur[1])
                    print('worker lost on %s (%s); node recorded as error' % (cur[1], 'timeout' if hung else 'crash'),
                          flush=True)
                    outstanding.discard(cur)
                    finish(cur[0], cur[1], [])
                if outstanding and (cur is not None or p.exitcode not in (0, None)):
                    task_q.put(None)
                    spawn()
        if not procs and outstanding:
            # every worker has ended although nodes are open (their messages were lost in a crash):
            # these nodes are queued again, twice at most, then recorded as errors
            rounds += 1
            if rounds > 2:
                for key in sorted(outstanding):
                    crashed.append(key[1])
                    print('node %s lost; recorded as error' % key[1], flush=True)
                    finish(key[0], key[1], [])
                outstanding.clear()
            else:
                for key in sorted(outstanding):
                    task_q.put(taskmap[key])
                for _ in range(nproc):
                    task_q.put(None)
                    spawn()
        if time.time() - t0 > budget:
            break
    for pid, (p, cur, started) in procs.items():
        p.terminate()
    if crashed:
        with open(os.path.join(outdir if extend else F.FILL_DIR, 'crashed_nodes.txt'), 'a') as f:
            for c in crashed:
                f.write(c + '\n')
    print('fillings done: %d shards %.0fs' % (n, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
