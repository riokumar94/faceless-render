import json,subprocess,time,sys,re,numpy as np,soundfile as sf
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import os;sys.path.insert(0,'/workspace/studio/ch3');import chan
t0=time.time();W,H,FPS=1080,1920,30;ch=sys.argv[1];n=int(sys.argv[2]);C=chan.C[ch];os.chdir(C['dir']);K=f'{ch}{n:02d}';XF=0.7
V=[v for v in json.load(open(f'{ch}_scripts.json')) if v['n']==n][0]
words=json.load(open(f'{K}_words.json'));vo,sr=sf.read(f'{K}_vo.wav');TEND=len(vo)/sr+0.4;CARD=2.5;DUR=TEND+CARD
# word-by-word caption check against the script text
TW=V['vo'].split();norm=lambda s:re.sub(r'[^a-z0-9]','',s.lower())
caps=[];i=0
for tw in TW:
    tgt=norm(tw)
    if not tgt: continue
    acc='';st=None
    while acc!=tgt:
        assert i<len(words),('ran out',tw);acc+=norm(words[i][0]);st=st if st is not None else words[i][1];en=words[i][2];i+=1
        assert len(acc)<=len(tgt) or tgt.startswith(acc) or acc.startswith(tgt),(tw,acc)
        if len(acc)>len(tgt): raise SystemExit(f'CAPTION MISMATCH {tw} vs {acc}')
    caps.append((tw,st,en))
