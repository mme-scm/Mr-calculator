# REPORT

Checkpoint report (passes continue; see "Tests failed / passes skipped"). Generated 2026-11-11 11:32 UTC from `export/`.

## Nodes by kind

| kind | nodes |
|---|---|
| cable | 2264 |
| census (peripheral) | 13142 |
| composite | 1517 |
| hyp (peripheral) | 818 |
| table | 25852 |
| torus | 64 |
| unknot | 1 |

Constraints (rule instances): 770742; move edges: 117151; events: 496999.

## Pinned values per invariant

| tier | nodes | M | r_2 | nu | r_0 | tau | upsilon |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 5 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 6 | 8 | 8 | 2 | 8 | 5 | 8 | 8 |
| 7 | 16 | 14 | 4 | 12 | 8 | 16 | 16 |
| 8 | 46 | 42 | 6 | 40 | 13 | 46 | 46 |
| 9 | 116 | 96 | 6 | 84 | 14 | 114 | 116 |
| 10 | 363 | 293 | 6 | 279 | 14 | 353 | 355 |
| 11 | 1226 | 972 | 8 | 866 | 22 | 1176 | 1204 |
| 12 | 4607 | 3463 | 8 | 3199 | 17 | 4233 | 4395 |
| 13 | 20950 | 10730 | 6 | 13090 | 36 | 16734 | 19640 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 26 | 26 | 124 | 124 | 64 | 150 |
| peripheral | 13960 | 1478 | 4 | 66 | 48 | 252 | 12672 |
| total | 43658 | 17160 | 84 | 17786 | 309 | 23034 | 38640 |

## Open domains (projection hull sizes of the unpinned values)

| invariant | <= 2 values | <= 3 values | <= 4 values | <= 5 values | > 5 values | unbounded |
|---|---|---|---|---|---|---|
| M | 12640 | 9944 | 1356 | 228 | 702 | 1628 |
| r_2 | 28 | 40 | 22 | 16 | 616 | 42852 |
| nu | 374 | 9524 | 6 | 744 | 1504 | 13720 |
| r_0 | 4 | 14 | 0 | 26 | 1056 | 42249 |
| tau | 4142 | 1234 | 28 | 14 | 1486 | 13720 |
| upsilon | 1556 | 334 | 756 | 168 | 524 | 1680 |

Sizes are the number of lattice points between the lower and upper end of the projection (M, r_2 on 4Z); the exact finite joint domains are in `export/knots.csv`.

## Ablation

| withheld | pins M / r_2 / nu / r_0 / tau / upsilon | lost M / r_2 / nu / r_0 / tau / upsilon | lost pins whose full-run chain lacks the withheld family |
|---|---|---|---|
| I | 3764 / 2 / 1 / 0 / 20707 / 17578 | 13396 / 82 / 17785 / 309 / 2327 / 21062 | 0 |
| unary | 17160 / 84 / 7350 / 293 / 9474 / 33676 | 0 / 0 / 10436 / 16 / 13560 / 4964 | 0 |
| cc | 13054 / 80 / 16342 / 309 / 21092 / 36748 | 4106 / 4 / 1444 / 0 / 1942 / 1892 | 0 |
| twist | 7798 / 80 / 17786 / 309 / 23034 / 37348 | 9362 / 4 / 0 / 0 / 0 / 1292 | 0 |
| coincidence | 17152 / 60 / 17772 / 275 / 23034 / 38640 | 8 / 24 / 14 / 34 / 0 / 0 | 0 |
| coupling | 17160 / 84 / 17786 / 309 / 23034 / 38640 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| mutation | 16834 / 84 / 17786 / 309 / 23034 / 38640 | 326 / 0 / 0 / 0 / 0 / 0 | 0 |
| mirror_composite | 6999 / 57 / 14553 / 179 / 18950 / 26142 | 10161 / 27 / 3233 / 130 / 4084 / 12498 | 0 |
| F11 | 17160 / 84 / 17786 / 309 / 23034 / 38640 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| F12 | 17130 / 64 / 17786 / 309 / 23034 / 38640 | 30 / 20 / 0 / 0 / 0 / 0 | 0 |
| F13 | 17156 / 74 / 17786 / 309 / 23034 / 38640 | 4 / 10 / 0 / 0 / 0 / 0 | 0 |
| F14 | 17156 / 84 / 17786 / 309 / 23034 / 38640 | 4 / 0 / 0 / 0 / 0 / 0 | 0 |
| C11 | 17160 / 84 / 17738 / 261 / 23034 / 38640 | 0 / 0 / 48 / 48 / 0 / 0 | 0 |
| C12 | 17160 / 84 / 17782 / 305 / 23032 / 38640 | 0 / 0 / 4 / 4 / 2 / 0 | 0 |
| C13 | 17160 / 84 / 17780 / 286 / 23030 / 38640 | 0 / 0 / 6 / 23 / 4 / 0 | 0 |
| C14 | 17160 / 84 / 17746 / 209 / 23034 / 38640 | 0 / 0 / 40 / 100 / 0 / 0 | 0 |

