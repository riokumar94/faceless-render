import re,json
C={'qm':dict(dir='/workspace/studio/ch3',src='science_week1_scripts.md',voice='af_bella',lang='a',name='QUARK MINUTE',handle='@QuarkMinute',hi=(0,229,255),acc=(255,128,0),bg=(18,20,24),
      style=" Cinematic scientific digital art, graphite black tones, electric cyan and signal orange highlights, sharp detail, no text.",ai="FLUX.1-schnell"),
   'nm':dict(dir='/workspace/studio/ch4',src='neuralminute_week1_scripts.md',voice='bf_emma',lang='b',name='NEURAL MINUTE',handle='@NeuralMinuteUK',hi=(57,255,20),acc=(255,255,255),bg=(8,10,8),
      style=" Sleek editorial tech illustration, deep black background, acid green neon accents and white highlights, crisp, high detail, no text, no logos.",ai="FLUX.1-schnell"),
   'hib':dict(dir='/workspace/studio/ch5',src='howitsbuilt_week1_scripts.md',voice='am_fenrir',lang='a',name="HOW IT'S BUILT",handle='@HowItsBuilt',hi=(255,196,0),acc=(255,255,255),bg=(40,42,46),
      style=" Detailed industrial cutaway illustration, steel grey and concrete tones with safety yellow highlights, technical blueprint feel, sharp, no text.",ai="FLUX.1-schnell")}
C['ogu']=dict(dir='/workspace/studio/ch2',src=None,voice='bm_fable',lang='b',name='OLD GODS UNSPUN',handle='Retold from Greek mythology.',hi=(240,190,95),acc=(200,170,130),bg=(20,12,8),style='',ai='FLUX.1-schnell',card='Retold from Greek mythology.')
C['mf']=dict(dir='/workspace/studio/ch6',src='mindfacts_week1_scripts.md',voice='af_heart',lang='a',name='MIND FACTS MINUTE',handle='@MindFactsMinute',hi=(200,150,255),acc=(255,255,255),bg=(40,20,60),style=' Soft surreal editorial illustration, deep plum and lavender palette, gentle light, no text.',ai='FLUX.1-schnell')
C['af']=dict(dir='/workspace/studio/ch7',src='animalfacts_week1_scripts.md',voice='am_puck',lang='a',name='ANIMAL FACTS MINUTE',handle='@AnimalFactsMinute',hi=(0,210,180),acc=(255,170,60),bg=(30,40,35),style=' Vivid wildlife photography style, natural light, sharp detail, no text.',ai='FLUX.1-schnell')
FIX={'qm':[("That delay isn't special to the Sun. It applies to everything.","That delay isn't special to the Sun. Light from everything you see is old, not just sunlight.")],'nm':[('about about','about'),('Who checked? Nobody.','Who checked? Nobody independent, yet.')]}
def scripts(ch):
    if ch=='ogu': return [dict(n=1,title='Orpheus and Eurydice',hook='',vo=open('/workspace/studio/ch2/orph.txt').read().strip(),tags='#greekmythology #orpheus #mythology #OldGodsUnspun')]
    s=open('/workspace/scripter/'+C[ch]['src']).read()
    for a,b in FIX.get(ch,[]): s=s.replace(a,b)
    V=[]
    for blk in re.split(r'\n## ',s)[1:]:
        t=blk.split('\n')[0];hook=re.search(r'Hook: "(.*)"',blk).group(1);vo=re.search(r'VO: "(.*)"',blk).group(1);tg=re.search(r'Hashtags: (.*)',blk)
        V.append(dict(n=int(t.split('.')[0]),title=re.sub(r'^\d+\. ','',t).split(' (')[0],hook=hook,vo=(vo if vo.strip().startswith(hook[:30]) else hook+' '+vo).replace('**',''),tags=tg.group(1) if tg else ''))
    return V
C['bf']=dict(dir='/workspace/studio/ch8',src='breachfiles_week1_scripts.md',voice='bm_george',lang='b',name='BREACH FILES',handle='@BreachFilesUK',hi=(0,255,110),acc=(255,60,60),bg=(6,10,20),style='',ai='none')
_scripts=scripts
def scripts(ch):
    if ch!='bf': return _scripts(ch)
    s=open('/workspace/scripter/'+C[ch]['src']).read();V=[]
    for blk in re.split(r'\n## ',s)[1:]:
        L=blk.strip().split('\n');t=L[0];n=int(re.match(r'BF(\d+)',t).group(1));title=re.sub(r'^BF\d+: ','',t).split('. Hook')[0]
        body=[l for l in L[1:] if l.strip() and not l.startswith(('Source','Hashtags','#','Title','Description','---'))]
        vo=' '.join(body).replace('**','');V.append(dict(n=n,title=title,hook=body[0],vo=vo,tags='#cybersecurity #hacking #BreachFiles'))
    return V
