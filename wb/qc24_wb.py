"""Full whiteboard qc24. usage: python qc24_wb.py <dir with qc24_words.json,qc24_lines.json,qc24_vo.wav> <out.mp4> [stills]"""
import json,sys,time,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from wb import *
import math
D=sys.argv[1];OUT=sys.argv[2];STILL='stills' in sys.argv[3:]
words=json.load(open(f'{D}/qc24_words.json'));lines=json.load(open(f'{D}/qc24_lines.json'))
toks=' '.join(lines).split();assert len(toks)==len(words)
ENDS={i for i,t in enumerate(toks) if t[-1] in '.?!,:'}
def st(word,after=0.0):
    for w,s,e in words:
        if s>=after-0.01 and norm(w)==norm(word):return s-0.08
    raise ValueError(word)
R=(214,40,40);G=(40,160,70);B=(60,110,200);O=(232,96,52);Y=(246,196,58);GR=(120,180,80);P=(150,90,190)
S=[]
def sc(t0,items,focus=(540,900)):
    out=[]
    for x in items:
        if isinstance(x,tuple):
            x[0].key=x[1];x=x[0]
        if getattr(x,'is_text',False) and abs(x.y-T)<1: x.instant=True
        out.append(x)
    big=next((x for x in out if not getattr(x,'is_text',False)),None)
    if big is not None: big.quick=True
    S.append(dict(t0=t0,items=out,focus=focus))
def jar(cx,cy,col=(150,200,230),fill_to=0.5):
    top=cy-150+300*(1-fill_to)
    return Item(L((cx-120,cy-150),(cx-130,cy+150),(cx+130,cy+150),(cx+120,cy-150))+L((cx-145,cy-150),(cx+145,cy-150)),fill=[([(cx-122,top),(cx-127,cy+145),(cx+127,cy+145),(cx+122,top)],col)])
def cal(cx,cy,top,big,bs=150):
    it=Item(rect(cx-220,cy-220,440,440)+L((cx-220,cy-120),(cx+220,cy-120))+L((cx-120,cy-260),(cx-120,cy-185))+L((cx+120,cy-260),(cx+120,cy-185)),fill=[([(cx-216,cy-216),(cx+216,cy-216),(cx+216,cy-124),(cx-216,cy-124)],R)])
    return [it,text(top,cx,cy-170,72,(255,255,255)),text(big,cx,cy+50,bs)]
def bank(cx,cy):
    return Item(poly((cx-230,cy-120),(cx,cy-260),(cx+230,cy-120))+rect(cx-210,cy-120,420,40)+L((cx-160,cy-80),(cx-160,cy+150))+L((cx-55,cy-80),(cx-55,cy+150))+L((cx+55,cy-80),(cx+55,cy+150))+L((cx+160,cy-80),(cx+160,cy+150))+rect(cx-240,cy+150,480,50),fill=[([(cx-230,cy-120),(cx,cy-260),(cx+230,cy-120)],(200,200,210))])
def letter(cx,cy):
    return Item(rect(cx-200,cy-130,400,260)+L((cx-200,cy-130),(cx,cy+20),(cx+200,cy-130)),fill=[([(cx-196,cy-126),(cx+196,cy-126),(cx+196,cy+126),(cx-196,cy+126)],(255,250,220))])
def scale_(cx,cy):
    return Item(L((cx,cy-250),(cx,cy+200))+L((cx-120,cy+200),(cx+120,cy+200))+L((cx-260,cy-200),(cx+260,cy-200))+L((cx-260,cy-200),(cx-320,cy-40),(cx-200,cy-40),(cx-260,cy-200))+L((cx+260,cy-200),(cx+200,cy-40),(cx+320,cy-40),(cx+260,cy-200)))
