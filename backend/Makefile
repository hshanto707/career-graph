.PHONY: run db-clean db-nuke clean seed

# Bring up the full stack (Postgres, Neo4j, API) in the foreground.
run:
	docker compose up

# Wipe all data from Postgres and Neo4j, keeping schema/containers/volumes
# intact. Fast -- no restart needed.
db-clean:
	docker compose exec backend python scripts/reset_db.py

clean: db-clean

# Seed Neo4j with the full 10k-job dataset (~9.4k jobs, 434 skills, 55k
# skill edges) -- the default demo seed only loads ~50 jobs, which is too
# small for skill-name/target-role autocomplete to cover most IT skills.
# Run after db-clean/db-nuke so the graph isn't empty.
seed:
	docker compose exec backend python -c "\
from app.services.graph_service import GraphService; \
from app.database.neo4j import get_driver; \
from app.etl.seed_demo_data import run_seed; \
gs = GraphService(get_driver()); \
gs.ensure_constraints(); \
summary = run_seed(gs, job_count=10000); \
print('Seed complete:', summary)"

# Full teardown: drops the Postgres/Neo4j volumes entirely, recreates the
# stack, and reapplies migrations from scratch. Use when db-clean isn't
# enough (e.g. suspected schema/volume corruption).
db-nuke:
	docker compose down -v
	docker compose up -d
	docker compose exec backend alembic upgrade head
