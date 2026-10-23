# af22_pilot.py <dir with af22_vo.wav/af22_words.json/af22_lines.json> <out.mp4> [--frames a:b] [--png t1,t2,..]
# New-style pilot for Animal Facts Minute AFW22: every shot drawn in code (pycairo), synced to Kokoro word timings.
import sys,os,json,math,random,subprocess,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from sketchlib import *
D=sys.argv[1]; OUT=sys.argv[2]
Wd=json.load(open(f'{D}/af22_words.json')); LN=json.load(open(f'{D}/af22_lines.json'))
# word index per line
LI=[];i=0
for l in LN: n=len(l.split()); LI.append(list(range(i,i+n))); i+=n
def w(k,j): return Wd[LI[k][j]][1]   # start time of word j in line k
AEND=Wd[-1][2]; DUR=AEND+0.85
# palettes (each shot unique top/bottom paper tints)
def P(h1,h2): return (h1,h2)
def env_floor(c,y,col,t,seed):
    random.seed(seed); c.move_to(0,y)
    for x in range(0,W+60,60): c.line_to(x,y+8*math.sin(x*0.02+seed))
    c.line_to(W,H); c.line_to(0,H); c.close_path(); wash(c,col,0.55,keep=False)
    for k in range(40):
        x=random.uniform(0,W); yy=y+random.uniform(20,500); c.move_to(x,yy); c.line_to(x+random.uniform(8,22),yy-random.uniform(4,12)); ink(c,1,2.5,mix(INK,col,0.5),0.6)
def cam(c,t,s0,s1,z0=1.0,z1=1.07,ox=W/2,oy=H*0.42,dx=0,dy=0):
    u=ease((t-s0)/max(0.01,s1-s0)); z=lerp(z0,z1,u); c.translate(ox+dx*u,oy+dy*u); c.scale(z,z); c.translate(-ox,-oy)
def label(c,s,x,y,size,t,a0,col=INK,d=0.35,outline=CREAM,ow=12):
    text(c,s,x,y,size,col,a=pr(t,a0,0.12),p=pr(t,a0,d),outline=outline,ow=ow)
def stamp(c,s,x,y,size,t,a0,col=RED,rot=-0.08):
    k=eback((t-a0)/0.3)
    if k<=0: return
    c.save(); c.translate(x,y); c.rotate(rot); c.scale(lerp(1.6,1,cl(k)) if k<1 else 1,lerp(1.6,1,cl(k)) if k<1 else 1)
    text(c,s,0,0,size,col,a=cl((t-a0)/0.12),outline=CREAM,ow=14); c.restore()
SH=[]
def shot(t0):
    def d(f): SH.append((t0,f)); return f
    return d
@shot(0.0)
def s_forest(c,t,s0,s1):
    paper(c,(0.80,0.88,0.78),(0.55,0.66,0.50)); cam(c,t,s0,s1,1.0,1.08,dx=-40)
    for layer,(off,col,lw) in enumerate([(0.25,(0.55,0.65,0.55),5),(0.6,(0.35,0.45,0.32),7),(1.0,INK,9)]):
        for k in range(5):
            x=(k*260+layer*90)-t*30*off; x=(x%1400)-160; eucalyptus(c,x,1500+layer*60,900+layer*150,40*math.sin(k+layer),col,p=1,lw=lw)
    env_floor(c,1520,(0.42,0.36,0.24),t,1)
    c.save(); wave(c,60,1020,820,130,'saw',phase=t*1.5,p=pr(t,0.08,1.7)); ink(c,1,9,RED); c.restore()
    label(c,"chainsaw?",540,640,110,t,w(0,6),RED)
@shot(2.6)
def s_saw(c,t,s0,s1):
    paper(c,(0.93,0.88,0.76),(0.82,0.74,0.58)); cam(c,t,s0,s1,1.05,1.0)
    jit=math.sin(t*90)*4 if t<w(0,9) else 0
    chainsaw(c,470+jit,820,1.25,pr(t,s0,0.9))
    for k in range(3):
        if t<w(0,9): c.move_to(780+k*40,680-k*30); c.curve_to(820+k*40,650-k*30,840+k*40,700-k*30,880+k*40,660-k*30); ink(c,1,5,ORANGE,0.8)
    x0=w(0,9)
    c.move_to(200,560); c.line_to(880,1080); ink(c,pr(t,x0,0.25),22,RED)
    c.move_to(880,560); c.line_to(200,1080); ink(c,pr(t,x0+0.2,0.25),22,RED)
    stamp(c,"NO CHAINSAW",540,1230,120,t,w(0,10))
@shot(4.95)
def s_car(c,t,s0,s1):
    paper(c,(0.82,0.86,0.93),(0.62,0.68,0.82)); cam(c,t,s0,s1,1.0,1.06,dx=30)
    c.move_to(0,1080); c.line_to(W,1080); ink(c,1,6); 
    for k in range(8): c.move_to(k*150-((t*200)%150),1130); c.line_to(k*150+70-((t*200)%150),1130); ink(c,1,6,(0.95,0.95,0.9))
    car(c,540,1010,1.9,pr(t,s0,0.45))
    if t>w(1,3):
        on=int((t-w(1,3))*6)%2==0
        for sx in (-1,1):
            for k in range(3): c.arc(540+sx*120,800,60+k*45,(-0.5 if sx>0 else math.pi-0.5),(0.5 if sx>0 else math.pi+0.5)); ink(c,1,8,RED if on else ORANGE,0.9); c.new_path()
        circle(c,540,820,30); wash(c,RED if on else ORANGE,0.95,keep=False)
    wave(c,60,1020,480,90,'alarm',phase=t,p=pr(t,s0+0.1,0.6)); ink(c,1,8,RED)
    label(c,"car alarm",540,330,100,t,w(1,2),INK)
