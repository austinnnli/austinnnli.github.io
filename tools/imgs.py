from PIL import Image, ImageEnhance, ImageFilter
import os
SRC='/home/claude/work'
OUT='/home/claude/site/assets/img'
os.makedirs(OUT, exist_ok=True)
BG=(241,238,235)

def warm_highlights(im):
    """Map near-white CAD-render backgrounds onto the page background colour."""
    im=im.convert('RGB')
    lut=[]
    for c,target in enumerate(BG):
        ch=[]
        for i in range(256):
            if i<200: ch.append(i)
            else: ch.append(int(round(200+(i-200)*(target-200)/55.0)))
        lut+=ch
    return im.point(lut)

def crop_to(im, ar, focus=0.5):
    w,h=im.size
    cur=w/h
    if abs(cur-ar)<0.005: return im
    if cur>ar:      # too wide -> crop sides
        nw=int(round(h*ar)); x=int((w-nw)*focus); return im.crop((x,0,x+nw,h))
    else:           # too tall -> crop top/bottom
        nh=int(round(w/ar)); y=int((h-nh)*focus); return im.crop((0,y,w,y+nh))

def save(im, name, width, ar=None, focus=0.5, q=84, render=False, sharpen=False):
    if render: im=warm_highlights(im)
    if ar: im=crop_to(im, ar, focus)
    if im.width!=width:
        h=int(round(width*im.height/im.width))
        im=im.resize((width,h), Image.LANCZOS)
        if sharpen: im=im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=3))
    p=os.path.join(OUT,name+'.webp')
    im.convert('RGB').save(p, 'WEBP', quality=q, method=6)
    print(f'{name:28s} {im.size[0]}x{im.size[1]}  {os.path.getsize(p)/1024:7.1f} KB')

L=lambda f: Image.open(os.path.join(SRC,f))

# ---------- headshot ----------
save(L('pg-001-000.png'), 'headshot', 1100, ar=4/5, focus=0.42)

# ---------- P1  PMSM hub motor ----------
save(L('pg-002-001.png'), 'p1-cover',            1720, ar=16/10)
save(L('pg-003-002.png'), 'p1-cad-section',      1000, render=True)
save(L('pg-003-003.png'), 'p1-cad-exploded',     1000, render=True)
save(L('pg-004-004.png'), 'p1-stator-housing',   1500, ar=4/3)
save(L('pg-005-005.png'), 'p1-encoder-original',  825, render=True)
save(L('pg-005-006.png'), 'p1-encoder-new',       825, render=True, sharpen=True)
save(L('pg-006-007.png'), 'p1-rotor',            1200)
save(L('pg-007-008.png'), 'p1-magfield',         1100)
save(L('pg-007-009.png'), 'p1-scope',             960, sharpen=True, q=88)

# ---------- P2  FORC ----------
save(L('pg-008-010.png'), 'p2-cover',            1320)
save(L('pg-009-011.png'), 'p2-top',              1400)
save(L('pg-009-012.png'), 'p2-layout',           1680)

# ---------- P3  Pool robot ----------
save(L('pg-010-013.png'), 'p3-cover',            1024, sharpen=True, q=88)
save(L('pg-010-014.png'), 'p3-team',             1400, ar=4/3)
save(L('pg-012-015.png'), 'p3-strike-detail',    1100, ar=3/4)
save(L('pg-012-016.png'), 'p3-strike-full',      1100, ar=4/3)

# ---------- P4  AutoCleat ----------
save(L('pg-013-017.png'), 'p4-cover',            1400, ar=4/3, focus=0.55)
save(L('pg-014-018.png'), 'p4-shoe-side',        1100, ar=3/4)
save(L('pg-014-019.png'), 'p4-shoe-worn',        1100, ar=3/4)
save(L('pg-015-020.png'), 'p4-prototype',        1400, ar=4/3)

# ---------- P5  Cycloidal ----------
save(L('pg-016-021.png'), 'p5-photo-a',          1300, ar=4/3)
save(L('pg-016-022.png'), 'p5-photo-b',          1300, ar=4/3)
save(L('pg-017-023.png'), 'p5-exploded',          991, render=True)

# ---------- P6  Trailer ----------
save(L('pg-017-024.png'), 'p6-cover',            1720, render=True)
save(L('pg-018-025.png'), 'p6-cad-iso',          1290, render=True)
save(L('pg-018-026.png'), 'p6-real',             1600, ar=16/9)
save(L('pg-018-027.png'), 'p6-cad-side',         1720, render=True)
