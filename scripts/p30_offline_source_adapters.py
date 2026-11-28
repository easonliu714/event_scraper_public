"""Fixed KKTIX / ACCUPASS offline LIST->same-ID DETAIL review adapters.

Consumes only supplied, SHA-pinned local fixture bytes. Never requests a
website, accepts a formal field, writes a snapshot, or publishes activities.
Each adapter can be reused by the shared field evidence / isolated LKG Core.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlsplit
from bs4 import BeautifulSoup

SOURCES = {
    "kktix": ("kktix.com", "events"),
    "accupass": ("www.accupass.com", "event"),
    "twtc": ("twtc.com.tw", "exhibition_more.aspx"),
    "cksmh": ("event.culture.tw", "mocweb/reg/CKSMH/Detail.init.ctr"),
}
LIMIT = 2_000_000
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")


def _canonical_event_url(provider, href):
    """Keep exact event IDs; reuse #236 ACCUPASS discovery-query rules."""
    host, prefix = SOURCES[provider]
    if not isinstance(href, str) or not href or href.startswith("//"):
        return None
    try:
        url = urlsplit(urljoin("https://" + host + "/", href))
        if (url.scheme != "https" or url.hostname != host or url.port is not None
                or url.username is not None or url.password is not None
                or url.fragment):
            return None
        if provider == "cksmh":
            if url.path not in ("/mocweb/reg/CKSMH/Detail.init.ctr",
                                "/CKSMH/portal/Registration/C0103MAction"):
                return None
            query = parse_qsl(url.query, keep_blank_values=True, strict_parsing=True)
            if len(query) != 1 or query[0][0] != "actId" or not re.fullmatch(
                    r"[0-9]{3,9}", query[0][1]):
                return None
            sid = query[0][1]
            return sid, "https://event.culture.tw" + url.path + "?actId=" + sid
        if provider == "twtc":
            if url.path != "/exhibition_more.aspx":
                return None
            query = parse_qsl(url.query, keep_blank_values=True, strict_parsing=True)
            params = dict(query)
            if (len(query) != len(params) or set(params) - {"id", "p"}
                    or not re.fullmatch(r"[0-9]{2,12}", params.get("id", ""))
                    or params.get("p", "home") != "home"):
                return None
            sid = params["id"]
            return sid, "https://twtc.com.tw/exhibition_more.aspx?id=" + sid + "&p=home"
        if url.query:
            if provider != "accupass":
                return None
            # Port the exact observed key/value allowlist from #236
            # p30_ab_kktix_fuzhong_native.exact_detail (08167a0a).
            query = parse_qsl(url.query, keep_blank_values=True, strict_parsing=True)
            allowed = {"utm_campaign": "accu_e_", "utm_medium": "search_result_",
                       "utm_source": "web"}
            if (len(query) != len(set(k for k, _ in query))
                    or any(allowed.get(k) != v for k, v in query)):
                return None
        path = url.path.split("/")
        if len(path) != 3 or path[0] != "" or path[1] != prefix:
            return None
        sid = path[2]
        if not IDENTIFIER.fullmatch(sid):
            return None
        return sid, "https://" + host + "/" + prefix + "/" + sid
    except ValueError:
        return None


def _list_url(provider, receipt):
    """Only the known public LIST endpoints; retain legacy root fixtures."""
    root = "https://" + SOURCES[provider][0] + "/"
    observed = receipt.get("source_url") if isinstance(receipt, dict) else None
    allowed = {root, root + "search"} if provider == "accupass" else {root}
    if provider == "cksmh":
        allowed = {"https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr"}
    if provider == "twtc":
        allowed = {"https://twtc.com.tw/exhibition?p=home"}
    if provider == "accupass":
        # Indexed regional/category entrances, not proof of live coverage.
        # Exact allowlist only; no guessed pagination or arbitrary query keys.
        allowed.update(root + "?area=" + area for area in ("north", "center", "south"))
        allowed.update(root + "?area=north&channel=" + channel
                       for channel in ("1", "2", "3"))
    if not isinstance(observed, str) or observed not in allowed:
        raise ValueError("SOURCE_RECEIPT_PROVENANCE_HOLD")
    return observed

def _read_fixture(root, relative):
    """Fail closed on path traversal, symlinks, directories and oversized files."""
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("SOURCE_FIXTURE_PATH_HOLD")
    base = Path(root).resolve(strict=True)
    candidate = base / relative
    if not candidate.resolve().is_relative_to(base):
        raise ValueError("SOURCE_FIXTURE_PATH_HOLD")
    segment = base
    for part in Path(relative).parts:
        if part in (".", "..") or segment.joinpath(part).is_symlink():
            raise ValueError("SOURCE_FIXTURE_PATH_HOLD")
        segment = segment / part
    if not candidate.is_file() or candidate.stat().st_size > LIMIT:
        raise ValueError("SOURCE_FIXTURE_IO_HOLD")
    return candidate.read_bytes()


def _receipt(body, receipt, url):
    if (not isinstance(receipt, dict)
            or receipt.get("evidence_class") != "SEALED_OFFLINE_FIXTURE_ONLY"
            or receipt.get("source_url") != url
            or receipt.get("body_sha256") != hashlib.sha256(body).hexdigest()):
        raise ValueError("SOURCE_RECEIPT_PROVENANCE_HOLD")
    stamp = receipt.get("observed_at")
    try:
        observed = datetime.fromisoformat(stamp)
    except (ValueError, TypeError):
        raise ValueError("SOURCE_RECEIPT_TIME_HOLD") from None
    if observed.utcoffset() is None:
        raise ValueError("SOURCE_RECEIPT_TIME_HOLD")
    return stamp


def _twtc_list(body):
    """Port the verified L3-A title-cell/table contract, without the 39-row freeze.

    L3-A #11 a63baf94 / L4-A #13 b1651e6f: preserve period text, exact
    official detail ID and title ownership; conflicting IDs fail closed.
    """
    soup = BeautifulSoup(body, "html.parser")
    found = {}
    for tr in soup.find_all("tr"):
        cols = tr.find_all("td", recursive=False)
        if len(cols) < 3:
            continue
        period = " ".join(cols[0].stripped_strings)
        if not (re.fullmatch(r"[0-9]{1,2}/[0-9]{1,2}\s*[~～-]\s*[0-9]{1,2}/[0-9]{1,2}", period)
                or period == "延期未定"):
            continue
        title = " ".join(" ".join(x for x in cols[1].stripped_strings
                                  if x.strip().casefold() not in ("more", "詳情")).split())
        edges = {}
        for link in cols[1].find_all("a", href=True):
            href = link["href"]
            parsed = _canonical_event_url("twtc", href)
            if parsed is not None:
                sid, canonical = parsed
                edges.setdefault(sid, (canonical, set()))[1].add(
                    urljoin("https://twtc.com.tw/", href))
        # Unknown rows cannot be silently dropped from a claimed LIST.
        if len(edges) != 1 or len(title) < 4:
            raise ValueError("SOURCE_TWTC_LIST_IDENTITY_HOLD")
        sid, (canonical, urls) = next(iter(edges.items()))
        previous = found.get(sid)
        if previous and (previous["title"] != title or previous["period"] != period):
            raise ValueError("SOURCE_LIST_DUPLICATE_IDENTITY_HOLD")
        found[sid] = {"id": sid, "title": title, "url": canonical, "period": period,
                      "source_link_urls": sorted(urls | set(
                          previous["source_link_urls"] if previous else []))}
        if len(found) > 100:
            raise ValueError("SOURCE_TWTC_LIST_CAP_HOLD")
    return found


def _twtc_period_fields(article, card, sid, stamp, sha):
    """Reuse L4-A exact full-year period + LIST MM/DD parity, never infer year."""
    from datetime import date
    raw = card["period"]
    if raw == "延期未定":
        reason = "SOURCE_TWTC_POSTPONED_HOLD"
    else:
        matches = re.findall(
            r"展出日期\s*[:：]\s*(20[0-9]{2}/[0-9]{1,2}/[0-9]{1,2})\s*[~～-]\s*(20[0-9]{2}/[0-9]{1,2}/[0-9]{1,2})",
            " ".join(article.stripped_strings))
        reason = "SOURCE_TWTC_PERIOD_AMBIGUOUS_HOLD"
        if len(matches) == 1:
            try:
                start, end = [date(*map(int, x.split("/"))) for x in matches[0]]
                md = [tuple(map(int, x.split("/"))) for x in re.split(r"\s*[~～-]\s*", raw)]
                if start <= end and md == [(start.month, start.day), (end.month, end.day)]:
                    return {"activity_period": _field(
                        [start.isoformat(), end.isoformat()], "EXHIBITION_PERIOD", sid,
                        card["url"], stamp, sha, "REVIEW",
                        "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")}
                reason = "SOURCE_TWTC_LIST_DETAIL_PERIOD_CONFLICT_HOLD"
            except ValueError:
                reason = "SOURCE_TWTC_INVALID_DATE_HOLD"
    return {"activity_period": _field(None, "UNKNOWN", sid, card["url"], stamp, sha,
                                        "HOLD", reason)}


def _cksmh_list(body):
    """Reuse L2-B actId/list-anchor ownership, not its one-shot network runner."""
    listing = "https://event.culture.tw/mocweb/reg/CKSMH/Query.list.ctr"
    soup = BeautifulSoup(body, "html.parser")
    found = {}
    for link in soup.find_all("a", href=True):
        href = urljoin(listing, link["href"])
        parsed = _canonical_event_url("cksmh", href)
        if parsed is None:
            continue
        sid, canonical = parsed
        title = " ".join(link.get_text(" ", strip=True).split())
        attr = " ".join((link.get("title") or "").split())
        if title in ("詳內容", "報名", "立即報名", "活動詳情", "詳細內容"):
            continue
        if title and attr and title != attr:
            raise ValueError("SOURCE_LIST_CARD_TITLE_CONFLICT_HOLD")
        title = title or attr
        if len(title) < 3 or len(title) > 300:
            continue
        if sid in found and (found[sid]["title"] != title or found[sid]["url"] != canonical):
            raise ValueError("SOURCE_LIST_DUPLICATE_IDENTITY_HOLD")
        found[sid] = {"id": sid, "title": title, "url": canonical,
                      "source_link_urls": [canonical]}
        if len(found) > 60:
            raise ValueError("SOURCE_CKSMH_LIST_CAP_HOLD")
    return found


