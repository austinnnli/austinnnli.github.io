"""Tessellate an AP214 STEP B-rep (planes / cylinders / spheres / tori) into a GLB."""
import math, struct, json, sys, os
from collections import defaultdict
from stepparse import load, Ref

TAU = math.pi * 2

# ---------------------------------------------------------------- vec helpers
def sub(a,b): return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def add(a,b): return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def mul(a,s): return (a[0]*s, a[1]*s, a[2]*s)
def dot(a,b): return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]
def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a):
    l = math.sqrt(dot(a,a))
    return (a[0]/l, a[1]/l, a[2]/l) if l > 1e-15 else (0.0,0.0,1.0)
def dist(a,b): return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2+(a[2]-b[2])**2)

class Model:
    def __init__(self, path):
        self.E = load(path)
        self._pt = {}; self._dir = {}; self._a2p = {}
        self.stats = defaultdict(int)

    def e(self, r): return self.E[int(r)]

    # ------------------------------------------------------------ primitives
    def point(self, r):
        r = int(r)
        if r not in self._pt:
            c = self.e(r)[1][1]; self._pt[r] = (float(c[0]), float(c[1]), float(c[2]))
        return self._pt[r]

    def direction(self, r):
        r = int(r)
        if r not in self._dir:
            c = self.e(r)[1][1]; self._dir[r] = norm((float(c[0]), float(c[1]), float(c[2])))
        return self._dir[r]

    def a2p(self, r):
        """AXIS2_PLACEMENT_3D -> (origin, ex, ey, ez)"""
        r = int(r)
        if r in self._a2p: return self._a2p[r]
        _, a = self.e(r)
        o = self.point(a[1])
        ez = self.direction(a[2]) if a[2] is not None else (0.,0.,1.)
        if a[3] is not None:
            ex = self.direction(a[3])
            ex = norm(sub(ex, mul(ez, dot(ex, ez))))
        else:
            t = (1.,0.,0.) if abs(ez[0]) < 0.9 else (0.,1.,0.)
            ex = norm(cross(t, ez))
        ey = cross(ez, ex)
        self._a2p[r] = (o, ex, ey, ez)
        return self._a2p[r]

# ---------------------------------------------------------------- curves
def bspline_eval(deg, ctrl, knots, t):
    n = len(ctrl)
    # find span
    k = deg
    while k < n - 1 and t >= knots[k+1]: k += 1
    d = [ctrl[k-deg+j] for j in range(deg+1)]
    for rr in range(1, deg+1):
        for j in range(deg, rr-1, -1):
            i = k - deg + j
            den = knots[i+deg-rr+1] - knots[i]
            a = 0.0 if den <= 1e-12 else (t - knots[i]) / den
            d[j] = add(mul(d[j-1], 1-a), mul(d[j], a))
    return d[deg]

def bspline_eval4(deg, ctrl, knots, t):
    n = len(ctrl); k = deg
    while k < n - 1 and t >= knots[k+1]: k += 1
    d = [ctrl[k-deg+j] for j in range(deg+1)]
    for rr in range(1, deg+1):
        for j in range(deg, rr-1, -1):
            i = k - deg + j
            den = knots[i+deg-rr+1] - knots[i]
            a = 0.0 if den <= 1e-12 else (t - knots[i]) / den
            p, q = d[j-1], d[j]
            d[j] = (p[0]*(1-a)+q[0]*a, p[1]*(1-a)+q[1]*a, p[2]*(1-a)+q[2]*a, p[3]*(1-a)+q[3]*a)
    return d[deg]

