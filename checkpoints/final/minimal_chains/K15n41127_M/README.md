# Small chains for M = 4 at K15n41127

The chain file of the final export (`chains/K15n41127.txt`, 380 events) holds the whole history of every node
it uses. `scripts/minimal_chain.py` cuts it down: it takes the rule instances of the final export on the nodes
within two steps of K15n41127 (111,938 instances on 3,886 nodes), and in 330 random orders keeps the chain of the
pin and drops every instance that can be dropped. No rule is added or changed; every set is solved by the solver
of the project and, written as an export of its own, checked by `checker/check.py` (RESULT: OK for the seven
sets of 8 instances).

Smallest sets found: 8 rule instances on 4 knots (7 different sets; none smaller in 330 tries).

- `set_A/` two surgery coincidences, one twist, one unknotting number: `route.txt` is the chain with the move and
  certificate records (`route.py K15n41127 M set_A`).
- `set_B/` three surgery coincidences and no move.
- `other_8_instances_*.txt` the other five sets of 8 instances (chain texts).
- `found_seed1.json`, `found_seed1000.json` the smallest sets of the two runs (8 and 60 kept), with their instances.

Commands:

    scripts/minimal_chain.py extract export=<final export> node=K15n41127 chain=<chains/K15n41127.txt> radius=2 out=r2.pkl
    scripts/minimal_chain.py minimize in=r2.pkl inv=M tries=90 procs=3 keep=8 out=<dir>
    scripts/minimal_chain.py minimize in=r2.pkl inv=M tries=240 procs=3 seed=1000 keep=60 out=<dir>
    scripts/minimal_chain.py miniexport in=<dir>/minimal.json set=<k> out=<dir>/export_<k>
    checker/check.py <dir>/export_<k>