@shot(6.05)
def s_camera(c,t,s0,s1):
    paper(c,(0.90,0.90,0.88),(0.72,0.72,0.70)); cam(c,t,s0,s1,1.0,1.1)
    k=w(1,6); iris=pr(t,k,0.12)*(1-pr(t,k+0.18,0.15))
    camera(c,540,860,1.8,pr(t,s0,0.3),iris)
    if k<t<k+0.35:
        a=1-(t-k)/0.35; c.set_source_rgba(1,1,1,0.8*a); c.paint()
    wave(c,60,1020,1240,110,'click',phase=t*0.5,p=pr(t,k,0.9)); ink(c,1,8,TEAL)
    label(c,"click",540,450,120,t,k,TEAL)
@shot(7.8)
def s_track(c,t,s0,s1):
    paper(c,(0.86,0.90,0.80),(0.66,0.72,0.55))
    u=ease((t-s0)/(w(2,7)-s0+0.1)); c.save(); c.translate(-1300*u,0)
    for k in range(9): eucalyptus(c,k*300+60,1450,1000,30*math.sin(k*2),(0.40,0.48,0.36),1,6)
    wave(c,-100,1900,800,90,'song',phase=t,p=1); ink(c,1,8,RED,0.85)
    # log
    rrect(c,1650,1180,520,80,40); wash(c,(0.5,0.36,0.22),0.7); ink(c,1,7)
    for k in range(4): c.move_to(1700+k*110,1200); c.curve_to(1740+k*110,1215,1760+k*110,1235,1790+k*110,1240); ink(c,1,3)
    c.restore()
    lyrebird(c,1900-1300*u,1060,1.3,pr(t,w(2,7)-0.2,0.6),fan=0.05,tilt=0.15*math.sin(t*3))
    env_floor(c,1500,(0.40,0.33,0.20),t,3)
    label(c,"follow the sound...",540,420,90,t,s0+0.05,INK)
@shot(9.85)
def s_title(c,t,s0,s1):
    paper(c,(0.97,0.90,0.78),(0.88,0.72,0.55),0.25); cam(c,t,s0,s1,1.12,1.0,ox=640,oy=820)
    lyrebird(c,600,1000,2.4,1,fan=0.1,tilt=-0.25+0.3*pr(t,w(2,9),0.4),beak=0.2)
    text(c,"SUPERB LYREBIRD",540,380,118,RED,p=pr(t,w(2,9),0.7),outline=CREAM,ow=14)
    text(c,"Menura novaehollandiae",540,470,60,INK,a=pr(t,w(2,10)+0.2,0.3),bold=False)
@shot(11.36)
def s_pie(c,t,s0,s1):
    paper(c,(0.95,0.93,0.85),(0.85,0.82,0.70)); cam(c,t,s0,s1,1.0,1.05)
    cx,cy,r=540,840,330
    circle(c,cx,cy,r); ink(c,pr(t,s0,0.4),8)
    f70=0.70*eout((t-w(3,1))/0.5); f80=0.10*eout((t-w(3,3))/0.4)
    a0=-math.pi/2
    if f70>0: c.move_to(cx,cy); c.arc(cx,cy,r-6,a0,a0+2*math.pi*f70); c.close_path(); wash(c,ORANGE,0.75,keep=False)
    if f80>0:
        c.move_to(cx,cy); c.arc(cx,cy,r-6,a0+2*math.pi*0.7,a0+2*math.pi*(0.7+f80)); c.close_path(); wash(c,ORANGE,0.35,keep=False)
        for k in range(8): c.move_to(cx,cy); c.line_to(cx+r*math.cos(a0+2*math.pi*(0.7+f80*k/8)),cy+r*math.sin(a0+2*math.pi*(0.7+f80*k/8))); ink(c,1,2,ORANGE)
    n=int(round(100*(f70+f80))); txt=f"{min(n,70)}" if f80<=0 else f"70–{70+int(round(100*f80))}"
    if f70>0: text(c,txt+"%",540,1330,150,RED,outline=CREAM,ow=14)
    label(c,"BORROWED",540,1450,80,t,w(3,4),INK)
    lyrebird(c,860,560,0.6,pr(t,s0,0.3),fan=0.0,beak=0.4)
@shot(13.3)
def s_species(c,t,s0,s1):
    paper(c,(0.84,0.92,0.92),(0.62,0.78,0.78)); cam(c,t,s0,s1,1.0,1.06,dy=-20)
    lyrebird(c,520,1000,1.7,1,fan=0.15,beak=0.6+0.4*math.sin(t*12))
    cols=[(0.2,0.5,0.8),(0.85,0.3,0.3),(0.3,0.7,0.3),(0.9,0.7,0.1),(0.6,0.3,0.7),(0.2,0.7,0.7)]
    starts=[(-100,300),(1180,250),(-100,1300),(1180,1350),(540,-100),(1180,800)]
    for k,(sx,sy) in enumerate(starts):
        a=s0+0.25*k; u=eout((t-a)/0.9)
        if u<=0: continue
        tx,ty=730,880; x=lerp(sx,tx,u); y=lerp(sy,ty,u)-math.sin(u*math.pi)*150; sc=lerp(1,0.2,u**3)
        c.save(); c.translate(x,y); c.scale(sc,sc)
        ell(c,0,0,46,30); wash(c,cols[k],0.8); ink(c,1,5); circle(c,38,-26,18); wash(c,cols[k],0.8); ink(c,1,5)
        c.move_to(54,-28); c.line_to(76,-22); c.line_to(54,-18); ink(c,1,4)
        c.move_to(-10,-10); c.curve_to(-30,-60*math.sin(t*20+k),-50,-40,-60,-10); ink(c,1,4)
        c.restore()
    label(c,"copies of other species",540,420,88,t,w(3,10),INK)