def sample_curve(M, cref, p1, p2, tol, closed_hint=False):
    """Return a list of 3D points from p1 to p2 along the curve (curve natural direction)."""
    typ, a = M.e(cref)
    if typ == 'LINE':
        return [p1, p2]
    if typ == 'CIRCLE':
        o, ex, ey, ez = M.a2p(a[1]); R = float(a[2])
        def ang(p):
            d = sub(p, o); return math.atan2(dot(d, ey), dot(d, ex))
        a1, a2 = ang(p1), ang(p2)
        sweep = a2 - a1
        while sweep <= 1e-9: sweep += TAU          # curve direction = +angle
        if dist(p1, p2) < 1e-9: sweep = TAU
        seg = seg_count(R, sweep, tol)
        return [add(o, add(mul(ex, R*math.cos(a1+sweep*i/seg)), mul(ey, R*math.sin(a1+sweep*i/seg))))
                for i in range(seg+1)]
    if typ == 'ELLIPSE':
        o, ex, ey, ez = M.a2p(a[1]); r1 = float(a[2]); r2 = float(a[3])
        def ang(p):
            d = sub(p, o); return math.atan2(dot(d, ey)/r2, dot(d, ex)/r1)
        a1, a2 = ang(p1), ang(p2)
        sweep = a2 - a1
        while sweep <= 1e-9: sweep += TAU
        if dist(p1, p2) < 1e-9: sweep = TAU
        seg = seg_count(max(r1, r2), sweep, tol)
        return [add(o, add(mul(ex, r1*math.cos(a1+sweep*i/seg)), mul(ey, r2*math.sin(a1+sweep*i/seg))))
                for i in range(seg+1)]
    if typ == 'B_SPLINE_CURVE_WITH_KNOTS':
        deg = int(a[1]); ctrl = [M.point(x) for x in a[2]]
        mult = [int(x) for x in a[6]]; kn = [float(x) for x in a[7]]
        knots = []
        for m_, k_ in zip(mult, kn): knots += [k_]*m_
        t0, t1 = knots[deg], knots[len(ctrl)]
        N = max(16, min(64, len(ctrl)*4))
        pts = [bspline_eval(deg, ctrl, knots, t0 + (t1-t0)*i/N) for i in range(N+1)]
        pts[0], pts[-1] = p1, p2
        return pts
    if typ in ('TRIMMED_CURVE',):
        return sample_curve(M, a[1], p1, p2, tol)
    if typ == '__COMPLEX__':
        parts = {kw: args for kw, args in a}
        if 'B_SPLINE_CURVE' in parts and 'B_SPLINE_CURVE_WITH_KNOTS' in parts:
            bc = parts['B_SPLINE_CURVE']; bk = parts['B_SPLINE_CURVE_WITH_KNOTS']
            deg = int(bc[0]); ctrl = [M.point(x) for x in bc[1]]
            w = [float(x) for x in parts['RATIONAL_B_SPLINE_CURVE'][0]] \
                if 'RATIONAL_B_SPLINE_CURVE' in parts else [1.0]*len(ctrl)
            mult = [int(x) for x in bk[0]]; kn = [float(x) for x in bk[1]]
            knots = []
            for m_, k_ in zip(mult, kn): knots += [k_]*m_
            hp = [(c[0]*wi, c[1]*wi, c[2]*wi, wi) for c, wi in zip(ctrl, w)]
            t0, t1 = knots[deg], knots[len(ctrl)]
            N = max(12, min(48, len(ctrl)*6))
            pts = []
            for i in range(N+1):
                q = bspline_eval4(deg, hp, knots, t0 + (t1-t0)*i/N)
                pts.append((q[0]/q[3], q[1]/q[3], q[2]/q[3]))
            pts[0], pts[-1] = p1, p2
            return pts
    M.stats['curve:'+typ] += 1
    return [p1, p2]

def seg_count(R, sweep, tol):
    if R <= 1e-9: return 1
    c = 1.0 - tol/R
    step = TAU if c <= -1 else 2*math.acos(max(-1.0, min(1.0, c)))
    n = int(math.ceil(abs(sweep)/max(step, 1e-6)))
    full = abs(sweep) / TAU
    return max(int(math.ceil(8*full)) if full > 0.99 else 2, min(n, 64))

# ---------------------------------------------------------------- loops
def edge_points(M, oref, tol):
    """ORIENTED_EDGE -> ordered 3D polyline (excluding final duplicate handled by caller)."""
    _, oa = M.e(oref)
    ec = oa[3]; o_flag = (str(oa[4]) == 'T')
    _, ea = M.e(ec)
    v1, v2, crv, same = ea[1], ea[2], ea[3], (str(ea[4]) == 'T')
    p1 = M.point(M.e(v1)[1][1]); p2 = M.point(M.e(v2)[1][1])
    if same: pts = sample_curve(M, crv, p1, p2, tol)
    else:    pts = list(reversed(sample_curve(M, crv, p2, p1, tol)))
    if not o_flag: pts = list(reversed(pts))
    return pts

