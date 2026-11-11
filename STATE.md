# STATE

Updated 2026-11-11 11:32 UTC.

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

## Pass progress (shards done out of 360; by tier)

- `cc`: 337 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250, 99: 1}
- `mu`: 336 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw2`: 29 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw3`: 82 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55}
- `tw4`: 6 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}
- `fillings`: 334 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250, 99: 2}

## Notes

- status: checkpoint: all seven milestones have been run for all tiers at a reduced scope; the passes continue at the specification values (Round A: twists up to k_max 6/5/4 on KnotInfo PD diagrams, then braid closures and re-diagrams, composites, cables, then the widening round)
- taper: not reached: widening k from 2 to 3 for knots with at most 11 crossings added about 2600 M pins; the k = 4 probe on the 36 knots with at most 8 crossings added none, which is too small a sample to conclude anything
- remaining-time estimate: Round A (PD diagrams, k up to 6/5/4): about 3 days on this machine; the same on braid closures and three re-diagrams per knot: about 2-3 weeks; cables and the widening round after that
