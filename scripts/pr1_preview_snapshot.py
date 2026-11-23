#!/usr/bin/env python3
"""Source-bound PR1 PWA snapshot: dry-run scrape ONLY in ephemeral temp, export public review data.

PR runner job has no write credentials, no .git in scrape workspace, no official data writes.
"""
from __future__ import annotations
import hashlib
import html
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

REPO = 'easonliu714/event_scraper_public'
BRANCH = 'fix/event-radar-v44-cloud-20261023'
BASE = '6004754f90d551cdb0cdb91a3e04b42c04f45f48'
FIELDS = ('title', 'url', 'platform', 'type', 'date', 'location', 'price',
          'description', 'ticket_date', 'img_url', 'region', 'scraped_at', 'detail_checked_at')
TEXT_KEYS = set(FIELDS) - {'url', 'img_url', 'scraped_at', 'detail_checked_at'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_url(value):
    if not isinstance(value, str) or len(value) > 4096:
        return False
    try:
        p = urlsplit(value)
        return p.scheme == 'https' and bool(p.hostname) and not p.username and not p.password and not any(ord(c) < 32 for c in value)
    except ValueError:
        return False


def export_rows(rows):
    """Preserve recognized PWA keys, HTML-encode untrusted text for innerHTML rendering."""
    output, seen, skipped = [], set(), 0
    for row in rows:
        if not isinstance(row, dict) or not all(row.get(k) for k in ('title', 'url', 'platform')):
            skipped += 1
            continue
        if not safe_url(row.get('url')) or row['url'] in seen:
            skipped += 1
            continue
        cleaned = {}
        for k in FIELDS:
            value = row.get(k)
            if not isinstance(value, str):
                continue
            if k in TEXT_KEYS:
                cleaned[k] = html.escape(value, quote=True)
            elif k == 'img_url':
                cleaned[k] = html.escape(value, quote=True) if safe_url(value) else ''
            else:
                cleaned[k] = value
        cleaned['url'] = html.escape(row['url'], quote=True)
        output.append(cleaned)
        seen.add(row['url'])
    return output, skipped


def guard_env(env, event):
    p = event.get('pull_request') or {}
    h = p.get('head') or {}
    b = p.get('base') or {}
    return bool(env.get('GITHUB_ACTIONS') == 'true'
                and env.get('GITHUB_EVENT_NAME') == 'pull_request'
                and env.get('GITHUB_REPOSITORY') == REPO
                and env.get('GITHUB_HEAD_REF') == BRANCH
                and env.get('EVENT_RADAR_TELEGRAM') == '0'
                and env.get('EVENT_RADAR_TERMUX') == '0'
                and env.get('EVENT_RADAR_ACTIONS') == '1'
                and (p.get('number') == 1)
                and h.get('ref') == BRANCH
                and (h.get('repo') or {}).get('full_name') == REPO
                and b.get('ref') == 'main'
                and h.get('sha')
                and env.get('RUNNER_TEMP') and env.get('GITHUB_WORKSPACE'))


def export_snapshot(data_path, dest, *, expected_source_sha, source_head, report):
    """No publisher: writes bounded public JSON + provenance only to runner temp."""
    data_path, dest = Path(data_path), Path(dest)
    if sha(data_path) != expected_source_sha:
        raise ValueError('HOLD OUTPUT_SHA_CHANGED_AFTER_DRYRUN')
    rows = json.loads(data_path.read_text(encoding='utf-8'))
    if not isinstance(rows, list) or len(rows) < 20 or report.get('changed_or_new_rows', 0) < 20:
        raise ValueError('HOLD NO_FRESH_LIVE_SNAPSHOT')
    if not report.get('baseline_unchanged') or report.get('process_exit_code') != 0 or report.get('process_timeout'):
        raise ValueError('HOLD LIVE_DRYRUN_UNPROVEN')
    clean, rejected = export_rows(rows)
    if len(clean) < 20:
        raise ValueError('HOLD SANITIZED_PREVIEW_TOO_SMALL')
    dest.mkdir(parents=True, exist_ok=False)
    out = dest/'data.json'
    out.write_text(json.dumps(clean, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')
    meta = {
        'kind': 'EVENTRADAR_PR1_PREVIEW_ONLY', 'public_unverified': True,
        'source_repository': REPO, 'source_branch': BRANCH,
        'source_pr_number': 1, 'source_head_sha': source_head,
        'baseline_main_sha': BASE, 'baseline_data_sha256': report['started_data_sha256'],
        'unsanitized_output_sha256': expected_source_sha, 'preview_data_sha256': sha(out),
        'preview_rows': len(clean), 'source_output_rows': len(rows),
        'dropped_invalid_rows': rejected,
        'new_rows_in_dryrun': report.get('added_rows'),
        'changed_or_new_rows': report['changed_or_new_rows'],
        'created_at_utc': report.get('finished_at_utc'),
        'warning': 'Preview only; activity dates, places, prices and classification are NOT verified.'
    }
    (dest/'preview_status.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return meta


def main():
    env = os.environ
    if '--generate' not in sys.argv[1:] or len(sys.argv) != 2:
        raise SystemExit('HOLD EXPECT_EXPLICIT_GENERATE_FLAG')
    if not env.get('GITHUB_EVENT_PATH') or not Path(env['GITHUB_EVENT_PATH']).is_file():
        raise SystemExit('HOLD MISSING_GITHUB_PR_EVENT')
    event = json.loads(Path(env['GITHUB_EVENT_PATH']).read_text(encoding='utf-8'))
    if not guard_env(env, event):
        raise SystemExit('HOLD UNAUTHORIZED_PR1_PREVIEW_SNAPSHOT')
    ws = Path(env['GITHUB_WORKSPACE']).resolve()
    rt = Path(env['RUNNER_TEMP']).resolve()
    if rt == ws or ws in rt.parents:
        raise SystemExit('HOLD RUNNER_TEMP_IS_REPO')
    src = ws/'docs/data.json'
    before = sha(src)
    sys.path.insert(0, str(ws/'scripts'))
    import pr1_cloud_dryrun
    temp = rt/'eventradar_pr1_preview_capture'
    ret = pr1_cloud_dryrun.run_live(ws, temp, 1200)
    if ret != 0 or sha(src) != before:
        raise SystemExit('HOLD PREVIEW_SCRAPE_OR_BASELINE')
    report = json.loads((temp/'evidence/report.json').read_text(encoding='utf-8'))
    if report['started_data_sha256'] != before:
        raise SystemExit('HOLD REPORT_BASELINE_MISMATCH')
    status = export_snapshot(temp/'workspace/docs/data.json',
                             rt/'eventradar_pr1_preview_snapshot/export',
                             expected_source_sha=report['output_data_sha256'],
                             source_head=event['pull_request']['head']['sha'], report=report)
    print('PASS PR1_PWA_PREVIEW_SNAPSHOT_NO_PUBLISH')
    print('PREVIEW_ROWS='+str(status['preview_rows']))
    print('SOURCE_HEAD_SHA='+status['source_head_sha'])
    print('BASELINE_SHA_UNCHANGED=True')
    print('NO_GIT_COMMIT_NO_PUSH_NO_MAIN_WRITE=True')

if __name__ == '__main__':
    main()