def loop_points(M, loop_ref, tol):
    _, la = M.e(loop_ref)
    pts = []
    for oe in la[1]:
        seg = edge_points(M, oe, tol)
        if pts and dist(pts[-1], seg[0]) < 1e-7: seg = seg[1:]
        pts.extend(seg)
    if len(pts) > 1 and dist(pts[0], pts[-1]) < 1e-7: pts.pop()
    return pts

# ---------------------------------------------------------------- surfaces
class Surf:
    """Wraps a STEP surface with forward (uv->xyz) and inverse (xyz->uv) maps."""
    def __init__(self, M, ref):
        typ, a = M.e(ref)
        self.typ = typ
        self.periodic_u = typ in ('CYLINDRICAL_SURFACE','SPHERICAL_SURFACE','TOROIDAL_SURFACE',
                                  'CONICAL_SURFACE','SURFACE_OF_REVOLUTION')
        self.periodic_v = typ == 'TOROIDAL_SURFACE'
        if typ == 'PLANE':
            self.o, self.ex, self.ey, self.ez = M.a2p(a[1])
        elif typ == 'CYLINDRICAL_SURFACE':
            self.o, self.ex, self.ey, self.ez = M.a2p(a[1]); self.R = float(a[2])
        elif typ == 'CONICAL_SURFACE':
            self.o, self.ex, self.ey, self.ez = M.a2p(a[1]); self.R = float(a[2]); self.ha = float(a[3])
        elif typ == 'SPHERICAL_SURFACE':
            self.o, self.ex, self.ey, self.ez = M.a2p(a[1]); self.R = float(a[2])
        elif typ == 'TOROIDAL_SURFACE':
            self.o, self.ex, self.ey, self.ez = M.a2p(a[1]); self.R = float(a[2]); self.r = float(a[3])
        else:
            self.typ = 'PLANE'; self.o=(0,0,0); self.ex=(1,0,0); self.ey=(0,1,0); self.ez=(0,0,1)
            M.stats['surf:'+typ] += 1
    def local(self, p):
        d = sub(p, self.o); return (dot(d,self.ex), dot(d,self.ey), dot(d,self.ez))
    def uv(self, p):
        x,y,z = self.local(p); t = self.typ
        if t == 'PLANE':               return (x, y)
        if t == 'CYLINDRICAL_SURFACE': return (math.atan2(y,x), z)
        if t == 'CONICAL_SURFACE':     return (math.atan2(y,x), z)
        if t == 'SPHERICAL_SURFACE':
            return (math.atan2(y,x), math.atan2(z, math.hypot(x,y)))
        if t == 'TOROIDAL_SURFACE':
            return (math.atan2(y,x), math.atan2(z, math.hypot(x,y) - self.R))
        return (x, y)
    def xyz(self, u, v):
        t = self.typ
        if t == 'PLANE':
            return add(self.o, add(mul(self.ex,u), mul(self.ey,v)))
        if t == 'CYLINDRICAL_SURFACE':
            c,s = math.cos(u), math.sin(u)
            return add(self.o, add(mul(self.ex,self.R*c), add(mul(self.ey,self.R*s), mul(self.ez,v))))
        if t == 'CONICAL_SURFACE':
            rr = self.R + v*math.tan(self.ha); c,s = math.cos(u), math.sin(u)
            return add(self.o, add(mul(self.ex,rr*c), add(mul(self.ey,rr*s), mul(self.ez,v))))
        if t == 'SPHERICAL_SURFACE':
            cv = math.cos(v)
            return add(self.o, add(mul(self.ex,self.R*cv*math.cos(u)),
                       add(mul(self.ey,self.R*cv*math.sin(u)), mul(self.ez,self.R*math.sin(v)))))
        if t == 'TOROIDAL_SURFACE':
            rr = self.R + self.r*math.cos(v)
            return add(self.o, add(mul(self.ex,rr*math.cos(u)),
                       add(mul(self.ey,rr*math.sin(u)), mul(self.ez,self.r*math.sin(v)))))
        return self.o
    def normal(self, u, v):
        t = self.typ
        if t == 'PLANE': return self.ez
        if t in ('CYLINDRICAL_SURFACE','CONICAL_SURFACE'):
            n = add(mul(self.ex,math.cos(u)), mul(self.ey,math.sin(u)))
            if t == 'CONICAL_SURFACE':
                return norm(sub(mul(n, math.cos(self.ha)), mul(self.ez, math.sin(self.ha))))
            return n
        if t == 'SPHERICAL_SURFACE':
            cv = math.cos(v)
            return norm(add(mul(self.ex,cv*math.cos(u)), add(mul(self.ey,cv*math.sin(u)), mul(self.ez,math.sin(v)))))
        if t == 'TOROIDAL_SURFACE':
            cv = math.cos(v)
            return norm(add(mul(self.ex,cv*math.cos(u)), add(mul(self.ey,cv*math.sin(u)), mul(self.ez,math.sin(v)))))
        return self.ez

