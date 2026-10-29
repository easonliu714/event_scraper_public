"""P30-L9-AK: offline heading-near bounded topology, hidden-ancestor fail-closed.
No global regex, no field acceptance, no network. Only explicit small local roots.
"""
from __future__ import annotations
from bs4 import BeautifulSoup
import p30_l9ai_accupass_sibling_roles as ai

RELEASE="HARD_HOLD_NO_PUBLICATION"
MAX_HEADINGS=12
MAX_DEPTH=4
MAX_REGION_CONTAINERS=400

def _hidden_chain(node):
    while node is not None and getattr(node,"name",None):
        if ai.hidden(node):
            return True
        node=node.parent
    return False

def inspect_heading_regions(html):
    base={"assessed":False,"decision":"HOLD_INVALID_HTML","headingCount":0,
          "boundedRegions":0,"acceptedFields":0,"published":False,
          "rawValuesPersisted":False}
    if not isinstance(html,str) or len(html.encode("utf-8"))>ai.MAX_HTML_BYTES:
        return base
    soup=BeautifulSoup(html,"html.parser")
    headings=soup.select("main h1,main h2,article h1,article h2,[role='main'] h1,[role='main'] h2,#event-detail h1,#event-detail h2")
    unique=list({id(h):h for h in headings}.values())
    if not unique:
        return dict(base,decision="HOLD_NO_SEMANTIC_HEADING")
    if len(unique)>MAX_HEADINGS:
        return dict(base,decision="HOLD_HEADING_CAP",headingCount=len(unique))
    if any(_hidden_chain(h) for h in unique):
        return dict(base,decision="HOLD_HIDDEN_HEADING_ANCESTOR",headingCount=len(unique))
    regions=[]
    for heading in unique:
        ancestor=heading.parent
        chosen=None
        for _ in range(MAX_DEPTH):
            if ancestor is None or not getattr(ancestor,"name",None):
                break
            if _hidden_chain(ancestor):
                return dict(base,decision="HOLD_HIDDEN_REGION_ANCESTOR",headingCount=len(unique))
            if ancestor.name in ("div","section","article","main"):
                count=len(ancestor.select("div,li,section,p"))
                if count<=MAX_REGION_CONTAINERS:
                    chosen=ancestor
                    break
            ancestor=ancestor.parent
        if chosen is None:
            return dict(base,decision="HOLD_NO_BOUNDED_HEADING_REGION",headingCount=len(unique))
        regions.append(chosen)
    regions=list({id(x):x for x in regions}.values())
    if len(regions)!=1:
        return dict(base,decision="HOLD_MULTIPLE_HEADING_REGIONS",headingCount=len(unique),boundedRegions=len(regions))
    region=regions[0]
    if region.find(["script","style","form","iframe"]):
        return dict(base,decision="HOLD_INTERACTIVE_OR_SCRIPT_REGION",headingCount=len(unique),boundedRegions=1)
    result=ai.inspect_local_siblings("<main>"+str(region)+"</main>")
    if not result.get("assessed"):
        return dict(base,decision=result.get("hold","HOLD_LOCAL_INSPECTOR"),headingCount=len(unique),boundedRegions=1)
    return dict(base,assessed=True,decision="REVIEW_BOUNDED_HEADING_TOPOLOGY_NOT_ACCEPTED",
                headingCount=len(unique),boundedRegions=1,
                observedLocalPairs=sum(x["localPairCount"] for x in result["roles"].values()))

def offline_contract():
    return dict(kind="EVENTRADAR_P30_L9AK_HEADING_NEAR_V1",releaseState=RELEASE,
                httpRequests=0,acceptedFields=0,goldenAccepted=0,published=False,
                rawHtmlPersisted=False,rawEventIdsPersisted=False,
                decision="REVIEW_OFFLINE_HEADING_NARROWING_ONLY")
