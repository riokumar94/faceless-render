"""motion.py - opt-in MOTION style for Shorts (does not touch the default qrender path).
usage: python motion.py <ch> <n> [out.mp4]   (needs <K>_vo.wav + <K>_words.json from vo2.py)
Every shot is code-drawn motion (PIL/numpy): self-drawing diagrams, maps, arrows, counters,
build-up cutaways, stick figure (stick.py), and 2-layer mask-split parallax on licensed photos.
Scene plans live in PLANS[K] (one list of scene calls per script line)."""
import json,subprocess,time,sys,re,os,math,shutil,numpy as np,soundfile as sf
if os.environ.get('MOTION_TEST') and os.path.exists('/workspace/studio/b1/HOLD'):print('HOLD: test frames paused until G approves new-style pilot');sys.exit(0)
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE);import chan,stick
t0=time.time();W,H,FPS=1080,1920,30;ch=sys.argv[1];n=int(sys.argv[2]);K=f'{ch}{n:02d}'
# Job JSON (cloud/portable): MOTION_JOB env or <dir>/<K>_motion.json -> {chan:{..}, plan:'csf05', script:{title,vo,tags}, lines:[..]}
JOBF=os.environ.get('MOTION_JOB') or (os.path.join(chan.C[ch]['dir'],K+'_motion.json') if ch in chan.C else '')
JOB=json.load(open(JOBF)) if JOBF and os.path.exists(JOBF) else None
if JOB:
    C={k:(tuple(v) if isinstance(v,list) else v) for k,v in JOB['chan'].items()};SRC=os.path.dirname(os.path.abspath(JOBF));PK=JOB.get('plan',K)
else: C=chan.C[ch];SRC=C['dir'];PK=K
OUT=os.path.abspath(sys.argv[3]) if len(sys.argv)>3 else os.path.join(SRC,K+'_motion.mp4')
TMP=os.path.join(os.path.dirname(OUT),f'tmp_{K}_motion');os.makedirs(TMP,exist_ok=True)
V=JOB['script'] if JOB else [v for v in json.load(open(f'{SRC}/{ch}_scripts.json')) if v['n']==n][0]
words=json.load(open(f'{SRC}/{K}_words.json'));vo,sr=sf.read(f'{SRC}/{K}_vo.wav');OFF=0.4;TEND=len(vo)/sr+OFF;CARD=2.5;DUR=TEND+CARD
TW=V['vo'].split();norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower());caps=[];i=0
for tw in TW:
    tgt=norm(tw);acc='';st=None
    if not tgt: continue
    while acc!=tgt:
        assert i<len(words);acc+=norm(words[i][0]);st=st if st is not None else words[i][1];en=words[i][2];i+=1
        if len(acc)>len(tgt): raise SystemExit(f'CAPTION MISMATCH {tw} vs {acc}')
    caps.append((tw,st+OFF,en+OFF))
assert i==len(words);print('captions verified',len(caps))
# script lines = sentences grouped as in the script file (LINES[K]) -> time span per line
FB='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf';_fc={}
def F(s):
    s=int(s)
    if s not in _fc:_fc[s]=ImageFont.truetype(FB,s)
    return _fc[s]
CY=C['hi'];ACC=(255,210,60);RED=(255,70,70);WH=(250,250,250);INK=(20,16,30)
def ease(u):u=min(max(u,0),1);return u*u*(3-2*u)
def back(u):u=min(max(u,0),1);s=1.7;u-=1;return u*u*((s+1)*u+s)+1
def grad(c1,c2):
    a=np.linspace(0,1,H)[:,None,None];g=np.array(c1)*(1-a)+np.array(c2)*a;return Image.fromarray(np.uint8(np.repeat(g,W,1)))
BG={}
def bg(name,c1,c2):
    if name not in BG:BG[name]=grad(c1,c2)
    return BG[name].copy()
def ctext(d,s,y,size,fill=WH,x=None,stroke=6,sc=INK):
    f=F(size);w=d.textlength(s,font=f);d.text(((W-w)/2 if x is None else x-w/2,y),s,font=f,fill=fill,stroke_width=stroke,stroke_fill=sc)
def pop(d,s,y,size,u,fill=ACC,x=None,box=None):
    k=back(u*1.4) if u<1 else 1
    if k<=0.02:return
    if box: f=F(size*k);w=d.textlength(s,font=f);cx=W/2 if x is None else x;d.rounded_rectangle([cx-w/2-24,y-12,cx+w/2+24,y+size*k*1.15+8],16,fill=box)
    ctext(d,s,y,size*k,fill,x)
def pline(d,pts,u,fill,width):  # polyline drawn on progressively (u 0..1)
    if u<=0 or len(pts)<2:return None
    L=[math.dist(a,b) for a,b in zip(pts,pts[1:])];T=sum(L)*min(u,1);out=[pts[0]]
    for (a,b),l in zip(zip(pts,pts[1:]),L):
        if T>=l:out.append(b);T-=l
        else:out.append((a[0]+(b[0]-a[0])*T/max(l,1e-6),a[1]+(b[1]-a[1])*T/max(l,1e-6)));break
    d.line(out,fill=fill,width=width,joint='curve');return out
def arrow(d,p0,p1,u,fill,width=16,head=40):
    if u<=0:return
    x=p0[0]+(p1[0]-p0[0])*min(u,1);y=p0[1]+(p1[1]-p0[1])*min(u,1);d.line([p0,(x,y)],fill=fill,width=width)
    a=math.atan2(y-p0[1],x-p0[0]);d.polygon([(x+head*math.cos(a),y+head*math.sin(a)),(x+head*0.6*math.cos(a+2.2),y+head*0.6*math.sin(a+2.2)),(x+head*0.6*math.cos(a-2.2),y+head*0.6*math.sin(a-2.2))],fill=fill)
def counter(a,b,u,fmt='{:.0f}'):return fmt.format(a+(b-a)*ease(u))
# ---------- photo parallax (mask split: sky/background vs building/foreground) ----------
_ph={}
def photo(f):
    if f in _ph:return _ph[f]
    im=ImageOps.exif_transpose(Image.open(f)).convert('RGB');im=ImageOps.fit(im,(int(W*1.3),int(H*1.3)),Image.LANCZOS)
    a=np.asarray(im,np.float32);lum=a.mean(2);sky=(a[...,2]>a[...,0]+8)&(lum>90)
    yy=np.linspace(0,1,a.shape[0])[:,None]
    if sky.mean()<0.06: m=np.clip((yy-0.45)*4,0,1)*np.ones_like(lum)   # no sky: depth split by height
    else: m=1-sky.astype(np.float32)
    mask=Image.fromarray(np.uint8(m*255)).filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(6))
    bgim=im.filter(ImageFilter.GaussianBlur(5));bgim=Image.blend(bgim,Image.new('RGB',bgim.size,(30,20,60)),0.25)
    _ph[f]=(im,bgim,mask);return _ph[f]
def crop_at(im,z,cx,cy):
    bw,bh=W/z*1.0,H/z*1.0;x0=min(max(cx-bw/2,0),im.width-bw);y0=min(max(cy-bh/2,0),im.height-bh)
    return im.transform((W,H),Image.EXTENT,(x0,y0,x0+bw,y0+bh),Image.BILINEAR)
def S_photo(f,dirx=1):
    def s(im,d,u,t):
        fg,bgi,mk=photo(f);e=ease(u);cw,chh=fg.width/2,fg.height/2
        b=crop_at(bgi,1.0+0.04*e,cw-dirx*60*e,chh)
        fz=1.08+0.1*e;fx=cw+dirx*90*(e-0.5);fy=chh-40*e
        f2=crop_at(fg,fz,fx,fy);m2=crop_at(mk.convert('RGB'),fz,fx,fy).convert('L')
        sh=Image.new('RGB',(W,H),(0,0,0));b.paste(sh,(14,18),m2.point(lambda v:v*0.5))
        b.paste(f2,(0,0),m2);im.paste(b)
    return s
# ---------- reusable drawn assets ----------
def tower(d,x,base,h,u=1.0,col=(235,235,245),floors=59,crack=0.0,stilts=True,tilt=0.0):
    w=220;top=base-h;sh=int(h*0.13);bt=base-sh  # body top->bt, stilts below
    k=ease(u);cur=bt-(bt-top)*k
    def R(px,py):  # rotate around base center (tilt in deg)
        a=math.radians(tilt);dx,dy=px-x,py-base;return (x+dx*math.cos(a)-dy*math.sin(a),base+dx*math.sin(a)+dy*math.cos(a))
    P=lambda pts:[R(*p) for p in pts]
    d.polygon(P([(x-w/2,bt),(x+w/2,bt),(x+w/2,cur),(x-w/2,cur)]),fill=col,outline=INK)
    nf=int(floors*k)
    for i in range(1,nf):
        yy=bt-(bt-top)*i/floors;d.line(P([(x-w/2+6,yy),(x+w/2-6,yy)]),fill=(150,160,190),width=2)
    if k>0.98: d.polygon(P([(x-w/2,top),(x+w/2,top),(x+w/2,top-w*0.55)]),fill=(210,215,230),outline=INK)  # slanted crown
    if stilts:
        d.rectangle(P([(x-22,bt),(x+22,base)])[0:1]+P([(x+22,base)]),fill=(120,125,150))
        d.polygon(P([(x-20,bt),(x+20,bt),(x+20,base),(x-20,base)]),fill=(110,115,140))
    if crack>0:
        cy=bt-(bt-top)*0.45;pts=P([(x-60,cy-40),(x-25,cy),(x-40,cy+25),(x+10,cy+60)]);g=int(140+115*abs(math.sin(crack*8)))
        pline(d,pts,crack,(g,30,30),9)
    return top
