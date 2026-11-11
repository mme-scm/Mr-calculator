# Notes on `export/FORMAT.md`

> Status: every note below has since been folded into `export/FORMAT.md`. Notes 2 and 16 described
> defects of the solver (a lossy ray intersection and undefined mixed lattices); both were fixed in
> `mrcalc/domains.py` / `mrcalc/rules.py` and the checker follows the corrected, documented semantics.

Written while implementing `checker/check.py` from `export/FORMAT.md` (version of the interim export
with 326847 events).  With FORMAT.md plus the points marked **needed** below, the checker reproduces
every digest, `in` list, final domain, pin, pin event, chain file and CSV cell of that export.
The points marked *not exercised* concern operators or situations that do not occur in that export;
there the checker was compared with the solver on random domains (`tests/test_checker.py`,
`test_operators_agree_with_the_solver`) and follows the solver.

Each note says what FORMAT.md says, and what is actually needed.

## A. Wrong or misleading

1. **§4.9, two nodes: "If a side is still a box: both unchanged."**  *(not exercised)*
   Not true for a `C` box without `c4`.  The box step bounds only nu
   (`tighten(nu in [cdiv(p-B,q), fdiv(p+B,q)])`); without `c4` tau stays unbounded, the domain stays a
   box, and the solver returns this tightened box (it is a change and gets an event).  Example:
   `S1`, dom `C`, `sA=[5,1]`, `sB=[7,2]`, `a=b=1`, A = `{"b":[null,null,null,null,false,0]}`,
   B = `{"e":[[1,2,{"v":[3,4]}]]}` gives A = `{"b":[null,null,-6,16,false,0]}`, B unchanged.
   Correct wording: "if a side is still a box, no further narrowing is done; a box side keeps the bounds
   obtained in the box step".  (For `F` the box step always produces an enum or the empty domain, so a
   remaining `F` box is indeed unchanged.)

2. **§2.1 `intersect` is not the set intersection.**  *(wording needed; the lossy case is not exercised)*
   FORMAT.md: "explicit values in both; up-ray = max of the two up-rays if both have one (else none);
   down-ray = min of the two if both have one".
   * "explicit values in both" has to be read as: the explicit values of *either* operand that are
     members of the other operand (rays included).  Reading it as "explicit in both operands" gives
     wrong digests for `F3`/`C3`.
   * With this rule the part where the up-ray of one operand overlaps the down-ray of the other is
     dropped although it belongs to both sets.  Example on step 4: ALL = `{"dn":-4,"up":0,"v":[]}`
     intersected with `{"up":-8,"v":[]}` gives `{"up":0,"v":[]}`; the values -8 and -4 are lost.
     This is what the solver does (`RSet.intersect`), so it is what the checker replays; it makes the
     operation narrower than an intersection.  It can only happen when a down-ray is present, i.e. for
     r-sets that were never bounded below.  The checker counts these intersections and prints a
     WARNING in its summary (`--strict` turns it into a failure).  Count in the current export: 0.

3. **§4.4 "Delta(M,nu) ... (none if no rule is switched on)".**  *(not exercised)*
   Delta is also none when the only rule switched on is x3 and no slope satisfies `|p| <= (2g-1)·q`
   (in particular when `slopes` is absent).  The two clauses "F: ... or Delta(M,nu) is none ..." and
   "C: ..." then apply as written.

4. **§4.3 "→ [0,0]", "→ [-tau,-tau]", "→ [value,value]", "→ [ups,ups]".**  *(clarification)*
   All `U` operators *intersect* the current interval with the stated interval (`lo = max`,
   `hi = min`, no normalisation of an empty result); they do not assign it.  The two readings differ
   only when the current interval does not contain the stated one, i.e. when the result is empty.

5. **§4.8 "If N is still a box after the restriction the parts are unchanged."**
   Cannot happen: `restrict_m` always returns an enum.  Harmless.  The same holds for "if still a box,
   stop" in the `F` case of `F10` (§4.1): after a box step with a bound the domain is an enum or empty.

6. **§1 "each part below 50 MB".**
   Only `events.jsonl`, `constraints.jsonl` and `edges.jsonl` are split by the exporter (at 45 MiB);
   `knots.jsonl` is written in one piece whatever its size.  The checker and `route.py` accept
   continuation parts for every `.jsonl` file.

