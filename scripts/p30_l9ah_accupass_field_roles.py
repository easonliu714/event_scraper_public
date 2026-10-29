#!/usr/bin/env python3
"""P30-L9-AH: bounded ACCUPASS local semantic role topology; never accept fields."""
import argparse
import hashlib
import json
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import p30_l9ag_accupass_detail_parity as prior

KIND = "EVENTRADAR_P30_L9AH_LOCAL_FIELD_ROLE_REVIEW_V1"
RELEASE = "HARD_HOLD_NO_PUBLICATION"
PARENT = "adbbe114c27259b80f5db80dcfee94204da09979"
ROLE_LABELS = {
    "EVENT": {"活動日期", "演出日期", "活動時間", "演出時間"},
    "SALE": {"售票時間", "開賣時間", "售票期間"},
    "ADMISSION": {"入場時間", "開放入場時間"},
    "REGISTRATION": {"報名時間", "報名期間", "登記時間"},
    "VOUCHER": {"兌換時間", "兌換期間"},
    "VENUE": {"活動地點", "演出地點", "活動場地"},
    "PRICE": {"票價", "票券價格"},
    "SESSION": {"場次", "演出場次"},
}
MAX_SCOPES = 8
MAX_PAIRS = 120
MAX_VALUE_CHARS = 240
MAX_HTML_BYTES = 1_500_000

def clean_label(s):
    return "".join(s.strip().strip("：:").split())

def scoped_pairs(html):
    """Use only explicit direct dt/dd and th/td siblings inside semantic roots."""
    if len(html.encode("utf-8")) > MAX_HTML_BYTES:
        return {"assessed":False,"hold":"HTML_CAP","roles":{}}
    soup = BeautifulSoup(html, "html.parser")
    roots = soup.select("main, article, [role='main'], #event-detail")
    if not roots:
        return {"assessed":False,"hold":"NO_SEMANTIC_ROOT","roles":{}}
    if len(roots) > MAX_SCOPES:
        return {"assessed":False,"hold":"SCOPE_CAP","roles":{}}
    pairs = []
    for root in roots:
        for dt in root.select("dt"):
            dd = dt.find_next_sibling()
            if dd is not None and dd.name == "dd":
                pairs.append((dt,dd))
        for tr in root.select("tr"):
            cells = tr.find_all(["th","td"], recursive=False)
            if len(cells)==2 and cells[0].name=="th" and cells[1].name=="td":
                pairs.append((cells[0],cells[1]))
    if len(pairs) > MAX_PAIRS:
        return {"assessed":False,"hold":"PAIR_CAP","roles":{}}
    values = {k:set() for k in ROLE_LABELS}
    evidence = {k:0 for k in ROLE_LABELS}
    seen = set()
    for label_node, value_node in pairs:
        label = clean_label(label_node.get_text(" ",strip=True))
        roles = [k for k,names in ROLE_LABELS.items() if label in names]
        if len(roles)!=1:
            continue
        value = " ".join(value_node.get_text(" ",strip=True).split())
        if not value or len(value)>MAX_VALUE_CHARS:
            continue
        pair_id = (id(label_node),id(value_node))
        if pair_id in seen:
            continue
        seen.add(pair_id)
        role = roles[0]
        evidence[role]+=1
        values[role].add(value)
    roles = {}
    for role in ROLE_LABELS:
        count = evidence[role]
        distinct = len(values[role])
        decision = ("HOLD_NO_EXPLICIT_LOCAL_PAIR" if not count else
                    "HOLD_CONFLICTING_LOCAL_VALUES" if distinct>1 else
                    "REVIEW_ONE_LOCAL_ROLE_NOT_ACCEPTED")
        roles[role] = {"localPairCount":count,"distinctValueCount":distinct,
                       "decision":decision,"accepted":False}
    return {"assessed":True,"hold":None,"scopeCount":len(roots),
            "inspectedPairs":len(pairs),"roles":roles,
            "acceptedFields":0,"rawValuesPersisted":False}

