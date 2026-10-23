import {registerRoot,Composition,useCurrentFrame,interpolate,AbsoluteFill} from 'remotion';
import React from 'react';
const C=()=>{const f=useCurrentFrame();const r=interpolate(f,[0,150],[0,360]);return <AbsoluteFill style={{background:'#f3ead7',alignItems:'center',justifyContent:'center'}}><svg width="800" height="800"><circle cx="400" cy="400" r="300" fill="none" stroke="#2b2118" strokeWidth="10" strokeDasharray={`${r/360*1885} 2000`}/></svg><div style={{fontSize:90,fontFamily:'Kalam'}}>frame {f}</div></AbsoluteFill>};
registerRoot(()=> <Composition id="T" component={C} durationInFrames={150} fps={30} width={1080} height={1920}/>);
