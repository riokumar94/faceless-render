"""land.py - 1920x1080 long-form renderer, Caveman Diaries v2 look (Grub, earthy palette, wobbly black outlines,
hard cuts, props popping in on their spoken word, captions chunked on whole words only, no on-screen AI line).
usage: python land.py <job.json> <words.json> <vo.wav> <out.mp4>   job = {title, vo, shots:[{a,b,tpl,props,kw,num,label,mark}]}"""
import sys,os,json,re,math,subprocess,random
from PIL import Image,ImageDraw,ImageFont
HERE=os.path.dirname(os.path.abspath(__file__));sys.path.insert(0,HERE)
import stick,props_lib as PL
W,H,FPS=1920,1080,30
J=json.load(open(sys.argv[1]));words=json.load(open(sys.argv[2]));VO=sys.argv[3];OUT=os.path.abspath(sys.argv[4])
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',VO],capture_output=True,text=True).stdout)
_f={}
def F(s,k='marker'):
    if (s,k) not in _f:_f[(s,k)]=ImageFont.truetype(f'{HERE}/props/{k}.ttf',int(s))
    return _f[(s,k)]
INK=(25,20,18);SKY1=(205,228,242);SKY2=(168,205,228);FAR=(150,168,150);NEAR=(176,150,104);GROUND=(214,186,138)
WH=(252,250,244);RED=(214,48,40);GRN=(40,160,70);HI=(214,120,30)
norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
# ---- captions: whole script tokens matched to word timings; chunks cut only between tokens
caps=[];i=0
for tw in J['vo'].split():
    tg=norm(tw);acc='';st=None
    if not tg:continue
    while acc!=tg:
        acc+=norm(words[i][0]);st=st if st is not None else words[i][1];en=words[i][2];i+=1
        if len(acc)>len(tg):raise SystemExit(f'CAPTION MISMATCH {tw}')
    caps.append((tw,st,en))
assert i==len(words),'words left over'
FW={'a','an','the','of','to','and','or','in','on','at','for','by','with','from','as','is','its','their','your','this','that','but','so'}
groups=[];cur=[]
for k,c in enumerate(caps):
    cur.append(c)
    if k+1==len(caps) or c[0][-1] in '.,:;!?' or (len(cur)>=5 and norm(c[0]) not in FW) or len(cur)>=7:groups.append(cur);cur=[]
assert [w for g in groups for w in g]==caps
json.dump([' '.join(w[0] for w in g) for g in groups],open(OUT.replace('.mp4','_chunks.json'),'w'),ensure_ascii=False)
def draw_caps(im,t):
    g=[g for g in groups if g[0][1]-0.05<=t<=g[-1][2]+0.25]
    if not g:return
    g=g[-1];d=ImageDraw.Draw(im);fs=54
    while d.textlength(' '.join(w[0] for w in g),font=F(fs,'kalam'))>1600 and fs>30:fs-=2
    f=F(fs,'kalam');tw=d.textlength(' '.join(w[0] for w in g),font=f);x=(W-tw)/2;y=H-118
    d.rounded_rectangle([x-26,y-8,x+tw+26,y+fs*1.3],18,fill=(20,16,14))
    for w in g:
        d.text((x,y),w[0],font=f,fill=(255,200,70) if w[1]<=t+0.02 else (250,248,240));x+=d.textlength(w[0]+' ',font=f)
# ---- helpers
def wob(pts,t,sd,a=2.2):
    r=random.Random(sd*1000+int(t*8));return [(x+r.uniform(-a,a),y+r.uniform(-a,a)) for x,y in pts]
def outline_poly(d,pts,fill,t,sd,w=7):
    p=wob(pts,t,sd);d.polygon(p,fill=fill);d.line(p+[p[0]],fill=INK,width=w,joint='curve')