@shot(15.76)
def s_question(c,t,s0,s1):
    paper(c,(0.92,0.86,0.92),(0.78,0.68,0.80)); cam(c,t,s0,s1,1.0,1.06)
    rrect(c,180,1150,620,80,40); wash(c,(0.5,0.36,0.22),0.7); ink(c,1,7)
    env_floor(c,1500,(0.45,0.36,0.30),t,5)
    hop=pr(t,s0+1.2,0.5); yb=lerp(1030,1360,hop)-math.sin(hop*math.pi)*200; xb=lerp(460,620,hop)
    lyrebird(c,xb,yb,1.3,1,fan=0.05,tilt=0.35*math.sin(t*4))
    c.move_to(470,520); c.curve_to(470,380,700,380,700,500); c.curve_to(700,600,590,600,590,700); c.line_to(590,760)
    ink(c,pr(t,s0+0.05,0.8),26,(0.55,0.25,0.65)); circle(c,590,840,18); wash(c,(0.55,0.25,0.65),pr(t,s0+0.8,0.1),keep=False)
@shot(17.92)
def s_impress(c,t,s0,s1):
    paper(c,(0.20,0.16,0.22),(0.10,0.08,0.12),0.5); cam(c,t,s0,s1,1.0,1.08)
    a=pr(t,s0,0.4)
    c.move_to(470,0); c.line_to(610,0); c.line_to(900,1450); c.line_to(180,1450); c.close_path()
    g=cairo.LinearGradient(0,0,0,1450); g.add_color_stop_rgba(0,1,0.95,0.7,0.55*a); g.add_color_stop_rgba(1,1,0.95,0.7,0.12*a); c.set_source(g); c.fill()
    ell(c,540,1440,380,60); wash(c,(1,0.9,0.6),0.35*a,keep=False)
    lyrebird(c,540,1290,1.5,1,fan=0.25*pr(t,w(5,1),0.8),beak=0.3)
    random.seed(3)
    for k in range(14):
        sx=random.uniform(150,930); sy=random.uniform(300,1300); tw=0.5+0.5*math.sin(t*8+k)
        if t>s0+0.1*k: c.save(); c.translate(sx,sy); c.rotate(t); poly(c,[(0,-22),(6,-6),(22,0),(6,6),(0,22),(-6,6),(-22,0),(-6,-6)]); wash(c,(1,0.9,0.5),0.9*tw,keep=False); c.restore()
    stamp(c,"IMPRESS",540,330,150,t,s0+0.05,(1,0.8,0.3),rot=0.04)
    label(c,"built for a show",540,1560,84,t,w(5,3),(1,0.95,0.8),outline=(0.1,0.08,0.1))
@shot(20.2)
def s_tape(c,t,s0,s1):
    paper(c,(0.96,0.94,0.80),(0.90,0.84,0.62)); cam(c,t,s0,s1,1.0,1.04,dx=-20)
    lyrebird(c,640,1000,1.15,1,fan=0.0)
    u=eout((t-w(5,10))/0.9); x0,x1=170,170+760*u
    rrect(c,90,1260,120,120,30); wash(c,(0.95,0.75,0.15),0.9); ink(c,1,6)
    if u>0:
        c.rectangle(170,1290,x1-170,60); wash(c,(0.98,0.85,0.25),0.95); ink(c,1,5)
        for k in range(0,101,5):
            xx=170+760*k/100
            if xx>x1: break
            c.move_to(xx,1290); c.line_to(xx,1290+(26 if k%10==0 else 14)); ink(c,1,3)
    val=u*1.0; text(c,f"{val:.1f} m" if u<1 else "≈ 1 m",540,1530,140,RED,outline=CREAM,ow=14,a=cl(u*4))
    label(c,"nose to tail tip",540,420,80,t,w(5,7))
@shot(22.1)
def s_taillen(c,t,s0,s1):
    paper(c,(0.94,0.88,0.84),(0.80,0.70,0.64)); cam(c,t,s0,s1,1.0,1.06,ox=400)
    lyrebird(c,720,860,1.6,1,fan=0.0)
    u=eout((t-w(6,4))/0.7)
    # tail runs from ~(720-125,873) leftwards
    c.move_to(590,1180); c.line_to(590-450*u,1180); ink(c,1,7,RED)
    c.move_to(590,1150); c.line_to(590,1210); ink(c,1,7,RED)
    if u>0.98: c.move_to(140,1150); c.line_to(140,1210); ink(c,1,7,RED)
    text(c,f"{int(70*u)} cm",380,1320,130,RED,a=cl(u*4),outline=CREAM,ow=14)
    label(c,"the tail alone",540,420,84,t,w(6,0))
@shot(24.6)
def s_tailfan(c,t,s0,s1):
    paper(c,(0.98,0.93,0.80),(0.92,0.78,0.58),0.25); cam(c,t,s0,s1,1.1,1.0,oy=900)
    n=1+int(15*cl((t-s0)/1.15))
    lyrebird(c,540,1180,1.5,1,fan=1.0,nf=n,beak=0.2)
    text(c,str(n),860,600,190,RED,outline=CREAM,ow=16)
    text(c,"feathers",860,690,70,INK,a=pr(t,w(6,8),0.2))
