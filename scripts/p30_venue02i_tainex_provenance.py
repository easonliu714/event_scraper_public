#!/usr/bin/env python3
"""VENUE-02I: one official TAINEX detail; two-ID provenance and anti-collapse."""
from __future__ import annotations
import argparse,hashlib,json
from datetime import datetime,timezone
from bs4 import BeautifulSoup
from p30_venue02g_tainex_parity import local_id
from p30_venue02h_tainex_live_identity import bounded_get
URL="https://www.tainex.com.tw/event/690"
TITLE="2026臺灣茶業博覽會"
OTHER="https://www.tainex.com.tw/event/689"
RELEASE="HARD_HOLD_NO_PUBLICATION"
LABELS={"exhibitionPeriod":"展覽活動期間","venue":"活動地點","organizer":"主辦單位"}

def inspect_detail(html,observed_at):
    base=dict(source="TAINEX_OFFICIAL_VENUE",sourceURL=URL,
              observedAtUTC=observed_at,decision="HOLD_INPUT",
              venueLocalIdReview=None,distinctFrom689="UNKNOWN",
              fieldProvenance={},acceptedFields=0,goldenAccepted=0,
              published=False,ticketEventId=None,releaseState=RELEASE)
    try:
        datetime.fromisoformat(observed_at.replace("Z","+00:00"))
    except (ValueError,AttributeError):
        return base
    if not isinstance(html,str) or not html or len(html.encode("utf-8"))>180000:
        return base
    if local_id(URL)!="690" or local_id(OTHER)!="689":
        return dict(base,decision="HOLD_SOURCE_PATH_IDENTITY")
    soup=BeautifulSoup(html,"html.parser")
    titles=[h for h in soup.find_all(["h1","h2"]) if " ".join(h.get_text(" ",strip=True).split())==TITLE]
    if len(titles)!=1:
        return dict(base,decision="HOLD_DETAIL_EXACT_TITLE_NOT_UNIQUE")
    base["venueLocalIdReview"]="690"
    base["distinctFrom689"]="REVIEW_DISTINCT_SOURCE_LOCAL_IDS_NO_MERGE"
    text=" ".join(soup.get_text(" ",strip=True).split())
    counts={role:text.count(label) for role,label in LABELS.items()}
    base["roleLabelCounts"]=counts
    if any(v!=1 for v in counts.values()):
        return dict(base,decision="HOLD_ROLE_LABEL_NOT_UNIQUE")
    base["fieldProvenance"]={
      role:dict(source=URL,observed_at=observed_at,
                role={"exhibitionPeriod":"EXHIBITION_RANGE_NOT_SESSION_START",
                      "venue":"VENUE_ROLE_NOT_TICKET_URL",
                      "organizer":"ORGANIZER_NOT_TICKET_EVENT_ID"}[role],
                decision="REVIEW_LABEL_PRESENCE_NO_VALUE_ACCEPTANCE")
      for role in LABELS
    }
    return dict(base,decision="REVIEW_ONE_OFFICIAL_DETAIL_ROLE_PROVENANCE_NO_PROMOTION")

def live_one():
    stamp=datetime.now(timezone.utc).isoformat()
    out=dict(observedAtUTC=stamp,requestCount=1,requestBudget=1,
             decision="HOLD_NETWORK",acceptedFields=0,goldenAccepted=0,
             published=False,releaseState=RELEASE)
    receipt,html=bounded_get(URL)
    out["receipt"]=receipt
    if html is not None:
        out.update(inspect_detail(html,stamp))
    return out

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--live-one",action="store_true")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    if not args.live_one:raise SystemExit("NO_IMPLICIT_NETWORK")
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(live_one(),f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write("\n")