def skyline(d,u,base,seed=3,col=(60,40,110)):
    r=np.random.default_rng(seed);x=0
    while x<W:
        w=int(r.integers(70,150));h=int(r.integers(250,700));k=ease(u*1.6-x/W*0.6)
        if k>0:d.rectangle([x,base-h*k,x+w-6,base],fill=col)
        x+=w
def padlock(d,cx,cy,u_close,s=1.0,col=ACC):
    sh=(1-ease(u_close))*90*s
    d.arc([cx-70*s,cy-150*s-sh,cx+70*s,cy-10*s-sh],180,360,fill=col,width=int(22*s))
    d.line([(cx-70*s,cy-80*s-sh),(cx-70*s,cy)],fill=col,width=int(22*s));d.line([(cx+70*s,cy-80*s),(cx+70*s,cy)],fill=col,width=int(22*s))
    d.rounded_rectangle([cx-110*s,cy-20*s,cx+110*s,cy+150*s],20,fill=col);d.ellipse([cx-18*s,cy+40*s,cx+18*s,cy+76*s],fill=INK);d.rectangle([cx-7*s,cy+60*s,cx+7*s,cy+110*s],fill=INK)
def stopwatch(d,cx,cy,r,ang):
    d.ellipse([cx-r,cy-r,cx+r,cy+r],fill=WH,outline=INK,width=10);d.rectangle([cx-18,cy-r-40,cx+18,cy-r],fill=INK)
    for k in range(12):a=k*math.pi/6;d.line([(cx+r*0.82*math.sin(a),cy-r*0.82*math.cos(a)),(cx+r*0.92*math.sin(a),cy-r*0.92*math.cos(a))],fill=INK,width=6)
    d.line([(cx,cy),(cx+r*0.75*math.sin(ang),cy-r*0.75*math.cos(ang))],fill=RED,width=10);d.ellipse([cx-12,cy-12,cx+12,cy+12],fill=INK)
def calendar(d,cx,cy,top,big,u):
    fl=ease(u*2);d.rounded_rectangle([cx-230,cy-200,cx+230,cy+230],30,fill=WH,outline=INK,width=8)
    d.rectangle([cx-230,cy-200,cx+230,cy-80],fill=RED)
    for k in (-120,120):d.rounded_rectangle([cx+k-14,cy-235,cx+k+14,cy-165],10,fill=INK)
    if fl<1: hh=(1-fl)*300;d.polygon([(cx-230,cy-80),(cx+230,cy-80),(cx+230,cy-80+hh),(cx-230,cy-80+hh)],fill=(220,220,230))
    ctext(d,top,cy-170,70,WH,cx,stroke=0);
    if fl>=1:
        bs=150 if len(big)<5 else 110
        while d.textlength(big,font=F(bs))>400 and bs>40:bs-=6
        ctext(d,big,cy-20,bs,INK,cx,stroke=0)
