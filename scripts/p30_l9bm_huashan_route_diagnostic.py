#!/usr/bin/env python3
"""L9-BM: diagnose Unicode percent-encoded Huashan detail routes; never publish."""
import re
from urllib.parse import urljoin, urlsplit, unquote
from bs4 import BeautifulSoup
from p30_l9bl_huashan_source import HOME, HOST, norm

def classify_href(raw):
    if not raw or raw.startswith("//") or any(c in raw for c in ("\\", "\n", "\r", "\t")):
        return "UNSAFE", None
    before = urlsplit(raw)
    if any(p in (".", "..") for p in unquote(before.path).split("/")):
        return "UNSAFE", None
    url = urlsplit(urljoin(HOME, raw))
    if (url.scheme != "https" or url.hostname != HOST or url.username or
            url.password or url.port or url.query or url.fragment):
        return "UNSAFE", None
    path = unquote(url.path)
    if "%" in path or any(ord(c) < 32 for c in path) or
            not re.fullmatch(r"/exhibition/[^/]{1,100}/?", path):
        return "NON_DETAIL_ROUTE", None
    slug = path.split("/")[2]
    if not re.fullmatch(r"[\w\-]+", slug, flags=re.UNICODE):
        return "UNSAFE", None
    return ("ENCODED_UNICODE_DETAIL" if "%" in url.path else "PLAIN_DETAIL"), url.geturl()

def diagnose_index(html):
    soup = BeautifulSoup(html, "html.parser")
    counts = {"PLAIN_DETAIL":0,"ENCODED_UNICODE_DETAIL":0,"NON_DETAIL_ROUTE":0,"UNSAFE":0}
    candidates = {}
    conflicts = 0
    for a in soup.find_all("a", href=True, limit=1200):
        kind, url = classify_href(a["href"])
        counts[kind] += 1
        if url is None:
            continue
        title = norm(a.get_text(" ", strip=True))
        if not title:
            imgs = a.find_all("img", alt=True, limit=2)
            title = norm(imgs[0].get("alt", "")) if len(imgs) == 1 else ""
        if not 4 <= len(title) <= 250:
            continue
        if url in candidates and candidates[url] != title:
            conflicts += 1
        candidates.setdefault(url, title)
    return {"gate":"P30-L9-BM","source":"HUASHAN_PLATFORM_13",
            "routeCounts":counts,"sourceDerivedRouteCandidates":len(candidates),
            "titleConflicts":conflicts,
            "decision":"REVIEW_ROUTE_TOPOLOGY_NOT_EVENT_IDENTITY" if candidates and not conflicts else "HOLD_ROUTE_OR_TITLE",
            "acceptedFields":0,"goldenAccepted":0,"published":False,
            "releaseState":"HARD_HOLD_NO_PUBLICATION"}
