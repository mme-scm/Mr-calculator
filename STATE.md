# STATE

Updated 2026-11-11 08:52 UTC.

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

## Pass progress (shards done out of 360; by tier)

- `cc`: 62 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 31}
- `mu`: 31 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14}
- `tw2`: 29 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14}
- `fillings`: 29 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 99: 2}

## Notes

- milestone 1: done
- tier <= 11, milestones 2-6: done at the shrunk scope: crossing changes (PD, braid closure, 3 re-diagrams), twists k = 2 on KnotInfo PD diagrams, fillings (160 slopes, 1.5 s recognition limit), coincidences (signature step budgeted), mutations (PD and braid closure), coupling, validation, ablation
- tiers 12-13: in progress: crossing changes on KnotInfo PD diagrams; then mutations, fillings (reduced slope set), coincidences, cables, upsilon
- remaining-time estimate: about 3 hours of computation for tiers 12-13, cables, upsilon, final ablation and export