def joint(d,cx,cy,mode,u,t):
    d.line([(cx-330,cy+330),(cx+330,cy-330)],fill=(150,155,175),width=70);d.line([(cx-330,cy-330),(cx+330,cy+330)],fill=(130,135,160),width=70)
    d.rectangle([cx-110,cy-110,cx+110,cy+110],fill=(175,180,200),outline=INK,width=6)
    if mode=='weld':
        pts=[(cx-110,cy-110),(cx+110,cy-110),(cx+110,cy+110),(cx-110,cy+110),(cx-110,cy-110)];o=pline(d,pts,u,(255,170,40),14)
        if o and u<1:
            x,y=o[-1];r=np.random.default_rng(int(t*30))
            for _ in range(14):a=r.random()*6.28;l=r.random()*70;d.line([(x,y),(x+l*math.cos(a),y+l*math.sin(a))],fill=(255,240,150),width=4)
    else:
        nb=int(9*ease(u*1.2))
        for k in range(nb):
            bx=cx-70+(k%3)*70;by=cy-70+(k//3)*70;d.ellipse([bx-22,by-22,bx+22,by+22],fill=(70,75,90),outline=WH,width=4);d.line([(bx-10,by),(bx+10,by)],fill=WH,width=4)
def coins(d,x,base,n):
    for k in range(n):d.ellipse([x-80,base-k*26-30,x+80,base-k*26+10],fill=(255,205,60),outline=(150,110,20),width=5)
def plan(d,cx,cy,s=260,glow=0.0,shake=0.0,t=0):
    j=math.sin(t*40)*shake;d.rectangle([cx-s+j,cy-s,cx+s+j,cy+s],fill=(225,228,240),outline=INK,width=8)
    for k,(px,py) in enumerate([(0,-s),(s,0),(0,s),(-s,0)]):
        c=(255,int(150-90*glow),40) if glow>0 else (90,95,120);d.ellipse([cx+px-30+j,cy+py-30,cx+px+30+j,cy+py+30],fill=c)
def bubble(d,x,y,w,h,tail):
    d.rounded_rectangle([x,y,x+w,y+h],40,fill=WH,outline=INK,width=6);d.polygon([(tail[0],tail[1]),(x+w*0.3,y+h-4),(x+w*0.45,y+h-4)],fill=WH)
def ny_map(d,u,pin=0.0,rise=0.0):
    P=[(-74.015,40.700),(-74.019,40.710),(-74.013,40.730),(-74.010,40.755),(-73.995,40.775),(-73.975,40.800),(-73.958,40.830),(-73.940,40.855),(-73.925,40.875),(-73.910,40.873),(-73.930,40.835),(-73.935,40.800),(-73.942,40.776),(-73.958,40.757),(-73.972,40.745),(-73.973,40.727),(-73.975,40.712),(-73.998,40.707),(-74.015,40.700)]
    pr=lambda lo,la:(W/2+(lo+73.962)*0.758*6200,1330-(la-40.700)*6200)
    pts=[pr(*p) for p in P]
    if u>=1:d.polygon(pts,fill=(70,170,110))
    pline(d,pts,u,WH,10);ctext(d,'MANHATTAN',300,60,WH) if u>0.6 else None
    px,py=pr(-73.970,40.758)
    if pin>0:
        yy=py-60-300*(1-back(pin));d.ellipse([px-26,yy-26,px+26,yy+26],fill=RED,outline=WH,width=5);d.polygon([(px-20,yy+12),(px+20,yy+12),(px,yy+60)],fill=RED)
        pop(d,'MIDTOWN',py+30,46,pin,WH,px+150)
    if rise>0: tower(d,px-190,py-30,int(380),rise,floors=30)
def coast(d,u,track,trk_u,veer=0.0,t=0):
    pr=lambda la,lo:(60+(lo+82)*62,260+(45-la)*62)
    C1=[(45,-67),(43.6,-70.2),(42.4,-70.9),(41.7,-70.1),(41.4,-71.4),(41.0,-72.0),(40.6,-74.0),(39.4,-74.3),(38.9,-74.9),(38.3,-75.1),(37.0,-76.0),(35.2,-75.5),(34.2,-77.9),(32.8,-79.9),(31.0,-81.3),(30.0,-81.4)]
    pts=[pr(*p) for p in C1];land=pts+[pr(30,-90),pr(45,-90)]
    if u>=1:d.polygon(land,fill=(80,160,90))
    pline(d,pts,u,WH,8)
    nx,ny=pr(40.7,-74.0);d.ellipse([nx-18,ny-18,nx+18,ny+18],fill=RED,outline=WH,width=4);ctext(d,'NEW YORK',ny-90,44,WH,nx-120)
    hx,hy=pr(35.2,-75.5);ctext(d,'CAPE HATTERAS',hy-20,34,WH,hx-230,stroke=4) if u>=1 else None
    o=pline(d,[pr(*p) for p in track],trk_u,RED,12)
    if o:
        x,y=o[-1];a=t*6
        for k in range(3):
            d.arc([x-70+k*18,y-70+k*18,x+70-k*18,y+70-k*18],math.degrees(a)+k*60,math.degrees(a)+k*60+220,fill=WH,width=10)
        ctext(d,'ELLA',y+70,48,ACC,x)
# ---------- scenes: each fn(im,d,u,t) ----------
def S(fn,**kw):return lambda im,d,u,t:fn(im,d,u,t,**kw)
def sc_tower_build(im,d,u,t):
    im.paste(bg('sky1',(255,150,200),(90,60,190)));d=ImageDraw.Draw(im);skyline(d,u,1250);tower(d,560,1250,900,u*1.15)
    d.rectangle([0,1250,W,1400],fill=(40,30,70));stick.draw(d,120+620*u,1250,1.0,'walk',t,WH,'hardhat')
    ctext(d,counter(0,59,u*1.15)+' FLOORS',280,90,ACC)
def sc_crack(im,d,u,t):
    im.paste(bg('sky2',(120,70,200),(30,20,70)));d=ImageDraw.Draw(im);tower(d,620,1260,900,1,crack=min(1,u*1.6))
    pop(d,'HIDDEN FLAW',260,84,u*1.5,RED);d.rectangle([0,1260,W,1400],fill=(30,20,60));stick.draw(d,260,1260,1.1,stick.pose_mix('look_up','shush',ease(u*2-0.6)),t,WH,'hardhat')
def sc_padlock(im,d,u,t,fast=False):
    im.paste(bg('lock',(40,30,90),(150,50,120)));d=ImageDraw.Draw(im)
    d.rounded_rectangle([170,560,910,1060],20,fill=(240,230,200),outline=INK,width=8);d.polygon([(170,560),(540,820),(910,560)],outline=INK,fill=(225,215,185))
    pop(d,'SECRET',880,90,u*2,RED);padlock(d,540,600,u*2.2,0.9);stopwatch(d,860,360,130,t*(9 if fast else 2))
def sc_map(im,d,u,t):
    im.paste(bg('map',(40,90,170),(20,40,90)));d=ImageDraw.Draw(im);ny_map(d,u*2.2,pin=u*2.2-1.1,rise=u*2.2-1.5)
def sc_date_photo(im,d,u,t,f,label):
    S_photo(f)(im,d,u,t);d=ImageDraw.Draw(im);k=ease(u*2.5);x=-700+(W/2+700)*k
    d.rectangle([x-330,300,x+330,420],fill=RED);ctext(d,label,315,80,WH,x,stroke=0)
    stick.draw(d,180,1280,0.9,'point_up',t,WH,'hardhat')
def sc_stilts(im,d,u,t):
    im.paste(bg('stilt',(255,190,90),(220,90,120)));d=ImageDraw.Draw(im);x=540;base=1250;bt=base-260
    d.rectangle([x-340,300,x+340,bt],fill=(235,235,245),outline=INK,width=6)
    for i in range(1,14):d.line([(x-334,bt-i*48),(x+334,bt-i*48)],fill=(160,165,195),width=3)
    cl=ease(u*2);d.rectangle([x-340,bt,x+340,bt+(base-bt)*(1-cl)],fill=(200,200,215))  # cladding strips away
    for k,sx in enumerate([x-340+30,x+340-30]):d.rectangle([sx-6,bt,sx+6,base],outline=(255,255,255),width=2) if cl>0.5 else None
    for k,(sx,lab) in enumerate([(x-150,'1'),(x+150,'2')]):
        if cl>0.3:d.rectangle([sx-30,bt,sx+30,base],fill=(110,115,140))
    d.rectangle([0,base,W,1400],fill=(60,40,60))
    # plan inset: stilts at mid-sides, church at corner
    px,py,s=820,520,130;pu=ease(u*2-0.5)
    if pu>0:
        d.rectangle([px-s-20,py-s-20,px+s+20,py+s+20],fill=WH);d.rectangle([px-s,py-s,px+s,py+s],outline=INK,width=6)
        for k,(dx,dy) in enumerate([(0,-s),(s,0),(0,s),(-s,0)]):
            if pu>k*0.22:pul=1+0.25*math.sin(t*10+k);d.ellipse([px+dx-24*pul,py+dy-24*pul,px+dx+24*pul,py+dy+24*pul],fill=RED);ctext(d,str(k+1),py+dy-20,34,WH,px+dx,stroke=3)
        d.rectangle([px+s-60,py+s-60,px+s,py+s],fill=(150,120,200));ctext(d,'CHURCH',py+s+30,30,INK,px+s-30,stroke=0)
    pop(d,counter(0,4,u*2)+' STILTS',180,90,u*2,ACC)
    stick.draw(d,(x-330)+260*ease(u),base,0.9,'walk' if u<0.85 else 'point_up',t,WH,'hardhat')
def sc_desk(im,d,u,t):
    im.paste(bg('desk',(90,200,200),(30,80,140)));d=ImageDraw.Draw(im)
    d.rectangle([140,600,940,1150],fill=(245,245,255),outline=INK,width=8)
    for k in range(1,8):d.line([(140,600+k*68),(940,600+k*68)],fill=(200,210,240),width=2)
    pline(d,[(220,1100),(540,700),(860,1100)],u*1.3,(40,60,160),14);pline(d,[(220,700),(540,1100),(860,700)],u*1.3-0.4,(40,60,160),14)
    if u>0.5:d.ellipse([500,860,580,940],outline=RED,width=8);pop(d,'JOINT',950,50,(u-0.5)*3,RED,540)
    d.rectangle([80,1150,1000,1180],fill=(120,80,50));stick.draw(d,900,1400,0.9,'point_l',t,WH,'hardhat');ctext(d,'BRACE DESIGN',300,80,ACC)
def sc_joint(im,d,u,t,mode):
    im.paste(bg('j'+mode,(60,60,90),(140,70,40) if mode=='weld' else (40,80,110)));d=ImageDraw.Draw(im);joint(d,540,780,mode,u*1.3,t)
    pop(d,'WELDED' if mode=='weld' else 'BOLTS',230,100,u*1.8,(255,170,40) if mode=='weld' else ACC,box=INK)
    if mode=='bolt':
        coins(d,880,1300,max(1,int(10-8*ease(u))));pop(d,'$ SAVED',1330,60,u*2-0.8,(120,255,140),860)
def sc_shrug_cal(im,d,u,t,top,big,pose='shrug'):
    im.paste(bg('cal'+big,(250,120,90),(120,40,120)));d=ImageDraw.Draw(im);calendar(d,700,620,top,big,u)
    stick.draw(d,250,1280,1.1,stick.pose_mix('stand',pose,ease(u*2)),t,WH,'hardhat')
    if u>0.5 and int(t*12)%3: d.ellipse([200,700,300,800],fill=(255,240,120));d.rectangle([230,800,270,830],fill=(200,200,200))
    if pose=='shrug': ctext(d,'?',560+math.sin(t*8)*10,120,ACC,420)
def sc_student(im,d,u,t):
    im.paste(bg('lec',(120,200,120),(30,100,90)));d=ImageDraw.Draw(im)
    for k in range(3):d.rectangle([60+k*330,1180,330+k*330,1220],fill=(120,80,50))
    for k,x in enumerate([200,530,860]):stick.draw(d,x,1300,0.75,'point_up' if k==1 and u>0.15 else 'stand',t+k,WH)
    bk=ease(u*2-0.3)
    if bk>0:
        bubble(d,290,260,520,560,(530,960));cx,cy=550,560;s=120*bk;d.rectangle([cx-s,cy-s,cx+s,cy+s],outline=INK,width=8)
        arrow(d,(cx-300,cy),(cx-s-20,cy),u*2-0.8,(80,120,255),12,30);arrow(d,(cx-250,cy-250),(cx-s-10,cy-s-10),u*2-1.2,RED,14,36)
        pop(d,'DIAGONAL WIND?',870,52,u*2-1.3,ACC)
def sc_plan_wind(im,d,u,t):
    im.paste(bg('pw',(70,90,200),(20,30,80)));d=ImageDraw.Draw(im);cx,cy=540,780;plan(d,cx,cy,230)
    arrow(d,(540,200),(540,500),u*3,(120,200,255),18);ctext(d,'FACE',190,44,WH,690) if u>0.2 else None
    for k in range(3):arrow(d,(60+k*60,260-k*60+240),(280+k*60,520-k*60+240),u*2.2-0.7-k*0.12,RED,18)
    pop(d,'QUARTERING WIND',1160,64,u*2-1,ACC);ctext(d,'TOWER FROM ABOVE',1240,42,WH) if u>0.3 else None
def sc_recalc(im,d,u,t):
    im.paste(bg('rc',(255,200,80),(200,90,60)));d=ImageDraw.Draw(im);calendar(d,780,450,'JULY','24',u*1.5)
    eqs=['F = q · A · Cd','M = F · h / 2','σ = M / S','+40% wind load','check joints...'];y0=900-(t*120)%120
    d.rectangle([60,820,620,1180],fill=(250,250,240),outline=INK,width=6)
    for k,e in enumerate(eqs):
        yy=y0+k*65
        if 830<yy<1130:d.text((90,yy),e,font=F(42),fill=INK)
    d.rectangle([60,1180,1020,1210],fill=(110,70,40));stick.draw(d,820,1420,1.0,'type',t*3,WH,'hardhat')
def sc_load(im,d,u,t):
    im.paste(bg('ld',(120,40,60),(40,10,30)));d=ImageDraw.Draw(im);plan(d,540,820,220,glow=ease(u*2),shake=ease(u)*6,t=t)
    for k in range(3):arrow(d,(80+k*70,300+k*0),(300+k*70,520+k*0),u*3-k*0.2,RED,16)
    ctext(d,'+'+counter(0,160,u*1.3)+'%',1120,150,(255,150,40));ctext(d,'AT BOLTED JOINTS',1290,50,WH)
def sc_wind_side(im,d,u,t):
    im.paste(bg('ws',(110,140,190),(50,60,90)));d=ImageDraw.Draw(im);tl=7*ease(u*1.4)+math.sin(t*6)*1.2
    d.line([(560,1260),(560+900*math.sin(math.radians(9)),1260-900*math.cos(math.radians(9)))],fill=RED,width=4)
    tower(d,560,1260,880,1,tilt=tl);d.rectangle([0,1260,W,1400],fill=(40,40,60))
    for k in range(4):xs=-200+((t*900+k*300)%600);arrow(d,(xs-200,420+k*160),(xs+120,420+k*160),1,WH,12,30)
    pop(d,'70 MPH',200,100,u*2,ACC);d.rectangle([780,500,960,600],fill=(90,90,120),outline=WH,width=4);ctext(d,'DAMPER',520,34,WH,870,stroke=0)
    if u>0.4:d.line([(770,490),(970,610)],fill=RED,width=12);d.line([(770,610),(970,490)],fill=RED,width=12)
    ctext(d,'1978 ESTIMATE',1300,48,WH)
def sc_speedo(im,d,u,t):
    im.paste(bg('sp',(60,60,110),(20,20,40)));d=ImageDraw.Draw(im);cx,cy,r=540,860,360
    d.arc([cx-r,cy-r,cx+r,cy+r],150,390,fill=WH,width=30);v=70*ease(u*1.3)
    for k in range(0,101,10):a=math.radians(150+240*k/100);d.line([(cx+(r-50)*math.cos(a),cy+(r-50)*math.sin(a)),(cx+(r-15)*math.cos(a),cy+(r-15)*math.sin(a))],fill=WH,width=6)
    a=math.radians(150+240*v/100);d.line([(cx,cy),(cx+(r-70)*math.cos(a),cy+(r-70)*math.sin(a))],fill=RED,width=16);d.ellipse([cx-30,cy-30,cx+30,cy+30],fill=RED)
    ctext(d,f'{v:.0f} mph',cy+120,120,ACC);ctext(d,'COULD TOPPLE IT',300,70,WH)
def sc_wheel(im,d,u,t):
    im.paste(bg('wh',(255,120,160),(120,40,150)));d=ImageDraw.Draw(im);cx,cy,r=600,720,330;rot=720*(1-ease(u*1.3))
    for k in range(16):
        a0=rot+k*22.5-90;d.pieslice([cx-r,cy-r,cx+r,cy+r],a0,a0+22.5,fill=RED if k==0 and u>0.6 else ((250,250,250) if k%2 else (200,200,230)),outline=INK,width=3)
    d.polygon([(cx-30,cy-r-50),(cx+30,cy-r-50),(cx,cy-r+10)],fill=INK);ctext(d,'1 IN 16',180,110,ACC);pop(d,'ANY YEAR',1100,64,u*2-1.2,WH)
    stick.draw(d,170,1300,0.9,stick.pose_mix('stand','shock',ease(u*2.5-1.2)),t,WH,'hardhat')
def sc_kinetic(im,d,u,t):
    im.paste(bg('kin',(250,220,60),(250,120,40)));tmp=Image.new('RGBA',(W,H));dd=ImageDraw.Draw(tmp)
    for k,wd in enumerate(["BUT","HERE'S","THE","THING"]):
        uu=u*3-k*0.35
        if uu>0:sz=150*min(1,back(uu));w=dd.textlength(wd,font=F(sz));dd.text(((W-w)/2,500+k*190),wd,font=F(sz),fill=INK)
    ang=8*(1-ease(u*2.5));tmp=tmp.rotate(ang,center=(W/2,800));im.paste(tmp,(0,0),tmp)
def sc_night(im,d,u,t):
    e=ease(u);a=np.array([140,190,255])*(1-e)+np.array([15,15,50])*e;b=np.array([255,200,140])*(1-e)+np.array([40,30,80])*e
    im.paste(grad(tuple(a),tuple(b)));d=ImageDraw.Draw(im);sy=300+700*e;d.ellipse([150-70,sy-70,150+70,sy+70],fill=(255,220,80))
    my=900-650*e;d.ellipse([850-60,my-60,850+60,my+60],fill=(240,240,255));d.ellipse([870-60,my-75,870+40,my+45],fill=tuple(int(c) for c in a))
    skyline(d,1,1300,5,(30,25,55));top=tower(d,540,1300,850,1)
    for f in range(10):
        lit=(f==6) or e<0.5
        for c in range(4):d.rectangle([450+c*48,1100-f*60,480+c*48,1130-f*60],fill=(255,230,120) if lit else (50,50,70))
    pop(d,'THE FIX: AT NIGHT',220,76,u*2-0.8,ACC)
def sc_split(im,d,u,t):
    im.paste(bg('spl',(20,20,60),(60,30,90)));d=ImageDraw.Draw(im);d.rectangle([540,0,W,H],fill=(150,210,255))
    d.rectangle([536,0,544,H],fill=WH);ctext(d,'NIGHT',220,64,ACC,270);ctext(d,'DAY',220,64,INK,810,stroke=0)
    joint(d,270,700,'weld',(u*2)%1,t) if False else None
    d.rectangle([150,560,390,800],fill=(175,180,200),outline=WH,width=5);plates=int(1+ease(u)*8)
    o=pline(d,[(150,560),(390,560),(390,800),(150,800),(150,560)],(t*0.8)%1,(255,170,40),10)
    if o:
        x,y=o[-1];r=np.random.default_rng(int(t*30))
        for _ in range(10):a=r.random()*6.28;l=r.random()*60;d.line([(x,y),(x+l*math.cos(a),y+l*math.sin(a))],fill=(255,240,150),width=4)
    stick.draw(d,300,1250,0.85,'weld',t,WH,'mask');ctext(d,f'PLATES: {plates}',900,54,WH,270)
    for k,x in enumerate([700,900]):d.rectangle([x-90,1080,x+90,1110],fill=(120,80,50));stick.draw(d,x,1300,0.7,'type',t*3+k,INK)
    calendar(d,810,620,'1978','AUG',u*1.6) if True else None
def sc_hurr(im,d,u,t,phase):
    im.paste(bg('hu',(30,90,160),(10,30,80)));d=ImageDraw.Draw(im)
    tr=[(31,-75),(33,-75.3),(35.2,-74.8),(37.2,-74.2)]
    if phase=='in':coast(d,u*2.5,tr,ease(u*1.6-0.4),t=t);pop(d,'1 SEPT 1978',1340,70,u*2,ACC)
    else:
        coast(d,1,tr+[(38.0,-72.5),(38.4,-69.5),(38.0,-66.5)],0.55+0.45*ease(u*1.4),t=t);pop(d,'OUT TO SEA',1340,80,u*2-0.6,ACC)
        stick.draw(d,900,1250,0.8,stick.pose_mix('shock','cheer',ease(u*2)),t,WH,'hardhat')
def sc_storm_photo(im,d,u,t,f):
    S_photo(f,-1)(im,d,u,t);d=ImageDraw.Draw(im)
    d.rounded_rectangle([140,280,940,420],20,fill=INK);d.rectangle([160,300,160+760*0.5*ease(u*2),400],fill=(255,170,40) if int(t*4)%2 else (255,120,40))
    ctext(d,'50% REPAIRED',310,64,WH,stroke=4)
    for k in range(40):x=(k*97+t*900)%W;y=(k*53*7+t*1500)%H;d.line([(x,y),(x-20,y+60)],fill=(200,220,255),width=3)
def sc_paper(im,d,u,t):
    im.paste(bg('pp',(230,230,220),(150,150,140)));d=ImageDraw.Draw(im);d.ellipse([140,220,940,420],fill=(80,80,90))
    y=320+900*ease(u*1.2);d.rectangle([180,320,900,y],fill=(250,248,240),outline=INK,width=5)
    if y>520:ctext(d,'THE NEWS · 1995',360,62,INK,stroke=0);
    for k in range(6):
        yy=480+k*90
        if yy<y-40:d.rectangle([230,yy,850,yy+30],fill=(180,180,180))
    pop(d,'PUBLIC LEARNS',1300,80,u*2-1,RED)
def sc_years(im,d,u,t):
    im.paste(bg('yr',(100,60,200),(240,100,160)));d=ImageDraw.Draw(im);y=counter(1978,1995,u*1.3);ctext(d,y,450,190,WH)
    d.line([(120,820),(960,820)],fill=WH,width=8);pline(d,[(120,820),(960,820)],ease(u*1.3),ACC,20)
    for k,x in ((0,120),(1,960)):d.ellipse([x-20,800,x+20,840],fill=ACC);ctext(d,('1978','1995')[k],860,44,WH,x)
    pop(d,'17 YEARS',980,120,u*2-1.2,ACC);padlock(d,540,1130,1-ease(u*2-1.0),0.5)
def sc_clip(im,d,u,t):
    im.paste(bg('cl',(120,200,240),(60,90,160)));d=ImageDraw.Draw(im);joint(d,660,620,'weld',1,t)
    ctext(d,'?',360+math.sin(t*6)*15,200,ACC,660);d.rounded_rectangle([90,850,450,1260],16,fill=(190,140,80));d.rectangle([120,890,420,1230],fill=WH)
    ctext(d,'LATER',910,40,INK,270,stroke=0);ctext(d,'REASSESSMENT',960,32,INK,270,stroke=0)
    for k in range(5):d.rectangle([140,1030+k*36,140+240*ease(u*2-k*0.15),1046+k*36],fill=(150,150,150))
    stick.draw(d,740,1350,1.0,'think',t,WH,'hardhat')
def sc_maynot(im,d,u,t,f):
    S_photo(f)(im,d,u,t);d=ImageDraw.Draw(im);pop(d,'MAY NOT HAVE',260,80,u*2,WH,box=INK);pop(d,'BEEN NEEDED',380,80,u*2-0.3,ACC,box=INK)
def sc_recap1(im,d,u,t):
    if u<0.5: im.paste(bg('r1',(60,20,40),(20,10,20)));d=ImageDraw.Draw(im);tower(d,540,1300,900,1,crack=1 if int(t*8)%2 else 0.0001);pop(d,'A HIDDEN FLAW',250,80,u*4,RED)
    else:
        sc_night(im,d,0.6+0.4*(u-0.5)*2,t);d=ImageDraw.Draw(im);stick.draw(d,300,1300,0.7,'weld',t,WH,'mask')
def sc_recap2(im,d,u,t):
    im.paste(bg('r2',(255,170,90),(120,60,180)));d=ImageDraw.Draw(im)
    if u<0.45: padlock(d,540,700,1,1.0);pop(d,'17',760,150,u*4,INK,540)
    else:skyline(d,1,1300,7);tower(d,540,1300,900,1);pop(d,'STILL STANDING',230,76,(u-0.45)*3,ACC)
def sc_end(im,d,u,t):
    im.paste(bg('end',(90,60,200),(255,120,170)));d=ImageDraw.Draw(im);tower(d,700,1300,850,1);d.rectangle([0,1300,W,1400],fill=(40,30,70))
    ctext(d,C['name'],1480+0*u,56,CY) if t>TEND else None;ctext(d,C['handle'],1560,50,C['acc']) if t>TEND else None
    stick.draw(d,300,1300,1.1,'cheer',t,WH,'hardhat');k=1+0.08*math.sin(t*8);w=360*k;d.rounded_rectangle([540-w/2,280,540+w/2,280+110*k],50,fill=RED);ctext(d,'FOLLOW',300,64*k,WH,stroke=0)
IMG=lambda s:f'{SRC}/img/{K}_s{s}.jpg'
def sc_but_night(im,d,u,t):
    if u<0.45: sc_kinetic(im,d,u/0.45,t)
    else: sc_night(im,d,(u-0.45)/0.55,t)
def sc_idea(im,d,u,t):
    im.paste(bg('idea',(255,170,60),(160,50,110)));d=ImageDraw.Draw(im);stick.draw(d,540,1350,2.2,stick.pose_mix('shrug','think',ease(u*2)),t,WH,'hardhat')
    if u>0.4 and (int(t*14)%4 or u>0.75): d.ellipse([440,180,640,380],fill=(255,240,120),outline=INK,width=6);d.rectangle([500,380,580,440],fill=(190,190,190),outline=INK,width=4)
    ctext(d,'MAY 1978',1150-60*ease(u*2),70,ACC) if u>0.2 else None;ctext(d,'"I DIDN\'T KNOW"',1250,54,WH) if u>0.5 else None
def sc_calc(im,d,u,t):
    im.paste(bg('calc',(60,200,170),(20,80,110)));d=ImageDraw.Draw(im);d.rounded_rectangle([240,300,840,1200],40,fill=(50,55,70),outline=INK,width=8)
    d.rectangle([290,360,790,520],fill=(170,220,160));import random;r=random.Random(int(t*12));v=f"{r.random()*999:.2f}" if u<0.7 else "+40%"
    ctext(d,v,400,100,INK,540,stroke=0)
    for k in range(12):x=320+(k%3)*170;y=580+(k//3)*150;pr=(int(t*10)%12)==k;d.rounded_rectangle([x,y,x+130,y+110],18,fill=ACC if pr else (200,200,215))
    stick.draw(d,920,1350,0.8,'point_l',t,WH,'hardhat')
PLANS={'csf05':[
 [sc_tower_build,sc_crack],[sc_padlock],[sc_map,S(sc_date_photo,f=IMG(0),label='12 OCT 1977')],[sc_stilts,S(sc_date_photo,f=IMG(2),label='4 STILTS')],
 [sc_desk,S(sc_joint,mode='weld')],[S(sc_joint,mode='bolt'),S(sc_date_photo,f=IMG(1),label='TO SAVE MONEY')],[S(sc_shrug_cal,top='1978',big='MAY'),sc_idea],[sc_student,sc_plan_wind],[sc_recalc,sc_calc],[sc_load,S(sc_date_photo,f=IMG(3),label='+160% AT JOINTS')],
 [sc_wind_side,sc_speedo],[sc_wheel],[sc_but_night],'MERGE',[sc_split,S(sc_date_photo,f=IMG(8),label='STEEL PLATES')],[S(sc_hurr,phase='in'),S(sc_storm_photo,f=IMG(4)),S(sc_hurr,phase='out')],'MERGE',
 [S(sc_padlock,fast=True)],[sc_paper,sc_years],[sc_clip,S(sc_maynot,f=IMG(3))],[sc_recap1,sc_recap2],[sc_end]]}
USED={'csf05':[0,1,2,3,4,8]}
PLANS['csf05s']=[[sc_tower_build,sc_crack],[sc_map],[sc_stilts],[sc_desk,S(sc_joint,mode='weld')],[S(sc_joint,mode='bolt'),sc_idea],[sc_student,sc_plan_wind],[sc_recalc],[sc_load],[sc_wind_side,sc_speedo],[sc_wheel],[sc_but_night],[sc_split,sc_night],[S(sc_hurr,phase='in')],[S(sc_hurr,phase='out')],[sc_paper,sc_years],[sc_clip],[sc_recap2],[sc_end]]
USED['csf05s']=[]
# ---------- generic batch-1 scene library (plans come from JOB['scenes']: per line a list of [type,{kw}]) ----------
def _gbg(im,t,c1,c2,kind=0):
    im.paste(bg(f'g{c1}{c2}',c1,c2));d=ImageDraw.Draw(im);o=(t*40)%120;gc=tuple(min(255,int(x*1.25+10)) for x in c1)
    if kind==0:
        for x in range(-120,W+120,120):d.line([(x+o,0),(x+o,H)],fill=gc,width=2)
        for y in range(-120,H+120,120):d.line([(0,y+o),(W,y+o)],fill=gc,width=2)
    else:
        import random;r=random.Random(7)
        for k in range(40):
            x=(r.random()*W+t*r.uniform(10,60))%W;y=(r.random()*H-t*r.uniform(20,90))%H;s=r.uniform(3,9);d.ellipse([x-s,y-s,x+s,y+s],fill=gc)
    return d
def _dk(c,f=0.35):return tuple(int(x*f) for x in c)
def _lab(d,s,y,u,size=92,fill=None,box=True):
    label(d,s,y,u,min(size,96),fill=fill if fill else None,box=CY if box else 0)
def g_words(im,d,u,t,words=(),sub=''):
    d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.45));n=max(1,len(words));y0=520
    for i,w in enumerate(words):
        k=min(max((u-i*0.6/n)/0.25,0),1)
        if k>0:_lab(d,w,y0+i*170,k,110 if i==0 else 90,fill=INK if i%2==0 else WH,box=(i%2==0))
    if sub:ctext(d,sub,1250,48,C['acc'],stroke=4)
    stick.draw(d,880+30*math.sin(t*2),1360,0.55,'point_l',t,WH)
