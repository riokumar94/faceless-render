# sketchlib.py - original vector "field-sketch" drawing kit (pycairo). All shapes drawn in code; no external images.
import cairo, math, random, numpy as np
W,H,FPS=1080,1920,30
INK=(0.16,0.12,0.08); RED=(0.80,0.22,0.16); ORANGE=(0.93,0.55,0.18); TEAL=(0.0,0.62,0.55); CREAM=(0.96,0.92,0.84)
FONT="Kalam"
def cl(x): return min(1.0,max(0.0,x))
def ease(x): x=cl(x); return x*x*(3-2*x)
def eout(x): x=cl(x); return 1-(1-x)**3
def eback(x):
    x=cl(x); k=1.70158; return 1+(k+1)*(x-1)**3+k*(x-1)**2
def pr(t,a,d=0.5): return ease((t-a)/d) if d>0 else float(t>=a)
def lerp(a,b,p): return a+(b-a)*p
def mix(c1,c2,p): return tuple(lerp(a,b,p) for a,b in zip(c1,c2))
# ---- paper grain (generated noise, not an asset)
_rng=np.random.default_rng(7); _n=_rng.integers(0,255,(H,W),dtype=np.uint8)
_a=np.zeros((H,W,4),np.uint8); al=22; v=(_n.astype(np.uint16)*al//255).astype(np.uint8)
_a[...,0]=v;_a[...,1]=v;_a[...,2]=v;_a[...,3]=al
GRAIN=cairo.ImageSurface.create_for_data(memoryview(_a),cairo.FORMAT_ARGB32,W,H)
def paper(c,top,bot,vig=0.35):
    g=cairo.LinearGradient(0,0,0,H); g.add_color_stop_rgb(0,*top); g.add_color_stop_rgb(1,*bot); c.set_source(g); c.paint()
    c.set_source_surface(GRAIN,0,0); c.paint()
    r=cairo.RadialGradient(W/2,H*0.42,W*0.3,W/2,H*0.45,H*0.75); r.add_color_stop_rgba(0,0,0,0,0); r.add_color_stop_rgba(1,0,0,0,vig); c.set_source(r); c.paint()
def pathlen(c):
    tot=0.0; last=None; st=None
    for typ,pts in c.copy_path_flat():
        if typ==cairo.PATH_MOVE_TO: last=st=pts
        elif typ==cairo.PATH_LINE_TO: tot+=math.dist(last,pts); last=pts
        elif typ==cairo.PATH_CLOSE_PATH: tot+=math.dist(last,st); last=st
    return tot
def ink(c,p=1,w=6,col=INK,a=1.0,keep=False):
    """stroke current path, revealed to fraction p (pen-drawing effect)"""
    if p<=0: c.new_path(); return
    L=pathlen(c); c.set_line_width(w); c.set_source_rgba(*col,a); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    if p<1: c.set_dash([max(0.01,L*p),L+10])
    (c.stroke_preserve if keep else c.stroke)(); c.set_dash([])
def wash(c,col,a=0.55,keep=True):
    c.set_source_rgba(*col,a); (c.fill_preserve if keep else c.fill)()
def text(c,s,x,y,size,col=INK,a=1.0,p=1.0,bold=True,anchor='c',outline=None,ow=10):
    if p<=0 or a<=0: return
    s2=s[:max(0,math.ceil(len(s)*cl(p)))]
    c.select_font_face(FONT,cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL); c.set_font_size(size)
    e=c.text_extents(s); ex=c.text_extents(s2) if s2 else None
    xx=x-e.width/2-e.x_bearing if anchor=='c' else (x if anchor=='l' else x-e.width)
    c.move_to(xx,y); c.text_path(s2)
    if outline: c.set_source_rgba(*outline,a); c.set_line_width(ow); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke_preserve()
    c.set_source_rgba(*col,a); c.fill()
def textw(c,s,size,bold=True):
    c.select_font_face(FONT,cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL); c.set_font_size(size); return c.text_extents(s).x_advance
def circle(c,x,y,r): c.new_sub_path(); c.arc(x,y,r,0,2*math.pi)
def ell(c,x,y,rx,ry,rot=0):
    c.save(); c.translate(x,y); c.rotate(rot); c.scale(rx,ry); c.new_sub_path(); c.arc(0,0,1,0,2*math.pi); c.restore()
def rrect(c,x,y,w,h,r):
    c.new_sub_path(); c.arc(x+w-r,y+r,r,-math.pi/2,0); c.arc(x+w-r,y+h-r,r,0,math.pi/2); c.arc(x+r,y+h-r,r,math.pi/2,math.pi); c.arc(x+r,y+r,r,math.pi,1.5*math.pi); c.close_path()
def poly(c,pts,close=True):
    c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]
    if close: c.close_path()
