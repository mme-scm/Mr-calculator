# Export format

All files are UTF-8. JSON lines are written with sorted keys and no spaces.

**Parts and packing.** No file of the export is larger than 50 MB. To keep that limit:

* Each of `knots.jsonl`, `edges.jsonl`, `constraints.jsonl`, `events.jsonl` is stored as parts `X.jsonl`,
  `X.1.jsonl`, `X.2.jsonl`, ...; each part is either plain or gzip-compressed (then it has the further suffix
  `.gz`, e.g. `events.3.jsonl.gz`). The file `X.jsonl` of this document is the concatenation of the
  (decompressed) parts in order. The exporter writes gzip parts and starts a new one at 40 MiB.
* A chain file `chains/<node>.txt` is stored either as that file or as the member named `<node>.txt` of one
  of the archives `chains/chains-NNN.tar.xz` (xz-compressed tar; the exporter writes archives; readers also
  accept `.tar.gz`). No chain file is stored twice.
* `knots.csv` may be continued in `knots.1.csv`, `knots.2.csv`, ...; every part starts with the header line.
* `knots.xlsx` has the sheets `knots`, `pins`, `ablation`, `parameters`; its sheet `knots` has the nodes that
  are not peripheral. The peripheral nodes are in `knots_peripheral.xlsx`, `knots_peripheral.1.xlsx`, ...
  (one sheet `knots`, same columns, 200000 rows per workbook). `knots.csv` has all nodes.

`python3 scripts/export_pack.py unpack export <dir>` writes the plain layout (one `X.jsonl` per file, one
file per chain); `checker/check.py` and `route.py` read both layouts.

## 1. Files

| file | content |
|---|---|
| `knots.jsonl` | one line per node |
| `edges.jsonl` | one line per move edge (deduplicated, with one representative move and both PD codes) |
| `constraints.jsonl` | one line per rule instance |
| `events.jsonl` | one line per narrowing event, in the order in which they happened |
| `chains/<node>.txt` | chains of the pinned values of a node (`*` → `m`, `#` → `+`, `:` and `/` → `_` in file names) |
| `certificates/` | `coincidences.jsonl`, `lens_fillings.jsonl`, `constructions.jsonl`, `certified_L.jsonl` |
| `parameters.json` | scope parameters used, slope sets, software versions |
| `knots.csv`, `knots.xlsx` | tabular export regenerated from `knots.jsonl` |
| `ablation.json`, `summary.json`, `pins_by_tier.json` | validation and counts |

## 2. Domains

Each node carries three domains: `F` (pairs (M, r_2)), `C` (triples (tau, nu, r_0)), `U` (upsilon).
Before the first event every domain is TOP (no information).

### 2.1 RSet (set of integers on the lattice `step`·Z)

JSON `{"v": [explicit values, increasing], "up": u, "dn": d}`; `up`/`dn` are omitted when absent. The set is
`v ∪ {u, u+step, ...} ∪ {d, d-step, ...}`. Canonical form: every explicit value is strictly between `dn` and
`up`; an explicit value adjacent to a ray is absorbed into it (repeat); if the two rays meet or overlap
(`dn + step >= up`) the set is ALL = `{"dn": -step, "up": 0, "v": []}`.

Operations (all keep the canonical form):

* `ge(L)`: keep values `>= L` (a down-ray is replaced by the explicit lattice values in `[L, dn]`).
* `le(H)`: keep values `<= H` (an up-ray is replaced by the explicit lattice values in `[up, H]`).
* `only(S)`: intersection with a finite set `S` (result has no rays).
* `remove(x)`: delete one value; if `x` is on the up-ray, the values `up, ..., x-step` become explicit and
  the ray starts at `x+step` (symmetrically for the down-ray).
* `intersect` (both operands on the same lattice): the set intersection, i.e. the explicit values of either
  operand that are members of the other (rays included), plus the lattice values in `[up_X, dn_Y]` whenever
  the up-ray of one operand and the down-ray of the other overlap; up-ray = max of the two up-rays if both
  have one (else none); down-ray = min of the two if both have one.
* `coarsen(s')` (`s'` a multiple of the step): the members on the lattice `s'`·Z — explicit values divisible
  by `s'`, `up` rounded up and `dn` rounded down to that lattice; the result has step `s'`.
* `min` / `max`: `None` (unbounded) if the corresponding ray exists.

### 2.2 `F` domain (M, r_2)

