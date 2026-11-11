# REPORT

Interim report. Generated 2026-11-11 16:38 UTC from `export/`.

## Nodes by kind

| kind | nodes |
|---|---|
| cable | 2264 |
| census (peripheral) | 323571 |
| composite | 1517 |
| hyp (peripheral) | 10158 |
| table | 25852 |
| torus | 64 |
| unknot | 1 |

Constraints (rule instances): 5548197; move edges: 681977; events: 3920313.

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
| 13 | 20950 | 12822 | 6 | 13140 | 36 | 16792 | 19804 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 26 | 26 | 124 | 124 | 66 | 150 |
| peripheral | 333729 | 57961 | 4 | 9307 | 48 | 233687 | 249697 |
| total | 363427 | 75799 | 84 | 27077 | 309 | 256529 | 275833 |

## Open domains (projection hull sizes of the unpinned values)

| invariant | <= 2 values | <= 3 values | <= 4 values | <= 5 values | > 5 values | unbounded |
|---|---|---|---|---|---|---|
| M | 241302 | 43416 | 578 | 92 | 654 | 1586 |
| r_2 | 28 | 40 | 22 | 16 | 616 | 362621 |
| nu | 374 | 233688 | 6 | 1088 | 67198 | 33996 |
| r_0 | 4 | 14 | 0 | 26 | 1056 | 362018 |
| tau | 4452 | 1236 | 28 | 1858 | 65328 | 33996 |
| upsilon | 79252 | 5886 | 244 | 24 | 508 | 1680 |

Sizes are the number of lattice points between the lower and upper end of the projection (M, r_2 on 4Z); the exact finite joint domains are in `export/knots.csv`.

## Ablation

| withheld | pins M / r_2 / nu / r_0 / tau / upsilon | lost M / r_2 / nu / r_0 / tau / upsilon | lost pins whose full-run chain lacks the withheld family |
|---|---|---|---|
| I | 10603 / 2 / 1 / 0 / 21109 / 224263 | 65196 / 82 / 27076 / 309 / 235420 / 51570 | 0 |
| unary | 75799 / 84 / 7525 / 293 / 9649 / 186423 | 0 / 0 / 19552 / 16 / 246880 / 89410 | 0 |
| cc | 75343 / 82 / 25655 / 309 / 254645 / 275303 | 456 / 2 / 1422 / 0 / 1884 / 530 | 0 |
| twist | 7973 / 80 / 27077 / 309 / 256529 / 250129 | 67826 / 4 / 0 / 0 / 0 / 25704 | 0 |
| coincidence | 75791 / 60 / 27063 / 275 / 256529 / 275833 | 8 / 24 / 14 / 34 / 0 / 0 | 0 |
| coupling | 75799 / 84 / 27077 / 309 / 256529 / 275833 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| mutation | 75113 / 84 / 27077 / 309 / 256529 / 275833 | 686 / 0 / 0 / 0 / 0 / 0 | 0 |
| mirror_composite | 21223 / 57 / 22288 / 179 / 230026 / 248196 | 54576 / 27 / 4789 / 130 / 26503 / 27637 | 0 |
| F11 | 75799 / 84 / 27077 / 309 / 256529 / 275833 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| F12 | 75715 / 64 / 27077 / 309 / 256529 / 275833 | 84 / 20 / 0 / 0 / 0 / 0 | 0 |
| F13 | 75795 / 74 / 27077 / 309 / 256529 / 275833 | 4 / 10 / 0 / 0 / 0 / 0 | 0 |
| F14 | 75797 / 84 / 27077 / 309 / 256529 / 275833 | 2 / 0 / 0 / 0 / 0 / 0 | 0 |
| C11 | 75799 / 84 / 27031 / 263 / 256529 / 275833 | 0 / 0 / 46 / 46 / 0 / 0 | 0 |
| C12 | 75799 / 84 / 27073 / 305 / 256529 / 275833 | 0 / 0 / 4 / 4 / 0 / 0 | 0 |
| C13 | 75799 / 84 / 27071 / 286 / 256525 / 275833 | 0 / 0 / 6 / 23 / 4 / 0 | 0 |
| C14 | 75799 / 84 / 27075 / 209 / 256529 / 275833 | 0 / 0 / 2 / 100 / 0 / 0 | 0 |

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

