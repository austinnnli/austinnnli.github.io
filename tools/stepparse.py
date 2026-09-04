"""Minimal AP203/AP214 STEP reader: entity table + recursive-descent argument parser."""
import re, sys

class Ref(int):
    __slots__ = ()
    def __repr__(self): return '#%d' % int(self)

class Enum(str):
    __slots__ = ()

_NUM = re.compile(r'[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?')

def parse_args(s, i=0):
    """Parse a comma separated argument list starting after '('. Returns (list, next_index)."""
    out = []; n = len(s)
    while i < n:
        while i < n and s[i] in ' \t\r\n': i += 1
        if i >= n: break
        c = s[i]
        if c == ')':
            return out, i + 1
        if c == ',':
            i += 1; continue
        if c == '(':
            sub, i = parse_args(s, i + 1); out.append(sub); continue
        if c == "'":
            j = i + 1; buf = []
            while j < n:
                if s[j] == "'":
                    if j + 1 < n and s[j + 1] == "'": buf.append("'"); j += 2; continue
                    break
                buf.append(s[j]); j += 1
            out.append(''.join(buf)); i = j + 1; continue
        if c == '#':
            j = i + 1
            while j < n and s[j].isdigit(): j += 1
            out.append(Ref(int(s[i + 1:j]))); i = j; continue
        if c == '$':
            out.append(None); i += 1; continue
        if c == '*':
            out.append('*'); i += 1; continue
        if c == '.':
            j = s.find('.', i + 1)
            out.append(Enum(s[i + 1:j])); i = j + 1; continue
        m = _NUM.match(s, i)
        if m:
            t = m.group(0)
            out.append(float(t) if ('.' in t or 'e' in t or 'E' in t) else int(t))
            i = m.end(); continue
        # bare keyword (typed value like  LENGTH_MEASURE(1.0) )
        j = i
        while j < n and (s[j].isalnum() or s[j] == '_'): j += 1
        kw = s[i:j]
        while j < n and s[j] in ' \t\r\n': j += 1
        if j < n and s[j] == '(':
            sub, j = parse_args(s, j + 1)
            out.append((kw.upper(), sub))
        elif kw:
            out.append(kw)
        else:
            j += 1
        i = j
    return out, i

def load(path):
    txt = open(path, 'r', errors='replace').read()
    txt = txt.split('DATA;', 1)[1].rsplit('ENDSEC;', 1)[0]
    txt = re.sub(r'/\*.*?\*/', ' ', txt, flags=re.S)
    ents = {}
    head = re.compile(r'#(\d+)\s*=\s*([A-Za-z_0-9]*)\s*\(')
    pos = 0
    while True:
        m = head.search(txt, pos)
        if not m: break
        eid = int(m.group(1)); typ = m.group(2).upper()
        args, nxt = parse_args(txt, m.end())
        if typ == '':                       # complex entity: ( A(..) B(..) )
            ents[eid] = ('__COMPLEX__', args)
        else:
            ents[eid] = (typ, args)
        pos = nxt
    return ents

if __name__ == '__main__':
    e = load(sys.argv[1])
    print(len(e), 'entities')
    from collections import Counter
    print(Counter(v[0] for v in e.values()).most_common(12))
    for k in (1, 2, 3, 4, 5, 6, 7):
        print(k, e.get(k))
    for k, v in e.items():
        if v[0] in ('COLOUR_RGB', 'STYLED_ITEM', 'ADVANCED_FACE', 'TOROIDAL_SURFACE',
                    'B_SPLINE_CURVE_WITH_KNOTS', 'MANIFOLD_SOLID_BREP', 'CIRCLE',
                    'AXIS2_PLACEMENT_3D', 'FACE_OUTER_BOUND', 'EDGE_LOOP',
                    'CYLINDRICAL_SURFACE', 'PRESENTATION_STYLE_ASSIGNMENT',
                    'SURFACE_STYLE_USAGE','SURFACE_SIDE_STYLE','SURFACE_STYLE_FILL_AREA',
                    'FILL_AREA_STYLE','FILL_AREA_STYLE_COLOUR','GEOMETRIC_REPRESENTATION_CONTEXT'):
            print(v[0], '->', k, str(v[1])[:170]); 
            globals().setdefault('_seen', set())
            
