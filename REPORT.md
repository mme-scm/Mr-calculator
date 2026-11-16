# REPORT

Final report. Generated 2026-11-16 18:23 UTC from the export `final` (repository mme-scm/Mr-export, branch export/final; small tables in checkpoints/final/).

## Nodes by kind

| kind | nodes |
|---|---|
| cable | 2264 |
| census (peripheral) | 378971 |
| composite | 1517 |
| hyp (peripheral) | 258099 |
| table | 25852 |
| torus | 64 |
| unknot | 1 |

Constraints (rule instances): 14067936; move edges: 2975199; events: 7899323.

## Pinned values per invariant

| tier | nodes | M | r_2 | nu | r_0 | tau | upsilon |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 5 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 6 | 8 | 8 | 5 | 8 | 6 | 8 | 8 |
| 7 | 16 | 16 | 8 | 12 | 8 | 16 | 16 |
| 8 | 46 | 46 | 21 | 40 | 21 | 46 | 46 |
| 9 | 116 | 114 | 18 | 86 | 18 | 116 | 116 |
| 10 | 363 | 357 | 42 | 285 | 38 | 355 | 357 |
| 11 | 1226 | 1202 | 38 | 872 | 34 | 1190 | 1204 |
| 12 | 4607 | 4461 | 55 | 3307 | 49 | 4409 | 4411 |
| 13 | 20950 | 20098 | 54 | 14586 | 60 | 19344 | 19938 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 32 | 32 | 124 | 124 | 70 | 150 |
| peripheral | 637070 | 282380 | 106 | 18264 | 72 | 370836 | 520730 |
| total | 666768 | 308752 | 387 | 37602 | 438 | 396428 | 547014 |

## Open domains (projection hull sizes of the unpinned values)

| invariant | <= 2 values | <= 3 values | <= 4 values | <= 5 values | > 5 values | unbounded |
|---|---|---|---|---|---|---|
| M | 281452 | 63510 | 6324 | 4452 | 1484 | 794 |
| r_2 | 64 | 36 | 22 | 16 | 1408 | 664835 |
| nu | 390 | 364588 | 6 | 59336 | 204234 | 612 |
| r_0 | 6 | 80 | 4 | 58 | 1412 | 664770 |
| tau | 64544 | 16536 | 70 | 2268 | 186310 | 612 |
| upsilon | 76688 | 22238 | 11096 | 4462 | 3590 | 1680 |

Sizes are the number of lattice points between the lower and upper end of the projection (M, r_2 on 4Z); the exact finite joint domains are in `export/knots.csv`.

## u_Z, u_R, u_M (rules N1-N6, RULES_U.md)

Solved by scripts/solve_u.py on the same pass data, checked by checker/check_u.py (checkpoints/u_final/).

Ranges of u_Z, u_R and u_M (u_Z with mutation invariance) by crossing number (a knot and its mirror count separately; composites by crossing sum).
"anchored": value given by rule N1 or N2 alone.  "Z 0" / "R 0": determined; the other columns: width of the range.
| cr | nodes | anchored | Z 0 | Z <=1 | Z <=2 | Z >2 | Z unbounded | R 0 | R <=1 | R <=2 | R >2 | R unbounded | M 0 | M <=1 | M <=2 | M >2 | M unbounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 3 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| 4 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 5 | 4 | 4 | 4 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| 6 | 8 | 6 | 8 | 0 | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 |
| 7 | 16 | 14 | 16 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| 8 | 46 | 38 | 46 | 0 | 0 | 0 | 0 | 46 | 0 | 0 | 0 | 0 | 46 | 0 | 0 | 0 | 0 |
| 9 | 116 | 96 | 116 | 0 | 0 | 0 | 0 | 116 | 0 | 0 | 0 | 0 | 116 | 0 | 0 | 0 | 0 |
| 10 | 363 | 305 | 363 | 0 | 0 | 0 | 0 | 363 | 0 | 0 | 0 | 0 | 363 | 0 | 0 | 0 | 0 |
| 11 | 1226 | 766 | 1224 | 2 | 0 | 0 | 0 | 1224 | 2 | 0 | 0 | 0 | 1224 | 2 | 0 | 0 | 0 |
| 12 | 4607 | 2647 | 4599 | 8 | 0 | 0 | 0 | 4599 | 8 | 0 | 0 | 0 | 4599 | 8 | 0 | 0 | 0 |
| 13 | 20950 | 10226 | 20868 | 82 | 0 | 0 | 0 | 20868 | 82 | 0 | 0 | 0 | 20868 | 82 | 0 | 0 | 0 |
| all | 27340 | 14106 | 27248 | 92 | 0 | 0 | 0 | 27248 | 92 | 0 | 0 | 0 | 27248 | 92 | 0 | 0 | 0 |

Knots with u open (KnotInfo chirality; the same range for u_Z, u_R and u_M), with the values left for M:

