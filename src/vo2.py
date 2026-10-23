import sys,os,json,numpy as np,soundfile as sf
sys.path.insert(0,'/workspace/studio/ch3');import chan
from kokoro import KPipeline
ch=sys.argv[1];c=chan.C[ch];os.chdir(c['dir']);V=json.load(open(f'{ch}_scripts.json')) if os.environ.get('USEJSON') else chan.scripts(ch)
if not os.environ.get('USEJSON'): json.dump(V,open(f'{ch}_scripts.json','w'),indent=1)
p=KPipeline(lang_code=c['lang'],repo_id='hexgrad/Kokoro-82M')
def run(t,sp,gap):
    off=0;W=[];A=[]
    for r in p(t,voice=c['voice'],speed=sp,split_pattern=None):  # one continuous pass (G's fix)
        a=r.audio.numpy();nz=np.where(np.abs(a)>0.01)[0];s0=max(0,nz[0]-960) if len(nz) else 0;a=a[s0:nz[-1]+960] if len(nz) else a;sh=s0/24000  # trim edge silence to 0.04s
        A+=[a,np.zeros(int(gap*24000))]
        for k in r.tokens:
            if k.start_ts is not None and any(q.isalnum() for q in k.text): W.append((k.text,max(0,off+k.start_ts-sh),min(off+k.end_ts-sh,off+len(a)/24000)))
        off+=len(a)/24000+gap
    return np.concatenate(A),W,off
ONLY=sys.argv[2:]
for v in V:
    K=f"{ch}{v['n']:02d}"
    if ONLY and K not in ONLY: continue
    if not ONLY and os.path.exists(K+'_vo.wav'): continue
    sp=float(os.environ.get('SP0','0.92'))
    while True:
        a,W,d=run(v['vo'],sp,0.0)
        wpm=len(W)/max(1e-6,W[-1][2])*60
        if (d>=63.5-3.3 and wpm<=172) or sp<=0.7: break
        sp-=0.04
    sf.write(K+'_vo.wav',a,24000);json.dump(W,open(K+'_words.json','w'));print(K,'speed',round(sp,2),'dur',round(d,1),flush=True)
