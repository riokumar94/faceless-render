"""Whiteboard stroke-reveal renderer (original line art, PIL only, free).
Each scene = hard cut. Items draw path-by-path, finishing on their key spoken word.
A drawn marker follows the stroke tip. Captions in whole words. Slow push-in."""
import json, math, random, subprocess, sys
from PIL import Image, ImageDraw
W,H,FPS=1080,1920,30
INK=(22,22,22); PAPER=(250,249,244); PAPERS=[PAPER,(228,237,248)]  # v13: alternate paper per shot so every cut registers
import os
import strokefont as SF
rnd=random.Random(7)
def wob(pts,amp=3.0):
    out=[]
    for i,(x,y) in enumerate(pts):
        out.append((x+rnd.uniform(-amp,amp),y+rnd.uniform(-amp,amp)))
    return out
def seg(pts,n=12):  # densify for smooth reveal
    o=[pts[0]]
    for a,b in zip(pts,pts[1:]):
        d=math.dist(a,b);k=max(1,int(d/n))
        o+= [(a[0]+(b[0]-a[0])*t/k,a[1]+(b[1]-a[1])*t/k) for t in range(1,k+1)]
    return o
# ---- primitive builders: return list of strokes (point lists) ----
def L(*p): return [wob(seg(list(p)))]
def circ(cx,cy,r,a0=-100,a1=265,ry=None):
    ry=ry or r;n=max(16,int(r/4))
    return [wob([(cx+r*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+ry*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+1)],2.5)]
def rect(x,y,w,h): return [wob(seg([(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y-4)]))]
def poly(*p): return [wob(seg(list(p)+[p[0]]))]
class Item:
    def __init__(s,strokes=(),fill=None,text=None,key=None,width=11,col=INK):
        s.strokes=list(strokes);s.fill=fill;s.text=text;s.key=key;s.width=width;s.col=col
# figure: big round head, stick body (top-ref style), flat colour shirt
def person(cx,cy,s=1.0,shirt=(232,96,52),mood='smile',arms='down'):
    r=70*s;st=[];hx,hy=cx,cy-170*s
    st+=circ(hx,hy,r)
    st+=L((hx-25*s,hy-10*s),(hx-25*s,hy+2*s));st+=L((hx+25*s,hy-10*s),(hx+25*s,hy+2*s))
    if mood=='smile':st+=circ(hx,hy+20*s,28*s,20,160)
    elif mood=='sad':st+=circ(hx,hy+50*s,26*s,200,340)
    else:st+=L((hx-20*s,hy+32*s),(hx+20*s,hy+32*s))
    body=[(cx-38*s,cy-95*s),(cx+38*s,cy-95*s),(cx+30*s,cy+10*s),(cx-30*s,cy+10*s)]
    st+=poly(*body)
    if arms=='up':st+=L((cx-38*s,cy-85*s),(cx-95*s,cy-170*s));st+=L((cx+38*s,cy-85*s),(cx+95*s,cy-170*s))
    elif arms=='head':st+=L((cx+38*s,cy-85*s),(cx+80*s,cy-150*s),(hx+50*s,hy-40*s));st+=L((cx-38*s,cy-85*s),(cx-70*s,cy-10*s))
    else:st+=L((cx-38*s,cy-85*s),(cx-70*s,cy-10*s));st+=L((cx+38*s,cy-85*s),(cx+70*s,cy-10*s))
    st+=L((cx-18*s,cy+10*s),(cx-30*s,cy+120*s),(cx-55*s,cy+122*s));st+=L((cx+18*s,cy+10*s),(cx+30*s,cy+120*s),(cx+55*s,cy+122*s))
    it=Item(st,fill=[(body,shirt),(('circle',hx,hy,r),(255,224,190))]);it.person=True;return it
def coin(cx,cy,r=45,mark='£'):
    it=Item(circ(cx,cy,r)+circ(cx,cy,r*0.72),fill=[(('circle',cx,cy,r),(250,226,140))])
    it.strokes+=text(mark,cx,cy,int(r*0.9)).strokes if r>=30 else [];return it
def text(t,x,y,size=90,col=INK,key=None):
    cap=size*0.8
    while SF.width(t,cap)>W-200 and cap>24: cap-=2
    hw=SF.width(t,cap)/2; x=min(max(x,110+hw),W-110-hw)
    st=[wob(seg(pl,8),1.6) for pl in SF.strokes(t,x,y,cap)]
    it=Item(st,key=key,width=max(6,int(cap/7)),col=col);it.is_text=True;it.y=y;return it
