"""stick.py - reusable original stick-figure character for any channel (PIL only, free).
draw(d, x, y, s, pose, t, col, hat=None, face=True)
  x,y = feet position; s = scale (1.0 ~ 300 px tall); t = seconds (drives idle/gesture motion)
  poses: stand, walk, point_up, point_r, point_l, shrug, shock, shush, think, look_up, weld, cheer, type
Poses are joint angles (deg, 0 = straight down); pose_mix() blends two poses for smooth transitions.
"""
import math
P={ # (l_upper,l_fore,r_upper,r_fore,l_thigh,l_shin,r_thigh,r_shin,head_tilt,lean)
 'stand':(15,10,-15,-10,6,0,-6,0,0,0),
 'walk':(15,10,-15,-10,6,0,-6,0,0,0),
 'point_up':(15,10,-160,-170,6,0,-6,0,-12,-3),
 'look_up':(20,30,-20,-30,6,0,-6,0,-25,-4),
 'point_r':(15,10,-95,-90,6,0,-6,0,0,0),
 'point_l':(95,90,-15,-10,6,0,-6,0,0,0),
 'shrug':(60,150,-60,-150,6,0,-6,0,10,0),
 'shock':(140,170,-140,-170,14,0,-14,0,0,6),
 'shush':(15,10,-40,-170,6,0,-6,0,4,0),
 'think':(15,10,-35,-160,6,0,-6,0,8,2),
 'weld':(70,95,-70,-95,25,-40,-10,5,10,6),
 'cheer':(150,175,-150,-175,10,0,-10,0,-5,0),
 'type':(55,95,-55,-95,80,-90,80,-90,5,4),
}
def pose_mix(a,b,u):
    A,B=P[a] if isinstance(a,str) else a,P[b] if isinstance(b,str) else b
    return tuple(x+(y-x)*u for x,y in zip(A,B))
def _seg(x,y,ang,L):
    r=math.radians(ang);return x+L*math.sin(r),y+L*math.cos(r)
def draw(d,x,y,s,pose,t=0.0,col=(255,255,255),hat=None,face=True,w=None):
    q=list(P[pose] if isinstance(pose,str) else pose)
    if pose=='walk':
        ph=math.sin(t*7);q=[25*ph,10,-25*ph,-10,-25*ph,10*max(0,ph),25*ph,10*max(0,-ph),0,0]
    else:  # idle breathing / gesture wobble so the figure is never frozen
        b=math.sin(t*3)*4;q[0]+=b;q[2]-=b;q[1]+=b;q[3]-=b
    w=w or max(3,int(9*s));U,F,TH,SH,BODY,HR=55*s,50*s,60*s,58*s,105*s,30*s
    lean=q[9];hipx,hipy=x,y-(TH+SH)*(0.82 if pose=='type' else 1)
    nx,ny=_seg(hipx,hipy,180+lean,BODY)
    for th,sh in ((q[4],q[5]),(q[6],q[7])):
        kx,ky=_seg(hipx,hipy,th,TH);fx,fy=_seg(kx,ky,th+sh,SH);d.line([(hipx,hipy),(kx,ky),(fx,fy)],fill=col,width=w,joint='curve')
    d.line([(hipx,hipy),(nx,ny)],fill=col,width=w)
    sx,sy=_seg(nx,ny,lean,12*s)
    for up,fo in ((q[0],q[1]),(q[2],q[3])):
        ex,ey=_seg(sx,sy,up,U);hx,hy=_seg(ex,ey,fo,F);d.line([(sx,sy),(ex,ey),(hx,hy)],fill=col,width=w,joint='curve')
        d.ellipse([hx-w*0.9,hy-w*0.9,hx+w*0.9,hy+w*0.9],fill=col)
    hx,hy=_seg(nx,ny,180+lean+q[8]*0.3,HR+2*s)
    d.ellipse([hx-HR,hy-HR,hx+HR,hy+HR],outline=col,width=w)
    if face:
        ex=6*s*(1 if pose!='point_l' else -1);ey=-4*s+(q[8]*0.25*s)
        for dx in (-9*s,9*s): d.ellipse([hx+dx+ex-3.5*s,hy+ey-3.5*s,hx+dx+ex+3.5*s,hy+ey+3.5*s],fill=col)
        if pose=='shock': d.ellipse([hx+ex-6*s,hy+8*s,hx+ex+6*s,hy+20*s],outline=col,width=max(2,w//2))
        elif pose=='shrug': d.line([(hx+ex-8*s,hy+14*s),(hx+ex+8*s,hy+12*s)],fill=col,width=max(2,w//2))
        else: d.arc([hx+ex-10*s,hy+2*s,hx+ex+10*s,hy+16*s],20,160,fill=col,width=max(2,w//2))
    if hat=='hardhat':
        hc=(255,200,40);d.chord([hx-HR*1.1,hy-HR*1.35,hx+HR*1.1,hy+HR*0.5],180,360,fill=hc);d.rectangle([hx-HR*1.35,hy-HR*0.45,hx+HR*1.35,hy-HR*0.3],fill=hc)
    elif hat=='mask':  # welding mask
        d.rectangle([hx-HR*1.05,hy-HR*0.9,hx+HR*1.05,hy+HR*0.9],fill=(70,70,80));d.rectangle([hx-HR*0.7,hy-HR*0.3,hx+HR*0.7,hy+HR*0.05],fill=(40,200,120))
    return hx,hy
