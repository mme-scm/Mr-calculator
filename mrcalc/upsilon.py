"""Upsilon at t = 1 from the calculator's UV = 0 complex (rules U1, U2)."""


def _reduce(v, basis):
    """Reduce bitmask v against a basis {leading bit: vector}."""
    while v:
        h = v.bit_length() - 1
        b = basis.get(h)
        if b is None:
            return v
        v ^= b
    return 0


def _insert(v, basis):
    v = _reduce(v, basis)
    if v:
        basis[v.bit_length() - 1] = v
        return True
    return False


def analyse(generators, differentials):
    """generators: [[id, A, M]]; differentials: [[a, b]] (arrow a -> b, coefficient 1).
    Returns {'homology_rank', 'thin', 'upsilon' (U1 value or None), 'arrows_ok'}.
    U1: upsilon = max{d : span{x : M(x) - A(x) >= d} contains a cycle of the total complex that
    is not a boundary}.  The total complex must have homology of rank one."""
    ids = [g[0] for g in generators]
    idx = {g: i for i, g in enumerate(ids)}
    A = {g[0]: g[1] for g in generators}
    M = {g[0]: g[2] for g in generators}
    n = len(ids)
    arrows_ok = True
    D = [0] * n
    for a, b in differentials:
        da = A[b] - A[a]
        if da > 0:
            ok = M[b] - 2 * da == M[a] - 1          # U-arrow
        elif da < 0:
            ok = M[b] == M[a] - 1                   # V-arrow
        else:
            ok = False
        arrows_ok = arrows_ok and ok
        D[idx[a]] ^= 1 << idx[b]
    # image of d
    im = {}
    for i in range(n):
        _insert(D[i], im)
    rank_im = len(im)
    out = {'generators': n, 'arrows_ok': arrows_ok, 'thin': len({M[g] - A[g] for g in ids}) == 1}
    # d^2 = 0 ?
    d2 = True
    for i in range(n):
        v, w = D[i], 0
        while v:
            h = v.bit_length() - 1
            w ^= D[h]
            v ^= 1 << h
        if w:
            d2 = False
            break
    out['d_squared_zero'] = d2
    out['homology_rank'] = (n - rank_im) - rank_im
    out['upsilon'] = None
    if not d2 or out['homology_rank'] != 1 or not arrows_ok:
        return out
    gr = {g: M[g] - A[g] for g in ids}
    for d in sorted(set(gr.values()), reverse=True):
        # kernel of d restricted to span{x : gr(x) >= d}
        pairs = {}       # leading bit of image -> (image, combination)
        found = False
        for g in ids:
            if gr[g] < d:
                continue
            img, comb = D[idx[g]], 1 << idx[g]
            while img:
                h = img.bit_length() - 1
                if h in pairs:
                    img ^= pairs[h][0]
                    comb ^= pairs[h][1]
                else:
                    pairs[h] = (img, comb)
                    break
            if not img:                      # comb is a cycle supported in the subspace
                if _reduce(comb, im):        # not a boundary
                    found = True
                    break
        if found:
            out['upsilon'] = d
            break
    return out


def upsilon_record(h):
    """Apply U1/U2/U3 to a calculator record with complex.  Returns
    {'epsilon', 'upsilon', 'exact', 'why', 'homology_rank'}."""
    a = analyse(h['generators'], h['differentials'])
    rec = {'epsilon': h['epsilon'], 'tau': h['tau'], 'homology_rank': a['homology_rank'],
           'upsilon': a['upsilon'], 'exact': False, 'why': None, 'thin': a['thin'], 'lspace': h['lspace'],
           'arrows_ok': a['arrows_ok'], 'd_squared_zero': a['d_squared_zero']}
    if a['upsilon'] is not None:
        if h['lspace']:
            rec['exact'], rec['why'] = True, 'L-space flag (staircase)'
        elif a['thin']:
            rec['exact'], rec['why'] = True, 'Floer-thin'
            if a['upsilon'] != -h['tau']:
                rec['exact'] = False
                rec['why'] = 'thin but U1 value differs from -tau: not used'
    return rec
