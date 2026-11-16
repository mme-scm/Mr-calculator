# Rules for u_Z and u_R

Supplied by the user on 2026-11-15 as an extension of the closed catalogue; used exactly as stated, by
citing the ID. The statements below are the user's; the notes say how each is instantiated.

> I have invariants u_Z and u_R with the following properties.
>
> (1) They all agree with upsilon for torus knots, and sigma/2 for (quasi)alternating knots.
>
> (2) They are additive under connected sum, negate under mirror, and vanish for slice knots.
>
> (3) Let K′ be K with one right-handed full twist along a disc meeting K in a positive and b negative
> points. Let l = a - b and m = min(a,b). Then
> −floor(l²/4)  ≤  f(K′) − f(K)  ≤  m − floor(|l|−1)²/4).
>
> (4) Take a knot diagram D0 of K0 and a crossing c. Smooth c the way that gives a diagram D1 of a knot K1.
> Set e = sign(c) - ( writhe(D1) - writhe(D0) ). Then (e - 2)/4 <= u(K1) - u(K0) <= (e + 2)/4.
>
> (5) u_Z is known to be an integer. u_R is merely known to be real.

| ID | rule | instantiated with |
|---|---|---|
| N1t | u(T(p,q)) = upsilon(T(p,q)) | the torus nodes of the main problem; value by the formula of rule U7 |
| N1a | K alternating: u(K) = sigma(K)/2 | KnotInfo `alternating` = Y and the tabulated signature (section 3 sign: sigma(3_1) = -2). Outside the table (from 2026-11-16, `scripts/alt_anchors.py`, `data/alt_anchors.jsonl.gz`; withheld with `solve_u.py noalt`): alternating by the census name K14a.., K15a.. (as rule C8 of the main problem uses the census table) or by an alternating result diagram of a pass record; the signature is computed exactly from the Seifert matrix of a diagram of the knot (the result diagram of a pass record naming it) and must agree on up to three records |
| N1q | K quasi-alternating: u(K) = sigma(K)/2 | KnotInfo `quasi_alternating` = Y for the 39 non-alternating knots it lists (at most 10 crossings), `data/knotinfo_qa.json`; withheld with `solve_u.py noqa` |
| N2s | u(A # B) = u(A) + u(B) | composite nodes |
| N2m | u(K*) = -u(K); K = K*: u(K) = 0 | mirror pairs; amphichiral nodes |
| N2z | K slice: u(K) = 0 | tabulated smooth four-genus 0 (as rules F5, U4a); the unknot |
| N3 | twist inequality (3) | every crossing-change edge (a = b = 1: K+ -> K- is a right-handed full twist on two oppositely oriented strands) and every twist edge of the main problem, with its a, b and handedness; also the crossing-change and twist records whose result is an alternating knot of N1a that is not a node of the main problem (a result reached from one node only is not a node there) |
| N4 | band inequality (4) | the band-move passes (`data/passes/bm*`): `mrcalc/pd.py band_smoothing` at every crossing of a diagram |
| N5 | u_Z is an integer | the bounds of u_Z are rounded inwards after every step; those of u_R are not |
| N6 | u_M only: mutants have equal u_M | every mutation edge of the main problem (certified mutant pairs, the instances of rule F6); u_M also uses N1-N5 |

u_M was supplied on 2026-11-16:

> I also have an invariant u_M which satisfies all the same rules as u_Z but is also known to be mutation
> invariant.

Reading of (3). The right-hand side is typeset with an unbalanced bracket; it is read as
m - floor((|l|-1)²/4). The other reading, m - (|l|-1)²/4, would give -1/4 as the upper bound for two
parallel strands and so contradict (5) and (1) (a full twist on two parallel strands can join two
unknot diagrams).

Handedness. "Right-handed" is the convention of rule F9 and section 3: a right-handed full twist on two
parallel strands turns the unknot diagram T(2,1) into the right-handed trefoil, whose u is -1 by N1.

Not applied: the rules are not used for upsilon itself (the catalogue's U rules are unchanged).

Method. Bounds only: a domain is an interval with exact rational ends, narrowed by the instantiated
rules until nothing changes (`mrcalc/usolve.py`, `scripts/solve_u.py`). An empty interval is a bug and
stops the run.
