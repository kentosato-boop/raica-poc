.PHONY: install dev-api dev-web test build docker

install:
	python3 -m venv .venv
	.venv/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm install

dev-api:
	.venv/bin/uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000

dev-web:
	cd frontend && npm run dev

test:
	PYTHONPATH=backend .venv/bin/pytest backend/tests
	cd frontend && npm run build

build:
	cd frontend && npm run build

docker:
	docker compose up --build