assert i==len(words),('extra tokens',i,len(words));print('captions verified',len(caps),'words')
import glob
from PIL import ImageOps
files=sorted(glob.glob(f'img/{K}_0_x2.png'))+sorted(glob.glob(f'img/{K}_s*.jpg'))+sorted(glob.glob(f'img/{K}_1_x2.png'))
assert len(files)>=3,('not enough images',files)
imgs=[ImageOps.fit(ImageOps.exif_transpose(Image.open(f)).convert('RGB'),(int(W*1.25),int(H*1.25)),Image.LANCZOS) for f in files];NI=len(imgs);print('images',files)
# 3 stills reused as 6 shots with different crops/moves
segs=max(1,int(round(TEND/2.5)));L=TEND/segs;XF=0.25
BASE=[(1.0,1.12,0,-40),(1.12,1.0,40,0),(1.0,1.1,-60,30),(1.15,1.05,60,-40),(1.0,1.15,-30,0),(1.08,1.2,30,-60),(1.2,1.08,-40,50)]
SH=[(k%NI,)+BASE[(k*5+k//3)%len(BASE)] for k in range(segs)]
def shot(k,t):
    j,z0,z1,px,py=SH[k];u=min(max((t-k*L)/(L+XF),0),1);u=u*u*(3-2*u);z=(z0+(z1-z0)*u)/1.25;im=imgs[j]
    w,h=int(im.width*z),int(im.height*z);w=max(w,W);h=max(h,H)
    cx=im.width/2+px*(1 if z0>1.3 else u);cy=im.height/2+py*(1 if z0>1.3 else u)
    bw,bh=W/z,H/z;x0=min(max(cx-bw/2,0),im.width-bw);y0=min(max(cy-bh/2,0),im.height-bh)
    return np.asarray(im.transform((W,H),Image.EXTENT,(x0,y0,x0+bw,y0+bh),Image.BICUBIC),np.float32)
F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',70);FT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',60)
ch=[];cur=[]
for k,c in enumerate(caps):
    cur.append(c)
    if len(cur)==4 or k+1==len(caps) or c[0][-1] in '.,:;!?"': ch.append(cur);cur=[]
CY=C['hi'];OR=C['acc'] if ch!='qm' else (255,128,0)
def draw_caps(im,t):
    c=[c for c in ch if c[0][1]-0.05<=t<=c[-1][2]+0.2]
    if not c:return
    c=c[-1];d=ImageDraw.Draw(im);txt=[w[0].strip('"') for w in c]
    lines=[list(zip(txt,c))] if d.textlength(' '.join(txt),font=F)<920 else [list(zip(txt[:2],c[:2])),list(zip(txt[2:],c[2:]))]
    y=1320;bw=max(d.textlength(' '.join(a for a,_ in l),font=F) for l in lines)
    d.rounded_rectangle([(W-bw)/2-30,y-20,(W+bw)/2+30,y+len(lines)*88+10],22,fill=C['bg'])
    d.rectangle([(W-bw)/2-30,y+len(lines)*88+10,(W-bw)/2+90,y+len(lines)*88+18],fill=OR)
    for ln in lines:
        x=(W-d.textlength(' '.join(a for a,_ in ln),font=F))/2
        for a,w in ln:
            d.text((x,y),a,font=F,fill=CY if w[1]<=t+0.02 else (245,245,245));x+=d.textlength(a+' ',font=F)
        y+=88
FH=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',80)
def hook(im):
    d=ImageDraw.Draw(im);words=V['title'].upper().split();lines=[];cur=''
    for w in words:
        if d.textlength(cur+' '+w,font=FH)>900: lines.append(cur);cur=w
        else: cur=(cur+' '+w).strip()
    lines.append(cur);y=330
    for l in lines:
        tw=d.textlength(l,font=FH);d.rectangle([(W-tw)/2-24,y-12,(W+tw)/2+24,y+96],fill=CY if l==lines[0] else C['bg']);d.text(((W-tw)/2,y),l,font=FH,fill=(0,0,0) if l==lines[0] else (255,255,255));y+=112
def card():
    im=Image.new('RGB',(W,H),(14,15,18));d=ImageDraw.Draw(im)
    for s,f,y,col in [(C['name'],FT,860,CY),(C.get('card','Follow for more.'),F,960,(240,240,240)),('' if ch=='ogu' else C['handle'],FT,1080,OR)]:
        d.text(((W-d.textlength(s,font=f))/2,y),s,font=f,fill=col)
    return np.asarray(im,np.float32)
CARDA=card()
# audio: VO + soft self-generated pad, loudnorm to -14 LUFS later
n_=int(DUR*sr);au=np.zeros(n_);au[int(0.4*sr):int(0.4*sr)+len(vo)]+=vo
tt=np.arange(n_)/sr
# generated music bed: soft chord arpeggio, set ~ -24 dB below voice RMS
notes=[220,277.2,329.6,440,329.6,277.2];bed=np.zeros(n_)
for q in range(int(DUR*4)):
    f=notes[q%6]*(1 if (q//24)%2==0 else 0.89);a0=int(q*0.25*sr);seg=np.arange(min(int(0.6*sr),n_-a0))/sr
    bed[a0:a0+len(seg)]+=np.sin(2*np.pi*f*seg)*np.exp(-seg*5)
bed+=0.4*np.sin(2*np.pi*110*tt)*(0.5+0.5*np.sin(2*np.pi*0.1*tt))
vr=np.sqrt((vo**2).mean());bed*=vr*10**(-24/20)/np.sqrt((bed**2).mean());au+=bed
# generated SFX: soft whoosh on every cut, low hit on first frame and end card
for k in range(1,segs):
    a0=int((k*L-0.15)*sr);m=int(0.3*sr);nz=np.random.default_rng(k).standard_normal(m);nz=np.convolve(nz,np.ones(30)/30,'same')
    au[a0:a0+m]+=nz[:len(au[a0:a0+m])]*np.hanning(m)[:len(au[a0:a0+m])]*vr*0.35
for a0 in (0,int(TEND*sr)):
    m=int(0.5*sr);seg=np.arange(m)/sr;hit=np.sin(2*np.pi*60*seg*np.exp(-seg*3))*np.exp(-seg*8);au[a0:a0+m]+=hit[:len(au[a0:a0+m])]*vr*1.2
fd=np.minimum(1,np.minimum(np.arange(n_),n_-np.arange(n_))/(0.3*sr));sf.write(f'{K}_mix0.wav',au*fd*0.9,sr)
subprocess.run([sys.executable,'/workspace/studio/ch3/loud.py',K],check=True)
p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-i',f'{K}_mix.wav','-c:v','libx264','-preset','medium','-pix_fmt','yuv420p','-crf','20','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',f'{K}.mp4'],stdin=subprocess.PIPE)
rng=np.random.default_rng(n);pts=rng.random((40,3))
for k in range(int(DUR*FPS)):
    t=k/FPS
    if t<TEND+XF:
        s=min(int(t//L),segs-1);o=shot(s,t)
        if s+1<segs and t>(s+1)*L-XF: w=(t-((s+1)*L-XF))/XF;o=o*(1-w)+shot(s+1,t)*w
        if t>=TEND: a=min(1,(t-TEND)/XF);o=o*(1-a)+CARDA*a
    else:o=CARDA
    im=Image.fromarray(np.uint8(np.clip(o,0,255)))
    if t<2.2: hook(im)
    if t<TEND:
        d=ImageDraw.Draw(im)
        for x,y,s2 in pts:
            yy=(y*H-t*(20+30*s2))%H;xx=x*W;r=1.5+2*s2;d.ellipse([xx-r,yy-r,xx+r,yy+r],fill=CY if s2>.5 else OR)
        draw_caps(im,t-0.4)
    p.stdin.write(im.tobytes())
p.stdin.close();p.wait()
desc=f"{V['title']}\n\n{V['tags']} #{C['handle'][1:]}\n\nVisuals are AI-generated (FLUX.1-schnell) and the voiceover is AI-synthesised (Kokoro TTS, voice {C['voice']}). Script written and fact-checked by our team. Educational content."+("\nArtwork: public-domain paintings via Wikimedia Commons (see sources.txt)." if ch=='ogu' else "")+""
open(f'{K}_description.txt','w').write(desc);print(K,'render',round(time.time()-t0),'s dur',round(DUR,1))
