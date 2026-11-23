#!/usr/bin/env python3
"""G4B source-bound public-page evidence probe. No page bodies or credentials in outputs.

Never scrape a listing, guess values, bypass challenges, or publish documents.
Only GET fixed public event-detail URLs from the checked-in G4A evidence manifest.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib import request, error, parse
from datetime import datetime, timezone
from bs4 import BeautifulSoup

REPO = 'easonliu714/event_scraper_public'
BRANCH = 'fix/event-radar-v44-cloud-20261023'
MANIFEST = Path(__file__).resolve().parents[1]/'fixtures/pr1_g4b_source_samples.json'
MAX_BYTES = 400000
MAX_SAMPLES = 7
ALLOWED = {'ACCUPASS':'www.accupass.com', 'FamiTicket':'www.famiticket.com.tw', 'OPENTIX':'www.opentix.life'}
FIELDS = ('date','location','price','description')


def authorized(env):
    return (env.get('GITHUB_ACTIONS') == 'true'
        and env.get('GITHUB_EVENT_NAME') == 'pull_request'
        and env.get('GITHUB_REPOSITORY') == REPO
        and env.get('GITHUB_HEAD_REF') == BRANCH
        and env.get('EVENT_RADAR_TELEGRAM') == '0'
        and env.get('EVENT_RADAR_TERMUX') == '0'
        and env.get('EVENT_RADAR_ACTIONS') == '0'
        and bool(env.get('RUNNER_TEMP')) and bool(env.get('GITHUB_WORKSPACE')))


def safe_target(url, platform):
    if platform not in ALLOWED or not isinstance(url, str):return False
    try:
        p=parse.urlsplit(url)
        if p.scheme!='https' or p.hostname!=ALLOWED[platform] or p.port not in (None,443) or p.username or p.password or p.fragment:return False
        if platform=='ACCUPASS': return bool(re.fullmatch(r'/event/\d{22}',p.path)) and not p.query
        if platform=='OPENTIX': return bool(re.fullmatch(r'/event/\d{18,20}',p.path)) and not p.query
        if platform=='FamiTicket':return bool(re.fullmatch(r'/Home/Activity/Info/[A-Za-z0-9_-]{60,220}',p.path)) and not p.query
    except (ValueError,AttributeError):pass
    return False


def load_manifest(path=MANIFEST):
    x=json.loads(Path(path).read_text(encoding='utf-8'))
    if x.get('baseline_head')!='509dfeb3b849b7dd05ca91ec39b79f7c3c8e21ca':raise ValueError('BASELINE_HEAD_CHANGED')
    rows=x.get('source_samples')
    if not isinstance(rows,list) or len(rows)!=MAX_SAMPLES:raise ValueError('NOT_EXACT_7_SAMPLES')
    count={k:0 for k in ALLOWED};seen=set()
    for row in rows:
        p=row.get('platform');u=row.get('url')
        if not safe_target(u,p) or u in seen:raise ValueError('SAMPLE_URL_UNTRUSTED_OR_DUPLICATE')
        if row.get('evidence_run')!=39906440620 or row.get('golden_status')!='UNVERIFIED_SOURCE_CAPTURE_PENDING':raise ValueError('SAMPLE_PROVENANCE_CHANGED')
        seen.add(u);count[p]+=1
    if count!={'ACCUPASS':2,'FamiTicket':2,'OPENTIX':3}:raise ValueError('SAMPLE_COVERAGE_CHANGED')
    return rows


def category_signal(soup):
    # Platform-specific explicit label, never infer from date/time or title.
    for tag in soup(['script','style','noscript']):tag.decompose()
    visible=soup.get_text(' ',strip=True)
    found=re.search(r'類別\s*[:：]\s*(商品|戲劇|免費身障|音樂|舞蹈|展覽|講座|親子|演唱會|其他)',visible)
    return found.group(1) if found else None


def summary_from_html(html, url, detail_parser=None):
    if detail_parser is None:
        repo_root=str(Path(__file__).resolve().parents[1])
        if repo_root not in sys.path:sys.path.insert(0,repo_root)
        from event_details import parse_detail as detail_parser
    soup=BeautifulSoup(html,'html.parser')
    def meta(key):
        node=soup.find('meta',attrs={'property':key}) or soup.find('meta',attrs={'name':key})
        value=node.get('content','') if node else ''
        return re.sub(r'\s+',' ',str(value)).strip()[:140]
    h=soup.find('h1'); h1=h.get_text(' ',strip=True)[:140] if h else ''
    sig=category_signal(BeautifulSoup(html,'html.parser'))
    # Do not save description text; length only. No HTML or session data in artifact.
    try: parsed=detail_parser(html,url)
    except (ValueError,TypeError,AttributeError):parsed={}
    return {'official_category_label':sig,'h1':h1,'og_title':meta('og:title'),
            'og_description_length':len(meta('og:description')),
            'jsonld_event_scripts':sum(1 for t in soup.select('script[type="application/ld+json"]') if 'Event' in t.get_text()),
            'time_tags':len(soup.select('time[datetime]')),
            'parser_fields_present':{k:bool(parsed.get(k) and parsed[k]!='詳內文') for k in FIELDS},
            'parser_date':str(parsed.get('date',''))[:60],
            'parser_location':str(parsed.get('location',''))[:100],
            'parser_price':str(parsed.get('price',''))[:70],
            'parser_description_length':len(str(parsed.get('description') or ''))}


class SameHostRedirect(request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        a=parse.urlsplit(req.full_url);b=parse.urlsplit(newurl)
        if b.scheme!='https' or b.hostname!=a.hostname or b.port not in (None,443):
            raise ValueError('REDIRECT_OUTSIDE_SAME_HTTPS_HOST')
        if b.username or b.password: raise ValueError('REDIRECT_HAS_CREDENTIALS')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def get_public_html(url,opener=None):
    opener=opener or request.build_opener(SameHostRedirect())
    req=request.Request(url,headers={'User-Agent':'EventRadarSourceProbe/1.0 (public-page read-only validation)',
                                     'Accept':'text/html,application/xhtml+xml;q=0.9','Accept-Language':'zh-TW,zh;q=0.9'},method='GET')
    with opener.open(req,timeout=15) as resp:
        status=resp.status
        ctype=resp.headers.get('Content-Type','')
        if status!=200:raise ValueError('HTTP_'+str(status))
        if not ('text/html' in ctype.lower() or 'application/xhtml+xml' in ctype.lower()):raise ValueError('NON_HTML_CONTENT')
        reported=resp.headers.get('Content-Length')
        if reported and int(reported)>MAX_BYTES:raise ValueError('BODY_TOO_LARGE_DECLARED')
        body=resp.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES:raise ValueError('BODY_TOO_LARGE')
        encoding=resp.headers.get_content_charset() or 'utf-8'
        return body.decode(encoding,errors='replace'), hashlib.sha256(body).hexdigest(),len(body)


def evidence_dir(env):
    tmp=Path(env['RUNNER_TEMP']).resolve(strict=True)
    workspace=Path(env['GITHUB_WORKSPACE']).resolve(strict=True)
    if tmp==workspace or workspace in tmp.parents or tmp in workspace.parents:
        raise ValueError('RUNNER_TEMP_OVERLAPS_WORKSPACE')
    result=tmp/'eventradar_pr1_g4b_probe'/'evidence'
    if result.parent.is_symlink() or result.is_symlink():raise ValueError('SYMLINK_OUTPUT')
    result.mkdir(parents=True,exist_ok=True)
    return result


def render_markdown(report):
    lines=['# EventRadar G4B — Public source evidence (not field-correctness approval)','',
     '- Source: G4A Run 39906440620 and locked seven sample event URLs',
     '- Mode: read-only exact URL GET; no auth, notifications, raw HTML, secrets, Git pushes or data publication',
     '- Evidence timestamp UTC: '+report['utc'],
     '- Baseline SHA unchanged: '+str(report['baseline_unchanged']),
     '- Accessible: '+str(report['accessible'])+'/7; blocked/errors: '+str(report['blocked']),
     '- Golden fixture status: **PENDING independent human/source verification**','',
     '| Site | HTTP/result | Source category | Parser date? | Location? | Price? | Description? |',
     '|---|---|---|---|---|---|---|']
    for a in report['samples']:
        p=a.get('parsed') or {}; f=p.get('parser_fields_present') or {}
        lines.append('| '+a['platform']+' | '+str(a.get('status'))+' | '+str(p.get('official_category_label') or '-')+' | '+
         ' | '.join('Y' if f.get(k) else '-' for k in FIELDS)+' |')
    lines.extend(['','Only metadata/category observations were saved. These do not establish event dates, ticket price accuracy, or whether a multi-show pass is one event.',
     'Do not merge PR #1 or publish docs/data.json on this evidence alone.'])
    return '\n'.join(lines)+'\n'


def run(env,opener=None):
    if not authorized(env):print('HOLD G4B_UNAUTHORIZED_ENV');return 20
    try:
        directory=evidence_dir(env)
        samples=load_manifest()
        repo=Path(env['GITHUB_WORKSPACE']).resolve(strict=True)
        baseline=repo/'docs/data.json'
        before=hashlib.sha256(baseline.read_bytes()).hexdigest()
    except (OSError,ValueError,KeyError,TypeError) as ex:
        print('HOLD G4B_PREFLIGHT '+type(ex).__name__);return 21
    result={'gate':'PR1_G4B_SOURCE_EVIDENCE','utc':datetime.now(timezone.utc).isoformat(),
            'baseline_head':'509dfeb3b849b7dd05ca91ec39b79f7c3c8e21ca',
            'baseline_sha_before':before,'samples':[],'accessible':0,'blocked':0}
    for row in samples:
        entry={'platform':row['platform'],'url':row['url'],'observed_title':row['observed_title'],
               'prior_date':row.get('observed_date'),'prior_location':row.get('observed_location'),
               'golden_status':'UNVERIFIED','official_category_reference':row.get('official_category_reference')}
        try:
            html,digest,n=get_public_html(row['url'],opener)
            entry.update(status='HTTP_200',response_bytes=n,body_sha256=digest,
                         parsed=summary_from_html(html,row['url']))
            result['accessible']+=1
        except error.HTTPError as ex:
            entry['status']='HTTP_'+str(ex.code);result['blocked']+=1
        except (error.URLError,OSError,ValueError,UnicodeError,TimeoutError) as ex:
            entry['status']=type(ex).__name__;result['blocked']+=1
        result['samples'].append(entry)
    after=hashlib.sha256(baseline.read_bytes()).hexdigest()
    result['baseline_sha_after']=after
    result['baseline_unchanged']=before==after
    (directory/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (directory/'report.md').write_text(render_markdown(result),encoding='utf-8')
    print('G4B_SAMPLES=7 ACCESSIBLE='+str(result['accessible'])+' BLOCKED='+str(result['blocked']))
    print('BASELINE_SHA_UNCHANGED='+str(result['baseline_unchanged']))
    print('EVIDENCE_DIR='+str(directory))
    if not result['baseline_unchanged']:print('HOLD G4B_BASELINE_CHANGED');return 22
    if result['accessible']<3:
        print('HOLD G4B_INSUFFICIENT_ACCESSIBLE_SOURCE_EVIDENCE');return 23
    print('PASS G4B_SOURCE_EVIDENCE_COLLECTED_GOLDEN_PENDING (NO PUBLISH)')
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run: parser.error('explicit --run required')
    sys.exit(run(os.environ))