- 11n_107: u in [-2, -1]; M in {4, 8}
- 12n_296: u in [-2, -1]; M in {4, 8}
- 12n_340: u in [-1, 0]; M in {0, 4}
- 12n_494: u in [-2, -1]; M in {4, 8}
- 12n_550: u in [0, 1]; M in {-4, 0}
- 13n_558: u in [0, 1]; M in {-4, 0}
- 13n_786: u in [-1, 0]; M in {0, 4}
- 13n_1195: u in [-4, -3]; M in {12, 16}
- 13n_1408: u in [0, 1]; M in {-4, 0}
- 13n_1442: u in [-1, 0]; M in {0, 4}
- 13n_1456: u in [-2, -1]; M in {4, 8}
- 13n_1623: u in [0, 1]; M in {-4, 0}
- 13n_1715: u in [-2, -1]; M in {4, 8}
- 13n_1792: u in [-2, -1]; M in {4, 8}
- 13n_1938: u in [-2, -1]; M in {4, 8}
- 13n_2006: u in [0, 1]; M in {-4, 0}
- 13n_2101: u in [-2, -1]; M in {4, 8}
- 13n_2197: u in [-2, -1]; M in {4, 8}
- 13n_2278: u in [0, 1]; M in {-4, 0}
- 13n_2355: u in [-2, -1]; M in {4, 8}
- 13n_2359: u in [-1, 0]; M in {0, 4}
- 13n_2383: u in [0, 1]; M in {-4, 0}
- 13n_2510: u in [-1, 0]; M in {0, 4}
- 13n_2511: u in [-1, 0]; M in {0, 4}
- 13n_2545: u in [-2, -1]; M in {4, 8}
- 13n_2673: u in [-2, -1]; M in {4, 8}
- 13n_2731: u in [-2, -1]; M in {4, 8}
- 13n_2810: u in [-2, -1]; M in {4, 8}
- 13n_2811: u in [-2, -1]; M in {4, 8}
- 13n_2884: u in [1, 2]; M in {-8, -4}
- 13n_2913: u in [-2, -1]; M in {4, 8}
- 13n_2932: u in [-1, 0]; M in {0, 4}
- 13n_2978: u in [2, 3]; M in {-12, -8}
- 13n_3002: u in [-1, 0]; M in {0, 4}
- 13n_3004: u in [-2, -1]; M in {4, 8}
- 13n_3125: u in [0, 1]; M in {-4, 0}
- 13n_3221: u in [0, 1]; M in {-4, 0}
- 13n_3252: u in [-1, 0]; M in {0, 4}
- 13n_3394: u in [-2, -1]; M in {4, 8}
- 13n_3505: u in [0, 1]; M in {-4, 0}
- 13n_3685: u in [-2, -1]; M in {4, 8}
- 13n_4587: u in [-4, -3]; M = 16
- 13n_4639: u in [-3, -2]; M = 12
- 13n_4858: u in [0, 1]; M in {-4, 0}
- 13n_4876: u in [-4, -3]; M in {12, 16}
- 13n_5016: u in [-4, -3]; M in {12, 16}

## Ablation

| withheld | pins M / r_2 / nu / r_0 / tau / upsilon | lost M / r_2 / nu / r_0 / tau / upsilon | of these on knots up to 13 crossings | check |
|---|---|---|---|---|
| I | 16792 / 2 / 0 / 0 / 39716 / 257743 | 291960 / 385 / 37602 / 438 / 356712 / 289271 | 21027 / 247 / 19204 / 242 / 965 / 6029 | 0 |
| unary | 308752 / 387 / 11070 / 358 / 35600 / 481800 | 0 / 0 / 26532 / 80 / 360828 / 65214 | 0 / 0 / 9406 / 66 / 10858 / 242 | 0 |
| cc | 276980 / 377 / 32696 / 424 / 357744 / 540950 | 31772 / 10 / 4906 / 14 / 38684 / 6064 | 2 / 0 / 2964 / 12 / 4598 / 2 | 0 |
| twist | 33908 / 234 / 37602 / 438 / 396428 / 518290 | 274844 / 153 / 0 / 0 / 0 / 28724 | 11814 / 93 / 0 / 0 / 0 / 2 | 0 |
| coincidence | 304496 / 60 / 37560 / 275 / 395318 / 547014 | 4256 / 327 / 42 / 163 / 1110 / 0 | 174 / 213 / 20 / 127 / 194 / 0 | 0 |
| coupling | 308752 / 387 / 37602 / 438 / 396428 / 547014 | 0 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| mutation | 307778 / 387 / 37602 / 438 / 396428 / 547014 | 974 / 0 / 0 / 0 / 0 / 0 | 42 / 0 / 0 / 0 / 0 / 0 | 0 |
| mirror_composite | 118599 / 205 / 29707 / 243 / 307124 / 418846 | 190153 / 182 / 7895 / 195 / 89304 / 128168 | 9997 / 113 / 1844 / 102 / 2853 / 2916 | 0 |
| F11 | 308752 / 387 / 37602 / 438 / 396428 / 547014 | 0 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| F12 | 308660 / 367 / 37602 / 438 / 396428 / 547014 | 92 / 20 / 0 / 0 / 0 / 0 | 12 / 4 / 0 / 0 / 0 / 0 | 0 |
| F13 | 308748 / 383 / 37602 / 438 / 396428 / 547014 | 4 / 4 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| F14 | 308750 / 387 / 37602 / 438 / 396428 / 547014 | 2 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| C11 | 308752 / 387 / 37560 / 396 / 396428 / 547014 | 0 / 0 / 42 / 42 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| C12 | 308752 / 387 / 37600 / 436 / 396428 / 547014 | 0 / 0 / 2 / 2 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| C13 | 308752 / 387 / 37596 / 431 / 396424 / 547014 | 0 / 0 / 6 / 7 / 4 / 0 | 0 / 0 / 0 / 1 / 0 / 0 | 0 |
| C14 | 308752 / 387 / 37602 / 380 / 396428 / 547014 | 0 / 0 / 0 / 58 / 0 / 0 | 0 / 0 / 0 / 20 / 0 / 0 | 0 |
| stage6a (passes tw5) | 308752 / 387 / 37602 / 438 / 396428 / 547014 | 0 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| stage6b (passes tw6) | 308752 / 387 / 37602 / 438 / 396428 / 547014 | 0 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| stage6c (passes tw3x, tw4x, tw5x, tw6x) | 306124 / 381 / 37442 / 434 / 396020 / 546628 | 2628 / 6 / 160 / 4 / 408 / 386 | 126 / 0 / 0 / 0 / 0 / 0 | 0 |
| k4 (passes tw4) | 307191 / 387 / 37571 / 438 / 396241 / 542103 | 1561 / 0 / 31 / 0 / 187 / 4911 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| targeted (passes twB, ccR, twL, g2cc, g2tw) | 212034 / 349 / 30800 / 430 / 295204 / 444556 | 96718 / 38 / 6802 / 8 / 101224 / 102458 | 1502 / 14 / 220 / 6 / 256 / 0 | 0 |
| neighbour_mutations (passes g2mu, g2mv, muR) | 308362 / 387 / 37602 / 438 / 396376 / 546908 | 390 / 0 / 0 / 0 / 52 / 106 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |

