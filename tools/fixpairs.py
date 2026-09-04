from PIL import Image, ImageFilter
import os
SRC='/home/claude/work'; OUT='/home/claude/site/assets/img'
BG=(241,238,235)
def warm(im):
    im=im.convert('RGB'); lut=[]
    for t in BG:
        lut+=[i if i<200 else int(round(200+(i-200)*(t-200)/55.0)) for i in range(256)]
    return im.point(lut)

def pad_to(im, ar):
    """Widen/heighten to the target aspect by replicating edge pixels (invisible on gradients)."""
    w,h = im.size; cur = w/h
    if abs(cur-ar) < 0.005: return im
    if cur < ar:                                   # need more width
        nw = int(round(h*ar)); extra = nw-w
        l = extra//2; r = extra-l
        out = Image.new('RGB', (nw,h))
        out.paste(im, (l,0))
        if l: out.paste(im.crop((0,0,1,h)).resize((l,h), Image.NEAREST), (0,0))
        if r: out.paste(im.crop((w-1,0,w,h)).resize((r,h), Image.NEAREST), (l+w,0))
    else:                                          # need more height
        nh = int(round(w/ar)); extra = nh-h
        t = extra//2; b = extra-t
        out = Image.new('RGB', (w,nh))
        out.paste(im, (0,t))
        if t: out.paste(im.crop((0,0,w,1)).resize((w,t), Image.NEAREST), (0,0))
        if b: out.paste(im.crop((0,h-1,w,h)).resize((w,b), Image.NEAREST), (0,t+h))
    return out

def crop_to(im, ar, fx=.5, fy=.5):
    w,h=im.size; cur=w/h
    if abs(cur-ar)<0.005: return im
    if cur>ar:
        nw=int(round(h*ar)); x=int((w-nw)*fx); return im.crop((x,0,x+nw,h))
    nh=int(round(w/ar)); y=int((h-nh)*fy); return im.crop((0,y,w,y+nh))

def save(im,name,W,q=84,sharp=False):
    if im.width != W:
        im = im.resize((W,int(round(W*im.height/im.width))), Image.LANCZOS)
        if sharp: im = im.filter(ImageFilter.UnsharpMask(1.2,70,3))
    p=os.path.join(OUT,name+'.webp'); im.convert('RGB').save(p,'WEBP',quality=q,method=6)
    print('%-24s %dx%d  %.1f KB' % (name, im.width, im.height, os.path.getsize(p)/1024))

L=lambda f: Image.open(os.path.join(SRC,f))

# --- pair 1: motor CAD renders -> common 3:2 (pad, never crop) ---
save(pad_to(warm(L('pg-003-002.png')), 1.5), 'p1-cad-section',  1100)
save(pad_to(warm(L('pg-003-003.png')), 1.5), 'p1-cad-exploded', 1100)

# --- pair 2: encoder renders -> common 1.26 ---
save(pad_to(warm(L('pg-005-005.png')), 1.26), 'p1-encoder-original', 950)
save(pad_to(warm(L('pg-005-006.png')), 1.26), 'p1-encoder-new',      950, sharp=True)

# --- pair 3: pool robot cover + team -> 4:3 ---
save(crop_to(L('pg-010-013.png'), 4/3), 'p3-cover', 1100, q=88, sharp=True)
save(crop_to(L('pg-010-014.png'), 4/3), 'p3-team',  1400)

# --- pair 4: striking mechanism -> 4:3, detail focused on the linkage ---
save(crop_to(L('pg-012-015.png'), 4/3, fy=0.42), 'p3-strike-detail', 1200)
save(crop_to(L('pg-012-016.png'), 4/3),          'p3-strike-full',   1200)
