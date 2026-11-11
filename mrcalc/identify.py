"""Identification service (section 4).

Certified identity of a diagram means one of
  (ii)  hyperbolic exterior whose orientation-sensitive isometry signature equals that of a
        verified-hyperbolic reference exterior (table knots: exteriors of KnotInfo's PD
        codes; otherwise the census of 14/15-crossing knots).  Equal signatures mean that
        both exteriors have combinatorially isomorphic oriented triangulations, i.e. an
        orientation-preserving isometry; this fixes the mirror flag.
  (iii) non-hyperbolic exterior whose Regina isomorphism signature (after simplification)
        equals one of a known node's exterior; mirror flag from the sign of tau or sigma,
        else from the HFK Maslov gradings.
  the unknot: Regina certifies the exterior to be a solid torus.
Alexander polynomial and HFK ranks are only used to rule candidates out.
"""
from __future__ import annotations

import json
import os
import random

from . import alg, hfk as H, names, pd as P
from .config import DATA
from .surgery import GEOMETRIC

REF_HYP = os.path.join(DATA, 'ref_hyp.jsonl')
REF_NONHYP = os.path.join(DATA, 'ref_nonhyp.jsonl')
REF_CENSUS = os.path.join(os.environ['MRCALC_STAGE'], 'ref_census.jsonl') if os.environ.get('MRCALC_STAGE') \
    else os.path.join(DATA, 'ref_census.jsonl')


def exterior(pd):
    import snappy  # noqa: F401  (registers the exterior constructor)
    import spherogram
    return spherogram.Link([list(c) for c in pd]).exterior()


def geometric(M, tries=6):
    for _ in range(tries):
        if M.solution_type() == GEOMETRIC:
            return True
        M.randomize()
    return M.solution_type() == GEOMETRIC


def verified(M, tries=6):
    for _ in range(tries):
        if M.solution_type() == GEOMETRIC:
            try:
                if M.verify_hyperbolicity()[0]:
                    return True
            except Exception:
                pass
        M.randomize()
    return False


def oriented_sig(M):
    return M.isometry_signature(ignore_orientation=False)


def mirror_sig(M):
    N = M.copy()
    N.reverse_orientation()
    return N.isometry_signature(ignore_orientation=False)


# ----------------------------------------------------------------------
# Regina side
# ----------------------------------------------------------------------
def regina_tri(M):
    import regina
    return regina.Triangulation3(M._to_string())


def regina_sigs(T, cap=200, height=None, extra=1, visit_cap=4000, exhaustive_below=10):
    """Isomorphism signatures of the simplified triangulation and of the triangulations
    reachable from it by 2-3/3-2 moves within `height` extra tetrahedra, of size at most
    (simplified size + extra), capped at `cap` signatures.  height=None picks a height by
    size (3 up to 5 tetrahedra, 2 up to 9, else 1)."""
    import regina
    T = regina.Triangulation3(T)
    T.intelligentSimplify()
    if T.size() <= exhaustive_below:
        for _ in range(4):
            try:
                if not T.simplifyExhaustive(2, 1):
                    break
            except Exception:
                break
    sigs = [T.isoSig()]
    seen = set(sigs)
    n0 = T.size()
    regina_sigs.last_n0 = n0
    if height is None:
        height = 3 if n0 <= 5 else 2 if n0 <= 9 else 1
    visited = [0]

    def act(sig, tri):
        visited[0] += 1
        if sig not in seen and tri.size() <= n0 + extra:
            seen.add(sig)
            sigs.append(sig)
        return len(seen) >= cap or visited[0] >= visit_cap
    if cap > 1:
        try:
            T.retriangulate(height, 1, act)
        except Exception:
            pass
    return sigs


def is_solid_torus(M):
    T = regina_tri(M)
    T.intelligentSimplify()
    return bool(T.isSolidTorus())


