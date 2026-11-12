#!/usr/bin/env python3
"""Free, read-only NASA/USGS candidates for DISI; no publishing or image rights."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from urllib.request import Request,urlopen
FEEDS={
 "USGS":"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
 "NASA_EONET":"https://eonet.gsfc.nasa.gov/api/v3/events?limit=5&days=7",
}
def normalize(provider,data):
 if provider=="USGS":
  items=data.get("features",[])
  if not isinstance(items,list):raise ValueError("Invalid USGS feed")
  return [{"provider":"USGS","title":str(f["properties"].get("title",""))[:240],"url":f["properties"]["url"],"feed":FEEDS[provider]} for f in items[:5] if isinstance(f,dict) and isinstance(f.get("properties"),dict) and f["properties"].get("url")]
 if provider=="NASA_EONET":
  items=data.get("events",[])
  if not isinstance(items,list):raise ValueError("Invalid EONET feed")
  return [{"provider":"NASA EONET","title":str(e.get("title",""))[:240],"url":e["link"],"feed":FEEDS[provider]} for e in items[:5] if isinstance(e,dict) and e.get("link")]
 raise ValueError("Unsupported feed")
def read(url):
 with urlopen(Request(url,headers={"User-Agent":"DISIEditorialResearch/0.1","Accept":"application/json"}),timeout=15) as r:
  if r.geturl().split("/")[2]!=url.split("/")[2]:raise ValueError("External redirect")
  raw=r.read(2_000_001)
 if len(raw)>2_000_000:raise ValueError("Feed larger than 2 MB")
 return json.loads(raw)
def collect(live=False,fetch=read):
 out={"schema":"disi-public-signals/0.1","checked_at":datetime.now(timezone.utc).isoformat(),"live":live,"status":"UNVERIFIED_EDITORIAL_CANDIDATES","publication_enabled":False,"image_reuse_authorized":False,"items":[],"errors":[]}
 if not live:return out
 for provider,url in FEEDS.items():
  try:out["items"]+=normalize(provider,fetch(url))
  except Exception as e:out["errors"].append({"provider":provider,"message":str(e)[:200]})
 return out
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--live",action="store_true",help="Explicitly query 2 read-only public feeds")
 p.add_argument("--output",required=True,type=Path)
 a=p.parse_args()
 report=collect(a.live)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("Candidates:",len(report["items"]),"errors:",len(report["errors"]))
 if a.live and len(report["errors"])==len(FEEDS):raise SystemExit("Both sources unavailable; not publishing")
