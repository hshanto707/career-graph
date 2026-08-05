.PHONY: run db-clean db-nuke clean

# Bring up the full stack (Postgres, Neo4j, API) in the foreground.
run:
	docker compose up

# Wipe all data from Postgres and Neo4j, keeping schema/containers/volumes
# intact. Fast -- no restart needed.
db-clean:
	docker compose exec backend python scripts/reset_db.py

clean: db-clean

# Full teardown: drops the Postgres/Neo4j volumes entirely, recreates the
# stack, and reapplies migrations from scratch. Use when db-clean isn't
# enough (e.g. suspected schema/volume corruption).
db-nuke:
	docker compose down -v
	docker compose up -d
	docker compose exec backend alembic upgrade head