# ---- distinct prop variants (v3: no repeated prop) ----
PINK=(247,170,190)
def piggy(cx,cy,v=0):
    f=-1 if v in (1,4) else 1; s=[1,0.9,0.85,0.7,0.75,1][v]; col=[PINK,(160,200,240),(150,215,150),(250,220,110),(200,170,230),(246,196,58)][v]
    X=lambda dx:cx+f*dx*s; Y=lambda dy:cy+dy*s
    st_=circ(cx,cy,230*s,0,360,ry=170*s)+circ(X(240),Y(-10),55*s,0,360,ry=65*s)+circ(X(228),Y(-12),8*s)+circ(X(252),Y(-12),8*s)
    st_+=L((X(-70),Y(-165)),(X(-25),Y(-240)),(X(10),Y(-163)))+circ(X(120),Y(-60),10*s)+L((X(-50),Y(-160)),(X(70),Y(-160)))
    if v==2: st_+=L((X(-160),Y(130)),(X(-170),Y(220)))+L((X(140),Y(130)),(X(150),Y(220)))+poly((X(-20),Y(-215)),(X(-90),Y(-260)),(X(-90),Y(-170)))+poly((X(-20),Y(-215)),(X(50),Y(-260)),(X(50),Y(-170)))
    else: st_+=L((X(-140),Y(130)),(X(-140),Y(230)))+L((X(120),Y(130)),(X(120),Y(230)))
    st_+=L((X(-230),Y(0)),(X(-270),Y(-30)),(X(-250),Y(-60)),(X(-280),Y(-80)))  # curly tail
    if v==3: st_+=circ(X(-60),Y(40),22*s)+circ(X(40),Y(80),18*s)+circ(X(-120),Y(-40),15*s)
    if v==4: st_+=circ(cx,Y(-250),40*s)+circ(cx,Y(-250),28*s)+L((cx,Y(-200)),(cx,Y(-175)))
    if v==5: st_+=L((X(-60),Y(-160)),(X(-60),Y(160)))+L((X(40),Y(-165)),(X(40),Y(165)))
    if v==1: st_+=L((X(-200),Y(60)),(X(-120),Y(150)))+L((X(160),Y(-120)),(X(200),Y(-150)))
    return Item(st_,fill=[(('circle',cx,cy,int(200*s)),col)])
def doc(cx,cy,v=0):
    W=170;Hh=230
    if v==0:  # gov page: header bar + dots
        st_=rect(cx-W,cy-Hh,2*W,2*Hh)+rect(cx-W,cy-Hh,2*W,70)+L((cx-110,cy-60),(cx+110,cy-60))+L((cx-110,cy),(cx+110,cy))+L((cx-110,cy+60),(cx+40,cy+60))+circ(cx-90,cy+150,25)+L((cx-50,cy+150),(cx+110,cy+150))
        return Item(st_,fill=[([(cx-W+4,cy-Hh+4),(cx+W-4,cy-Hh+4),(cx+W-4,cy-Hh+66),(cx-W+4,cy-Hh+66)],(190,215,245))])
    if v==1:  # payslip table
        st_=rect(cx-W,cy-Hh,2*W,2*Hh)+L((cx-W,cy-100),(cx+W,cy-100))+L((cx-W,cy-20),(cx+W,cy-20))+L((cx-W,cy+60),(cx+W,cy+60))+L((cx-W,cy+140),(cx+W,cy+140))+L((cx+20,cy-100),(cx+20,cy+230))
        return Item(st_,fill=[([(cx-W+4,cy+64),(cx+W-4,cy+64),(cx+W-4,cy+136),(cx-W+4,cy+136)],(255,236,150))])
    if v==2:  # tilted page, folded corner
        a=math.radians(-10);rot=lambda x,y:(cx+x*math.cos(a)-y*math.sin(a),cy+x*math.sin(a)+y*math.cos(a))
        P=[rot(-W,-Hh),rot(W-60,-Hh),rot(W,-Hh+60),rot(W,Hh),rot(-W,Hh)]
        st_=poly(*P)+L(rot(W-60,-Hh),rot(W-60,-Hh+60),rot(W,-Hh+60))
        for yy in (-110,-40,30,100): st_+=L(rot(-110,yy),rot(90,yy))
        return Item(st_,fill=[(P,(255,255,255))])
    if v==3:  # clipboard
        st_=rect(cx-W-20,cy-Hh-20,2*W+40,2*Hh+40)+rect(cx-70,cy-Hh-50,140,60)+L((cx-110,cy-80),(cx+110,cy-80))+L((cx-110,cy-10),(cx+110,cy-10))+L((cx-110,cy+60),(cx+50,cy+60))
        return Item(st_,fill=[([(cx-W-16,cy-Hh-16),(cx+W+16,cy-Hh-16),(cx+W+16,cy+Hh+16),(cx-W-16,cy+Hh+16)],(205,160,110)),([(cx-W+10,cy-Hh+20),(cx+W-10,cy-Hh+20),(cx+W-10,cy+Hh-10),(cx-W+10,cy+Hh-10)],(255,255,255))])
    # v4 scroll
    st_=rect(cx-W,cy-Hh+30,2*W,2*Hh-60)+circ(cx-W,cy-Hh+30,30,0,360,ry=30)+circ(cx+W,cy+Hh-30,30,0,360,ry=30)+L((cx-110,cy-120),(cx+110,cy-120))+L((cx-110,cy-50),(cx+110,cy-50))+L((cx-110,cy+20),(cx+60,cy+20))
    return Item(st_,fill=[([(cx-W+4,cy-Hh+34),(cx+W-4,cy-Hh+34),(cx+W-4,cy+Hh-34),(cx-W+4,cy+Hh-34)],(250,236,200))])