def _sg(u,a,b):return min(max((u-a)/max(b-a,1e-6),0),1)
def g_count(im,d,u,t,a=0.0,b=100.0,fmt='{:,.0f}',label='',unit=''):
    d=_gbg(im,t,_dk(CY,0.25),_dk(C['bg'],1.0));k=ease(_sg(u,0.02,0.35))
    v=fmt.format(a+(b-a)*k);s=v+unit;f=F(170)
    while d.textlength(s,font=f)>980:f=F(f.size-10)
    w=d.textlength(s,font=f);d.text(((W-w)/2,500),s,font=f,fill=WH,stroke_width=8,stroke_fill=INK)
    d.rounded_rectangle([120,800,960,880],30,outline=WH,width=6);d.rounded_rectangle([130,810,130+820*k,870],24,fill=CY)
    _lab(d,label,980,_sg(u,0.3,0.6),70)
    for j in range(3):stick.draw(d,300+j*240,1380,0.45,'look_up' if k<1 else 'shock',t+j,WH)
def g_date(im,d,u,t,top='',big=''):
    d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.5),1);calendar(d,540,760,top,big,_sg(u,0,0.8));stick.draw(d,540,1390,0.5,'point_up',t,WH)
def g_clock(im,d,u,t,label=''):
    d=_gbg(im,t,(10,10,16),_dk(CY,0.4),1);ang=ease(_sg(u,0,0.8))*math.pi*4+t*0.5;stopwatch(d,540,760,300,ang)
    _lab(d,label,1150,_sg(u,0.4,0.7),110)
