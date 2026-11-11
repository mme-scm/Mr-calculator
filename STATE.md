# STATE

Updated 2026-11-11 09:47 UTC.

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

## Pass progress (shards done out of 360; by tier)

- `cc`: 337 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250, 99: 1}
- `mu`: 336 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw2`: 29 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw3`: 22 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 9}
- `fillings`: 334 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250, 99: 2}

## Notes

- milestones 1-7: done at the shrunk scope for all tiers (see REPORT.md): crossing changes, k = 2 twists (and k = 3 from small knots), mutations, fillings, coincidences, cables (S3/S4), coupling, validation, ablation, upsilon
- still running: extra coverage: k = 3 twists for 9-11 crossings, k = 4 probe, composite shards, braid-closure crossing changes for 12-13 crossings, twists on braid closures and re-diagrams, coincidence signatures (budgeted), cable calculator inputs
- remaining-time estimate: about 1.5 hours for the extra coverage and the final re-solve, ablation, export and check