- node set: as specified: 12965 table knots and their mirrors, 1517 composite nodes, positive torus knots with pq <= 60 and mirrors, 2268 cable nodes (companions with at most 8 crossings, s in {2,3}, |r| <= P_cab = 15)
- diagrams: at most 11 crossings: KnotInfo PD code, braid closure(s) of KnotInfo braid word(s), 3 seeded re-diagrams (specification value). 12-13 crossings: KnotInfo PD code and braid closure, 0 re-diagrams (shrunk from 3). Torus knots: braid closure and 1 re-diagram
- crossing changes: at most 11 crossings: every crossing of all 5 diagrams of every prime knot and of the composites with crossing sum <= 9. 12-13 crossings: every crossing of the KnotInfo PD diagram (braid-closure diagrams for the first 31 of 305 shards only). Torus knots: braid-closure diagrams. Mirror nodes: not recomputed (implied by F3/C3/U4b)
- twists: k_max shrunk from 6/5/4 to the staged plan on KnotInfo PD diagrams only: k = 2 on every prime knot with at most 13 crossings (12-13 crossings: 255 of 305 shards in this export, the rest follows), k = 3 on every prime knot with at most 11 crossings and on part of the 12-13 crossing knots (see pass progress), k = 4 on prime knots with at most 8 crossings (probe) and the first shards of 9-11 crossings; |a-b| <= 2 and both handednesses throughout; no twists on braid closures, re-diagrams, composite, torus or cable diagrams
- mutations: every diagrammatic Conway circle, three rotations: PD and braid-closure diagrams for at most 11 crossings, PD diagrams for 12-13 crossings; composites with crossing sum <= 9
- slope set: X1/X3 (all nodes): |p| <= 30, q <= 4 (specification), plus integers |p| <= 60 for torus knots and the S3/S4 slopes for cables. Fillings actually built: |p| <= 30, q <= 4 for prime knots with at most 11 crossings; |p| <= 30, q <= 2 for 12 crossings; |p| <= 30, q = 1 for 13 crossings; torus slope set for torus knots; none for composites and cables (S3/S4 need no recognition)
- recognition time limit: 1.5 s per filling (at most 11 crossings), 0.3 s (12 crossings), 0.2 s (13 crossings), 0.5 s for torus-knot fillings (shrunk from 60 s); enforced inside the Regina retriangulation search instead of a subprocess; each node is processed by a worker that is replaced if it crashes or exceeds 25 minutes
- coincidence certificates: candidates are fillings with equal |p| and volume within 2e-7; verification (verify_hyperbolicity) and the verified isometry signature are computed only for candidates, in priority order (clusters containing a node with pinned r_2 or r_0 first) under a time budget; self-coincidences p/q, -p/q of amphichiral knots are skipped because their equations are implied by F5/C5
- peripheral nodes: a result that is not a core node is instantiated as a node only if it is reached from two distinct nodes or a homogeneous diagram of it was found; other identified results are counted (parameters.json, stats) but not instantiated; unidentified results are discarded. Census names (K14a.., K14n.., K15a.., K15n..) come from the SnapPy census of 14-15 crossing knots (300,265 knots, matched by orientation-sensitive verified isometry signature)
- calculator: KnotInfo PD codes of all table knots; construction diagrams of composites, torus knots and family constructions; cable diagrams with at most 40 crossings (10 s limit); every instantiated peripheral node known when the checkpoint started (60 s limit; 184,868 results, no failures); complexes (milestone 7) only for nodes whose upsilon was not pinned, and for peripheral nodes only if they are Floer-thin or carry the L-space flag (U2)
- identification: Regina solid-torus test only when the Alexander polynomial is trivial; Regina isosig matching of non-hyperbolic results against the pool of torus knots, composites, family constructions and small cables with a bounded retriangulation search
- rule instantiations for peripheral nodes: I1-I3 and the unary rules use the calculator output of the node (genus, fibredness, tau, epsilon, L-space flag, ranks). C8 and U2a are instantiated for census knots whose census name marks them as alternating (K14a.., K15a..), with tau from the calculator; C8 also for nodes with a homogeneous diagram found by a pass; U3 for nodes whose calculator epsilon is 0

## Pass progress

- `cc`: 337 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250, 99: 1}
- `mu`: 336 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw2`: 255 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 171}
- `tw3`: 82 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55}
- `tw4`: 6 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1}
- `fillings`: 334 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250, 99: 2}

## Tests failed / passes skipped

- IN PROGRESS, NOT COMPLETE: the taper criterion of section 11 is not yet met and the widening round has not been run. This export is a checkpoint; passes not yet completed are listed below and under "Pass progress".
- Twists: the specification values k_max 6/5/4 on five diagrams per knot were not run (estimated at about a month). Run so far: k = 2 on KnotInfo PD diagrams up to 13 crossings (255 of 305 shards for 12-13 crossings in this export), k = 3 up to 11 crossings and on part of the 12-13 crossing knots, k = 4 up to 8 crossings and the first shards of 9-11. The remaining stages of the agreed plan are running.
- Crossing changes on composite diagrams with crossing sum 10-13: not completed (sum <= 9 done). Mutations on composite diagrams with crossing sum 10-13: not run.
- Crossing changes on braid-closure diagrams of 12-13 crossing knots: 31 of 305 shards. Re-diagrams of 12-13 crossing knots: none.
- Crossing-change and twist passes on cable diagrams: not run. Twists on torus-knot diagrams: not run.
- Fillings of composite and cable nodes: not built (cables use S3/S4 only). Slope set for 12-13 crossing knots reduced as listed under scope.
- Coincidence search: the signature step stopped at its time budget; candidates without a verified signature give no S1 equation (counts in the pass log).
- Calculator on cable diagrams with more than 40 crossings: not run (g, fibered, tau unknown for those cable nodes; see WANTED_RULES.md #1).
- A filling pass worker crashed inside a native library (segmentation fault in PARI under the Sage-enabled interpreter) during the first tier <= 11 run; the pass was rerun with the plain SnapPy interpreter and a crash-tolerant scheduler; no data from the crashed run were kept for the affected nodes.
- Peripheral nodes received no move passes of their own. Peripheral nodes first reached after the calculator run of this checkpoint started have no calculator input yet; they get it at the next full checkpoint.
- Tests: the section-3 convention tests passed before every pass and before this solve. Full suite (conventions, operator soundness and exactness, diagrams, solver, surgery recognition, independent checker, packed layout): see export/tests.txt.

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
- The solver was reworked for memory (slotted constraint/event/edge records, pass records streamed twice instead of held, ablation in forked children without event recording); the events and constraints of the reworked solver were compared byte for byte with those of the previous code on the same input before it was used.

