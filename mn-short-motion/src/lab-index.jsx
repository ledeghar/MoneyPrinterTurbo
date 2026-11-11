import React from "react";
import {Composition,registerRoot} from "remotion";
import {DisiMotionLab} from "./DisiMotionLab";
// Separate entry point: approved DISIV9Approved and MNShortEditorial are untouched.
registerRoot(()=><Composition id="DISIFreeMotionLab" component={DisiMotionLab} fps={30} width={1080} height={1920} durationInFrames={360}/>);