def wave(c,x0,x1,y,amp,kind,phase=0,n=400,p=1.0):
    """sound-wave line. kind: saw|alarm|click|flat|song"""
    xe=lerp(x0,x1,cl(p)); c.move_to(x0,y)
    for i in range(1,n+1):
        x=lerp(x0,x1,i/n)
        if x>xe: break
        u=(x-x0)/(x1-x0)
        if kind=='saw': v=((u*38+phase)%1)*2-1; v*= (0.6+0.4*math.sin(u*9+phase*3))
        elif kind=='alarm': v=(1 if math.sin(u*22*math.pi+phase*6)>0 else -1)*0.8*(0.6+0.4*abs(math.sin(u*5+phase)))
        elif kind=='click': v=math.exp(-((u*6+phase)%1)*14)*math.sin(u*300)
        elif kind=='song': v=math.sin(u*40+phase*4)*math.sin(u*7+phase)*0.9
        else: v=0
        c.line_to(x,y-amp*v)
def eucalyptus(c,x,base,h,sway,col,p=1,lw=6):
    c.move_to(x,base); c.curve_to(x+sway*0.3,base-h*0.4,x-sway*0.4,base-h*0.7,x+sway,base-h)
    ink(c,p,lw,col)
    if p>0.6:
        a=(p-0.6)/0.4
        for k in range(5):
            bx=x+sway*(0.6+0.1*k); by=base-h*(0.65+0.08*k); side=1 if k%2 else -1
            c.move_to(bx,by); c.curve_to(bx+side*60,by-30,bx+side*110,by-20,bx+side*150*a,by+10*a); ink(c,1,lw*0.6,col)
            for j in range(4):
                lx=bx+side*(40+30*j)*a; ly=by-18+j*6; ell(c,lx,ly+16,9,26,side*0.5)
                wash(c,mix(col,(0.3,0.5,0.35),0.6),0.45*a,keep=False)
