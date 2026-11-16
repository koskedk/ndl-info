# NHAI proof of concept. Run `make help` for the list.
.DEFAULT_GOAL := help
.PHONY: help init up down check-rules measure sample verify-sample reset-source purge purge-dry-run

help:  ## Show the commands
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-15s %s\n", $$1, $$2}'

init:  ## Create local settings and keys (poc/.env, poc/.secrets); safe to run again
	@./ops/init_env.sh

up: init  ## Start the core services
	@docker compose --profile core up -d

down:  ## Stop the services; data is kept
	@docker compose --profile core down

check-rules:  ## Check that every text column the sampler copies has a rule
	@python3 source-sample/check_rules.py

measure: check-rules  ## Show how many source files each table needs; copies nothing (VPN)
	@cd source-sample && env -u VIRTUAL_ENV uv run python sampler.py measure

sample: check-rules up  ## Copy the sampled facilities from the real S3 Ceph into the stand-in (VPN)
	@cd source-sample && env -u VIRTUAL_ENV uv run python sampler.py sample

verify-sample:  ## Count the same rows on the real S3 Ceph and compare with the sample (VPN)
	@cd source-sample && env -u VIRTUAL_ENV uv run python sampler.py verify

reset-source:  ## Delete only the stand-in S3 Ceph and its sample
	@docker compose --profile core rm -sf standin-s3 && docker volume rm -f nhai-poc_standin_data

purge-dry-run:  ## List what `make purge` would remove, and remove nothing
	@DRY_RUN=1 ./purge.sh

purge:  ## Remove every copy of the data from this machine (asks first)
	@./purge.sh
