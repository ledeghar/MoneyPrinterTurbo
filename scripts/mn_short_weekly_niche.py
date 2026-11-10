#!/usr/bin/env python3
"""Weekly, evidence-led MNShort niche research from recent public YouTube videos.

Reports are NOT a claim that a news event is verified. Any public release
requires separate journalism, licensing, source and render checks.

Credential: YOUTUBE_DATA_API_KEY (preferred) or valid GitHub OAuth secrets.
No scraping, fake view figures, preselected permanent winner, or publication.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
from statistics import median
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

NICHES = {
    "technology": ["AI artificial intelligence news shorts", "new technology explained shorts"],
    "gaming": ["video game industry news shorts", "gaming news trending shorts"],
    "world": ["international news explained shorts", "world news update shorts"],
    "cinema": ["movie industry film news shorts", "film cinema trending news shorts"],
    "society": ["society education news shorts", "social issues news explained shorts"],
    "news": ["breaking news explained shorts", "news investigations shorts"],
}
MIN_VIEWS_PER_HIT = 1_000_000
MIN_HITS = 2
LOOKBACK_DAYS = 7
MAX_SHORT_SECONDS = 180


def iso_seconds(raw: str) -> int:
    """Parse the ISO-8601 durations returned by videos.list."""
    m = re.fullmatch(r"P(?:\d+D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", raw or "")
    if not m:
        return 0
    return int(m.group(1) or 0)*3600+int(m.group(2) or 0)*60+int(m.group(3) or 0)


def auth():
    key = os.getenv("YOUTUBE_DATA_API_KEY", "").strip()
    if key:
        return {"key":key},{}
    # Use the OAuth credentials already configured for the MNShort publisher,
    # but never upload or request extra scopes from this read-only research.
    import requests
    from mn_short_youtube_direct import get_access_token
    with requests.Session() as session:
        token = get_access_token(session)
    return {},{"Authorization":"Bearer "+token}


def api(endpoint: str, query: dict, credentials: tuple) -> dict:
    params,headers=credentials
    args={**query,**params}
    url="https://www.googleapis.com/youtube/v3/"+endpoint+"?"+urlencode(args)
    try:
        with urlopen(Request(url,headers=headers),timeout=32) as response:
            data=json.load(response)
    except HTTPError as exc:
        raise RuntimeError("YouTube Data API rejected read-only request: HTTP "
                           +str(exc.code)+"; check API enablement, OAuth permissions and quota") from None
    if not isinstance(data,dict) or "items" not in data:
        raise RuntimeError("YouTube Data API returned no usable statistics")
    return data


def rank_niches(videos: dict, now: datetime) -> list[dict]:
    rankings=[]
    cutoff=now-timedelta(days=LOOKBACK_DAYS)
    for niche,candidates in videos.items():
        qualified={}
        for item in candidates:
            try:
                identifier=item["id"]
                views=int(item["views"])
                duration=int(item["duration_seconds"])
                created=datetime.fromisoformat(item["published_at"].replace("Z","+00:00"))
                channel=item["channel_id"]
                if not (0<duration<=MAX_SHORT_SECONDS and cutoff<=created<=now):
                    continue
                if views<MIN_VIEWS_PER_HIT or not identifier or not channel:
                    continue
                qualified[identifier]={
                    "id":identifier,"title":item["title"][:180],"views":views,
                    "channel_id":channel,"duration_seconds":duration,
                    "published_at":created.isoformat(),
                    "url":"https://www.youtube.com/shorts/"+identifier,
                }
            except (KeyError, ValueError, TypeError, AttributeError):
                continue
        top=sorted(qualified.values(),key=lambda x:x["views"],reverse=True)[:12]
        creators=len({x["channel_id"] for x in top})
        if len(top)<MIN_HITS or creators<2:
            continue
        # Multiple independent creators and recency matter more than one
        # exceptional outlier; this is demand evidence, NOT a virality promise.
        millions=sum(v["views"] for v in top)
        rankings.append({"topic":niche,"viral_videos":len(top),
                         "independent_creators":creators,
                         "total_views_7d":millions,
                         "median_views":int(median([v["views"] for v in top])),
                         "examples":top[:6]})
    return sorted(rankings,key=lambda x:(x["viral_videos"],x["median_views"],
                                         x["independent_creators"]),reverse=True)


def gather(now: datetime, credentials: tuple) -> dict:
    cutoff=(now-timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    seen={n:{} for n in NICHES}
    for niche,queries in NICHES.items():
        for phrase in queries:
            discovery=api("search",{"part":"snippet","q":phrase,
                "type":"video","videoDuration":"short",
                "order":"viewCount","maxResults":20,
                "publishedAfter":cutoff,"safeSearch":"moderate"},credentials)
            ids=[x.get("id",{}).get("videoId","") for x in discovery["items"]
                 if isinstance(x.get("id"),dict)]
            ids=[x for x in ids if re.fullmatch(r"[A-Za-z0-9_-]{11}",x)]
            if not ids:
                continue
            detail=api("videos",{"part":"snippet,statistics,contentDetails",
                                  "id":",".join(dict.fromkeys(ids))},credentials)
            for v in detail["items"]:
                snippet=v.get("snippet",{})
                duration=iso_seconds(v.get("contentDetails",{}).get("duration",""))
                item={
                    "id":v.get("id"),"title":snippet.get("title",""),
                    "published_at":snippet.get("publishedAt",""),
                    "channel_id":snippet.get("channelId",""),
                    "views":v.get("statistics",{}).get("viewCount",0),
                    "duration_seconds":duration,
                }
                if item["id"]:
                    seen[niche][item["id"]]=item
    ranked=rank_niches({k:list(v.values()) for k,v in seen.items()},now)
    if not ranked:
        raise RuntimeError("No niche meets minimum: 2 distinct recent Shorts, "
                           "each >=1M verified views from >=2 channels; skip publication")
    return {"checked_at_utc":now.isoformat(),"window_days":LOOKBACK_DAYS,
            "minimum_views_per_example":MIN_VIEWS_PER_HIT,
            "chosen":ranked[0],"ranking":ranked,
            "editorial_disclaimer":"Audience demand evidence; does NOT verify any news event."}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="weekly-niche.json")
    args=p.parse_args()
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc)
    report={"checked_at_utc":now.isoformat(),"status":"no_qualified_niche"}
    try:
        report=gather(now,auth())
        report["status"]="qualified"
        print("WEEKLY NICHE:",report["chosen"]["topic"],
              "independent creators:",report["chosen"]["independent_creators"],
              "viral examples:",report["chosen"]["viral_videos"])
    except Exception as exc:
        report["reason"]=str(exc)
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        raise SystemExit("No verified niche this Wednesday: "+str(exc))
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
