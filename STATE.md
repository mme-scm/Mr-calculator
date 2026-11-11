# STATE

Updated 2026-11-11 06:23 UTC.

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

## Pass progress (shards done out of 360; by tier)

- `cc`: 31 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14}
- `fillings`: 3 shards {4: 1, 6: 1, 8: 1}

## Notes

- milestone 1: done (conventions, identification service, tests, cost estimate)
- milestone 2 (tier <= 11): crossing changes done on KnotInfo PD, braid closure and 3 re-diagrams of every prime knot with at most 11 crossings and of composites with crossing sum <= 9; composite shards s10, s11 pending (queued)
- remaining-time estimate: tier <= 11 fillings ~25 min, coincidences ~10 min, k=2 twists ~35 min, mutations ~5 min; tiers 12-13 ~3 h; cables, upsilon, ablation ~1 h
