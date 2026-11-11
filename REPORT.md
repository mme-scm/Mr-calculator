# REPORT

Interim report. Generated 2026-11-11 09:47 UTC from `export/`.

## Nodes by kind

| kind | nodes |
|---|---|
| cable | 2264 |
| census (peripheral) | 350 |
| composite | 1517 |
| table | 25852 |
| torus | 64 |
| unknot | 1 |

Constraints (rule instances): 566999; move edges: 71772; events: 385843.

## Pinned values per invariant

| tier | nodes | M | r_2 | nu | r_0 | tau | upsilon |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 5 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 6 | 8 | 6 | 2 | 8 | 5 | 8 | 8 |
| 7 | 16 | 14 | 4 | 12 | 8 | 16 | 16 |
| 8 | 46 | 38 | 6 | 40 | 13 | 46 | 46 |
| 9 | 116 | 82 | 6 | 84 | 14 | 114 | 116 |
| 10 | 363 | 245 | 4 | 279 | 14 | 353 | 355 |
| 11 | 1226 | 768 | 8 | 866 | 22 | 1176 | 1204 |
| 12 | 4607 | 2395 | 4 | 3197 | 8 | 4233 | 4395 |
| 13 | 20950 | 6678 | 6 | 13090 | 34 | 16734 | 19640 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 26 | 26 | 64 | 64 | 64 | 64 |
| peripheral | 350 | 8 | 4 | 48 | 48 | 8 | 276 |
| total | 30048 | 10298 | 78 | 17706 | 238 | 22790 | 26158 |

## Open domains (projection hull sizes of the unpinned values)

| invariant | <= 2 values | <= 3 values | <= 4 values | <= 5 values | > 5 values | unbounded |
|---|---|---|---|---|---|---|
| M | 14378 | 1758 | 38 | 1000 | 948 | 1628 |
| r_2 | 22 | 28 | 22 | 16 | 634 | 29248 |
| nu | 372 | 9292 | 4 | 396 | 1154 | 1124 |
| r_0 | 2 | 8 | 0 | 0 | 1148 | 28652 |
| tau | 3754 | 1226 | 6 | 2 | 1146 | 1124 |
| upsilon | 1380 | 100 | 0 | 76 | 70 | 2264 |

Sizes are the number of lattice points between the lower and upper end of the projection (M, r_2 on 4Z); the exact finite joint domains are in `export/knots.csv`.

## Ablation

