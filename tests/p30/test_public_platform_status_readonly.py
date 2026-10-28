#!/usr/bin/env python3
"""Read-only public platform status snapshot contract; NEVER enable event publication."""
import argparse
import hashlib
import json
from pathlib import Path

def check(report, basic, adapter, recent):
    assert report['kind']=='EVENTRADAR_PUBLIC_PLATFORM_ENGINEERING_STATUS_V1'
    assert report['schemaVersion']=='1.0.0'
    assert report['production']['eventDataModifiedByThisReport'] is False
    assert report['production']['eventFeedReleaseState']=='HARD_HOLD_NO_PUBLICATION'
    assert report['production']['goldenAccepted']==0
    assert report['production']['eventCandidatesPublishedFromL7BL9M']==0
    assert report['production']['writerEnabled']==False
    assert report['production']['schedulerEnabled']==False
    assert report['production']['notifierEnabled']==False
    assert report['production']['fullAndroidE2EAttested']==False
    assert report['production']['sourceMainEventDataSHA256GitBlob']=='7fc4fe32567a57fd504483eeb9a8b9e10b568ea4'
    rows=report['platforms']
    assert len(rows)==19
    assert len({p['platform'] for p in rows})==19
    assert [p['id'] for p in rows]==[f'{i:02}' for i in range(1,20)]
    bs=basic['platforms']
    assert len(bs)==len(adapter['rows'])==19
    assert report['baselineSummary']['platformsChecked']==19
    assert report['baselineSummary']['http200Platforms']==16
    assert report['baselineSummary']['blocked403Platforms']==3
    assert report['baselineSummary']['positiveListPlatforms']==12
    assert report['baselineSummary']['listCandidates']==264
    assert report['baselineSummary']['detailAttempts']==12
    assert report['baselineSummary']['detailTitleMatches']==5
    assert report['baselineSummary']['canonicalEventCount']==0
    assert basic['kind']=='EVENTRADAR_P30_L7B_FRESH_ACQUISITION_DIAGNOSTICS_V1'
    assert basic['counts']['platformsChecked']==19
    assert basic['counts']['listCandidates']==264
    assert basic['counts']['httpOK']==16
    assert basic['counts']['listPositive']==12
    assert basic['counts']['detailIdentityVerified']==5
    assert adapter['kind']=='EVENTRADAR_P30_L9B_PLATFORM_ADAPTER_GAPS_READONLY_V1'
    for p,b,a in zip(rows,bs,adapter['rows']):
        assert p['platform']==b['platform']==a['platform']
        assert p['baseline']['httpStatus']==b['http']['httpStatus']
        assert p['baseline']['listCandidates']==b['listCandidateCount']
        assert p['baseline']['detailAttempted']==b['detailAttempted']
        assert p['baseline']['detailTitleMatches']==b['detailIdentityVerified']
        assert p['baseline']['observedAtUTC']==basic['collectedAtUTC']
        assert a['listCandidateCount']==b['listCandidateCount']
        assert p['stages']['publication']=='HARD_HOLD_NO_EVENT_RELEASE'
        assert p['stages']['fields']=='HOLD_NOT_FORMALLY_VERIFIED'
        assert isinstance(p['blocker'],str) and len(p['blocker'])>=10
    assert sum(p['baseline']['listCandidates'] for p in rows)==264
    assert sum(p['baseline']['detailTitleMatches'] for p in rows)==5
    overlay={x['platform']:x.get('independentGate') for x in rows}
    assert set(k for k,v in overlay.items() if v)=={'ibon','中正紀念堂','台北世貿'}
    assert overlay['中正紀念堂']['listCandidates']==5
    assert overlay['中正紀念堂']['androidUserPass']==5
    assert overlay['台北世貿']['listCandidates']==39
    assert overlay['台北世貿']['dateRoleCandidates']==38
    assert overlay['台北世貿']['dateConflictHolds']==1
    assert overlay['台北世貿']['androidUserPass']==39
    assert overlay['ibon']['listCandidates']==22
    assert overlay['ibon']['semanticAccepted']==0
    assert overlay['ibon']['semanticRefused']==4
    assert overlay['ibon']['refusalReason']=='AMBIGUOUS_OR_INTERACTIVE'
    assert report['separateEvidence']['androidPlatformSpecificPass']==44
    assert report['separateEvidence']['androidL8CoreUiPass']==True
    assert report['separateEvidence']['ibonL9MFieldCandidatesAccepted']==0
    assert recent['kind']=='EVENTRADAR_P30_L9M_IBON_NEIGHBOR_REASON_DIAGNOSTICS_V1'
    assert recent['sampleCount']==4
    assert recent['titleParityCount']==4
    assert recent['localReviewCount']==0
    assert [r['id'] for r in recent['rows']]==['39575','39878','39907','39978']
    assert all(r['reasonCounts']=={'AMBIGUOUS_OR_INTERACTIVE':1} for r in recent['rows'])
    assert recent['goldenAccepted']==0 and recent['published']==False
    assert recent['releaseState']=='HARD_HOLD_NO_PUBLICATION'
    print('PASS_STATUS_19_BASELINE_HTTP_LIST_DETAIL_IDENTITY_SHA')
    print('PASS_STATUS_CKSMH_5_TWTC_39_ANDROID_44_EVIDENCE_SCOPED')
    print('PASS_STATUS_IBON_22_CANDIDATES_4_REJECTION_CAUSES_0_FIELDS')
    print('HOLD_STATUS_ONLY_DO_NOT_PUBLISH_EVENT_CANDIDATES')

def check_html(base):
    index=(base/'docs/index.html').read_text(encoding='utf-8')
    status=(base/'docs/platform-status.html').read_text(encoding='utf-8')
    assert index.count('href="platform-status.html"')==1
    assert index.count('fetch(')>=1
    assert 'data.json?t=' in index
    assert 'platform_status.json?v=' in status
    assert 'cache:"no-store"' in status
    assert 'textContent' in status
    assert 'document.getElementById("cards").replaceChildren' in status
    assert 'status.html' not in index.replace('platform-status.html','')
    assert 'innerHTML=' not in status
    assert status.count('<script>')==1
    print('PASS_STATUS_PWA_LINK_JSON_FETCH_SAFE_DOM_NO_EVENT_FEED_CHANGED')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--l7b',required=True)
    parser.add_argument('--l9b',required=True)
    parser.add_argument('--l9m',required=True)
    opts=parser.parse_args()
    root=Path('.')
    report=json.loads((root/'docs/platform_status.json').read_text(encoding='utf-8'))
    basic=json.loads(Path(opts.l7b).read_text(encoding='utf-8'))
    adapter=json.loads(Path(opts.l9b).read_text(encoding='utf-8'))
    recent=json.loads(Path(opts.l9m).read_text(encoding='utf-8'))
    check(report,basic,adapter,recent)
    check_html(root)
