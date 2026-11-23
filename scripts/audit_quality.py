#!/usr/bin/env python3
"""V44.1 read-only detail coverage audit; field presence is NOT factual correctness."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

FIELDS = ('date', 'location', 'price', 'description')
PLACEHOLDERS = {'', '詳內文', 'None', 'null', 'undefined',
                '詳細資訊請點擊連結查看。', '暫無詳細簡介，請點擊下方按鈕前往官網查看。'}

def populated(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip() not in PLACEHOLDERS

def audit(path):
    rows = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(rows, list):
        raise ValueError('EVENT_DATA_NOT_LIST')
    per_platform = defaultdict(lambda: Counter())
    bad_url = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        platform = str(row.get('platform') or 'UNKNOWN')
        stats = per_platform[platform]
        stats['rows'] += 1
        url = urlsplit(str(row.get('url', '')))
        if url.scheme != 'https' or not url.hostname:
            bad_url += 1
        for field in FIELDS:
            if populated(row.get(field)):
                stats[field] += 1
    print('START V44_1_FIELD_COVERAGE_AUDIT (presence only; not live-site accuracy)')
    for platform, counts in sorted(per_platform.items()):
        n = counts['rows']
        percentages = ' '.join(
            f'{field}={counts[field]}/{n}({100*counts[field]/n:.1f}%)'
            for field in FIELDS
        )
        print(f'PLATFORM {platform}: rows={n} {percentages}')
    print(f'PASS V44_1_FIELD_COVERAGE_AUDIT rows={len(rows)} platforms={len(per_platform)} invalid_url={bad_url}')
    return len(rows), len(per_platform), bad_url

if __name__ == '__main__':
    try:
        audit(sys.argv[1] if len(sys.argv) > 1 else 'docs/data.json')
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
        print(f'HOLD V44_1_FIELD_COVERAGE_AUDIT {type(e).__name__}', file=sys.stderr)
        sys.exit(4)
