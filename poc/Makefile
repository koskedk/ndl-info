# NHAI proof of concept. Run `make help` for the list.
.DEFAULT_GOAL := help
.PHONY: help init up down tables browse-rows export-source import-source reset-source purge purge-dry-run

TOOLS = env -u VIRTUAL_ENV uv run --project tools python tools/standin.py

help:  ## Show the commands
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-16s %s\n", $$1, $$2}'

init:  ## Create local settings and keys (.env, .secrets); safe to run again
	@./ops/init_env.sh

up: init  ## Start the core services
	@docker compose --profile core up -d

down:  ## Stop the services; data is kept
	@docker compose --profile core down

tables: up  ## List the tables in the stand-in S3 Ceph, with row counts
	@$(TOOLS) tables

browse-rows: up  ## Open a web page for reading rows in the stand-in with SQL; Ctrl+C stops it
	@$(TOOLS) browse

export-source: up  ## Write the whole stand-in to one encrypted file under exports/, to hand to a teammate
	@$(TOOLS) export

import-source: up  ## Replace the stand-in with an export: make import-source FILE=path/to/standin-....tar.gpg
	@test -n "$(FILE)" || { echo "Give the export file: make import-source FILE=path/to/standin-....tar.gpg"; exit 1; }
	@$(TOOLS) import "$(FILE)"

reset-source:  ## Delete only the stand-in S3 Ceph and what it holds
	@docker compose --profile core rm -sf standin-browser standin-s3
	@docker volume rm -f "$$(docker compose --profile core config --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["volumes"]["standin_data"]["name"])')"

purge-dry-run:  ## List what `make purge` would remove, and remove nothing
	@DRY_RUN=1 ./purge.sh

purge:  ## Remove every copy of the data from this machine (asks first)
	@./purge.sh

# Commands for whoever samples from DHA's lake. They need the VPN and are not in the shared copy.
-include lead.mk
