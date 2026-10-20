#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project="kestrel-compose-smoke-${GITHUB_RUN_ID:-local}"
tmp="$(mktemp -d)"
export KESTREL_DATA_DIR="$tmp/data"
export KESTREL_UID="$(id -u)"
export KESTREL_GID="$(id -g)"
mkdir -p "$KESTREL_DATA_DIR"

compose() {
  docker compose -p "$project" -f "$root/compose.yaml" "$@"
}

cleanup() {
  docker compose -p "$project" -f "$root/compose.yaml" -f "$root/compose.ssi.yaml" down --remove-orphans >/dev/null 2>&1 || true
  compose down --remove-orphans >/dev/null 2>&1 || true
  rm -rf "$tmp"
}
trap cleanup EXIT

compose config -q
compose -f "$root/compose.dev.yaml" config -q
compose up -d --build

wait_healthy() {
  local id status
  id="$(compose ps -q kestrel)"
  for _ in $(seq 1 120); do
    status="$(docker inspect --format '{{.State.Health.Status}}' "$id")"
    if [[ "$status" == "healthy" ]]; then
      curl --fail --silent http://127.0.0.1:8080/api/v1/ready >/dev/null
      return
    fi
    if [[ "$status" == "unhealthy" ]]; then
      compose logs
      return 1
    fi
    sleep 1
  done
  compose logs
  echo "Kestrel did not become healthy" >&2
  return 1
}

wait_healthy
container="$(compose ps -q kestrel)"
host_ip="$(docker inspect --format '{{(index (index .HostConfig.PortBindings "8080/tcp") 0).HostIp}}' "$container")"
[[ "$host_ip" == "127.0.0.1" ]]
[[ -s "$KESTREL_DATA_DIR/kestrel.sqlite" ]]

compose down
[[ -s "$KESTREL_DATA_DIR/kestrel.sqlite" ]]
compose up -d
wait_healthy

secret_file="$tmp/ssi-secret.json"
printf '{"ConsumerID":"fixture-id","ConsumerSecret":"compose-secret-sentinel"}' > "$secret_file"
chmod 600 "$secret_file"
export KESTREL_SSI_SECRET_FILE="$secret_file"
compose -f "$root/compose.ssi.yaml" config -q
compose -f "$root/compose.ssi.yaml" up -d
wait_healthy
if compose logs 2>&1 | grep -Fq 'compose-secret-sentinel'; then
  echo "SSI secret sentinel appeared in container logs" >&2
  exit 1
fi
