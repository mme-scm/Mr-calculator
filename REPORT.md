# REPORT

Interim report. Generated 2026-11-11 08:52 UTC from `export/`.

## Nodes by kind

| kind | nodes |
|---|---|
| cable | 2264 |
| census (peripheral) | 130 |
| composite | 1517 |
| table | 25852 |
| torus | 64 |
| unknot | 1 |

Constraints (rule instances): 482420; move edges: 44178; events: 365723.

## Pinned values per invariant

| tier | nodes | M | r_2 | nu | r_0 | tau | upsilon |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 5 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 6 | 8 | 6 | 2 | 8 | 5 | 8 | 8 |
| 7 | 16 | 14 | 4 | 12 | 8 | 16 | 16 |
| 8 | 46 | 34 | 6 | 40 | 13 | 46 | 46 |
| 9 | 116 | 80 | 6 | 84 | 14 | 114 | 110 |
| 10 | 363 | 225 | 4 | 279 | 14 | 353 | 333 |
| 11 | 1226 | 718 | 8 | 866 | 22 | 1176 | 1104 |
| 12 | 4607 | 1151 | 2 | 3009 | 6 | 3863 | 3383 |
| 13 | 20950 | 3324 | 6 | 12128 | 34 | 15552 | 13286 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 22 | 22 | 64 | 64 | 64 | 64 |
| peripheral | 130 | 8 | 4 | 48 | 48 | 6 | 0 |
| total | 29828 | 5620 | 72 | 16556 | 236 | 21236 | 18388 |

## Open domains (projection hull sizes of the unpinned values)

| invariant | <= 2 values | <= 3 values | <= 4 values | <= 5 values | > 5 values | unbounded |
|---|---|---|---|---|---|---|
| M | 14456 | 4130 | 46 | 2366 | 1582 | 1628 |
| r_2 | 26 | 28 | 22 | 16 | 634 | 29030 |
| nu | 372 | 10286 | 4 | 330 | 1164 | 1116 |
| r_0 | 2 | 8 | 0 | 0 | 1148 | 28434 |
| tau | 3400 | 2912 | 14 | 4 | 1146 | 1116 |
| upsilon | 5704 | 2440 | 0 | 674 | 358 | 2264 |

Sizes are the number of lattice points between the lower and upper end of the projection (M, r_2 on 4Z); the exact finite joint domains are in `export/knots.csv`.

## Ablation

| withheld | pins M / r_2 / nu / r_0 / tau / upsilon | lost M / r_2 / nu / r_0 / tau / upsilon | lost pins whose full-run chain lacks the withheld family |
|---|---|---|---|
| I | 1638 / 2 / 1 / 0 / 19113 / 15930 | 3982 / 70 / 16555 / 236 / 2123 / 2458 | 0 |
| unary | 5620 / 72 / 2242 / 228 / 2856 / 7882 | 0 / 0 / 14314 / 8 / 18380 / 10506 | 0 |
| cc | 5540 / 72 / 16250 / 236 / 20870 / 18366 | 80 / 0 / 306 / 0 / 366 / 22 | 0 |
| twist | 3434 / 72 / 16556 / 236 / 21236 / 16420 | 2186 / 0 / 0 / 0 / 0 / 1968 | 0 |
| coincidence | 5608 / 56 / 16556 / 225 / 21236 / 18388 | 12 / 16 / 0 / 11 / 0 / 0 | 0 |
| coupling | 5620 / 72 / 16556 / 236 / 21236 / 18388 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| mutation | 5612 / 72 / 16556 / 236 / 21236 / 18388 | 8 / 0 / 0 / 0 / 0 / 0 | 0 |
| mirror_composite | 2091 / 51 / 13802 / 140 / 17899 / 15729 | 3529 / 21 / 2754 / 96 / 3337 / 2659 | 0 |
| F11 | 5620 / 72 / 16556 / 236 / 21236 / 18388 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| F12 | 3302 / 44 / 16556 / 236 / 21236 / 18388 | 2318 / 28 / 0 / 0 / 0 / 0 | 0 |
| F13 | 5610 / 41 / 16556 / 236 / 21236 / 18388 | 10 / 31 / 0 / 0 / 0 / 0 | 0 |
| F14 | 5614 / 72 / 16556 / 236 / 21236 / 18388 | 6 / 0 / 0 / 0 / 0 / 0 | 0 |
| C11 | 5620 / 72 / 16556 / 236 / 21236 / 18388 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| C12 | 5620 / 72 / 16552 / 232 / 21234 / 18388 | 0 / 0 / 4 / 4 / 2 / 0 | 0 |
| C13 | 5620 / 72 / 16550 / 213 / 21232 / 18388 | 0 / 0 / 6 / 23 / 4 / 0 | 0 |
| C14 | 5620 / 72 / 16518 / 141 / 21236 / 18388 | 0 / 0 / 38 / 95 / 0 / 0 | 0 |

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


## Pass progress

- `cc`: 62 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 31}
- `mu`: 31 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14}
- `tw2`: 29 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14}
- `fillings`: 29 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 99: 2}

## Tests failed / passes skipped

- (nothing recorded yet)

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

