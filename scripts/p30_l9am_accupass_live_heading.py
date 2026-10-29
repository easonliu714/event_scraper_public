#!/usr/bin/env python3
"""P30-L9-AM: source-first bounded heading-region topology after same-path identity.
One normal public ACCUPASS list, at most two identity-bound details. Review/HOLD only.
Reuses frozen L9-AH browser flow and L9-AK inspector; never persists raw pages.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from unittest.mock import patch
import p30_l9ah_accupass_field_roles as ah
import p30_l9ak_accupass_heading_near as ak

KIND="EVENTRADAR_P30_L9AM_LIVE_HEADING_REGION_V1"
RELEASE="HARD_HOLD_NO_PUBLICATION"
MAX_DETAILS=2

def adapter(html):
    r=ak.inspect_heading_regions(html)
    return {"assessed":r.get("assessed") is True,
            "hold":None if r.get("assessed") is True else r.get("decision","HOLD_INSPECTOR"),
            "roles":{},
            "headingDecision":r.get("decision","HOLD_INSPECTOR"),
            "headingCount":r.get("headingCount",0),
            "boundedRegions":r.get("boundedRegions",0),
            "observedLocalPairs":r.get("observedLocalPairs",0)}

def summarize(source):
    details=source.get("details",[])
    if not isinstance(details,list) or len(details)>MAX_DETAILS:
        return {"decision":"HOLD_DETAIL_SCOPE","detailCount":0,"details":[]}
    safe=[]
    for item in details:
        topology=item.get("fieldTopology") or {}
        identity=item.get("identityDecision","")
        if not isinstance(identity,str) or not (identity.startswith("REVIEW_") or identity.startswith("HOLD_")):
            identity="HOLD_INVALID_IDENTITY_DECISION"
        decision=topology.get("headingDecision",topology.get("hold","HOLD_UNASSESSED"))
        if not isinstance(decision,str) or not (decision.startswith("REVIEW_") or decision.startswith("HOLD_")):
            decision="HOLD_UNKNOWN_HEADING_DECISION"
        safe.append({"http":item.get("http") if item.get("http") in (200,None) else None,
                     "identityDecision":identity,"headingDecision":decision,
                     "assessed":topology.get("assessed") is True,
                     "headingCount":min(topology.get("headingCount",0),100) if type(topology.get("headingCount",0)) is int and topology.get("headingCount",0)>=0 else 0,
                     "boundedRegions":min(topology.get("boundedRegions",0),100) if type(topology.get("boundedRegions",0)) is int and topology.get("boundedRegions",0)>=0 else 0,
                     "observedLocalPairs":min(topology.get("observedLocalPairs",0),80) if type(topology.get("observedLocalPairs",0)) is int and topology.get("observedLocalPairs",0)>=0 else 0})
    identity_ok=len(safe)==MAX_DETAILS and all(x["identityDecision"].startswith("REVIEW_") for x in safe)
    assessed=identity_ok and all(x["assessed"] for x in safe)
    return {"decision":"HOLD_IDENTITY_OR_COUNT" if not identity_ok else
                       "HOLD_BOUNDED_HEADING_TOPOLOGY" if not assessed else
                       "REVIEW_BOUNDED_HEADING_TOPOLOGY_NOT_FIELDS",
            "detailCount":len(safe),"details":safe,
            "listHttp":source.get("listHttp") if source.get("listHttp") in (200,None) else None,
            "listDecision":source.get("listDecision") if source.get("listDecision") in
            ("REVIEW_SOURCE_BOUND_CANDIDATES","HOLD_LIST_STABILITY_OR_SCOPE","HOLD_LIST_HTTP_OR_URL") else "HOLD_UNCLASSIFIED_LIST"}

def probe():
    with patch.object(ah,"scoped_pairs",adapter):
        source=ah.probe()
    return summarize(source)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--live",action="store_true")
    p.add_argument("--status",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if not args.live:
        p.error("explicit --live required")
    ah.prior.prior.validate_status(Path(args.status).read_bytes())
    out=Path(args.out)
    if out.resolve()!=(Path.cwd()/"p30-l9am-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    result=probe()
    result.update(kind=KIND,releaseState=RELEASE,maxDetails=MAX_DETAILS,
                  acceptedFields=0,goldenAccepted=0,published=False,
                  rawHtmlPersisted=False,rawUrlsPersisted=False,rawTitlesPersisted=False,
                  rawEventIdsPersisted=False,rawFieldValuesPersisted=False)
    out.mkdir(exist_ok=True)
    raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+chr(10)).encode()
    (out/"heading_review.json").write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps({"kind":KIND,"releaseState":RELEASE,
      "filesSHA256":{"heading_review.json":hashlib.sha256(raw).hexdigest()}},sort_keys=True,indent=2)+chr(10))
    print("L9AM_DECISION="+result["decision"])
    print("L9AM_DETAILS="+str(result["detailCount"]))
    print("HOLD_NO_FORMAL_FIELDS_GOLDEN_PUBLICATION")
if __name__=="__main__":
    main()
