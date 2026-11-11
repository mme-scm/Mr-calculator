# REPORT

Interim report. Generated 2026-11-11 06:23 UTC from `export/`.

## Nodes by kind

| kind | nodes |
|---|---|
| census (peripheral) | 102 |
| composite | 1517 |
| table | 25852 |
| torus | 64 |
| unknot | 1 |

Constraints (rule instances): 383596; move edges: 9698; events: 334650.

## Pinned values per invariant

| tier | nodes | M | r_2 | nu | r_0 | tau | upsilon |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 5 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 6 | 8 | 6 | 2 | 8 | 5 | 8 | 8 |
| 7 | 16 | 14 | 4 | 12 | 8 | 16 | 16 |
| 8 | 46 | 34 | 4 | 40 | 8 | 46 | 46 |
| 9 | 116 | 80 | 4 | 84 | 14 | 114 | 110 |
| 10 | 363 | 225 | 4 | 279 | 8 | 353 | 333 |
| 11 | 1226 | 712 | 4 | 866 | 22 | 1176 | 1104 |
| 12 | 4607 | 581 | 2 | 2979 | 6 | 3827 | 3087 |
| 13 | 20950 | 1598 | 4 | 11998 | 30 | 15384 | 11598 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 64 | 16 | 16 | 64 | 64 | 64 | 64 |
| peripheral | 102 | 8 | 4 | 48 | 48 | 6 | 0 |
| total | 27536 | 3312 | 56 | 16396 | 221 | 21032 | 16404 |

## Open domains (projection hull sizes of the unpinned values)

| invariant | <= 2 values | <= 3 values | <= 4 values | <= 5 values | > 5 values | unbounded |
|---|---|---|---|---|---|---|
| M | 5370 | 4006 | 56 | 10200 | 4548 | 44 |
| r_2 | 16 | 20 | 12 | 0 | 0 | 27432 |
| nu | 370 | 10436 | 2 | 316 | 16 | 0 |
| r_0 | 0 | 0 | 0 | 0 | 0 | 27315 |
| tau | 3496 | 2992 | 10 | 4 | 2 | 0 |
| upsilon | 2302 | 5862 | 0 | 2056 | 912 | 0 |

Sizes are the number of lattice points between the lower and upper end of the projection (M, r_2 on 4Z); the exact finite joint domains are in `export/knots.csv`.

## Ablation

Not run yet.

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

- `cc`: 31 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14}
- `fillings`: 3 shards done, by tier {4: 1, 6: 1, 8: 1}

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