@shot(26.15)
def s_scrape(c,t,s0,s1):
    paper(c,(0.90,0.84,0.72),(0.62,0.50,0.36)); cam(c,t,s0,s1,1.0,1.08,oy=1200)
    g=pr(t,s0+0.15,1.5)
    c.move_to(160,1380); c.curve_to(300,1380-260*g,600,1380-260*g,760,1380); c.close_path(); wash(c,(0.48,0.34,0.20),0.85); ink(c,1,7)
    env_floor(c,1380,(0.40,0.30,0.18),t,8)
    kick=math.sin(t*14)
    lyrebird(c,820,1240,1.0,1,fan=0.0,tilt=0.4)
    random.seed(int(t*30))
    for k in range(18):
        ph=((t*2.2+k/18)%1); x=780-ph*420; y=1370-math.sin(ph*math.pi)*(240+k*6)
        circle(c,x,y,6+k%4*2); wash(c,(0.42,0.28,0.15),0.9,keep=False)
    label(c,"scrape...",540,420,96,t,w(7,1))
    label(c,"a dirt mound",540,530,80,t,w(7,5),RUST)
@shot(28.0)
def s_mapmounds(c,t,s0,s1):
    paper(c,(0.84,0.80,0.66),(0.74,0.70,0.54)); cam(c,t,s0,s1,1.05,1.0)
    random.seed(11)
    for k in range(26):   # canopy blobs (top-down)
        x=random.uniform(0,W); y=random.uniform(200,1600); r=random.uniform(50,110); circle(c,x,y,r); wash(c,(0.36,0.50,0.32),0.35,keep=False)
    pts=[(260,520),(780,700),(360,1050),(800,1330)]
    c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]; c.set_dash([18,22]); ink(c,1,6,(0.3,0.2,0.1),pr(t,w(7,10),0.6)); c.set_dash([])
    for k,(x,y) in enumerate(pts):
        u=eback((t-(s0+0.25*k))/0.4)
        if u>0: circle(c,x,y,70*u); wash(c,(0.50,0.34,0.18),0.9); ink(c,1,6); text(c,str(k+1),x,y+20,64,CREAM,a=cl(u))
    text(c,"top-down: his stages",540,330,84,INK,a=pr(t,s0,0.2),outline=CREAM,ow=12)
@shot(29.9)
def s_stage(c,t,s0,s1):
    paper(c,(0.86,0.80,0.92),(0.60,0.50,0.70)); 
    hop=pr(t,w(7,15),0.6); c.save(); c.translate(-520*hop,0)
    for k,x in enumerate((540,1060)):
        c.move_to(x-260,1420); c.curve_to(x-150,1250,x+150,1250,x+260,1420); c.close_path(); wash(c,(0.48,0.34,0.2),0.85); ink(c,1,7)
    c.restore()
    env_floor(c,1420,(0.36,0.30,0.22),t,9)
    xb=540+0*hop; yb=1220-math.sin(hop*math.pi)*260
    lyrebird(c,xb,yb,1.25,1,fan=0.9+0.1*math.sin(t*6),beak=0.4)
    label(c,"one stage after another",540,400,84,t,w(7,13),(1,0.95,0.85),outline=(0.2,0.12,0.2))
@shot(31.85)
def s_female(c,t,s0,s1):
    paper(c,(0.93,0.90,0.85),(0.85,0.80,0.72)); cam(c,t,s0,s1,1.0,1.04)
    c.save(); c.rectangle(0,0,W/2-6,H); c.clip(); c.set_source_rgba(0.3,0.25,0.35,0.35); c.paint()
    lyrebird(c,300,1000,0.9,1,fan=1.0,fill=0.3); text(c,"him: the show",270,560,62,INK); c.restore()
    c.move_to(W/2,200); c.line_to(W/2,1500); ink(c,pr(t,s0,0.3),6)
    nest(c,800,1150,1.0,1); lyrebird(c,780,1040,0.85,pr(t,s0,0.5),female=True)
    text(c,"her: simple",800,560,62,RED,a=pr(t,w(8,2),0.2))
@shot(33.7)
def s_egg(c,t,s0,s1):
    paper(c,(0.82,0.88,0.96),(0.55,0.65,0.82)); cam(c,t,s0,s1,1.0,1.1,oy=1000)
    nest(c,540,1180,1.6,1)
    ell(c,540,1080,95,125); wash(c,(0.96,0.92,0.95),0.95*pr(t,w(8,6),0.3)); ink(c,pr(t,w(8,6),0.4),7)
    random.seed(4)
    if t>w(8,8):
        for k in range(22):
            x=random.uniform(40,1040); sp=random.uniform(150,260); y=(random.uniform(0,1900)+(t-w(8,8))*sp)%1900; snowflake(c,x,y,random.uniform(14,30),t+k,pr(t,w(8,8),0.3))
    text(c,"ONE egg",540,420,120,RED,a=pr(t,w(8,6),0.2),outline=CREAM,ow=14)
    label(c,"winter",540,1470,100,t,w(8,9),(0.15,0.3,0.6))