def _cksmh_semantic_roles(page, title):
    """Port pure L4-C parser from #18 2656c43f, no historical GET or frozen count."""
    import unicodedata
    def short_title(text):
        s = " ".join(text.split())
        for suffix in ("圖片說明", "圖片描述", "圖片資訊"):
            if s.endswith(suffix):
                s = s[:-len(suffix)].rstrip()
        return s
    def normalize(text):
        return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(text))).casefold()

    SECTION_START = re.compile(r"場\s*次\s*資\s*料")
    SESSION_MARK = re.compile(r"場\s*次\s*[:：]")
    REG_MARK = re.compile(r"報\s*名\s*期\s*間")
    INTRO_MARK = re.compile(r"活動\s*內\s*容\s*介\s*紹")
    VENUE_MARK = re.compile(r"場\s*地\s*[:：]?")
    NEXT_INFO = re.compile(r"(?:名\s*額|講\s*師|名額剩|正取剩|報\s*名\s*期\s*間|場\s*次\s*介\s*紹)")
    FULL_RANGE = re.compile(
        r"(?P<d1>20\d{2}/\d{1,2}/\d{1,2})\s+"
        r"(?P<t1>\d{2}:\d{2})\s*[～~\-]\s*"
        r"(?P<d2>20\d{2}/\d{1,2}/\d{1,2})\s+"
        r"(?P<t2>\d{2}:\d{2})")
    HEADING_RANGE = re.compile(
        r"(?P<d>20\d{2}/\d{1,2}/\d{1,2})\s*"
        r"(?:[\(（]\s*[一二三四五六日天]\s*[\)）])?\s*"
        r"(?P<t1>\d{2}:?\d{2})\s*[～~\-]\s*(?P<t2>\d{2}:?\d{2})(?![/\d:])")
    DATEISH = re.compile(r"20\d{2}/\d{1,2}/\d{1,2}")


    def iso_time(s):
        if re.fullmatch(r"\d{4}",s):return s[:2]+":"+s[2:]
        if re.fullmatch(r"\d{2}:\d{2}",s):return s
        raise ValueError("INVALID_CLOCK")


    def date_pair(d1,t1,d2,t2):
        a=datetime.fromisoformat(d1.replace("/","-")+"T"+iso_time(t1))
        b=datetime.fromisoformat(d2.replace("/","-")+"T"+iso_time(t2))
        if b<a or (b-a).days>370:
            raise ValueError("TIME_REVERSED_OR_TOO_LONG")
        return {"start":a.isoformat(timespec="minutes"),"end":b.isoformat(timespec="minutes"),
                "timeZone":"Asia/Taipei"}


    def exact_one(values):
        """Require exactly one unique occurrence, not one arbitrary date from prose."""
        seen={(x["start"],x["end"]) for x in values}
        return values[0] if len(seen)==1 else None


    def occurrence(section):
        values=[]
        for m in FULL_RANGE.finditer(section):
            try:values.append(date_pair(m["d1"],m["t1"],m["d2"],m["t2"]))
            except ValueError:pass
        for m in HEADING_RANGE.finditer(section):
            try:values.append(date_pair(m["d"],m["t1"],m["d"],m["t2"]))
            except ValueError:pass
        return exact_one(values)


    def paragraphs(page):
        soup=BeautifulSoup(page,"html.parser")
        # NFKC normalizes fullwidth digits/whitespace while keeping content literal.
        return unicodedata.normalize("NFKC"," ".join(soup.stripped_strings))


    def parse_event(page,row):
        soup=BeautifulSoup(page,"html.parser")
        title=short_title(row["title"])
        exact=[normalize(x) for x in list(soup.stripped_strings)[:65]]
        if normalize(title) not in exact:
            return {"state":"HOLD_EVENT_TITLE_IDENTITY","sessions":[],"registrationWindows":[],
                    "eventDateStart":None,"eventDateEnd":None}
        whole=paragraphs(page)
        begin=SECTION_START.search(whole)
        if not begin:
            # No sessions: retain L4B date only if the role was a separate
            # uniquely actId-bound official listing PERIOD; it is not a session.
            return {"state":"NO_SESSION_SECTION","sessions":[],"registrationWindows":[],
                    "eventDateStart":None,"eventDateEnd":None}
        segment=whole[begin.end():]
        stop=INTRO_MARK.search(segment)
        if stop:segment=segment[:stop.start()]
        chunks=SESSION_MARK.split(segment)[1:]
        if len(chunks)>20:
            return {"state":"HOLD_SESSION_CAP","sessions":[],"registrationWindows":[]}
        sessions=[]
        registrations=[]
        warnings=[]
        for index,chunk in enumerate(chunks):
            mark=REG_MARK.search(chunk)
            header=chunk[:mark.start()] if mark else chunk
            # A bare '2026/10/16 ~ ...' after '報名期間' must never be used as EVENT.
            event=occurrence(header)
            if not event:
                warnings.append({"block":index+1,"reason":"EVENT_TIME_UNPROVEN"})
                continue
            # One session per explicit '場次:' block. No duplicate acts or borrowed dates.
            label=header[:240]
            if len(label)>180:label=label[:180]
            v=VENUE_MARK.search(chunk)
            venue=None
            if v:
                next_marker=NEXT_INFO.search(chunk,v.end())
                raw=chunk[v.end():next_marker.start() if next_marker else len(chunk)]
                raw=re.sub(r"\s+"," ",raw).strip()
                raw=re.sub(r"(?:名額剩|正取剩|名單|報名|登入).*$","",raw).strip()
                if 2<=len(raw)<=160:venue=raw
            entry={"ordinal":index+1,"title":label.strip(),"start":event["start"],
                   "end":event["end"],"timeZone":"Asia/Taipei",
                   "role":"OFFICIAL_EVENT_SESSION_TIME","venue":venue}
            if mark:
                # Registration window is captured separately and only after the
                # explicit label, in this SAME session block.
                regpart=chunk[mark.end():]
                matches=list(FULL_RANGE.finditer(regpart))
                rm=matches[0] if len(matches)==1 else None
                if rm:
                    try:
                        r=date_pair(rm["d1"],rm["t1"],rm["d2"],rm["t2"])
                        entry["registration"]={**r,"role":"OFFICIAL_REGISTRATION_WINDOW"}
                        registrations.append({**r,"sessionOrdinal":index+1,
                                              "role":"OFFICIAL_REGISTRATION_WINDOW"})
                    except ValueError:
                        warnings.append({"block":index+1,"reason":"REG_WINDOW_INVALID"})
            sessions.append(entry)
        # Extra date-like values in blocks lacking an event are not proof.
        if not sessions:
            return {"state":"HOLD_NO_OFFICIAL_EVENT_SESSION","sessions":[],
                    "registrationWindows":registrations,
                    "eventDateStart":None,"eventDateEnd":None,"warnings":warnings,
                    "sessionBlocks":len(chunks)}
        dates=sorted(x["start"][:10] for x in sessions)
        ends=sorted(x["end"][:10] for x in sessions)
        return {"state":"OFFICIAL_EVENT_SESSIONS_VERIFIED",
                "sessions":sessions,"registrationWindows":registrations,
                "eventDateStart":dates[0],"eventDateEnd":ends[-1],
                "eventTimeRole":"OFFICIAL_EVENT_SESSION_BOUNDS",
                "sessionBlocks":len(chunks),"warnings":warnings}
    return parse_event(page, {"title": title})


def _cksmh_role_fields(roles, card, sid, stamp, sha):
    """Explicit session/registration roles; never turn a list period into SHOW."""
    fields = {}
    sessions = roles.get("sessions", [])
    registrations = roles.get("registrationWindows", [])
    def evidence(value, role, reason):
        return _field(value, role if value is not None else "UNKNOWN", sid,
                      card["url"], stamp, sha, "REVIEW" if value is not None else "HOLD",
                      "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE" if value is not None else reason)
    # Partial blocks cannot prove complete occurrence bounds.
    complete = (roles["state"] == "OFFICIAL_EVENT_SESSIONS_VERIFIED"
                and len(sessions) == roles.get("sessionBlocks"))
    fields["sessions"] = evidence(sessions or None, "OFFICIAL_EVENT_SESSIONS",
                                  "SOURCE_CKSMH_SESSION_UNPROVEN_HOLD")
    fields["registration_windows"] = evidence(registrations or None,
        "OFFICIAL_REGISTRATION_WINDOWS", "SOURCE_CKSMH_REGISTRATION_UNPROVEN_HOLD")
    if complete:
        fields["show_start"] = evidence(min(x["start"] for x in sessions) + "+08:00",
                                        "EVENT_SHOW_START", "")
        venues = [x.get("venue") for x in sessions]
        if venues and all(venues) and len(set(venues)) == 1:
            fields["venue"] = evidence(venues[0], "EVENT_VENUE", "")
    return fields


def _owned_list(provider, body):
    if provider == "cksmh":
        return _cksmh_list(body)
    if provider == "twtc":
        return _twtc_list(body)
    soup = BeautifulSoup(body, "html.parser")
    found = {}
    for link in soup.select("a[href]"):
        parsed = _canonical_event_url(provider, link.get("href"))
        if parsed is None:
            continue
        sid, detail_url = parsed
        if provider == "kktix":
            name_node = link.select_one(".name")
        else:
            name_node = link.select_one("h3")
        # LIST card identity must not silently prefer a stale title
        # attribute over a conflicting rendered event heading. Both are
        # source-owned assertions and disagreement makes the ID untrusted.
        attribute_title = link.get("title")
        visible_title = (name_node.get_text(" ", strip=True)
                         if name_node else link.get_text(" ", strip=True))
        attribute_title = (" ".join(attribute_title.split())
                           if isinstance(attribute_title, str) else "")
        visible_title = " ".join(visible_title.split())
        if attribute_title and visible_title and attribute_title != visible_title:
            raise ValueError("SOURCE_LIST_CARD_TITLE_CONFLICT_HOLD")
        name = attribute_title or visible_title
        if not name or len(name) > 300:
            continue
        # Duplicate event IDs with conflicting titles must not override the
        # earlier source-owned identity.
        if sid in found and found[sid]["title"] != name:
            raise ValueError("SOURCE_LIST_DUPLICATE_IDENTITY_HOLD")
        # Keep the actual LIST edge distinct from canonical identity.
        link_url = urljoin("https://" + SOURCES[provider][0] + "/", link.get("href"))
        edges = set(found.get(sid, {}).get("source_link_urls", []))
        edges.add(link_url)
        found[sid] = {"id": sid, "title": name, "url": detail_url,
                      "source_link_urls": sorted(edges)}
    return found


def _field(value, role, sid, url, stamp, sha, decision, reason):
    return {"value": value, "role": role, "event_id": sid,
            "source_url": url, "observed_at": stamp,
            "source_body_sha256": sha, "decision": decision,
            "hold_reason": reason}



