# STATE

Updated 2026-11-12 15:50 UTC.
Pin counts below are from a re-solve on all pass data synced so far (not exported; the last exported and checked checkpoint is described in REPORT.md).


## Pinned values per invariant

| tier | nodes | M | r_2 | nu | r_0 | tau | upsilon |
|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| 4 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 5 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 6 | 8 | 8 | 2 | 8 | 5 | 8 | 8 |
| 7 | 16 | 16 | 4 | 12 | 8 | 16 | 16 |
| 8 | 46 | 46 | 6 | 40 | 13 | 46 | 46 |
| 9 | 116 | 114 | 6 | 84 | 14 | 114 | 116 |
| 10 | 363 | 349 | 8 | 279 | 14 | 353 | 357 |
| 11 | 1226 | 1156 | 8 | 868 | 22 | 1178 | 1204 |
| 12 | 4607 | 4207 | 8 | 3261 | 17 | 4323 | 4411 |
| 13 | 20950 | 18668 | 8 | 14406 | 36 | 18994 | 19938 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 30 | 30 | 124 | 124 | 68 | 150 |
| peripheral | 466534 | 181058 | 4 | 11652 | 48 | 269764 | 414170 |
| total | 496232 | 205690 | 92 | 30752 | 309 | 294902 | 440454 |

## Pass progress (shards done out of 360; by tier)

- `cc`: 358 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 6, 11: 16, 12: 60, 13: 263, 99: 1}
- `ccb`: 305 shards {12: 55, 13: 250}
- `mu`: 357 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 6, 11: 16, 12: 60, 13: 263}
- `tw2`: 334 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw3`: 332 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw3x`: 332 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw4`: 27 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw4x`: 332 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw5`: 27 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw5x`: 27 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw6`: 5 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1}
- `tw6x`: 13 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5}
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
| 2026-11-11 16:37 | tw2 +36 | 17782 | 54 | 17636 | 137 | 22746 | 25956 | +334 / +0 / +0 / +0 / +0 / +50 |
| 2026-11-11 18:29 | tw2 +79, tw3 +12 | 18944 | 54 | 17644 | 137 | 22754 | 26100 | +1162 / +0 / +8 / +0 / +8 / +144 |
| 2026-11-11 20:47 | tw3 +69 | 19032 | 54 | 17644 | 137 | 22754 | 26100 | +88 / +0 / +0 / +0 / +0 / +0 |
| 2026-11-12 00:05 | tw3 +101 | 19780 | 54 | 17644 | 137 | 22754 | 26100 | +748 / +0 / +0 / +0 / +0 / +0 |
| 2026-11-12 05:57 | tw3 +68 | 20632 | 54 | 17644 | 137 | 22754 | 26102 | +852 / +0 / +0 / +0 / +0 / +2 |
| 2026-11-12 06:21 | cc +21, ccb +305, mu +21, tw4 +21, tw5 +15 | 20634 | 54 | 18966 | 137 | 25040 | 26104 | +2 / +0 / +1322 / +0 / +2286 / +2 |
| 2026-11-12 10:26 | tw5 +3 | 20634 | 54 | 18966 | 137 | 25040 | 26104 | +0 / +0 / +0 / +0 / +0 / +0 |
| 2026-11-12 15:23 | tw3x +332, tw4x +27, tw5 +9, tw6 +5 | 24534 | 58 | 18966 | 137 | 25040 | 26104 | +3900 / +4 / +0 / +0 / +0 / +0 |
| 2026-11-12 15:50 | tw4x +305, tw5x +27, tw6x +13 | 24572 | 58 | 18966 | 137 | 25040 | 26104 | +38 / +0 / +0 / +0 / +0 / +0 |

## Notes

- status: checkpoint during stage 2 (k = 2 twists on 12-13 crossings: 255 of 305 shards in this export). Plan agreed with the user (2026-11-11): carry through steps 1-6 (k = 2, 3 on 12-13 crossings; k = 4 on 9-11; braid-closure crossing changes and composites; k = 5 up to 11 and k = 6 up to 10 crossings, all on KnotInfo PD diagrams), then step 7 (k = 4 on 12-13 crossings); the yield of step 7 decides whether the later steps (other diagrams, cables, widening round) are run. Full checkpoints (solve, ablation, export, independent check) follow at the end of stage 3, of stages 4 and 5, of stage 6a, of stage 6b and of stage 7 (scripts/orchestrate.sh); light check-ins (pass data, re-solve, this file) every 3 hours
- taper: definition given by the user (2026-11-11): a notable decrease in new pins on knots with at most 13 crossings; tracked per re-solve in the table above. Not reached so far
- memory: after the storage rework of 2026-11-11 (constraints, events and edges as columns; checker reads events front to back and keeps constraints on disk): solve and export 2.2 GB, independent checker 2.4 GB for 363,427 nodes, 5,548,197 constraints, 3,920,313 events (before: 6.4 GB and 9.6 GB; same output files, compared byte for byte). Container limit 16 GB; the pass workers use about 2.5 GB