@shot(35.17)
def s_weeks(c,t,s0,s1):
    paper(c,(0.95,0.95,0.90),(0.86,0.86,0.78)); cam(c,t,s0,s1,1.0,1.05)
    n=1+int(6*cl((t-w(9,1))/(w(9,6)-w(9,1)+0.3)))
    rrect(c,290,500,500,560,30); wash(c,(1,1,1),0.95); ink(c,1,7)
    c.rectangle(290,500,500,120); wash(c,RED,0.85,keep=False)
    for k in range(5): circle(c,350+k*95,500,16); wash(c,INK,1,keep=False)
    text(c,"WEEK",540,590,70,CREAM)
    fr=((t-w(9,1))*(6/(w(9,6)-w(9,1)+0.3)))%1 if n<7 else 1
    c.save(); c.translate(540,850); c.scale(1,ease(min(1,fr*3))); text(c,str(n),0,90,300,INK); c.restore()
    nest(c,540,1330,0.8,1); ell(c,540,1290,48,62); wash(c,(0.96,0.92,0.95),0.95); ink(c,1,5)
    text(c,"up to 7",540,1560,96,RED,a=pr(t,w(9,6),0.2),outline=CREAM,ow=12)
@shot(37.47)
def s_timeline(c,t,s0,s1):
    paper(c,(0.92,0.88,0.80),(0.80,0.72,0.60)); 
    off=(t-s0)*900
    c.move_to(1000,900); c.line_to(80,900); ink(c,1,8)
    c.move_to(120,860); c.line_to(80,900); c.line_to(120,940); ink(c,1,8)
    for k in range(-2,14):
        x=900-k*220+off%220
        c.move_to(x,880); c.line_to(x,920); ink(c,1,5)
    labs=[(0,"today"),(1,"1 million yrs"),(2,"5 million"),(3,"10 million")]
    for k,s in labs:
        x=900-k*600+off
        if 60<x<1040: text(c,s,x,1000,60,INK,bold=False)
    lyrebird(c,860,760,0.5,1,fan=0.0)
    stamp(c,"OLD.",540,560,170,t,w(10,3),RUST)
@shot(39.0)
def s_strata(c,t,s0,s1):
    paper(c,(0.90,0.84,0.74),(0.70,0.60,0.46)); cam(c,t,s0,s1,1.0,1.06,oy=1200)
    cols=[(0.62,0.50,0.34),(0.72,0.60,0.40),(0.52,0.42,0.30),(0.66,0.48,0.32),(0.45,0.36,0.28),(0.58,0.46,0.36)]
    for k,col in enumerate(cols):
        y=420+k*190; u=pr(t,s0+0.12*k,0.35)
        if u<=0: continue
        c.move_to(0,y)
        for x in range(0,W+40,40): c.line_to(x*u,y+14*math.sin(x*0.013+k))
        c.line_to(W*u,y+190); c.line_to(0,y+190); c.close_path(); wash(c,col,0.9); ink(c,1,4)
    g=pr(t,w(10,8),0.4)
    if g>0:
        c.save(); c.translate(560,1400); c.rotate(-0.5)
        c.move_to(0,0); c.curve_to(60,-80,40,-200,-10,-260); ink(c,1,6,(0.98,0.9,0.6),g)
        for k in range(10): c.move_to(10+k*1,-20-k*24); c.line_to(60-k*3,-40-k*24); c.move_to(5+k,-20-k*24); c.line_to(-40+k*2,-30-k*24); ink(c,1,3,(0.98,0.9,0.6),g)
        c.restore()
        r=cairo.RadialGradient(560,1300,10,560,1300,260); r.add_color_stop_rgba(0,1,0.9,0.5,0.5*g); r.add_color_stop_rgba(1,1,0.9,0.5,0); c.set_source(r); c.paint()
    c.move_to(860,420); c.line_to(860,1450); ink(c,pr(t,w(10,7),0.5),6,RED)
    label(c,"≈15 million years",540,330,96,t,w(10,8),RED)
@shot(41.8)
def s_aus(c,t,s0,s1):
    paper(c,(0.80,0.90,0.96),(0.55,0.74,0.88)); cam(c,t,s0,s1,1.0,1.06,ox=760,oy=1080)
    def pj(lo,la): return (90+(lo-112)*21.5, 520+(-la-10)*24)
    poly(c,[pj(*p) for p in AUS]); wash(c,(0.92,0.75,0.45),0.85*pr(t,s0+0.6,0.4)); ink(c,pr(t,s0,0.8),7)
    poly(c,[pj(*p) for p in TAS]); wash(c,(0.92,0.75,0.45),0.85*pr(t,s0+0.6,0.4)); ink(c,pr(t,s0+0.4,0.4),7)
    x,y=pj(148.5,-36); u=eback((t-w(11,1))/0.4)
    if u>0:
        for k in range(5):
            a=k*1.256+t; heart(c,x+math.cos(a)*120*u,y-60+math.sin(a)*90*u,22*u); wash(c,RED,0.9,keep=False)
        circle(c,x,y,16); wash(c,RED,1,keep=False)
    text(c,"AUSTRALIA",540,420,110,INK,a=pr(t,s0,0.2),outline=CREAM,ow=12)
@shot(43.4)
def s_coin(c,t,s0,s1):
    paper(c,(0.30,0.28,0.26),(0.15,0.14,0.13),0.5); cam(c,t,s0,s1,1.0,1.08)
    sp=eout((t-s0)/1.2); ang=(1-sp)*6*math.pi; sx=abs(math.cos(ang))*0.9+0.1
    c.save(); c.translate(540,880); c.scale(sx,1)
    circle(c,0,0,330); g=cairo.RadialGradient(-80,-120,40,0,0,340); g.add_color_stop_rgb(0,0.95,0.95,0.95); g.add_color_stop_rgb(1,0.62,0.62,0.66); c.set_source(g); c.fill_preserve(); ink(c,1,8,(0.4,0.4,0.42))
    circle(c,0,0,300); ink(c,1,3,(0.45,0.45,0.48))
    if math.cos(ang)>0: lyrebird(c,40,40,0.9,1,fan=0.75,col=False)
    c.restore()
    shine=(t*0.8)%1.5
    text(c,"10c",540,1400,170,(0.95,0.95,0.95),a=pr(t,w(11,6),0.2),outline=(0.2,0.2,0.2),ow=12)
    label(c,"on the ten-cent coin",540,330,84,t,w(11,6),(1,0.95,0.85),outline=(0.15,0.14,0.13))