# ------------- the lyrebird character (original drawing) -------------
BROWN=(0.55,0.38,0.24); RUST=(0.78,0.42,0.18)
def lyrebird(c,x,y,s=1.0,p=1.0,fan=0.0,nf=16,tilt=0.0,droop=0.0,beak=0.0,col=True,female=False,flip=False,fill=1.0):
    c.save(); c.translate(x,y); c.scale(-s if flip else s,s); lw=5.5/max(s,0.4)*min(s,1.4)
    lw=6/s
    pf=cl(p*1.6); pt=cl(p*1.6-0.6)
    # tail
    if not female:
        ca=math.radians(lerp(168,272,fan)+droop*35); sp=math.radians(lerp(14,150,fan)); Lf=lerp(300,250,fan)*(1-0.12*droop)
        bx,by=-78,8
        for i in range(nf):
            if nf==1: u=0.5
            else: u=i/15
            if i>15: break
            a=ca+sp*(u-0.5); outer=(i==0 or i==15)
            dx,dy=math.cos(a),math.sin(a); nx,ny=-dy,dx; side=-1 if u<0.5 else 1
            ex,ey=bx+dx*Lf,by+dy*Lf
            if outer:
                c.move_to(bx,by); c.curve_to(bx+dx*Lf*0.4+nx*side*45,by+dy*Lf*0.4+ny*side*45,bx+dx*Lf*0.8-nx*side*40,by+dy*Lf*0.8-ny*side*40,ex+nx*side*30,ey+ny*side*30)
                if col and fill>0: c.save(); ink(c,pt,22/s if True else 22,RUST,0.85*fill); c.restore()
                c.move_to(bx,by); c.curve_to(bx+dx*Lf*0.4+nx*side*45,by+dy*Lf*0.4+ny*side*45,bx+dx*Lf*0.8-nx*side*40,by+dy*Lf*0.8-ny*side*40,ex+nx*side*30,ey+ny*side*30)
                ink(c,pt,lw*1.1)
            else:
                c.move_to(bx,by); c.curve_to(bx+dx*Lf*0.5+nx*12,by+dy*Lf*0.5+ny*12,bx+dx*Lf*0.8,by+dy*Lf*0.8,ex,ey); ink(c,pt,lw*0.6,mix(INK,BROWN,0.4))
    # legs
    for lx in (8,-18):
        c.move_to(lx,48); c.line_to(lx-6,135); c.line_to(lx+22,140); c.move_to(lx-6,135); c.line_to(lx-26,142); ink(c,pf,lw*0.9)
    # body
    ell(c,0,0,92,58,-0.18)
    if col and fill>0: wash(c,(0.60 if not female else 0.66,0.45,0.32),0.6*fill*cl(p*2-0.4))
    ink(c,pf,lw)
    # wing hatch
    for k in range(5):
        c.move_to(-40+k*14,-20+k*4); c.curve_to(-10+k*14,-5+k*4,20+k*10,10,40,22); ink(c,pf,lw*0.5,mix(INK,BROWN,0.3))
    # neck + head
    c.save(); c.translate(62,-38); c.rotate(tilt)
    c.move_to(-8,8); c.curve_to(10,-20,20,-40,34,-50); c.move_to(14,16); c.curve_to(28,-6,40,-24,52,-36); ink(c,pf,lw)
    circle(c,44,-58,30)
    if col and fill>0: wash(c,(0.6,0.46,0.34),0.6*fill*cl(p*2-0.4))
    ink(c,pf,lw)
    circle(c,52,-64,5); c.set_source_rgba(*INK,cl(p*2-0.5)); c.fill()
    # beak
    ob=beak*0.45
    c.move_to(70,-66); c.line_to(104,-58-ob*30); c.line_to(72,-52); ink(c,pf,lw)
    if beak>0: c.move_to(72,-52); c.line_to(102,-46+ob*30); ink(c,pf,lw)
    c.restore(); c.restore()
def car(c,x,y,s,p,col=(0.3,0.5,0.8)):
    c.save(); c.translate(x,y); c.scale(s,s)
    c.move_to(-160,30); c.line_to(-160,-20); c.line_to(-110,-30); c.line_to(-70,-80); c.line_to(60,-80); c.line_to(110,-30); c.line_to(160,-20); c.line_to(160,30); c.close_path()
    wash(c,col,0.5*cl(p*2-1)); ink(c,p,6/s)
    for wx in (-95,95): circle(c,wx,32,32); wash(c,(0.25,0.25,0.25),0.8*cl(p*2-1)); ink(c,p,6/s)
    c.move_to(-60,-72); c.line_to(-90,-32); c.line_to(0,-32); c.line_to(0,-72); c.close_path(); ink(c,p,4/s)
    c.restore()
