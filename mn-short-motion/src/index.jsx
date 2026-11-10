import React from "react";
import {Composition, registerRoot} from "remotion";
import {NewsVideo} from "./NewsVideo";
import {DisiV9} from "./DisiV9";

const Root = () => (<>
  <Composition
    id="DISIV9Approved"
    component={DisiV9}
    fps={25}
    width={720}
    height={1280}
    durationInFrames={1367}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max(1, Number(props.totalFrames) || 1367)
    })}
    defaultProps={{
      totalFrames:1367,bodyFrames:1175,scenes:[],captions:[],
      audio:"PELAYO_WAV_ORIGINAL.wav"
    }}
  />
  <Composition
    id="MNShortEditorial"
    component={NewsVideo}
    fps={30}
    width={1080}
    height={1920}
    durationInFrames={1200}
    calculateMetadata={({props}) => ({durationInFrames: Math.max(30, Number(props.totalFrames) || 1200)})}
    defaultProps={{
      language: "es", storyTitle: "MNShort", publisher: "Media News",
      totalFrames: 1200, scenes: [],
    }}
  />
</>);
registerRoot(Root);