@shot(45.0)
def s_pocket(c,t,s0,s1):
    paper(c,(0.40,0.50,0.70),(0.25,0.33,0.52),0.4); cam(c,t,s0,s1,1.0,1.05)
    for k,px in enumerate((300,780)):
        c.move_to(px-220,600); c.curve_to(px-200,1000,px+200,1000,px+220,600); ink(c,1,9,(0.85,0.75,0.4))
        c.move_to(px-220,600); c.line_to(px+220,600); ink(c,1,6,(0.85,0.75,0.4))
        for j in range(3):
            a=s0+0.3*k+0.45*j; u=eout((t-a)/0.5)
            if u>0:
                y=lerp(200,820-j*40,u); c.save(); c.translate(px+(j-1)*60,y); c.scale(0.4+0.6*abs(math.cos(t*6+j)),1); circle(c,0,0,60); wash(c,(0.8,0.8,0.84),0.95); ink(c,1,4); c.restore()
    c.move_to(80,1150)
    for k in range(9):
        x=80+k*115; c.line_to(x,1150); circle(c,x,1150,12); 
    ink(c,pr(t,w(11,13),0.7),5,(0.95,0.9,0.7))
    label(c,"every day",540,1330,110,t,w(11,14),(1,0.92,0.6),outline=(0.15,0.2,0.35))
    label(c,"in people's pockets",540,380,84,t,w(11,12),(1,0.95,0.85),outline=(0.15,0.2,0.35))
@shot(47.16)
def s_flat(c,t,s0,s1):
    paper(c,(0.12,0.16,0.14),(0.05,0.07,0.06),0.6); cam(c,t,s0,s1,1.08,1.0)
    for k in range(6): eucalyptus(c,k*200+20,1600,1100,30*math.sin(k),(0.22,0.30,0.25),1,10)
    amp=130*(1-pr(t,s0+0.1,0.8)); wave(c,60,1020,860,amp,'saw',phase=t,p=1); ink(c,1,9,RED)
    text(c,"...",540,600,140,(0.9,0.9,0.85),a=pr(t,w(12,3),0.2))
@shot(48.44)
def s_year(c,t,s0,s1):
    paper(c,(0.95,0.92,0.84),(0.86,0.80,0.66)); cam(c,t,s0,s1,1.0,1.06)
    c.select_font_face(FONT,cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD); c.set_font_size(380); e=c.text_extents("2013")
    c.move_to(540-e.width/2-e.x_bearing,1000); c.text_path("2013"); wash(c,ORANGE,0.8*pr(t,w(13,2),0.3)); ink(c,pr(t,w(13,1),0.7),8)
    label(c,"the archive year",540,1200,80,t,w(13,2))
@shot(49.5)
def s_reel(c,t,s0,s1):
    paper(c,(0.88,0.86,0.92),(0.70,0.68,0.78)); cam(c,t,s0,s1,1.0,1.05,dx=-30)
    for k,(rx) in enumerate((330,750)):
        c.save(); c.translate(rx,700); c.rotate(t*3)
        circle(c,0,0,160); wash(c,(0.25,0.25,0.3),0.85); ink(c,1,6)
        for j in range(3): c.save(); c.rotate(j*2.094); circle(c,0,-90,38); wash(c,CREAM,0.9,keep=False); c.restore()
        circle(c,0,0,22); wash(c,CREAM,1,keep=False); c.restore()
    c.move_to(330,860); c.line_to(750,860); ink(c,1,8,(0.4,0.25,0.15))
    # mic + bird left, wave travels into the tape
    lyrebird(c,220,1260,0.75,1,fan=0.1,beak=0.7)
    rrect(c,480,1120,60,130,30); wash(c,(0.3,0.3,0.32),0.9); ink(c,1,5); c.move_to(510,1250); c.line_to(510,1350); ink(c,1,6)
    wave(c,320,1020,1180,70,'saw',phase=t*2,p=pr(t,w(13,4),0.8)); ink(c,1,7,RED)
    label(c,"recording: chainsaw (by a bird)",540,380,70,t,w(13,7),INK)
@shot(51.8)
def s_drawer(c,t,s0,s1):
    paper(c,(0.86,0.84,0.80),(0.66,0.64,0.60)); cam(c,t,s0,s1,1.0,1.06)
    rrect(c,200,300,680,1180,20); wash(c,(0.45,0.50,0.48),0.9); ink(c,1,7)
    for k in range(3):
        if k==1: continue
        rrect(c,240,340+k*370,600,330,14); wash(c,(0.55,0.60,0.58),0.9); ink(c,1,5)
    op=1-pr(t,w(13,13)+0.1,0.5); dy=0
    c.save(); c.translate(0,0); rrect(c,240-80*op,710,600+160*op,330,14); wash(c,(0.62,0.67,0.64),0.95); ink(c,1,6)
    rrect(c,380-80*op*0.5,770,320,110,10); wash(c,CREAM,1); ink(c,1,4)
    text(c,"NATIONAL",540-40*op,815,40,INK,p=pr(t,w(13,11),0.4)); text(c,"SOUND ARCHIVE · 2013",540-40*op,860,34,INK,p=pr(t,w(13,12),0.6))
    c.restore()
    u=eout((t-(w(13,10)))/0.5)
    if op>0.2:
        c.save(); c.translate(540,lerp(150,720,u)); c.rotate(t*2); circle(c,0,0,80); wash(c,(0.25,0.25,0.3),0.9); ink(c,1,5); circle(c,0,0,14); wash(c,CREAM,1,keep=False); c.restore()
    label(c,"preserved",540,1580,100,t,w(13,13)+0.2,INK)