## B. Incomplete

7. **§2.3 enum of `C`: entries with an empty RSet are dropped**, as stated for `F` in §2.2. *(needed)*

8. **§3.4 `in` is sorted increasingly and has no duplicates.** *(needed: the checker compares lists)*

9. **§3.1 pins.**  *(needed)*  "Projection is a singleton" means: the domain is a non-empty enum
   (or, for `U`, `lo = hi`) and
   * `M`: exactly one entry; `tau`, `nu`: all keys have the same tau, resp. nu;
   * `r_2`, `r_0`: no RSet of the domain has a ray and the union of their explicit values is one value.
   A box never pins anything.  `chain` in `knots.jsonl` is the path relative to the export directory
   (`chains/<file>.txt`), not a bare file name.

10. **§3.3 constraints.**  *(needed)*  `par` and `ref` are omitted when a constraint has none.  `par`
    may contain keys that the operator ignores (`src` of `C5`, `why` of `C8` and `F5`, `n` of `C13`
    with `kind = n3m3`).

11. **§5 how to recognise one application in `events.jsonl`.**  *(needed)*  The events of one
    application are consecutive, have the same `c` and the same `in`, and there is at most one per
    output of the operator; all of them are computed from the domains before the first of them.
    (A later application of the same constraint always has a different `in`, because `in` contains
    the event just emitted.)  The checker groups events by this rule.

12. **§5 chain lines.**  *(needed)*  `par=` is the JSON of `par` with sorted keys and no spaces;
    `nodes=` are the nodes of the constraint (not of the event) joined by commas; `<rule>` is the
    rule of the event.  The statement of an empty `C` enum and of an empty `U` interval is `EMPTY`
    too (only stated for `F`; never reached in an export, since the run stops at an empty domain).

13. **§2.2 `restrict_m(S)`: members of S that are not on the lattice of the domain are ignored.**
    *(not exercised in a way that matters)*

14. **§4.6 enum∩box for `C`: "the keys allowed by the box"** includes `|2 tau - nu| <= 1` when the
    box has `c4`.  *(not exercised)*

15. **`knots.csv` is not described at all.**  *(needed for the CSV round trip)*  The checker uses
    `node`, and for each invariant `<inv>_pin` (empty = not pinned), `<inv>_lo`, `<inv>_hi`
    (ends of the projection of the final domain, empty = unbounded; for an empty domain both empty).
    For an `F` *box* with `absM` the exporter writes `r_2_lo = max(rlo, 0)` (0 if `rlo` is null)
    whatever the M-range is, whereas the least value of the projection is the smallest lattice value
    `>= max(rlo, |M|)` over the M-range.  The two agree whenever 0 is in the M-range (all 44 box
    domains of the current export are `[null,null,null,true]`).  The checker computes the projection;
    if a one-sided box that excludes 0 ever survives to the final state, it will report the cell.

## C. Not defined

16. **Domains on different lattices in one operation.**  *(not exercised; count in the current
    export: 0)*  `F3` and `F6` intersect two `F` domains; FORMAT.md does not say what happens when
    their `s` differ (e.g. a TOP domain, `s = 1`, against an enum with `s = 4`).  The solver gives the
    result the `s` of the first operand while the RSets keep the lattice of the operand they came from,
    which the JSON encoding cannot express (an RSet has no `step`), e.g.
    `{"s":1,"e":[[-8,{"up":8,"v":[]}],...]}` whose RSets are really on 4Z.  The checker gives the
    result the `s` of the first operand, prints a WARNING, and may then disagree with the solver in
    later events.  In the current export every binary rule meets `F` domains of the same `s`, except
    89 applications of `F7` with `0_1` (`s = 1`); difference rules only compare M values, so nothing
    is undefined there.

17. **§4.2 `C13`:** only `kind = n3m3` and `kind = odd32` are defined; the solver treats every other
    kind as `odd32`, the checker reports an error.

18. **§4.8:** more than two parts, or two parts with multiplicities other than `[1, 1]`, are not
    defined (the solver's back-propagation to two parts ignores `mult`); the checker reports an error.
    After a step that makes N empty the results for the parts are irrelevant (no further event).
