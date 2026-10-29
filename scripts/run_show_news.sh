#!/usr/bin/env bash
# V44: single-service launch, explicit opt-in for each channel. Default both OFF.
set -Eeuo pipefail
export EVENT_RADAR_TELEGRAM=0
export EVENT_RADAR_TERMUX=0
MODE='--once'
for arg in "$@"; do
  case "$arg" in
    --telegram) export EVENT_RADAR_TELEGRAM=1 ;;
    --termux) export EVENT_RADAR_TERMUX=1 ;;
    --once|--daemon|--version) MODE="$arg" ;;
    *) printf 'HOLD INVALID_OPTION %s\n' "$arg" >&2; exit 2 ;;
  esac
done
# [V44.2] Local, dependency-free version gate. Never runs the scraper or notifications.
if [[ "$MODE" == '--version' ]]; then
  REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
  python3 - "$REPO_DIR/show_news.py" <<'PY_VERSION'
import ast, pathlib, sys
p = pathlib.Path(sys.argv[1])
module = ast.parse(p.read_text(encoding='utf-8'))
versions = [ast.literal_eval(node.value) for node in module.body
            if isinstance(node, ast.Assign) and
            any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in node.targets)]
if len(versions) != 1 or not isinstance(versions[0], str):
    raise SystemExit('HOLD VERSION_NOT_UNIQUE')
print('EVENT_RADAR_VERSION=' + versions[0])
PY_VERSION
  if command -v git >/dev/null 2>&1 && git -C "$REPO_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf 'GIT_BRANCH=%s\n' "$(git -C "$REPO_DIR" branch --show-current)"
    printf 'GIT_HEAD=%s\n' "$(git -C "$REPO_DIR" rev-parse HEAD)"
    if [[ -n "$(git -C "$REPO_DIR" status --porcelain --untracked-files=no)" ]]; then
      echo 'GIT_WORKTREE=MODIFIED_OR_STAGED'
    else
      echo 'GIT_WORKTREE=CLEAN'
    fi
  fi
  echo 'PASS EVENT_RADAR_VERSION_READONLY'
  exit 0
fi
if [[ "$EVENT_RADAR_TELEGRAM" == 1 ]] && { [[ -z "${TG_BOT_TOKEN:-}" ]] || [[ -z "${TG_CHAT_ID:-}" ]]; }; then
  echo 'HOLD TELEGRAM_SECRETS_MISSING (do not print credentials)' >&2
  exit 3
fi
if [[ "$EVENT_RADAR_TERMUX" == 1 ]] && ! command -v termux-notification >/dev/null 2>&1; then
  echo 'HOLD TERMUX_API_MISSING' >&2
  exit 4
fi
if [[ "${GITHUB_ACTIONS:-}" == 'true' && "$MODE" == '--daemon' ]]; then
  echo 'HOLD NO_DAEMON_ON_CI' >&2
  exit 5
fi
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$REPO_DIR"
echo "START EVENT_RADAR_V44 mode=$MODE telegram=$EVENT_RADAR_TELEGRAM termux=$EVENT_RADAR_TERMUX"
exec python3 -u show_news.py "$MODE"
