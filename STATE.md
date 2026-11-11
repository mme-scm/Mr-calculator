# STATE

Updated 2026-11-11 15:05 UTC.
Pin counts below are from a re-solve on all pass data synced so far (not exported; the last exported and checked checkpoint is described in REPORT.md).


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
| 9 | 116 | 98 | 6 | 84 | 14 | 114 | 116 |
| 10 | 363 | 297 | 6 | 279 | 14 | 353 | 355 |
| 11 | 1226 | 974 | 8 | 866 | 22 | 1176 | 1204 |
| 12 | 4607 | 3519 | 8 | 3199 | 17 | 4233 | 4399 |
| 13 | 20950 | 12488 | 6 | 13140 | 36 | 16792 | 19754 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 26 | 26 | 124 | 124 | 64 | 150 |
| peripheral | 297786 | 50846 | 4 | 244 | 48 | 538 | 121782 |
| total | 327484 | 68350 | 84 | 18014 | 309 | 23378 | 147868 |

## Pass progress (shards done out of 360; by tier)

- `cc`: 337 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250, 99: 1}
- `mu`: 336 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw2`: 219 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 135}
- `tw3`: 82 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55}
- `tw4`: 6 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}
- `fillings`: 334 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250, 99: 2}

## Taper tracking: pins on knots with at most 13 crossings

Taper = a notable decrease in new pins on knots with at most 13 crossings (prime knots, mirrors and composites of the node set; peripheral knots are not counted). One row per re-solve; the pass column lists the shards added since the previous row.

| time (UTC) | passes added | M | r_2 | nu | r_0 | tau | upsilon | new pins |
|---|---|---|---|---|---|---|---|---|
| 2026-11-11 06:23 | start of tracking | 3258 | 36 | 16274 | 109 | 20932 | 16310 |  |
| 2026-11-11 08:52 | cc +31, fillings +26, mu +31, tw2 +29 | 5560 | 46 | 16434 | 124 | 21136 | 18294 | +2302 / +10 / +160 / +15 / +204 / +1984 |
| 2026-11-11 09:47 | cc +275, fillings +305, mu +305, tw3 +22 | 10234 | 48 | 17584 | 126 | 22688 | 25788 | +4674 / +2 / +1150 / +2 / +1552 / +7494 |
| 2026-11-11 11:32 | tw3 +60, tw4 +6 | 15626 | 54 | 17586 | 137 | 22688 | 25788 | +5392 / +6 / +2 / +11 / +0 / +0 |
| 2026-11-11 13:36 | tw2 +149 | 17042 | 54 | 17634 | 137 | 22742 | 25890 | +1416 / +0 / +48 / +0 / +54 / +102 |
| 2026-11-11 15:04 | tw2 +41 | 17448 | 54 | 17636 | 137 | 22746 | 25906 | +406 / +0 / +2 / +0 / +4 / +16 |

## Notes

- status: checkpoint: all seven milestones have been run for all tiers at a reduced scope; the passes continue at the specification values. Plan agreed with the user (2026-11-11): carry through steps 1-6 (k = 2, 3 on 12-13 crossings; k = 4 on 9-11; braid-closure crossing changes and composites; k = 5 up to 11 and k = 6 up to 10 crossings, all on KnotInfo PD diagrams), then step 7 (k = 4 on 12-13 crossings); the yield of step 7 decides whether the later steps (other diagrams, cables, widening round) are run
- taper: definition given by the user (2026-11-11): a notable decrease in new pins on knots with at most 13 crossings; tracked per re-solve in the table above. Not reached so far
- memory: the solver peaks at 3.8 GB for 327,484 nodes (after the rework of 2026-11-11); estimated 9-10.5 GB when the 14-15 crossing census is saturated (about 630,000 nodes); container limit 16 GB