# ---------------------------------------------------------------- 2D polygon utils
def signed_area(poly):
    s = 0.0
    for i in range(len(poly)):
        x1,y1 = poly[i]; x2,y2 = poly[(i+1) % len(poly)]
        s += x1*y2 - x2*y1
    return s * 0.5

def _tri_area2(a,b,c): return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

def _in_tri(p,a,b,c):
    d1 = _tri_area2(p,a,b); d2 = _tri_area2(p,b,c); d3 = _tri_area2(p,c,a)
    neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)

def earclip(poly):
    """poly: list of (u,v) CCW, simple. Returns list of index triples."""
    n = len(poly)
    if n < 3: return []
    idx = list(range(n))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 4*n + 60:
        guard += 1
        done = False
        m = len(idx)
        for k in range(m):
            i0, i1, i2 = idx[(k-1) % m], idx[k], idx[(k+1) % m]
            a,b,c = poly[i0], poly[i1], poly[i2]
            if _tri_area2(a,b,c) <= 1e-16: continue
            ok = True
            for j in idx:
                if j in (i0,i1,i2): continue
                if _in_tri(poly[j], a, b, c): ok = False; break
            if ok:
                tris.append((i0,i1,i2)); idx.pop(k); done = True; guard = 0; break
        if not done:
            break
    if len(idx) == 3: tris.append(tuple(idx))
    elif len(idx) > 3:                        # degenerate leftovers -> fan
        for k in range(1, len(idx)-1): tris.append((idx[0], idx[k], idx[k+1]))
    return tris

def _seg_int_x(p, a, b):
    """x of intersection of horizontal ray from p with segment a-b (a.y > p.y > b.y or reverse)."""
    if abs(b[1]-a[1]) < 1e-18: return None
    t = (p[1]-a[1]) / (b[1]-a[1])
    if t < 0 or t > 1: return None
    return a[0] + t*(b[0]-a[0])

def merge_holes(outer, holes):
    """Bridge CW holes into a CCW outer ring -> one simple polygon (list of (u,v))."""
    outer = list(outer)
    holes = sorted([list(h) for h in holes], key=lambda h: -max(p[0] for p in h))
    for hole in holes:
        if len(hole) < 3: continue
        hi = max(range(len(hole)), key=lambda i: hole[i][0])
        M_ = hole[hi]
        best_x = None; best_i = None
        for i in range(len(outer)):
            a = outer[i]; b = outer[(i+1) % len(outer)]
            if (a[1] > M_[1]) == (b[1] > M_[1]): continue
            x = _seg_int_x(M_, a, b)
            if x is None or x < M_[0] - 1e-12: continue
            if best_x is None or x < best_x:
                best_x = x; best_i = i if a[0] > b[0] else (i+1) % len(outer)
        if best_i is None:
            best_i = max(range(len(outer)), key=lambda i: outer[i][0])
        P = outer[best_i]
        # candidate visible vertex: reflex points inside triangle (M, (best_x,M.y), P)
        cand = best_i; bestang = None
        for i,q in enumerate(outer):
            if q[0] <= M_[0]: continue
            if _in_tri(q, M_, (best_x if best_x is not None else P[0], M_[1]), P):
                ang = abs(math.atan2(q[1]-M_[1], q[0]-M_[0]))
                if bestang is None or ang < bestang: bestang = ang; cand = i
        rot = hole[hi:] + hole[:hi]
        outer = outer[:cand+1] + rot + [rot[0]] + outer[cand:]
    return outer

