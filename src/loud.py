# loud.py K [remux]: K_mix0.wav -> K_mix.wav at -14.0 LUFS, TP<=-1 (measured on AAC output)
import sys,subprocess,re,os
K=sys.argv[1];remux=len(sys.argv)>2
def meas(f):
    e=subprocess.run(['ffmpeg','-nostats','-i',f,'-map','0:a','-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
    s=e[e.rindex('Summary'):];return float(re.search(r'I:\s+(-?[\d.]+)',s).group(1)),float(re.search(r'Peak:\s+(-?[\d.]+)',s).group(1))
g=0.0;lim=-1.6
for it in range(9):
    af=f"volume={g}dB,aresample=192000,alimiter=limit={10**(lim/20):.4f}:level=false:attack=1:release=50,aresample=48000"
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',f'{K}_mix0.wav','-af',af,'-ar','48000',f'{K}_mix.wav'],check=True)
    if it==0:
        I,_=meas(f'{K}_mix0.wav');g=-14.0-I;continue
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',f'{K}_mix.wav','-c:a','aac','-b:a','192k',f'{K}_t.m4a'],check=True)
    I,TP=meas(f'{K}_t.m4a');print(K,'iter',it,'gain',round(g,2),'I',I,'TP',TP,flush=True)
    if abs(I+14)<=0.05 and TP<=-1.0: break
    if TP>-1.0: lim-=0.3
    g+=1.6*(-14.0-I)
os.remove(f'{K}_t.m4a')
if remux:
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',f'{K}.mp4','-i',f'{K}_mix.wav','-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',f'{K}_l.mp4'],check=True);os.replace(f'{K}_l.mp4',f'{K}.mp4')
    print(K,'final',meas(f'{K}.mp4'))
