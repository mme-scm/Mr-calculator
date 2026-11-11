# Invariants of small knots: constraint-propagation pipeline

A computational pipeline that propagates a fixed, closed catalogue of rules over computed data to bound
six integer invariants (M, r_2, nu^#, r_0, tau^#, upsilon) of small knots. Every pinned value comes with a
machine-generated chain of rule applications (`export/chains/`).

* `REPORT.md` — results, ablation, scope parameters used, skipped passes.
* `STATE.md` — pinned counts and pass progress.
* `WANTED_RULES.md` — statements that would help but are not in the catalogue (never used).
* `export/` — deliverable (`knots.csv` / `knots.xlsx` are the human-readable tables; `FORMAT.md` documents every file).
* `checker/check.py` — independent checker: replays `export/events.jsonl`, rebuilds every chain file.
* `route.py <node> <invariant>` — prints the chain of a pinned value with the cited edges inlined.

## Layout

| path | content |
|---|---|
| `mrcalc/pd.py` | planar diagrams: PD codes, crossing changes, full twists, cables, pretzels, mutation, Reidemeister moves |
| `mrcalc/identify.py` | identification service with certificates (hyperbolic isometry signature / Regina isosig) |
| `mrcalc/surgery.py`, `mrcalc/fillings.py` | fillings, Regina recognition, Moser (S2) |
| `mrcalc/rules.py`, `mrcalc/domains.py`, `mrcalc/solver.py` | rule operators, domains, worklist propagation with events |
| `mrcalc/prepare.py` | instantiates the rules with data (nodes, constraints, edges) |
| `mrcalc/export.py` | export |
| `mrcalc/conventions.py` | section-3 convention tests (run before every pass) |
| `scripts/` | pass drivers (resumable, sharded), solve/export, ablation, report |
| `data/` | KnotInfo snapshot, reference tables, pass shards, fillings, calculator caches |
| `tests/` | conventions, operator soundness, diagrams, solver, checker |

## Reproducing

```bash
python scripts/build_refs.py all            # reference tables and KnotInfo checks
python scripts/build_constructions.py       # family constructions, composite/torus inputs
python scripts/run_pass.py diagrams 3 11    # diagrams, then passes (cc, tw, mu), fillings, coincidences
python scripts/solve.py ablation            # re-solve, validate, export
python checker/check.py export              # independent check and chain round trip
python scripts/report.py final
```

Requires SnapPy (with spherogram, snappy_15_knots) inside a Sage-enabled Python (passagemath) for verified
hyperbolicity, Regina, database_knotinfo, knot_floer_homology, networkx, openpyxl. Versions used are in
`export/parameters.json`.