# ---------------------------------------------------------------- face -> triangles
def unwrap(surf, pts, close=True):
    out = []; pu = pv = None
    seq = pts + [pts[0]] if close else pts
    for p in seq:
        u,v = surf.uv(p)
        if surf.periodic_u and pu is not None:
            while u - pu >  math.pi: u -= TAU
            while u - pu < -math.pi: u += TAU
        if surf.periodic_v and pv is not None:
            while v - pv >  math.pi: v -= TAU
            while v - pv < -math.pi: v += TAU
        out.append((u,v)); pu, pv = u, v
    wind_u = out[-1][0] - out[0][0]
    wind_v = out[-1][1] - out[0][1]
    if close: out.pop()
    return out, wind_u, wind_v

def resample_ring(ring, target_u0, n):
    """Resample a u-monotone-ish ring to n points spanning a full turn starting near target_u0."""
    return ring

def face_triangles(M, face_ref, tol):
    typ, a = M.e(face_ref)
    surf = Surf(M, a[2]); same = (str(a[3]) == 'T')
    rings = []
    for b in a[1]:
        bt, ba = M.e(b)
        lp = loop_points(M, ba[1], tol)
        if len(lp) < 3: continue
        if str(ba[2]) != 'T': lp = list(reversed(lp))
        if not same:        lp = list(reversed(lp))
        uv, wu, wv = unwrap(surf, lp)
        rings.append({'uv': uv, 'wu': wu, 'wv': wv, 'outer': (bt == 'FACE_OUTER_BOUND'),
                      'area': signed_area(uv)})
    if not rings: return []

    enc  = [r for r in rings if abs(r['wu']) > math.pi]
    encv = [r for r in rings if abs(r['wv']) > math.pi]
    poly = None; holes = []

    if not enc and not encv:
        outs = [r for r in rings if r['area'] > 0]
        if not outs:
            outs = [max(rings, key=lambda r: abs(r['area']))]
            outs[0]['uv'] = list(reversed(outs[0]['uv']))
        outer = max(outs, key=lambda r: abs(r['area']))
        holes = [r['uv'] if signed_area(r['uv']) < 0 else list(reversed(r['uv']))
                 for r in rings if r is not outer]
        poly = outer['uv']
    elif len(enc) == 2:
        A, B = enc
        if A['wu'] < 0: A, B = B, A                    # A runs +u
        ra = A['uv']
        rb = B['uv'] if B['wu'] > 0 else list(reversed(B['uv']))
        # align B's start u to A's start u (mod 2pi)
        sh = round((ra[0][0] - rb[0][0]) / TAU) * TAU
        rb = [(u+sh, v) for u,v in rb]
        k = min(range(len(rb)), key=lambda i: abs(rb[i][0] - ra[0][0]))
        rb = rb[k:] + [(u+TAU, v) for u,v in rb[:k]]
        poly = ra + list(reversed(rb))
        if signed_area(poly) < 0: poly = list(reversed(poly))
        holes = [r['uv'] if signed_area(r['uv']) < 0 else list(reversed(r['uv']))
                 for r in rings if r not in (A, B)]
    elif len(enc) == 1:
        r = enc[0]; ring = r['uv']
        up = r['wu'] > 0
        if surf.typ == 'SPHERICAL_SURFACE':
            vp = math.pi/2 * (1 if up else -1)
        elif surf.typ == 'CONICAL_SURFACE':
            t = math.tan(surf.ha)
            vp = (-surf.R / t) if abs(t) > 1e-9 else None
            if vp is None: return _fan(surf, rings, same, tol)
        else:
            return _fan(surf, rings, same, tol)
        u0 = ring[0][0]; u1 = ring[-1][0]
        n = max(8, min(48, len(ring)))
        cap = [(u1 + (u0-u1)*i/n, vp) for i in range(n+1)]
        poly = ring + cap
        if signed_area(poly) < 0: poly = list(reversed(poly))
        holes = [rr['uv'] if signed_area(rr['uv']) < 0 else list(reversed(rr['uv']))
                 for rr in rings if rr is not r]
    else:
        M.stats['fallback:%s:%d' % (surf.typ, len(enc))] += 1
        return _fan(surf, rings, same, tol)

    if holes: poly = merge_holes(poly, holes)
    tris = earclip(poly)
    return _emit(surf, poly, tris, same, tol)