def _structured_event_fields(article, provider, sid, title, detail_url, stamp, sha):
    """Extract only unambiguous same-event JSON-LD startDate and venue as REVIEW.

    JSON-LD is untrusted archived HTML: no cross-event, timezone-naive,
    multiple Event, or incomplete venue inference is allowed.
    """
    # Keep each Event bound to its own JSON-LD document. An @id from a
    # different script is not evidence that the Event owns that Place.
    matches = []
    for node in article.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.string or node.get_text())
        except (ValueError, TypeError):
            continue
        # Archived schema.org pages commonly wrap Event nodes in @graph.
        # Inspect only the top-level graph (never arbitrary nested objects),
        # and require a single exact same-ID event before admitting fields.
        roots = data if isinstance(data, list) else [data]
        objects = []
        for root in roots:
            if not isinstance(root, dict):
                continue
            objects.append(root)
            graph = root.get("@graph")
            if isinstance(graph, list):
                objects.extend(node for node in graph if isinstance(node, dict))
        for obj in objects:
            kinds = obj.get("@type")
            if not (kinds == "Event" or
                    isinstance(kinds, list) and kinds.count("Event") == 1):
                continue
            parsed = _canonical_event_url(provider, obj.get("url"))
            if (parsed != (sid, detail_url)
                    or " ".join(str(obj.get("name", "")).split()) != title):
                continue
            matches.append((obj, objects))
    if len(matches) != 1:
        return {}
    obj, same_document_objects = matches[0]
    # A structurally invalid Event startDate invalidates this JSON-LD event
    # as a field-evidence source; do not retain a venue REVIEW from the same
    # malformed event while show_start is HOLD.
    start = obj.get("startDate")
    if not isinstance(start, str):
        return {}
    try:
        dt = datetime.fromisoformat(start)
    except ValueError:
        return {}
    if dt.utcoffset() is None:
        return {}
    fields = {"show_start": _field(
        start, "EVENT_SHOW_START", sid, detail_url, stamp, sha,
        "REVIEW", "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")}
    # JSON-LD may reference a Place by @id in the same local @graph.
    # Resolve only one exact graph-local Place; never dereference remote URLs
    # or infer a venue from a different event or an ambiguous graph node.
    location = obj.get("location")
    if isinstance(location, dict) and set(location) == {"@id"}:
        reference = location.get("@id")
        places = []
        if isinstance(reference, str) and reference:
            for candidate in same_document_objects:
                kinds = candidate.get("@type")
                is_place = (kinds == "Place" or
                            isinstance(kinds, list) and kinds.count("Place") == 1)
                if (candidate is not obj and candidate.get("@id") == reference
                        and is_place):
                    places.append(candidate)
        if len(places) == 1:
            location = places[0]
        else:
            location = None
    # A graph-local Place may advertise multiple schema.org types; apply
    # the same exact Place predicate used when resolving its @id.
    location_kinds = location.get("@type") if isinstance(location, dict) else None
    if isinstance(location, dict) and (
            location_kinds == "Place" or
            isinstance(location_kinds, list) and location_kinds.count("Place") == 1):
        name = location.get("name")
        if isinstance(name, str) and 0 < len(name.strip()) <= 200:
            fields["venue"] = _field(
                " ".join(name.split()), "EVENT_VENUE", sid, detail_url,
                stamp, sha, "REVIEW", "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")
    return fields


def _detail_title_from_jsonld(article, provider, sid, title, detail_url):
    """Use a unique same-ID JSON-LD Event as title identity when H1 is absent.

    This is an offline identity fallback, not a FIELD acceptance or a network
    lookup. Ambiguous or conflicting assertions remain HOLD.
    """
    matches = 0
    for script in article.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        roots = data if isinstance(data, list) else [data]
        for root in roots:
            if not isinstance(root, dict):
                continue
            objects = [root]
            if isinstance(root.get("@graph"), list):
                objects.extend(item for item in root["@graph"] if isinstance(item, dict))
            for obj in objects:
                kinds = obj.get("@type")
                if not (kinds == "Event" or
                        isinstance(kinds, list) and kinds.count("Event") == 1):
                    continue
                if _canonical_event_url(provider, obj.get("url")) != (sid, detail_url):
                    continue
                name = obj.get("name")
                if not isinstance(name, str) or " ".join(name.split()) != title:
                    return False
                matches += 1
    return matches == 1


def _sealed_list_union(provider, entries, fixture_root):
    """Union verified LIST observations without claiming provider completeness.

    Per-card page lineage is retained so a DETAIL receipt cannot borrow a
    discovery link from a different page while attributing the first page SHA.
    """
    cards, pages, failures, seen_urls = {}, [], {}, set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {"list_file", "list_receipt"}:
            raise ValueError("SOURCE_PARTITION_SCHEMA_HOLD")
        try:
            url = _list_url(provider, entry["list_receipt"])
            if url in seen_urls:
                raise ValueError("SOURCE_PARTITION_DUPLICATE_URL_HOLD")
            seen_urls.add(url)
            raw = _read_fixture(fixture_root, entry["list_file"])
            stamp = _receipt(raw, entry["list_receipt"], url)
            found = _owned_list(provider, raw)
        except (ValueError, OSError) as exc:
            if str(exc) == "SOURCE_PARTITION_DUPLICATE_URL_HOLD":
                raise
            failures[str(index)] = str(exc)
            continue
        if not found:
            failures[str(index)] = "SOURCE_EMPTY_LIST_HOLD"
            continue
        digest = hashlib.sha256(raw).hexdigest()
        pages.append({"list_url": url, "list_observed_at": stamp,
                      "list_body_sha256": digest,
                      "event_ids": sorted(found)})
        for sid, card in found.items():
            if sid in cards and cards[sid]["title"] != card["title"]:
                raise ValueError("SOURCE_LIST_DUPLICATE_IDENTITY_HOLD")
            target = cards.setdefault(sid, {**card, "list_observations": []})
            target["source_link_urls"] = sorted(set(target["source_link_urls"])
                                                 | set(card["source_link_urls"]))
            target["list_observations"].append({
                "list_url": url, "list_observed_at": stamp,
                "list_body_sha256": digest, "list_link_urls": card["source_link_urls"],
            })
    return cards, pages, failures


def replay_offline_sources(manifest, fixture_root):
    """Replay any nonempty subset of registered providers without network or publication."""
    if (not isinstance(manifest, dict) or set(manifest) != {"mode", "sources"}
            or manifest["mode"] != "SEALED_OFFLINE_REPLAY_ONLY"
            or not isinstance(manifest["sources"], dict)
            or not manifest["sources"]
            or not set(manifest["sources"]).issubset(SOURCES)):
        raise ValueError("SOURCE_DUAL_ADAPTER_MANIFEST_HOLD")
    rows, holds, states, listed = {}, {}, {}, {provider: [] for provider in SOURCES}
    partition_inventory = {}
    twtc_list_body_sha256 = None
    cksmh_list_body_sha256 = None
    for provider in SOURCES:
        if provider not in manifest["sources"]:
            # Not scheduled is not an empty or failed official LIST.
            # Keep prior sibling snapshots intact without claiming observation.
            states[provider] = "NOT_ATTEMPTED"
            continue
        entry = manifest["sources"][provider]
        if (not isinstance(entry, dict)
                or set(entry) not in ({"list_file", "list_receipt", "details"},
                                      {"lists", "details"})
                or not isinstance(entry["details"], dict)
                or len(entry["details"]) > 20):
            raise ValueError("SOURCE_ADAPTER_INPUT_SCHEMA_HOLD")
        multi = "lists" in entry
        if multi and (provider != "accupass" or not isinstance(entry["lists"], list)
                      or not entry["lists"] or len(entry["lists"]) > 100):
            raise ValueError("SOURCE_PARTITION_SCHEMA_HOLD")
        # Legacy whole-source manifests remain compatible. Regional URL inputs
        # and explicit multi-LIST manifests never imply full provider coverage.
        try:
            if multi:
                cards, pages, failures = _sealed_list_union(
                    provider, entry["lists"], fixture_root)
                partial = True
            else:
                list_url = _list_url(provider, entry["list_receipt"])
                raw = _read_fixture(fixture_root, entry["list_file"])
                list_stamp = _receipt(raw, entry["list_receipt"], list_url)
                cards = _owned_list(provider, raw)
                partial = provider in ("twtc", "cksmh") or (provider == "accupass" and bool(urlsplit(list_url).query))
                digest = hashlib.sha256(raw).hexdigest()
                if provider == "twtc":
                    twtc_list_body_sha256 = digest
                if provider == "cksmh":
                    cksmh_list_body_sha256 = digest
                pages = [{"list_url": list_url, "list_observed_at": list_stamp,
                          "list_body_sha256": digest, "event_ids": sorted(cards)}]
                failures = {}
                for card in cards.values():
                    card["list_observations"] = [{
                        "list_url": list_url, "list_observed_at": list_stamp,
                        "list_body_sha256": digest,
                        "list_link_urls": card["source_link_urls"],
                    }]
        except (ValueError, OSError) as exc:
            holds[provider] = str(exc)
            states[provider] = "HOLD_LIST"
            continue
        if partial:
            partition_inventory[provider] = {
                "coverage": "PARTIAL_NOT_PROVIDER_COMPLETE",
                "pages": pages, "failed_pages": failures,
                "event_ids": sorted(cards),
                "detail_backlog": sorted(set(cards) - set(entry["details"])),
                "detail_attempt_ids": sorted(entry["details"]),
            }
        if not cards:
            holds[provider] = "SOURCE_EMPTY_LIST_HOLD"
            states[provider] = "HOLD_EMPTY_LIST"
            continue
        states[provider] = "REVIEW_PARTITION_ONLY" if partial else "REVIEW_IDENTITY_ONLY"
        # A DETAIL HOLD may preserve an existing identity only if the latest
        # verified LIST still explicitly contains its provider-owned ID.
        listed[provider] = [provider + ":" + sid for sid in sorted(cards)]
        for sid in entry["details"]:
            if sid not in cards:
                raise ValueError("SOURCE_DETAIL_ID_NOT_IN_LIST_HOLD")
        for sid, card in cards.items():
            identity = provider + ":" + sid
            record = entry["details"].get(sid)
            if record is None:
                holds[identity] = "SOURCE_DETAIL_NOT_PROVIDED_HOLD"
                continue
            if (not isinstance(record, dict)
                    or set(record) != {"detail_file", "receipt"}):
                raise ValueError("SOURCE_DETAIL_SCHEMA_HOLD")
            try:
                detail = _read_fixture(fixture_root, record["detail_file"])
                # Bind bytes to their original observed URL, not a rewritten
                # canonical URL. A canonical fetch is also a valid LIST edge.
                receipt = record["receipt"]
                observed_url = receipt.get("source_url") if isinstance(receipt, dict) else None
                if (observed_url not in [card["url"], *card["source_link_urls"]]
                        or _canonical_event_url(provider, observed_url) != (sid, card["url"])):
                    raise ValueError("SOURCE_RECEIPT_PROVENANCE_HOLD")
                stamp = _receipt(detail, receipt, observed_url)
                # Choose the actual page bearing the observed edge; a
                # canonical URL may use any verified page containing this ID.
                page_evidence = next(
                    page for page in card["list_observations"]
                    if observed_url == card["url"] or observed_url in page["list_link_urls"])
                article = BeautifulSoup(detail, "html.parser")
                if provider == "cksmh":
                    roles = _cksmh_semantic_roles(detail, card["title"])
                    if roles["state"] == "HOLD_EVENT_TITLE_IDENTITY":
                        raise ValueError("SOURCE_LIST_DETAIL_TITLE_PARITY_HOLD")
                    actual = card["title"]
                else:
                    # TWTC L4-A uses exact H1/H2/H3 title parity (not page-wide text).
                    if provider == "twtc":
                        heads = [node for node in article.select("h1,h2,h3")
                                 if " ".join(node.get_text(" ", strip=True).split()) == card["title"]]
                        if len(heads) != 1:
                            raise ValueError("SOURCE_LIST_DETAIL_TITLE_PARITY_HOLD")
                    else:
                        heads = [node for node in article.select("h1")
                                 if node.get_text(" ", strip=True)]
                    if len(heads) > 1:
                        raise ValueError("SOURCE_DETAIL_TITLE_AMBIGUOUS_HOLD")
                    if heads:
                        actual = " ".join(heads[0].get_text(" ", strip=True).split())
                        if actual != card["title"]:
                            raise ValueError("SOURCE_LIST_DETAIL_TITLE_PARITY_HOLD")
                    else:
                        # Some archived event pages render the visible title via
                        # client JS. Only a unique same-ID Event assertion may
                        # supply offline identity; never trust arbitrary metadata.
                        if not _detail_title_from_jsonld(
                                article, provider, sid, card["title"], card["url"]):
                            raise ValueError("SOURCE_DETAIL_TITLE_AMBIGUOUS_HOLD")
                        actual = card["title"]
            except (ValueError, OSError) as exc:
                holds[identity] = str(exc)
                continue
            sha = hashlib.sha256(detail).hexdigest()
            fields = {"title": _field(
                actual, "EVENT_TITLE", sid, card["url"], stamp, sha,
                "REVIEW", "SOURCE_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE")}
            for name in ("date", "show_start", "price", "venue", "image"):
                fields[name] = _field(
                    None, "UNKNOWN", sid, card["url"], stamp, sha,
                    "HOLD", "SOURCE_FIELD_ROLE_NOT_VERIFIED")
            if provider == "twtc":
                fields.update(_twtc_period_fields(article, card, sid, stamp, sha))
            elif provider == "cksmh":
                fields.update(_cksmh_role_fields(roles, card, sid, stamp, sha))
            else:
                fields.update(_structured_event_fields(article, provider, sid, actual, card["url"], stamp, sha))
            rows[identity] = {
                "identity": identity, "source_namespace": provider,
                "event_id": sid, "detail_source_url": card["url"],
                "archive_evidence_current": False,
                "source_evidence": {
                    **page_evidence,
                    "detail_observed_url": observed_url,
                },
                "fields": fields, "decision": "REVIEW_ONLY_NO_FIELD_ACCEPTANCE",
            }
    for provider, inventory in partition_inventory.items():
        inventory["detail_backlog"] = [
            sid for sid in inventory["event_ids"] if provider + ":" + sid not in rows]
    return {
        "kind": "MULTI_SOURCE_OFFLINE_FIELD_EVIDENCE_V1",
        "scope": "SEALED_OFFLINE_REPLAY_ONLY",
        "records": rows, "holds": holds, "source_states": states,
        "listed_identities": listed,
        "counts": {"review_identities": len(rows), "sources": len(manifest["sources"])},
        "partition_inventory": partition_inventory,
        **({"twtc_list_body_sha256": twtc_list_body_sha256} if twtc_list_body_sha256 else {}),
        **({"cksmh_list_body_sha256": cksmh_list_body_sha256} if cksmh_list_body_sha256 else {}),
        "new_official_get": 0, "accepted_fields": 0, "published": 0,
        "release_state": "HARD_HOLD_NO_PUBLICATION",
    }


