.PHONY: all build run test clean-start rollback

SHELL := /bin/bash
PORT ?= 8080
HOST ?= 127.0.0.1
APP_VERSION ?= v1.0.0
DEPENDENCY_PATH ?= data/dependency.ok

all: build test

build:
	python -m pip install --upgrade pip
	python -m pip install -r requirements.txt

run:
	PORT=$(PORT) HOST=$(HOST) APP_VERSION=$(APP_VERSION) DEPENDENCY_PATH=$(DEPENDENCY_PATH) python -m app.main

test:
	pytest -v

clean-start:
	bash scripts/clean_start.sh

rollback:
	git checkout v1.0.0
	pytest -v