* box: `{"s": step, "b": [mlo, mhi, rlo, absM]}` — M on the lattice in `[mlo, mhi]` (null = infinite),
  `r_2 >= rlo` (null = unbounded below), and `r_2 >= |M|` when `absM`. TOP is `{"s":1,"b":[null,null,null,false]}`.
* enum: `{"s": step, "e": [[M, RSet], ...]}` sorted by M; entries with an empty RSet are dropped. An empty
  list is the empty domain.
* A box whose `mlo` and `mhi` are both finite is converted at once to enum: every lattice M in the range gets
  the RSet `up = lattice-ceiling(max(rlo, |M| if absM))`, or ALL if there is no lower bound.
* `tighten_m(lo, hi)`: intersect the M-range (box: bounds rounded inwards to the lattice; empty if crossed).
* `restrict_m(S)`: keep only M in the finite set S (a box becomes enum on S ∩ box); members of S that are
  not on the lattice of the domain are ignored. The result is always an enum.

### 2.3 `C` domain (tau, nu, r_0)

* box: `{"b": [tlo, thi, nlo, nhi, c4, r0lo]}`; `c4` true means `|2 tau - nu| <= 1`; `r_0 >= r0lo`
  (null = unbounded below). TOP is `{"b":[null,null,null,null,false,null]}`. With `c4`, bounds are propagated
  on construction: `nlo >= 2 tlo - 1`, `nhi <= 2 thi + 1`, `tlo >= ceil((nlo-1)/2)`, `thi <= floor((nhi+1)/2)`
  (one pass, in this order).
* enum: `{"e": [[tau, nu, RSet(step 1)], ...]}` sorted by (tau, nu); entries with an empty RSet are dropped.
* A box with all four of `tlo, thi, nlo, nhi` finite is converted to enum: all (tau, nu) in the rectangle
  (satisfying C4 if `c4`), each with RSet `up = r0lo` (ALL if null).
* `tighten(tlo, thi, nlo, nhi)`: intersect ranges (enum: filter keys).

### 2.4 `U` domain

`{"u": [lo, hi]}` (null = infinite). Empty when `lo > hi` (not normalised). Every `U` operator intersects the
current interval with the stated one (`lo = max`, `hi = min`).

### 2.5 Digest

`digest(domain)` = first 12 hex digits of SHA-1 of the domain JSON written with sorted keys and separators
`(",", ":")`.

## 3. Records

### 3.1 `knots.jsonl`

`node`, `aliases`, `kind` (unknot, table, composite, torus, cable, census, hyp, construction),
`mirror` (name of the mirror node; equal to `node` when amphichiral), `mirror_flag`, `amphichiral`,
`peripheral`, `tier`, `crossing_number`, `cert` (identification certificate type), `knotinfo` (g4 interval,
signature, tau, genus, fibered, alternating, symmetry_type, u, c4, quasipositive — values of this chirality;
null for non-table nodes), `calculator` (tau, nu, epsilon, genus, fibered, lspace where computed),
`used` (the inputs the rules used: g, g4_upper, fibered, tau, slice, nontrivial, certified_L,
certified_not_L, slopes), `domains` (`F`, `C`, `U` in the encoding above), `pins` (invariant → value),
`pin_events` (invariant → id of the first event after which the projection is a singleton),
`last_events`, `upsilon_unverified`, `chain` (path relative to the export directory, or null).
Invariant names: `M`, `r_2`, `nu`, `r_0`, `tau`, `upsilon`.

"Pinned" means: the domain is a non-empty enum (for `U`: `lo = hi`) and — `M`: exactly one entry;
`tau`, `nu`: all keys have the same tau, resp. nu; `r_2`, `r_0`: no RSet of the domain has a ray and the
union of their explicit values is a single value. A box never pins anything.

`knots.csv` / sheet `knots` of `knots.xlsx`: one row per node; `<inv>_pin` (empty = not pinned), `<inv>_lo`,
`<inv>_hi` are the ends of the projection of the final domain onto the invariant (empty = unbounded; for an
`F` box with `absM` the lower end of r_2 is the least lattice value `>= max(rlo, |M|)` over the M-range);
`M_r2_joint` and `tau_nu_r0_joint` hold the finite joint domain as a JSON list when it has at most 20
elements; an empty cell means unknown.

### 3.2 `edges.jsonl`