def bucket(cx,cy):
    return Item(L((cx-150,cy-150),(cx-110,cy+150),(cx+110,cy+150),(cx+150,cy-150))+circ(cx,cy-150,150,180,360,ry=40)+circ(cx,cy-150,150,0,180,ry=40)+circ(cx,cy-160,170,190,350,ry=150),fill=[([(cx-148,cy-145),(cx-112,cy+146),(cx+112,cy+146),(cx+148,cy-145)],(150,200,230))])
def spill(cx,cy):
    return Item(circ(cx,cy,35,0,360,ry=22)+circ(cx+60,cy+40,25,0,360,ry=16)+L((cx-30,cy-30),(cx-60,cy-90)),fill=[(('circle',cx,cy,30),(150,200,230))])
def deskcal(cx,cy,top,big):
    it=Item(poly((cx-240,cy+200),(cx-200,cy-180),(cx+200,cy-180),(cx+240,cy+200))+L((cx-205,cy-90),(cx+205,cy-90))+circ(cx-110,cy-185,18,0,360)+circ(cx,cy-185,18,0,360)+circ(cx+110,cy-185,18,0,360)+L((cx-230,cy+160),(cx+230,cy+160)),fill=[([(cx-197,cy-176),(cx+197,cy-176),(cx+202,cy-94),(cx-202,cy-94)],G)])
    return [it,text(top,cx,cy-135,62,(255,255,255)),text(big,cx,cy+40,140)]
def coin1p(cx,cy,r): c=coin(cx,cy,r,'1p'); c.fill=[(('circle',cx,cy,r),(205,125,70))]; return c
def note(cx,cy):
    return Item(rect(cx-160,cy-80,320,160)+rect(cx-170,cy-95,320,160)+circ(cx,cy-10,40)+L((cx-130,cy-50),(cx-90,cy-50)),fill=[([(cx-156,cy-76),(cx+156,cy-76),(cx+156,cy+76),(cx-156,cy+76)],(170,215,160))],text=None)
def moneybag(cx,cy):
    it=Item(circ(cx,cy+30,110,0,360,ry=100)+L((cx-45,cy-65),(cx-70,cy-130),(cx+70,cy-130),(cx+45,cy-65))+L((cx-55,cy-70),(cx+55,cy-70)),fill=[(('circle',cx,cy+30,100),(205,170,120))]);it.text=('£',cx,cy+35,90,INK);return it
def coin_edge(cx,cy,r):
    return Item(circ(cx,cy,r,0,360,ry=r*0.35)+L((cx-r,cy),(cx-r,cy+14))+L((cx+r,cy),(cx+r,cy+14))+circ(cx,cy+14,r,0,180,ry=r*0.35),fill=[(('circle',cx,cy,int(r*0.5)),(246,196,58))])
def wallet(cx,cy):
    return Item(rect(cx-140,cy-90,280,180)+rect(cx+40,cy-40,100,80)+circ(cx+90,cy,12)+L((cx-120,cy-90),(cx-80,cy-130),(cx+60,cy-130),(cx+80,cy-90)),fill=[([(cx-136,cy-86),(cx+136,cy-86),(cx+136,cy+86),(cx-136,cy+86)],(150,100,70))])
def coin_shine(cx,cy,r):
    c=coin(cx,cy,r); c.strokes+=L((cx+r*1.1,cy-r*0.9),(cx+r*1.35,cy-r*1.15))+L((cx+r*1.2,cy-r*0.5),(cx+r*1.5,cy-r*0.55))+L((cx+r*0.6,cy-r*1.2),(cx+r*0.7,cy-r*1.5)); return c
def receipt(cx,cy):
    return Item(poly((cx-90,cy-140),(cx+90,cy-140),(cx+90,cy+120),(cx+60,cy+140),(cx+30,cy+120),(cx,cy+140),(cx-30,cy+120),(cx-60,cy+140),(cx-90,cy+120))+L((cx-60,cy-90),(cx+60,cy-90))+L((cx-60,cy-40),(cx+60,cy-40))+L((cx-60,cy+40),(cx+60,cy+40)),fill=[([(cx-86,cy-136),(cx+86,cy-136),(cx+86,cy+116),(cx-86,cy+116)],(255,240,240))])
