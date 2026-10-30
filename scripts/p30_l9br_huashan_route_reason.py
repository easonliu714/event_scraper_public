#!/usr/bin/env python3
"""L9-BR: classify one observed Huashan decoded-path / canonical-href mismatch.
No GET; source HTML is caller-supplied and never persisted. No FIELD promotion.
"""
import hashlib
from collections import Counter
from urllib.parse import unquote, urljoin, urlsplit
from bs4 import BeautifulSoup
from p30_l9bp_huashan_live_card_probe import ROUTE, INDEX, HOLD
from p30_l9bn_huashan_card_identity import classify_href

def diagnose(html, selected=ROUTE):
    kind, target = classify_href(selected)
    out={"gate":"P30-L9-BR","source":"HUASHAN_PLATFORM_13",
         "decodedPathMatches":0,"strictMatches":0,"reasonCounts":{},
         "acceptedFields":0,"goldenAccepted":0,"published":False,
         "ticketEventId":None,"releaseState":HOLD}
    if target is None:
        return dict(out,decision="HOLD_UNSAFE_TARGET")
    expected=unquote(urlsplit(target).path)
    reasons=Counter()
    for a in BeautifulSoup(html,"html.parser").find_all("a",href=True,limit=2500):
        raw=a["href"]
        try:
            resolved=urlsplit(urljoin(INDEX,raw))
            if unquote(resolved.path)!=expected:
                continue
            out["decodedPathMatches"]+=1
            _,canonical=classify_href(raw)
            if canonical==target:
                out["strictMatches"]+=1
                reasons["EXACT_CANONICAL"]+=1
            elif resolved.scheme!="https" or resolved.hostname!="www.huashan1914.com" or resolved.username or resolved.password or resolved.port:
                reasons["UNSAFE_OR_FOREIGN_ORIGIN"]+=1
            elif resolved.query or resolved.fragment:
                reasons["QUERY_OR_FRAGMENT_NOT_IDENTITY"]+=1
            elif canonical is None:
                reasons["REJECTED_PATH_SHAPE"]+=1
            elif resolved.path!=urlsplit(target).path:
                reasons["ENCODING_OR_UNICODE_VARIANT"]+=1
            else:
                reasons["NONIDENTICAL_CANONICAL_URL"]+=1
        except (ValueError,UnicodeError):
            reasons["UNPARSEABLE"]+=1
    out["reasonCounts"]=dict(sorted(reasons.items()))
    out["targetPathSHA256"]=hashlib.sha256(expected.encode()).hexdigest()
    if out["strictMatches"]==1 and out["decodedPathMatches"]==1:
        return dict(out,decision="REVIEW_EXACT_ROUTE_ONLY_NO_FIELDS")
    if out["strictMatches"]>1 or out["decodedPathMatches"]>1:
        return dict(out,decision="HOLD_DUPLICATE_OR_CONFLICTING_ROUTE")
    if out["decodedPathMatches"]==1:
        return dict(out,decision="HOLD_ROUTE_VARIANT_REQUIRES_SOURCE_IDENTITY")
    return dict(out,decision="HOLD_ROUTE_NOT_PRESENT")

if __name__=="__main__":
    raise SystemExit("OFFLINE_IMPORT_ONLY_NO_IMPLICIT_NETWORK")