# Shared Candidate/Core integration: the existing provenance validator is reused
# rather than introducing a second, weaker field admission contract.
def _validate_tpac_archive_candidate(row):
    """TPAC historical archive authority, distinct from current LIVE evidence."""
    ev = row.get("tpac_archive_evidence")
    catalog, sid = row.get("source_namespace"), row.get("event_id")
    if (catalog not in ("program", "event") or not isinstance(sid, str)
            or not re.fullmatch(r"[1-9][0-9]{0,9}", sid)
            or row.get("identity") != "tpac:" + catalog + ":" + sid
            or row.get("detail_source_url") != "https://tpac.org.taipei/" + catalog + "/" + sid
            or row.get("source_current") is not False
            or not isinstance(ev, dict)
            or set(ev) != {"inventory_sha256", "list_source_url", "list_body_sha256",
                          "archive_detail_current"}
            or ev["list_source_url"] != "https://tpac.org.taipei/" + catalog
            or type(ev["archive_detail_current"]) is not bool
            or any(not isinstance(ev[k], str) or not re.fullmatch(r"[0-9a-f]{64}", ev[k])
                   for k in ("inventory_sha256", "list_body_sha256"))
            or "source_evidence" in row):
        raise ValueError("SOURCE_TPAC_ARCHIVE_AUTHORITY_HOLD")
    fields, held = row.get("fields"), row.get("held_fields")
    allowed = {"title": {"EVENT_TITLE"}, "show_start": {"EVENT_SHOW_START"},
               "show_count": {"SOURCE_SHOW_COUNT"},
               "show_times": {"SOURCE_SHOW_STARTS"},
               "open_hours": {"OPEN_HOURS"},
               "activity_period": {"ACTIVITY_PERIOD", "EXHIBITION_PERIOD"},
               "venue": {"EVENT_VENUE_SPACE"},
               "price": {"EVENT_ADVERTISED_PRICE_RANGE_NTD", "EVENT_GENERAL_ADMISSION_PRICE_RANGE"}}
    if (not isinstance(fields, dict) or not isinstance(held, dict)
            or set(fields) & set(held)
            or set(fields) | set(held) not in ({"title", "date", "show_start", "show_count",
                                          "activity_period", "price", "venue", "description", "image"},
                                         {"title", "date", "show_start", "show_count", "show_times",
                                          "activity_period", "price", "venue", "description", "image"},
                                         {"title", "date", "show_start", "show_count", "show_times",
                                          "activity_period", "price", "venue", "description", "image", "open_hours"})
            or (bool(fields) != ev["archive_detail_current"])
            or (fields and "title" not in fields)):
        raise ValueError("SOURCE_TPAC_ARCHIVE_FIELD_HOLD")
    from scripts.p30_tpac_multi_event_refresh import (_valid_archived_venue_price,
                                                     _validate_archived_show_times,
                                                     _validate_archived_open_hours)
    _validate_archived_show_times(fields)
    _validate_archived_open_hours(fields, catalog)
    for name, field in fields.items():
        if (not isinstance(field, dict) or field.get("role") not in allowed.get(name, set())
                or field.get("value") is None
                or field.get("event_id") != sid
                or field.get("source_url") != row["detail_source_url"]
                or field.get("decision") != "REVIEW_ONLY_NOT_ACCEPTED"
                or field.get("hold_reason") != "ARCHIVED_FIELD_REQUIRES_INDEPENDENT_ACCEPTANCE"
                or not isinstance(field.get("source_body_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", field["source_body_sha256"])):
            raise ValueError("SOURCE_TPAC_ARCHIVE_FIELD_HOLD")
        if name in ("venue", "price") and not _valid_archived_venue_price(
                name, field["role"], field["value"], catalog):
            raise ValueError("SOURCE_TPAC_ARCHIVE_FIELD_HOLD")
        try:
            if datetime.fromisoformat(field["observed_at"]).utcoffset() is None:
                raise ValueError("naive")
        except (TypeError, ValueError, KeyError):
            raise ValueError("SOURCE_TPAC_ARCHIVE_FIELD_HOLD") from None
    for field in held.values():
        if (not isinstance(field, dict) or field.get("role") != "UNKNOWN"
                or field.get("decision") != "HOLD" or field.get("value") is not None):
            raise ValueError("SOURCE_TPAC_ARCHIVE_FIELD_HOLD")


def _tpac_archive_rows(repo_root, expected_inventory_sha):
    """Import only an exact existing archive inventory via the established parser/Core."""
    from scripts.p30_tpac_multi_event_refresh import (
        load_detail_inventory, build_archived_field_review_export,
        build_archived_field_candidate_delta, _validate_archived_candidate_snapshot_row)
    if (not isinstance(expected_inventory_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_inventory_sha)):
        raise ValueError("SOURCE_TPAC_ARCHIVE_EXPECTED_SHA_HOLD")
    archive_root = Path(repo_root).resolve() / "_isolated_archive_replay"
    if any(p.is_symlink() for p in (archive_root, archive_root / "_isolated_review",
                                    archive_root / "_isolated_review" / "tpac")):
        raise ValueError("SOURCE_TPAC_ARCHIVE_PATH_HOLD")
    inventory, actual = load_detail_inventory(archive_root)
    if actual != expected_inventory_sha or not inventory["items"]:
        raise ValueError("SOURCE_TPAC_ARCHIVE_INVENTORY_CAS_HOLD")
    ledger = build_archived_field_review_export(inventory, actual)
    delta = build_archived_field_candidate_delta(dict(ledger, records={}), ledger)
    rows = delta["candidates"]
    for identity, row in rows.items():
        original = ledger["records"][identity]
        # Current within the historical archive is NOT current official HTTP.
        row["source_current"] = False
        row["tpac_archive_evidence"] = {
            "inventory_sha256": actual,
            "list_source_url": original["list_source_url"],
            "list_body_sha256": original["list_body_sha256"],
            "archive_detail_current": original["archive_evidence_current"],
        }
        _validate_archived_candidate_snapshot_row(identity, row, "SOURCE_TPAC_ARCHIVE_CORE_HOLD")
        _validate_tpac_archive_candidate(row)
    return rows


def _validate_source_evidence(row):
    """Validate new URL lineage while retaining legacy sealed snapshots."""
    if row.get("source_namespace") in ("program", "event") or "tpac_archive_evidence" in row:
        _validate_tpac_archive_candidate(row)
        return
    if "source_evidence" not in row:
        return
    evidence = row["source_evidence"]
    provider, canonical = row["source_namespace"], row["detail_source_url"]
    expected = (row["event_id"], canonical)
    if (not isinstance(evidence, dict)
            or set(evidence) != {"list_url", "list_observed_at", "list_body_sha256",
                                 "list_link_urls", "detail_observed_url"}
            or not isinstance(evidence["list_body_sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", evidence["list_body_sha256"]) is None
            or not isinstance(evidence["list_link_urls"], list)
            or not evidence["list_link_urls"]
            or any(not isinstance(url, str) or not url.startswith("https://")
                   or _canonical_event_url(provider, url) != expected
                   for url in evidence["list_link_urls"])
            or evidence["detail_observed_url"] not in [canonical, *evidence["list_link_urls"]]
            or _canonical_event_url(provider, evidence["detail_observed_url"]) != expected):
        raise ValueError("SOURCE_CANDIDATE_SOURCE_EVIDENCE_HOLD")
    _list_url(provider, {"source_url": evidence["list_url"]})
    try:
        stamp = datetime.fromisoformat(evidence["list_observed_at"])
        if stamp.utcoffset() is None:
            raise ValueError("naive")
    except (ValueError, TypeError):
        raise ValueError("SOURCE_CANDIDATE_SOURCE_EVIDENCE_HOLD") from None


def _candidate_rows(report):
    from scripts.p30_tpac_multi_event_refresh import _validate_archived_candidate_snapshot_row
    if (not isinstance(report, dict)
            or report.get("kind") != "MULTI_SOURCE_OFFLINE_FIELD_EVIDENCE_V1"
            or report.get("scope") != "SEALED_OFFLINE_REPLAY_ONLY"
            or report.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
            or report.get("new_official_get") != 0
            or report.get("accepted_fields") != 0 or report.get("published") != 0
            or not isinstance(report.get("records"), dict)
            or not isinstance(report.get("holds"), dict)
            or not isinstance(report.get("source_states"), dict)
            or set(report["source_states"]) != set(SOURCES)
            or any(state not in ("REVIEW_IDENTITY_ONLY", "REVIEW_PARTITION_ONLY", "HOLD_LIST",
                                 "HOLD_EMPTY_LIST", "NOT_ATTEMPTED")
                   for state in report["source_states"].values())
            or not isinstance(report.get("listed_identities"), dict)
            or set(report["listed_identities"]) != set(SOURCES)
            or any(not isinstance(report["listed_identities"][provider], list)
                   or len(set(report["listed_identities"][provider])) !=
                       len(report["listed_identities"][provider])
                   or any(not isinstance(identity, str)
                          or not identity.startswith(provider + ":")
                          or not IDENTIFIER.fullmatch(identity[len(provider) + 1:])
                          for identity in report["listed_identities"][provider])
                   for provider in SOURCES)
            or any(report["source_states"][provider] not in ("REVIEW_IDENTITY_ONLY", "REVIEW_PARTITION_ONLY")
                   and report["listed_identities"][provider]
                   for provider in SOURCES)):
        raise ValueError("SOURCE_CANDIDATE_AUTHORITY_HOLD")
    rows = {}
    for identity, record in sorted(report["records"].items()):
        if (not isinstance(record, dict)
                or identity != record.get("identity")
                or record.get("source_namespace") not in SOURCES
                or identity != record["source_namespace"] + ":" + str(record.get("event_id"))
                or record.get("archive_evidence_current") is not False
                or record.get("decision") != "REVIEW_ONLY_NO_FIELD_ACCEPTANCE"
                or not isinstance(record.get("fields"), dict)):
            raise ValueError("SOURCE_CANDIDATE_IDENTITY_HOLD")
        provider = record["source_namespace"]
        if (report["source_states"][provider] not in ("REVIEW_IDENTITY_ONLY", "REVIEW_PARTITION_ONLY")
                or identity not in report["listed_identities"][provider]
                or identity in report["holds"]):
            raise ValueError("SOURCE_CANDIDATE_IDENTITY_HOLD")
        url = _canonical_event_url(record["source_namespace"], record.get("detail_source_url"))
        if url is None or url[0] != record["event_id"] or url[1] != record["detail_source_url"]:
            raise ValueError("SOURCE_CANDIDATE_SOURCE_URL_HOLD")
        accepted, held = {}, {}
        for name, field in sorted(record["fields"].items()):
            if (not isinstance(field, dict) or field.get("event_id") != record["event_id"]
                    or field.get("source_url") != url[1]
                    or not isinstance(field.get("observed_at"), str)
                    or not isinstance(field.get("source_body_sha256"), str)
                    or re.fullmatch(r"[0-9a-f]{64}", field["source_body_sha256"]) is None
                    or not isinstance(field.get("hold_reason"), str)
                    or not field["hold_reason"]):
                raise ValueError("SOURCE_CANDIDATE_FIELD_PROVENANCE_HOLD")
            if field.get("decision") == "REVIEW" and field.get("value") is not None:
                accepted[name] = dict(field, decision="REVIEW_ONLY_NOT_ACCEPTED")
            elif field.get("decision") == "HOLD" and field.get("value") is None:
                held[name] = dict(field)
            else:
                raise ValueError("SOURCE_CANDIDATE_FIELD_AUTHORITY_HOLD")
        row = {"identity": identity, "source_namespace": record["source_namespace"],
               "event_id": record["event_id"], "detail_source_url": url[1],
               "fields": accepted, "held_fields": held, "source_current": False,
               "decision": "ISOLATED_REVIEW_CANDIDATE_ONLY"}
        # Keep observed source URL and canonical event identity separate
        # through CAS and restart, without promoting archive authority.
        if "source_evidence" in record:
            row["source_evidence"] = record["source_evidence"]
            _validate_source_evidence(row)
        _validate_archived_candidate_snapshot_row(identity, row, "SOURCE_CANDIDATE_CORE_HOLD")
        rows[identity] = row
    return rows


def _candidate_canonical(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _partition_page_index(pages, provider="accupass"):
    """Content-addressed page receipts, never a claim of full coverage."""
    if not isinstance(pages, list):
        raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
    index = {}
    for page in pages:
        if (not isinstance(page, dict)
                or set(page) != {"list_url", "list_observed_at", "list_body_sha256", "event_ids"}
                or not isinstance(page["list_body_sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", page["list_body_sha256"])
                or not isinstance(page["event_ids"], list)
                or not page["event_ids"]
                or any(not isinstance(sid, str) or not IDENTIFIER.fullmatch(sid)
                       for sid in page["event_ids"])
                or page["event_ids"] != sorted(set(page["event_ids"]))):
            raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
        _list_url(provider, {"source_url": page["list_url"]})
        try:
            if datetime.fromisoformat(page["list_observed_at"]).utcoffset() is None:
                raise ValueError("naive")
        except (ValueError, TypeError):
            raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD") from None
        key = hashlib.sha256(_candidate_canonical(page)).hexdigest()
        index[key] = page
    return index


def _partition_report_pages(report, provider="accupass"):
    inventories = report.get("partition_inventory", {})
    if not isinstance(inventories, dict) or set(inventories) - {"accupass", "twtc", "cksmh"}:
        raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
    item = inventories.get(provider)
    if item is None:
        if report["source_states"][provider] == "REVIEW_PARTITION_ONLY":
            raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
        return {}
    if (not isinstance(item, dict)
            or item.get("coverage") != "PARTIAL_NOT_PROVIDER_COMPLETE"
            or not isinstance(item.get("failed_pages"), dict)):
        raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
    # Empty or unreadable observations must never replace historical receipts.
    if report["source_states"][provider] != "REVIEW_PARTITION_ONLY":
        return {}
    pages = _partition_page_index(item.get("pages"), provider)
    ids = sorted({sid for page in pages.values() for sid in page["event_ids"]})
    if (not ids or item.get("event_ids") != ids
            or report["listed_identities"][provider] != [provider + ":" + sid for sid in ids]
            or item.get("detail_backlog") !=
                [sid for sid in ids if provider + ":" + sid not in report["records"]]):
        raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
    attempted = item.get("detail_attempt_ids")
    if (not isinstance(attempted, list)
            or any(not isinstance(sid, str) or sid not in ids for sid in attempted)
            or attempted != sorted(set(attempted)) or len(attempted) > 20):
        raise ValueError("SOURCE_PARTITION_ATTEMPT_SCHEMA_HOLD")
    expected = [sid for sid in ids if provider + ":" + sid in report["records"]
                or report["holds"].get(provider + ":" + sid)
                    != "SOURCE_DETAIL_NOT_PROVIDED_HOLD"]
    if attempted != expected:
        raise ValueError("SOURCE_PARTITION_ATTEMPT_SCHEMA_HOLD")
    return pages


def _page_binds_row(page, row):
    evidence = row.get("source_evidence", {})
    return (row.get("event_id") in page["event_ids"]
            and all(evidence.get(k) == page[k] for k in
                    ("list_url", "list_observed_at", "list_body_sha256")))


def _partition_ledger(pages, rows, attempts=None, provider="accupass"):
    """Persist all discovered IDs, page receipts and completion in one CAS."""
    ids = sorted({sid for page in pages.values() for sid in page["event_ids"]})
    items = {}
    for sid in ids:
        refs = sorted(key for key, page in pages.items() if sid in page["event_ids"])
        row = rows.get(provider + ":" + sid, {})
        title = row.get("fields", {}).get("title")
        complete = (isinstance(title, dict)
                    and title.get("decision") == "REVIEW_ONLY_NOT_ACCEPTED"
                    and any(_page_binds_row(pages[key], row) for key in refs))
        items[sid] = {
            "page_keys": refs,
            "status": "DETAIL_REVIEW_ONLY" if complete else "PENDING_DETAIL",
            "detail_body_sha256": title["source_body_sha256"] if complete else None,
        }
    ledger = {"coverage": "PARTIAL_NOT_PROVIDER_COMPLETE",
              "pages": pages, "items": items,
              "detail_backlog": [sid for sid, item in items.items()
                                 if item["status"] == "PENDING_DETAIL"]}
    # Legacy V1 snapshots (no attempt journal) remain readable/rollbackable.
    # New snapshots count only explicitly supplied DETAIL replay attempts.
    if attempts is not None:
        if not isinstance(attempts, dict) or set(attempts) - set(items):
            raise ValueError("SOURCE_PARTITION_ATTEMPT_SCHEMA_HOLD")
        for sid, attempt in attempts.items():
            if (not isinstance(attempt, dict)
                    or set(attempt) != {"count", "last_outcome"}
                    or type(attempt["count"]) is not int or attempt["count"] < 1
                    or attempt["last_outcome"] not in _PARTITION_ATTEMPT_OUTCOMES):
                raise ValueError("SOURCE_PARTITION_ATTEMPT_SCHEMA_HOLD")
        ledger["detail_attempts"] = attempts
        ledger["detail_backlog"].sort(key=lambda sid: (
            attempts.get(sid, {}).get("count", 0), sid))
    return ledger


_PARTITION_ATTEMPT_OUTCOMES = {
    "DETAIL_REVIEW_ONLY",
    "SOURCE_FIXTURE_IO_HOLD",
    "SOURCE_FIXTURE_PATH_HOLD",
    "SOURCE_RECEIPT_PROVENANCE_HOLD",
    "SOURCE_RECEIPT_TIME_HOLD",
    "SOURCE_DETAIL_TITLE_AMBIGUOUS_HOLD",
    "SOURCE_LIST_DETAIL_TITLE_PARITY_HOLD",
}


def _advance_partition_attempts(prior, report, incoming_pages, provider="accupass"):
    """Count committed offline attempts, not absent DETAIL or live requests."""
    attempts = dict(prior)
    if not incoming_pages:
        return attempts
    for sid in report["partition_inventory"][provider]["detail_attempt_ids"]:
        identity = provider + ":" + sid
        outcome = ("DETAIL_REVIEW_ONLY" if identity in report["records"]
                   else report["holds"].get(identity))
        if outcome not in _PARTITION_ATTEMPT_OUTCOMES:
            raise ValueError("SOURCE_PARTITION_ATTEMPT_SCHEMA_HOLD")
        attempts[sid] = {
            "count": attempts.get(sid, {}).get("count", 0) + 1,
            "last_outcome": outcome,
        }
    return attempts


def _partition_ledgers(snapshot):
    """Read legacy ACCUPASS flat ledger or source-isolated envelope."""
    if "partition_inventory" not in snapshot:
        return {}
    raw = snapshot["partition_inventory"]
    if not isinstance(raw, dict):
        raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
    if set(raw) == {"providers"}:
        ledgers = raw["providers"]
        if (not isinstance(ledgers, dict) or not ledgers
                or set(ledgers) - {"accupass", "twtc", "cksmh"}):
            raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
    else:
        ledgers = {"accupass": raw}
    for provider, ledger in ledgers.items():
        if not isinstance(ledger, dict) or not isinstance(ledger.get("pages"), dict):
            raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
        pages = _partition_page_index(list(ledger["pages"].values()), provider)
        if (not pages or pages != ledger["pages"]
                or _partition_ledger(pages, snapshot["candidates"],
                                     ledger.get("detail_attempts"), provider) != ledger):
            raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
    return ledgers


def _validate_partition_ledger(snapshot, provider="accupass"):
    return _partition_ledgers(snapshot).get(provider, {}).get("pages", {})


def select_partition_pending(snapshot, limit=20, provider="accupass"):
    """Least-attempted pending IDs per source; no cross-source ID collisions."""
    ledgers = _partition_ledgers(snapshot)
    if type(limit) is not int or not 0 <= limit <= 20:
        raise ValueError("SOURCE_PARTITION_SELECTION_LIMIT_HOLD")
    if provider not in ("accupass", "twtc", "cksmh"):
        raise ValueError("SOURCE_PARTITION_PROVIDER_HOLD")
    return ledgers.get(provider, {}).get("detail_backlog", [])[:limit]


def commit_offline_candidate_lkg(report, root, expected_sha=None, *,
                                 tpac_archive_root=None, tpac_inventory_sha=None):
    """Non-destructive, locked CAS of provider-namespaced Candidate ledgers.

    Failed source replays retain their prior candidate, never replace it with
    an empty source result. Historical versions remain available for rollback.
    """
    import os
    import tempfile
    from scripts.p30_tpac_multi_event_refresh import (
        _isolated_writer_lock, _validate_archived_candidate_snapshot_row)
    if (isinstance(report, dict)
            and isinstance(report.get("source_states"), dict)
            and isinstance(report.get("listed_identities"), dict)
            and set(report["source_states"]) == set(report["listed_identities"])
                and set(report["source_states"]) in ({"kktix", "accupass"},
                                                     {"kktix", "accupass", "twtc"})):
        missing = set(SOURCES) - set(report["source_states"])
        report = dict(report, source_states={**report["source_states"],
                                            **{p: "NOT_ATTEMPTED" for p in missing}},
                      listed_identities={**report["listed_identities"],
                                         **{p: [] for p in missing}})
    rows = _candidate_rows(report)
    incoming_by_provider = {p: _partition_report_pages(report, p)
                            for p in ("accupass", "twtc", "cksmh")}
    incoming_pages = incoming_by_provider["accupass"]
    if (tpac_archive_root is None) != (tpac_inventory_sha is None):
        raise ValueError("SOURCE_TPAC_ARCHIVE_ARGUMENT_HOLD")
    tpac_rows = (_tpac_archive_rows(tpac_archive_root, tpac_inventory_sha)
                 if tpac_archive_root is not None else {})
    rows.update(tpac_rows)
    # A successful DETAIL must point at a verified page in this partition run.
    for identity, row in rows.items():
        source_pages = incoming_by_provider.get(row["source_namespace"], {})
        if (source_pages
                and not any(_page_binds_row(page, row) for page in source_pages.values())):
            raise ValueError("SOURCE_PARTITION_LEDGER_SCHEMA_HOLD")
    if expected_sha is not None and not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("SOURCE_CANDIDATE_EXPECTED_SHA_HOLD")
    root = Path(root).resolve()
    directory = root / "_isolated_multi_source_candidates"
    if directory.is_symlink():
        raise ValueError("SOURCE_CANDIDATE_SYMLINK_HOLD")
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "candidate_lkg.json"
    if target.is_symlink():
        raise ValueError("SOURCE_CANDIDATE_SYMLINK_HOLD")
    with _isolated_writer_lock(directory / ".candidate.lock", "SOURCE_CANDIDATE_WRITER_HOLD"):
        prior = target.read_bytes() if target.exists() else None
        actual = hashlib.sha256(prior).hexdigest() if prior is not None else None
        if actual != expected_sha:
            raise ValueError("SOURCE_CANDIDATE_CAS_HOLD")
        prior_pages, prior_ledgers = {}, {}
        if prior is not None:
            try:
                old = json.loads(prior)
                if (_candidate_canonical(old) != prior
                        or old.get("kind") != "MULTI_SOURCE_ISOLATED_CANDIDATE_LKG_V1"
                        or old.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
                        or old.get("accepted_fields") != 0 or old.get("published") != 0
                        or not isinstance(old.get("candidates"), dict)):
                    raise ValueError("SOURCE_CANDIDATE_PRIOR_CORRUPT_HOLD")
                prior_ledgers = _partition_ledgers(old)
                prior_pages = prior_ledgers.get("accupass", {}).get("pages", {})
                for identity, row in old["candidates"].items():
                    _validate_archived_candidate_snapshot_row(
                        identity, row, "SOURCE_CANDIDATE_PRIOR_FIELD_HOLD")
                    _validate_source_evidence(row)
                    provider = row["source_namespace"]
                    if identity in rows:
                        if any(row.get(k) != rows[identity].get(k) for k in
                               ("source_namespace", "event_id", "detail_source_url")):
                            raise ValueError("SOURCE_CANDIDATE_IDENTITY_SWAP_HOLD")
                    elif provider in ("program", "event"):
                        # A different provider's replay must not erase TPAC.
                        # An explicit TPAC import may not drop an existing ID.
                        if tpac_rows:
                            raise ValueError("SOURCE_TPAC_ARCHIVE_DESTRUCTIVE_REMOVAL_HOLD")
                        rows[identity] = row
                    elif (report["source_states"][provider] == "REVIEW_PARTITION_ONLY"
                          and identity not in report["listed_identities"][provider]):
                        # An unobserved identity is not a removed event. Prior
                        # archive authority remains historical, never current.
                        rows[identity] = row
                    elif (provider in ("twtc", "cksmh")
                          and identity in report["listed_identities"][provider]
                          and report["holds"].get(identity) == "SOURCE_DETAIL_NOT_PROVIDED_HOLD"
                          and any(_page_binds_row(page, row)
                                  for page in incoming_by_provider[provider].values())):
                        # Same sealed list, subsequent bounded DETAIL batch:
                        # absence of a supplied body is not a new failure.
                        rows[identity] = row
                    elif report["source_states"][provider] in (
                            "REVIEW_IDENTITY_ONLY", "REVIEW_PARTITION_ONLY"):
                        # A healthy LIST may include a known ID whose DETAIL
                        # is absent/invalid. It is not a deletion: retain the
                        # identity and immutable historical provenance, but
                        # withdraw *all* old REVIEW values from current use.
                        # A missing ID from the verified LIST still fails closed.
                        held_reason = report["holds"].get(identity)
                        # Replaying the identical archived LIST to drain a
                        # later batch is not a fresh failed DETAIL observation.
                        # Keep an already reviewed row only for known receipts.
                        if (provider == "accupass" and incoming_pages
                                and held_reason == "SOURCE_DETAIL_NOT_PROVIDED_HOLD"
                                and row.get("fields", {}).get("title")
                                and any(_page_binds_row(page, row) for page in prior_pages.values())
                                and {key for key, page in incoming_pages.items()
                                     if row["event_id"] in page["event_ids"]}
                                and all(key in prior_pages for key, page in incoming_pages.items()
                                        if row["event_id"] in page["event_ids"])):
                            rows[identity] = row
                            continue
                        allowed = {
                            "SOURCE_DETAIL_NOT_PROVIDED_HOLD",
                            "SOURCE_FIXTURE_IO_HOLD",
                            "SOURCE_FIXTURE_PATH_HOLD",
                            "SOURCE_RECEIPT_PROVENANCE_HOLD",
                            "SOURCE_RECEIPT_TIME_HOLD",
                            "SOURCE_DETAIL_TITLE_AMBIGUOUS_HOLD",
                            "SOURCE_LIST_DETAIL_TITLE_PARITY_HOLD",
                        }
                        if (identity not in report["listed_identities"][provider]
                                or held_reason not in allowed):
                            raise ValueError("SOURCE_CANDIDATE_DESTRUCTIVE_REMOVAL_HOLD")
                        pending = dict(row)
                        pending["fields"] = {}
                        pending["held_fields"] = {
                            name: {**field, "value": None,
                                   "role": "UNKNOWN", "decision": "HOLD",
                                   "hold_reason": held_reason}
                            for name, field in {**row["held_fields"], **row["fields"]}.items()
                        }
                        pending["detail_replay_hold_reason"] = held_reason
                        _validate_archived_candidate_snapshot_row(
                            identity, pending, "SOURCE_CANDIDATE_DETAIL_HOLD")
                        rows[identity] = pending
                    else:
                        rows[identity] = row
            except (TypeError, UnicodeError, json.JSONDecodeError) as exc:
                raise ValueError("SOURCE_CANDIDATE_PRIOR_CORRUPT_HOLD") from exc
        ledgers = {}
        for provider, new_pages in incoming_by_provider.items():
            old_ledger = prior_ledgers.get(provider, {})
            merged = {**old_ledger.get("pages", {}), **new_pages}
            if merged:
                attempts = _advance_partition_attempts(
                    old_ledger.get("detail_attempts", {}), report, new_pages, provider)
                ledgers[provider] = _partition_ledger(merged, rows, attempts, provider)
        if not rows and not ledgers:
            raise ValueError("SOURCE_CANDIDATE_EMPTY_HOLD")
        snapshot = {"kind": "MULTI_SOURCE_ISOLATED_CANDIDATE_LKG_V1",
                    "candidates": rows, "release_state": "HARD_HOLD_NO_PUBLICATION",
                    "accepted_fields": 0, "published": 0}
        if ledgers:
            # Preserve the legacy ACCUPASS-only wire format.
            snapshot["partition_inventory"] = (ledgers["accupass"]
                if set(ledgers) == {"accupass"} else {"providers": ledgers})
        payload = _candidate_canonical(snapshot)
        digest = hashlib.sha256(payload).hexdigest()
        versions = directory / "versions"
        if versions.is_symlink():
            raise ValueError("SOURCE_CANDIDATE_SYMLINK_HOLD")
        versions.mkdir(exist_ok=True)
        # Keep immutable version files for an explicit CAS-controlled rollback.
        version = versions / (digest + ".json")
        if version.is_symlink():
            raise ValueError("SOURCE_CANDIDATE_SYMLINK_HOLD")
        if version.exists():
            if version.read_bytes() != payload:
                raise ValueError("SOURCE_CANDIDATE_VERSION_COLLISION_HOLD")
        else:
            with version.open("xb") as out:
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".candidate-",
                                             delete=False) as out:
                temp = Path(out.name)
                out.write(payload)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, target)
            temp = None
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        return {"sha256": digest, "events": len(rows),
                "decision": "ISOLATED_MULTI_SOURCE_CANDIDATE_COMMITTED_NOT_FORMAL",
                "accepted_fields": 0, "published": 0,
                **({"pending_details": len(ledgers.get("accupass", {}).get("detail_backlog", [])),
                    "next_detail_ids": select_partition_pending(snapshot),
                    **({"pending_by_provider": {p: len(l["detail_backlog"]) for p,l in ledgers.items()},
                        "next_by_provider": {p: select_partition_pending(snapshot, provider=p)
                                             for p in ledgers}}
                       if set(ledgers) - {"accupass"} else {})}
                   if ledgers else {})}


def load_offline_candidate_lkg(root, expected_sha):
    """Restart readback validates both canonical bytes and shared Core fields."""
    from scripts.p30_tpac_multi_event_refresh import _validate_archived_candidate_snapshot_row
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("SOURCE_CANDIDATE_READ_SHA_HOLD")
    directory = Path(root).resolve() / "_isolated_multi_source_candidates"
    target = directory / "candidate_lkg.json"
    if directory.is_symlink() or target.is_symlink() or not target.is_file():
        raise ValueError("SOURCE_CANDIDATE_READ_PATH_HOLD")
    raw = target.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("SOURCE_CANDIDATE_READ_CAS_HOLD")
    try:
        snapshot = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("SOURCE_CANDIDATE_READ_SCHEMA_HOLD") from exc
    if (_candidate_canonical(snapshot) != raw
            or set(snapshot) not in ({"kind", "candidates", "release_state",
                                     "accepted_fields", "published"},
                                    {"kind", "candidates", "release_state",
                                     "accepted_fields", "published", "partition_inventory"})
            or snapshot["kind"] != "MULTI_SOURCE_ISOLATED_CANDIDATE_LKG_V1"
            or snapshot["release_state"] != "HARD_HOLD_NO_PUBLICATION"
            or snapshot["accepted_fields"] != 0 or snapshot["published"] != 0
            or not isinstance(snapshot["candidates"], dict)):
        raise ValueError("SOURCE_CANDIDATE_READ_SCHEMA_HOLD")
    for identity, row in snapshot["candidates"].items():
        _validate_archived_candidate_snapshot_row(identity, row, "SOURCE_CANDIDATE_READ_FIELD_HOLD")
        _validate_source_evidence(row)
    _validate_partition_ledger(snapshot)
    return snapshot


def rollback_offline_candidate_lkg(root, archived_sha, expected_current_sha):
    """Restore an archived version only after exact current-state CAS."""
    directory = Path(root).resolve() / "_isolated_multi_source_candidates"
    version = directory / "versions" / (archived_sha + ".json")
    if (not isinstance(archived_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", archived_sha)
            or directory.is_symlink() or version.is_symlink() or not version.is_file()):
        raise ValueError("SOURCE_CANDIDATE_ROLLBACK_VERSION_HOLD")
    raw = version.read_bytes()
    if hashlib.sha256(raw).hexdigest() != archived_sha:
        raise ValueError("SOURCE_CANDIDATE_ROLLBACK_HASH_HOLD")
    historical = json.loads(raw)
    # Reuse the normal admission path, without trusting historical filenames.
    report = {"kind": "MULTI_SOURCE_OFFLINE_FIELD_EVIDENCE_V1",
              "scope": "SEALED_OFFLINE_REPLAY_ONLY",
              "records": {}, "source_states": {p: "HOLD_LIST" for p in SOURCES},
              "new_official_get": 0, "accepted_fields": 0, "published": 0,
              "release_state": "HARD_HOLD_NO_PUBLICATION"}
    from scripts.p30_tpac_multi_event_refresh import _isolated_writer_lock
    import os
    import tempfile
    with _isolated_writer_lock(directory / ".candidate.lock", "SOURCE_CANDIDATE_WRITER_HOLD"):
        target = directory / "candidate_lkg.json"
        if target.is_symlink() or not target.is_file():
            raise ValueError("SOURCE_CANDIDATE_ROLLBACK_PATH_HOLD")
        current = target.read_bytes()
        if hashlib.sha256(current).hexdigest() != expected_current_sha:
            raise ValueError("SOURCE_CANDIDATE_ROLLBACK_CAS_HOLD")
        load_offline_candidate_lkg(root, expected_current_sha)
        if (_candidate_canonical(historical) != raw
                or historical.get("kind") != "MULTI_SOURCE_ISOLATED_CANDIDATE_LKG_V1"
                or historical.get("release_state") != "HARD_HOLD_NO_PUBLICATION"
                or historical.get("accepted_fields") != 0 or historical.get("published") != 0):
            raise ValueError("SOURCE_CANDIDATE_ROLLBACK_SCHEMA_HOLD")
        from scripts.p30_tpac_multi_event_refresh import _validate_archived_candidate_snapshot_row
        for identity, row in historical["candidates"].items():
            _validate_archived_candidate_snapshot_row(identity, row, "SOURCE_CANDIDATE_ROLLBACK_FIELD_HOLD")
            _validate_source_evidence(row)
        _validate_partition_ledger(historical)
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=directory, prefix=".rollback-", delete=False) as out:
                temp = Path(out.name)
                out.write(raw)
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, target)
            temp = None
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    return {"sha256": archived_sha, "decision": "ISOLATED_ROLLBACK_NOT_FORMAL"}

def build_partition_archive_batch(snapshot, archive_index, fixture_root, limit=20):
    """Resolve the next fair batch from existing, SHA-pinned offline bytes.

    The index is reusable across CAS versions; the caller must load the exact
    current snapshot. It is a locator, not a source authority or permission
    to fetch. Only page receipts already present in the ledger are admitted.
    """
    kinds = {"ACCUPASS_SEALED_ARCHIVE_INDEX_V1": "accupass",
             "TWTC_SEALED_ARCHIVE_INDEX_V1": "twtc",
             "CKSMH_SEALED_ARCHIVE_INDEX_V1": "cksmh"}
    provider = kinds.get(archive_index.get("kind")) if isinstance(archive_index, dict) else None
    if provider is None:
        raise ValueError("SOURCE_ARCHIVE_INDEX_SCHEMA_HOLD")
    selected = select_partition_pending(snapshot, limit, provider)
    if not selected:
        raise ValueError("SOURCE_ARCHIVE_NO_PENDING_HOLD")
    if (not isinstance(archive_index, dict)
            or set(archive_index) != {"kind", "lists", "details"}
            or not isinstance(archive_index["lists"], list)
            or not 0 < len(archive_index["lists"]) <= 100
            or not isinstance(archive_index["details"], dict)
            or any(not isinstance(sid, str) or not IDENTIFIER.fullmatch(sid)
                   for sid in archive_index["details"])):
        raise ValueError("SOURCE_ARCHIVE_INDEX_SCHEMA_HOLD")

    ledger = _partition_ledgers(snapshot)[provider]
    ledger_pages = ledger["pages"]
    indexed, seen_urls = {}, set()
    # Verify every supplied LIST against its real bytes, parsed IDs, and the
    # exact previously admitted page receipt. A filename alone proves nothing.
    for entry in archive_index["lists"]:
        if not isinstance(entry, dict) or set(entry) != {"list_file", "list_receipt"}:
            raise ValueError("SOURCE_ARCHIVE_INDEX_SCHEMA_HOLD")
        url = _list_url(provider, entry["list_receipt"])
        raw = _read_fixture(fixture_root, entry["list_file"])
        stamp = _receipt(raw, entry["list_receipt"], url)
        cards = _owned_list(provider, raw)
        page = {"list_url": url, "list_observed_at": stamp,
                "list_body_sha256": hashlib.sha256(raw).hexdigest(),
                "event_ids": sorted(cards)}
        key = hashlib.sha256(_candidate_canonical(page)).hexdigest()
        if key not in ledger_pages or ledger_pages[key] != page:
            raise ValueError("SOURCE_ARCHIVE_PAGE_NOT_IN_LEDGER_HOLD")
        # The existing replay contract permits one observation per LIST URL.
        # A conflicting archive version cannot be silently substituted.
        if url in seen_urls:
            raise ValueError("SOURCE_ARCHIVE_DUPLICATE_PAGE_URL_HOLD")
        seen_urls.add(url)
        indexed[key] = (entry, cards)

    lists, details, used = [], {}, set()
    for sid in selected:
        record = archive_index["details"].get(sid)
        if record is None:
            raise ValueError("SOURCE_ARCHIVE_DETAIL_MISSING_HOLD:" + sid)
        if not isinstance(record, dict) or set(record) != {"detail_file", "receipt"}:
            raise ValueError("SOURCE_ARCHIVE_INDEX_SCHEMA_HOLD")
        receipt = record["receipt"]
        url = receipt.get("source_url") if isinstance(receipt, dict) else None
        parsed = _canonical_event_url(provider, url)
        if parsed is None or parsed[0] != sid:
            raise ValueError("SOURCE_RECEIPT_PROVENANCE_HOLD")
        canonical = parsed[1]
        # Select only a real archived LIST edge bearing this event and observed
        # URL. Preserve the original tracked URL rather than inventing a link.
        matching = [key for key in ledger["items"][sid]["page_keys"]
                    if key in indexed and sid in indexed[key][1]
                    and canonical == indexed[key][1][sid]["url"]
                    and url in [canonical, *indexed[key][1][sid]["source_link_urls"]]]
        if not matching:
            raise ValueError("SOURCE_ARCHIVE_LIST_MISSING_HOLD:" + sid)
        key = matching[0]
        if key not in used:
            lists.append(indexed[key][0])
            used.add(key)
        raw = _read_fixture(fixture_root, record["detail_file"])
        _receipt(raw, receipt, url)
        details[sid] = record

    # Validate cross-page identity conflicts with the established union code.
    # No second event parser, no network, and no mutation during planning.
    if provider != "accupass":
        if len(lists) != 1:
            raise ValueError("SOURCE_ARCHIVE_BATCH_LIST_HOLD")
        return {"mode": "SEALED_OFFLINE_REPLAY_ONLY", "sources": {
            provider: {**lists[0], "details": details}}}
    cards, _, failures = _sealed_list_union(provider, lists, fixture_root)
    if failures or not set(selected).issubset(cards):
        raise ValueError("SOURCE_ARCHIVE_BATCH_LIST_HOLD")
    return {"mode": "SEALED_OFFLINE_REPLAY_ONLY", "sources": {
        provider: {"lists": lists, "details": details}}}


def project_tpac_archive_preview(root, expected_sha):
    """Read exact shared CAS and reuse the existing L7 PWA REVIEW normalizer.

    Only TPAC sealed, same-ID DETAIL rows are exported; other provider fixture
    siblings and pending LIST-only rows are intentionally excluded. No writes,
    new GETs, accepted fields, or availability assertion.
    """
    from scripts.p30_candidate_review_pipeline import build_candidate_dataset
    snapshot = load_offline_candidate_lkg(root, expected_sha)
    inputs, provenance = [], {}
    for identity, row in sorted(snapshot["candidates"].items()):
        if not identity.startswith("tpac:"):
            continue
        _validate_tpac_archive_candidate(row)
        if not row["tpac_archive_evidence"]["archive_detail_current"]:
            continue
        fields = row["fields"]
        title = fields["title"]
        url, stamp, sha = row["detail_source_url"], title["observed_at"], title["source_body_sha256"]
        if any(f["observed_at"] != stamp or f["source_body_sha256"] != sha
               for f in fields.values()):
            raise ValueError("TPAC_PREVIEW_MIXED_DETAIL_RECEIPT_HOLD")
        namespace, sid = row["source_namespace"], row["event_id"]
        raw = {"title": title["value"], "url": url,
               "platform": "臺北表演藝術中心", "type": "其他", "scraped_at": stamp,
               "_candidate": {"scope": "CANDIDATE_PREVIEW_ONLY",
                   "decision": "REVIEW_WITH_HOLD", "record_id": identity,
                   "platform_id": "tpac", "source_event_id": namespace + ":" + sid,
                   "source_class": "ARCHIVED_OFFLINE_REVIEW_ONLY",
                   "sources": [url], "hold_reasons": [
                       "HISTORICAL_ARCHIVE_NOT_CURRENT_OFFICIAL_DATA",
                       "INDEPENDENT_FIELD_ACCEPTANCE_REQUIRED",
                       "NOT_TICKET_AVAILABILITY"],
                   "field_evidence": {}, "published": False,
                   "golden_accepted": False, "formal_field_pass": False}}
        meta = raw["_candidate"]
        def display(key, value, role):
            raw[key] = value
            meta["field_evidence"][key] = {"value": value, "role": role,
                "source": url, "observed_at": stamp, "decision": "REVIEW"}
        period = fields.get("activity_period")
        show = fields.get("show_start")
        if period:
            display("date", " ～ ".join(period["value"]), "VENUE_EVENT_DATE")
        elif show:
            display("date", datetime.fromisoformat(show["value"]).strftime("%Y-%m-%d %H:%M"),
                    "EVENT_DATE")
        if "venue" in fields:
            value = fields["venue"]["value"]
            display("location", value if value.startswith(raw["platform"]) else
                    raw["platform"] + "／" + value, "EVENT_VENUE")
        else:
            meta["hold_reasons"].append("EVENT_VENUE_SPACE_NOT_PROVEN")
        if "price" in fields:
            receipt = fields["price"]
            low, high = receipt["value"]
            label = "一般票：" if receipt["role"] == "EVENT_GENERAL_ADMISSION_PRICE_RANGE" else "官網票價："
            display("price", label + (f"NT${low:,}" if low == high else f"NT${low:,}–{high:,}"),
                    "EVENT_ADMISSION_PRICE")
        else:
            meta["hold_reasons"].append("OFFICIAL_PRICE_NOT_PROVEN")
        inputs.append(raw)
        provenance[identity] = {"candidate_snapshot_sha256": expected_sha,
            "historical_only": True, "source_fields": fields,
            "held_fields": row["held_fields"]}
    if not inputs or len(inputs) > 500:
        raise ValueError("TPAC_PREVIEW_EMPTY_OR_CAP_HOLD")
    preview, report = build_candidate_dataset(inputs)
    if report["rejectedRows"] or len(preview) != len(inputs):
        raise ValueError("TPAC_PREVIEW_NORMALIZER_HOLD")
    # Retain source roles/SHA alongside the existing UI-compatible receipts.
    # Detail evidence is an allowlisted projection, never arbitrary HTML.
    for raw, normalized in zip(inputs, preview):
        meta = normalized["_candidate"]
        if any(normalized[key] != raw[key] for key in ("date", "location", "price") if key in raw):
            raise ValueError("TPAC_PREVIEW_FIELD_LOSS_HOLD")
        source = provenance[meta["record_id"]]
        meta["archive_provenance"] = source
        original = source["source_fields"]
        detail = []
        for key, label, role in (("show_start", "首場開始（歷史）", "EVENT_DATE"),
                                  ("activity_period", "活動期間（歷史）", "VENUE_EVENT_DATE"),
                                  ("venue", "官方場地（歷史）", "EVENT_VENUE"),
                                  ("price", "官網票價（歷史）", "VENUE_ADVERTISED_PRICE")):
            if key in original:
                value = original[key]["value"]
                if key == "price":
                    value = normalized["price"]
                elif key == "activity_period":
                    value = " ～ ".join(value)
                elif key == "show_start":
                    value = datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M")
                detail.append({"label": label, "role": role, "value": value,
                    "source": normalized["url"], "observed_at": original[key]["observed_at"],
                    "decision": "REVIEW"})
        # Existing PWA detail receipts allow <=500 chars and 16 blocks.
        # Chunk the complete list without changing UI or claiming ticket inventory.
        if "show_times" in original:
            times = original["show_times"]
            values = times["value"]
            for offset in range(0, len(values), 10):
                chunk = values[offset:offset+10]
                detail.append({"label": f"官方場次（歷史） {offset+1}–{offset+len(chunk)}／{len(values)}",
                    "role": "EVENT_DATE",
                    "value": "、".join(datetime.fromisoformat(v).strftime("%Y-%m-%d %H:%M") for v in chunk),
                    "source": normalized["url"], "observed_at": times["observed_at"],
                    "decision": "REVIEW"})
        if "open_hours" in original:
            hours = original["open_hours"]
            v = hours["value"]
            detail.append({"label": "展覽開放時間（歷史）", "role": "OPEN_HOURS",
                "value": f"每日 {v['start']}～翌日 {v['end']}（休展異動依官方公告）",
                "source": normalized["url"], "observed_at": hours["observed_at"],
                "decision": "REVIEW"})
            for notice in v["source_notices"]:
                detail.append({"label": "展覽時間例外（歷史公告）", "role": "OPEN_HOURS",
                    "value": notice, "source": normalized["url"],
                    "observed_at": hours["observed_at"], "decision": "REVIEW"})
        meta["detail_evidence"] = detail
    return preview


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline selected-source LIST+DETAIL; no GET/publish")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--manifest", type=Path)
    inputs.add_argument("--export-tpac-preview", action="store_true",
                        help="Read exact CAS and print historical TPAC PWA REVIEW array only")
    inputs.add_argument("--archive-index", type=Path,
                        help="Resolve next pending batch from sealed local archive")
    inputs.add_argument("--tpac-archive-root", type=Path,
                        help="Import existing TPAC archive inventory into shared isolated CAS")
    parser.add_argument("--tpac-inventory-sha",
                        help="Exact existing TPAC archive inventory SHA256")
    parser.add_argument("--batch-limit", type=int, default=20,
                        help="Archive batch size, 1-20")
    parser.add_argument("--fixture-root", type=Path)
    parser.add_argument("--candidate-root", type=Path,
                        help="Explicit isolated Candidate CAS destination; default is read-only")
    parser.add_argument("--expected-sha",
                        help="Current Candidate SHA for CAS; omit only for first creation")
    args = parser.parse_args(argv)
    if args.expected_sha is not None and args.candidate_root is None:
        parser.error("--expected-sha requires --candidate-root")
    if args.export_tpac_preview:
        if args.candidate_root is None or args.expected_sha is None or args.tpac_inventory_sha is not None:
            parser.error("--export-tpac-preview requires --candidate-root and --expected-sha only")
        print(json.dumps(project_tpac_archive_preview(args.candidate_root, args.expected_sha),
                         ensure_ascii=False, sort_keys=True))
        return 0
    if args.tpac_archive_root is not None:
        if args.candidate_root is None or args.tpac_inventory_sha is None:
            parser.error("--tpac-archive-root requires --candidate-root and --tpac-inventory-sha")
        report = {"kind": "MULTI_SOURCE_OFFLINE_FIELD_EVIDENCE_V1",
                  "scope": "SEALED_OFFLINE_REPLAY_ONLY",
                  "records": {}, "holds": {},
                  "source_states": {p: "NOT_ATTEMPTED" for p in SOURCES},
                  "listed_identities": {p: [] for p in SOURCES},
                  "new_official_get": 0, "accepted_fields": 0, "published": 0,
                  "release_state": "HARD_HOLD_NO_PUBLICATION"}
        result = commit_offline_candidate_lkg(
            report, args.candidate_root, args.expected_sha,
            tpac_archive_root=args.tpac_archive_root,
            tpac_inventory_sha=args.tpac_inventory_sha)
        snapshot = load_offline_candidate_lkg(args.candidate_root, result["sha256"])
        result["tpac_archive_identities"] = sum(
            key.startswith("tpac:") for key in snapshot["candidates"])
        print(json.dumps({"candidate_commit": result, "new_official_get": 0,
                          "accepted_fields": 0, "published": 0}, sort_keys=True))
        return 0
    if args.tpac_inventory_sha is not None:
        parser.error("--tpac-inventory-sha requires --tpac-archive-root")
    if args.fixture_root is None:
        parser.error("--fixture-root is required for manifest or archive index")
    if args.archive_index is not None:
        if args.candidate_root is None or args.expected_sha is None:
            parser.error("--archive-index requires --candidate-root and --expected-sha")
        if not 1 <= args.batch_limit <= 20:
            parser.error("--batch-limit must be 1-20")
        prior = load_offline_candidate_lkg(args.candidate_root, args.expected_sha)
        archive = json.loads(args.archive_index.read_text(encoding="utf-8"))
        data = build_partition_archive_batch(prior, archive, args.fixture_root,
                                             args.batch_limit)
    else:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = replay_offline_sources(data, args.fixture_root)
    if args.archive_index is not None:
        # Reuse the normal DETAIL parser and CAS path; ensure planning and
        # replay did not diverge before admitting any mutation.
        provider = next(iter(data["sources"]))
        intended = set(data["sources"][provider]["details"])
        inv = report["partition_inventory"].get(provider, {})
        if (report["source_states"][provider] != "REVIEW_PARTITION_ONLY"
                or set(inv.get("detail_attempt_ids", [])) != intended
                or inv.get("failed_pages")):
            raise ValueError("SOURCE_ARCHIVE_BATCH_REPLAY_HOLD")
        report["archive_batch"] = {"snapshot_sha256": args.expected_sha,
                                   "event_ids": sorted(intended),
                                   "new_official_get": 0}
    if args.candidate_root is not None:
        result = commit_offline_candidate_lkg(report, args.candidate_root, args.expected_sha)
        # Verify the persisted canonical bytes with the existing restart reader.
        load_offline_candidate_lkg(args.candidate_root, result["sha256"])
        report["candidate_commit"] = result
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