`id`, `type` (crossing change | twist | mutation), `key`, `count` (number of moves found with the same key),
`pass`, `source_node`, `source_diagram`, `pd` (source PD code), `source_certificate`, `result_pd`,
`result_node`, `result_certificate`, `writhe_before`, `writhe_after`; re-diagrams add `diagram_seed` and
`diagram_moves`; braid closures add `diagram_word`, `diagram_strands`.
* crossing change: `crossing` (index into `pd`), `sign`, `K_plus`, `K_minus`; key = `[K_plus, K_minus]`.
* twist: `circle_edges` (ordered PD edge labels crossed by the dual-graph path), `edge_directions`
  (+1 left-to-right, -1 right-to-left relative to the path), `a`, `b`, `handedness` (+1 right-handed),
  `insertion`; key = `[source, result, max(a,b), min(a,b), handedness]`.
* mutation: `circle_edges` (four labels in cyclic order), `rotation` (x, y or z); key = sorted pair of nodes.

PD convention: `[a, b, c, d]`, `a` the incoming under edge, counterclockwise; positive crossing iff the over
strand runs d → b. Edge labels 1..2n follow the orientation.

### 3.3 `constraints.jsonl`

`{"id": "c17", "rule": <ID>, "fam": <ablation family>, "dom": "F"|"C"|"U"|"X", "nodes": [...], "par": {...},
"ref": <edge id or certificate object>}`. Parameters and operators are listed in section 4.

### 3.4 `events.jsonl`

`{"id": k, "c": <constraint id>, "rule": <ID>, "node": <node>, "dom": "F"|"C"|"U", "in": [event ids], "dg": digest}`.
`in` lists (sorted increasingly, without duplicates) the latest earlier events of every (node, domain) the
constraint reads (section 4), including the target itself; a domain that has no earlier event is TOP and
contributes no id. `dg` is the digest of the target domain after the event. Ids are consecutive from 0.
The events of one application of a constraint are consecutive, have the same `c` and the same `in`, and
there is at most one per output of the operator; all of them are computed from the domains before the first
of them. (A later application of the same constraint has a different `in`.)

## 4. Operators

A constraint reads the listed domain of each of its nodes (`X` reads `F` and `C` of its single node). Applying
it yields new domains for those (node, domain) pairs; one event is emitted for every pair whose domain
changed (JSON differs), in the order given by the operator's output list (stated below); all events of one
application share the same `in`.

Notation: `cdiv(a,b) = ceil(a/b)`, `fdiv = floor`. `phi2(M;p,q) = |p - qM| + (2 if q = 1 and p = M else 0)`,
`phic(nu;p,q) = |p - q nu|`, `E_2 = q r_2 + phi2`, `E_C = q r_0 + phic`.
"enum only" means: if the domain is a box the operator returns it unchanged.

### 4.1 Unary, domain F

* `F1` — if the domain is TOP: `{"s":4,"b":[null,null,null,true]}`; otherwise unchanged.
* `0_1` (dom F) — `tighten_m(0,0)` then every RSet `only({0})`.
* `F5` — `tighten_m(0,0)`.
* `F8` par `c`, `u` (upper ends, may be null) — `B = 4·min(non-null of c, u)`; `tighten_m(-B, B)`; unchanged if both null.
* `F11` par `p`, `q` — `tighten_m(pq-p-q, -4·ups)` with `ups` = upsilon(T(p,q)) as in rule F11; then
  (enum only) every RSet at M becomes `only({M})`.
* `F12` par `n` — `tighten_m(4n,4n)`, then (enum only) `only({4n})`.
* `F13` par `m`, `tau` — `tighten_m(4tau,4tau)`, then (enum only) `only({4m})`.
* `F14` par `p`, `q` — `tighten_m(v,v)`, `v = 2(p+q-2)`.
* `F15` par `fibered`, `tau`, `g` (each may be null) — enum only. For every M != 0: let
  `ok = fibered and tau = sign(M)·g and 2g <= |M|`. If all three inputs are known and not `ok`, or if
  `fibered` is false: RSet `remove(|M|)`. Otherwise unchanged.
