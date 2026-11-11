"""Surgery pass over shards (resumable).
usage: run_fillings.py <tier-lo> <tier-hi> [procs=4] [p=30] [q=4] [time_limit=2] [budget=sec]"""
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
    todo = [(s, ns, opt) for s, ns in shards.items() if lo <= passes.shard_tier(s) <= hi and s not in done
            and ns and (s[0] != 's' or kv.get('composites') == '1')]
    print('fillings: %d shards, %d generic slopes' % (len(todo), len(opt['slopes_G'])), flush=True)
    t0 = time.time()
    budget = float(kv.get('budget', 1e9))
    tasks = [(s, n, opt) for s, ns, _ in todo for n in ns]
    pending = {s: set(ns) for s, ns, _ in todo}
    recs = {s: {} for s, ns, _ in todo}
    order = {s: list(ns) for s, ns, _ in todo}
    n = 0
    crashed = []

    def finish(shard, node, rs):
        nonlocal n
        recs[shard][node] = rs
        pending[shard].discard(node)
        if not pending[shard]:
            F.write_shard(shard, [x for nd in order[shard] for x in recs[shard].get(nd, [])])
            del recs[shard]
            n += 1
            if n % 5 == 0 or n == len(todo):
                print('  %d/%d shards %.0fs' % (n, len(todo), time.time() - t0), flush=True)

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
    remaining = len(tasks)
    node_timeout = float(kv.get('node_timeout', 1500))
    while remaining > 0:
        try:
            msg = res_q.get(timeout=5)
        except Exception:
            msg = None
        if msg is not None:
            if msg[0] == 'start':
                if msg[1] in procs:
                    procs[msg[1]][1] = (msg[2], msg[3])
                    procs[msg[1]][2] = time.time()
            else:
                _, pid, shard, node, rs, err = msg
                if pid in procs:
                    procs[pid][1] = None
                if err:
                    print('error', shard, node, err, flush=True)
                finish(shard, node, rs)
                remaining -= 1
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
                if cur is not None:
                    crashed.append(cur[1])
                    print('worker lost on %s (%s); node recorded as error' % (cur[1], 'timeout' if hung else 'crash'),
                          flush=True)
                    finish(cur[0], cur[1], [])
                    remaining -= 1
                if remaining > 0 and (cur is not None or p.exitcode not in (0, None)):
                    task_q.put(None)
                    spawn()
        if not procs and remaining > 0:
            task_q.put(None)
            spawn()
        if time.time() - t0 > budget:
            break
    for pid, (p, cur, started) in procs.items():
        p.terminate()
    if crashed:
        with open(os.path.join(F.FILL_DIR, 'crashed_nodes.txt'), 'a') as f:
            for c in crashed:
                f.write(c + '\n')
    print('fillings done: %d shards %.0fs' % (n, time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
