#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  fallback_monitor_control.sh --control <control.md> --owner <owner> --status <status> [options]

Options:
  --control <path>       Absolute or relative path to control.md. Required.
  --owner <owner>        Owner value to wake on, such as executor or orchestrator. Required.
  --status <status>      Status value to wake on, such as awaiting-executor. Required.
  --interval <seconds>   Poll interval. Default: 5.
  --log <path>           Log path. Default: <control-dir>/terminal/monitors/fallback-monitor-control.log.
  --pid-file <path>      Optional pid file to write.
  --exit-statuses <csv>  Statuses that stop the monitor. Default: complete,user-decision-needed.
  --help                 Show this help.

The script is a fallback only. Prefer Codex automations in Codex and Claude
Code Monitor in Claude Code. It never edits control.md; it only logs wake-up
events when Owner and Status match the requested values.
EOF
}

control_path=""
watch_owner=""
watch_status=""
interval="5"
log_path=""
pid_file=""
exit_statuses="complete,user-decision-needed"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --control)
      control_path="${2:-}"
      shift 2
      ;;
    --owner)
      watch_owner="${2:-}"
      shift 2
      ;;
    --status)
      watch_status="${2:-}"
      shift 2
      ;;
    --interval)
      interval="${2:-}"
      shift 2
      ;;
    --log)
      log_path="${2:-}"
      shift 2
      ;;
    --pid-file)
      pid_file="${2:-}"
      shift 2
      ;;
    --exit-statuses)
      exit_statuses="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$control_path" || -z "$watch_owner" || -z "$watch_status" ]]; then
  usage >&2
  exit 2
fi

if ! [[ "$interval" =~ ^[0-9]+$ ]] || [[ "$interval" -lt 1 ]]; then
  echo "--interval must be a positive integer" >&2
  exit 2
fi

control_dir="$(cd "$(dirname "$control_path")" && pwd)"
control_file="$control_dir/$(basename "$control_path")"

if [[ -z "$log_path" ]]; then
  log_path="$control_dir/terminal/monitors/fallback-monitor-control.log"
fi

mkdir -p "$(dirname "$log_path")"

if [[ -n "$pid_file" ]]; then
  mkdir -p "$(dirname "$pid_file")"
  printf '%s\n' "$$" > "$pid_file"
fi

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log() {
  printf '%s %s\n' "$(timestamp)" "$*" >> "$log_path"
}

field() {
  local name="$1"
  awk -F: -v key="$name" '
    $1 == key {
      value = substr($0, index($0, ":") + 1)
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      print value
      exit
    }
  ' "$control_file" 2>/dev/null || true
}

status_is_terminal() {
  local status="$1"
  local old_ifs="$IFS"
  local item
  IFS=","
  for item in $exit_statuses; do
    if [[ "$status" == "$item" ]]; then
      IFS="$old_ifs"
      return 0
    fi
  done
  IFS="$old_ifs"
  return 1
}

cleanup() {
  if [[ -n "$pid_file" && -f "$pid_file" ]]; then
    rm -f "$pid_file"
  fi
}
trap cleanup EXIT

log "started control=$control_file owner=$watch_owner status=$watch_status interval=${interval}s"

last_seen_key=""
last_wake_key=""

while true; do
  if [[ ! -f "$control_file" ]]; then
    key="missing"
    if [[ "$key" != "$last_seen_key" ]]; then
      log "waiting control-file-missing path=$control_file"
      last_seen_key="$key"
    fi
    sleep "$interval"
    continue
  fi

  owner="$(field Owner)"
  status="$(field Status)"
  phase="$(field Phase)"
  target="$(field Target)"
  next_action="$(field "Next action")"
  updated_at="$(field "Updated at")"

  key="$owner|$status|$phase|$target|$next_action|$updated_at"
  if [[ "$key" != "$last_seen_key" ]]; then
    log "state owner=$owner status=$status phase=$phase target=$target next_action=$next_action updated_at=$updated_at"
    last_seen_key="$key"
  fi

  if status_is_terminal "$status"; then
    log "terminal status=$status; exiting"
    exit 0
  fi

  if [[ "$owner" == "$watch_owner" && "$status" == "$watch_status" ]]; then
    if [[ "$key" != "$last_wake_key" ]]; then
      log "wake owner=$owner status=$status phase=$phase target=$target next_action=$next_action updated_at=$updated_at"
      last_wake_key="$key"
    fi
  fi

  sleep "$interval"
done
