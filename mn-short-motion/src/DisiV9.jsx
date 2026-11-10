import React from "react";
import {
  AbsoluteFill, Audio, Img, OffthreadVideo, Sequence,
  staticFile, useCurrentFrame, useVideoConfig
} from "remotion";

// DISI V9 — faithful, reusable editorial layout.
// Original logos, MEDIA wordmark and V6 outro are REQUIRED asset files.
// No typographic placeholders, no camera jitter or photo zoom.
const NAVY = "#051627";
const WHITE = "#f5f9ff";
const RED = "#e22344";
const CAPTION = "#030d1b";
const at = (name) => staticFile("disi-v9/" + name);

const Logo = ({filename, style}) => <Img src={at(filename)} style={style}/>;

function HighlightedCaption({cue}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const now = frame / fps;
  if (!cue) return null;
  const wordTimings = cue.words || [];
  return <div style={{
    position:"absolute", left:55, right:55, top:1007, height:155,
    color:WHITE, fontFamily:"DejaVu Sans, Arial, sans-serif",
    fontSize:36, lineHeight:1.28, fontWeight:780,
    display:"flex", alignItems:"center", justifyContent:"center",
    textAlign:"center", flexWrap:"wrap", overflowWrap:"anywhere"
  }}>
    {wordTimings.length
      ? wordTimings.map((w, i) => <span key={i} style={{
          whiteSpace:"pre-wrap",
          color:now >= w.start && now < w.end ? RED : WHITE
        }}>{w.text}{i === wordTimings.length-1 ? "" : " "}</span>)
      : cue.text}
  </div>;
}

function Body({scenes=[], captions=[], audio}) {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cue = captions.find((c) => frame >= c.startFrame && frame < c.endFrame);
  const active = scenes.find((s) => frame >= s.startFrame && frame < s.startFrame+s.durationFrames);
  if (!active) throw new Error("DISI V9 requires a footage scene covering every body frame.");
  if (!audio) throw new Error("The approved narration must be provided; silence is not acceptable.");
  return <AbsoluteFill style={{backgroundColor:NAVY,color:WHITE}}>
    {/* Original circular logo + MEDIA artwork, NOT a replacement text logo */}
    <Logo filename="LOGO_MEDIA_NEWS_CANVA.png" style={{
      position:"absolute",left:24,top:24,width:80,height:80,objectFit:"contain"
    }}/>
    <Logo filename="MEDIA_CANVA_WORDMARK.png" style={{
      position:"absolute",left:127,top:30,width:358,height:75,objectFit:"contain"
    }}/>
    <Logo filename="LOGO_DISI_CANVA.png" style={{
      position:"absolute",right:24,top:24,width:80,height:80,objectFit:"contain"
    }}/>
    <div style={{
      position:"absolute",left:28,top:140,width:660,
      fontFamily:"Liberation Serif, Georgia, serif",fontSize:43,
      lineHeight:1.05,whiteSpace:"nowrap",overflow:"hidden",
      textOverflow:"ellipsis"
    }}>{active.headline || ""}</div>
    <div style={{position:"absolute",left:30,top:216,width:155,height:5,background:RED}}/>
    <div style={{
      position:"absolute",left:30,top:229,
      fontSize:17,fontFamily:"DejaVu Sans, sans-serif",letterSpacing:1.5
    }}>DISI / MEDIOS · INVESTIGACIÓN · TECNOLOGÍA</div>
    <div style={{position:"absolute",left:0,top:250,width:720,height:720,overflow:"hidden"}}>
      {scenes.map((scene, i) => <Sequence key={i} from={scene.startFrame} durationInFrames={scene.durationFrames}>
        <OffthreadVideo src={at(scene.file)}
          startFrom={scene.sourceStartFrame || 0}
          muted style={{width:"100%",height:"100%",objectFit:"cover"}}/>
      </Sequence>)}
    </div>
    <div style={{position:"absolute",left:0,top:971,width:720,height:309,backgroundColor:NAVY}}/>
    <div style={{position:"absolute",left:30,top:1018,width:5,height:136,background:RED}}/>
    <HighlightedCaption cue={cue}/>
    <div style={{position:"absolute",left:30,top:1190,width:660,height:1,background:"#365d7d"}}/>
    <div style={{
      position:"absolute",left:35,bottom:39,fontFamily:"DejaVu Sans",
      fontWeight:750,fontSize:19
    }}>Media News by DISI</div>
    <div style={{position:"absolute",right:30,bottom:39,fontSize:17}}>MNShort</div>
    <Audio src={at(audio)} volume={1}/>
  </AbsoluteFill>;
}

export const DisiV9 = (props) => {
  const bodyFrames = Math.round(Number(props.bodyFrames));
  const totalFrames = Math.round(Number(props.totalFrames));
  if (!bodyFrames || !totalFrames || totalFrames <= bodyFrames)
    throw new Error("Explicit bodyFrames + totalFrames with complete V6 outro are required.");
  if (totalFrames / 25 >= 59)
    throw new Error("DISI policy: total output including V6 must remain below 59 seconds.");
  return <AbsoluteFill>
    <Sequence from={0} durationInFrames={bodyFrames}>
      <Body scenes={props.scenes} captions={props.captions} audio={props.audio}/>
    </Sequence>
    <Sequence from={bodyFrames} durationInFrames={totalFrames-bodyFrames}>
      {/* This is the original Canva M-to-DISI V6 WITH its original soundtrack */}
      <OffthreadVideo src={at("OUTRO_V6_ORIGINAL.mp4")}
        style={{width:"100%",height:"100%",objectFit:"cover"}}/>
    </Sequence>
  </AbsoluteFill>;
};