Rule rows: the rules of a family (or one rule) are withheld; check = lost pins whose chain in the full run uses no withheld rule (must be 0).  Pass rows: the records of the named passes are withheld and all rules are used; check = pins of that run that are not pins of the full run with the same value (must be 0).

M at the 48 knots of `data/targets/u1_open.txt` (u_Z open on 2026-11-15) with the coincidence family (S1, S2, S3, S4, F10) withheld (scripts/ablate_nodes.py, `checkpoints/final/ablate_nodes_coincidence.json`); the knots with M pinned in the full run:

| knot | M, full run | M, coincidences withheld |
|---|---|---|
| 13n_2911 | 8 | 8 |
| 13n_4524 | -8 | -8 |
| 13n_4587 | 16 | 12, 16 |
| 13n_4639 | 12 | 8, 12 |

The other 44 knots have two values of M in both runs.

## Check set (section 2.6)

`data/check_set.json` is absent: comparison skipped.

## Scope parameters used

```json
{
 "P_cab": 15,
 "family_max_crossings": 15,
 "filling_slope_p": 60,
 "filling_slope_q": 8,
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
- crossing changes: at most 11 crossings: every crossing of all 5 diagrams of every prime knot and of the composites with crossing sum <= 9. 12-13 crossings: every crossing of the KnotInfo PD diagram (pass cc) and of the braid-closure diagram (pass ccb, all 305 shards, stage 5; up to the stage 3 checkpoint only the first 31 shards). Without the records of ccb a re-solve of 2026-11-13 loses 2,282 tau^# pins and 1,318 nu^# pins on knots with at most 13 crossings (2,190 and 1,254 of them at 13 crossings) and no M pin. Torus knots: braid-closure diagrams. Mirror nodes: not recomputed (implied by F3/C3/U4b)
- twists: KnotInfo PD diagrams of prime knots only, both handednesses, in stages (the pass progress in STATE.md says which passes are complete in an export): k = 2 and k = 3 on diagrams with at most 13 crossings (stages 1-3); k = 4 on at most 8 crossings (probe), on 9-11 crossings (stage 4) and on 12-13 crossings (stage 7); k = 5 on at most 11 crossings (stage 6a); k = 6 on at most 10 crossings (stage 6b); |a-b| <= 2 in all of these (specification value). Stage 6c (added 2026-11-12 at the user's request, a widening of the scope parameter): |a-b| > 2 for k = 3, 4 on at most 13 crossings, k = 5 on at most 11 crossings and k = 6 on at most 10 crossings (passes tw3x, tw4x, tw5x, tw6x; 292,045, 90,534, 62,261 and 1,253 twist regions, both handednesses); these records are withheld as a group in the ablation run `stage6c`; the passes of stages 6a (tw5) and 6b (tw6) are likewise withheld in the ablation runs `stage6a` and `stage6b`, because the pass data is copied into a checkpoint as soon as a shard is complete (the stage 4+5 checkpoint already contains the k = 5 shards up to 10 crossings and 5 of the 14 shards on 11 crossings). No twists on braid closures, re-diagrams, composite, torus or cable diagrams. The first run of the tw6 pass (stage 6b) stopped after the shards up to 7 crossings, because the pass runner gave up on shards that take more than 5400 s; the 8 shards of 8-10 crossings (326,916 records) are computed by scripts/queue_6d.sh after the stage 6c passes, and an export contains them only when STATE.md lists 13 tw6 shards Measured weight of k = 4 with |a-b| <= 2 (pass tw4: 9-11 crossings, and stage 7 with 206 of its 305 shards at 12-13 crossings, i.e. all 12-crossing knots and about 60% of the 13-crossing ones): a re-solve of 2026-11-14 without the records of tw4 loses no pin of any invariant on knots with at most 13 crossings; it loses 1,046 M, 140 tau, 1,074 upsilon and 12 nu pins, all on nodes outside the table. Second measurement (2026-11-15, 285 of the 305 stage 7 shards): again no pin of any invariant on knots with at most 13 crossings is lost without tw4; 1,288 M, 138 tau, 1,052 upsilon and 14 nu pins on nodes outside the table are.
- mutations: every diagrammatic Conway circle, three rotations: PD and braid-closure diagrams for at most 11 crossings, PD diagrams for 12-13 crossings; composites with crossing sum <= 9
- slope set: X1/X3 (all nodes): |p| <= 30, q <= 4 (specification), plus integers |p| <= 60 for torus knots and the S3/S4 slopes for cables. Fillings built: |p| <= 30, q <= 4 for every prime knot with at most 13 crossings (up to 2026-11-12, i.e. in the exports up to the stage 6a checkpoint, only q <= 2 at 12 crossings and q = 1 at 13 crossings; the other 1,151,020 fillings were added by scripts/run_fillings.py extend=1); torus slope set for torus knots; none for composites and cables (S3/S4 need no recognition). From 2026-11-13 the fillings of the prime knots up to 13 crossings cover |p| <= 60, q <= 8 (scope parameters filling_slope_p, filling_slope_q; 620 slopes per knot, 8,034,220 records; 5,960,220 added by scripts/run_fillings.py extend=1 p=60 q=8): S1 and F10 hold at any slope, so the search for coincidences is not tied to the slope set of X1/X3, which stays |p| <= 30, q <= 4 (inequalities of X1/X3 at further slopes are implied by those at the integer slopes and add solver time only). Table knots that are torus knots keep the torus slope set
- recognition time limit: 1.5 s per filling (at most 11 crossings), 0.3 s (12 crossings), 0.2 s (13 crossings), 0.5 s for torus-knot fillings (shrunk from 60 s); enforced inside the Regina retriangulation search instead of a subprocess; each node is processed by a worker that is replaced if it crashes or exceeds 25 minutes; 1.5 s for the slopes added on 2026-11-12. The 990 table-knot fillings recorded as unknown were tried again for a geometric solution with 40 randomisations (4 in the first run): 408 are now geometric. A sample of 60 unknown fillings with a 20 s Regina limit recognised no further table-knot filling
- coincidence certificates: candidates are fillings with equal |p| and volume within 1e-8 (2e-7 up to 2026-11-13); on the slope set |p| <= 30, q <= 4 of all prime knots up to 13 crossings: 295,319 fillings in 138,752 clusters; self-coincidences p/q, -p/q of amphichiral knots are skipped because their equations are implied by F5/C5. Certificate: equal verified isometry signatures; the unverified signature is computed first for every candidate of a cluster (hashes in data/filling_usig.jsonl) and the verified one only where unverified signatures agree or are missing (budget choice). State 2026-11-13 07:00: the search on this slope set is complete: every candidate filling has an unverified signature (295,871 hashes, no failure). 138,378 of the clusters consist of knots of one mutation class (classes of the mu pass; mutants have fillings of equal volume at corresponding slopes): no two signatures agree in any of them. The other 374 clusters give 286 hyperbolic coincidences (84 at the same slope, 47 at slopes p/q and -p/q, 155 at different slopes; 253 closed manifolds, 223 knots); with the 42 by name the file has 328 records. History: up to the stage 6a checkpoint the exports had 68 hyperbolic coincidences, found under a time budget on a smaller slope set; the check-in of 2026-11-12 22:12 had 142 (full slope set); 134 more involve fillings whose filled triangulation has no positively oriented solution (see geometric solutions) and 10 more came from the hard retry of failed signatures; the stage 6c checkpoint has all 286. Audit (scripts/audit_coincidences.py, data/coincidence_audit.json): for the 35 prime knots with at most 8 crossings the verified signature of every filling of the slope set was computed with no filter (60 randomisations, Regina with 60 s on the rest); the classes of equal signature are the 25 classes the pipeline has on these knots, no class is split by the volume or the unverified-signature filter, and SnapPy's isometry checker finds no isometric pair among fillings with equal |p|, close volume and different signatures (there is no such pair); 11 fillings stay without geometric solution and without lens or Seifert name (degenerate solutions; Regina names 10 of them as graph manifolds). Lens-space pairs are not written as S1 records: F10 gives both equations on each filling. Further checks (2026-11-12): for 200 random candidates the filling -p/q of the mirror, built from a re-drawn mirror diagram, has the same unverified signature in all 200 cases; for 150 random fillings the volume from such a second triangulation differs by at most 5e-10. Orientation: a coincidence is a homeomorphism of fillings that may reverse orientation (isometry signatures with ignore_orientation, lens and Seifert names normalised up to orientation); candidates are matched on |p|. The mirror identities S_{-p/q}(K*) = -S_{p/q}(K) are not coincidences: fillings exist for one chirality of each knot with slopes of both signs, and mirror nodes are reached through F3/C3. Counting: the 1,059 records written up to the stage 4+5 checkpoint include 922 that name the same torus knot twice at the same slope (T(p,q) and its table name; the solver drops them) and 2 that compare p/q with -p/q on the amphichiral knot 4_1; they form 98 classes of fillings, i.e. 110 independent equations (68 hyperbolic, 42 by name). From 2026-11-12 scripts/find_coincidences.py writes only those. Search-key changes of 2026-11-13 (three engineering agents studied the step; their scripts and tables are in /home/user/mrcalc_scratch/agents): (1) the unverified signature is computed by mrcalc/fastsig.py, the same algorithm and the same string as SnapPy's isometry_signature(verified=False) with a scalar inner loop (0.15 instead of about 0.6 CPU-s per filling; identical strings on 568 fillings, the 25 audit classes and 40 mirror pairs; tests/test_fastsig.py compares it with SnapPy on every test run and must pass after any SnapPy upgrade); (2) the volume tolerance of the candidate clusters is 1e-8 instead of 2e-7 (volumes of two descriptions of one filling agreed to 1e-13 in 340 checked pairs and are recorded to 1e-9): 295,319 candidate fillings in 138,752 clusters, 374 of them outside a single mutation class, the same 328 coincidence records; (3) a failed signature is retried with 40 randomisations and higher precision, and a filling that still has none is compared with its cluster by SnapPy's isometry checker (none left); (4) considered and not used: homology of the covers of degree at most 5 as a further key (removes about a third of the mutation-class fillings at 0.04-0.06 CPU-s each, which no longer pays at 0.15 CPU-s per signature), Chern-Simons (splits no mutation-class cluster and, taken modulo 1/2, separated two certified coincidences), high-precision volume, length spectrum, Turaev-Viro (split nothing or cost as much as the signature). Wider slope set (2026-11-13, |p| <= 60, q <= 8 on the table knots): 1,143,597 candidate fillings in 537,301 clusters; the 1,140 clusters outside a mutation class were tested (1,632 unverified and 115 verified signatures): 345 hyperbolic coincidences, i.e. 59 more, on 35 knots with 4 to 13 crossings (new ones at q = 5, 6 and at |p| between 30 and 50; none at q = 7, 8), all 328 earlier records kept. The 536,161 clusters of one mutation class are not tested at the new slopes (budget choice): on the old slope set none of the 138,378 contained a coincidence, their members sit at corresponding slopes (495,872 at the same slope, 40,289 at p/q and -p/q with one knot a mutant of the other's mirror image) and the F domains of their knots are identical by F6/F3. In a re-solve the 59 new coincidences pin r_0 of 12a_722 and r_2 of 13a_4874 (and mirrors) and change no other node. Nodes outside the table (2026-11-13; beyond the core nodes of section 6, a budget choice): fillings at the 160 slopes |p| <= 30, q <= 4 of the 233,354 census and other hyperbolic knots that a move produced (one per mirror pair, diagram: the result diagram of the move, mrcalc/node_pd.py): 37,336,640 records, 37,336,339 geometric, 299 unknown, 2 Seifert fibred, no lens space. Only the 301 records that are not geometric are in data/fillings (p-nongeo-0000); the geometric ones (volumes, 330 MB) are search data kept outside the repository (it is near the size GitHub recommends as a maximum) and are rebuilt by scripts/run_fillings.py 0 0 nodes=peripheral in about 5 CPU-hours. Candidates over all nodes: 8,133,973 fillings in 3,775,733 clusters; 3,735,948 are of one mutation class or systematic (pairs of nodes sharing at least 10 clusters, the order heuristic for nodes without mutation classes) and are not tested; the other 39,785 were tested (86,024 unverified, 915 verified signatures): 816 hyperbolic coincidences, i.e. 471 more (231 between a table knot and a node outside the table, 240 between two nodes outside the table; 531 such nodes and 164 table knots; in 18 classes a node outside the table ties two or more table knots). Records with a node outside the table name the diagrams in dA, dB (the source move).
- peripheral nodes: a result that is not a core node is instantiated as a node only if it is reached from two distinct nodes or a homogeneous diagram of it was found; other identified results are counted (parameters.json, stats) but not instantiated; unidentified results are discarded. Census names (K14a.., K14n.., K15a.., K15n..) come from the SnapPy census of 14-15 crossing knots (300,265 knots, matched by orientation-sensitive verified isometry signature)
- calculator: KnotInfo PD codes of all table knots; construction diagrams of composites, torus knots and family constructions; cable diagrams with at most 40 crossings (10 s limit); every instantiated peripheral node known when the checkpoint started (60 s limit; 184,868 results, no failures); complexes (milestone 7) only for nodes whose upsilon was not pinned, and for peripheral nodes only if they are Floer-thin or carry the L-space flag (U2)
- identification: Regina solid-torus test only when the Alexander polynomial is trivial; Regina isosig matching of non-hyperbolic results against the pool of torus knots, composites, family constructions and small cables with a bounded retriangulation search
- rule instantiations for peripheral nodes: I1-I3 and the unary rules use the calculator output of the node (genus, fibredness, tau, epsilon, L-space flag, ranks). C8 and U2a are instantiated for census knots whose census name marks them as alternating (K14a.., K15a..), with tau from the calculator; C8 also for nodes with a homogeneous diagram found by a pass; U3 for nodes whose calculator epsilon is 0
- geometric solutions: a filling counts as hyperbolic when SnapPy has a positively oriented solution on a triangulation of it and verify_hyperbolicity succeeds. Triangulations tried: the filled triangulation of the knot exterior under randomisation (4 times in the fillings pass, 40 in the retry of unknown fillings, 10-12 in the signature step), and, from 2026-11-12, when none of these is positively oriented but a solution with volume above 0.5 exists, other surgery descriptions of the same closed manifold (mrcalc/surgery.py redescriptions: a curve of the dual 1-skeleton is drilled, the old cusp is filled for good, the new cusp is filled along its meridian (1,0), which restores the manifold by the SnapPea kernel's convention; convention test "drilled redescription of a filling"; a description is kept only if homology and volume agree). Before that date such fillings were recorded as unknown and could not enter a coincidence: 36 fillings on knots with at most 8 crossings, 406 on all prime knots up to 13 crossings (volumes from 0.98; 129 below 3). 432 table-knot fillings are still unknown.
- targeted search: added 2026-11-13 (agreed with the user): further moves are computed only where they can decide an open M. scripts/targets.py lists, from a solve, the open knots (core nodes whose M is not pinned; all but 6 of the 2,768 at the stage 6b checkpoint have exactly two values left) and their adjacent nodes: the other end N of a crossing-change or twist constraint on an open knot K such that M(N) is open and some value still possible for M(N) would leave one value for M(K) (56,007 nodes at the stage 6b checkpoint: 1,498 table knots, 54,509 census and other hyperbolic knots outside the table). Moves computed: (a) k = 2, 3 twists with every |a-b| on the braid-closure and re-diagrams of the open knots (pass twB; until then twists used the KnotInfo PD diagram only); (b) crossing changes (pass g2cc) and k = 2, 3 twists with every |a-b| (pass g2tw) on a diagram of each adjacent node outside the table (diagram kind g2: the result diagram of the move that first produced the node, scripts/target_diagrams.py). The lists used are kept in data/targets/. Pilot on the 43 open knots with at most 11 crossings and their 160 adjacent nodes outside the table (twB 142,936 records, g2cc 2,438, g2tw 117,334): M is pinned for 17 of the 43, and by propagation for 352 nodes with at most 13 crossings in all (6, 28, 28, 290 at 10, 11, 12, 13 crossings), with 10 r_2, 14 nu, 16 tau and 2 r_0 pins; 1,208 knots (up to mirror) stay open Round 3 (2026-11-15): a second braid-closure diagram (kind braidv0, 1,600 of the 1,905 open knots; 282 words longer than 32 skipped) with crossing changes (ccR) and k = 2, 3 twists (twB), and re-diagrams re4..re6 of the 566 knots with M open. Correction (2026-11-15): the scope parameter k_max['>20'] = 0 (specification value) applied to every twist pass, so the twists of rounds 1-3 ran only on the diagrams with at most 20 crossings: 694 of the 1,600 second braid closures and 5,455 of the 7,506 re-diagrams (all but 5 of the first braid closures have at most 20 crossings); crossing changes ran on all of them. Round 4 (scripts/queue_T4.sh, queued 2026-11-15; budget choices): (0) pass twL: k = 2, 3 twists with every |a-b| on the second braid closures with 21-32 crossings, i.e. k_max['>20'] widened to 3 for this pass only (run_moves.py kbig=3 nmin=21); (1) pass twB4: k = 4 with every |a-b| on the braid0 and braidv0 diagrams (at most 20 crossings) of the knots with M open; (2) pass g2tw: k = 2, 3 twists from the g2 diagram of the 3,000 adjacent nodes outside the table that decide the most M-open knots (scripts/select_adjacent.py; 25,540 such nodes at round 3, of which 7,003 decide at least two open knots); (3) twL on the re-diagrams with more than 20 crossings of the M-open knots; (4) twB4 on their re-diagrams. A light check-in follows each step. Order changed 2026-11-15 after the check-in that contains round 3's moves on the second braid closures (crossing changes on all 1,600, twists on the 694 with at most 20 crossings): no M pin on knots with at most 13 crossings (tau +14, nu +14); step (2) therefore runs first, then (1), (0), (3), (4). Evidence and order of 2026-11-15 12:20 UTC (supersedes the order above): the check-in 15-1103, which adds 9 of the 14 shards of round 3's k = 2, 3 twists on the re-diagrams re4..re6 and further stage 7 shards (285 of 305 in all), pins 58 more M on knots with at most 13 crossings (12 at 12, 46 at 13 crossings); a re-solve of the same data without the pass tw4 (stage 4 and 285 of the 305 stage 7 shards) keeps every pin of every invariant on knots with at most 13 crossings (it loses 1,288 M, 138 tau, 1,052 upsilon and 14 nu pins on nodes outside the table), so the 58 come from the re-diagram twists. Round 4 as queued: twL on the re-diagrams with more than 20 crossings; g2tw on the 3,000 selected adjacent nodes; re-diagrams re7..re9 of the M-open knots with ccR and twB (k = 2, 3, no limit on the diagram's crossings: kbig=3); twB4 on the braid closures; twL on the second braid closures; twB4 on the re-diagrams.
- u_Z and u_R: added 2026-11-15 at the user's request: rules N1-N5 (RULES_U.md, the user's statements verbatim and how each is instantiated). Solved separately from the six invariants by bound propagation on exact intervals (mrcalc/usolve.py, scripts/solve_u.py, checker/check_u.py) over the nodes and the crossing-change and twist edges of the main problem (rule N3) and the band-move passes (rule N4). Anchors: 13,384 alternating table knots (N1a), 40 torus nodes (N1t), 1,006 slice nodes (N2z), 78 nodes of the 39 non-alternating knots KnotInfo lists as quasi-alternating (N1q; no result depends on them). First full solve (checkpoints/u1, before the re-verification of the older passes ended): u_Z and u_R determined for 27,244 of 27,340 nodes with at most 13 crossings (27,194 without rule N4); the other 96 (48 knots, data/targets/u1_open.txt) have two adjacent integers left; the ranges of u_Z and u_R coincide on every node because every band move so far has e = 2 mod 4. Second solve (checkpoints/u2, 2026-11-16 04:23 UTC; with the further diagrams of the 48 knots, the band moves from their neighbours (bm5) and the mutations g2mu, g2mv): 27,248 nodes determined, 46 knots open (data/targets/u2_open.txt; 13n_2911 and 13n_4524 are now determined), checker OK. 2026-11-16 09:25 UTC (checkpoints/u3): rule N1a is also instantiated outside the table (scripts/alt_anchors.py, data/alt_anchors.jsonl.gz): 99,427 census knots K14a.., K15a.. that occur as move results, signature computed from the Seifert matrix of a result diagram (96,908 of these diagrams are alternating, which is then the certificate of alternation; for 2,309 more an alternating diagram was found by simplifying the record diagram and identifying it again (alt_anchors.py certify); the other 210 rest on the census name as rule C8 does; 9,798 knots cross-checked on a second record, no disagreement; checker/check_u.py recomputes the signatures it meets with spherogram's Seifert matrix). The u problem also reads the crossing-change and twist records whose result is such a knot and not a node of the main problem (4,447 instances of N3). Result: 213,157 anchors instead of 14,508, the same 46 knots open, checker OK. 2026-11-16 10:57 UTC (checkpoints/u4, with the face bands bm6 and the passes staged up to 10:38): the same 46 knots open for u_Z, u_R and u_M (data/targets/u4_open.txt), 27,248 of 27,340 nodes determined, checker OK. On all 46 one end of the range is sigma/2; upsilon is pinned on 38 of them and equals sigma/2 there (WANTED_RULES.md 11).
- band moves: rule N4 only (passes bm*, read by scripts/solve_u.py, not by the main problem): mrcalc/pd.py band_smoothing at every crossing of a diagram, checked against an independent construction with spherogram on 693 smoothings. bm1: KnotInfo PD diagrams of all table knots (164,371 records); bm2: first braid closures; bm3: re-diagrams and second braid closures of the targeted search, and the further diagrams of the 48 knots with u open (queue_U2: re-diagrams up to re12, second braid closures up to 60 crossings); bm4 (diagrams of the torus nodes outside the table) was stopped after 2.3 h on its one shard. 523,309 records at the first full solve, 10,940 with an unidentified (non-hyperbolic) result. bm5 (2026-11-16): the g2 diagrams of the neighbours whose u would decide one of the open knots and of the mutants of the M neighbours (36,895 records). bm6 (2026-11-16, scripts/queue_FB.sh): face bands, i.e. rule N4 on the diagram after a Reidemeister II move between two arcs of a face (passes.face_band_records; record field r2 = [face, i, j, over]); convention test on 12 small knots: 1,158 results with both values known by N1a, no violation. On the KnotInfo PD diagrams and first braid closures of the 46 knots with u open: 28,776 records, 20,095 to a knot with known u, none narrows a range; the re-diagrams and second braid closures follow. bm6 complete 10:38 UTC: 366,904 records on all diagrams of the 46 knots (KnotInfo PD, both braid closures, re-diagrams); 219,877 of them go to a knot whose u is determined or anchored and none narrows a range.
- M at the knots with u_Z open: added 2026-11-15 at the user's request (the tools M has and u_Z has not: mutation, surgery coincidences). 46 of the 48 knots with u_Z open also have M open; 13n_4587 and 13n_4639 have M pinned by rule S3. Their 2,434 neighbours whose M would decide one of them (data/targets/m46_adjacent.jsonl, from the round 4 targets; 58 table knots, 924 census knots, 1,452 unnamed hyperbolic knots): fillings at |p| <= 60, q <= 8 of the 2,278 outside the table (one per mirror pair; 888 had none, 1,390 only the narrow slope set), coincidence search over all fillings: 7 more hyperbolic records (865 in all), 3 of them on neighbours of 12n_550 and 13n_2355; pass g2mu: mutations on the neighbours' g2 diagrams (62,217 records, 208 pairs of a neighbour and a mutant that is another knot, 179 neighbours, which could decide 41 of the 46 knots); the result of a mutation of a node is now a node (prepare.py), the 127 mutants without a diagram got one (g2x) with crossing changes, k = 2, 3 twists and fillings; crossing changes and k = 2, 3 twists (every |a-b|, no limit on the diagram's crossings) from the neighbours' diagrams (g2cc, g2tw with only=). Round 4 of the targeted search is paused (flag pause_T4) since 15:59 UTC. State 2026-11-16 08:00 UTC: M is pinned on 4 of the 48 knots: 13n_2911 = 8 and 13n_4524 = -8 (also with rules S1-S4, F10 withheld), 13n_4587 = 16 and 13n_4639 = 12 (not with the surgery rules withheld: two values each remain; scripts/ablate_nodes.py, the user's question of 2026-11-16); 44 have two values left. The fillings of the 127 mutants gave no further coincidence. Twists from the neighbours' diagrams (g2tw): 643 of the 2,278 diagrams done by 06:20 UTC, the remaining shards are slow (large diagrams); twists from the g2u diagrams (neighbours of the u search): 370,452 records, done 07:46 UTC. Checkpoint m46a (solve of 08:10 UTC, mutants of the neighbours as nodes with calculator inputs): still 4 of the 48 pinned. Of the 2,434 neighbours, 704 are pinned (282 census, 422 unnamed), all at a value that decides nothing; 1,730 are open. On each of the 44 knots the two values left for M are -4 times the two values left for u.
- u_M: added 2026-11-16 at the user's request: u_M satisfies the rules of u_Z and is mutation invariant (rule N6, RULES_U.md; instances: the mutation edges of the main problem, 1,399 of them at the solve of checkpoints/u2). Solved next to u_Z and u_R by scripts/solve_u.py (columns uM_lo, uM_hi; events u_events_M, constraints u_constraints_M; checker/check_u.py verifies the variant). Result: the same 46 knots are open for u_M as for u_Z and u_R. Pass muR (mutations on the re-diagrams and braid closures of the 46 knots, 36,462 records): 36,252 results are the knot itself, none is another knot, 210 are unidentified (non-hyperbolic, all from 13n_4587 and 13n_4639).

## Pass progress

- `bm1`: 332 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `bm2`: 332 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `bm3`: 81 shards done, by tier {99: 81}
- `bm4`: 1 shards done, by tier {99: 1}
- `bm5`: 119 shards done, by tier {99: 119}
- `bm6`: 82 shards done, by tier {11: 1, 12: 4, 13: 34, 99: 43}
- `cc`: 358 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 6, 11: 16, 12: 60, 13: 263, 99: 1}
- `ccR`: 81 shards done, by tier {99: 81}
- `ccb`: 305 shards done, by tier {12: 55, 13: 250}
- `g2cc`: 139 shards done, by tier {99: 139}
- `g2mu`: 118 shards done, by tier {99: 118}
- `g2mv`: 47 shards done, by tier {99: 47}
- `g2tw`: 109 shards done, by tier {99: 109}
- `mu`: 357 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 6, 11: 16, 12: 60, 13: 263}
- `muR`: 82 shards done, by tier {11: 1, 12: 4, 13: 34, 99: 43}
- `tw2`: 334 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw3`: 332 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw3x`: 332 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw4`: 332 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw4x`: 332 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw5`: 27 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw5x`: 27 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw6`: 13 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5}
- `tw6x`: 13 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5}
- `twB`: 371 shards done, by tier {9: 1, 10: 3, 11: 10, 12: 45, 13: 231, 99: 81}
- `twL`: 25 shards done, by tier {99: 25}
- `fillings`: 334 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250, 99: 2}

