#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

NEO4J_PASSWORD="${NEO4J_PASSWORD:-axkg2026}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.neo4j.yml}"
CONTAINER="${CONTAINER:-ax-kg-neo4j}"
IMPORT_CYPHER="/var/lib/neo4j/import/neo4j_import.cypher"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not available in PATH." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  cat >&2 <<'EOF'
Docker is installed, but the current user cannot access the Docker daemon.

Typical fixes:
  1. Ask the server admin to add this user to the docker group, then reconnect:
       sudo usermod -aG docker "$USER"

  2. If you have sudo permission, run this script with sudo:
       sudo -E NEO4J_PASSWORD=axkg2026 bash scripts/start_neo4j_kg.sh

After group changes, fully disconnect and reconnect your SSH/VS Code session.
EOF
  exit 1
fi

if [[ ! -f outputs/11_neo4j_import/neo4j_import.cypher ]]; then
  echo "Neo4j import package not found. Generating it first..."
  /home/minjoo/tdpo2_aaai2027/.venv_tdpo2/bin/python scripts/export_kg_to_neo4j.py \
    --outputs-dir outputs \
    --out-dir outputs/11_neo4j_import
fi

docker compose -f "$COMPOSE_FILE" up -d

echo "Waiting for Neo4j to accept Cypher connections..."
for _ in $(seq 1 90); do
  if docker exec "$CONTAINER" cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

docker exec "$CONTAINER" cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" >/dev/null

echo "Importing KG CSV files into Neo4j..."
docker exec "$CONTAINER" cypher-shell -u neo4j -p "$NEO4J_PASSWORD" -f "$IMPORT_CYPHER"

echo
echo "Neo4j is ready."
echo "Browser: http://localhost:7474"
echo "Bolt: bolt://localhost:7687"
echo "User: neo4j"
echo "Password: $NEO4J_PASSWORD"