def ease(u):u=min(max(u,0),1);return u*u*(3-2*u)
def back(u):u=min(max(u,0),1);c=1.9;return 1+(c+1)*(u-1)**3+c*(u-1)**2
def scene_bg(im,t,sd,cold=False):
    d=ImageDraw.Draw(im)
    for y in range(0,700,4):k=y/700;d.rectangle([0,y,W,y+4],fill=tuple(int(a+(b-a)*k) for a,b in zip(SKY1,SKY2)))
    r=random.Random(sd);far=[(0,700)]+[(x,560+r.randint(-70,40)) for x in range(0,W+160,160)]+[(W,700)]
    outline_poly(d,far+[(W,760),(0,760)],FAR if not cold else (200,215,225),t,sd)
    near=[(0,760)]+[(x,690+r.randint(-30,20)) for x in range(0,W+240,240)]+[(W,760)]
    outline_poly(d,near+[(W,800),(0,800)],NEAR if not cold else (225,232,238),t,sd+1)
    d.rectangle([0,795,W,H],fill=GROUND if not cold else (236,240,244));d.line(wob([(0,797),(W/2,800),(W,797)],t,sd+2),fill=INK,width=7)
    if cold:
        r2=random.Random(5)
        for k in range(70):x=(r2.uniform(0,W)+t*30*r2.uniform(.5,1.5))%W;y=(r2.uniform(0,H)+t*120*r2.uniform(.6,1.4))%H;d.ellipse([x-4,y-4,x+4,y+4],fill=(255,255,255))
    return d