## Tests failed / passes skipped

- Run wound down on 2026-11-16 at the user's decision (a taper by any definition); no pass is running and the pass data are final. The widening round of section 11 was not run as a round of its own: the widenings actually made are listed under scope (twists with |a-b| > 2, further diagrams of open knots and diagrams of adjacent nodes in the targeted search, twists on diagrams with more than 20 crossings in the targeted passes).
- Twists: the specification values k_max 6/5/4 on five diagrams per knot were not run (estimated at about a month). Run on the KnotInfo PD diagram of every prime knot up to 13 crossings: k = 2, 3, 4 with |a-b| <= 2 (tw2, tw3, tw4) and with |a-b| > 2 for k = 3, 4 (tw3x, tw4x); k = 5 up to 11 crossings and k = 6 up to 10 crossings (tw5, tw5x, tw6, tw6x). Twists on other diagrams only in the targeted search: k = 2, 3 on braid closures and re-diagrams of open knots (twB, twL) and on diagrams of selected adjacent nodes (g2tw).
- Crossing changes and mutations: complete on the KnotInfo PD diagrams of prime knots and on the composite diagrams up to crossing sum 13 (cc, mu); crossing changes on the first braid closures of 12-13 crossing knots complete (ccb). Re-diagrams of 12-13 crossing knots exist only for knots with M or u open (targeted search: ccR, twB, bm3, bm6, muR).
- Crossing-change and twist passes on cable diagrams: not run. Twists on torus-knot diagrams: not run. Band moves on torus-knot diagrams (bm4): stopped after 2.3 h on its one shard.
- Targeted search: round 4 was paused on 2026-11-15 15:59 UTC during its first step (twL on re-diagrams with more than 20 crossings: 25 shards done) and not resumed; its further steps were not run. The neighbour twist pass g2tw (diagrams of the nodes whose M would decide one of the knots with u open) was stopped at the wind-down with 18 shards not done (1,139 of its 2,338 diagrams).
- Fillings of composite and cable nodes: not built (cables use S3/S4 only). Coincidence search: complete for the candidate clusters that are not inside one mutation class; clusters inside one mutation class were tested in part only (scope, coincidence certificates).
- Calculator on cable diagrams with more than 40 crossings: not run (g, fibered, tau unknown for those cable nodes; see WANTED_RULES.md #1).
- A filling pass worker crashed inside a native library (segmentation fault in PARI under the Sage-enabled interpreter) during the first tier <= 11 run; the pass was rerun with the plain SnapPy interpreter and a crash-tolerant scheduler; no data from the crashed run were kept for the affected nodes.
- Peripheral nodes received move passes only in the targeted search (g2cc, g2tw, g2mu, g2mv, bm5 on diagrams of selected adjacent nodes).
- u_Z, u_R, u_M (RULES_U.md): 46 knots with 11-13 crossings keep two values; see the section on u and WANTED_RULES.md #11. The search for alternating diagrams of unnamed hyperbolic knots (alt_anchors.py hyp) was not run.
- Tests: the section-3 convention tests passed before every pass and before the final solve. Full suite (conventions, operator soundness and exactness, diagrams, solver, surgery recognition, independent checker, packed layout, u rules, ablation driver): checkpoints/final/tests.txt.

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
- + k = 3 twists on part of the 12-crossing knots, k = 2 twists on 12-13 crossings (first 219 of 305 shards), peripheral nodes without calculator input: 68350 / 84 / 18014 / 309 / 23378 / 147868
- + calculator inputs of 184,868 peripheral nodes with C8/U2a for alternating census knots and U3, 36 further k = 2 shards (this export): 75799 / 84 / 27077 / 309 / 256529 / 275833
- of which on knots with at most 13 crossings: see "Taper tracking" in STATE.md

## Export layout and memory (2026-11-11)

- The export is packed: JSONL files are gzip parts of at most 40 MiB, chain files are members of chains/chains-NNN.tar.xz, knots.csv is continued in knots.N.csv, peripheral nodes are in knots_peripheral[.k].xlsx (FORMAT.md, "Parts and packing"). scripts/export_pack.py unpack restores the literal section-9 file names; the checker and route.py read both layouts.
- No file exceeds 50 MB. Reference tables that grew past the limit (census signatures, calculator outputs of peripheral nodes) are stored as deduplicated parts under data/ref_census and data/hfk_peripheral.
- Memory. With the calculator inputs of the peripheral nodes the problem outgrew the machine (16 GB): the solver needed 6.4 GB, the checker 9.6 GB, and a check-in solve was killed. Constraints, events and move edges are now stored as columns (objects are built when one is read), the node tables are written row by row, the ablation runs are separate processes started after the export, and the checker reads events.jsonl front to back with the constraints in a temporary file. The reworked code was run on a frozen copy of the input of the committed export: all 20 files of the solve and export are byte-identical, the 16 ablation runs give the same counts, and the reworked checker prints the same summary. Peak memory: solve and export 2.2 GB, checker 2.4 GB.
- The rework does not touch operators, rule instantiation or the order of propagation: the work list is processed in the same order as before (fresh constraints in order, then re-queued ones first in, first out).