def _fan(surf, rings, same, tol):
    outer = max(rings, key=lambda r: abs(r['area']))
    poly = outer['uv']
    if signed_area(poly) < 0: poly = list(reversed(poly))
    tris = earclip(poly)
    return _emit(surf, poly, tris, same, tol)

def _emit(surf, poly, tris, same, tol):
    out = []
    flat = surf.typ == 'PLANE'
    for (i,j,k) in tris:
        _subdiv(surf, poly[i], poly[j], poly[k], out, tol, 0 if flat else 3)
    if not same:
        out = [(c,b,a) for (a,b,c) in out]
    return out

def _mid(a,b): return ((a[0]+b[0])*0.5, (a[1]+b[1])*0.5)

def _subdiv(surf, A, B, C, out, tol, depth):
    if depth > 0:
        pa, pb, pc = surf.xyz(*A), surf.xyz(*B), surf.xyz(*C)
        worst = 0.0
        for (u1,p1),(u2,p2) in (((A,pa),(B,pb)), ((B,pb),(C,pc)), ((C,pc),(A,pa))):
            m = surf.xyz(*_mid(u1,u2))
            worst = max(worst, dist(m, mul(add(p1,p2), 0.5)))
        if worst > tol:
            AB, BC, CA = _mid(A,B), _mid(B,C), _mid(C,A)
            _subdiv(surf, A, AB, CA, out, tol, depth-1)
            _subdiv(surf, AB, B, BC, out, tol, depth-1)
            _subdiv(surf, CA, BC, C, out, tol, depth-1)
            _subdiv(surf, AB, BC, CA, out, tol, depth-1)
            return
    out.append((A,B,C))

# ---------------------------------------------------------------- driver
def solid_colours(M):
    col = {}
    for eid,(t,a) in M.E.items():
        if t != 'STYLED_ITEM': continue
        item = a[2]
        rgb = None
        try:
            for psa in a[1]:
                for ssu in M.e(psa)[1][0]:
                    t2,a2 = M.e(ssu)
                    if t2 != 'SURFACE_STYLE_USAGE': continue
                    sss = M.e(a2[1])[1][1]
                    for ssfa in sss:
                        t3,a3 = M.e(ssfa)
                        if t3 != 'SURFACE_STYLE_FILL_AREA': continue
                        fas = M.e(a3[0])[1][1]
                        for fasc in fas:
                            c = M.e(M.e(fasc)[1][1])
                            if c[0] == 'COLOUR_RGB':
                                rgb = (float(c[1][1]), float(c[1][2]), float(c[1][3]))
        except Exception:
            pass
        if rgb: col[int(item)] = rgb
    return col