def coin_mark(cx,cy,r,mark,col):
    c=coin(cx,cy,r,mark); c.fill=[(('circle',cx,cy,r),col)]; return c
def chest(cx,cy):
    return Item(rect(cx-150,cy-40,300,150)+circ(cx,cy-40,150,180,360,ry=70)+rect(cx-25,cy-30,50,50),fill=[([(cx-146,cy-36),(cx+146,cy-36),(cx+146,cy+106),(cx-146,cy+106)],(170,110,60))])
def card(cx,cy):
    return Item(rect(cx-120,cy-75,240,150)+L((cx-120,cy-35),(cx+120,cy-35))+rect(cx-90,cy+5,50,35),fill=[([(cx-116,cy-71),(cx+116,cy-71),(cx+116,cy+71),(cx-116,cy+71)],(120,160,220))])
def briefcase(cx,cy):
    return Item(rect(cx-130,cy-70,260,170)+rect(cx-40,cy-110,80,40)+L((cx-130,cy),(cx+130,cy)),fill=[([(cx-126,cy-66),(cx+126,cy-66),(cx+126,cy+96),(cx-126,cy+96)],(120,80,50))])
def flag(cx,cy):
    return Item(L((cx,cy+120),(cx,cy-120))+poly((cx,cy-120),(cx+110,cy-90),(cx,cy-60)),fill=[([(cx,cy-118),(cx+106,cy-90),(cx,cy-62)],R)])

def hand(cx,cy):  # open empty palm, wobbly line art only
    st_=L((cx-100,cy+190),(cx-105,cy+40),(cx-150,cy-30),(cx-175,cy-70),(cx-150,cy-95),(cx-115,cy-60),(cx-80,cy-5))
    for x0,top in ((-80,-200),(-25,-240),(30,-228),(85,-185)):
        st_+=L((cx+x0,cy-5),(cx+x0+2,cy+top))+circ(cx+x0+26,cy+top,26,180,360)+L((cx+x0+52,cy+top),(cx+x0+52,cy-5))
    st_+=L((cx+137,cy-5),(cx+125,cy+190))+L((cx-60,cy+60),(cx-10,cy+90))+L((cx+20,cy+40),(cx+80,cy+70))+L((cx-100,cy+190),(cx+125,cy+190))
    st_+=L((cx-180,cy-190),(cx-215,cy-235))+L((cx+180,cy-190),(cx+215,cy-235))
    return Item(st_)
def purse(cx,cy):  # line-art coin purse with clasp and stitching
    return _sc(_purse(0,0),cx,cy,1.5)
def _purse(cx,cy):
    st_=L((cx-120,cy+10),(cx-100,cy+120),(cx+100,cy+120),(cx+120,cy+10))+circ(cx,cy+10,120,180,360,ry=55)
    st_+=circ(cx-22,cy-50,16,0,360)+circ(cx+22,cy-50,16,0,360)+L((cx-90,cy+40),(cx-60,cy+40))+L((cx-30,cy+40),(cx,cy+40))+L((cx+30,cy+40),(cx+60,cy+40))
    return Item(st_)
def halfcoin(cx,cy,r):  # coin snapped in two, line art
    z=[(0,-r),(12,-r*0.5),(-10,-r*0.1),(10,r*0.35),(0,r)]
    st_=circ(cx-15,cy,r,90,270)+L(*[(cx-15+a,cy+b) for a,b in z])+circ(cx+25,cy+10,r,-90,90)+L(*[(cx+25+a,cy+10+b) for a,b in z])
    st_+=L((cx+r+50,cy-40),(cx+r+90,cy-60))+L((cx+r+55,cy+10),(cx+r+100,cy+10))+L((cx-r-50,cy-40),(cx-r-90,cy-60))
    return Item(st_)
def _sc(it,cx,cy,k):
    it.strokes=[[(cx+x*k,cy+y*k) for x,y in st] for st in it.strokes];return it
def padlock(cx,cy):
    return Item(rect(cx-90,cy-20,180,150)+circ(cx,cy-20,60,180,360,ry=80)+circ(cx,cy+40,14,0,360)+L((cx,cy+54),(cx,cy+90)))
def bills(cx,cy,n):
    st_=[]
    for i in range(n): st_+=rect(cx-90+i*6,cy-40-i*34,180,30)
    return Item(st_)

def sparkle(cx,cy,r=40,col=Y):
    return Item(L((cx-r,cy),(cx+r,cy))+L((cx,cy-r),(cx,cy+r))+L((cx-r*0.5,cy-r*0.5),(cx+r*0.5,cy+r*0.5)),col=col,width=8)
