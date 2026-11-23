#!/usr/bin/env python3
"""PR#1 controlled live HTTP crawl. Works in isolated temp directory, never Git-pushes.

Run on GitHub-hosted runner via pull_request only. Sanitized evidence only.
Pure helpers are separately tested with synthetic data, no network needed.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

REPO_NAME = 'easonliu714/event_scraper_public'
PR_BRANCH = 'fix/event-radar-v44-cloud-20261023'
FIELDS = ('date', 'location', 'price', 'description')
PLACEHOLDERS = {'', '詳內文', 'None', 'null', 'undefined', '詳細資訊請點擊連結查看。',
                '暫無詳細簡介，請點擊下方按鈕前往官網查看。'}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def present(v):
    return isinstance(v, str) and bool(v.strip()) and v.strip() not in PLACEHOLDERS


def valid_https(url):
    if not isinstance(url, str):
        return False
    p = urlsplit(url)
    return p.scheme == 'https' and bool(p.hostname) and not p.username and not p.password


def text_safe(value, limit=90):
    s = str(value or '').replace('\n', ' ').replace('\r', ' ').replace('|', '／').replace('`', "'")
    s = ''.join(c for c in s if c.isprintable())
    return s[:limit]


def report_events(before, after, *, exit_code, timed_out, source_sha, result_sha):
    original = {r['url']:r for r in before if isinstance(r,dict) and r.get('url')}
    now_urls = set(original)
    touched = []
    per_platform = {}
    invalid_urls = 0
    for row in after:
        if not isinstance(row,dict):
            continue
        p = str(row.get('platform') or 'UNKNOWN')
        s = per_platform.setdefault(p, {'rows': 0, 'new': 0, 'changed': 0,
                                         **{k:0 for k in FIELDS}, 'samples': []})
        s['rows'] += 1
        for f in FIELDS:
            s[f] += int(present(row.get(f)))
        if not valid_https(row.get('url')):
            invalid_urls += 1
        old = original.get(row.get('url'))
        if old is None:
            s['new'] += 1
            touched.append(row)
        elif row != old:
            s['changed'] += 1
            touched.append(row)
    # deterministic bounded examples, one each among updated/new results per platform
    for row in touched:
        p = str(row.get('platform') or 'UNKNOWN')
        samples = per_platform[p]['samples']
        if len(samples) < 3:
            samples.append({
                'title': text_safe(row.get('title'), 80),
                'url': text_safe(row.get('url'), 200),
                'date': text_safe(row.get('date')),
                'location': text_safe(row.get('location')),
                'price': text_safe(row.get('price')),
                'description_chars': len(str(row.get('description') or ''))
            })
    return {
        'gate': 'EVENT_RADAR_PR1_LIVE_DRYRUN',
        'version': 'V44.2-CLOUD-GATE3',
        'mode': 'NO_PUBLISH_ISOLATED_TEMP',
        'started_data_sha256': source_sha,
        'output_data_sha256': result_sha,
        'process_exit_code': exit_code,
        'process_timeout': timed_out,
        'original_rows': len(before),
        'output_rows': len(after),
        'changed_or_new_rows': len(touched),
        'added_rows': sum(1 for r in after if isinstance(r,dict) and r.get('url') not in now_urls),
        'invalid_https_urls': invalid_urls,
        'platforms': dict(sorted(per_platform.items())),
    }


def write_evidence(report, dest):
    dest = Path(dest);dest.mkdir(parents=True,exist_ok=True)
    (dest/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines = [
        '# EventRadar PR1 live dry-run (NO publication)',
        '',
        f"- Program: `{report['version']}`; isolated temp runner directory",
        f"- Original JSON: `{report['started_data_sha256']}`",
        f"- Temp output JSON: `{report['output_data_sha256']}`",
        f"- Before: {report['original_rows']}; after: {report['output_rows']}; changed/new: {report['changed_or_new_rows']}; added: {report['added_rows']}",
        f"- HTTP subprocess exit: {report['process_exit_code']}; timed out: {report['process_timeout']}",
        f"- Invalid HTTPS URLs: {report['invalid_https_urls']}",
        '',
        '| Source | Rows | New | Changed | Date | Location | Price | Description |',
        '|---|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for platform,d in report['platforms'].items():
        n=d['rows'] or 1
        vals=[f"{d[k]}/{d['rows']} ({100*d[k]/n:.0f}%)" for k in FIELDS]
        lines.append(f"| {text_safe(platform,40)} | {d['rows']} | {d['new']} | {d['changed']} | "+' | '.join(vals)+' |')
    lines += ['', '## Crawl errors and warnings (sanitized excerpts)', '']
    lines.append(f"- Matched diagnostic lines: {report.get('diagnostic_total',0)}")
    for entry in report.get('diagnostic_excerpt', []):
        lines.append('- '+text_safe(entry,220))
    lines += ['', '## Examples (up to 3 changed/new rows per source)', '']
    for platform,d in report['platforms'].items():
        if not d['samples']:
            continue
        lines.append('### '+text_safe(platform,50))
        for r in d['samples']:
            lines.append(f"- **{r['title']}** — {r['url']} (date={r['date']}; location={r['location']}; price={r['price']}; description_chars={r['description_chars']})")
    lines += ['', 'Presence does not establish accuracy. Some platforms remain disabled in the source. No raw HTML, secrets, complete data.json or local credentials are uploaded.', '']
    (dest/'report.md').write_text('\n'.join(lines),encoding='utf-8')


def is_runner_authorized(env):
    # No external secrets required or accepted. This is not a general-purpose runner.
    if env.get('GITHUB_ACTIONS') != 'true': return False
    if env.get('GITHUB_EVENT_NAME') != 'pull_request': return False
    if env.get('GITHUB_REPOSITORY') != REPO_NAME: return False
    if env.get('GITHUB_HEAD_REF') != PR_BRANCH: return False
    if env.get('EVENT_RADAR_TELEGRAM') != '0': return False
    if env.get('EVENT_RADAR_TERMUX') != '0': return False
    if env.get('EVENT_RADAR_ACTIONS') != '1': return False
    if not env.get('RUNNER_TEMP') or not env.get('GITHUB_WORKSPACE'): return False
    return True


def run_live(repo_dir, temp_root, max_seconds=1200):
    """The source script may write state ONLY inside the runner temporary copy."""
    repo_dir=Path(repo_dir).resolve()
    temp_root=Path(temp_root).resolve()
    # Never place the temporary copy below the tracked workspace.
    if temp_root == repo_dir or repo_dir in temp_root.parents:
        raise ValueError('HOLD TEMP_ROOT_INSIDE_REPOSITORY')
    original=repo_dir/'docs/data.json'
    original_sha=sha256(original)
    original_rows=json.loads(original.read_text(encoding='utf-8'))
    if not isinstance(original_rows,list): raise ValueError('HOLD INVALID_BASELINE_JSON')
    temp_root.mkdir(parents=True,exist_ok=False)
    scratch=temp_root/'workspace'
    scratch.mkdir()
    (scratch/'docs').mkdir()
    # No .git, no .env, no ssh key, no git credentials copied.
    for filename in ('show_news.py','event_details.py'):
        shutil.copyfile(repo_dir/filename,scratch/filename)
    shutil.copyfile(original,scratch/'docs/data.json')
    env=dict(os.environ)
    env.update(EVENT_RADAR_ACTIONS='1',EVENT_RADAR_TELEGRAM='0',EVENT_RADAR_TERMUX='0',
               DETAIL_NEW_LIMIT='12',DETAIL_REPAIR_LIMIT='8')
    for key in ('GH_TOKEN','GITHUB_TOKEN','TG_BOT_TOKEN','TG_CHAT_ID','TELEGRAM_TOKEN','TELEGRAM_CHAT_ID'):
        env.pop(key,None)
    log_file=temp_root/'crawler_console.log'
    code=1;timed_out=False
    with log_file.open('w',encoding='utf-8') as log:
        try:
            p=subprocess.run([sys.executable,'-u','show_news.py','--once'],cwd=scratch,
                             env=env,stdout=log,stderr=subprocess.STDOUT,
                             timeout=max_seconds,check=False)
            code=p.returncode
        except subprocess.TimeoutExpired:
            timed_out=True;code=124
    output=scratch/'docs/data.json'
    try:
        output_rows=json.loads(output.read_text(encoding='utf-8'))
        if not isinstance(output_rows,list): raise ValueError('not a list')
    except (OSError, ValueError,TypeError, json.JSONDecodeError):
        output_rows=[]
    after_sha=sha256(output) if output.exists() else 'MISSING'
    report=report_events(original_rows,output_rows,exit_code=code,timed_out=timed_out,
                         source_sha=original_sha,result_sha=after_sha)
    unchanged=(sha256(original)==original_sha)
    # No secrets or complete log files in downloadable evidence. Keep bounded,
    # sanitized failure indicators to diagnose site-specific HTTP/parser errors.
    raw_log = log_file.read_text(encoding='utf-8',errors='replace')
    diagnostics = []
    for line in raw_log.splitlines():
        if any(keyword in line.lower() for keyword in ('hold','fail','error','timeout','403','404','429','502','失敗','異常')):
            line = re.sub(r'https?://\S+', '[URL_REDACTED]', line)
            line = re.sub(r'(?:gh[pousr]_[A-Za-z0-9]{15,}|[0-9]{8,}:[A-Za-z0-9_-]{20,})', '[TOKEN_REDACTED]', line)
            diagnostics.append(text_safe(line,220))
    report['diagnostic_total'] = len(diagnostics)
    report['diagnostic_excerpt'] = diagnostics[-80:]
    report['baseline_unchanged']=unchanged
    report['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    write_evidence(report,temp_root/'evidence')
    baseline_by_url={r['url']:r for r in original_rows if isinstance(r,dict) and r.get('url')}
    touched_platforms={r.get('platform') for r in output_rows if isinstance(r,dict)
        and r.get('url') and (r['url'] not in baseline_by_url or r != baseline_by_url[r['url']])}
    print('START EVENT_RADAR_PR1_CLOUD_DRYRUN')
    print('EVENT_RADAR_VERSION=V44.2-CLOUD-GATE3')
    print(f"INPUT_ROWS={len(original_rows)} OUTPUT_ROWS={len(output_rows)} CHANGED={report['changed_or_new_rows']} PLATFORM_COVERAGE={len(touched_platforms)}")
    print('BASELINE_SHA_UNCHANGED='+str(unchanged))
    print('SANITIZED_EVIDENCE='+str(temp_root/'evidence'/'report.md'))
    # Never falsely mark success from old retained records alone.
    if code != 0 or timed_out or not unchanged or report['changed_or_new_rows'] < 20 or len(touched_platforms) < 3:
        print('HOLD EVENT_RADAR_PR1_CLOUD_DRYRUN_UNPROVEN (inspect artifact and log)')
        return 5
    print('PASS EVENT_RADAR_PR1_CLOUD_DRYRUN_NO_PUBLISH (field correctness NOT proven)')
    return 0


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',action='store_true',required=True)
    parser.add_argument('--max-seconds',type=int,default=1200)
    args=parser.parse_args()
    if not is_runner_authorized(os.environ):
        raise SystemExit('HOLD PR1_DRYRUN_ONLY_ON_AUTHORIZED_PR_RUNNER')
    if args.max_seconds < 30 or args.max_seconds > 1500:
        raise SystemExit('HOLD INVALID_TIME_BUDGET')
    runner_tmp=Path(os.environ['RUNNER_TEMP']).resolve()
    runner_dir=runner_tmp/'eventradar_pr1_cloud_dryrun'
    if runner_dir.exists():
        raise SystemExit('HOLD EXISTING_DRYRUN_DIRECTORY')
    raise SystemExit(run_live(Path(os.environ['GITHUB_WORKSPACE']),runner_dir,args.max_seconds))

if __name__=='__main__':
    main()
