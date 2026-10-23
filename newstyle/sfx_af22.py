# Synthesises all AF22 SFX procedurally (numpy only) -> sfx.wav ; no samples used.
import numpy as np, wave, sys
SR=48000; DUR=71.64; N=int(SR*DUR); rng=np.random.default_rng(22)
out=np.zeros(N)
def T(n): return np.arange(n)/SR
def place(sig,t0,g):
    i=int(t0*SR); j=min(N,i+len(sig)); out[i:j]+=g*sig[:j-i]
def env(n,a,r):
    e=np.ones(n); na=int(a*SR); nr=int(r*SR); e[:na]=np.linspace(0,1,na); e[n-nr:]=np.linspace(1,0,nr); return e
def lp(x,k): # one-pole lowpass, k in (0,1)
    y=np.empty_like(x); s=0.
    for i in range(len(x)): s+=k*(x[i]-s); y[i]=s
    return y
# forest ambience: brown-ish wind + leaf rustle + chirps
wn=np.cumsum(rng.standard_normal(N)); wn-=np.convolve(wn,np.ones(4801)/4801,'same'); wn/=np.abs(wn).max()
gust=0.6+0.4*np.sin(2*np.pi*T(N)*0.07)*np.sin(2*np.pi*T(N)*0.031+1)
amb=wn*gust*0.5
def chirp(f0,f1,d,vib=0):
    t=T(int(d*SR)); f=np.linspace(f0,f1,len(t))+vib*np.sin(2*np.pi*35*t)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*t/d)**2
t=0.4
while t<DUR-1:
    k=rng.integers(3)
    for m in range(rng.integers(1,4)):
        if k==0: s=chirp(3200,4800,0.09)
        elif k==1: s=chirp(5200,2600,0.14,300)
        else: s=chirp(2400,2500,0.25,600)
        place(s,t+m*0.16,0.10)
    t+=rng.uniform(0.9,2.6)
amb_sig=amb.copy()
# stillness 63.8-65.6: duck ambience
tt=T(N); duck=np.ones(N); m=(tt>63.6)&(tt<65.8); duck[m]=0.15
out=out*duck; amb_sig*=duck
out+=amb_sig*0.25
# chainsaw (bird-mimic flavour: tonal sawtooth + rasp + rev curve)
def saw(d,rev=True):
    n=int(d*SR); t=T(n); f=95+ (60*np.clip(np.sin(np.pi*t/d*1.3),0,1) if rev else 0) + 6*np.sin(2*np.pi*7*t)
    ph=np.cumsum(f)/SR; x=2*(ph%1)-1; x+=0.5*(2*((ph*2.02)%1)-1)
    x+=0.35*rng.standard_normal(n)*(0.5+0.5*np.sign(np.sin(2*np.pi*f*t)))
    x=np.tanh(2.2*x); x=lp(x,0.35); return x*env(n,0.08,0.25)/1.4
place(saw(2.0),2.05,0.55); place(saw(1.1),50.5,0.25); place(saw(1.4),62.0,0.45)
# car alarm: two-tone warble
n=int(0.85*SR); t=T(n); f=np.where((t*6)%1<0.5,1450,950); x=np.sign(np.sin(2*np.pi*np.cumsum(f)/SR)); place(lp(x,0.3)*env(n,0.02,0.1),5.25,0.22)
# camera shutter: two-stage click + mirror slap
def click():
    n=int(0.12*SR); t=T(n); a=rng.standard_normal(n)*np.exp(-t*90); b=np.zeros(n); i=int(0.045*SR); b[i:]=rng.standard_normal(n-i)*np.exp(-(t[i:]-t[i])*120)
    return (a+0.8*b+0.6*np.sin(2*np.pi*2200*t)*np.exp(-t*60))/2
place(click(),6.32,0.5); place(click(),7.3,0.5)
# soft reel whir under 'recording' and tape rewind whoosh at 61.5
n=int(0.9*SR); t=T(n); place(lp(rng.standard_normal(n),0.05)*env(n,0.2,0.3)*3*np.sin(2*np.pi*np.linspace(30,8,n)*t)**2,61.3,0.25)
out/=max(1,np.abs(out).max()/0.9)
w=wave.open(sys.argv[1],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype('<i2').tobytes()); w.close()
