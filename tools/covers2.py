from PIL import Image, ImageFilter
import os
SRC='/home/claude/work'; OUT='/home/claude/site/assets/img'
BG=(241,238,235)
def warm(im):
    im=im.convert('RGB'); lut=[]
    for t in BG:
        lut+=[i if i<200 else int(round(200+(i-200)*(t-200)/55.0)) for i in range(256)]
    return im.point(lut)
def crop_to(im, ar, fx=0.5, fy=0.5):
    w,h=im.size; cur=w/h
    if cur>ar:
        nw=int(round(h*ar)); x=int((w-nw)*fx); return im.crop((x,0,x+nw,h))
    nh=int(round(w/ar)); y=int((h-nh)*fy); return im.crop((0,y,w,y+nh))
def cover(src,name,W,H,fx=.5,fy=.5,render=False,sharp=False,q=84):
    im=Image.open(os.path.join(SRC,src))
    if render: im=warm(im)
    im=crop_to(im,W/H,fx,fy).resize((W,H),Image.LANCZOS)
    if sharp: im=im.filter(ImageFilter.UnsharpMask(1.2,80,3))
    p=os.path.join(OUT,name+'.webp'); im.convert('RGB').save(p,'WEBP',quality=q,method=6)
    print(f'{name:22s} {W}x{H} {os.path.getsize(p)/1024:7.1f} KB')

cover('pg-002-001.png','cover-motor',   1440,844)
cover('pg-013-017.png','cover-cleat',    704,844, fy=0.55)
cover('pg-008-010.png','cover-forc',     704,552)
cover('pg-010-013.png','cover-pool',     704,552, sharp=True, q=88)
cover('pg-016-021.png','cover-cycloid',  704,552)
cover('pg-017-024.png','cover-trailer', 2208,844, render=True)