def g_map(im,d,u,t,label=''):
    d=_gbg(im,t,(12,30,60),(5,12,30),0);import random;r=random.Random(len(label))
    pts=[(80+i*920/14,700+170*math.sin(i*0.7+r.random())+r.uniform(-40,40)) for i in range(15)];pline(d,pts,ease(_sg(u,0,0.5)),(200,220,240),10)
    p0=pts[3];p1=(700,1150);
    for q in range(12):
        k=_sg(u,0.4+q*0.03,0.43+q*0.03)
        if k>0:a=(p0[0]+(p1[0]-p0[0])*q/12,p0[1]+(p1[1]-p0[1])*q/12);d.ellipse([a[0]-9,a[1]-9,a[0]+9,a[1]+9],fill=CY)
    k=back(_sg(u,0.75,1));
    if k>0:d.ellipse([p1[0]-40*k,p1[1]-40*k,p1[0]+40*k,p1[1]+40*k],fill=RED,outline=WH,width=6)
    _lab(d,label,1260,_sg(u,0.7,0.95),80)
def g_gauge(im,d,u,t,label='',frac=0.8):
    d=_gbg(im,t,(6,10,20),_dk(CY,0.35),1);cx,cy,r=540,880,360;d.arc([cx-r,cy-r,cx+r,cy+r],180,360,fill=WH,width=24)
    for q in range(11):a=math.pi+q*math.pi/10;d.line([(cx+r*0.82*math.cos(a),cy+r*0.82*math.sin(a)),(cx+r*0.95*math.cos(a),cy+r*0.95*math.sin(a))],fill=WH,width=8)
    a=math.pi+math.pi*frac*ease(_sg(u,0,0.7))+0.03*math.sin(t*20);d.line([(cx,cy),(cx+r*0.78*math.cos(a),cy+r*0.78*math.sin(a))],fill=RED,width=18);d.ellipse([cx-30,cy-30,cx+30,cy+30],fill=WH)
    _lab(d,label,1020,_sg(u,0.35,0.7),100)
def g_bars(im,d,u,t,labels=('A','B'),vals=(1,2)):
    d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.3),0);mx=max(vals) or 1;n=len(vals);bw=760/n
    for i,(l,v) in enumerate(zip(labels,vals)):
        k=ease(_sg(u,0.1+i*0.15,0.6+i*0.15));x=160+i*bw;h=700*v/mx*k
        d.rectangle([x+20,1250-h,x+bw-20,1250],fill=CY if i==n-1 else C['acc'],outline=INK,width=6);ctext(d,l,1280,52,WH,x+bw/2,stroke=4)
    d.line([(120,1250),(960,1250)],fill=WH,width=8)
