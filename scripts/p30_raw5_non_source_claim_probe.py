"""NON-SOURCE TEST: protected GitHub ref collision probe. Never authorizes source HTTP."""
from __future__ import annotations
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO = "easonliu714/event_scraper_public"
REF_PREFIX = "refs/heads/source-claims/validation-raw5-"
SHA = re.compile(r"[0-9a-f]{40}\Z")
TOKEN = re.compile(r"[a-z0-9][a-z0-9-]{7,63}\Z")

def validate(scope, anchor, run):
    if not TOKEN.fullmatch(scope) or not TOKEN.fullmatch(run) or not SHA.fullmatch(anchor):
        raise ValueError("INVALID_NON_SOURCE_SCOPE")
    return REF_PREFIX + scope

def api(method, path, token, payload=None):
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode()
    req = urllib.request.Request("https://api.github.com/repos/" + REPO + path,
        data=data, method=method, headers={"Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json", "User-Agent": "eventradar-isolated-claim-probe"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode())

def probe(scope, anchor, run, token, transport=api):
    ref = validate(scope, anchor, run)
    if not token:
        raise ValueError("MISSING_GITHUB_TOKEN")
    status, base = transport("GET", "/git/commits/" + anchor, token)
    if status != 200 or not SHA.fullmatch(base.get("tree", {}).get("sha", "")):
        raise RuntimeError("ANCHOR_READ_HOLD:" + str(status))
    tree = base["tree"]["sha"]
    message = "NON_SOURCE_RAW5_TEST_V1 " + scope + " " + run
    status, commit = transport("POST", "/git/commits", token,
        {"message": message, "tree": tree, "parents": [anchor]})
    if status != 201 or not SHA.fullmatch(commit.get("sha", "")):
        raise RuntimeError("COMMIT_CREATE_HOLD:" + str(status))
    sha = commit["sha"]
    status, result = transport("POST", "/git/refs", token, {"ref": ref, "sha": sha})
    if status == 422:
        return {"decision": "LOST_COLLISION", "status": 422, "ref": ref, "run": run}
    if status != 201:
        raise RuntimeError("REF_CREATE_HOLD:" + str(status) + ":" + str(result.get("message")))
    status, got = transport("GET", "/git/ref/" + ref.removeprefix("refs/"), token)
    if status != 200 or got.get("object", {}).get("sha") != sha:
        raise RuntimeError("WINNER_READBACK_HOLD:" + str(status))
    status, bound = transport("GET", "/git/commits/" + sha, token)
    if (status != 200 or bound.get("message") != message or
        [p.get("sha") for p in bound.get("parents", [])] != [anchor] or
        bound.get("tree", {}).get("sha") != tree):
        raise RuntimeError("WINNER_COMMIT_BINDING_HOLD:" + str(status))
    return {"decision": "WON_TEST_ONLY", "status": 201, "ref": ref,
            "run": run, "commit_sha": sha, "native_get_allowed": False}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scope", required=True, help="Shared unique non-source test ID")
    p.add_argument("--anchor", required=True, help="Existing immutable Git commit")
    p.add_argument("--run", required=True, help="Distinct executor identifier")
    a = p.parse_args()
    result = probe(a.scope, a.anchor, a.run, os.environ.get("GH_TOKEN", ""))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] in ("WON_TEST_ONLY", "LOST_COLLISION") else 2

if __name__ == "__main__":
    sys.exit(main())
