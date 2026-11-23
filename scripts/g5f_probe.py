#!/usr/bin/env python3
"""EventRadar G5F equal-contract network probe. No HTML, no Git mutations.

One exact public URL GET each, no redirects, max 1.0 KiB response body (actually none read),
no cookies/auth, fixed UA and Accept, bounded timeout/spacing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import sys
import time
from urllib import request, error, parse
from datetime import datetime, timezone

MANIFEST_SHA = '30c846a526491b1eb574f1f60f63cfc3990fa8a24d05661c467e55ab70716894'
SNAPSHOT_SHA = 'ef39c6be44a3f26c30bc3ce13f41548d1bd6b6408af8e872eb55fff360fea43b'
UA = 'EventRadar-G5F-AB-Probe/1.0 (public HTTP status comparison; no automation bypass)'
ACCEPT='text/html,application/xhtml+xml'
TIMEOUT=8
DELAY=2
ALLOWED = {
    'www.beclass.com','kidsclub.com.tw','www.accupass.com','www.twtc.com.tw',
    'www.famiticket.com.tw','strolltimes.com','hsinchucityfilm.kktix.cc','www.opentix.life'
}

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_url(u):
    if not isinstance(u,str):raise ValueError('HOLD URL_TYPE')
    s=parse.urlsplit(u.replace('&amp;','&'))
    if (s.scheme!='https' or s.hostname not in ALLOWED or s.username or s.password or
        s.port is not None or s.fragment or not s.path.startswith('/') or '\\' in u):
        raise ValueError('HOLD UNSAFE_PUBLIC_URL')
    return parse.urlunsplit((s.scheme,s.netloc,s.path,s.query,''))


def load_targets(p:Path):
    raw=Path(p).read_bytes()
    if sha(raw)!=MANIFEST_SHA:raise ValueError('HOLD TARGETS_MANIFEST_SHA')
    obj=json.loads(raw)
    if obj.get('kind')!='G5E_PINNED_SOURCE_PROBES' or obj.get('snapshot_sha256')!=SNAPSHOT_SHA:
        raise ValueError('HOLD TARGETS_PROVENANCE')
    targets=obj['targets']
    if len(targets)!=11 or len({x['id'] for x in targets})!=11 or len({x['url'] for x in targets})!=11:
        raise ValueError('HOLD TARGET_COUNT')
    for t in targets:
        if set(t)!={'id','platform','url'} or not re.fullmatch(r'[A-Z][A-Z0-9_]{3,50}',t['id']):
            raise ValueError('HOLD TARGET_SCHEMA')
        validate_url(t['url'])
    return targets


def kind(code):
    if code in (404,410):return 'GONE_CANDIDATE_REVIEW_ONLY'
    if code in (301,302,303,307,308):return 'REDIRECT_REVIEW'
    if code==200:return 'HTTP_200_CONTENT_UNVERIFIED'
    if code in (401,403,408,429,500,502,503,504):return 'ACCESS_UNCERTAIN'
    return 'HTTP_OTHER_REVIEW'


def request_once(url,opener=None):
    safe=validate_url(url)
    req=request.Request(safe,headers={'User-Agent':UA,'Accept':ACCEPT},method='GET')
    opener=opener or request.build_opener(request.ProxyHandler({}),request.HTTPSHandler(context=ssl.create_default_context()),NoRedirect())
    t0=time.monotonic();status=None;err=None
    try:
        with opener.open(req,timeout=TIMEOUT) as response:
            status=response.status
            # No response body read or persisted.
    except error.HTTPError as e:
        status=e.code
    except (error.URLError,TimeoutError,OSError,ssl.SSLError,ValueError) as e:
        err=type(e).__name__
    elapsed=int((time.monotonic()-t0)*1000)
    result={'http':status,'outcome':kind(status) if status is not None else 'ACCESS_UNCERTAIN',
            'elapsed_ms':elapsed,'exception_type':err,'auto_hide':False}
    return result


def cloud_authorized(env):
    if not (env.get('GITHUB_ACTIONS')=='true' and env.get('GITHUB_EVENT_NAME')=='pull_request' and
            env.get('GITHUB_REPOSITORY')=='easonliu714/event_scraper_public' and
            env.get('GITHUB_HEAD_REF')=='fix/event-radar-v44-cloud-20261023' and
            env.get('EVENT_RADAR_TERMUX')=='0' and env.get('EVENT_RADAR_TELEGRAM')=='0'):
        return False
    try:
        evt=json.loads(Path(env['GITHUB_EVENT_PATH']).read_text())
        p=evt['pull_request'];head=p['head']
        return (p['number']==1 and p['draft'] is True and
                head['repo']['full_name']=='easonliu714/event_scraper_public' and
                head['ref']=='fix/event-radar-v44-cloud-20261023' and
                Path(env['RUNNER_TEMP']).is_dir())
    except (OSError,KeyError,ValueError,TypeError):return False


def main(argv=None):
    pa=argparse.ArgumentParser()
    pa.add_argument('--environment',choices=('phone','cloud'),required=True)
    pa.add_argument('--manifest',required=True)
    pa.add_argument('--output',required=True)
    args=pa.parse_args(argv)
    dst=Path(args.output).expanduser().resolve()
    if args.environment=='cloud':
        if not cloud_authorized(os.environ):raise ValueError('HOLD CLOUD_CONTEXT')
        temp=Path(os.environ['RUNNER_TEMP']).resolve()
        if temp not in dst.parents:raise ValueError('HOLD CLOUD_EVIDENCE_OUTSIDE_RUNNER_TEMP')
    else:
        if os.environ.get('GITHUB_ACTIONS')=='true':raise ValueError('HOLD PHONE_IN_ACTIONS')
        home=Path.home().resolve()
        root=home/'eventradar_toolkit'/'gates'/'g5f_phone_cloud_ab_v100'/'evidence'
        if root.resolve()!=dst.parent:raise ValueError('HOLD PHONE_EVIDENCE_OUTSIDE_GATE')
    targets=load_targets(Path(args.manifest))
    results=[]
    for i,t in enumerate(targets):
        if i:time.sleep(DELAY)
        obj=request_once(t['url'])
        results.append({'id':t['id'],'platform':t['platform'],'url_sha256':sha(t['url'].encode()),**obj})
        print('PROBE',args.environment,t['id'],'HTTP='+str(obj['http']),obj['outcome'],flush=True)
    payload={'gate':'G5F_CLOUD_PHONE_AB','environment':args.environment,'probe_contract':'v1-no-redirect-GET-no-body',
             'manifest_sha256':MANIFEST_SHA,'snapshot_sha256':SNAPSHOT_SHA,
             'utc':datetime.now(timezone.utc).isoformat(),'samples':len(results),
             'timeout_seconds':TIMEOUT,'delay_seconds':DELAY,'results':results,
             'auto_hidden':0,'no_html_saved':True,'no_git_mutations':True}
    if dst.exists():raise ValueError('HOLD EXISTING_EVIDENCE_NO_OVERWRITE')
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('PASS G5F_'+args.environment.upper()+'_11_SOURCE_PROBES_EVIDENCE_ONLY')
    print('OUTPUT='+str(dst))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:
        print('HOLD G5F '+str(e),file=sys.stderr);sys.exit(2)
