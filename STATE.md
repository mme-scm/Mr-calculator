# STATE

Updated 2026-11-13 19:10 UTC.
Pin counts below are from a re-solve on all pass data synced so far (not exported and not checked; the last checked checkpoint is in checkpoints/, the last full export in export/ and REPORT.md).


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
| 10 | 363 | 357 | 42 | 285 | 36 | 355 | 357 |
| 11 | 1226 | 1202 | 38 | 872 | 34 | 1188 | 1204 |
| 12 | 4607 | 4409 | 55 | 3297 | 47 | 4399 | 4411 |
| 13 | 20950 | 19674 | 52 | 14518 | 58 | 19268 | 19938 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 30 | 30 | 124 | 124 | 68 | 150 |
| peripheral | 491264 | 240616 | 96 | 12184 | 70 | 290110 | 417896 |
| total | 520962 | 266510 | 373 | 31444 | 430 | 315612 | 444180 |

## Pass progress (shards done out of 360; by tier)

- `cc`: 358 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 6, 11: 16, 12: 60, 13: 263, 99: 1}
- `ccb`: 305 shards {12: 55, 13: 250}
- `g2cc`: 94 shards {99: 94}
- `g2tw`: 1 shards {99: 1}
- `mu`: 357 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 6, 11: 16, 12: 60, 13: 263}
- `tw2`: 334 shards {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw3`: 332 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw3x`: 332 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw4`: 113 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 31}
- `tw4x`: 332 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw5`: 27 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw5x`: 27 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw6`: 13 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5}
- `tw6x`: 13 shards {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5}
- `twB`: 182 shards {9: 1, 10: 3, 11: 10, 12: 45, 13: 123}
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
| 2026-11-12 19:12 | tw6 +2 | 24572 | 58 | 18966 | 137 | 25040 | 26104 | +0 / +0 / +0 / +0 / +0 / +0 |
| 2026-11-12 22:34 | tw6 +2 | 24572 | 70 | 18966 | 145 | 25040 | 26104 | +0 / +12 / +0 / +8 / +0 / +0 |
| 2026-11-13 06:00 | tw6 +1 | 24572 | 187 | 18974 | 210 | 25042 | 26104 | +0 / +117 / +8 / +65 / +2 / +0 |
| 2026-11-13 11:55 | tw6 +3 | 24572 | 187 | 18974 | 210 | 25042 | 26104 | +0 / +0 / +0 / +0 / +0 / +0 |
| 2026-11-13 12:18 | tw4 +28 | 24572 | 187 | 18974 | 210 | 25042 | 26104 | +0 / +0 / +0 / +0 / +0 / +0 |
| 2026-11-13 15:44 | g2cc +74, g2tw +1, tw4 +37, twB +14 | 24972 | 197 | 19084 | 212 | 25182 | 26104 | +400 / +10 / +110 / +2 / +140 / +0 |
| 2026-11-13 19:10 | g2cc +20, tw4 +21, twB +168 | 25834 | 247 | 19126 | 236 | 25404 | 26104 | +862 / +50 / +42 / +24 / +222 / +0 |

## Notes

- status: 2026-11-13: stages 1-6 are complete (k = 2, 3 on at most 13 crossings; k = 4 on 9-11; braid-closure crossing changes and composites; k = 5 up to 11 and k = 6 up to 10 crossings; stage 6c, twists with |a-b| > 2). Stage 7 (k = 4 on 12-13 crossings, KnotInfo PD diagrams) is running; stage 8 (other diagrams) follows, by the user's decision of 2026-11-13. The surgery-coincidence search is being widened in parallel (more slopes on the table knots, fillings of the nodes outside the table). Light check-ins (pass data, re-solve, this file) every 3 hours
- taper: definition given by the user (2026-11-11): a notable decrease in new pins on knots with at most 13 crossings; tracked per re-solve in the table above. Not reached so far
- memory: after the storage rework of 2026-11-11 (constraints, events and edges as columns; checker reads events front to back and keeps constraints on disk): solve and export 2.2 GB, independent checker 2.4 GB for 363,427 nodes, 5,548,197 constraints, 3,920,313 events (before: 6.4 GB and 9.6 GB; same output files, compared byte for byte). Container limit 16 GB; the pass workers use about 2.5 GB
- checkpoints: from 2026-11-13 (user's decision): a checkpoint is a solve with chains verified by the independent checker, the tests, and the commit of small tables in checkpoints/<label>/ (knots.xlsx with the nodes that are not peripheral, pins_by_tier.json, summary.json, parameters.json, solve.log, check.log, tests.txt). No ablation is run at a checkpoint (run on request with scripts/solve.py; the final export has one) and the packed export is not committed (it added 1.1 GB to the repository at each of the five checkpoints up to stage 6c); export/ and REPORT.md stay those of the stage 6c checkpoint until the final export. The stage 6b checkpoint was finished this way: its ablation was stopped after 9 of 22 runs
