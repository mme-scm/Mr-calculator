# REPORT

Interim report. Generated 2026-11-12 15:23 UTC from `export/`.

## Nodes by kind

| kind | nodes |
|---|---|
| cable | 2264 |
| census (peripheral) | 368852 |
| composite | 1517 |
| hyp (peripheral) | 96238 |
| table | 25852 |
| torus | 64 |
| unknot | 1 |

Constraints (rule instances): 8349538; move edges: 1277429; events: 5750462.

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
| 11 | 1226 | 1154 | 8 | 868 | 22 | 1178 | 1204 |
| 12 | 4607 | 4207 | 8 | 3261 | 17 | 4323 | 4411 |
| 13 | 20950 | 18632 | 8 | 14406 | 36 | 18994 | 19938 |
| 14 | 10 | 10 | 0 | 2 | 0 | 10 | 10 |
| 15 | 20 | 20 | 0 | 8 | 0 | 20 | 20 |
| constructions | 2328 | 28 | 28 | 124 | 124 | 66 | 150 |
| peripheral | 465090 | 180712 | 4 | 11652 | 48 | 269760 | 414170 |
| total | 494788 | 205304 | 90 | 30752 | 309 | 294896 | 440454 |

## Open domains (projection hull sizes of the unpinned values)

| invariant | <= 2 values | <= 3 values | <= 4 values | <= 5 values | > 5 values | unbounded |
|---|---|---|---|---|---|---|
| M | 260968 | 25388 | 908 | 18 | 616 | 1586 |
| r_2 | 24 | 38 | 22 | 16 | 616 | 493982 |
| nu | 374 | 266560 | 6 | 11396 | 184844 | 856 |
| r_0 | 4 | 14 | 0 | 26 | 1056 | 493379 |
| tau | 14100 | 944 | 26 | 3186 | 180780 | 856 |
| upsilon | 40068 | 8612 | 3174 | 308 | 492 | 1680 |

Sizes are the number of lattice points between the lower and upper end of the projection (M, r_2 on 4Z); the exact finite joint domains are in `export/knots.csv`.

## Ablation

| withheld | pins M / r_2 / nu / r_0 / tau / upsilon | lost M / r_2 / nu / r_0 / tau / upsilon | of these on knots up to 13 crossings | check |
|---|---|---|---|---|
| I | 12219 / 2 / 1 / 0 / 33052 / 242834 | 193085 / 88 / 30751 / 309 / 261844 / 197620 | 19275 / 56 / 18965 / 137 / 781 / 6041 | 0 |
| unary | 205304 / 90 / 10178 / 293 / 14600 / 355542 | 0 / 0 / 20574 / 16 / 280296 / 84912 | 0 / 0 / 9196 / 16 / 10732 / 748 | 0 |
| cc | 204732 / 90 / 28008 / 309 / 290348 / 440370 | 572 / 0 / 2744 / 0 / 4548 / 84 | 0 / 0 / 2744 / 0 / 4168 / 2 | 0 |
| twist | 13202 / 80 / 30752 / 309 / 294896 / 406460 | 192102 / 10 / 0 / 0 / 0 / 33994 | 11652 / 8 / 0 / 0 / 0 / 12 | 0 |
| coincidence | 205290 / 60 / 30738 / 275 / 294896 / 440454 | 14 / 30 / 14 / 34 / 0 / 0 | 4 / 22 / 2 / 22 / 0 / 0 | 0 |
| coupling | 205304 / 90 / 30752 / 309 / 294896 / 440454 | 0 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| mutation | 203732 / 90 / 30752 / 309 / 294896 / 440454 | 1572 / 0 / 0 / 0 / 0 / 0 | 90 / 0 / 0 / 0 / 0 / 0 | 0 |
| mirror_composite | 56045 / 59 / 24701 / 179 / 254279 / 350162 | 149259 / 31 / 6051 / 130 / 40617 / 90292 | 12196 / 18 / 3196 / 50 / 4289 / 4648 | 0 |
| F11 | 205304 / 90 / 30752 / 309 / 294896 / 440454 | 0 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| F12 | 205200 / 70 / 30752 / 309 / 294896 / 440454 | 104 / 20 / 0 / 0 / 0 / 0 | 14 / 4 / 0 / 0 / 0 / 0 | 0 |
| F13 | 205300 / 80 / 30752 / 309 / 294896 / 440454 | 4 / 10 / 0 / 0 / 0 / 0 | 0 / 6 / 0 / 0 / 0 / 0 | 0 |
| F14 | 205302 / 90 / 30752 / 309 / 294896 / 440454 | 2 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| C11 | 205304 / 90 / 30706 / 263 / 294896 / 440454 | 0 / 0 / 46 / 46 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| C12 | 205304 / 90 / 30748 / 305 / 294896 / 440454 | 0 / 0 / 4 / 4 / 0 / 0 | 0 / 0 / 2 / 2 / 0 / 0 | 0 |
| C13 | 205304 / 90 / 30746 / 286 / 294892 / 440454 | 0 / 0 / 6 / 23 / 4 / 0 | 0 / 0 / 0 / 17 / 0 / 0 | 0 |
| C14 | 205304 / 90 / 30750 / 209 / 294896 / 440454 | 0 / 0 / 2 / 100 / 0 / 0 | 0 / 0 / 2 / 62 / 0 / 0 | 0 |
| stage6a (passes tw5) | 205304 / 90 / 30752 / 309 / 294896 / 440454 | 0 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| stage6b (passes tw6) | 205304 / 90 / 30752 / 309 / 294896 / 440454 | 0 / 0 / 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 / 0 / 0 | 0 |
| stage6c (passes tw3x, tw4x, tw5x, tw6x) | 144102 / 86 / 30722 / 309 / 294766 / 440260 | 61202 / 4 / 30 / 0 / 130 / 194 | 3900 / 4 / 0 / 0 / 0 / 0 | 0 |