def cross(cx,cy,r=60,col=(214,40,40)): return Item(L((cx-r,cy-r),(cx+r,cy+r))+L((cx+r,cy-r),(cx-r,cy+r)),width=16,col=col)
def tick(cx,cy,r=60,col=(40,160,70)): return Item(L((cx-r,cy),(cx-r*0.3,cy+r*0.7),(cx+r,cy-r*0.8)),width=16,col=col)
def arrow(a,b,col=INK):
    ang=math.atan2(b[1]-a[1],b[0]-a[0]);h=40
    p1=(b[0]-h*math.cos(ang-0.5),b[1]-h*math.sin(ang-0.5));p2=(b[0]-h*math.cos(ang+0.5),b[1]-h*math.sin(ang+0.5))
    return Item(L(a,b)+L(p1,b,p2),col=col)
# ---- rendering ----
def stroke_len(st): return sum(math.dist(a,b) for a,b in zip(st,st[1:]))
def draw_partial(d,item,frac,sc,ox,oy):
    T=lambda p:(p[0]*sc+ox,p[1]*sc+oy)
    tot=sum(stroke_len(s) for s in item.strokes) or 1;budget=frac*tot;tip=None
    for st in item.strokes:
        if budget<=0:break
        pts=[T(st[0])];acc=0
        for a,b in zip(st,st[1:]):
            l=math.dist(a,b)
            if acc+l>budget:
                t=(budget-acc)/l if l else 0;pts.append(T((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)));acc=budget;break
            pts.append(T(b));acc+=l
        budget-=acc;w=max(2,int(item.width*sc))
        if len(pts)>1:d.line(pts,fill=item.col,width=w,joint='curve')
        for p in (pts[0],pts[-1]):d.ellipse([p[0]-w/2,p[1]-w/2,p[0]+w/2,p[1]+w/2],fill=item.col)
        tip=pts[-1]
    return tip
def draw_fill(d,item,sc,ox,oy):
    for shape,col in item.fill or []:
        if shape[0]=='circle':
            _,x,y,r=shape;x,y,r=x*sc+ox,y*sc+oy,r*sc*0.93;d.ellipse([x-r,y-r,x+r,y+r],fill=col)
        else:d.polygon([(x*sc+ox,y*sc+oy) for x,y in shape],fill=col)
def draw_marker(d,tip):
    if not tip:return
    x,y=tip;a=math.radians(35)  # original drawn marker: barrel + cap, follows the tip
    ux,uy=math.cos(a),math.sin(a);px,py=-uy,ux;L1,R=230,24
    nib=[(x,y),(x+ux*40+px*12,y+uy*40+py*12),(x+ux*40-px*12,y+uy*40-py*12)]
    body=[(x+ux*40+px*R,y+uy*40+py*R),(x+ux*L1+px*R,y+uy*L1+py*R),(x+ux*L1-px*R,y+uy*L1-py*R),(x+ux*40-px*R,y+uy*40-py*R)]
    d.polygon(nib,fill=INK);d.polygon(body,fill=(60,110,200),outline=INK,width=6)
    d.line([(x+ux*150+px*R,y+uy*150+py*R),(x+ux*150-px*R,y+uy*150-py*R)],fill=INK,width=6)