def g_timeline(im,d,u,t,ticks=('','')):
    d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.4),0);n=len(ticks);arrow(d,(100,900),(980,900),ease(_sg(u,0,0.5)),WH,14,46)
    for i,s in enumerate(ticks):
        k=_sg(u,0.05+i*0.3/n,0.15+i*0.3/n);x=180+i*(720/max(n-1,1))
        if k>0:d.ellipse([x-24,876,x+24,924],fill=CY);_lab(d,s,700 if i%2==0 else 980,k,64)
    stick.draw(d,180+720*ease(u),1500,0.55,'walk',t,WH)
def g_stick(im,d,u,t,poses=('stand','point_r'),label='',n=1):
    d=_gbg(im,t,_dk(CY,0.3),_dk(C['bg'],1.0),1);pa,pb=poses[0],poses[-1];k=ease(_sg(u,0.15,0.5))
    for j in range(n):
        x=540+(j-(n-1)/2)*300-(1-ease(_sg(u,0,0.25)))*700;stick.draw(d,x,1250,0.9 if n==1 else 0.7,stick.pose_mix(pa,pb,k),t+j,WH)
    if label and _sg(u,0.25,0.4)>=1:
        bubble(d,140,300,800,240,(540,600));sz=84
        while d.textlength(label,font=F(sz))>740 and sz>34:sz-=4
        ctext(d,label,420-sz/2,sz,INK,stroke=0)
def g_twist(im,d,u,t):
    c=(255,255,255) if int(t*12)%2 and u<0.25 else RED;im.paste(bg('tw',_dk(c,0.6),(10,0,0)));d=ImageDraw.Draw(im)
    j=8*math.sin(t*50)*(1-ease(u));pop(d,"BUT HERE'S",560+j,130,u*2,fill=WH);pop(d,'THE THING',760-j,150,max(0,u*2-0.3),fill=CY)
    stick.draw(d,540,1400,0.8,'shock',t,WH)
def g_vs(im,d,u,t,a='',b=''):
    d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.3),0);k=ease(_sg(u,0,0.4))
    d.rectangle([-540+540*k,300,530-540*(1-k),1300],fill=_dk(CY,0.6));d.rectangle([550+540*(1-k),300,W+540*(1-k),1300],fill=_dk(C['acc'],0.5))
    ctext(d,a,700,64,WH,270,stroke=5);ctext(d,b,700,64,WH,810,stroke=5);pop(d,'VS',740,100,_sg(u,0.35,0.7),fill=INK,box=WH)
def g_end(im,d,u,t):
    d=_gbg(im,t,_dk(CY,0.4),_dk(C['bg'],1.0),1);es=80
    while d.textlength(C['name'],font=F(es))>820 and es>40:es-=4
    pop(d,C['name'],620,es,u*1.5,fill=INK,box=CY);stick.draw(d,540,1350,0.9,'cheer',t,CY)

def g_turbine(im,d,u,t,label='',gust=True,n=1):
    d=_gbg(im,t,(90,160,220),(200,230,250),1);xs=[540] if n==1 else [200+i*680/(n-1) for i in range(n)]
    for x in xs:
        sc=1.0 if n==1 else 0.5;hub=(x,700 if n==1 else 900);tw=hub[1]+700*sc
        d.polygon([(x-14*sc,hub[1]),(x+14*sc,hub[1]),(x+26*sc,tw),(x-26*sc,tw)],fill=WH,outline=INK)
        a0=t*2.5*(0.3+ease(_sg(u,0,0.5)))
        for b in range(3):
            a=a0+b*2*math.pi/3;L=330*sc;p=(hub[0]+L*math.cos(a),hub[1]+L*math.sin(a));q=(hub[0]+40*sc*math.cos(a+1.4),hub[1]+40*sc*math.sin(a+1.4))
            d.polygon([hub,q,p],fill=WH,outline=INK);
        d.ellipse([hub[0]-26*sc,hub[1]-26*sc,hub[0]+26*sc,hub[1]+26*sc],fill=(200,200,210),outline=INK,width=4)
    d.rectangle([0,1420,W,H],fill=(70,140,70))
    if gust:
        for k in range(6):
            y=420+k*110;x0=((t*500+k*190)%(W+600))-400;d.arc([x0,y-30,x0+300,y+30],200,340,fill=(255,255,255),width=8)
    if label:_lab(d,label,1500,_sg(u,0.3,0.6),80)
def g_icesink(im,d,u,t,obj='ship',label='',tag=''):
    d=_gbg(im,t,(10,30,60),(2,6,18),1);k=ease(_sg(u,0,0.8))
    ox=540;oy=500+600*k
    if obj=='ship':
        d.polygon([(ox-260,oy),(ox+260,oy),(ox+190,oy+120),(ox-190,oy+120)],fill=(110,70,40),outline=INK,width=6)
        for m in (-120,0,120):d.line([(ox+m,oy),(ox+m,oy-300)],fill=(90,60,35),width=12)
    else:
        d.rounded_rectangle([ox-160,oy-50,ox+160,oy+50],40,fill=(250,200,40),outline=INK,width=6);d.polygon([(ox+160,oy),(ox+220,oy-50),(ox+220,oy+50)],fill=(80,80,90))
        if int(t*4)%2 and u<0.7:d.ellipse([ox-190,oy-20,ox-150,oy+20],fill=(255,255,200))
        for r in range(1,4):
            rr=(t*200+r*120)%420
            if u<0.6:d.arc([ox-rr,oy-rr,ox+rr,oy+rr],60,120,fill=(120,220,255),width=4)
    gap=max(0,1-ease(_sg(u,0.3,0.9)));w=420*gap
    d.polygon([(0,300),(540-w,300),(540-w-30,380),(0,380)],fill=(225,240,250),outline=(150,190,220))
    d.polygon([(W,300),(540+w,300),(540+w+30,380),(W,380)],fill=(225,240,250),outline=(150,190,220))
    if label:_lab(d,label,140,_sg(u,0.1,0.4),80)
    if tag and u>0.7:pop(d,tag,1350,110,(u-0.7)*3,fill=WH,box=(120,120,130))
def g_sonar(im,d,u,t,label=''):
    d=_gbg(im,t,(4,20,14),(0,6,4),0);cx,cy=540,1250
    for r in range(200,1100,200):d.arc([cx-r,cy-r,cx+r,cy+r],200,340,fill=(30,120,70),width=3)
    a=math.radians(200+(t*90)%140);d.line([(cx,cy),(cx+1100*math.cos(a),cy+1100*math.sin(a))],fill=(80,255,140),width=8)
    rr=(t*500)%1100;d.arc([cx-rr,cy-rr,cx+rr,cy+rr],200,340,fill=(120,255,170),width=6)
    k=ease(_sg(u,0.35,0.85))
    if k>0:
        c=tuple(int(40+200*k) if i==1 else int(40+60*k) for i in range(3));ox,oy=540,700
        d.polygon([(ox-260,oy),(ox+260,oy),(ox+190,oy+110),(ox-190,oy+110)],outline=c,width=8)
        for m in (-120,0,120):d.line([(ox+m,oy),(ox+m,oy-260*k)],fill=c,width=8)
    if label:_lab(d,label,1450,_sg(u,0.6,0.9),90)
def g_diagram(im,d,u,t,title='NOTE G',cols=('Op','Var','Result'),rows=4,label=''):
    d=_gbg(im,t,(240,230,205),(215,200,170),0);_lab(d,title,220,_sg(u,0,0.2),90)
    x0,y0,cw,rh=120,420,840/len(cols),110
    for i,cn in enumerate(cols):ctext(d,cn,y0+20,44,INK,x0+cw*(i+.5),stroke=0)
    d.rectangle([x0,y0,x0+840,y0+rh*(rows+1)],outline=INK,width=6)
    for r in range(1,rows+1):
        k=_sg(u,0.15+r*0.12,0.25+r*0.12);d.line([(x0,y0+rh*r),(x0+840,y0+rh*r)],fill=INK,width=3)
        if k>0:
            for i in range(len(cols)):
                v=['x','V%d'%(r+3),'B%d'%(2*r-1)][i%3] if i<3 else '';ctext(d,v,y0+rh*r+25,48,(120,40,30),x0+cw*(i+.5),stroke=0)
    for i in range(1,len(cols)):d.line([(x0+cw*i,y0),(x0+cw*i,y0+rh*(rows+1))],fill=INK,width=3)
    if label:_lab(d,label,1420,_sg(u,0.5,0.8),70)
def g_engine(im,d,u,t,label='ANALYTICAL ENGINE'):
    d=_gbg(im,t,(60,50,40),(20,16,12),0)
    for c in range(5):
        x=220+c*160
        for r in range(6):
            y=420+r*110;a=t*(1+c*0.3)*(1 if r%2 else -1);d.ellipse([x-48,y-48,x+48,y+48],fill=(190,150,70),outline=INK,width=4)
            for q in range(8):b=a+q*math.pi/4;d.line([(x+30*math.cos(b),y+30*math.sin(b)),(x+48*math.cos(b),y+48*math.sin(b))],fill=INK,width=5)
    d.rectangle([150,360,930,1100],outline=(220,190,110),width=8);_lab(d,label,1220,_sg(u,0.2,0.5),80)
def g_prices(im,d,u,t,a='£120',b='£180',label=''):
    d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.3),0);d.rounded_rectangle([200,300,880,620],30,fill=(230,225,215),outline=INK,width=6);ctext(d,'ROOM 204',420,70,INK,stroke=0)
    for j,(x,p) in enumerate(((330,a),(750,b))):
        stick.draw(d,x,1300,0.8,'stand' if j==0 else 'shrug',t+j,WH);k=_sg(u,0.3+j*0.25,0.5+j*0.25)
        if k>0:pop(d,p,800,110,k,fill=INK,x=x,box=CY if j==0 else RED)
    if label:_lab(d,label,1450,_sg(u,0.7,0.95),70)