def grub(im,x,y,s,pose,t,emo='calm',sweat=False,qm=False):
    d=ImageDraw.Draw(im);w=max(5,int(11*s))
    # fur tunic first (behind arms)
    hip=y-118*s;nk=hip-105*s
    outline_poly(d,[(x-34*s,nk+8*s),(x+34*s,nk+8*s),(x+46*s,hip+28*s),(x+10*s,hip+14*s),(x-14*s,hip+30*s),(x-46*s,hip+22*s)],(150,96,50),t,7,max(4,int(6*s)))
    hx,hy=stick.draw(d,x,y,s,pose,t,INK,face=False,w=w);HR=30*s
    d.ellipse([hx-HR,hy-HR,hx+HR,hy+HR],fill=(238,200,160),outline=INK,width=w)
    hair=[(hx+HR*math.cos(a)*1.15,hy-HR*0.2+HR*math.sin(a)*1.05) for a in [math.pi*(1+k/10) for k in range(11)]]
    d.polygon(hair+[(hx+HR*1.1,hy-HR*0.3),(hx-HR*1.1,hy-HR*0.3)],fill=(70,40,20));d.line(hair,fill=INK,width=max(3,w//2))
    d.chord([hx-HR*0.85,hy+HR*0.1,hx+HR*0.85,hy+HR*1.25],0,180,fill=(70,40,20))   # beard
    ey=hy-HR*0.15
    for sx in (-1,1):
        d.ellipse([hx+sx*11*s-5*s,ey-6*s,hx+sx*11*s+5*s,ey+6*s],fill=WH,outline=INK,width=2);d.ellipse([hx+sx*11*s-2.5*s,ey-2*s,hx+sx*11*s+2.5*s,ey+3*s],fill=INK)
        tilt={'calm':0,'worried':-1,'angry':1,'surprised':0}[emo];lift=(14 if emo=='surprised' else 10)*s
        d.line([(hx+sx*4*s,ey-lift+tilt*sx*-4*s),(hx+sx*18*s,ey-lift-tilt*sx*-4*s)],fill=INK,width=max(3,int(5*s)))
    if emo=='surprised':d.ellipse([hx-6*s,hy+HR*0.35,hx+6*s,hy+HR*0.75],fill=INK)
    if sweat:
        for k in range(2):d.line([(hx+HR*1.3+k*12*s,hy-HR*0.6+k*14*s),(hx+HR*1.45+k*12*s,hy-HR*0.25+k*14*s)],fill=(80,150,230),width=max(3,int(5*s)))
    if qm:d.text((hx+HR*1.2,hy-HR*3.2+6*math.sin(t*4)),'?',font=F(80*s),fill=INK)
    return hx,hy
def pop(im,e,x,y,size,t0,t,rot=0):
    u=(t-t0)/0.28
    if u<=0:return
    PL.paste(im,e,x,y,size*back(u),rot,1.0)
def card(im,txt,x,y,t0,t,mark=None,w=760):
    """hand-drawn keyword card: big all-caps on white, optional red X / green tick"""
    if t<t0:return
    d=ImageDraw.Draw(im);k=back((t-t0)/0.25);fs=96
    while d.textlength(txt,font=F(fs))>w-80 and fs>40:fs-=4
    bw=d.textlength(txt,font=F(fs))+80;bh=fs*1.5+40;bw*=k;bh*=k
    outline_poly(d,[(x-bw/2,y-bh/2),(x+bw/2,y-bh/2),(x+bw/2,y+bh/2),(x-bw/2,y+bh/2)],WH,t,11,8)
    if k>0.9:
        d.text((x,y),txt,font=F(fs),fill=INK,anchor='mm')
        if mark=='x':
            for a,b in (((-1,-1),(1,1)),((-1,1),(1,-1))):d.line(wob([(x+a[0]*bw*0.42,y+a[1]*bh*0.6),(x+b[0]*bw*0.42,y+b[1]*bh*0.6)],t,3),fill=RED,width=22)
        if mark=='v':d.line(wob([(x+bw/2-20,y),(x+bw/2+30,y+50),(x+bw/2+120,y-80)],t,4),fill=GRN,width=24,joint='curve')
def kwtimes(s):
    """time each prop pops = start of its keyword in the narration (fallback: even spacing)"""
    ws=[c for c in caps if s['a']-0.05<=c[1]<s['b']];out=[]
    for j,k in enumerate(s.get('kw',[])):
        hit=[c[1] for c in ws if norm(c[0]).startswith(norm(k))]
        out.append(hit[0] if hit else s['a']+(j+0.5)*(s['b']-s['a'])/max(1,len(s.get('kw',[]))))
    while len(out)<len(s['props']):out.append(out[-1]+0.5 if out else s['a']+0.3)
    if out:out[0]=min(out[0],s['a']+0.12)   # first prop is up at the cut: never a figure-only frame
    return out
# ---- templates (each: props + figure/diagram, never text-only or figure-only)
def T_hook(im,s,t,u,b):
    scene_bg(im,t,1,True);d=ImageDraw.Draw(im);T=kwtimes(s)
    outline_poly(d,[(380,800),(1540,800),(1440,690),(480,690)],(190,225,240),t,21)    # ice sheet
    rise=ease((t-s['a'])/1.6);grub(im,960,800-70*rise,1.25,'stand',t,'worried')
    d.rectangle([380,800,1540,1000],fill=(205,232,244));d.line(wob([(380,800),(1540,800)],t,22),fill=INK,width=7)
    for k in range(5):d.line(wob([(700+k*130,800),(740+k*130,860),(690+k*130,930)],t,30+k),fill=INK,width=4)
    pop(im,s['props'][0],330,560,190,T[0],t);pop(im,s['props'][1],1600,520,220,s['a']+0.2,t)
    if s.get('num') and t>T[-1]:card(im,s['num']+' YEARS',960,190,T[-1],t,w=900)
def T_diary(im,s,t,u,b):
    d=scene_bg(im,t,2+b);T=kwtimes(s)
    outline_poly(d,[(900,170),(1720,140),(1760,760),(880,790)],(168,156,140),t,40,9)          # cave-wall stone page
    lines=[l for l in [s.get('label') or '',] if l];txt=lines[0] if lines else ''
    f=F(64);n=int(len(txt)*ease((t-s['a']-0.3)/1.4));d.text((960,250),txt[:0] if n<=0 else '',font=f,fill=INK)
    # strokes draw on (tally marks) + label reveals word by word, never mid-word
    for k in range(int(8*ease((t-s['a'])/2))):d.line(wob([(980+k*34,600),(995+k*34,700)],t,50+k),fill=INK,width=8)
    wsx=txt.split();m=max(1,int(len(wsx)*ease((t-s['a'])/1.5)+0.999)) if wsx else 0
    if m:
        fl,L=PL.wrap(d,F,' '.join(wsx[:m]),maxw=760,size=72,maxl=3,minsz=40)
        for j,l in enumerate(L):d.text((1320,300+j*fl.size*1.15),l,font=fl,fill=INK,anchor='ma')
    pose=['type','think','point_r'][b%3];grub(im,560,820,1.4,'point_r' if b%2 else 'think',t,'calm')
    pop(im,s['props'][0],300,420,170,T[0],t);pop(im,s['props'][1],820,330,150,T[1] if len(T)>1 else s['a']+1,t)
def T_storm(im,s,t,u,b):
    scene_bg(im,t,3,True);T=kwtimes(s);sh=6*math.sin(t*40)
    grub(im,760+sh,820,1.5,'shock',t,'worried',sweat=True)
    pop(im,s['props'][0],1350,330,260,T[0],t,rot=8*math.sin(t*3));pop(im,s['props'][1],1550,620,180,T[1],t)
    card(im,s['label'],1320,150,T[-1]+0.3,t,w=640)
def T_stamp(im,s,t,u,b):
    scene_bg(im,t,4,True);T=kwtimes(s)
    grub(im,420,820,1.4,'point_r',t,'angry');pop(im,s['props'][0],760,420,170,s['a'],t)
    x=1500-1100*(1-ease((t-s['a'])/0.35));pop(im,s['props'][1],x,560,180,s['a']+0.05,t,rot=-35)
    card(im,s['label'],1250,330,s['a']+0.3,t,mark='x',w=700)
def T_ridge(im,s,t,u,b):
    d=ImageDraw.Draw(im);sc=1+0.06*u
    for k,(c,y0) in enumerate([((150,168,150),420),((176,150,104),560),((214,186,138),720)]):
        r=random.Random(60+k);off=(t-s['a'])*(20+30*k)
        pts=[(x-off,y0+r.randint(-80,60)) for x in range(-200,W+400,200)]
        if k==0:d.rectangle([0,0,W,H],fill=SKY1)
        outline_poly(d,pts+[(W+400,H),(-200,H)],c,t,70+k)
    T=kwtimes(s);pop(im,s['props'][0],1180,330,120,T[0],t);d.line(wob([(1120,260),(1240,400)],t,5),fill=RED,width=12) if t>T[0]+0.3 and int(t*3)%2 else None
    grub(im,380,1000,1.2,'point_r',t,'worried')
def T_lock(im,s,t,u,b):
    scene_bg(im,t,5+b,True);T=kwtimes(s)
    grub(im,600,820,1.4,'look_up',t,'worried',qm=True)
    for j,e in enumerate(s['props']):pop(im,e,1150+j*300,360-40*j,200,T[min(j,len(T)-1)]+0.15*j,t,rot=-8+16*j)
    card(im,s['label'],1300,640,T[-1]+0.4,t,w=820)
def T_icons(im,s,t,u,b):
    scene_bg(im,t,6);d=ImageDraw.Draw(im);T=kwtimes(s);names=s['label'].split(' · ')
    grub(im,260,820,1.2,'point_r',t,'surprised')
    for j,e in enumerate(s['props']):
        x=600+j*350;pop(im,e,x,420,200,T[j],t)
        if t>T[j]+0.2:d.text((x,600),names[j] if j<len(names) else '',font=F(54),fill=INK,anchor='mm')
def T_calendar(im,s,t,u,b):
    scene_bg(im,t,7);d=ImageDraw.Draw(im);T=kwtimes(s)
    pop(im,s['props'][0],600,430,300,s['a'],t)
    d.line([(950,560),(1750,560)],fill=INK,width=8)
    for j,(lab,yr) in enumerate([('then',None),('',None)]):pass
    for j,yr in enumerate(['1990','1991','1992']):
        x=1050+j*300;d.line([(x,540),(x,580)],fill=INK,width=6);d.text((x,610),yr,font=F(44),fill=INK,anchor='ma')
    if t>T[0]:pop(im,'📍',1350,490,110,T[0],t)
    card(im,s['num'],1350,300,T[0]+0.3,t,w=640);grub(im,260,880,1.0,'think',t,'calm')
def T_hikers(im,s,t,u,b):
    scene_bg(im,t,8+int(t-s['a'])//3);T=kwtimes(s);x0=200+(t-s['a'])*170
    for k,col in enumerate([(220,60,50),(40,110,200)]):
        x=x0+k*230;ImageDraw.Draw(im).polygon([(x-30,560),(x+30,560),(x+38,690),(x-38,690)],fill=col)
        stick.draw(ImageDraw.Draw(im),x,820,1.25,'walk',t+k,INK,face=True,w=12);pop(im,s['props'][0],x-40,600,80,T[0]+0.2*k,t)
    pop(im,s['props'][1],1600,860,110,T[-1],t);card(im,s['label'],1250,170,T[0],t,w=760)
def T_map(im,s,t,u,b):
    d=ImageDraw.Draw(im);d.rectangle([0,0,W,H],fill=(232,216,180));T=kwtimes(s)
    alps=[(300,700),(500,520),(640,600),(820,420),(1000,560),(1180,380),(1380,540),(1600,470),(1700,700)]
    n=ease((t-s['a'])/1.0);m=max(2,int(len(alps)*n));outline_poly(d,alps[:m]+[(alps[m-1][0],760),(300,760)],(160,175,150),t,90)
    route=[(400,880),(600,800),(760,760),(900,640),(1000,560)];k=int(len(route)*ease((t-T[0])/1.2))
    for j in range(max(0,k-1)):
        a,bq=route[j],route[j+1]
        for q in range(6):
            if q%2==0:d.line([(a[0]+(bq[0]-a[0])*q/6,a[1]+(bq[1]-a[1])*q/6),(a[0]+(bq[0]-a[0])*(q+1)/6,a[1]+(bq[1]-a[1])*(q+1)/6)],fill=RED,width=8)
    pop(im,s['props'][0],220,200,160,s['a'],t);pop(im,s['props'][1],1000,500,120,T[-1],t)
    if t>T[-1]+0.2:card(im,s['label'],1000,300,T[-1]+0.2,t,w=600)
    grub(im,1620,1000,1.0,'point_l',t,'calm')
def T_altitude(im,s,t,u,b):
    scene_bg(im,t,9,True);d=ImageDraw.Draw(im);T=kwtimes(s);k=ease((t-T[0])/1.4)
    d.rectangle([1300,180,1380,900],fill=WH,outline=INK,width=7);d.rectangle([1306,min(894,900-714*k),1374,894],fill=(90,150,210))
    pop(im,s['props'][1],1000,520,320,s['a'],t);pop(im,s['props'][0],1340,950,70,s['a']+0.2,t)
    v=int(3210*k);d.text((1430,900-714*k-40),f'{v:,} m' if k<1 else s['num'],font=F(84),fill=INK)
    grub(im,380,880,1.2,'look_up',t,'surprised')
def T_find(im,s,t,u,b):
    scene_bg(im,t,10,True);d=ImageDraw.Draw(im);T=kwtimes(s)
    outline_poly(d,[(900,820),(1700,820),(1620,700),(980,700)],(190,225,240),t,95)
    pop(im,s['props'][0],1300,640,200,T[0],t)
    for k,col in enumerate([(220,60,50),(40,110,200)]):
        x=300+k*200;ImageDraw.Draw(im).polygon([(x-30,560),(x+30,560),(x+38,690),(x-38,690)],fill=col);stick.draw(d,x,820,1.25,'shock',t,INK,w=12)
    if t>T[-1]:grub(im,1300,780,0.9,'stand',t,'calm');d.rectangle([1150,700,1450,820],fill=(200,230,244));d.line([(1150,700),(1450,700)],fill=INK,width=6)
    if t>T[-1]+0.25:card(im,s['label'],1300,250,T[-1]+0.25,t,w=760)
TPL={k[2:]:v for k,v in globals().items() if k.startswith('T_')}
# ---- beats: hard cuts; long shots split into 2-4 s beats with a new composition each beat
BEATS=[]
for s in J['shots']:
    n=max(1,round((s['b']-s['a'])/3.2))
    for j in range(n):BEATS.append((s['a']+(s['b']-s['a'])*j/n,s['a']+(s['b']-s['a'])*(j+1)/n,s,j))
TOT=max(dur,J['shots'][-1]['b'])+0.3
p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',VO,
  '-filter_complex','[1:a]apad,atrim=0:%.3f,loudnorm=I=-14:TP=-1.5:LRA=11[a]'%TOT,'-map','0:v','-map','[a]','-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000',OUT],stdin=subprocess.PIPE)
nf=int(TOT*FPS);sheet=[]
for fi in range(nf):
    t=fi/FPS;be=[x for x in BEATS if x[0]<=t<x[1]] or [BEATS[-1]];a,b_,s,j=be[0]
    im=Image.new('RGB',(W,H),SKY1);u=(t-a)/max(0.01,b_-a)
    ss=dict(s);ss['a']=s['a']
    if j>0:  # new composition per beat: mirror + zoom
        TPL[s['tpl']](im,ss,t,u,j);im=im.transpose(Image.FLIP_LEFT_RIGHT) if s['tpl'] in ('lock','storm','hikers') and False else im
        z=1.12;cw,ch=int(W/z),int(H/z);cx=(W-cw)//2+(-1)**j*90;im=im.crop((cx,(H-ch)//2-40,cx+cw,(H-ch)//2-40+ch)).resize((W,H),Image.BICUBIC)
    else:TPL[s['tpl']](im,ss,t,u,j)
    draw_caps(im,t);p.stdin.write(im.tobytes())
    if fi%FPS==0:sheet.append(im.resize((320,180)))
p.stdin.close();p.wait()
cols=8;S=Image.new('RGB',(cols*320,math.ceil(len(sheet)/cols)*180));[S.paste(x,((k%cols)*320,(k//cols)*180)) for k,x in enumerate(sheet)]
S.save(OUT.replace('.mp4','_contact.png'));print('land render',OUT,len(BEATS),'beats',nf,'frames')