| withheld | pins M / r_2 / nu / r_0 / tau / upsilon | lost M / r_2 / nu / r_0 / tau / upsilon | lost pins whose full-run chain lacks the withheld family |
|---|---|---|---|
| I | 3764 / 2 / 1 / 0 / 20477 / 17578 | 6534 / 76 / 17705 / 238 / 2313 / 8580 | 0 |
| unary | 10298 / 78 / 7282 / 230 / 9468 / 21122 | 0 / 0 / 10424 / 8 / 13322 / 5036 | 0 |
| cc | 6398 / 74 / 16262 / 238 / 20884 / 24266 | 3900 / 4 / 1444 / 0 / 1906 / 1892 | 0 |
| twist | 7742 / 78 / 17706 / 238 / 22790 / 24866 | 2556 / 0 / 0 / 0 / 0 / 1292 | 0 |
| coincidence | 10290 / 60 / 17706 / 227 / 22790 / 26158 | 8 / 18 / 0 / 11 / 0 / 0 | 0 |
| coupling | 10298 / 78 / 17706 / 238 / 22790 / 26158 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| mutation | 10088 / 78 / 17706 / 238 / 22790 / 26158 | 210 / 0 / 0 / 0 / 0 / 0 | 0 |
| mirror_composite | 3796 / 54 / 14508 / 141 / 18824 / 19898 | 6502 / 24 / 3198 / 97 / 3966 / 6260 | 0 |
| F11 | 10298 / 78 / 17706 / 238 / 22790 / 26158 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| F12 | 9336 / 54 / 17706 / 238 / 22790 / 26158 | 962 / 24 / 0 / 0 / 0 / 0 | 0 |
| F13 | 10294 / 47 / 17706 / 238 / 22790 / 26158 | 4 / 31 / 0 / 0 / 0 / 0 | 0 |
| F14 | 10294 / 78 / 17706 / 238 / 22790 / 26158 | 4 / 0 / 0 / 0 / 0 / 0 | 0 |
| C11 | 10298 / 78 / 17706 / 238 / 22790 / 26158 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| C12 | 10298 / 78 / 17702 / 234 / 22788 / 26158 | 0 / 0 / 4 / 4 / 2 / 0 | 0 |
| C13 | 10298 / 78 / 17700 / 215 / 22786 / 26158 | 0 / 0 / 6 / 23 / 4 / 0 | 0 |
| C14 | 10298 / 78 / 17668 / 143 / 22790 / 26158 | 0 / 0 / 38 / 95 / 0 / 0 | 0 |

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
- diagrams: at most 11 crossings: KnotInfo PD code, braid closure(s) of KnotInfo braid word(s), 3 seeded re-diagrams (specification value). 12-13 crossings: KnotInfo PD code and braid closure built, 0 re-diagrams (shrunk from 3)
- crossing changes: at most 11 crossings: every crossing of all 5 diagrams of every prime knot and of composites with crossing sum <= 9. 12-13 crossings: every crossing of the KnotInfo PD diagram (braid-closure diagrams only for the first 31 of 305 shards). Mirror nodes: not recomputed (implied by F3/C3/U4b)
- twists: k = 2 only (k_max shrunk from 6/5/4 to 2), |a-b| <= 2, both handednesses, on the KnotInfo PD diagram of every prime knot with at most 11 crossings; a k = 3 probe on prime knots with at most 8 crossings; no twists from 12-13 crossing diagrams, composite, torus or cable diagrams
- mutations: every diagrammatic Conway circle, three rotations: PD and braid-closure diagrams for at most 11 crossings, PD diagrams for 12-13 crossings
- slope set: X1/X3 (all nodes): |p| <= 30, q <= 4 (specification), plus integers |p| <= 60 for torus knots and the S3/S4 slopes for cables. Fillings actually built: |p| <= 30, q <= 4 for prime knots with at most 11 crossings; |p| <= 30, q <= 2 for 12 crossings; |p| <= 30, q = 1 for 13 crossings; torus slope set for torus knots; none for composites and cables (S3/S4 need no recognition)
- recognition time limit: 1.5 s per filling (at most 11 crossings), 0.3 s (12 crossings), 0.2 s (13 crossings), 0.5 s for torus-knot fillings (shrunk from 60 s); enforced inside the Regina retriangulation search instead of a subprocess
- coincidence certificates: candidates are fillings with equal |p| and volume within 2e-7; verification and isometry signature only for candidates, in priority order (clusters containing a node with pinned r_2 or r_0 first) under a time budget; self-coincidences p/q, -p/q of amphichiral knots are skipped because their equations are implied by F5/C5
- peripheral nodes: a result that is not a core node is instantiated as a node only if it is reached from two distinct core nodes or a homogeneous diagram of it was found (the criterion of section 4); other identified results are counted but not instantiated
- calculator: KnotInfo PD codes of all table knots; construction diagrams of composites, torus knots, family constructions; cable diagrams with at most 40 crossings (10 s limit); peripheral nodes (30 s limit)

## Pass progress

- `cc`: 337 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250, 99: 1}
- `mu`: 336 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw2`: 29 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw3`: 22 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 9}
- `fillings`: 334 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250, 99: 2}

## Tests failed / passes skipped

- Crossing changes on composite diagrams with crossing sum 10-13 were not completed (identification of composite results is slow); sum <= 9 done.
- Crossing changes on braid-closure diagrams of 12-13 crossing knots: only 31 of 305 shards (results with more than 13 crossings need census look-ups; stopped for time).
- Twists: only k = 2 on KnotInfo PD diagrams of knots with at most 11 crossings, plus a k = 3 probe on knots with at most 8 crossings; the specification values (k_max 6/5/4, five diagrams, all tiers) were estimated at about a month of computation.
- Crossing-change and twist passes on cable diagrams and on re-diagrams of torus knots were not run.
- Fillings of composite nodes and of cable nodes (other than the S3/S4 identities) were not built.
- The signature step of the coincidence search stopped at its time budget; candidates without a signature are listed in the log of scripts/find_coincidences.py and give no S1 equation.
- Peripheral nodes received no move passes (the one-round rule of section 4 was not exercised).
- The widening round (P_cab + 5, k_max + 1, slopes + 10 / q + 1, re-diagrams + 2) was not run as a whole; only the k = 3 twist probe was. The taper criterion of section 11 is therefore not established: the run was stopped early for time.
- Convention tests of section 3: all passed before every pass. Operator soundness tests: all passed.

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

