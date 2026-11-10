#!/usr/bin/env python3
"""Upload ten timed SRT caption files to ONE YouTube Short using captions.insert.

Explicit release-only stage: requires successful scheduled upload ID,
OAuth youtube.force-ssl scope, channel ownership, and 10 validated SRTs.
Can be rerun safely because existing tracks are checked first.
Does not upload dubbed audio, which lacks a public YouTube Data API endpoint.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
from uuid import uuid4
import requests
from mn_short_youtube_direct import get_access_token
from mn_short_youtube_channel_guard import verify_expected_channel

LANGS={"es":"Español","en":"English","fr":"Français","de":"Deutsch",
       "it":"Italiano","pt":"Português","ru":"Русский",
       "zh":"中文","ja":"日本語","ar":"العربية"}
BASE="https://www.googleapis.com/youtube/v3/captions"

def read_publish_id(path):
    release=json.loads(Path(path).read_text(encoding="utf-8"))
    vid=release.get("video_id","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}",vid):
        raise ValueError("Invalid/missing YouTube release video ID")
    return vid

def srt_files(folder):
    d=Path(folder)
    paths={lang:d/("SUBTITULOS_"+lang+".srt") for lang in LANGS}
    for lang,path in paths.items():
        if not path.is_file():
            raise FileNotFoundError("Missing captions for "+lang)
        raw=path.read_text(encoding="utf-8-sig")
        if len(raw)<20 or "-->" not in raw or not re.search(r"\d\d:\d\d:\d\d,\d{3}",raw):
            raise ValueError("Missing timed caption cues for "+lang)
    return paths

def upload_one(session,token,vid,lang,label,path):
    meta=json.dumps({"snippet":{"videoId":vid,"language":lang,
                                     "name":label,"isDraft":False}},ensure_ascii=False).encode()
    boundary="disi"+uuid4().hex
    data=b"".join((
        ("--"+boundary+"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n").encode(),
        meta,b"\r\n",
        ("--"+boundary+"\r\nContent-Type: application/octet-stream\r\n\r\n").encode(),
        path.read_bytes(),b"\r\n",
        ("--"+boundary+"--\r\n").encode(),
    ))
    response=session.post("https://www.googleapis.com/upload/youtube/v3/captions",
        params={"part":"snippet","uploadType":"multipart"},
        headers={"Authorization":"Bearer "+token,
                 "Content-Type":"multipart/related; boundary="+boundary},
        data=data,timeout=90)
    if response.status_code not in (200,201):
        raise RuntimeError(f"Upload subtitles {lang}: YouTube HTTP {response.status_code}; "
                           "check youtube.force-ssl scope and quota, do not silently claim ten languages")
    item=response.json()
    if not item.get("id"):
        raise RuntimeError("YouTube returned no confirmed caption track for "+lang)
    return item["id"]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--video-id-file",required=True)
    p.add_argument("--srt-folder",required=True)
    args=p.parse_args()
    vid=read_publish_id(args.video_id_file)
    files=srt_files(args.srt_folder)
    with requests.Session() as s:
        verify_expected_channel(s)
        token=get_access_token(s)
        existing=s.get(BASE,params={"part":"snippet","videoId":vid,"maxResults":100},
            headers={"Authorization":"Bearer "+token},timeout=45)
        if existing.status_code!=200:
            raise RuntimeError("Cannot list existing subtitles: HTTP "
                               +str(existing.status_code)+"; need OAuth youtube.force-ssl")
        done={(x.get("snippet",{}).get("language"),x.get("snippet",{}).get("name"))
              for x in existing.json().get("items",[])}
        result={}
        for lang,label in LANGS.items():
            if (lang,label) in done:
                result[lang]="already_exists"
                continue
            result[lang]=upload_one(s,token,vid,lang,label,files[lang])
        out=Path(args.video_id_file).parent/"YOUTUBE_10_SUBTITULOS.json"
        out.write_text(json.dumps({"video_id":vid,"tracks":result},
                                  ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        if len(result)!=10:raise RuntimeError("Incomplete multilingual subtitle upload")
        print("Ten timed subtitle language tracks accounted for:",", ".join(result))

if __name__=="__main__":
    main()