# ----------------------------------------------------------------------
class Identifier:
    def __init__(self, use_census=True):
        self.hyp = {}          # oriented isosig -> (name, mirror)
        self.census = {}       # oriented isosig -> (name, mirror)
        self.census_seen = set()
        self.pool_sig = {}     # regina isosig -> base name
        self.pool_alex = {}    # alexander tuple -> [base names]
        self.pool = {}         # base name -> record
        self.cache = {}
        self.nonhyp_cache = {}
        self.use_census = use_census
        self._load()

    def _load(self):
        if os.path.exists(REF_HYP):
            with open(REF_HYP) as f:
                for line in f:
                    r = json.loads(line)
                    if r.get('sig'):
                        self.hyp[r['sig']] = (r['name'], False)
                        if r['sig_mirror'] != r['sig']:
                            self.hyp[r['sig_mirror']] = (r['name'], True)
        if os.path.exists(REF_CENSUS):
            with open(REF_CENSUS) as f:
                for line in f:
                    r = json.loads(line)
                    self._add_census(r)
        if os.path.exists(REF_NONHYP):
            with open(REF_NONHYP) as f:
                for line in f:
                    r = json.loads(line)
                    if 'isosigs' in r:
                        self.add_pool(r)

    def _add_census(self, r):
        self.census_seen.add(r['name'])
        if r.get('sig'):
            self.census[r['sig']] = (r['name'], False)
            if r['sig_mirror'] != r['sig']:
                self.census[r['sig_mirror']] = (r['name'], True)

    def add_pool(self, r):
        self.pool[r['name']] = r
        for s in r['isosigs']:
            self.pool_sig.setdefault(s, r['name'])
        self.pool_alex.setdefault(tuple(r['alex']), []).append(r['name'])

    # ------------------------------------------------------------------
    def identify(self, pd, want_tau=None):
        key = H.pd_key(pd)
        if key in self.cache:
            return self.cache[key]
        try:
            res = self._identify(pd)
        except BaseException as e:      # cysignals' SignalError is a BaseException
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            res = {'name': None, 'kind': 'unknown', 'cert': {'type': 'none', 'why': 'error: %r' % (e,)}}
        if len(self.cache) > 200000:
            self.cache.clear()
        self.cache[key] = res
        return res

    def _identify(self, pd):
        random.seed(len(pd))
        try:
            M = exterior(pd)
        except Exception as e:
            return {'name': None, 'kind': 'unknown', 'cert': {'type': 'none', 'why': 'exterior failed: %r' % (e,)}}
        if M.num_tetrahedra() == 0:
            return {'name': '0_1', 'kind': 'unknot', 'cert': {'type': 'regina-solid-torus', 'note': 'empty triangulation'}}
        if geometric(M):
            sig = oriented_sig(M)
            hit = self.hyp.get(sig)
            if hit:
                name, mir = hit
                return {'name': names.with_mirror(name, mir), 'kind': 'table',
                        'cert': {'type': 'isometry', 'sig': sig, 'ref': 'knotinfo:' + name, 'mirror': mir}}
            hit = self.census.get(sig)
            if hit is None and self.use_census:
                hit = self._census_lookup(M, sig)
            if hit:
                name, mir = hit
                return {'name': names.with_mirror(name, mir), 'kind': 'census',
                        'cert': {'type': 'isometry', 'sig': sig, 'ref': 'census:' + name, 'mirror': mir}}
            if verified(M):
                sig = oriented_sig(M)
                sm = mirror_sig(M)
                base = min(sig, sm)
                return {'name': names.with_mirror('H:' + base, sig != base), 'kind': 'hyp',
                        'cert': {'type': 'hyp-unidentified', 'sig': sig, 'sig_mirror': sm, 'verified': True,
                                 'amphichiral': sig == sm}}
            return {'name': None, 'kind': 'unknown', 'cert': {'type': 'none', 'why': 'geometric but not verified'}}
        # non-hyperbolic route.  Regina's solid-torus test can be very slow on knot exteriors, so it is
        # only run when the Alexander polynomial does not already rule the unknot out.
        try:
            alex = tuple(alg.alexander_from_seifert(alg.seifert_matrix(pd)))
        except Exception:
            alex = None
        if alex is None or alex == (1,):
            try:
                if is_solid_torus(M):
                    return {'name': '0_1', 'kind': 'unknot', 'cert': {'type': 'regina-solid-torus'}}
            except Exception:
                pass
        return self._nonhyp(pd, M, alex)

    def _census_lookup(self, M, sig):
        import snappy
        try:
            cands = [str(x).split('(')[0] for x in M.identify()]
        except Exception:
            cands = []
        hit = None
        for nm in cands:
            if not (nm.startswith('K14') or nm.startswith('K15')):
                continue
            if nm in self.census_seen:
                continue
            try:
                C = snappy.Manifold(nm)
                if not verified(C):
                    continue
                r = {'name': nm, 'sig': oriented_sig(C), 'sig_mirror': mirror_sig(C), 'verified': True}
            except Exception:
                continue
            self._add_census(r)
            self.new_census = getattr(self, 'new_census', [])
            self.new_census.append(r)
        return self.census.get(sig)

    def _nonhyp(self, pd, M, alex=None):
        if alex is None:
            return {'name': None, 'kind': 'unknown', 'cert': {'type': 'none', 'why': 'seifert matrix failed'}}
        cands = self.pool_alex.get(alex)
        if not cands:
            return {'name': None, 'kind': 'unknown',
                    'cert': {'type': 'none', 'why': 'non-hyperbolic, no candidate with this Alexander polynomial',
                             'alex': list(alex)}}
        base = None
        hitsig = None
        # results of the same kind recur: remember the outcome per (Alexander polynomial, quick isosig)
        try:
            RT = regina_tri(M)
            RT.intelligentSimplify()
            qkey = (alex, RT.isoSig())
        except Exception:
            qkey = None
        if qkey is not None and qkey in self.nonhyp_cache:
            base, hitsig = self.nonhyp_cache[qkey]
            if base is None:
                return {'name': None, 'kind': 'unknown',
                        'cert': {'type': 'none', 'why': 'non-hyperbolic, no isosig match (cached)',
                                 'alex': list(alex)}}
        for cap, height, vc in (((200, None, 1500), (600, 3, 5000)) if base is None else ()):
            try:
                sigs = regina_sigs(regina_tri(M), cap=cap, height=height, visit_cap=vc,
                                   exhaustive_below=8 if cap == 200 else 10)
            except Exception as e:
                return {'name': None, 'kind': 'unknown', 'cert': {'type': 'none', 'why': 'regina failed'}}
            for s in sigs:
                b = self.pool_sig.get(s)
                if b is not None and b in cands:
                    base, hitsig = b, s
                    break
            # the deeper search is only worth its time on small triangulations
            if base is not None or getattr(regina_sigs, 'last_n0', 99) > 6:
                break
        if qkey is not None:
            if len(self.nonhyp_cache) > 50000:
                self.nonhyp_cache.clear()
            self.nonhyp_cache[qkey] = (base, hitsig)
        if base is None:
            return {'name': None, 'kind': 'unknown',
                    'cert': {'type': 'none', 'why': 'non-hyperbolic, no isosig match', 'alex': list(alex),
                             'candidates': cands[:8]}}
        ref = self.pool[base]
        mir, how = self._chirality(pd, ref)
        if mir is None:
            return {'name': None, 'kind': 'unknown',
                    'cert': {'type': 'none', 'why': 'matched %s up to mirror, chirality undetermined' % base,
                             'isosig': hitsig}}
        return {'name': names.with_mirror(base, mir), 'kind': 'nonhyp',
                'cert': {'type': 'regina-isosig', 'isosig': hitsig, 'ref': base, 'mirror': mir,
                         'chirality_by': how}}

    def _chirality(self, pd, ref):
        if ref.get('amphichiral'):
            return False, 'amphichiral'
        if len(pd) > 60:
            return None, None
        r = H.hfk(pd, timeout=60)
        if 'tau' not in r:
            return None, None
        if ref.get('tau'):
            if abs(r['tau']) != abs(ref['tau']):
                return None, None
            return (r['tau'] > 0) != (ref['tau'] > 0), 'tau'
        if r['tau'] != 0:
            return None, None
        if ref.get('sigma'):
            try:
                s = alg.signature(pd)
            except Exception:
                return None, None
            if abs(s) != abs(ref['sigma']):
                return None, None
            return (s > 0) != (ref['sigma'] > 0), 'sigma'
        a, b = ref.get('ranks'), H.mirror_ranks(ref.get('ranks') or [])
        if a is None or a == b:
            return None, None
        if r['ranks'] == a:
            return False, 'hfk'
        if r['ranks'] == b:
            return True, 'hfk'
        return None, None