import props_lib as PLB
paste=PLB.paste
def label(d,s,y,u,size=84,fill=None,box=None,maxw=900,maxl=3):
    """full phrase, wrapped to <=3 lines, pops in; never truncated"""
    if not s or u<=0:return y
    f,L=PLB.wrap(d,F,s,maxw,size,maxl);lh=f.size*1.18;k=back(min(u*1.6,1));box=CY if box is None else box
    for i,l in enumerate(L):
        w=d.textlength(l,font=f);yy=y+i*lh+(1-k)*40
        if box:d.rounded_rectangle([(W-w)/2-24,yy-10,(W+w)/2+24,yy+f.size+14],18,fill=box)
        d.text(((W-w)/2,yy),l,font=f,fill=fill or (INK if box else WH),stroke_width=0 if box else 5,stroke_fill=INK)
    return y+len(L)*lh
def _cnt(d,u,a,b,fmt,unit,y,size=170,pre=''):
    k=ease(_sg(u,0.02,0.35))   # holds the final value from 35% of the shot
    s=pre+fmt.format(a+(b-a)*k)+unit;f=F(size)
    while d.textlength(s,font=f)>960:f=F(f.size-8)
    w=d.textlength(s,font=f);d.text(((W-w)/2,y),s,font=f,fill=WH,stroke_width=8,stroke_fill=INK)
def g_prop(im,d,u,t,props=('📦',),anim='pop',label_='',count=None,sub='',tag='',pose=None,size=300,bgk=0,y=640):
    """props: 1-4 emoji drawn as the subject; anim pop|row|drop|grow|shrink|slide|stack|orbit|fall"""
    _pj=''.join(props);props=[c for j,c in enumerate(_pj) if (j==0 or _pj[j-1]!='\u200d') and os.path.exists(f'{HERE}/props/{ord(c):x}.png')];d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.4),bgk);n=len(props);sx=780/max(n,1)
    for i,e in enumerate(props):
        k=_sg(u,0.04+i*0.10,0.30+i*0.10);bob=10*math.sin(t*2.2+i)
        cx=540 if n==1 else 150+sx*(i+0.5);cy=y+bob;sz=size*(1 if n<=2 else 0.7)
        if k<=0:continue
        if anim=='pop':paste(im,e,cx,cy,sz*back(k))
        elif anim=='row':paste(im,e,cx,cy-(1-ease(k))*300,sz,alpha=ease(k))
        elif anim=='drop':paste(im,e,cx,cy-(1-ease(k))*900,sz,rot=(1-ease(k))*40)
        elif anim=='grow':paste(im,e,cx,cy,sz*(0.35+0.9*ease(_sg(u,0,0.8))))
        elif anim=='shrink':paste(im,e,cx,cy,sz*(1.25-0.75*ease(_sg(u,0.1,0.8))))
        elif anim=='slide':paste(im,e,cx+(1-ease(k))*(-900 if i%2==0 else 900),cy,sz)
        elif anim=='fall':paste(im,e,cx,cy+ease(_sg(u,0.2,1))*700,sz,rot=ease(_sg(u,0.2,1))*60,alpha=1-0.6*ease(_sg(u,0.5,1)))
        elif anim=='stack':
            for q in range(1+int(ease(_sg(u,0,0.6))*5)):paste(im,e,cx+(q%2)*30,cy+200-q*70,sz*0.6)
        elif anim=='orbit':a=t*1.5+i*2*math.pi/n;paste(im,e,540+260*math.cos(a),y+200*math.sin(a),sz*0.6)
    yy=y+size*0.62+40
    if count:_cnt(d,u,*count,y=yy);yy+=210
    if pose:stick.draw(d,880,1340,0.55,pose,t,WH)
    if label_:label(d,label_,max(yy,1000) if count else max(yy,980),_sg(u,0.12,0.4),84)
    if sub:label(d,sub,1290,_sg(u,0.3,0.55),56,fill=C['acc'],box=0)
    if tag and u>0.55:pop(d,tag,260,110,(u-0.55)*3,fill=WH,box=RED)
def g_pair(im,d,u,t,a=('',''),b=('',''),la='',lb='',label_='',ca=None,cb=None):
    """real two-sided comparison: each side = (emoji, caption) + optional counter (a,b,fmt,unit)"""
    d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.3),0)
    for j,(side,lab,cn) in enumerate(((a,la,ca),(b,lb,cb))):
        x=270+540*j;k=ease(_sg(u,0.05+0.25*j,0.35+0.25*j))
        if k<=0:continue
        d.rounded_rectangle([x-250,330+(1-k)*80,x+250,1200],30,fill=_dk(CY if j==0 else C['acc'],0.45),outline=WH,width=4)
        paste(im,side[0],x,560,230*back(k))
        if cn:
            kk=ease(_sg(u,0.1+0.25*j,0.4+0.25*j));s=cn[2].format(cn[0]+(cn[1]-cn[0])*kk)+cn[3];f=F(96)
            while d.textlength(s,font=f)>460:f=F(f.size-6)
            w=d.textlength(s,font=f);d.text((x-w/2,760),s,font=f,fill=WH,stroke_width=6,stroke_fill=INK)
        cap=side[1] or lab;f,L=PLB.wrap(d,F,cap,440,58,3,34)
        for i,l in enumerate(L):w=d.textlength(l,font=f);d.text((x-w/2,900+i*f.size*1.15),l,font=f,fill=WH,stroke_width=4,stroke_fill=INK)
    if label_:label(d,label_,1240,_sg(u,0.55,0.8),72)
def g_stack(im,d,u,t,parts=(('fuel',63),('duty',53)),total='',label_='',unit='p'):
    """stacked bar built part by part (e.g. a litre receipt); each part labelled with its final value"""
    d=_gbg(im,t,_dk(C['bg'],1.0),_dk(CY,0.35),0);tot=sum(v for _,v in parts);y=1250;cols=[CY,C['acc'],RED,(120,200,255),(200,160,255)]
    for i,(nm,v) in enumerate(parts):
        k=ease(_sg(u,0.05+i*0.5/len(parts),0.25+i*0.5/len(parts)));h=820*v/tot*k
        if k<=0:continue
        d.rectangle([300,y-h,620,y],fill=cols[i%5],outline=INK,width=6)
        if k>=1:d.text((650,y-h/2-30),f'{nm} {v:g}{unit}',font=F(56),fill=WH,stroke_width=4,stroke_fill=INK)
        y-=h
    if total:label(d,total,260,_sg(u,0.6,0.8),90)
    if label_:label(d,label_,1320,_sg(u,0.2,0.5),70)
def g_lean(im,d,u,t,a0=5.5,a1=5.5,weights=False,drill=False,label_=''):
    """leaning tower diagram (Pisa): tilt animates a0->a1 degrees, with lead weights / soil drills"""
    d=_gbg(im,t,(150,200,235),(230,240,250),1);ang=a0+(a1-a0)*ease(_sg(u,0.05,0.4));d.rectangle([0,1250,W,H],fill=(150,120,80))
    base=(540,1250);r=math.radians(ang);hgt=820;wd=170
    def P(x,y):return (base[0]+x*math.cos(r)+y*math.sin(r),base[1]+x*math.sin(r)-y*math.cos(r))
    for lv in range(8):
        y0,y1=lv*hgt/8,(lv+1)*hgt/8-6;ww=wd*(0.8 if lv==7 else 1)
        d.polygon([P(-ww,y0),P(ww,y0),P(ww,y1),P(-ww,y1)],fill=(245,240,225),outline=INK)
        for c in range(-2,3):d.line([P(c*ww/2.6,y0+10),P(c*ww/2.6,y1-6)],fill=(170,160,140),width=4)
    d.line([(540,300),(540,1250)],fill=RED,width=4)
    ctext(d,f'{ang:.2f}°'.replace('.00',''),330,110,WH)
    if weights:
        for q in range(int(ease(_sg(u,0.2,0.7))*6)):d.rectangle([150+q*40,1250-40-(q%2)*42,186+q*40,1250-(q%2)*42],fill=(90,90,100),outline=INK,width=3)
        ctext(d,'LEAD WEIGHTS',1300,52,WH,270)
    if drill:
        for q in range(3):
            k=ease(_sg(u,0.15+q*0.1,0.6+q*0.1));x=380-q*90;d.line([(x,1250),(x+60*k,1250+300*k)],fill=(60,60,70),width=14)
            if k>0.4:d.ellipse([x+60*k-25,1250+300*k-25,x+60*k+25,1250+300*k+25],fill=(110,80,50))
        ctext(d,'SOIL OUT',1300,52,WH,560)
    if label_:label(d,label_,170,_sg(u,0.15,0.4),72)
def _banned(name):
    def f(*a,**k):raise ValueError(f'scene type {name} banned by QC v3 (generic prop / text-only / stick-only)')
    return f
GEN=dict(prop=g_prop,pair=g_pair,stack=g_stack,lean=g_lean,turbine=g_turbine,icesink=g_icesink,sonar=g_sonar,diagram=g_diagram,engine=g_engine,prices=g_prices,words=g_words,count=g_count,date=g_date,clock=g_clock,map=g_map,gauge=g_gauge,bars=g_bars,timeline=g_timeline,stick=g_stick,twist=g_twist,vs=g_vs,end=g_end)
for _b in ('clock','gauge','vs','map','words','stick','twist'):GEN[_b]=_banned(_b)
if JOB and PK not in PLANS and JOB.get('scenes'):
    PLANS[PK]=[[S(GEN[ty],**kw) for ty,kw in line] for line in JOB['scenes']];USED[PK]=[]