* `F16` par `p`, `q`, `g` — `tighten_m(lo, cdiv(p,q) - 1)` with `lo = 4·cdiv(2g-1, 4)` (`lo` = none if g is null).
* `F10` (dom F) par `p`, `q` — `E_2(K;p/q) ∈ V = {|p|}`:
  box: let `rmin = rlo`, and if `absM`, `rmin = max(rmin or 0, 0)`; if `rmin` is none return unchanged;
  `B = max(V) - q·rmin`; empty if `B < 0`; `tighten_m(cdiv(p-B,q), fdiv(p+B,q))`; if still a box, stop.
  enum: at each M the RSet becomes `only({(v - phi2(M))/q : v ∈ V, divisible})`.

### 4.2 Unary, domain C

* `C1` — if TOP: `{"b":[null,null,null,null,false,0]}`; otherwise unchanged.
* `C4` — box: set `c4` true (bounds propagate as in 2.3); enum: drop keys with `|2 tau - nu| > 1`.
* `0_1` (dom C) — `tighten(0,0,0,0)` then (enum only) every RSet `only({0})`.
* `C5` par `g4` — `tighten(-g4, g4, -nb, nb)`, `nb = max(2 g4 - 1, 0)`; par `why = "amphichiral"` — `tighten(0,0,0,0)`.
* `C8` par `tau` — `tighten(tau, tau, -, -)`.
* `C9` par `n`, `w` — `tighten(cdiv(w-n+1,2), fdiv(w+n-1,2), w-n, w+n)`.
* `C10` par `named` = v — (enum only) every RSet `only({v})`.
  par `ge3`, `a`, `b` (flags) — box: if `ge3`, raise `r0lo` to at least 3; else unchanged. enum: at key
  (tau, nu): if `ge3`: `ge(3)`; if `a`: `remove(3 - |1 - nu|)`; if `b` and `|nu| = 3`: `remove(3)` (in this order).
* `C11` par `g` — `v = 2g-1`; `tighten(nu in [v,v])`, then (enum only) `only({v})`.
* `C12` par `m`, `tau` — `tighten(nu in [tau,tau])`, then (enum only) `only({m})`.
* `C13` par `kind`: `n3m3` → (nu, r_0) = (0, 4); `odd32` with `n` → (2n-1, 6n-1); applied as C11. No other
  kind exists.
* `C14` par `n`, `norm` — nu = 2n-1, r_0 = (norm + 2n - 3)/2 (must be an integer); applied as C11.
* `C15` — enum only; at key (tau, nu) remove every `r_0 >= 0` in `{nu+2} ∪ {2n+2-nu : 1 <= n < nu}`
  (increasing order).
* `F10` (dom C) par `p`, `q` — `E_C ∈ V = {|p|}`: box: if `r0lo` is none unchanged; `B = max(V) - q·r0lo`;
  empty if `B < 0`; `tighten(nu in [cdiv(p-B,q), fdiv(p+B,q)])`; if still a box stop. enum: RSet
  `only({(v - phic(nu))/q : divisible})`.

### 4.3 Unary, domain U

All of them intersect the current interval with the stated one.
* `U4a` par `why` in {slice, amphichiral, unknot} → `[0,0]`; par `g4` → `[-g4, g4]`.
* `U2a` par `tau` → `[-tau,-tau]`. `U3` → `[0,0]`. `U1` par `value` → `[value,value]`.
  `U7` par `p`, `q` → `[ups, ups]`, `ups` = upsilon(T(p,q)).

### 4.4 Coupling `X` (one node; output order F, C)

par: `x1`, `x2`, `x4`, `x5`, `x5m` (flags, absent = false), `x3_g` (genus or absent), `slopes` (an id of
`parameters.json/slope_sets`, or `{"base": id, "extra": [[p,q],...]}` meaning the base list followed by the
extra slopes not already in it).
Both domains must be enum and non-empty, else unchanged. For M in F and nu occurring in C let `Delta(M,nu)`
be the maximum of the following (none if no rule is switched on, or if the only rule switched on is x3 and no
slope qualifies):
* x1: `|M - nu|`, `0`, and `cdiv(phic(nu;p,q) - phi2(M;p,q), q)` for every slope;
* x2: `1`;
* x3_g = g: `cdiv(phic + 2 - phi2, q)` for every slope with `|p| <= (2g-1)·q`;
* x4: `|1-nu| - |1-M| + 1` and `|1+nu| - |1+M| + 1`;
* x5: `M - nu + 2`;  x5m: `nu - M + 2`.
If every Delta is none: unchanged. Let `cmin(nu)` = minimum of r_0 over all keys with that nu (none if
any of them is unbounded below).
* F: at each M, if some `cmin(nu)` or `Delta(M,nu)` is none the RSet is unchanged; else `ge(min over nu of
  (cmin(nu) + Delta(M,nu)))`.
