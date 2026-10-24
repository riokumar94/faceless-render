"""Full whiteboard qc24. usage: python qc24_wb.py <dir with qc24_words.json,qc24_lines.json,qc24_vo.wav> <out.mp4> [stills]"""
import json,sys,time,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from wb import *
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
        out.append(x)
    S.append(dict(t0=t0,items=out,focus=focus))
def jar(cx,cy,col=(150,200,230),fill_to=0.5):
    top=cy-150+300*(1-fill_to)
    return Item(L((cx-120,cy-150),(cx-130,cy+150),(cx+130,cy+150),(cx+120,cy-150))+L((cx-145,cy-150),(cx+145,cy-150)),fill=[([(cx-122,top),(cx-127,cy+145),(cx+127,cy+145),(cx+122,top)],col)])
def piggy(cx,cy):
    st_=circ(cx,cy,230,0,360,ry=170)+circ(cx+240,cy-10,55,0,360,ry=65)+L((cx-70,cy-165),(cx-25,cy-240),(cx+10,cy-163))+L((cx-140,cy+130),(cx-140,cy+230))+L((cx+120,cy+130),(cx+120,cy+230))+L((cx-50,cy-160),(cx+70,cy-160))+circ(cx+120,cy-60,10)
    return Item(st_,fill=[(('circle',cx,cy,200),(247,170,190))])
def cal(cx,cy,top,big,bs=150):
    it=Item(rect(cx-220,cy-220,440,440)+L((cx-220,cy-120),(cx+220,cy-120))+L((cx-120,cy-260),(cx-120,cy-185))+L((cx+120,cy-260),(cx+120,cy-185)),fill=[([(cx-216,cy-216),(cx+216,cy-216),(cx+216,cy-124),(cx-216,cy-124)],R)])
    return [it,text(top,cx,cy-170,72,(255,255,255)),text(big,cx,cy+50,bs)]
def bank(cx,cy):
    return Item(poly((cx-230,cy-120),(cx,cy-260),(cx+230,cy-120))+rect(cx-210,cy-120,420,40)+L((cx-160,cy-80),(cx-160,cy+150))+L((cx-55,cy-80),(cx-55,cy+150))+L((cx+55,cy-80),(cx+55,cy+150))+L((cx+160,cy-80),(cx+160,cy+150))+rect(cx-240,cy+150,480,50),fill=[([(cx-230,cy-120),(cx,cy-260),(cx+230,cy-120)],(200,200,210))])
def letter(cx,cy):
    return Item(rect(cx-200,cy-130,400,260)+L((cx-200,cy-130),(cx,cy+20),(cx+200,cy-130)),fill=[([(cx-196,cy-126),(cx+196,cy-126),(cx+196,cy+126),(cx-196,cy+126)],(255,250,220))])
def scale_(cx,cy):
    return Item(L((cx,cy-250),(cx,cy+200))+L((cx-120,cy+200),(cx+120,cy+200))+L((cx-260,cy-200),(cx+260,cy-200))+L((cx-260,cy-200),(cx-320,cy-40),(cx-200,cy-40),(cx-260,cy-200))+L((cx+260,cy-200),(cx+200,cy-40),(cx+320,cy-40),(cx+260,cy-200)))
def doc(cx,cy):
    return Item(poly((cx-170,cy-230),(cx+110,cy-230),(cx+170,cy-170),(cx+170,cy+230),(cx-170,cy+230))+L((cx-110,cy-120),(cx+110,cy-120))+L((cx-110,cy-50),(cx+110,cy-50))+L((cx-110,cy+20),(cx+60,cy+20)),fill=[([(cx-166,cy-226),(cx+108,cy-226),(cx+166,cy-168),(cx+166,cy+226),(cx-166,cy+226)],(255,255,255))])
PX=290;PY=1250;SC=2.1   # big character, left
T=380
# 0 Three people earn the same interest on their savings
sc(0.0,[(person(200,1180,1.25,O),'three'),(person(540,1180,1.25,B),'people'),(person(880,1180,1.25,GR),'earn'),(text('SAME INTEREST',540,T,110),'interest'),
        (coin(200,1440,55),'savings'),(coin(540,1440,55),'savings'),(coin(880,1440,55),'savings')],focus=(540,1000))