@shot(54.7)
def s_case(c,t,s0,s1):
    paper(c,(0.94,0.90,0.80),(0.82,0.74,0.60)); cam(c,t,s0,s1,1.08,1.0)
    rrect(c,240,1300,600,90,10); wash(c,(0.45,0.30,0.20),0.95); ink(c,1,6)
    lyrebird(c,560,1080,1.15,1,fan=0.2)
    gl=pr(t,w(14,2)-0.2,0.6)
    c.move_to(280,1300); c.line_to(280,560); c.curve_to(280,330,800,330,800,560); c.line_to(800,1300); ink(c,gl,6,(0.6,0.8,0.9)); 
    if gl>0.9:
        c.move_to(330,600); c.curve_to(330,460,420,420,480,410); ink(c,1,10,(1,1,1),0.6)
    rrect(c,380,1400,320,90,10); wash(c,(0.85,0.70,0.30),0.95*pr(t,w(14,3),0.2)); ink(c,pr(t,w(14,3),0.3),4)
    text(c,"preserved",540,1462,52,INK,p=pr(t,w(14,3),0.4))
@shot(56.4)
def s_machine(c,t,s0,s1):
    paper(c,(0.92,0.84,0.70),(0.80,0.62,0.44)); cam(c,t,s0,s1,1.0,1.07,dx=20)
    lyrebird(c,300,1000,1.0,1,fan=0.1,beak=0.6+0.4*math.sin(t*16))
    chainsaw(c,770,900,0.85,pr(t,w(14,4),0.5))
    wave(c,440,620,870,50,'saw',phase=t*3,p=1); ink(c,1,7,RED)
    text(c,"=",540,1260,160,INK,a=pr(t,w(14,6),0.2))
    label(c,"copying a machine",540,420,92,t,w(14,4),INK)
@shot(58.2)
def s_honour(c,t,s0,s1):
    paper(c,(0.96,0.92,0.86),(0.88,0.82,0.74)); cam(c,t,s0,s1,1.0,1.05)
    dr=pr(t,w(14,8),1.0)
    c.save(); c.translate(540,700); c.rotate(0.6*dr)
    for k in range(16): a=k*math.pi/8; c.move_to(0,0); c.arc(0,0,150,a,a+0.35); c.close_path(); wash(c,(0.15,0.45,0.75) if k%2 else (0.25,0.55,0.85),0.95,keep=False)
    circle(c,0,0,105); wash(c,(0.96,0.85,0.4),1); ink(c,1,5)
    text(c,"honour",0,20,54,INK)
    for sx in (-1,1): poly(c,[(sx*30,120),(sx*90,420+60*dr),(sx*40*1,380+60*dr),(0,120)]); wash(c,(0.2,0.5,0.8),0.95); ink(c,1,4)
    c.restore()
    c.save(); c.translate(0,lerp(0,420,ease(dr))); c.restore()
    stamp(c,"NOT EXACTLY",540,1350,110,t,w(14,8))
@shot(59.9)
def s_peer(c,t,s0,s1):
    paper(c,(0.84,0.84,0.86),(0.62,0.62,0.66)); cam(c,t,s0,s1,1.0,1.08,ox=400)
    rrect(c,620,600,420,900,16); wash(c,(0.45,0.50,0.48),0.9); ink(c,1,6)
    rrect(c,650,880,360,200,10); wash(c,(0.62,0.67,0.64),0.95); ink(c,1,5); text(c,"2013",830,1000,64,INK)
    lyrebird(c,330,1200,1.1,1,fan=0.0,droop=pr(t,w(14,11),0.8),tilt=0.25)
    label(c,"...auditioned for",400,420,84,t,w(14,12),INK)
@shot(61.5)
def s_rewind(c,t,s0,s1):
    paper(c,(0.60,0.72,0.66),(0.40,0.52,0.44))
    for k in range(5): x=(k*260+(t-s0)*900)%1400-160; eucalyptus(c,x,1500,1000,30*math.sin(k),(0.25,0.35,0.28),1,8)
    wave(c,60,1020,820,130,'saw',phase=-t*3,p=1); ink(c,1,9,RED)
    for k in range(12): y=((k*170+(t*1500))%1920); c.rectangle(0,y,W,8); c.set_source_rgba(1,1,1,0.15); c.fill()
    a=0.6+0.4*math.sin(t*10)
    for k in range(2): poly(c,[(600-k*150,520),(460-k*150,600),(600-k*150,680)]); wash(c,CREAM,a,keep=False)
    text(c,"REWIND",560,450,90,CREAM,outline=INK,ow=10)
@shot(63.85)
def s_resolve(c,t,s0,s1):
    paper(c,(0.97,0.92,0.80),(0.90,0.80,0.62)); cam(c,t,s0,s1,1.0,1.06,ox=700,oy=800)
    m=pr(t,w(16,1),1.0)
    # wave shrinks and flows into beak at (~830,640)
    c.save(); wave(c,lerp(60,820,m),lerp(1020,1000,m),lerp(820,650,m),lerp(130,40,m),'saw',phase=t,p=1); ink(c,1,9,RED,1-0.5*m); c.restore()
    lyrebird(c,600,930,1.6,pr(t,s0,0.6),fan=0.1,beak=0.8)
    stamp(c,"NEVER A CHAINSAW",540,1400,96,t,w(16,2),RED)
