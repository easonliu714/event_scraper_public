#!/usr/bin/env python3
"""V44 cloud publish gate: never publish stale, empty, or badly shaped output."""
import json, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse
p=Path('docs/data.json')
try:
    rows=json.loads(p.read_text(encoding='utf-8'))
    assert isinstance(rows,list) and len(rows)>=20, 'MIN_EVENTS'
    valid=[e for e in rows if isinstance(e,dict) and e.get('title') and e.get('url') and e.get('platform')]
    assert len(valid)==len(rows), 'ROW_SHAPE'
    assert len({e['url'] for e in valid})==len(valid), 'DUPLICATE_URL'
    assert all(urlparse(e['url']).scheme=='https' and urlparse(e['url']).hostname for e in valid), 'URL_SCHEME'
    def fresh(e):
        try:
            d=datetime.fromisoformat(e.get('scraped_at',''))
            return d.tzinfo is not None and timedelta(0)<=datetime.now(timezone.utc)-d.astimezone(timezone.utc)<=timedelta(hours=2)
        except (ValueError,TypeError,OverflowError):return False
    fresh_rows=[e for e in valid if fresh(e)]
    assert len(fresh_rows)>=20, 'RECENT_ROWS_LT_20'
    assert len({e['platform'] for e in fresh_rows})>=3, 'RECENT_PLATFORMS_LT_3'
    print(f'PASS V44_DATA_GATE total={len(valid)} fresh={len(fresh_rows)} platforms={len({e["platform"] for e in fresh_rows})}')
except Exception as exc:
    print(f'HOLD V44_DATA_GATE {str(exc)}',file=sys.stderr)
    sys.exit(4)