def camera(c,x,y,s,p,iris=0.0):
    c.save(); c.translate(x,y); c.scale(s,s)
    rrect(c,-170,-100,340,220,28); wash(c,(0.35,0.35,0.38),0.5*cl(p*2-1)); ink(c,p,6/s)
    c.move_to(-70,-100); c.line_to(-50,-140); c.line_to(50,-140); c.line_to(70,-100); ink(c,p,6/s)
    circle(c,0,10,80); wash(c,(0.15,0.2,0.3),0.6*cl(p*2-1)); ink(c,p,6/s)
    # iris blades
    r=70*(1-iris)
    for k in range(6):
        a=k*math.pi/3; c.move_to(r*math.cos(a),10+r*math.sin(a)); c.line_to(70*math.cos(a+1.0),10+70*math.sin(a+1.0)); ink(c,p,3/s)
    circle(c,0,10,max(2,r*0.7)); wash(c,(0.05,0.05,0.08),0.9*cl(p*2-1),keep=False)
    c.restore()
def chainsaw(c,x,y,s,p,col=(0.95,0.55,0.15)):
    c.save(); c.translate(x,y); c.scale(s,s)
    rrect(c,-200,-70,170,130,30); wash(c,col,0.6*cl(p*2-1)); ink(c,p,6/s)
    c.move_to(-30,-35); c.line_to(260,-30); c.arc(260,0,30,-math.pi/2,math.pi/2); c.line_to(-30,35); ink(c,p,6/s)
    for k in range(14): xx=-20+k*20; c.move_to(xx,-30); c.line_to(xx+10,-44); c.line_to(xx+20,-30); ink(c,p,3/s)
    c.move_to(-170,-70); c.curve_to(-160,-130,-80,-130,-60,-70); ink(c,p,6/s)
    c.restore()
def nest(c,x,y,s,p):
    c.save(); c.translate(x,y); c.scale(s,s)
    ell(c,0,0,160,55); wash(c,(0.5,0.38,0.22),0.6*cl(p*2-1)); ink(c,p,6/s)
    for k in range(16):
        a=k/16*math.pi; c.move_to(-150+k*19,-20+12*math.sin(k)); c.curve_to(-120+k*19,10,-100+k*19,30,-80+k*19,20); ink(c,p,2.5/s,mix(INK,BROWN,0.4))
    c.restore()
def snowflake(c,x,y,r,rot,a=1):
    c.save(); c.translate(x,y); c.rotate(rot)
    for k in range(6):
        c.save(); c.rotate(k*math.pi/3); c.move_to(0,0); c.line_to(0,-r); c.move_to(0,-r*0.6); c.line_to(-r*0.25,-r*0.8); c.move_to(0,-r*0.6); c.line_to(r*0.25,-r*0.8); c.restore()
    ink(c,1,4,(0.95,0.97,1.0),a); c.restore()
AUS=[(142.5,-10.7),(143.8,-14),(145.4,-15),(146,-18),(148.8,-20.3),(150.8,-22.7),(153.1,-25.8),(153.6,-28.6),(153,-31),(152,-32.8),(150.8,-34.6),(150,-37.5),(147.9,-37.9),(146.4,-39.1),(144.6,-38.3),(142,-38.4),(140.6,-38),(139.5,-36.8),(138,-35.6),(137.8,-33),(136,-34.8),(135.5,-34.8),(134.2,-32.8),(131,-31.5),(128,-32),(124,-33.8),(119.8,-34),(117.9,-35.1),(115,-34.3),(115.6,-33.3),(114.9,-29),(113.5,-26),(114,-22),(116.7,-20.6),(121,-19.5),(122.2,-17.2),(125.2,-14.5),(127.8,-14.3),(129.7,-15),(130.3,-12.6),(132.6,-11.5),(135.8,-12.2),(136.7,-12.3),(135.5,-14.9),(137.8,-16.5),(140.8,-17.4),(141.6,-13),(142.5,-10.7)]
TAS=[(144.6,-40.7),(148.3,-40.9),(148,-43.2),(146,-43.6),(144.7,-41.2)]
def heart(c,x,y,r):
    c.move_to(x,y+r); c.curve_to(x-r*1.6,y-r*0.2,x-r*0.8,y-r*1.4,x,y-r*0.5); c.curve_to(x+r*0.8,y-r*1.4,x+r*1.6,y-r*0.2,x,y+r); c.close_path()