## Check set (section 2.6)

`data/check_set.json` is absent: comparison skipped.

## Scope parameters used

```json
{
 "P_cab": 15,
 "family_max_crossings": 15,
 "k_max": {
  "11": 5,
  "12-20": 4,
  "<=10": 6,
  ">20": 0
 },
 "max_cable_companion_crossings": 8,
 "max_imbalance": 2,
 "recognition_time_limit_s": 60,
 "rediagrams": 3,
 "slope_p": 30,
 "slope_q": 4,
 "torus_integer_p": 60,
 "torus_pq_max": 60
}
```

- node set: as specified: 12965 table knots and their mirrors, 1517 composite nodes, positive torus knots with pq <= 60 and mirrors, 2268 cable nodes (companions with at most 8 crossings, s in {2,3}, |r| <= P_cab = 15)
- diagrams: at most 11 crossings: KnotInfo PD code, braid closure(s) of KnotInfo braid word(s), 3 seeded re-diagrams (specification value). 12-13 crossings: KnotInfo PD code and braid closure, 0 re-diagrams (shrunk from 3). Torus knots: braid closure and 1 re-diagram
- crossing changes: at most 11 crossings: every crossing of all 5 diagrams of every prime knot and of the composites with crossing sum <= 9. 12-13 crossings: every crossing of the KnotInfo PD diagram (braid-closure diagrams for the first 31 of 305 shards only). Torus knots: braid-closure diagrams. Mirror nodes: not recomputed (implied by F3/C3/U4b)
- twists: k_max shrunk from 6/5/4 to: k = 2 and k = 3 on the KnotInfo PD diagram of every prime knot with at most 11 crossings; k = 3 on the PD diagrams of part of the 12-crossing knots (time-boxed, see pass progress); k = 4 on prime knots with at most 8 crossings (probe); |a-b| <= 2 and both handednesses throughout; no twists on braid closures, re-diagrams, 13-crossing, composite, torus or cable diagrams
- mutations: every diagrammatic Conway circle, three rotations: PD and braid-closure diagrams for at most 11 crossings, PD diagrams for 12-13 crossings; composites with crossing sum <= 9
- slope set: X1/X3 (all nodes): |p| <= 30, q <= 4 (specification), plus integers |p| <= 60 for torus knots and the S3/S4 slopes for cables. Fillings actually built: |p| <= 30, q <= 4 for prime knots with at most 11 crossings; |p| <= 30, q <= 2 for 12 crossings; |p| <= 30, q = 1 for 13 crossings; torus slope set for torus knots; none for composites and cables (S3/S4 need no recognition)
- recognition time limit: 1.5 s per filling (at most 11 crossings), 0.3 s (12 crossings), 0.2 s (13 crossings), 0.5 s for torus-knot fillings (shrunk from 60 s); enforced inside the Regina retriangulation search instead of a subprocess; each node is processed by a worker that is replaced if it crashes or exceeds 25 minutes
- coincidence certificates: candidates are fillings with equal |p| and volume within 2e-7; verification (verify_hyperbolicity) and the verified isometry signature are computed only for candidates, in priority order (clusters containing a node with pinned r_2 or r_0 first) under a time budget; self-coincidences p/q, -p/q of amphichiral knots are skipped because their equations are implied by F5/C5
- peripheral nodes: a result that is not a core node is instantiated as a node only if it is reached from two distinct core nodes or a homogeneous diagram of it was found; other identified results are counted (parameters.json, stats) but not instantiated; unidentified results are discarded
- calculator: KnotInfo PD codes of all table knots; construction diagrams of composites, torus knots and family constructions; cable diagrams with at most 40 crossings (10 s limit); instantiated peripheral nodes (30 s limit); complexes (milestone 7) only for nodes whose upsilon was not pinned
- identification: Regina solid-torus test only when the Alexander polynomial is trivial; Regina isosig matching of non-hyperbolic results against the pool of torus knots, composites, family constructions and small cables with a bounded retriangulation search

## Pass progress

- `cc`: 337 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250, 99: 1}
- `mu`: 336 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw2`: 29 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw3`: 82 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55}
- `tw4`: 6 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}
- `fillings`: 334 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250, 99: 2}

## Tests failed / passes skipped

