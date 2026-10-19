#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image='mongo:7.0.16@sha256:c630c59342c1493d50345136df2af14a76b9e827dd5316bfabee07a0880a5f3a'
mkdir -p data/mongo
container='electricity-mongo-dev'
if docker container inspect electricity-mongo-dev >/dev/null 2>&1; then
  [[ $(docker inspect --format '{{index .Config.Labels "project"}}' electricity-mongo-dev) == electricity-load-analytics ]] || {
    echo 'Existing container is not owned by this project' >&2; exit 1;
  }
  docker start electricity-mongo-dev >/dev/null
elif docker container inspect fdc-mongo-dev >/dev/null 2>&1; then
  [[ $(docker inspect --format '{{index .Config.Labels "project"}}' fdc-mongo-dev) == fdc-track-b ]] || {
    echo 'Existing legacy MongoDB container is not owned by this project' >&2; exit 1;
  }
  container='fdc-mongo-dev'
  docker start "$container" >/dev/null
else
  docker run -d --name "$container" --label project=electricity-load-analytics \
    -p 127.0.0.1:27017:27017 \
    --mount "type=bind,source=$(pwd)/data/mongo,target=/data/db" "$image"
fi
for ((attempt=0; attempt<30; attempt++)); do
  if docker exec "$container" mongosh --quiet --eval 'quit(db.adminCommand({ping:1}).ok === 1 ? 0 : 1)' >/dev/null 2>&1; then
    echo 'MongoDB responds to ping on 127.0.0.1:27017'
    exit 0
  fi
  sleep 1
done
docker logs --tail 40 "$container" >&2
exit 1
