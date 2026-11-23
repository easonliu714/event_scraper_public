#!/usr/bin/env python3
"""G5G: eleven pinned public event pages; bounded in-memory parsing and status-only/field evidence.
No cookies, no auth, no redirects, no automatic record removals, no HTML saved.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import ssl
import sys
import time
from urllib import request, error

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path: sys.path.insert(0, str(REPO))
from g5f_probe import (load_targets, validate_url, cloud_authorized, MANIFEST_SHA,
                       SNAPSHOT_SHA, UA, ACCEPT, TIMEOUT, DELAY)
import event_details

EXPECTED_G5F_MANIFEST = '30c846a526491b1eb574f1f60f63cfc3990fa8a24d05661c467e55ab70716894'
EXPECTED_PARSER_BLOB = 'ed425662b4f2ce2032a0fa0c3e83075842f30767'
EXPECTED_G5G_REL = 'eventradar_toolkit/gates/g5g_field_parity_v100/evidence'
MAX_BYTES = 350_000
MAX_FIELD = {'title': 120, 'date': 90, 'location': 130, 'price': 75}

class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob_hash(path):
    buf = Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(buf)).encode()+b'\0'+buf).hexdigest()


def source_gate(manifest):
    if MANIFEST_SHA != EXPECTED_G5F_MANIFEST:
        raise ValueError('HOLD G5F_MANIFEST_CONTRACT')
    if blob_hash(REPO/'event_details.py') != EXPECTED_PARSER_BLOB:
        raise ValueError('HOLD EVENT_DETAILS_BLOB_CHANGED')
    entries = load_targets(Path(manifest))
    if len(entries) != 11:
        raise ValueError('HOLD EXACT_11_TARGETS')
    return entries


def safe_preview(text, limit):
    return ''.join(c for c in str(text or '') if c.isprintable()).strip()[:limit]


def analyze_html(body, pageurl):
    # Transient raw HTML is never persisted. Parser belongs to pinned PR code.
    doc = body.decode('utf-8', errors='replace')
    try:
        parsed = event_details.parse_detail(doc, pageurl)
        if not isinstance(parsed,dict): raise TypeError('PARSER_NOT_DICT')
    except (ValueError,TypeError,AttributeError,KeyError) as exc:
        return {'parser_status':'PARSER_ERROR','parser_exception':type(exc).__name__,
                'fields_present':{k:False for k in MAX_FIELD}}
    # Public field excerpts only; no description or raw HTML content in report.
    fields={k:bool(parsed.get(k) and str(parsed[k]).strip() not in ('詳內文','未提供')) for k in MAX_FIELD}
    result={'parser_status':'PARSER_RAN_UNVERIFIED', 'fields_present':fields,
            'fields':{k:safe_preview(parsed.get(k),v) if fields[k] else None for k,v in MAX_FIELD.items()},
            'description_present':bool(str(parsed.get('description') or '').strip()),
            'description_chars':len(str(parsed.get('description') or ''))}
    return result


def probe_once(target,opener=None):
    url=validate_url(target['url'])
    opener=opener or request.build_opener(request.ProxyHandler({}),
              request.HTTPSHandler(context=ssl.create_default_context()), NoRedirect())
    req=request.Request(url,headers={'User-Agent':UA, 'Accept':ACCEPT,
                       'Accept-Encoding':'identity'},method='GET')
    start=time.monotonic(); status=None
    payload={'http':None,'outcome':'ACCESS_UNCERTAIN','elapsed_ms':None,
             'downloaded_bytes':0,'body_sha256':None,'auto_hide':False}
    try:
        with opener.open(req,timeout=TIMEOUT) as resp:
            status=resp.status
            payload['http']=status
            if status!=200:
                payload['outcome']='HTTP_OTHER_REVIEW'
                return payload
            ctype=resp.headers.get('Content-Type','').split(';')[0].strip().lower()
            if ctype not in ('text/html','application/xhtml+xml'):
                payload['outcome']='NON_HTML_CONTENT_REVIEW'
                return payload
            data=resp.read(MAX_BYTES+1)
            if len(data)>MAX_BYTES:
                payload['outcome']='OVERSIZED_HTML_REVIEW'
                return payload
            payload.update(outcome='HTTP_200_PARSER_UNVERIFIED', downloaded_bytes=len(data),
                           body_sha256=sha(data))
            payload.update(analyze_html(data,url))
            return payload
    except error.HTTPError as exc:
        status=exc.code
        payload['http']=status
        payload['outcome']='REDIRECT_REVIEW' if status in (301,302,303,307,308) else (
             'GONE_CANDIDATE_REVIEW_ONLY' if status in (404,410) else 'ACCESS_UNCERTAIN')
    except (error.URLError,TimeoutError,OSError,ssl.SSLError,ValueError) as exc:
        payload['exception_type']=type(exc).__name__
    finally:
        payload['elapsed_ms']=int((time.monotonic()-start)*1000)
    return payload


def output_gate(environment,output,env):
    dst=Path(output).expanduser().resolve()
    if dst.exists() or dst.is_symlink():raise ValueError('HOLD EVIDENCE_EXISTS_NO_OVERWRITE')
    if environment=='cloud':
        if not cloud_authorized(env):raise ValueError('HOLD CLOUD_NOT_AUTHORIZED')
        tmp=Path(env['RUNNER_TEMP']).resolve()
        if tmp not in dst.parents or dst.name != 'cloud.json':raise ValueError('HOLD CLOUD_OUTPUT_SCOPE')
    else:
        if env.get('GITHUB_ACTIONS')=='true':raise ValueError('HOLD PHONE_IN_CLOUD')
        required=Path.home()/EXPECTED_G5G_REL
        if dst.parent != required.resolve() or dst.name not in ('phone_wifi.json','phone_cellular.json'):
            raise ValueError('HOLD PHONE_OUTPUT_SCOPE')
    return dst


def execute(environment,manifest,output,env=None,opener=None,delay=True):
    env=os.environ if env is None else env
    dst=output_gate(environment,output,env)
    targets=source_gate(manifest)
    results=[]
    for idx,entry in enumerate(targets):
        if delay and idx:time.sleep(DELAY)
        p=probe_once(entry,opener)
        results.append({'id':entry['id'],'platform':entry['platform'],
                        'url_sha256':sha(entry['url'].encode()),**p})
        print('PROBE',environment,entry['id'],p['http'],p['outcome'],flush=True)
    body={'gate':'G5G_FIELD_PARITY','environment':environment,
          'probe_contract':'G5G_V1_G5F_HEADERS_NORedirect_350KB_INMEMORY',
          'utc':datetime.now(timezone.utc).isoformat(),
          'manifest_sha256':MANIFEST_SHA,'snapshot_sha256':SNAPSHOT_SHA,
          'source_parser_blob_sha':EXPECTED_PARSER_BLOB,
          'sample_count':len(results),'max_html_bytes':MAX_BYTES,
          'no_html_saved':True,'auto_hidden':0,'no_git_mutations':True,
          'result_is_ground_truth':False,'results':results}
    dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open('x',encoding='utf-8') as fp:
        json.dump(body,fp,ensure_ascii=False,indent=2)
        fp.write('\n')
    print('PASS G5G_11_FIELD_PROBES_EVIDENCE_ONLY')
    print('REPORT='+str(dst))
    return 0


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--environment',choices=('phone','cloud'),required=True)
    p.add_argument('--manifest',required=True)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    return execute(args.environment,args.manifest,args.output)

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('HOLD G5G '+str(exc),file=sys.stderr)
        sys.exit(2)
