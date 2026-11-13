"""Exact linear algebra helpers: signature and Alexander polynomial from a Seifert matrix,
homology rank over F_2."""
from fractions import Fraction


def seifert_matrix(pd):
    import snappy  # noqa: F401  (registers the exterior constructor)
    import spherogram
    L = spherogram.Link([list(c) for c in pd])
    V = L.seifert_matrix()
    return [list(map(int, row)) for row in V]


def _inertia(A):
    """(positive, negative, zero) index of a symmetric rational matrix (exact)."""
    n = len(A)
    A = [[Fraction(x) for x in row] for row in A]
    pos = neg = zero = 0
    active = list(range(n))
    while active:
        # find a nonzero diagonal pivot
        piv = next((i for i in active if A[i][i] != 0), None)
        if piv is None:
            # find nonzero off-diagonal entry and make a diagonal one: replace e_i by e_i + e_j
            found = None
            for i in active:
                for j in active:
                    if i < j and A[i][j] != 0:
                        found = (i, j)
                        break
                if found:
                    break
            if not found:
                zero += len(active)
                break
            i, j = found
            for k in range(n):
                A[i][k] += A[j][k]
            for k in range(n):
                A[k][i] += A[k][j]
            piv = i
        d = A[piv][piv]
        if d > 0:
            pos += 1
        else:
            neg += 1
        active.remove(piv)
        for i in active:
            f = A[i][piv] / d
            if f != 0:
                for k in range(n):
                    A[i][k] -= f * A[piv][k]
                for k in range(n):
                    A[k][i] -= f * A[k][piv]
    return pos, neg, zero


def signature_from_seifert(V):
    """Signature in KnotInfo's convention (right-handed trefoil: -2)."""
    n = len(V)
    if n == 0:
        return 0
    S = [[V[i][j] + V[j][i] for j in range(n)] for i in range(n)]
    p, q, z = _inertia(S)
    return q - p


def signature(pd):
    return signature_from_seifert(seifert_matrix(pd))


def _det_int(M):
    """Bareiss fraction-free determinant of an integer matrix."""
    n = len(M)
    if n == 0:
        return 1
    M = [row[:] for row in M]
    sign = 1
    prev = 1
    for k in range(n - 1):
        if M[k][k] == 0:
            sw = next((i for i in range(k + 1, n) if M[i][k] != 0), None)
            if sw is None:
                return 0
            M[k], M[sw] = M[sw], M[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                M[i][j] = (M[i][j] * M[k][k] - M[i][k] * M[k][j]) // prev
        prev = M[k][k]
    return sign * M[n - 1][n - 1]


_PLAIN_N = 24           # up to this size the plain routine below is used (well under a second)


def _coeffs_charpoly(V):
    """Coefficients c_0..c_n of det(V - t V^T) by exact integer arithmetic of Sage (FLINT), or None when Sage
    is not available or A = V - V^T is not unimodular (it is for a Seifert matrix of a knot).
    With B = A^-1 V (an integer matrix): V - t V^T = (1-t)V + tA = A(tI - (t-1)B), and
    det(tI - (t-1)B) = sum_k chi_k t^k (t-1)^(n-k), chi the characteristic polynomial of B.
    Speed only: the result is the same polynomial as the evaluation and interpolation below
    (tests/test_alg.py compares the two).  SnapPy's Seifert matrices come from a braid word and can be large
    (304 x 304 for a 40-crossing twist result of 10_130, about an hour with the plain routine, 4 s here)."""
    try:
        from sage.all import matrix, ZZ, PolynomialRing
    except Exception:
        return None
    n = len(V)
    Vm = matrix(ZZ, V)
    A = Vm - Vm.transpose()
    dA = A.det()
    if dA not in (1, -1):
        return None
    B = A.solve_right(Vm).change_ring(ZZ)
    if A * B != Vm:
        raise AssertionError('A^-1 V is not exact')
    chi = B.charpoly()
    R = PolynomialRing(ZZ, 't')
    t = R.gen()
    pw = [R(1)]
    for _ in range(n):
        pw.append(pw[-1] * (t - 1))
    f, tk = R(0), R(1)
    for k in range(n + 1):
        f += int(chi[k]) * tk * pw[n - k]
        tk *= t
    f *= int(dA)
    return [int(f[k]) for k in range(n + 1)]


def _coeffs_plain(V):
    """Coefficients c_0..c_n of det(V - t V^T): Bareiss determinants at t = 0..n, Lagrange interpolation."""
    n = len(V)
    pts = list(range(n + 1))
    vals = [_det_int([[V[i][j] - t * V[j][i] for j in range(n)] for i in range(n)]) for t in pts]
    # Lagrange interpolation with Fractions
    coeffs = [Fraction(0)] * (n + 1)
    for i, xi in enumerate(pts):
        num = [Fraction(1)]
        den = Fraction(1)
        for j, xj in enumerate(pts):
            if i == j:
                continue
            num = [Fraction(0)] + num
            for k in range(len(num) - 1):
                num[k] -= xj * num[k + 1]
            den *= (xi - xj)
        for k in range(len(num)):
            coeffs[k] += vals[i] * num[k] / den
    c = [int(x) for x in coeffs]
    assert all(Fraction(a) == b for a, b in zip(c, coeffs))
    return c


def alexander_from_seifert(V, route=None):
    """Coefficients of det(V - t V^T), normalised: symmetric list c_0..c_{2g} with leading
    coefficient positive, trailing zeros stripped.  route: 'plain' or 'charpoly' forces one of the two
    computations (tests); by default small matrices take the plain one and larger ones the fast one when
    it applies."""
    n = len(V)
    if n == 0:
        return [1]
    c = None
    if route == 'charpoly' or (route is None and n > _PLAIN_N):
        c = _coeffs_charpoly(V)
        if c is None and route == 'charpoly':
            raise ValueError('the charpoly route does not apply')
    if c is None:
        c = _coeffs_plain(V)
    while c and c[-1] == 0:
        c.pop()
    while c and c[0] == 0:
        c.pop(0)
    if c and c[-1] < 0:
        c = [-x for x in c]
    return c


def alexander_from_hfk_ranks(ranks):
    """Alexander polynomial from HFK ranks {(A, M): rank}: sum (-1)^M rank t^A, normalised."""
    co = {}
    for (a, m), r in ranks.items():
        co[a] = co.get(a, 0) + (-1) ** (m % 2) * r
    lo, hi = min(co), max(co)
    c = [co.get(a, 0) for a in range(lo, hi + 1)]
    while c and c[-1] == 0:
        c.pop()
    while c and c[0] == 0:
        c.pop(0)
    if c and c[-1] < 0:
        c = [-x for x in c]
    return c


def rank_f2(rows):
    """Rank over F_2 of a list of rows given as Python ints (bitmasks)."""
    rows = [r for r in rows if r]
    rank = 0
    basis = {}
    for r in rows:
        while r:
            h = r.bit_length() - 1
            if h in basis:
                r ^= basis[h]
            else:
                basis[h] = r
                rank += 1
                break
    return rank
