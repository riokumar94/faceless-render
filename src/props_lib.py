# v3 QC rules: every shot shows topic props; full-phrase labels wrapped (never truncated); counters hold final value.
import math,os
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__));_PC={}
def prop(e,size):
    cp=ord(e[0]);k=(cp,size)
    if k not in _PC:
        im=Image.open(f'{HERE}/props/{cp:x}.png').convert('RGBA');s=size/max(im.size);_PC[k]=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
    return _PC[k]
def paste(im,e,cx,cy,size,rot=0.0,alpha=1.0):
    if size<4:return
    p=prop(e,int(size))
    if rot:p=p.rotate(rot,expand=True,resample=Image.BICUBIC)
    if alpha<1:a=p.getchannel('A').point(lambda v:int(v*alpha));p=p.copy();p.putalpha(a)
    im.paste(p,(int(cx-p.width/2),int(cy-p.height/2)),p)
def wrap(d,F,s,maxw=900,size=88,maxl=3,minsz=50):
    while True:
        f=F(size);ws=s.split();L=[];cur=''
        for w in ws:
            c=(cur+' '+w).strip()
            if d.textlength(c,font=f)<=maxw or not cur:cur=c
            else:L.append(cur);cur=w
        L.append(cur)
        if (len(L)<=maxl and max(d.textlength(l,font=f) for l in L)<=maxw) or size<=24:return f,L   # breaks only at spaces; shrink until even the widest single word fits
        size-=6 if size>minsz or len(L)<=maxl else 0
        if size<=minsz and len(L)>maxl:return f,L
