import React from "react";
import {Composition, registerRoot} from "remotion";
import {NewsVideo} from "./NewsVideo";

const Root = () => (
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
);
registerRoot(Root);
