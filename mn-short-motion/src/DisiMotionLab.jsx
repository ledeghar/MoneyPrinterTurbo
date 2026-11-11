import React from "react";
import {AbsoluteFill,Sequence,interpolate,spring,useCurrentFrame,useVideoConfig} from "remotion";
const color={navy:"#041422",blue:"#0d2c48",cyan:"#79d3f2",red:"#e52d4d",white:"#f8fbff",muted:"#aecadd"};
const clamp={extrapolateLeft:"clamp",extrapolateRight:"clamp"};
function Frame({step,children}){
 const f=useCurrentFrame();
 const progress=interpolate(f,[0,120],[0,100],clamp);
 return <AbsoluteFill style={{background:"radial-gradient(ellipse at 73% 20%,#164265,#061726 57%,#030b14)",color:color.white,fontFamily:"Arial,sans-serif",overflow:"hidden"}}>
   <div style={{position:"absolute",inset:0,backgroundSize:"85px 85px",opacity:.1,backgroundImage:"linear-gradient(#bdd3e5 1px,transparent 1px),linear-gradient(90deg,#bdd3e5 1px,transparent 1px)"}}/>
   <div style={{position:"absolute",top:65,left:70,fontWeight:900,fontSize:32,letterSpacing:4}}>DISI <span style={{color:color.cyan}}>/ MOTION LAB</span></div>
   <div style={{position:"absolute",top:70,right:70,color:color.muted,fontSize:25}}>{step}</div>
   <div style={{position:"absolute",top:135,left:70,right:70,height:4,background:"#2c4c66"}}><div style={{width:progress+"%",height:"100%",background:color.red}}/></div>
   {children}
   <div style={{position:"absolute",bottom:65,left:70,right:70,fontSize:27,color:"#ff8b9e",fontWeight:850,letterSpacing:2}}>BORRADOR · NO PUBLICAR · SIN CIERRE V6</div>
 </AbsoluteFill>;
}
function Kinetic(){
 const f=useCurrentFrame(),{fps}=useVideoConfig();
 return <Frame step="01 / TIPOGRAFÍA">
 <div style={{position:"absolute",top:445,left:65,right:50}}>
 {["LA OPINIÓN","NO ES","INFORMACIÓN"].map((word,i)=>{
  const v=spring({frame:f-i*13,fps,config:{stiffness:120,damping:19}});
  return <div key={word} style={{transform:"translateY("+interpolate(v,[0,1],[150,0])+"px)",opacity:Math.max(0,v),fontSize:i===2?91:122,fontWeight:950,lineHeight:1.3,letterSpacing:-4,color:i===1?color.red:color.white}}>{word}</div>;
 })}
 <div style={{height:9,marginTop:42,width:interpolate(f,[50,95],[0,770],clamp),background:color.cyan}}/>
 <div style={{marginTop:50,fontSize:37,color:color.muted}}>El dato necesita una fuente.</div>
 </div></Frame>;
}
const cards=[["ARCHIVO","Material documentado",65,475,-5],["FUENTE","Procedencia y fecha",330,675,5],["CONTEXTO","Contraste periodístico",100,1050,-3]];
function Collage(){
 const f=useCurrentFrame(),{fps}=useVideoConfig();
 return <Frame step="02 / COLLAGE">
 <div style={{position:"absolute",top:245,left:66,fontSize:80,fontWeight:950}}>DOCUMENTAR</div>
 <div style={{position:"absolute",top:345,left:66,fontSize:44,color:color.cyan,fontWeight:750}}>ANTES DE PUBLICAR</div>
 {cards.map(([name,desc,x,y,rot],i)=>{
 const s=spring({frame:f-i*11,fps,config:{stiffness:85,damping:18}});
 return <div key={name} style={{position:"absolute",left:x,top:y,width:680,height:330,padding:43,boxSizing:"border-box",background:i%2?"#0b3454":"#164365",border:"3px solid #699abb",borderRadius:22,boxShadow:"0 25px 40px #0008",opacity:Math.max(0,s),transform:"translateY("+interpolate(s,[0,1],[210,0])+"px) rotate("+rot+"deg)"}}>
 <div style={{fontSize:30,color:color.cyan,letterSpacing:5,fontWeight:800}}>DISI / 0{i+1}</div>
 <div style={{fontSize:76,fontWeight:950,marginTop:35}}>{name}</div>
 <div style={{fontSize:31,marginTop:17,color:color.muted}}>{desc}</div>
 <div style={{background:color.red,height:7,width:130,marginTop:23}}/>
 </div>;
 })}
 <div style={{position:"absolute",bottom:165,left:65,fontSize:27,color:color.muted}}>Ejemplo gráfico · Sin imágenes ni hechos inventados</div>
 </Frame>;
}
function Data(){
 const f=useCurrentFrame();
 return <Frame step="03 / GRÁFICOS">
 <div style={{position:"absolute",top:270,left:67,fontSize:84,fontWeight:950,lineHeight:1.13}}>DATOS ANTES<br/>QUE OPINIONES</div>
 <div style={{position:"absolute",top:680,left:67,right:67}}>
 {["LOCALIZAR","CONTRASTAR","PUBLICAR"].map((s,i)=>{
 const v=interpolate(f,[i*20,i*20+46],[0,100],clamp);
 return <div key={s} style={{marginBottom:73}}>
 <div style={{display:"flex",gap:30,alignItems:"baseline"}}><span style={{fontSize:45,fontWeight:900,color:color.red}}>0{i+1}</span><span style={{fontSize:56,fontWeight:900}}>{s}</span></div>
 <div style={{height:16,marginTop:22,background:"#27536e",borderRadius:9,overflow:"hidden"}}><div style={{height:"100%",width:v+"%",background:i===2?color.red:color.cyan}}/></div>
 </div>;
 })}
 </div>
 <div style={{position:"absolute",bottom:195,left:65,fontSize:31,color:color.muted}}>Flujo editorial ilustrativo · No contiene métricas reales</div>
 </Frame>;
}
export const DisiMotionLab=()=> <AbsoluteFill>
 <Sequence from={0} durationInFrames={120}><Kinetic/></Sequence>
 <Sequence from={120} durationInFrames={120}><Collage/></Sequence>
 <Sequence from={240} durationInFrames={120}><Data/></Sequence>
</AbsoluteFill>;
