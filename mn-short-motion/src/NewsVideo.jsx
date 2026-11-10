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
const LANG_LABELS = {
  es:{person:"PROTAGONISTA",noPhoto:"Sin retrato autorizado disponible",metric:"CIFRA DE LA NOTICIA",place:"DIAGRAMA DE CONTEXTO, NO MAPA REAL",source:"FUENTE ORIGINAL",sourceText:"Enlace original en el informe editorial",outro:"Contexto. Fuentes. Hechos.",context:"CLAVES DE LA NOTICIA"},
  en:{person:"NAMED PERSON",noPhoto:"No cleared portrait available",metric:"NUMBER IN THE STORY",place:"CONTEXT DIAGRAM, NOT A REAL MAP",source:"ORIGINAL SOURCE",sourceText:"Article link in editorial report",outro:"Context. Sources. Facts.",context:"IN CONTEXT"},
  fr:{person:"PERSONNE CITÉE",noPhoto:"Portrait non autorisé indisponible",metric:"CHIFFRE DU REPORTAGE",place:"SCHÉMA, PAS UNE CARTE RÉELLE",source:"SOURCE ORIGINALE",sourceText:"Lien dans le rapport éditorial",outro:"Contexte. Sources. Faits.",context:"LE CONTEXTE"},
  de:{person:"GENANNTE PERSON",noPhoto:"Kein freigegebenes Porträt",metric:"ZAHL DER MELDUNG",place:"SCHEMA, KEINE ECHTE KARTE",source:"ORIGINALQUELLE",sourceText:"Quellenlink im Redaktionsbericht",outro:"Kontext. Quellen. Fakten.",context:"HINTERGRUND"},
  it:{person:"PROTAGONISTA",noPhoto:"Ritratto autorizzato non disponibile",metric:"DATO DELLA NOTIZIA",place:"SCHEMA, NON UNA MAPPA REALE",source:"FONTE ORIGINALE",sourceText:"Link nel rapporto editoriale",outro:"Contesto. Fonti. Fatti.",context:"IL CONTESTO"},
  pt:{person:"PROTAGONISTA",noPhoto:"Retrato autorizado indisponível",metric:"NÚMERO DA NOTÍCIA",place:"ESQUEMA, NÃO É UM MAPA REAL",source:"FONTE ORIGINAL",sourceText:"Ligação no relatório editorial",outro:"Contexto. Fontes. Factos.",context:"EM CONTEXTO"},
  ru:{person:"УПОМИНАЕМЫЙ ЧЕЛОВЕК",noPhoto:"Разрешённого портрета нет",metric:"ЦИФРА В МАТЕРИАЛЕ",place:"СХЕМА, НЕ ГЕОГРАФИЧЕСКАЯ КАРТА",source:"ПЕРВОИСТОЧНИК",sourceText:"Ссылка в редакционном отчёте",outro:"Контекст. Источники. Факты.",context:"КОНТЕКСТ"},
  zh:{person:"新闻人物",noPhoto:"没有获准使用的人物照片",metric:"报道数据",place:"背景示意图，非真实地图",source:"原始来源",sourceText:"原文链接见编辑报告",outro:"背景、来源、事实。",context:"新闻背景"},
  ja:{person:"登場人物",noPhoto:"使用許可を確認できる肖像なし",metric:"報道の数字",place:"背景図・実際の地図ではありません",source:"元の記事",sourceText:"元記事のリンクは編集資料に記載",outro:"背景。情報源。事実。",context:"ニュースの背景"},
  ar:{person:"الشخص المذكور",noPhoto:"لا تتوفر صورة مصرح باستخدامها",metric:"رقم في الخبر",place:"رسم توضيحي وليس خريطة حقيقية",source:"المصدر الأصلي",sourceText:"رابط المقال في التقرير التحريري",outro:"السياق. المصادر. الحقائق.",context:"في السياق"}
};
const label = (lang, key) => (LANG_LABELS[lang] || LANG_LABELS.es)[key];
const font = (lang) => lang==="ar" ? "'Noto Sans Arabic', 'Noto Sans', Arial, sans-serif" : lang==="ja" ? "'Noto Sans CJK JP','Noto Sans',sans-serif" : lang==="zh" ? "'Noto Sans CJK SC','Noto Sans',sans-serif" : "'Noto Sans', Arial, Helvetica, sans-serif";


function Nameplate() {
  return <div style={{display:"flex",alignItems:"center",gap:18}}>
    <span style={{fontSize:42,fontWeight:900,background:RED,padding:"9px 16px",borderRadius:8,letterSpacing:-3}}>MN</span>
    <span style={{fontSize:37,fontWeight:900,letterSpacing:8}}>SHORT</span>
  </div>;
}

