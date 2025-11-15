PYTHON ?= python3
PORT ?= 8080
APP_MODULE ?= app.main:app
IMAGE_NAME ?= offer-ranker-api

.PHONY: train run-local test docker-build docker-run

train:
	$(PYTHON) -m scripts.train_model

run-local:
	uvicorn $(APP_MODULE) --host 0.0.0.0 --port $(PORT)

test:
	pytest

docker-build:
	docker build -t $(IMAGE_NAME):local .

docker-run:
	docker run --rm -p $(PORT):$(PORT) -e PORT=$(PORT) $(IMAGE_NAME):local