- IN PROGRESS, NOT COMPLETE: the taper criterion of section 11 is not yet met and the widening round has not been run. This export is a checkpoint; passes not yet completed are listed below and under "Pass progress".
- Twists: specification values k_max 6/5/4 on five diagrams per knot were not run (estimated at about a month). Run: k = 2, 3 on KnotInfo PD diagrams up to 11 crossings, k = 3 on part of the 12-crossing knots, k = 4 probe up to 8 crossings.
- Crossing changes on composite diagrams with crossing sum 10-13: not completed (sum <= 9 done). Mutations on composite diagrams with crossing sum 10-13: not run.
- Crossing changes on braid-closure diagrams of 12-13 crossing knots: 31 of 305 shards. Re-diagrams of 12-13 crossing knots: none.
- Crossing-change and twist passes on cable diagrams: not run. Twists on torus-knot diagrams: not run.
- Fillings of composite and cable nodes: not built (cables use S3/S4 only). Slope set for 12-13 crossing knots reduced as listed under scope.
- Coincidence search: the signature step stopped at its time budget; candidates without a verified signature give no S1 equation (counts in the pass log).
- Peripheral nodes received no move passes of their own.
- Calculator on cable diagrams with more than 40 crossings: not run (g, fibered, tau unknown for those cable nodes; see WANTED_RULES.md #1).
- A filling pass worker crashed inside a native library (segmentation fault in PARI under the Sage-enabled interpreter) during the first tier <= 11 run; the pass was rerun with the plain SnapPy interpreter and a crash-tolerant scheduler; no data from the crashed run were kept for the affected nodes.
- Tests: the section-3 convention tests passed before every pass; operator soundness, exactness on finite domains, diagram, solver, surgery and checker tests: see the line below.

## Software versions

```json
{
 "database_knotinfo": "2026.11.2",
 "knot_floer_homology": "1.2.2",
 "networkx": "3.7",
 "openpyxl": "3.1.5",
 "passagemath-standard": "10.8.13",
 "regina": "7.4.1",
 "snappy": "3.3.2",
 "snappy_15_knots": "1.2.1",
 "snappy_manifolds": "1.4",
 "spherogram": "2.4.1"
}
```

## Cost estimate at the specification values (after milestone 1)

- Measured on this machine (4 cores): identification of a crossing-change result 27 ms on KnotInfo diagrams and about 120 ms on re-diagrams (14-18 crossings, kinks, more non-hyperbolic results); identification of a twist result about 120 ms for k <= 4 on a 10-crossing diagram and more for k = 5, 6 (20 to 30 extra crossings); a filling costs about 0.3 ms when SnapPy finds a geometric solution, and the recognition time limit for each of the 2 to 6 slopes per knot where it does not.
- Dual-graph paths with |a-b| <= 2 on a 10-crossing diagram: about 60 (k=2), 140 (k=3), 360 (k=4), 550 (k=5), 960 (k=6), each twisted in both senses.
- Crossing changes at the specification values: about 2 CPU-hours for nodes of at most 11 crossings, about 29 CPU-hours for 12-13 crossings (5 diagrams per knot).
- Twists at the specification values (k_max 6/5/4, five diagrams per knot): about 210 CPU-hours for at most 10 crossings, 250 for 11 crossings, 2400 for 12-13 crossings: about a month on this machine. Shrunk (values below).
- Fillings at the specification values (160 slopes, 60 s recognition limit): up to 650 CPU-hours; with a 1.5 s limit about 18 CPU-hours for all table knots.
- Cables: 2268 cable diagrams of 13 to 110 crossings; crossing changes on all of them are estimated at 150 CPU-hours or more. Not run (see skipped passes).
- Revised after removing the main bottleneck (Regina solid-torus test now only when the Alexander polynomial is trivial): identification costs about 13-27 ms per k = 3 result and about 50 ms per k = 4 result. Twists at the specification values on KnotInfo PD diagrams only: about 39 CPU-hours (at most 10 crossings), 29 (11 crossings), 216 (12-13 crossings), i.e. about 3 days on 4 cores; on all five diagrams per knot about 2-3 weeks. The 12-13 crossing tier dominates because it holds 94% of the knots; within it k = 4 dominates.

## Pins after each round (M / r_2 / nu / r_0 / tau / upsilon), all nodes

- initialisers, unary rules, families, mirror, composite, coupling; crossing changes for at most 11 crossings: 3312 / 56 / 16396 / 221 / 21032 / 16404
- + cable nodes with S3/S4: 3524 / 66 / 16418 / 236 / 21060 / 16560
- + k = 2 twists, fillings and coincidences, mutations for at most 11 crossings: 5620 / 72 / 16556 / 236 / 21236 / 18388
- + crossing changes for 12-13 crossings (KnotInfo PD diagrams): 9550 / 72 / 17698 / 236 / 22782 / 20448
- + mutations for 12-13 crossings, k = 3 twists from knots with at most 8 crossings, upsilon (milestone 7): 10298 / 78 / 17706 / 238 / 22790 / 26158
- + k = 3 twists from knots with 9-11 crossings: 12882 / 80 / 17706 / 238 / 22800 / 26158
- + fillings and coincidences for 12-13 crossings, calculator inputs of peripheral nodes and small cables: 12882 / 84 / 17768 / 297 / 22990 / 26158
- k = 4 twists from knots with at most 8 crossings (probe, 681 edges): no new pin
- final numbers (after the time-boxed k = 3 twists on 12-crossing knots): see the table above