def ease(t):return t*t*(3-2*t)
def render(scenes,words,audio,out,t_end,ends=(),stills=None):
    # assign timings: items reveal sequentially, each ending on its key word end
    cap=[]
    for sc_ in scenes:
        t0=sc_['t0'];prev=t0
        for it in sc_['items']:
            ke=word_end(words,it.key,t0,sc_['t1']) if it.key else None
            it.te=min(ke if ke else prev+0.6,sc_['t1']-0.3);it.ts=min(prev,it.te-0.25);prev=it.te
        its=sc_['items'];dl=t0+min(0.35*(sc_['t1']-t0),1.1);mx=max([i.te for i in its]+[t0+0.01])
        k=min(1.0,(dl-t0)/(mx-t0))
        for it in its:
            it.ts=t0+(it.ts-t0)*k; it.te=max(it.ts+0.12,t0+(it.te-t0)*k)
            if getattr(it,'is_text',False): it.ts=max(it.ts,it.te-0.45)
            if getattr(it,'quick',False): it.ts=t0-0.1; it.te=t0+0.3
            elif not getattr(it,'instant',False): it.ts=max(it.ts,t0+0.3); it.te=max(it.te,it.ts+0.12)
            if getattr(it,'instant',False): it.ts=it.te=t0
            if getattr(it,'is_text',False) and not getattr(it,'instant',False):
                # v13: words pop in whole (never partly written), no later than t0+0.3
                it.ts=it.te=min(max(it.ts,t0+0.15),t0+0.3)
            it.te=min(it.te,sc_['t1']-0.35); it.ts=min(it.ts,it.te)
            assert it.te<sc_['t1']-0.3, (t0,it.te)
            if getattr(it,'is_text',False): assert it.te==it.ts and it.te<=t0+0.3, (t0,it.ts,it.te)
    if not stills:
     p=subprocess.Popen(['nice','-n','19','ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',audio,'-t',str(t_end),
        '-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest',out],stdin=subprocess.PIPE)
    chunks=caption_chunks(words,t_end,ends=set(ends))
    fr_list=[int(x*FPS) for x in stills] if stills else range(int(t_end*FPS))
    for fi in fr_list:
        t=fi/FPS;sc_=next((s for s in scenes if s['t0']<=t<s['t1']),scenes[-1])
        u=(t-sc_['t0'])/max(0.1,sc_['t1']-sc_['t0']);z=1.0+0.07*u  # slow push-in
        cx,cy=sc_.get('focus',(W/2,H*0.45));ox=cx-cx*z;oy=cy-cy*z
        img=Image.new('RGB',(W,H),PAPERS[scenes.index(sc_)%2]);d=ImageDraw.Draw(img);tip=None
        for it in sc_['items']:
            if t<it.ts:continue
            fr=1.0 if t>=it.te else ease((t-it.ts)/(it.te-it.ts))
            if it.fill and (fr>=1 or getattr(it,'quick',False)):draw_fill(d,it,z,ox,oy)
            if it.strokes:
                tp=draw_partial(d,it,fr,z,ox,oy)
                if fr<1:tip=tp
        c=next((c for c in chunks if c[0]<=t<c[1]),None)
        if c:
            fs=58;txt=c[2].upper();lines_=[txt]
            if SF.width(txt,fs)>W-160:
                ws=txt.split();h=len(ws)//2 or 1;lines_=[' '.join(ws[:h]),' '.join(ws[h:])]
            while fs>40 and max(SF.width(l,fs) for l in lines_)>W-160: fs-=2
            bw=max(SF.width(l,fs) for l in lines_);lh=fs*1.6;bh=lh*len(lines_)
            d.rounded_rectangle([W/2-bw/2-34,1640-bh/2-14,W/2+bw/2+34,1640+bh/2+14],22,fill=(255,255,255),outline=INK,width=6)
            for li,l in enumerate(lines_):
                for pl in SF.strokes(l,W/2,1640-bh/2+lh*(li+0.5),fs):
                    d.line(pl,fill=INK,width=8,joint='curve')
        if stills: img.save(f'{out}_{fi/FPS:06.2f}.png')
        else: p.stdin.write(img.tobytes())
    if not stills: p.stdin.close();p.wait()
def norm(w):return ''.join(ch for ch in w.lower() if ch.isalnum())
def word_end(words,key,t0,t1):
    for w,s,e in words:
        if t0-0.05<=s<t1 and norm(w)==norm(key):return e
    raise ValueError(f'key {key} not in {t0}-{t1}')
def caption_chunks(words,t_end,maxw=3,maxc=18,ends=set()):
    out=[];cur=[]
    for i,(w,s,e) in enumerate(words):
        if s>=t_end:break
        cur.append((w,s,e))
        if len(cur)>=maxw or len(' '.join(x[0] for x in cur))>=maxc or w[-1] in '.?!,:' or i in ends:
            out.append([cur[0][1],cur[-1][2],' '.join(x[0] for x in cur).upper()]);cur=[]
    if cur:out.append([cur[0][1],cur[-1][2],' '.join(x[0] for x in cur).upper()])
    for a,b in zip(out,out[1:]):a[1]=b[0]
    return out
