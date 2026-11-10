#!/usr/bin/env python3
"""DISI/MNShort V9: immutable reference QA, YouTube distribution export, and backups.

The original approved master NEVER gets rewritten. All operations use new paths.
Python stdlib + FFmpeg/FFprobe only. No upload is performed by this script.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

LANGS = [("es","spa"),("en","eng"),("fr","fra"),("de","deu"),("it","ita"),
         ("pt","por"),("ru","rus"),("zh","zho"),("ja","jpn"),("ar","ara")]
MAX_SECONDS = 59.0
V9_APPROVED_SHA256 = "3b2817d6b5461f2ddcd76062c4315074f6faed64fceac2b434f83fdba45b59de"
V9_APPROVED_OUTRO_SHA256 = "67536b800ba211d52e364489c6c1418459e9e3c5c256a2df92669ad054c6e926"

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def cmd(args):
    p=subprocess.run(args,text=True,capture_output=True)
    if p.returncode:
        raise RuntimeError((" ".join(map(str,args))+"\n"+p.stderr)[-1800:])
    return p.stdout

def probe(path):
    return json.loads(cmd(["ffprobe","-v","error","-show_entries",
      "stream=index,codec_type,codec_name,width,height:stream_tags=language:format=duration",
      "-of","json",str(path)]))

def validate(path, *, approved=False, check_signal=True):
    path=Path(path)
    if not path.is_file() or path.stat().st_size<100000:
        raise ValueError("Missing/empty MP4 master")
    info=probe(path)
    streams=info.get("streams",[])
    select=lambda typ:[x for x in streams if x.get("codec_type")==typ]
    video,audio,subs=[select(t) for t in ("video","audio","subtitle")]
    if (len(video),len(audio),len(subs))!=(1,10,10):
        raise ValueError(f"Require 1 video, 10 audios, 10 subtitles; got {len(video)}/{len(audio)}/{len(subs)}")
    if video[0].get("codec_name")!="h264":raise ValueError("H264 required")
    w,h=video[0].get("width",0),video[0].get("height",0)
    if not w or not h or abs(w*16-h*9)>30:
        raise ValueError(f"Video is not 9:16 vertical: {w}x{h}")
    if any(x.get("codec_name")!="aac" for x in audio):
        raise ValueError("All ten tracks must be AAC")
    if any(x.get("codec_name") not in ("mov_text","subrip","ass") for x in subs):
        raise ValueError("Selectable subtitle codec expected")
    for category, tracks in (("audio",audio),("subtitle",subs)):
        got=[s.get("tags",{}).get("language","und") for s in tracks]
        expected=[code for _,code in LANGS]
        if got!=expected:raise ValueError(f"{category}: unexpected language order {got}; expected {expected}")
    duration=float(info["format"]["duration"])
    if not 5<duration<MAX_SECONDS:
        raise ValueError(f"Video duration {duration:.3f}s must be <59s")
    digest=sha256(path)
    if approved and digest!=V9_APPROVED_SHA256:
        raise ValueError("Approved V9 was modified: SHA256 mismatch")
    if check_signal:
        for i,(lang,_) in enumerate(LANGS):
            stderr=subprocess.run(["ffmpeg","-hide_banner","-nostdin","-i",str(path),
              "-map",f"0:a:{i}","-ss","2","-t","10","-af","volumedetect","-f","null","-"],
              stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True).stderr
            m=re.findall(r"mean_volume:\s*(-?[\d.]+)\s*dB",stderr)
            if not m or float(m[-1]) < -40:
                raise ValueError(f"Audio track {lang} silent/too quiet in early narration")
    return {"path":str(path),"sha256":digest,"duration_seconds":duration,
            "dimensions":[w,h],"video":1,"audio":len(audio),"subtitle":len(subs),
            "languages":[lang for lang,_ in LANGS]}

def export_youtube(args):
    d=Path(args.output)
    d.mkdir(parents=True,exist_ok=True)
    data=validate(args.master,approved=args.approved,check_signal=not args.skip_signal_check)
    video=d/"MNShort_YOUTUBE_ES.mp4"
    cmd(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
      "-i",args.master,"-map","0:v:0","-map","0:a:0",
      "-c","copy","-movflags","+faststart",str(video)])
    trackdir=d/"IDIOMAS_YOUTUBE_STUDIO"
    trackdir.mkdir(exist_ok=True)
    for i,(lang,_) in enumerate(LANGS):
        # The API can upload caption tracks, but cannot install other dubbed audio streams.
        cmd(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
            "-i",args.master,"-map",f"0:s:{i}","-c:s","srt",str(trackdir/f"{lang}.srt")])
        if lang!="es":
            cmd(["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
                "-i",args.master,"-map",f"0:a:{i}","-c:a","copy",
                str(trackdir/f"{lang}.m4a")])
    out={"format":"DISI-V9","approved_v9_reference_sha":V9_APPROVED_SHA256,
         "source_sha256":data["sha256"],"source_duration":data["duration_seconds"],
         "publish_ready":bool(args.reviewed),"youtube_initial_visibility":"unlisted",
         "youtube_video":video.name,"languages":[l for l,_ in LANGS],
         "title":args.title,"description":args.description,
         "disclosure":"Synthetic voices and illustrative archive material where applicable",
         "requires":"Human editorial, audiovisual, copyright, and channel review before publishing"}
    (d/"YOUTUBE_ENVIO.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    return out

def backup(args):
    src=Path(args.master)
    info=validate(src,approved=args.approved,check_signal=not args.skip_signal_check)
    target=Path(args.output)
    target.mkdir(parents=True,exist_ok=True)
    dest=target/src.name
    if dest.exists() and sha256(dest)!=sha256(src):
        raise FileExistsError("A different master already exists at destination")
    if not dest.exists():shutil.copy2(src,dest)
    items=[dest]
    for extra in args.asset:
        extra=Path(extra)
        if not extra.is_file():raise FileNotFoundError(extra)
        dst=target/extra.name
        if dst.exists() and sha256(dst)!=sha256(extra):
            raise FileExistsError(f"Conflicting asset: {dst}")
        if not dst.exists():shutil.copy2(extra,dst)
        items.append(dst)
    manifest={"reference":"DISI V9 approved 2026-11-10",
              "locked":True,"source":info,
              "files":{x.name:sha256(x) for x in items}}
    (target/"SHA256_MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return manifest

def main():
    p=argparse.ArgumentParser(description="MNShort DISI V9 approved template")
    group=p.add_subparsers(dest="action",required=True)
    for action in ("verify","youtube","backup"):
        sub=group.add_parser(action)
        sub.add_argument("--master",required=True)
        sub.add_argument("--approved",action="store_true",
                         help="Require exact untouched approved V9 SHA-256")
        sub.add_argument("--skip-signal-check",action="store_true",
                         help="Only use when verifying test/synthetic fixtures")
        if action!="verify":
            sub.add_argument("--output",required=True)
        if action=="youtube":
            sub.add_argument("--title",required=True)
            sub.add_argument("--description",default="")
            sub.add_argument("--reviewed",action="store_true")
        if action=="backup":
            sub.add_argument("--asset",action="append",default=[])
    args=p.parse_args()
    if args.action=="verify":
        result=validate(args.master,approved=args.approved,check_signal=not args.skip_signal_check)
    elif args.action=="youtube":
        result=export_youtube(args)
    else:result=backup(args)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