* C: at each key (tau, nu), if for some M the RSet of M is unbounded above or `Delta(M,nu)` is none, unchanged;
  else `le(max over M of (max r_2 at M - Delta(M,nu)))`.
Both new domains are computed from the old ones.

### 4.5 Difference rules (nodes `[A, B]`, bounds `lo <= x(B) - x(A) <= hi`; output order A, B)

* `F7` (x = M, nodes `[K_minus, K_plus]`): `[0, 4]`.  `C7` (x = tau, `[K_minus, K_plus]`): `[0, 1]`.
  `U5` (x = upsilon, nodes `[K_plus, K_minus]`): `[0, 1]`.
* `F9` (x = M, nodes `[K, K']`, par `a`, `b`, `h`): `h > 0`: `[-4ab, (a-b)^2]`; else `[-(a-b)^2, 4ab]`.
* `U6` (x = upsilon, same nodes and par): with `t = a(a-1)/2 + b(b-1)/2`: `h > 0`: `[-t, ab]`; else `[-ab, t]`.
* With par `coef = c` the constraint has one node N (the other end is its mirror image) and means
  `lo <= c·x(N) <= hi`: box: tighten x to `[cdiv(lo,c), fdiv(hi,c)]` if `c > 0`, `[cdiv(hi,c), fdiv(lo,c)]`
  if `c < 0`; enum: keep the values with `lo <= c·x <= hi`.
* Two nodes: first narrow A against B, then B against the new A. "Narrow d against o with x(o) - x(d) in
  [l, h]": if o is enum and empty, d becomes empty; `tighten` x(d) to `[min x(o) - h, max x(o) - l]`
  (a none end of o gives no bound); then, if both are enum, keep the values of x(d) for which some value of
  x(o) lies in `[x + l, x + h]` (for C: keys are kept or dropped by their tau). For B against A use
  `[-h, -l]`. For U (intervals): `A ∩ [B.lo - hi, B.hi - lo]`, then `B ∩ [A.lo + lo, A.hi + hi]`.

### 4.6 Mirror `F3`, `C3`, `U4b` (par kind = mirror); nodes `[A, B]`, output order A, B

`A' = A ∩ mirror(B)`, then `B' = B ∩ mirror(A')`. Mirror: F: M → -M (box: `[-mhi, -mlo]`); C: (tau, nu) →
(-tau, -nu); U: `[-hi, -lo]`. Intersection: enum∩enum key-wise RSet intersection; box∩box component-wise
(`absM`, `c4` are or-ed); enum∩box: keep the keys allowed by the box (for C including `|2 tau - nu| <= 1`
when the box has `c4`) and apply `ge` of the box's lower bound on r (for F: `max(rlo, |M| if absM)`; for C:
`r0lo`). Two `F` domains with different `s` are first restricted to the coarser lattice (the larger `s`,
which the smaller must divide): an enum keeps the entries with M on that lattice and `coarsen`s their RSets,
a box only changes its `s`; the result has the larger `s`.

### 4.7 Mutation `F6`; nodes `[A, B]`

Both become `A ∩ B`.

### 4.8 Connected sum `F4`, `C6`, `U4b` (par kind = sum); nodes `[N, P1(, P2)]`, par `mult`

`x(N) = Σ mult_i x(P_i)` (two different parts with multiplicities `[1, 1]`, or one part with multiplicity
`[2]`; no other shape exists).
Output order N, P1, P2.
* F, all parts enum: `restrict_m(N)` to the attainable sums; then each part keeps the M values that occur in
  a combination whose sum survived in N. If N is still a box after the restriction the parts are unchanged.
  If some part is a box: interval reasoning — `tighten_m(N)` to `[Σ m_i lo_i, Σ m_i hi_i]` (none if any end is
  none); one part: `tighten_m(P)` to `[cdiv(N.lo, m), fdiv(N.hi, m)]`; two parts: `P_i` to
  `[N.lo - hi_j, N.hi - lo_j]` (bounds of the other part before this step, N after).
