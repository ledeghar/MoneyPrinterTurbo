#!/usr/bin/env python3
"""Fail-closed destination-channel guard. Runs BEFORE any YouTube upload."""
from __future__ import annotations
import os
import requests
from mn_short_youtube_direct import get_access_token

def verify_expected_channel(session:requests.Session):
    expected=os.getenv("MNSHORT_EXPECTED_CHANNEL_ID","").strip()
    if not expected.startswith("UC") or len(expected)!=24:
        raise RuntimeError("MNSHORT_EXPECTED_CHANNEL_ID must name the authorized destination channel")
    token=get_access_token(session)
    response=session.get("https://www.googleapis.com/youtube/v3/channels",
                         params={"part":"id,snippet","mine":"true"},
                         headers={"Authorization":"Bearer "+token},timeout=30)
    if response.status_code!=200:
        raise RuntimeError("Cannot verify destination channel: YouTube API HTTP "
                           +str(response.status_code)+"; upload blocked")
    actual=[str(x.get("id","")) for x in response.json().get("items",[])]
    if expected not in actual:
        raise RuntimeError("OAuth channel does not match configured destination; upload blocked")
    print("CONFIRMED expected destination channel ID:",expected)
    return expected

if __name__=="__main__":
    with requests.Session() as session:
        verify_expected_channel(session)