def build(path, tol_frac=0.0016, out='model.glb'):
    M = Model(path)
    cols = solid_colours(M)
    solids = [(eid,a) for eid,(t,a) in M.E.items() if t == 'MANIFOLD_SOLID_BREP']
    # bounding box from all cartesian points
    xs=[];ys=[];zs=[]
    for eid,(t,a) in M.E.items():
        if t == 'CARTESIAN_POINT' and len(a[1]) == 3:
            xs.append(a[1][0]); ys.append(a[1][1]); zs.append(a[1][2])
    lo = (min(xs),min(ys),min(zs)); hi = (max(xs),max(ys),max(zs))
    diag = dist(lo,hi)
    tol = diag * tol_frac
    print('solids %d  bbox %.1f x %.1f x %.1f  diag %.1f  tol %.4f'
          % (len(solids), hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2], diag, tol))

    groups = defaultdict(lambda: {'v': [], 'n': [], 'i': []})
    edge_ids = set()
    nfaces = 0
    for eid, a in solids:
        rgb = cols.get(eid, (0.72,0.74,0.78))
        key = tuple(round(c,3) for c in rgb)
        g = groups[key]
        shell = M.e(a[1])
        for f in shell[1][1]:
            nfaces += 1
            try:
                for bnd in M.e(f)[1][1]:
                    for oe in M.e(M.e(bnd)[1][1])[1][1]:
                        edge_ids.add(int(M.e(oe)[1][3]))
            except Exception:
                pass
            try:
                tris = face_triangles(M, f, tol)
            except Exception as ex:
                M.stats['err:'+type(ex).__name__] += 1; continue
            surf = Surf(M, M.e(f)[1][2]); same = (str(M.e(f)[1][3]) == 'T')
            for (A,B,C) in tris:
                for uv in (A,B,C):
                    p = surf.xyz(*uv); nn = surf.normal(*uv)
                    if not same: nn = mul(nn,-1)
                    g['i'].append(len(g['v'])//3)
                    g['v'] += [p[0],p[1],p[2]]
                    g['n'] += [nn[0],nn[1],nn[2]]
    # --- B-rep edges, as line segments, for the CAD-style overlay ---
    lv = []
    for ec in edge_ids:
        try:
            _, ea = M.e(ec)
            p1 = M.point(M.e(ea[1])[1][1]); p2 = M.point(M.e(ea[2])[1][1])
            pts = sample_curve(M, ea[3], p1, p2, tol) if str(ea[4]) == 'T' \
                  else list(reversed(sample_curve(M, ea[3], p2, p1, tol)))
        except Exception:
            continue
        for a, b in zip(pts, pts[1:]):
            lv += [a[0], a[1], a[2], b[0], b[1], b[2]]
    if lv: groups['__edges__'] = {'v': lv, 'n': [], 'i': [], 'lines': True}

    tri_total = sum(len(g['i']) for g in groups.values())//3
    print('faces %d   groups %d   triangles %d   edge segments %d'
          % (nfaces, len(groups), tri_total, len(lv)//6))
    if M.stats: print('notes:', dict(M.stats))
    return M, groups, lo, hi

# ---------------------------------------------------------------- GLB
def write_glb(groups, lo, hi, path, yup=True, target=2.0):
    # recompute bbox from the tessellated vertices (ignores stray construction points)
    xs=[];ys=[];zs=[]
    for g in groups.values():
        v=g['v']
        xs+= v[0::3]; ys+= v[1::3]; zs+= v[2::3]
    if xs:
        lo=(min(xs),min(ys),min(zs)); hi=(max(xs),max(ys),max(zs))
        print('mesh bbox %.1f x %.1f x %.1f' % (hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2]))
    ctr = mul(add(lo,hi), 0.5)
    scale = target / max(1e-9, max(hi[0]-lo[0], hi[1]-lo[1], hi[2]-lo[2]))
    bin_parts = []; offset = 0
    bufferViews = []; accessors = []; materials = []; prims = []

    def push(data, target_hint):
        nonlocal offset
        pad = (-len(data)) % 4
        bin_parts.append(data + b'\x00'*pad)
        bv = {'buffer':0, 'byteOffset':offset, 'byteLength':len(data)}
        if target_hint: bv['target'] = target_hint
        bufferViews.append(bv); offset += len(data)+pad
        return len(bufferViews)-1

    for key, g in sorted(groups.items(), key=lambda kv: str(kv[0])):
        if g.get('lines'):
            V = []
            for i in range(0, len(g['v']), 3):
                x, y, z = (g['v'][i]-ctr[0])*scale, (g['v'][i+1]-ctr[1])*scale, (g['v'][i+2]-ctr[2])*scale
                if yup: x, y, z = x, z, -y
                V += [x, y, z]
            nv = len(V)//3
            bvP = push(struct.pack('<%df' % len(V), *V), 34962)
            mn = [min(V[i::3]) for i in range(3)]; mx = [max(V[i::3]) for i in range(3)]
            aP = len(accessors)
            accessors.append({'bufferView': bvP, 'componentType': 5126, 'count': nv,
                              'type': 'VEC3', 'min': mn, 'max': mx})
            mi = len(materials)
            materials.append({'pbrMetallicRoughness': {'baseColorFactor': [.20, .21, .24, 1.0]},
                              'name': 'edges'})
            prims.append({'attributes': {'POSITION': aP}, 'mode': 1, 'material': mi})
            print('edge lines: %d segments' % (nv//2))
            continue
        if not g['i']: continue
        # weld identical vertices
        vmap = {}; V=[]; N=[]; I=[]
        vv, nn = g['v'], g['n']
        for idx in g['i']:
            p = (round(vv[3*idx],5), round(vv[3*idx+1],5), round(vv[3*idx+2],5))
            q = (round(nn[3*idx],3), round(nn[3*idx+1],3), round(nn[3*idx+2],3))
            k = (p,q)
            j = vmap.get(k)
            if j is None:
                j = len(V)//3; vmap[k] = j
                x,y,z = (vv[3*idx]-ctr[0])*scale, (vv[3*idx+1]-ctr[1])*scale, (vv[3*idx+2]-ctr[2])*scale
                a,b,c = nn[3*idx], nn[3*idx+1], nn[3*idx+2]
                if yup: x,y,z = x, z, -y ; a,b,c = a, c, -b
                V += [x,y,z]; N += [a,b,c]
            I.append(j)
        nv = len(V)//3
        pos = struct.pack('<%df' % len(V), *V)
        nor = struct.pack('<%df' % len(N), *N)
        if nv < 65536: idx_b = struct.pack('<%dH' % len(I), *I); ctype = 5123
        else:          idx_b = struct.pack('<%dI' % len(I), *I); ctype = 5125
        bvP = push(pos, 34962); bvN = push(nor, 34962); bvI = push(idx_b, 34963)
        mn = [min(V[i::3]) for i in range(3)]; mx = [max(V[i::3]) for i in range(3)]
        aP = len(accessors); accessors.append({'bufferView':bvP,'componentType':5126,'count':nv,'type':'VEC3','min':mn,'max':mx})
        aN = len(accessors); accessors.append({'bufferView':bvN,'componentType':5126,'count':nv,'type':'VEC3'})
        aI = len(accessors); accessors.append({'bufferView':bvI,'componentType':ctype,'count':len(I),'type':'SCALAR'})
        mi = len(materials)
        materials.append({'pbrMetallicRoughness':{
            'baseColorFactor':[key[0],key[1],key[2],1.0],'metallicFactor':0.35,'roughnessFactor':0.55},
            'doubleSided': True, 'name':'c%d'%mi})
        prims.append({'attributes':{'POSITION':aP,'NORMAL':aN},'indices':aI,'material':mi})

    binb = b''.join(bin_parts)
    gltf = {'asset':{'version':'2.0','generator':'step2glb'},
            'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],
            'meshes':[{'primitives':prims}],
            'materials':materials,'accessors':accessors,'bufferViews':bufferViews,
            'buffers':[{'byteLength':len(binb)}]}
    js = json.dumps(gltf, separators=(',',':')).encode()
    js += b' ' * ((-len(js)) % 4)
    total = 12 + 8 + len(js) + 8 + len(binb)
    with open(path,'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, total))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(binb), 0x004E4942)); f.write(binb)
    print('wrote %s  %.2f MB  (%d prims, %d tris)' % (path, total/1e6, len(prims), sum(a['count'] for a in accessors if a['type']=='SCALAR')//3))

if __name__ == '__main__':
    src = sys.argv[1]; dst = sys.argv[2] if len(sys.argv)>2 else 'model.glb'
    M, groups, lo, hi = build(src, float(sys.argv[3]) if len(sys.argv)>3 else 0.0016)
    # This SolidWorks export is already Y-up (Y is the trailer's height axis),
    # so no Z-up -> Y-up rotation is needed for glTF.
    write_glb(groups, lo, hi, dst, yup=(len(sys.argv) > 4 and sys.argv[4] == 'zup'))
