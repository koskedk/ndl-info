# Commands for whoever samples from DHA's lake and publishes the shared copy.
# They need the VPN and the lake explorer beside this folder. This file is not published.
.PHONY: check-rules measure sample verify-sample publish publish-dry-run

check-rules:  ## Check that every text column the sampler copies has a rule
	@python3 source-sample/check_rules.py

measure: check-rules  ## Show how many source files each table needs; copies nothing (VPN)
	@cd source-sample && env -u VIRTUAL_ENV uv run python sampler.py measure $(if $(ONLY),--only $(ONLY))

sample: check-rules up  ## Copy the sampled facilities from the real S3 Ceph into the stand-in (VPN)
	@cd source-sample && env -u VIRTUAL_ENV uv run python sampler.py sample $(if $(ONLY),--only $(ONLY))

verify-sample:  ## Count the same rows on the real S3 Ceph and compare with the sample (VPN)
	@cd source-sample && env -u VIRTUAL_ENV uv run python sampler.py verify $(if $(ONLY),--only $(ONLY))

publish-dry-run:  ## Show what `make publish` would change in the shared copy, and change nothing
	@python3 ops/publish.py --dry-run

publish:  ## Copy the files listed in ops/publish-list.txt to the shared copy (ndl-poc-sources)
	@python3 ops/publish.py