def probe():
    result = {"listHttp":None,"listDecision":"HOLD_NOT_STARTED","detailCount":0,
              "details":[],"decision":"HOLD_NOT_STARTED"}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        ctx=browser.new_context(accept_downloads=False,service_workers="block")
        def guard(route):
            if route.request.is_navigation_request() and not prior.prior.allowed(route.request.url):
                route.abort("blockedbyclient")
            else:
                route.continue_()
        page=ctx.new_page()
        page.route("**/*",guard)
        candidates=[]
        try:
            response=page.goto(prior.ENTRY,wait_until="domcontentloaded",timeout=18000)
            result["listHttp"]=response.status if response else None
            if result["listHttp"]==200 and page.url==prior.ENTRY:
                raw,raw_c=prior.list_candidates(response.text())
                dom=None;dom_c=[]
                for i in range(prior.OBSERVATIONS):
                    if i: page.wait_for_timeout(650)
                    dom,dom_c=prior.list_candidates(page.content())
                if (raw["assessed"] and dom["assessed"] and
                    not raw["hold"] and not dom["hold"] and
                    {x[0] for x in raw_c}=={x[0] for x in dom_c}):
                    candidates=dom_c[:prior.MAX_DETAILS]
                    result["listDecision"]="REVIEW_SOURCE_BOUND_CANDIDATES"
                else: result["listDecision"]="HOLD_LIST_STABILITY_OR_SCOPE"
            else: result["listDecision"]="HOLD_LIST_HTTP_OR_URL"
        except Exception as exc:
            result["listDecision"]="HOLD_LIST_"+type(exc).__name__
        finally: page.close()
        for candidate in candidates:
            d=ctx.new_page()
            d.route("**/*",guard)
            item={"http":None,"identityDecision":"HOLD_NOT_STARTED",
                  "fieldTopology":{"assessed":False,"hold":"IDENTITY_NOT_REVIEWED","roles":{}}}
            states=[];obs=[];final_url="";redirected=False;error=None;last_html=None
            try:
                response=d.goto(candidate[2],wait_until="domcontentloaded",timeout=18000)
                item["http"]=response.status if response else None
                redirected=bool(response and response.request.redirected_from)
                if item["http"]==200 and prior.safe_event(d.url):
                    for i in range(prior.OBSERVATIONS):
                        if i:d.wait_for_timeout(650)
                        states.append(d.evaluate("document.readyState"))
                        last_html=d.content()
                        obs.append(prior.detail_heading_evidence(last_html,candidate[1]))
            except Exception as exc: error=type(exc).__name__
            finally:
                final_url=d.url
                d.close()
            item["identityDecision"]=prior.detail_decision(candidate,final_url,item["http"],
                                                             redirected,states,obs,error)
            if item["identityDecision"].startswith("REVIEW_") and last_html is not None:
                item["fieldTopology"]=scoped_pairs(last_html)
            result["details"].append(item)
        ctx.close();browser.close()
    result["detailCount"]=len(result["details"])
    if result["detailCount"]!=prior.MAX_DETAILS:
        result["decision"]="HOLD_LIST_OR_DETAIL_SAMPLE"
    elif not all(x["identityDecision"].startswith("REVIEW_") for x in result["details"]):
        result["decision"]="HOLD_DETAIL_IDENTITY"
    elif not all(x["fieldTopology"]["assessed"] for x in result["details"]):
        result["decision"]="HOLD_LOCAL_ROLE_TOPOLOGY_UNASSESSED"
    else:
        result["decision"]="REVIEW_LOCAL_FIELD_ROLE_TOPOLOGY_NOT_ACCEPTED"
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--live",action="store_true")
    p.add_argument("--status",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    if not args.live: p.error("explicit --live required")
    prior.prior.validate_status(Path(args.status).read_bytes())
    if Path(args.out).resolve()!=(Path.cwd()/"p30-l9ah-evidence").resolve():
        raise ValueError("HOLD_OUTPUT_SCOPE")
    r=probe()
    r.update(kind=KIND,parentHead=PARENT,releaseState=RELEASE,acceptedFields=0,
             goldenAccepted=0,published=False,productionModified=False,
             writerExecuted=False,schedulerExecuted=False,notifierExecuted=False,
             rawHtmlPersisted=False,rawUrlsPersisted=False,rawTitlesPersisted=False,
             rawEventIdsPersisted=False,rawFieldValuesPersisted=False,
             queryValuesPersisted=False,cookiesPersisted=False)
    out=Path(args.out);out.mkdir(exist_ok=True)
    raw=(json.dumps(r,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode()
    (out/"accupass_roles.json").write_bytes(raw)
    (out/"manifest.json").write_text(json.dumps({
        "kind":KIND,"releaseState":RELEASE,
        "filesSHA256":{"accupass_roles.json":hashlib.sha256(raw).hexdigest()}
    },sort_keys=True,indent=2)+"\n")
    print("L9AH_DECISION="+r["decision"])
    print("L9AH_DETAIL_COUNT="+str(r["detailCount"]))
    print("HOLD_NO_FORMAL_FIELDS_GOLDEN_PUBLICATION")

if __name__=="__main__":main()