# 1 One of them can't keep a single penny of it tax-free.
sc(st('one'),[(person(PX,PY,SC,B,'sad'),'one'),(coin(780,860,90,'1p'),'penny'),(cross(780,860,130),'penny'),(text('NOT TAX-FREE',540,T,115,R),'tax-free'),(text('WHY?',780,1250,150,R),'why')])
# 2-3 Why? It's called the Personal Savings Allowance.
sc(st('called'),[(piggy(540,1000),'personal'),(text('PERSONAL SAVINGS',540,T,100),'savings'),(text('ALLOWANCE',540,T+130,125,G),'allowance')])
# 4 It started in April twenty sixteen.
sc(st('started'),cal(540,950,'APRIL','2016',170)); S[-1]['items'][0].key='started';S[-1]['items'][1].key='april';S[-1]['items'][2].key='sixteen'
S[-1]['items'].append(text('SINCE',540,T,120));S[-1]['items'][-1].key='started'
# 5 Your allowance depends on your income tax band. (labels drawn with the steps)
stp=Item(L((100,1350),(100,1180),(400,1180),(400,980),(700,980),(700,780),(980,780),(980,1350),(100,1350)))
sc(st('allowance',11.8),[(text('YOUR TAX BAND',540,T,115),'depends'),(stp,'income'),(text('BASIC',250,1270,64),'income'),(text('HIGHER',550,1080,64),'tax'),(text('ADDITIONAL',840,880,54),'tax')],focus=(540,1000))
S[-1]['items'][-1].key='tax'
# 6 Basic-rate payers get up to one thousand pounds of interest tax-free.
sc(st('basic-rate'),[(person(PX,PY,SC,GR),'basic-rate'),(text('BASIC RATE',540,T,115),'payers'),(coin(780,820,110),'thousand'),(text('£1,000',780,1060,140,G),'pounds'),(tick(780,1230,80),'tax-free')])
# 7 Higher-rate payers get five hundred.
sc(st('higher-rate'),[(person(PX,PY,SC,B),'higher-rate'),(text('HIGHER RATE',540,T,115),'payers'),(coin(780,860,90),'five'),(text('£500',780,1080,150,(220,140,20)),'hundred')])
# 8 Additional-rate payers get nothing.
sc(st('additional-rate'),[(person(PX,PY,SC,P,'sad'),'additional-rate'),(text('ADDITIONAL RATE',540,T,100),'payers'),(text('£0',780,900,220,R),'nothing'),(cross(780,900,130),'nothing')])
# 9 And for 2026 to 2027, those limits are unchanged.
sc(st('and',23.5),cal(300,900,'TAX YEAR','26/27',150)+[(text('=',620,900,220)),(text('SAME',860,900,120,G)),(text('LIMITS UNCHANGED',540,1330,100))])
k=S[-1]['items'];k[0].key='for';k[1].key='twenty-six';k[2].key='twenty-seven';k[3].key='limits';k[4].key='unchanged';k[5].key='unchanged'
# 10 Go over, and you pay tax on the extra.
sc(st('go'),[(jar(380,1100,fill_to=0.95),'go'),(coin(380,890,50),'over'),(coin(450,810,50),'over'),(coin(340,740,50),'over'),(arrow((500,740),(760,620),R),'pay'),(text('TAX',860,570,140,R),'tax'),(text('ON THE EXTRA',540,1400,100),'extra')])
# 11 Gov.uk's example: thirteen hundred pounds of interest, basic rate.
sc(st("gov.uk's"),[(doc(540,900),"gov.uk's"),(text('EXAMPLE',540,T,125,B),'example')])
sc(st('thirteen'),[(coin(540,850,150),'thirteen'),(text('£1,300',540,1120,160),'pounds'),(text('INTEREST',540,1260,95),'interest'),(text('BASIC RATE',540,T,110,G),'rate')])
# 12 Three hundred is over the limit. Taxed at 20%, that's £60.
sc(st('three',35),[(jar(540,1100,fill_to=0.9),'three'),(text('£1,000 LIMIT',540,880,80),'limit'),(text('£300 OVER',540,T,130,R),'over')])
k=S[-1]['items'];k[1],k[2]=k[2],k[1]
sc(st('taxed'),[(text('£300',290,750,130),'taxed'),(text('x 20%',760,750,130,R),'percent'),(arrow((540,880),(540,1060)),'that\'s'),(text('£60 TAX',540,1200,180,R),'pounds')])
# 13-14 Watch out, though. Add your interest to your other income to find your band.
sc(st('watch'),[(person(PX,PY,SC,O,'flat','up'),'watch'),(text('WATCH OUT!',540,T,130,R),'though')])
sc(st('add'),[(coin(230,900,90),'interest'),(text('+',420,900,160),'other'),(doc(700,920),'income'),(text('= YOUR BAND',540,1300,120,B),'band'),(text('ADD IT UP',540,T,120),'add')])
k=S[-1]['items'];k.insert(0,k.pop())
# 15 Your interest counts as income, so it can tip you into a higher band.
sc(st('your',45.1),[(coin(540,900,140),'interest'),(text('COUNTS AS INCOME',540,T,105),'income')])
stp2=Item(L((140,1350),(140,1150),(540,1150),(540,900),(940,900),(940,1350),(140,1350)))
sc(st('so',46.5),[(stp2,'tip'),(text('BASIC',340,1260,70),'tip'),(text('HIGHER',740,1010,70,R),'higher'),(arrow((340,1120),(700,820),R),'higher'),(text('TIPPED UP',540,T,120,R),'band')],focus=(540,1050))
# 16-17 But here's the thing. There's a second allowance most people never hear of.
sc(st('but',49.5),[(person(PX,PY,SC,B,'smile','up'),'but'),(text('BUT...',760,800,150,B),'thing')])
sc(st("there's",50.9),[(piggy(380,1000),'second'),(piggy(800,700),'allowance'),(text('A 2ND ALLOWANCE',540,T,105,G),'allowance'),(text('LITTLE KNOWN',540,1400,95),'never')])
k=S[-1]['items'];k[1].fill=[(('circle',800,700,200),(170,220,170))]
# 18 If your other taxable income is under £17,570, up to £5,000 of interest can be taxed at zero.
sc(st('if',54.0),[(doc(540,980),'income'),(text('OTHER INCOME',540,T,110),'taxable'),(text('UNDER',540,T+140,90,B),'under')])
sc(st('seventeen'),[(text('£17,570',540,900,190,B),'seventy'),(text('INCOME LIMIT',540,T,110),'seventeen'),(arrow((540,1060),(540,1260)),'seventy')])
sc(st('up',59.5),[(coin(540,850,150),'five'),(text('£5,000',540,1110,170,G),'pounds'),(text('OF INTEREST',540,T,110),'interest')])
sc(st('can',61.8),[(text('0%',540,880,330,G),'zero'),(text('TAXED AT',540,T,120),'taxed'),(tick(540,1250,90),'zero')])
# 19 Every pound you earn above £12,570 shrinks it by a pound.
sc(st('every'),[(person(PX,PY,SC,GR),'every'),(coin(780,850,90),'pound'),(text('EARN ABOVE',540,T,115),'above')])
sc(st('twelve'),[(text('£12,570',540,820,190),'seventy'),(text('£1 MORE =',380,1150,95),'shrinks'),(text('£1 LESS',780,1150,95,R),'pound')])
# 20 ISA interest doesn't usually count at all.
sc(st('isa'),[(piggy(540,1000),'isa'),(text('ISA',540,1000,120),'isa'),(text('ISA INTEREST',540,T,115),'interest'),(text("DOESN'T COUNT",540,1420,100,G),'count')])
k=S[-1]['items'];k[0].fill=[(('circle',540,1000,200),(190,215,245))]
# 21 And banks report your interest, so HMRC may send you a calculation.
sc(st('and',71.8),[(bank(540,1000),'banks'),(arrow((540,700),(540,560),B),'report'),(text('BANKS REPORT IT',540,T,105),'interest')])
sc(st('so',73.5),[(letter(540,950),'send'),(text('HMRC',540,T,140,R),'hmrc'),(text('£ CALCULATION',540,1200,90),'calculation')])
# 22 Same interest. Very different bills.
sc(st('same',76.7),[(person(200,1180,1.25,O),'same'),(person(540,1180,1.25,B),'same'),(person(880,1180,1.25,GR),'interest'),(text('SAME INTEREST',540,T,115),'interest')],focus=(540,1000))
sc(st('very'),[(scale_(540,1000),'very'),(coin(220,800,40),'different'),(coin(860,800,40),'bills'),(coin(860,720,40),'bills'),(coin(860,640,40),'bills'),(text('DIFFERENT BILLS',540,T,110),'bills')])
# 23 General info, not financial advice.
sc(st('general'),[(doc(540,960),'general'),(text('GENERAL INFO',540,T,120),'info'),(text('NOT ADVICE',540,1330,110,R),'advice')])
END=words[-1][2]+0.4
for a,b in zip(S,S[1:]):a['t1']=b['t0']
S[-1]['t1']=END
for s in S: assert 0.4<s['t1']-s['t0']<4.6, (s['t0'],s['t1'])
if os.environ.get('DRY'):
    for s_ in S:
        for it in s_['items']:
            if it.key: word_end(words,it.key,s_['t0'],s_['t1'])
    print([(round(s_['t0'],2),round(s_['t1']-s_['t0'],2)) for s_ in S]);sys.exit()
t=time.time()
stills=[ (s['t0']+s['t1'])/2 if False else s['t1']-0.1 for s in S] if STILL else None
render(S,words,f'{D}/qc24_vo.wav',OUT,END,ends=ENDS,stills=stills)
print('render s',round(time.time()-t,1),'shots',len(S),'dur',round(END,2))