def goldbars(cx,cy):
    sh=[];st_=[]
    for dx,dy in ((-70,0),(70,0),(0,-55)):
        q=[(cx+dx-60,cy+dy+25),(cx+dx+60,cy+dy+25),(cx+dx+40,cy+dy-25),(cx+dx-40,cy+dy-25)]
        st_+=poly(*q);sh.append((q,(240,190,60)))
    return Item(st_,fill=sh)
def payslip(cx,cy):
    st_=rect(cx-110,cy-140,220,280)+L((cx-80,cy-90),(cx+60,cy-90))+L((cx-80,cy-40),(cx+80,cy-40))+L((cx-80,cy+10),(cx+40,cy+10))+L((cx+10,cy+80),(cx+80,cy+80))
    return Item(st_,fill=[([(cx-106,cy-136),(cx+106,cy-136),(cx+106,cy+136),(cx-106,cy+136)],(235,240,250))])
def stamp(cx,cy):
    st_=rect(cx-130,cy+40,260,60)+poly((cx-50,cy+40),(cx-35,cy-60),(cx+35,cy-60),(cx+50,cy+40))+circ(cx,cy-110,55)
    return Item(st_,fill=[(('circle',cx,cy-110,55),(214,40,40)),([(cx-126,cy+44),(cx+126,cy+44),(cx+126,cy+96),(cx-126,cy+96)],(120,80,50))])
def key_(cx,cy):
    return Item(circ(cx-90,cy,50,0,360)+L((cx-40,cy),(cx+120,cy))+L((cx+80,cy),(cx+80,cy+40))+L((cx+110,cy),(cx+110,cy+30)),col=(200,150,30),width=12)
def shield(cx,cy):
    q=[(cx-110,cy-120),(cx+110,cy-120),(cx+100,cy+20),(cx,cy+140),(cx-100,cy+20)]
    return Item(poly(*q),fill=[(q,(150,215,150))])
def magnifier(cx,cy):
    return Item(circ(cx,cy,80,0,360)+L((cx+57,cy+57),(cx+150,cy+150)),fill=[(('circle',cx,cy,80),(220,235,250))])
def _bbox(it):
    xs=[p[0] for s_ in it.strokes for p in s_];ys=[p[1] for s_ in it.strokes for p in s_]
    return min(xs),min(ys),max(xs),max(ys)
def _scale(it,k,ax,ay,bx,by):
    f=lambda x,y:(bx+(x-ax)*k,by+(y-ay)*k)
    it.strokes=[[f(*p) for p in s_] for s_ in it.strokes]
    nf=[]
    for shp,col in it.fill or []:
        if shp[0]=='circle':x,y=f(shp[1],shp[2]);nf.append((('circle',x,y,shp[3]*k),col))
        else:nf.append(([f(*p) for p in shp],col))
    if it.fill:it.fill=nf
    it.width=min(18,max(it.width,it.width*k**0.5))
    if hasattr(it,'y'):it.y=f(0,it.y)[1]
def _area(b):return (b[2]-b[0])*(b[3]-b[1])
def _inside(b,m):cx,cy=(b[0]+b[2])/2,(b[1]+b[3])/2;return m[0]<=cx<=m[2] and m[1]<=cy<=m[3]
def _fit(items,box,kmax):
    bb=[_bbox(i) for i in items];x0=min(b[0] for b in bb);y0=min(b[1] for b in bb);x1=max(b[2] for b in bb);y1=max(b[3] for b in bb)
    k=min((box[2]-box[0])/max(1,x1-x0),(box[3]-box[1])/max(1,y1-y0),kmax)
    for i in items:_scale(i,k,(x0+x1)/2,(y0+y1)/2,(box[0]+box[2])/2,(box[1]+box[3])/2)
