import React from "react";
import {
  AbsoluteFill, Audio, Img, Sequence, interpolate, spring,
  staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";

const INK = "#07192c";
const WHITE = "#f5faff";
const RED = "#f0405c";
const MUTED = "#b6c9db";
const BLUE = "#468fd4";

function Nameplate() {
  return <div style={{display:"flex",alignItems:"center",gap:18}}>
    <span style={{fontSize:42,fontWeight:900,background:RED,padding:"9px 16px",borderRadius:8,letterSpacing:-3}}>MN</span>
    <span style={{fontSize:37,fontWeight:900,letterSpacing:8}}>SHORT</span>
  </div>;
}

function VoiceCaption({text,frame,duration}) {
  const words=String(text||"").split(/\s+/).filter(Boolean);
  const current=Math.floor(interpolate(frame,[0,Math.max(1,duration-1)],[0,words.length],{extrapolateLeft:"clamp",extrapolateRight:"clamp"}));
  const size=words.length>23?46:words.length>14?53:60;
  return <div style={{fontSize:size,lineHeight:1.24,fontWeight:820,overflowWrap:"anywhere"}}>
    {words.map((word,i)=><React.Fragment key={i}><span style={{color:i===current?RED:i<current?WHITE:MUTED}}>{word}</span>{" "}</React.Fragment>)}
  </div>;
}

function Display({item,frame,fps}){
  const enter=spring({frame,fps,config:{damping:17,stiffness:88}});
  const appear={opacity:enter,transform:"translateY("+Math.round((1-enter)*75)+"px)"};
  const box={width:"100%",height:690,borderRadius:28,background:"linear-gradient(145deg,#193753,#0a1f37)",border:"2px solid #36516c",boxSizing:"border-box",overflow:"hidden",position:"relative"};
  const subject=String(item.subject||"");
  if(item.kind==="person") return <div style={{...box,...appear}}>
    {item.image ? <Img src={staticFile(item.image)} style={{width:"100%",height:"100%",objectFit:"cover"}}/> :
      <div style={{height:"100%",display:"flex",justifyContent:"center",alignItems:"center",flexDirection:"column"}}>
        <div style={{height:220,width:220,borderRadius:110,border:"8px solid "+RED,display:"grid",placeItems:"center",fontWeight:900,fontSize:88,color:MUTED}}>
          {subject.split(/\s+/).slice(0,2).map(x=>x.charAt(0)).join("").toUpperCase()}
        </div>
        <div style={{fontSize:27,marginTop:30,color:MUTED,textAlign:"center"}}>{item.language==="en"?"No cleared portrait available":"Sin retrato autorizado disponible"}</div>
      </div>
    }
    <div style={{position:"absolute",left:0,right:0,bottom:0,padding:"70px 45px 35px",background:"linear-gradient(transparent,rgba(0,0,0,.93))"}}>
      <div style={{fontSize:23,letterSpacing:4,color:"#ffb5c3",fontWeight:900}}>{item.language==="en"?"NAMED PERSON":"PROTAGONISTA"}</div>
      <div style={{fontSize:subject.length>28?52:66,fontWeight:900,lineHeight:1.12,marginTop:10}}>{subject}</div>
      {item.image && <div style={{fontSize:17,marginTop:18,color:MUTED}}>{String(item.credit||"").slice(0,105)}</div>}
    </div>
  </div>;
  if(item.kind==="metric") return <div style={{...box,...appear,padding:56,display:"flex",flexDirection:"column",justifyContent:"center"}}>
    <div style={{fontSize:24,color:MUTED,fontWeight:900,letterSpacing:5}}>{item.language==="en"?"NUMBER IN THE STORY":"CIFRA DEL RELATO"}</div>
    <div style={{fontSize:String(item.metric||"").length>5?126:190,fontWeight:900,color:RED,letterSpacing:-9,lineHeight:1.5}}>{item.metric}</div>
    <div style={{height:7,width:(enter*83)+"%",borderRadius:5,background:BLUE}}/>
    <div style={{fontSize:41,lineHeight:1.2,fontWeight:750,marginTop:35}}>{subject}</div>
  </div>;
  if(item.kind==="place") return <div style={{...box,...appear}}>
    <svg width="100%" height="100%" viewBox="0 0 860 690">
      <defs><pattern id="dots" width="45" height="45" patternUnits="userSpaceOnUse"><circle cx="22" cy="22" r="2" fill="#4281bd" opacity=".45"/></pattern></defs>
      <rect width="860" height="690" fill="url(#dots)"/>
      {[220,150,75].map((r,i)=><circle key={r} cx="430" cy="290" r={r+Math.sin(frame*.08+i)*9} fill="none" stroke={BLUE} strokeWidth="3" opacity={.25+i*.17}/>)}
      <circle cx="430" cy="290" r="24" fill={RED}/>
      <path d="M430 312 L430 408" stroke={RED} strokeWidth="5"/>
    </svg>
    <div style={{position:"absolute",left:45,bottom:35,right:40}}>
      <div style={{fontSize:20,color:MUTED,letterSpacing:2}}>{item.language==="en"?"CONTEXT DIAGRAM — NOT A GEOGRAPHIC MAP":"DIAGRAMA DE CONTEXTO — NO ES UN MAPA REAL"}</div>
      <div style={{fontSize:66,fontWeight:900,marginTop:12}}>{subject}</div>
    </div>
  </div>;
  if(item.kind==="source") return <div style={{...box,...appear,padding:58,display:"flex",flexDirection:"column",justifyContent:"space-around"}}>
    <div style={{fontSize:25,color:RED,letterSpacing:5,fontWeight:900}}>{item.language==="en"?"ORIGINAL SOURCE":"FUENTE ORIGINAL"}</div>
    <div style={{fontSize:subject.length>26?57:81,fontWeight:900,letterSpacing:-2,lineHeight:1.12,overflowWrap:"anywhere"}}>{subject}</div>
    <div style={{height:5,width:"100%",background:BLUE}}/>
    <div style={{fontSize:29,color:MUTED}}>{item.language==="en"?"Article link in editorial report":"Enlace original en el informe editorial"}</div>
  </div>;
  if(item.kind==="outro") return <div style={{...box,...appear,display:"flex",flexDirection:"column",justifyContent:"center",alignItems:"center",gap:40}}>
    <div style={{fontSize:140,fontWeight:900,color:RED,letterSpacing:-7}}>MN</div>
    <div style={{fontSize:85,fontWeight:900,letterSpacing:8}}>SHORT</div>
    <div style={{height:6,width:460,background:BLUE}}/>
    <div style={{fontSize:31,color:MUTED}}>{item.language==="en"?"Context. Sources. Facts.":"Contexto. Fuentes. Hechos."}</div>
  </div>;
  return <div style={{...box,...appear,padding:56,display:"flex",flexDirection:"column",justifyContent:"center",gap:43}}>
    <div style={{height:9,width:175,borderRadius:5,background:RED}}/>
    <div style={{fontSize:subject.length>75?49:subject.length>45?59:71,fontWeight:900,lineHeight:1.12,letterSpacing:-1.7,overflowWrap:"anywhere"}}>{subject}</div>
    <div style={{height:4,width:"83%",background:BLUE}}/>
    <div style={{fontSize:31,color:MUTED}}>{item.language==="en"?"IN CONTEXT":"CLAVES DE LA NOTICIA"}</div>
  </div>;
}

function Segment({item,index,count,publisher,duration}){
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const progress=(100*(index+Math.min(frame,duration)/duration)/count)+"%";
  return <AbsoluteFill style={{background:"radial-gradient(ellipse at 25% 25%,#194368,#081728 58%,#05101c)",fontFamily:"Arial,Helvetica,sans-serif",color:WHITE,padding:"65px 68px 56px",boxSizing:"border-box",display:"flex",flexDirection:"column"}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
      <Nameplate/>
      <span style={{fontSize:24,letterSpacing:3,fontWeight:850,color:MUTED}}>{item.language.toUpperCase()}  {index+1}/{count}</span>
    </div>
    <div style={{marginTop:38,height:4,background:"#284763",width:"100%",borderRadius:5,overflow:"hidden"}}>
      <div style={{height:"100%",background:RED,width:progress}}/>
    </div>
    <div style={{flex:1,display:"flex",alignItems:"center",width:"100%"}}><Display item={item} frame={frame} fps={fps}/></div>
    <div style={{minHeight:350,display:"flex",alignItems:"center",padding:"20px 5px 30px"}}><VoiceCaption text={item.text} frame={frame} duration={duration}/></div>
    <div style={{height:2,background:"#38556b",marginBottom:22}}/>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:12}}>
      <div style={{fontSize:21,fontWeight:800,color:MUTED}}>MEDIA NEWS · {String(publisher||"").slice(0,45)}</div>
      <div style={{fontSize:22,fontWeight:900,color:RED}}>MN SHORT</div>
    </div>
  </AbsoluteFill>;
}

export const NewsVideo=({language="es",publisher="Media News",scenes=[]})=>(
  <AbsoluteFill style={{background:INK}}>
    {(Array.isArray(scenes)?scenes:[]).map((scene,i)=>(
      <Sequence key={i} from={scene.startFrame} durationInFrames={scene.durationFrames}>
        <Segment item={{...scene,language}} index={i} count={scenes.length} publisher={publisher} duration={scene.durationFrames}/>
        {scene.audio && <Audio src={staticFile(scene.audio)} volume={1}/>}
      </Sequence>
    ))}
  </AbsoluteFill>
);
