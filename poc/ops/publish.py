#!/usr/bin/env python3
"""Copies the shareable part of this project to the shared copy, which teammates work from.

Only the paths in ops/publish-list.txt are copied. Run it through `make publish`.

  --dry-run          show what would change and change nothing
  NDL_POC_DIR=path   the shared copy; default is ndl-poc-sources beside the reference project

In the shared copy, only files that were published before are ever replaced or removed.
Its .git, .env, keys, data, exports and anything a teammate added are never touched.
"""
import argparse
import filecmp
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

POC = Path(__file__).resolve().parent.parent
LIST = POC / "ops" / "publish-list.txt"
RECORD = ".published.json"  # in the shared copy: the files the last publish put there
SKIP_NAMES = {"__pycache__", ".venv", "target", "logs", "dbt_packages"}
NEVER = re.compile(r"(^|/)(\.env(\..*)?|\.secrets|\.data|exports|\.git)(/|$)|\.(gpg|tar|tgz|age|parquet|avro|duckdb|wal|pem|key)$|(^|/)hash_key$")
SECRET_NAME = re.compile(r"(KEY|SECRET|PASS|TOKEN|CREDENTIAL)$")
LAKE_NAME = re.compile(r"(KEY|SECRET|PASS|TOKEN|CREDENTIAL|ENDPOINT|HOST|USER|URI)$")
NOTE = ("> This is the shared copy. Links to the planning papers, the exploration notes and the lake explorer "
        "have been removed, because those are kept by the project lead. Ask them for anything referred to here that you cannot find.")


def stop(message: str) -> None:
    sys.exit(f"publish: {message}")


def listed_files() -> list[Path]:
    """Every file named in the list, relative to the project folder."""
    files: list[Path] = []
    for line in LIST.read_text().splitlines():
        item = line.split("#")[0].strip()
        if not item:
            continue
        path = POC / item
        if not path.exists():
            stop(f"{item} is in publish-list.txt but does not exist")
        found = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
        files += [p.relative_to(POC) for p in found if not SKIP_NAMES & set(p.relative_to(POC).parts)]
    return sorted(set(files))


def secret_values() -> list[tuple[str, str]]:
    """Keys and passwords from the local settings, so no published file can carry one."""
    found = []
    for env_file in (POC / ".env", POC.parent / ".env"):
        if not env_file.is_file():
            continue
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            value = value.strip().strip("'\"")
            private = SECRET_NAME if env_file.parent == POC else LAKE_NAME  # the lake's address is private too
            if private.search(name.strip()) and len(value) >= 8:
                found.append((f"{name.strip()} in {env_file.parent.name}/{env_file.name}", value))
                host = re.sub(r"^[a-z]+://", "", value).split("/")[0].split(":")[0]
                if host != value and len(host) >= 8:
                    found.append((f"the host in {name.strip()}", host))
    hash_key = POC / ".secrets" / "hash_key"
    if hash_key.is_file():
        found.append(("the hash key", hash_key.read_text().strip()))
    return found


def without_private_links(doc: Path, stage: Path) -> int:
    """Turn links that point outside the shared copy into plain text. Returns how many."""
    removed = 0

    def swap(match: re.Match) -> str:
        nonlocal removed
        target = match.group(2).split("#")[0]
        if not target or re.match(r"[a-z]+:", target) or (doc.parent / target).resolve().is_relative_to(stage):
            return match.group(0)
        removed += 1
        return match.group(1)

    text = re.sub(r"\[([^\]]*)\]\(([^)\s]+)\)", swap, doc.read_text())
    if removed:
        lines = text.split("\n")
        title = next((i for i, line in enumerate(lines) if line.startswith("# ")), -1)
        lines[title + 1:title + 1] = ["", NOTE]
        doc.write_text("\n".join(lines))
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    dry = parser.parse_args().dry_run
    target = Path(os.environ.get("NDL_POC_DIR") or POC.parent.parent / "ndl-poc-sources").resolve()
    if not target.is_dir():
        stop(f"the shared copy is not at {target}. Create the folder, or set NDL_POC_DIR.")
    if target == POC or POC.is_relative_to(target) or target.is_relative_to(POC):
        stop("the shared copy must be a separate folder")

    print("Step 1 of 4: collecting the listed files", flush=True)
    files = listed_files()
    refused = [str(f) for f in files if NEVER.search(f.as_posix())]
    if refused:
        stop("these must never be published: " + ", ".join(refused))
    print(f"  {len(files)} files")

    with tempfile.TemporaryDirectory() as folder:
        stage = Path(folder).resolve()
        for f in files:
            (stage / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(POC / f, stage / f)

        print("Step 2 of 4: checking that no key is in them", flush=True)
        secrets = secret_values()
        for f in files:
            content = (stage / f).read_bytes()
            for name, value in secrets:
                if value.encode() in content:
                    stop(f"{f} contains the value of {name}. Nothing was published.")
        print(f"  none found ({len(secrets)} keys checked)")

        print("Step 3 of 4: removing links to the private folders from the documents", flush=True)
        for doc in sorted(stage.rglob("*.md")):
            removed = without_private_links(doc, stage)
            if removed:
                print(f"  {doc.relative_to(stage)}: {removed} links removed")

        print(f"Step 4 of 4: {'comparing with' if dry else 'updating'} {target}", flush=True)
        record = target / RECORD
        before = set(json.loads(record.read_text())["files"]) if record.is_file() else set()
        now = {f.as_posix() for f in files}
        changes = []
        for name in sorted(now):
            there = target / name
            if not there.exists():
                changes.append(("new", name))
            elif not filecmp.cmp(stage / name, there, shallow=False):
                changes.append(("changed", name))
        gone = sorted(name for name in before - now if (target / name).is_file())
        changes += [("removed", name) for name in gone]
        for kind, name in changes:
            print(f"  {kind:8} {name}")
            if dry:
                continue
            if kind == "removed":
                (target / name).unlink()
            else:
                (target / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(stage / name, target / name)
        if not changes:
            print("  nothing to change: the shared copy is up to date")
        if not dry:
            record.write_text(json.dumps({"files": sorted(now)}, indent=2) + "\n")

    if dry:
        print(f"Dry run: nothing was changed. {len(changes)} files would change.")
    else:
        print(f"Done: {len(changes)} files changed. Review with `git status` in {target}, then commit and push from there.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