# line spans from the script file line structure (sentences grouped per '>' line)
def script_lines():
    if JOB:return JOB['lines']
    src=open('/workspace/scripter/week2/city_skyline_files_week2.md').read() if ch=='csf' else ''
    blk=[b for b in src.split('\n## ') if b.startswith(f'CSF{n:02d} ')][0]
    return [re.sub(r'\*\*','',l[2:]).strip() for l in blk.splitlines() if l.startswith('> ')]
LN=script_lines();assert ' '.join(LN)==V['vo'];PL=PLANS[PK];assert len(PL)==len(LN),(len(PL),len(LN))
spans=[];wi=0
for l in LN:
    nw=len([w for w in l.split() if norm(w)]);spans.append((caps[wi][1],caps[wi+nw-1][2]));wi+=nw
SHOTS=[]  # (start,end,fn); 'MERGE' folds a short line into the previous line's shots; last line runs through the end card
G=[]
for li,sc in enumerate(PL):
    if sc=='MERGE':G[-1][1].append(li)
    else:G.append((sc,[li]))
for gi,(sc,lis) in enumerate(G):
    a=0 if gi==0 else spans[lis[0]][0]-0.08;b2=(spans[G[gi+1][1][0]][0]-0.08) if gi+1<len(G) else DUR
    D=b2-a;k=1 if gi+1==len(G) else min(len(sc),max(1,math.ceil(D/3.0-0.02)))
    for j in range(k):SHOTS.append((a+D*j/k,a+D*(j+1)/k,sc[j]))
CUTS=[s[0] for s in SHOTS[1:]];NSH=len(SHOTS)
# captions (same style as default path, moved low so the diagrams stay clear)
groups=[];cur=[]
for k,c in enumerate(caps):
    cur.append(c)
    if len(cur)==4 or k+1==len(caps) or c[0][-1] in '.,:;!?"':groups.append(cur);cur=[]
def draw_caps(im,t):
    c=[c for c in groups if c[0][1]-0.05<=t<=c[-1][2]+0.2]
    if not c:return
    c=c[-1];d=ImageDraw.Draw(im);txt=[w[0].strip('"') for w in c];f=F(70)
    lines=[list(zip(txt,c))] if d.textlength(' '.join(txt),font=f)<920 else [list(zip(txt[:2],c[:2])),list(zip(txt[2:],c[2:]))]
    y=1460;bw=max(d.textlength(' '.join(a for a,_ in l),font=f) for l in lines)
    d.rounded_rectangle([(W-bw)/2-30,y-20,(W+bw)/2+30,y+len(lines)*88+10],22,fill=C['bg'])
    for ln in lines:
        x=(W-d.textlength(' '.join(a for a,_ in ln),font=f))/2
        for a,w in ln:d.text((x,y),a,font=f,fill=CY if w[1]<=t+0.02 else (245,245,245));x+=d.textlength(a+' ',font=f)
        y+=88
def hook(im,t):
    d=ImageDraw.Draw(im);k=ease(t*4)*(1-ease((t-1.9)*4));
    if k<=0:return
    s=V['title'].upper();f=F(64);tw=d.textlength(s,font=f)
    if tw>980:f=F(64*980/tw);tw=d.textlength(s,font=f)
    y=90-120*(1-k);d.rectangle([(W-tw)/2-20,y-10,(W+tw)/2+20,y+84],fill=CY);d.text(((W-tw)/2,y),s,font=f,fill=(0,0,0))
def card(t):
    im=Image.new('RGB',(W,H),(14,15,18));d=ImageDraw.Draw(im);u=t-TEND
    for s,sz,y,col in [(C['name'],60,820,CY),('Follow for more.',70,920,(240,240,240)),(C['handle'],60,1040,C['acc'])]:
        ctext(d,s,y+40*(1-ease(u*3)),sz,col,stroke=0)
    stick.draw(d,540,1500,0.9,'cheer',t,CY);return im
# audio (same recipe as qrender: VO + generated bed ~-24 dB + whoosh per cut + hits; loud.py -> -14 LUFS / TP<=-1)
n_=int(DUR*sr);au=np.zeros(n_);s0=int(OFF*sr);au[s0:s0+len(vo)]+=vo;tt=np.arange(n_)/sr
notes=[220,277.2,329.6,440,329.6,277.2];bed=np.zeros(n_)
for q in range(int(DUR*4)):
    fq=notes[q%6]*(1 if (q//24)%2==0 else 0.89);a0=int(q*0.25*sr);seg=np.arange(min(int(0.6*sr),n_-a0))/sr;bed[a0:a0+len(seg)]+=np.sin(2*np.pi*fq*seg)*np.exp(-seg*5)
bed+=0.4*np.sin(2*np.pi*110*tt)*(0.5+0.5*np.sin(2*np.pi*0.1*tt));vr=np.sqrt((vo**2).mean());bed*=vr*10**(-24/20)/np.sqrt((bed**2).mean());au+=bed
for k,c in enumerate(CUTS):
    a0=int(max(0,c-0.15)*sr);m=int(0.3*sr);nz=np.random.default_rng(k).standard_normal(m);nz=np.convolve(nz,np.ones(30)/30,'same');seg=au[a0:a0+m];au[a0:a0+m]+=nz[:len(seg)]*np.hanning(m)[:len(seg)]*vr*0.3
for a0 in (0,int(TEND*sr)):
    m=int(0.5*sr);seg=np.arange(m)/sr;hit=np.sin(2*np.pi*60*seg*np.exp(-seg*3))*np.exp(-seg*8);au[a0:a0+m]+=hit[:len(au[a0:a0+m])]*vr*1.2
fd=np.minimum(1,np.minimum(np.arange(n_),n_-np.arange(n_))/(0.3*sr));KM=K+'_motion'
os.chdir(TMP);sf.write(f'{KM}_mix0.wav',au*fd*0.9,sr);subprocess.run([sys.executable,os.path.join(HERE,'loud.py'),KM],check=True)
TMPV=os.path.join(TMP,KM+'.mp4')
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-i',f'{KM}_mix.wav','-c:v','libx264','-preset','medium','-pix_fmt','yuv420p','-crf','20','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',TMPV],stdin=subprocess.PIPE)
thumbs=[];XF=0.12;prev=None
TEST=os.environ.get('MOTION_TEST')
FRS=[int((a+b)/2*FPS) for a,b,_ in SHOTS] if TEST else range(int(DUR*FPS))
for fr in FRS:
    t=fr/FPS;si=max(i for i,s in enumerate(SHOTS) if s[0]<=t+1e-9);a,b,fn=SHOTS[si]
    if True:
        im=Image.new('RGB',(W,H));u=(t-a)/(b-a);fn(im,ImageDraw.Draw(im),u,t);hook(im,t);draw_caps(im,t) if t<TEND else None
    if si>0 and t-a<XF and prev is not None: im=Image.blend(prev,im,(t-a)/XF)  # 4-frame dissolve
    if not TEST and abs(t-(a+b)/2)<0.5/FPS:thumbs.append(im.resize((270,480)))
    if t-a>=XF:prev=None
    if si+1<len(SHOTS) and SHOTS[si+1][0]-t<XF+1/FPS and prev is None:prev=im.copy()
    if TEST:thumbs.append(im.resize((270,480)));continue
    p.stdin.write(im.tobytes())
if TEST:
    p.kill();sh=Image.new('RGB',(8*270,math.ceil(len(thumbs)/8)*480))
    for i,th in enumerate(thumbs):sh.paste(th,((i%8)*270,(i//8)*480))
    sh.save(OUT.replace('.mp4','_test_contact.png'));print('TEST ok shots',len(SHOTS));sys.exit(0)
p.stdin.close();assert p.wait()==0
shutil.move(TMPV,OUT)
cols=8;rows=math.ceil(len(thumbs)/cols);sheet=Image.new('RGB',(cols*270,rows*480),(0,0,0))
for i,th in enumerate(thumbs):sheet.paste(th,((i%cols)*270,(i//cols)*480))
sheet.save(OUT.replace('.mp4','_contact.png'))
src=[l.split('\t') for l in open(f'{SRC}/sources.txt') if l.startswith(K+'\t')];used=[f'{K}_s{i}.jpg' for i in USED[PK]]
cred='\n'.join(f'- {r[1]}: "{r[5].split("File:")[-1].replace("_"," ")}" by {r[4]}, {r[3]}, via {r[2]}: {r[5]}' for r in src if r[1] in used)
desc=f"{V['title']}\n\n{V['tags']}\n\nSources: Wikipedia, \"Citicorp Center engineering crisis\" (https://en.wikipedia.org/wiki/Citicorp_Center_engineering_crisis); Joseph Morgenstern, \"The Fifty-Nine-Story Crisis\", The New Yorker, May 1995. The 1978 topple risk is the estimate made at the time.\n\nImages cropped and animated:\n{cred}\n\nDiagrams, maps, counters and the stick-figure character are original, drawn in code. Music bed and sound effects are generated in code. Contains AI-generated voice. Educational content."
if JOB and JOB.get('desc'):desc=JOB['desc']
if JOB and any(ty in ('prop','pair') for ln in JOB.get('scenes',[]) for ty,_ in ln) and 'Noto Emoji' not in desc:desc+="\n\nIcons: Noto Emoji by Google (SIL Open Font License 1.1)."
open(OUT.replace('.mp4','_description.txt'),'w').write(desc)
json.dump({'shots':[(round(a,2),round(b,2)) for a,b,_ in SHOTS],'render_s':round(time.time()-t0)},open(OUT.replace('.mp4','_shots.json'),'w'))
print(K,'motion render',round(time.time()-t0),'s dur',round(DUR,1),'shots',len(SHOTS))