* C, all parts enum: for every combination of keys let `t = Σ m_i tau_i`, `n = Σ m_i nu_i`. If N is a box it
  is first tightened to `[min t, max t] × [min n - 1, max n + 1]` (if still a box: parts unchanged). N keeps
  the keys `(t, n + d)`, `d ∈ {-1, 0, 1}`, reached by some combination; each part keeps the keys occurring in
  a combination that reached a key of N. If some part is a box: interval reasoning on tau as for F, and
  nu(N) in `[Σ m_i nlo_i - 1, Σ m_i nhi_i + 1]`.
* U: interval reasoning as for F.
* An empty enum part or N makes N empty.

### 4.9 Surgery equations `S1`, `S3`, `S4`; par `sA = [p,q]`, `sB = [p',q']`, `a`, `b`

Meaning `a·E(A; sA) = b·E(B; sB)` on domain F (E_2) or C (E_C). Output order A, B.
* One node (A = B): enum only. At each key with `x` = M (resp. nu): `c = a q - b q'`,
  `rhs = b·phi(x; sB) - a·phi(x; sA)`; if `c = 0`: keep the RSet if `rhs = 0`, else empty; else if `c ∤ rhs`
  empty, else `only({rhs / c})`.
* Two nodes. Box sides first (twice in a row: A then B): if this side is a box and the other is enum with
  every RSet bounded above, let `mx` = max of the other side's factor·E; bound this side by `E <= fdiv(mx,
  own factor)` exactly as in the box step of `F10` (4.1/4.2) with `max(V)` replaced by that number. If a
  side is still a box no further narrowing is done (a box side keeps the bounds obtained in the box step: a
  `C` box without `c4` stays a box with tightened nu). Otherwise, with items `(key, phi, RSet)`:
  the support of side B is the set `vals = {b(q' v + phi') : v explicit}`, the upward progressions
  `(b(q' up + phi'), b q' step)` for every up-ray, and a flag if any down-ray exists.
  Narrowing side A by the support of B: if the flag is set, A is unchanged. Otherwise at each key:
  explicit `v` survives iff `e = a(q v + phi)` is in `vals` or on some progression (`e >= start` and
  `(e - start) mod step = 0`). If the RSet has an up-ray `u`: `cand` = the `v >= u` in the RSet with
  `a(q v + phi) ∈ vals`; if B has no progression the ray is replaced by `cand`; otherwise the ray starts at
  `u' = max(u, lattice-ceiling(cdiv(cdiv(ray_min, a) - phi, q)))` with `ray_min` the smallest progression
  start, and the members of `cand` below `u'` become explicit. A down-ray of A is kept.
  Then B is narrowed in the same way by the support of the new A.

## 5. Replay and chains

Replay the events in order, starting from TOP domains; each event's digest must equal the digest of the
target domain produced by applying its constraint to the current domains, and its `in` must equal the set of
latest events of the domains read.

`chains/<node>.txt` (only for nodes with at least one pin):

```
# chains for <node>
<k>. e<event id> <rule> nodes=<n1,n2,...> par=<json of par, {} if none> -> <node>.<dom>: <statement> | in: <k1,k2,...>
...
== <invariant> = <value> : pinned at <k> ; chain <k1,k2,...>
```

The numbered lines are the union, over the pinned invariants of the node (order `M, r_2, nu, r_0, tau,
upsilon`), of the ancestor closures (through `in`) of the pin events, in increasing event id, numbered from 1;
`in:` lists the numbers of the event's inputs (`-` if none). Each `==` line lists the numbers of the ancestor
closure of that pin event. The file ends with a newline. `<rule>` is the rule of the event, `nodes=` are the
nodes of the constraint (not of the event) joined by commas, `par=` is the JSON of `par` with sorted keys and
no spaces. The statement of any empty domain is `EMPTY`.

Statements (text of the target domain after the event), truncated to `max_statement_text` characters
(see `parameters.json`) followed by `... [digest <dg>]` when longer:
* F box: `M in [<mlo>,<mhi>]; r_2 >= <rlo>` + `, |M|` if absM, with `-inf`/`inf` for none;
  F enum: entries `M=<M>:r_2<RSet>` joined by a space; `EMPTY` if empty.
* C box: `tau in [..,..]; nu in [..,..]` + `; |2tau-nu|<=1` if c4 + `; r_0 >= <r0lo>`;
  C enum: `(tau=<t>,nu=<n>):r_0<RSet>` joined by a space.
* U: `upsilon in [<lo>,<hi>]`.
* RSet: `{` + comma-joined parts + `}` where parts are `<=d` (down-ray), the explicit values, `>=u` (up-ray).