def enlarge():
    for n,s_ in enumerate(S):
        its=s_['items']
        hd=[i for i in its if getattr(i,'is_text',False) and i.y<T+200]
        top=max([_bbox(i)[3] for i in hd]+[200])+60
        props=[i for i in its if not getattr(i,'is_text',False) and i.strokes]
        if s_.get('keep') and props:
            ps=sorted(props,key=lambda i:_area(_bbox(i)))[1:];s_['items']=[i for i in its if i not in ps];its=s_['items']
        if n==0 or not props or s_.get('keep'):
            body=[i for i in its if i not in hd];_fit(body,(105,top,975,1480),2.3);continue
        np_=[i for i in props if not getattr(i,'person',False)] or props
        main=max(np_,key=lambda i:_area(_bbox(i)));mb=_bbox(main)
        grp=[main]+[i for i in its if i is not main and i not in hd and _inside(_bbox(i),mb)]
        rest=[i for i in its if i not in grp and i not in hd]
        others=[i for i in rest if not getattr(i,'is_text',False)]
        acc=min(others,key=lambda i:_area(_bbox(i))) if others else None
        txt=[i for i in rest if getattr(i,'is_text',False)]
        s_['items']=[i for i in its if i in grp or i in hd or i in txt or i is acc]
        for i in s_['items']:i.quick=False
        main.quick=True
        bot=1480 if not (txt or acc) else 1200
        _fit(grp,(105,top,975,bot),3.5)
        if acc is not None:_fit([acc],(105,1220,300,1480),1.0)
        if txt:
            x0=320 if acc is not None else 105;h=(1480-1220)/len(txt)
            for j,t_ in enumerate(txt):
                b=_bbox(t_);k=min(1.0,(975-x0)/(b[2]-b[0]),(h-10)/(b[3]-b[1]))
                _scale(t_,k,(b[0]+b[2])/2,(b[1]+b[3])/2,(x0+975)/2,1220+h*(j+0.5))
        s_['focus']=(540,(top+bot)/2)
PX=290;PY=1250;SC=2.1   # big character, left
T=380
# 0 Three people earn the same interest on their savings
sc(0.0,[(person(200,1180,1.25,O),'three'),(person(540,1180,1.25,B),'people'),(person(880,1180,1.25,GR),'earn'),(text('SAME INTEREST',540,T,110),'interest'),
        (coin(200,1440,55),'savings'),(coin(540,1440,55),'savings'),(coin(880,1440,55),'savings')],focus=(540,1000))