Rule rows: the rules of a family (or one rule) are withheld; check = lost pins whose chain in the full run uses no withheld rule (must be 0).  Pass rows: the records of the named passes are withheld and all rules are used; check = pins of that run that are not pins of the full run with the same value (must be 0).

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
- twists: KnotInfo PD diagrams of prime knots only, both handednesses, in stages (the pass progress in STATE.md says which passes are complete in an export): k = 2 and k = 3 on diagrams with at most 13 crossings (stages 1-3); k = 4 on at most 8 crossings (probe), on 9-11 crossings (stage 4) and on 12-13 crossings (stage 7); k = 5 on at most 11 crossings (stage 6a); k = 6 on at most 10 crossings (stage 6b); |a-b| <= 2 in all of these (specification value). Stage 6c (added 2026-11-12 at the user's request, a widening of the scope parameter): |a-b| > 2 for k = 3, 4 on at most 13 crossings, k = 5 on at most 11 crossings and k = 6 on at most 10 crossings (passes tw3x, tw4x, tw5x, tw6x; 292,045, 90,534, 62,261 and 1,253 twist regions, both handednesses); these records are withheld as a group in the ablation run `stage6c`; the passes of stages 6a (tw5) and 6b (tw6) are likewise withheld in the ablation runs `stage6a` and `stage6b`, because the pass data is copied into a checkpoint as soon as a shard is complete (the stage 4+5 checkpoint already contains the k = 5 shards up to 10 crossings and 5 of the 14 shards on 11 crossings). No twists on braid closures, re-diagrams, composite, torus or cable diagrams. The first run of the tw6 pass (stage 6b) stopped after the shards up to 7 crossings, because the pass runner gave up on shards that take more than 5400 s; the 8 shards of 8-10 crossings (326,916 records) are computed by scripts/queue_6d.sh after the stage 6c passes, and an export contains them only when STATE.md lists 13 tw6 shards
- mutations: every diagrammatic Conway circle, three rotations: PD and braid-closure diagrams for at most 11 crossings, PD diagrams for 12-13 crossings; composites with crossing sum <= 9
- slope set: X1/X3 (all nodes): |p| <= 30, q <= 4 (specification), plus integers |p| <= 60 for torus knots and the S3/S4 slopes for cables. Fillings actually built: |p| <= 30, q <= 4 for prime knots with at most 11 crossings; |p| <= 30, q <= 2 for 12 crossings; |p| <= 30, q = 1 for 13 crossings; torus slope set for torus knots; none for composites and cables (S3/S4 need no recognition)
- recognition time limit: 1.5 s per filling (at most 11 crossings), 0.3 s (12 crossings), 0.2 s (13 crossings), 0.5 s for torus-knot fillings (shrunk from 60 s); enforced inside the Regina retriangulation search instead of a subprocess; each node is processed by a worker that is replaced if it crashes or exceeds 25 minutes
- coincidence certificates: candidates are fillings with equal |p| and volume within 2e-7 (119,174 fillings in 56,152 clusters); self-coincidences p/q, -p/q of amphichiral knots are skipped because their equations are implied by F5/C5. Up to the stage 4+5 checkpoint the verified isometry signature was computed under a time budget, in priority order (clusters containing a node with pinned r_2 or r_0 first): 3,589 of the candidates (1,777 clusters) were tested, which gave the 68 hyperbolic coincidences of these exports. From 2026-11-12 the step runs without a budget (scripts/find_coincidences.py, logs/coinc3.log) with a prefilter (budget choice): the unverified isometry signature is computed for every candidate (hashes in data/filling_usig.jsonl) and the verified signature only for the fillings of a cluster whose unverified signatures agree or are missing; a certificate still requires equal verified signatures. Orientation: a coincidence is a homeomorphism of fillings that may reverse orientation (isometry signatures with ignore_orientation, lens and Seifert names normalised up to orientation); candidates are matched on |p|. The mirror identities S_{-p/q}(K*) = -S_{p/q}(K) are not coincidences: fillings exist for one chirality of each knot with slopes of both signs, and mirror nodes are reached through F3/C3. Counting: the 1,059 records written up to the stage 4+5 checkpoint include 922 that name the same torus knot twice at the same slope (T(p,q) and its table name; the solver drops them) and 2 that compare p/q with -p/q on the amphichiral knot 4_1; they form 98 classes of fillings, i.e. 110 independent equations (68 hyperbolic, 42 by name). From 2026-11-12 scripts/find_coincidences.py writes only those.
- peripheral nodes: a result that is not a core node is instantiated as a node only if it is reached from two distinct nodes or a homogeneous diagram of it was found; other identified results are counted (parameters.json, stats) but not instantiated; unidentified results are discarded. Census names (K14a.., K14n.., K15a.., K15n..) come from the SnapPy census of 14-15 crossing knots (300,265 knots, matched by orientation-sensitive verified isometry signature)
- calculator: KnotInfo PD codes of all table knots; construction diagrams of composites, torus knots and family constructions; cable diagrams with at most 40 crossings (10 s limit); every instantiated peripheral node known when the checkpoint started (60 s limit; 184,868 results, no failures); complexes (milestone 7) only for nodes whose upsilon was not pinned, and for peripheral nodes only if they are Floer-thin or carry the L-space flag (U2)
- identification: Regina solid-torus test only when the Alexander polynomial is trivial; Regina isosig matching of non-hyperbolic results against the pool of torus knots, composites, family constructions and small cables with a bounded retriangulation search
- rule instantiations for peripheral nodes: I1-I3 and the unary rules use the calculator output of the node (genus, fibredness, tau, epsilon, L-space flag, ranks). C8 and U2a are instantiated for census knots whose census name marks them as alternating (K14a.., K15a..), with tau from the calculator; C8 also for nodes with a homogeneous diagram found by a pass; U3 for nodes whose calculator epsilon is 0

## Pass progress

- `cc`: 358 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 6, 11: 16, 12: 60, 13: 263, 99: 1}
- `ccb`: 305 shards done, by tier {12: 55, 13: 250}
- `mu`: 357 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 6, 11: 16, 12: 60, 13: 263}
- `tw2`: 334 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw3`: 332 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw3x`: 332 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14, 12: 55, 13: 250}
- `tw4`: 27 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw4x`: 27 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw5`: 27 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 2, 10: 5, 11: 14}
- `tw6`: 5 shards done, by tier {3: 1, 4: 1, 5: 1, 6: 1, 7: 1}
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
- Memory. With the calculator inputs of the peripheral nodes the problem outgrew the machine (16 GB): the solver needed 6.4 GB, the checker 9.6 GB, and a check-in solve was killed. Constraints, events and move edges are now stored as columns (objects are built when one is read), the node tables are written row by row, the ablation runs are separate processes started after the export, and the checker reads events.jsonl front to back with the constraints in a temporary file. The reworked code was run on a frozen copy of the input of the committed export: all 20 files of the solve and export are byte-identical, the 16 ablation runs give the same counts, and the reworked checker prints the same summary. Peak memory: solve and export 2.2 GB, checker 2.4 GB.
- The rework does not touch operators, rule instantiation or the order of propagation: the work list is processed in the same order as before (fresh constraints in order, then re-queued ones first in, first out).