@shot(65.7)
def s_colour(c,t,s0,s1):
    paper(c,(0.88,0.92,0.80),(0.66,0.76,0.52)); cam(c,t,s0,s1,1.05,1.0)
    c.move_to(220,1420); c.curve_to(330,1260,750,1260,860,1420); c.close_path(); wash(c,(0.48,0.34,0.2),0.85); ink(c,1,7)
    env_floor(c,1420,(0.38,0.32,0.20),t,12)
    lyrebird(c,540,1230,1.3,1,fan=1.0,fill=pr(t,s0+0.1,1.2),beak=0.5)
    label(c,"just a bird",540,380,100,t,w(16,6),INK)
@shot(67.4)
def s_voices(c,t,s0,s1):
    paper(c,(0.92,0.88,0.96),(0.74,0.66,0.86)); cam(c,t,s0,s1,1.0,1.06)
    lyrebird(c,300,1150,1.0,1,fan=0.3,beak=0.7+0.3*math.sin(t*14))
    icons=[('car',car),('cam',camera),('saw',chainsaw),('bird',None),('bird2',None)]
    for k,(nm,fn) in enumerate(icons):
        a=s0+0.3*k; u=eout((t-a)/0.6)
        if u<=0: continue
        bx=lerp(420,560+(k%2)*260,u); by=lerp(950,300+k*200,u)
        rrect(c,bx-130,by-80,260,160,40); wash(c,CREAM,0.95); ink(c,1,5)
        c.move_to(bx-100,by+70); c.line_to(420,960); ink(c,1,4,INK,0.5)
        if fn: fn(c,bx,by+10,0.32,1)
        else: lyrebird(c,bx+10,by+10,0.3,1,fan=0.0,female=True)
    label(c,"everyone else's voice",540,1540,88,t,w(16,9),INK)
@shot(69.5)
def s_end(c,t,s0,s1):
    paper(c,(0.98,0.93,0.82),(0.92,0.80,0.60),0.25)
    lyrebird(c,540,1250,1.6,1,fan=pr(t,s0,0.9),beak=0.3)
    u=eback((t-(s0+0.3))/0.4)
    if u>0:
        c.save(); c.translate(540,700); c.scale(cl(u)*1 if u<1 else 1,cl(u) if u<1 else 1)
        rrect(c,-260,-80,520,160,80); wash(c,RED,0.95); ink(c,1,6); text(c,"FOLLOW",0,28,90,CREAM); c.restore()
    text(c,"Animal Facts Minute",540,480,70,INK,a=pr(t,s0+0.4,0.3))
# ---------- captions (word-synced, chunked by line) ----------
DISP0={};_i=0
for _l in LN:
    for _tok in _l.split(): DISP0[_i]=_tok; _i+=1
CH=[]
for k in range(len(LN)):
    ids=LI[k]; cur=[]
    for j in ids:
        cur.append(j)
        if len(cur)>=3 or DISP0[j][-1:] in ',.?' : CH.append(cur); cur=[]
    if cur: CH.append(cur)
# use original punctuated words from lines for display
DISP={};i=0
for l in LN:
    for tok in l.split(): DISP[i]=tok; i+=1
def captions(c,t):
    for ci in range(len(CH)-1,-1,-1):
        ch=CH[ci]; s=Wd[ch[0]][1]; e=Wd[ch[-1]][2]+0.25
        if s-0.05<=t<e:
            words=[DISP[j] for j in ch]; size=78; sp=textw(c," ",size)
            tw=sum(textw(c,x,size) for x in words)+sp*(len(words)-1); x=540-tw/2; y=1700
            for j,wd in zip(ch,words):
                on=Wd[j][1]<=t; col=(1,0.82,0.25) if (Wd[j][1]<=t<Wd[j][2]+0.05) else (1,1,1)
                text(c,wd,x,y,size,col,a=1.0 if on else 0.55,outline=(0.08,0.06,0.05),ow=12,anchor='l'); x+=textw(c,wd,size)+sp
            return
def frame(t,surf):
    c=cairo.Context(surf)
    idx=max(i for i,(s,_) in enumerate(SH) if s<=t+1e-6); s0,f=SH[idx]; s1=SH[idx+1][0] if idx+1<len(SH) else DUR
    c.save(); f(c,t,s0,s1); c.restore(); c.new_path(); captions(c,t)
    # 4-frame flash-dissolve across cuts
    return idx
if __name__=='__main__':
    surf=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H)
    if '--png' in sys.argv:
        for tt in sys.argv[sys.argv.index('--png')+1].split(','): frame(float(tt),surf); surf.write_to_png(f'{OUT}_{tt}.png')
        raise SystemExit
    N=int(DUR*FPS); T0=time.time()
    ff=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','bgra','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',f'{D}/af22_vo.wav',
        '-af','apad','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-t',f'{DUR:.3f}','-movflags','+faststart',OUT],stdin=subprocess.PIPE)
    shots=[]
    for n in range(N):
        t=n/FPS; idx=frame(t,surf); ff.stdin.write(surf.get_data())
        if n%300==0: print(f'frame {n}/{N} {time.time()-T0:.1f}s',flush=True)
    ff.stdin.close(); ff.wait(); print(f'done {N} frames in {time.time()-T0:.1f}s; shots={len(SH)}')
    json.dump([[s,f.__name__] for s,f in SH],open(OUT.replace('.mp4','_shots.json'),'w'),indent=0)