function VoiceCaption({text,frame,duration,lang}) {
  const cjk = lang==="zh" || lang==="ja";
  const words = cjk ? Array.from(String(text||"")).filter(c => c.trim()) : String(text||"").split(/\s+/).filter(Boolean);
  const current=Math.floor(interpolate(frame,[0,Math.max(1,duration-1)],[0,words.length],{extrapolateLeft:"clamp",extrapolateRight:"clamp"}));
  const size = cjk ? (words.length>65?41:words.length>38?48:57) : (words.length>23?46:words.length>14?53:60);
  return <div style={{fontSize:size,lineHeight:1.24,fontWeight:820,overflowWrap:"anywhere"}}>
    {words.map((word,i)=><React.Fragment key={i}><span style={{color:i===current?RED:i<current?WHITE:MUTED}}>{word}</span>{cjk?"":" "}</React.Fragment>)}
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
        <div style={{fontSize:27,marginTop:30,color:MUTED,textAlign:"center"}}>{label(item.language,"noPhoto")}</div>
      </div>
    }
    <div style={{position:"absolute",left:0,right:0,bottom:0,padding:"70px 45px 35px",background:"linear-gradient(transparent,rgba(0,0,0,.93))"}}>
      <div style={{fontSize:23,letterSpacing:4,color:"#ffb5c3",fontWeight:900}}>{label(item.language,"person")}</div>
      <div style={{fontSize:subject.length>28?52:66,fontWeight:900,lineHeight:1.12,marginTop:10}}>{subject}</div>
      {item.image && <div style={{fontSize:17,marginTop:18,color:MUTED}}>{String(item.credit||"").slice(0,105)}</div>}
    </div>
  </div>;
  if(item.kind==="metric") return <div style={{...box,...appear,padding:56,display:"flex",flexDirection:"column",justifyContent:"center"}}>
    <div style={{fontSize:24,color:MUTED,fontWeight:900,letterSpacing:5}}>{label(item.language,"metric")}</div>
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
      <div style={{fontSize:20,color:MUTED,letterSpacing:2}}>{label(item.language,"place")}</div>
      <div style={{fontSize:66,fontWeight:900,marginTop:12}}>{subject}</div>
    </div>
  </div>;
  if(item.kind==="source") return <div style={{...box,...appear,padding:58,display:"flex",flexDirection:"column",justifyContent:"space-around"}}>
    <div style={{fontSize:25,color:RED,letterSpacing:5,fontWeight:900}}>{label(item.language,"source")}</div>
    <div style={{fontSize:subject.length>26?57:81,fontWeight:900,letterSpacing:-2,lineHeight:1.12,overflowWrap:"anywhere"}}>{subject}</div>
    <div style={{height:5,width:"100%",background:BLUE}}/>
    <div style={{fontSize:29,color:MUTED}}>{label(item.language,"sourceText")}</div>
  </div>;
  if(item.kind==="outro") return <div style={{...box,...appear,display:"flex",flexDirection:"column",justifyContent:"center",alignItems:"center",gap:40}}>
    <div style={{fontSize:140,fontWeight:900,color:RED,letterSpacing:-7}}>MN</div>
    <div style={{fontSize:85,fontWeight:900,letterSpacing:8}}>SHORT</div>
    <div style={{height:6,width:460,background:BLUE}}/>
    <div style={{fontSize:31,color:MUTED}}>{label(item.language,"outro")}</div>
  </div>;
  return <div style={{...box,...appear,padding:56,display:"flex",flexDirection:"column",justifyContent:"center",gap:43}}>
    <div style={{height:9,width:175,borderRadius:5,background:RED}}/>
    <div style={{fontSize:subject.length>75?49:subject.length>45?59:71,fontWeight:900,lineHeight:1.12,letterSpacing:-1.7,overflowWrap:"anywhere"}}>{subject}</div>
    <div style={{height:4,width:"83%",background:BLUE}}/>
    <div style={{fontSize:31,color:MUTED}}>{label(item.language,"context")}</div>
  </div>;
}

function Segment({item,index,count,publisher,duration}){
  const frame=useCurrentFrame();
  const {fps}=useVideoConfig();
  const progress=(100*(index+Math.min(frame,duration)/duration)/count)+"%";
  return <AbsoluteFill style={{background:"radial-gradient(ellipse at 25% 25%,#194368,#081728 58%,#05101c)",fontFamily:font(item.language),direction:item.language==="ar"?"rtl":"ltr",color:WHITE,padding:"65px 68px 56px",boxSizing:"border-box",display:"flex",flexDirection:"column"}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
      <Nameplate/>
      <span style={{fontSize:24,letterSpacing:3,fontWeight:850,color:MUTED}}>{item.language.toUpperCase()}  {index+1}/{count}</span>
    </div>
    <div style={{marginTop:38,height:4,background:"#284763",width:"100%",borderRadius:5,overflow:"hidden"}}>
      <div style={{height:"100%",background:RED,width:progress}}/>
    </div>
    <div style={{flex:1,display:"flex",alignItems:"center",width:"100%"}}><Display item={item} frame={frame} fps={fps}/></div>
    <div style={{minHeight:350,display:"flex",alignItems:"center",padding:"20px 5px 30px"}}><VoiceCaption text={item.text} frame={frame} duration={duration} lang={item.language}/></div>
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