# ----------------------------------------------------------------------
# reference construction
# ----------------------------------------------------------------------
def build_hyp_reference_one(rec):
    """Reference entry of a table knot: oriented signatures of K and K*."""
    pd = rec['pd']
    M = exterior(pd)
    out = {'name': rec['name'], 'sig': None, 'sig_mirror': None, 'verified': False}
    if verified(M):
        out['sig'] = oriented_sig(M)
        Mm = exterior(P.mirror(pd))
        if not verified(Mm):
            out['sig'] = None
            return out
        out['sig_mirror'] = oriented_sig(Mm)
        out['verified'] = True
        # cross-check: the mirror diagram and the reversed-orientation exterior agree
        out['mirror_check'] = (mirror_sig(M) == out['sig_mirror'])
    return out


def pool_record(name, pd, amphichiral=False, cap=600, height=None):
    """Pool entry (non-hyperbolic known node)."""
    M = exterior(pd)
    sigs = regina_sigs(regina_tri(M), cap=cap, height=height, visit_cap=8000)
    r = H.hfk(pd, timeout=120)
    V = alg.seifert_matrix(pd)
    return {
        'name': name, 'isosigs': sigs, 'alex': alg.alexander_from_seifert(V),
        'sigma': alg.signature_from_seifert(V),
        'tau': r.get('tau'), 'ranks': r.get('ranks'), 'genus': r.get('genus'),
        'amphichiral': amphichiral, 'crossings': len(pd),
    }
