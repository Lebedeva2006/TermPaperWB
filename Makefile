run-server:
	uvicorn main:app --reload

pip-install:
	pip install -r requirements.txt

alembic-init:
	alembic init alembic

alembic-upgrade:
	alembic upgrade head

connect-db:
	psql -U sima -h localhost -p 5432 -d marketplace_db