# 1 One of them can't keep a single penny of it tax-free.
sc(st('one'),[(person(PX,PY,SC,B,'sad'),'one'),(text("CAN'T KEEP IT",540,T,115,R),'keep'),(coin1p(780,860,90),'penny'),(cross(780,860,130),'penny'),(text('A SINGLE PENNY',780,1150,70),'penny')])
sc(st('it',5.0),[(stamp(400,1050),'tax-free'),(text('NOT TAX-FREE',540,T,115,R),'tax-free'),(text('TAX-FREE',400,1250,70,G),'tax-free'),(text('WHY?',820,900,170,R),'why')])
# 2-3 Why? It's called the Personal Savings Allowance.
sc(st('called'),[(piggy(540,1000,0),'personal'),(text('PERSONAL SAVINGS',540,T,100),'savings'),(text('ALLOWANCE',540,T+130,125,G),'allowance')])
# 4 It started in April twenty sixteen.
sc(st('started'),cal(540,950,'APRIL','2016',170)); S[-1]['items'][0].key='started';S[-1]['items'][1].key='april';S[-1]['items'][2].key='sixteen'
S[-1]['items'].append(text('SINCE',540,T,120));S[-1]['items'][-1].key='started'
S[-1]['items']+= [person(880,1400,0.9,Y,'smile','up'),flag(910,1150)];S[-1]['items'][-2].key='twenty';S[-1]['items'][-1].key='sixteen'
# 5 Your allowance depends on your income tax band. (labels drawn with the steps)
stp=Item(L((100,1350),(100,1180),(400,1180),(400,980),(700,980),(700,780),(980,780),(980,1350),(100,1350)))
sc(st('allowance',11.8),[(text('YOUR TAX BAND',540,T,115),'depends'),(stp,'income'),(text('BASIC',250,1270,64),'income'),(text('HIGHER',550,1080,64),'tax'),(text('ADDITIONAL',840,880,54),'tax'),(person(250,1150,0.7,GR),'depends'),(arrow((330,1100),(520,930),R),'income')],focus=(540,1000))
S[-1]['items'][-1].key='tax'
# 6 Basic-rate payers get up to one thousand pounds of interest tax-free.
sc(st('basic-rate'),[(person(PX,PY,SC,GR),'basic-rate'),(text('BASIC RATE',540,T,115),'payers'),(arrow((560,1000),(760,880),G),'get'),(text('UP TO',780,800,110,G),'to')])
sc(16.9,[(note(780,830),'pounds'),(text('£1,000',780,1060,140,G),'pounds'),(person(250,1300,1.3,GR,'smile','up'),'interest')])
# 7 Higher-rate payers get five hundred.
sc(st('higher-rate'),[(person(PX,PY,SC,B),'higher-rate'),(text('HIGHER RATE',540,T,115),'payers'),(moneybag(780,850),'five'),(text('£500',780,1080,150,(220,140,20)),'hundred')])
# 8 Additional-rate payers get nothing.
sc(st('additional-rate'),[(person(PX,PY,SC,P,'sad'),'additional-rate'),(text('ADDITIONAL RATE',540,T,100),'payers'),(hand(780,920),'nothing'),(text('NOTHING',780,1220,90,R),'nothing')])
# 9 And for 2026 to 2027, those limits are unchanged.
sc(st('and',23.5),deskcal(540,950,'TAX YEAR','26/27'))
k=S[-1]['items'];k[0].key='for';k[1].key='twenty-six';k[2].key='twenty-seven'
sc(st('those',23.5),[(padlock(540,950),'limits'),(text('SAME',540,T,130,G),'those'),(text('LIMITS UNCHANGED',540,1330,100),'unchanged'),(key_(300,1180),'unchanged')])
# 10 Go over, and you pay tax on the extra.
sc(st('go'),[(jar(380,1100,fill_to=0.95),'go'),(text('GO OVER',540,T,130,R),'go'),(coin_edge(380,900,50),'over'),(coin_edge(450,810,50),'over'),(coin_edge(340,730,50),'over'),(arrow((490,760),(650,650),R),'pay'),(text('TAX',780,600,120,R),'tax'),(text('ON THE EXTRA',540,1400,100),'extra')])
# 11 Gov.uk's example: thirteen hundred pounds of interest, basic rate.
sc(st("gov.uk's"),[(doc(330,950,0),"gov.uk's"),(text('GOV.UK',330,800,60,B),"gov.uk's"),(text('EXAMPLE',540,T,125,B),'example'),(wallet(780,860),'thirteen'),(text('£1,300',780,1080,120),'hundred')])
sc(32.95,[(coin_shine(540,820,150),'of'),(text('£1,300',540,1080,160),'of'),(text('INTEREST',540,1220,95),'interest'),(text('BASIC RATE',540,T,110,G),'basic'),(person(170,1330,1.0,GR),'rate')])
# 12 Three hundred is over the limit. Taxed at 20%, that's £60.
sc(st('three',35),[(bucket(540,1130),'three'),(spill(330,1320),'over'),(spill(760,1330),'over'),(Item(L((300,980),(780,980)),col=R,width=8),'limit'),(text('£300 OVER',540,T,130,R),'over'),(text('£1,000 LIMIT',540,880,80),'limit'),(text('TAXED',540,1380,110,R),'taxed')])
sc(st('at',37.5),[(text('£300',290,750,130),'twenty'),(text('x 20%',760,750,130,R),'percent'),(arrow((540,880),(540,1060)),"that's"),(text('£60 TAX',540,1200,180,R),'pounds'),(receipt(880,1420),'pounds')]);S[-1]['keep']=True
# 13-14 Watch out, though. Add your interest to your other income to find your band.
sc(st('watch'),[(person(PX,PY,SC,O,'flat','up'),'watch'),(text('WATCH OUT!',540,T,130,R),'though'),(text('ADD IT UP',780,800,100),'add'),(purse(780,1050),'interest'),(coin(700,1250,40),'interest'),(coin(860,1260,40),'interest')])
sc(st('to',42.5),[(coin_mark(230,900,90,'%',(150,215,150)),'your'),(text('+',420,900,160),'other'),(doc(700,920,1),'income'),(text('INCOME',700,800,60),'income'),(text('= YOUR BAND',540,1300,120,B),'band'),(text('INTEREST + INCOME',540,T,100),'find')])
# 15 Your interest counts as income, so it can tip you into a higher band.
sc(st('your',45.1),[(coin_mark(260,900,110,'£',(200,200,210)),'interest'),(arrow((400,900),(560,900)),'counts'),(doc(780,920,2),'as'),(text('INCOME',780,800,60),'income'),(text('COUNTS AS INCOME',540,T,105),'income')])
stp2=Item(L((160,1350),(160,1150),(540,1150),(540,900),(900,900),(900,1350),(160,1350)))
sc(st('so',46.5),[(stp2,'tip'),(text('BASIC',340,1260,70),'tip'),(text('HIGHER',720,1010,60,R),'higher'),(arrow((340,1120),(660,840),R),'higher'),(text('TIPPED UP',540,T,120,R),'band')],focus=(540,1050))
# 16-17 But here's the thing. There's a second allowance most people never hear of.
sc(st('but',49.5),[(person(PX,PY,SC,B,'smile','up'),'but'),(text('BUT...',760,700,150,B),'thing'),(piggy(730,1150,1),'second')])
sc(51.75,[(piggy(380,1000,2),'allowance'),(piggy(760,700,3),'allowance'),(text('A 2ND ALLOWANCE',540,T,105,G),'allowance'),(text('LITTLE KNOWN',540,1400,95),'never')])
# 18 If your other taxable income is under £17,570, up to £5,000 of interest can be taxed at zero.
sc(st('if',54.0),[(doc(540,980,3),'income'),(briefcase(860,1250),'taxable'),(text('INCOME',540,860,60),'income'),(text('OTHER INCOME',540,T,110),'taxable'),(text('UNDER',540,T+140,90,B),'under'),(person(170,1330,1.0,O),'other')])
sc(st('seventeen'),[(text('INCOME LIMIT',540,T,110),'seventeen'),(stp2_:=Item(L((120,1000),(960,1000)),width=14,col=B),'thousand'),(text('£17,570',540,880,170,B),'seventy'),(person(300,1350,1.2,GR),'five'),(arrow((300,1180),(300,1060),G),'hundred'),(text('UNDER IT?',760,1250,100,G),'pounds'),(payslip(800,1450),'five')])
sc(59.45,[(chest(540,1000),'five'),(goldbars(540,1210),'thousand'),(sparkle(330,830),'pounds'),(sparkle(760,800,30),'pounds'),(text('£5,000',540,1380,130,G),'pounds'),(text('UP TO',540,T,110),'up')])
sc(st('interest',61.3),[(text('0%',400,1000,300,G),'zero'),(text('TAX ON INTEREST',540,T,105),'taxed'),(tick(800,1000,110),'zero'),(shield(800,1300),'can'),(text('TAXED AT ZERO',540,1450,80),'zero')])
# 19 Every pound you earn above £12,570 shrinks it by a pound.
sc(st('every'),[(person(PX,PY,SC,GR),'every'),(coin_mark(780,850,90,'£',(200,200,210)),'pound'),(text('EARN ABOVE',540,T,115),'above')])
sc(65.55,[(text('£12,570',540,700,190),'seventy'),(text('£1 MORE =',380,1000,95),'shrinks'),(text('£1 LESS',780,1000,95,R),'pound'),(halfcoin(380,1200,60),'shrinks'),(piggy(780,1260,4),'by')]);S[-1]['keep']=True
# 20 ISA interest doesn't usually count at all.
sc(st('isa'),[(piggy(540,1000,5),'isa'),(text('ISA',540,1000,120),'isa'),(text('ISA INTEREST',540,T,115),'interest'),(text("DOESN'T COUNT",540,1420,100,G),'count'),(magnifier(860,800),'usually')])
# 21 And banks report your interest, so HMRC may send you a calculation.
sc(st('and',71.8),[(bank(540,1050),'banks'),(arrow((540,760),(540,620),B),'report'),(text('BANKS REPORT IT',540,T,105),'interest'),(card(220,1320),'your')])
sc(73.85,[(letter(540,950),'send'),(text('HMRC',540,T,140,R),'hmrc'),(text('£ CALCULATION',540,1200,90),'calculation'),(person(170,1340,1.0,B,'flat'),'may')])
# 22 Same interest. Very different bills.
sc(st('same',76.7),[(text('SAME INTEREST',540,T,115),'interest'),(scale_(540,1050),'very'),(bills(220,980,1),'different'),(bills(860,980,4),'bills'),(text('DIFFERENT BILLS',540,1380,105,R),'bills')])
# 23 General info, not financial advice.
sc(st('general'),[(doc(540,960,4),'general'),(text('GENERAL INFO',540,T,120),'info'),(text('NOT ADVICE',540,1330,110,R),'advice'),(person(860,1250,0.9,P,'flat','head'),'not')])
enlarge()
for s_ in S:
    for i in s_['items']:
        if getattr(i,'is_text',False) and abs(i.y-T)<1: i.instant=True
END=words[-1][2]+0.4
for a,b in zip(S,S[1:]):a['t1']=b['t0']
S[-1]['t1']=END
for s in S: assert 1.7<s['t1']-s['t0']<=3.8, (s['t0'],s['t1'])
if os.environ.get('DRY'):
    for s_ in S:
        for it in s_['items']:
            if it.key: word_end(words,it.key,s_['t0'],s_['t1'])
    print([(round(s_['t0'],2),round(s_['t1']-s_['t0'],2)) for s_ in S]);sys.exit()
t=time.time()
stills=[ (s['t0']+s['t1'])/2 if False else s['t1']-0.1 for s in S] if STILL else None
render(S,words,f'{D}/qc24_vo.wav',OUT,END,ends=ENDS,stills=stills)
print('render s',round(time.time()-t,1),'shots',len(S),'dur',round(END,2))
