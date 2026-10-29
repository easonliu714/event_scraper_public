#!/usr/bin/env bash
# Only allow the GitHub Actions runner to write docs/data.json. No force or merge.
set -Eeuo pipefail
[[ "${GITHUB_ACTIONS:-}" == 'true' ]] || { echo 'HOLD NOT_GITHUB_ACTIONS'; exit 10; }
[[ "${GITHUB_REPOSITORY:-}" == 'easonliu714/event_scraper_public' ]] || { echo 'HOLD WRONG_REPO'; exit 11; }
[[ "${GITHUB_REF:-}" == 'refs/heads/main' ]] || { echo 'HOLD WRONG_REF'; exit 12; }
[[ "$(git branch --show-current)" == 'main' ]] || { echo 'HOLD WRONG_LOCAL_BRANCH'; exit 13; }
python3 scripts/validate_data.py
# V44.1: show each platform's populated field ratio before publication.
python3 scripts/audit_quality.py
git fetch --no-tags origin main
remote_sha="$(git rev-parse FETCH_HEAD)"
local_sha="$(git rev-parse HEAD)"
[[ "$remote_sha" == "$local_sha" ]] || { echo 'HOLD REMOTE_MAIN_DRIFT'; exit 14; }
# Only stage the output. Ignore all runtime records and secret files.
git add -- docs/data.json
if git diff --cached --quiet; then echo 'PASS NO_DATA_CHANGE'; exit 0; fi
git diff --cached --name-only | grep -Fx 'docs/data.json' >/dev/null || { echo 'HOLD UNEXPECTED_STAGED_FILE'; exit 15; }
[[ "$(git diff --cached --name-only | wc -l)" -eq 1 ]] || { echo 'HOLD MULTIPLE_STAGED_FILES'; exit 16; }
git -c user.name='github-actions[bot]' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' commit -m "EventRadar V44 automatic update $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
git push origin HEAD:main
expected="$(git rev-parse HEAD)"
actual="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
[[ "$actual" == "$expected" ]] || { echo 'HOLD REMOTE_READBACK_SHA_MISMATCH'; exit 17; }
echo "PASS V44_PUBLISH_AND_REMOTE_READBACK SHA=$actual"
