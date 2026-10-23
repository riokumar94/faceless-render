"""motion_job.py <ch> <n> [--lines FILE.json] [--plan PK] [--dir D] [--key K]
Writes <D>/<K>_motion.json for motion.py (portable, no /workspace/scripter needed in the cloud).
Lines default: the '> ' lines of the channel's scripter week-2 md (read only). Must join to scripts.json vo."""
import sys,os,json,re,argparse
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));import chan
a=argparse.ArgumentParser();a.add_argument('ch');a.add_argument('n',type=int);a.add_argument('--lines');a.add_argument('--plan');a.add_argument('--dir');a.add_argument('--key')
a=a.parse_args();C=dict(chan.C[a.ch]);K0=f'{a.ch}{a.n:02d}';D=a.dir or C['dir'];K=a.key or K0
MD={'csf':'/workspace/scripter/week2/city_skyline_files_week2.md'}
V=[v for v in json.load(open(f"{C['dir']}/{a.ch}_scripts.json")) if v['n']==a.n][0]
if a.lines: LN=json.load(open(a.lines))
else:
    blk=[b for b in open(MD[a.ch]).read().split('\n## ') if b.upper().startswith(f'{K0.upper()} ')][0]
    LN=[re.sub(r'\*\*','',l[2:]).strip() for l in blk.splitlines() if l.startswith('> ')]
if ' '.join(LN)!=V['vo']: raise SystemExit(f'{K0}: script lines do not match {a.ch}_scripts.json vo - re-sync scripts.json/VO first')
C.pop('dir',None);C.pop('src',None)
json.dump({'chan':C,'plan':a.plan or K0,'script':{k:V[k] for k in ('title','vo','tags') if k in V},'lines':LN},open(f'{D}/{K}_motion.json','w'),indent=1)
print('wrote',f'{D}/{K}_motion.json',len(LN),'lines')
