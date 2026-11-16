#!/usr/bin/env python3
"""Tools for the stand-in S3 Ceph on this laptop. Run them through make, from the project folder.

  tables          list the tables in the stand-in with their row counts
  browse          open a web page for reading rows with SQL
  export          write the whole stand-in to one encrypted file, to hand to a teammate
  import FILE     replace this laptop's stand-in with the contents of such a file

The stand-in holds real patient records. An export holds them too: it is encrypted with a
passphrase, and no unencrypted copy is written to disk on the way out or the way in.
"""
from __future__ import annotations

import argparse
import csv
import getpass
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from pyarrow import fs as pafs

HERE = Path(__file__).resolve().parent
POC = HERE.parent
EXPORTS = POC / "exports"
MANIFESTS = POC / "source-sample" / "manifests"
SOURCE_FOLDERS = POC / "source-sample" / "source-folders.csv"
FORMAT = 1
SUMMARY = "export.json"
MIN_PASSPHRASE = 12


def say(message: str = "") -> None:
    print(message, flush=True)


def stop(message: str) -> None:
    sys.exit(f"Stopped: {message}")


def mb(n: int) -> str:
    return f"{n / 1024 / 1024:,.1f} MB"


# -- settings and connections ------------------------------------------------------

def settings() -> dict[str, str]:
    env_file = POC / ".env"
    if not env_file.is_file():
        stop("no .env file here yet. Run `make up` first; it creates the local settings and keys.")
    values = {k: v for k, v in dotenv_values(env_file).items() if v is not None}
    values.update({k: v for k, v in os.environ.items() if k.startswith("STANDIN_")})
    return values


def bucket_name(s: dict) -> str:
    return s["STANDIN_S3_BUCKETS"].split(",")[0].strip()


def keys(s: dict, write: bool) -> tuple[str, str]:
    if write:
        return s["STANDIN_S3_WRITE_ACCESS_KEY"], s["STANDIN_S3_WRITE_SECRET_KEY"]
    return s["STANDIN_S3_ACCESS_KEY"], s["STANDIN_S3_SECRET_KEY"]


def filesystem(s: dict, write: bool = False) -> pafs.S3FileSystem:
    """The stand-in. Reads use the key that can only list and read; only import uses the other one."""
    access, secret = keys(s, write)
    endpoint = s["STANDIN_S3_ENDPOINT"]
    return pafs.S3FileSystem(
        access_key=access, secret_key=secret,
        endpoint_override=re.sub(r"^https?://", "", endpoint).rstrip("/"),
        scheme="https" if endpoint.startswith("https") else "http",
        region=s.get("STANDIN_S3_REGION") or "us-east-1",
        force_virtual_addressing=False, allow_bucket_creation=write,
    )


def list_objects(fs: pafs.S3FileSystem, bucket: str) -> list[tuple[str, int]]:
    """Every file in the bucket as (bucket/key, size). Empty when the bucket is not there yet."""
    try:
        found = fs.get_file_info(pafs.FileSelector(bucket, recursive=True, allow_not_found=True))
    except OSError as exc:
        if "NoSuchBucket" in str(exc) or "NO_SUCH_BUCKET" in str(exc) or "404" in str(exc):
            return []
        raise
    return sorted((f.path, f.size or 0) for f in found if f.type == pafs.FileType.File)


# -- tables --------------------------------------------------------------------------

def short_names() -> dict[str, str]:
    """Folder name in the bucket -> the short name used in SQL, from source-folders.csv."""
    if not SOURCE_FOLDERS.is_file():
        return {}
    return {row["folder"]: row["source"] for row in csv.DictReader(SOURCE_FOLDERS.open())}


def find_tables(objects: list[tuple[str, int]]) -> list[dict]:
    """Tables are folders holding metadata/NNNNN-<id>.metadata.json. The highest number is current."""
    names = short_names()
    newest: dict[str, tuple[int, str]] = {}
    sizes: dict[str, int] = {}
    for path, size in objects:
        match = re.match(r"(.+)/(metadata|data)/([^/]+)$", path)
        if not match:
            continue
        root, kind, name = match.groups()
        if kind == "data":
            sizes[root] = sizes.get(root, 0) + size
            continue
        version = re.match(r"(\d+)-.*\.metadata\.json$", name)
        if version and (root not in newest or int(version.group(1)) > newest[root][0]):
            newest[root] = (int(version.group(1)), path)
    tables = []
    for root, (_, metadata) in sorted(newest.items()):
        folder, table = root.rsplit("/", 2)[-2:]
        source = names.get(folder, re.sub(r"\W", "_", folder))
        tables.append({"source": source, "table": table, "root": root, "metadata": metadata, "bytes": sizes.get(root, 0)})
    return tables


def find_plain_files(objects: list[tuple[str, int]], tables: list[dict]) -> list[dict]:
    """Plain Parquet files that belong to no Iceberg table (the KHIS figures).

    Each file name under a top folder is treated as one table: khis/.../khis_data.parquet in
    every indicator folder together make khis.khis_data.
    """
    roots = tuple(t["root"] + "/" for t in tables)
    names = short_names()
    found: dict[tuple[str, str], dict] = {}
    for path, size in objects:
        parts = path.split("/")
        if not path.endswith(".parquet") or len(parts) < 3 or (roots and path.startswith(roots)):
            continue
        source = names.get(parts[1], re.sub(r"\W", "_", parts[1]))
        table = parts[-1][: -len(".parquet")]
        entry = found.setdefault((source, table), {"source": source, "table": table, "root": f"{parts[0]}/{parts[1]}",
                                                   "metadata": None, "bytes": 0, "files": []})
        entry["files"].append(path)
        entry["bytes"] += size
    return [found[key] for key in sorted(found)]


def current_files(s: dict, table: dict) -> tuple[list[str], int]:
    """The data files of the table's current state, and its row count, from the table's own records."""
    from pyiceberg.table import StaticTable

    access, secret = keys(s, write=False)
    opened = StaticTable.from_metadata(f"s3://{table['metadata']}", properties={
        "s3.endpoint": s["STANDIN_S3_ENDPOINT"], "s3.access-key-id": access, "s3.secret-access-key": secret,
        "s3.region": s.get("STANDIN_S3_REGION") or "us-east-1", "s3.force-virtual-addressing": "false",
        "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO",
    })
    tasks = list(opened.scan().plan_files())
    if any(task.delete_files for task in tasks):
        stop(f"{table['source']}.{table['table']} has row-level deletes, which these tools do not handle.")
    files = [task.file.file_path.removeprefix("s3://").removeprefix("s3a://") for task in tasks]
    return files, sum(task.file.record_count for task in tasks)


def describe(s: dict, objects: list[tuple[str, int]], progress: bool = True) -> list[dict]:
    """Every table with its files and row count."""
    tables = find_tables(objects)
    plain = find_plain_files(objects, tables)
    total = len(tables) + len(plain)
    for number, table in enumerate(tables, 1):
        table["files"], table["rows"] = current_files(s, table)
        if progress:
            say(f"  {number}/{total} {table['source']}.{table['table']}: {table['rows']:,} rows")
    if plain:
        import pyarrow.parquet as pq

        fs = filesystem(s)
        for number, table in enumerate(plain, len(tables) + 1):
            table["rows"] = sum(pq.read_metadata(path, filesystem=fs).num_rows for path in table["files"])
            if progress:
                say(f"  {number}/{total} {table['source']}.{table['table']}: {table['rows']:,} rows")
    return tables + plain


def connect(s: dict):
    """DuckDB, given the read-only key so it reads the stand-in's files itself."""
    import duckdb

    quote = lambda v: "'" + str(v).replace("'", "''") + "'"
    access, secret = keys(s, write=False)
    endpoint = s["STANDIN_S3_ENDPOINT"]
    con = duckdb.connect()
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    con.execute(
        f"CREATE OR REPLACE SECRET standin (TYPE s3, KEY_ID {quote(access)}, SECRET {quote(secret)}, "
        f"ENDPOINT {quote(re.sub(r'^https?://', '', endpoint).rstrip('/'))}, REGION {quote(s.get('STANDIN_S3_REGION') or 'us-east-1')}, "
        f"URL_STYLE 'path', USE_SSL {'true' if endpoint.startswith('https') else 'false'})"
    )
    return con


def read_sql(table: dict) -> str:
    listed = ", ".join("'s3://" + f.replace("'", "''") + "'" for f in table["files"])
    return f"read_parquet([{listed}], union_by_name=true)"


def cmd_tables(args) -> int:
    s = settings()
    objects = list_objects(filesystem(s), bucket_name(s))
    if not objects:
        say("The stand-in is empty. Use `make import-source FILE=...` to fill it.")
        return 0
    tables = describe(s, objects, progress=False)
    width = max(len(f"{t['source']}.{t['table']}") for t in tables)
    say(f"{'table'.ljust(width)}  {'rows':>12}  {'files':>5}  {'size':>10}")
    for t in tables:
        say(f"{(t['source'] + '.' + t['table']).ljust(width)}  {t['rows']:>12,}  {len(t['files']):>5}  {mb(t['bytes']):>10}")
    say(f"{'total'.ljust(width)}  {sum(t['rows'] for t in tables):>12,}  {sum(len(t['files']) for t in tables):>5}  {mb(sum(t['bytes'] for t in tables)):>10}")
    return 0


def cmd_browse(args) -> int:
    s = settings()
    say("Step 1 of 2: finding the tables")
    objects = list_objects(filesystem(s), bucket_name(s))
    if not objects:
        stop("the stand-in is empty. Use `make import-source FILE=...` to fill it.")
    tables = describe(s, objects)
    say("Step 2 of 2: starting the page")
    con = connect(s)
    for t in tables:
        if not t["files"]:
            continue
        con.execute(f'CREATE SCHEMA IF NOT EXISTS "{t["source"]}"')
        con.execute(f'CREATE OR REPLACE VIEW "{t["source"]}"."{t["table"]}" AS SELECT * FROM {read_sql(t)}')
    port = int(s.get("STANDIN_ROWS_PORT") or 4213)
    con.execute("INSTALL ui")
    con.execute("LOAD ui")
    con.execute(f"SET ui_local_port={port}")
    con.execute("CALL start_ui_server()")
    say(f"\n{len(tables)} tables ready. Open http://localhost:{port}/")
    say("Tables are under the `memory` database, one group per source system. They hold real names and identifiers.")
    say("Press Ctrl+C here to stop.")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        say("Stopped.")
    return 0


# -- the passphrase and gpg ------------------------------------------------------------

def passphrase(confirm: bool) -> str:
    given = os.environ.get("STANDIN_EXPORT_PASSPHRASE")
    if given is None:
        given = getpass.getpass("Passphrase for the export: ")
        if confirm and getpass.getpass("Type it again: ") != given:
            stop("the two passphrases differ. Nothing was written.")
    if confirm and len(given) < MIN_PASSPHRASE:
        stop(f"the passphrase must be at least {MIN_PASSPHRASE} characters. Nothing was written.")
    return given


def gpg(arguments: list[str], secret: str, **pipes) -> subprocess.Popen:
    """Start gpg with the passphrase handed over on a pipe, so it is never on the command line or on disk."""
    if shutil.which("gpg") is None:
        stop("gpg is not installed. Install GnuPG (Ubuntu: sudo apt install gnupg; macOS: brew install gnupg).")
    read_end, write_end = os.pipe()
    process = subprocess.Popen(
        ["gpg", "--batch", "--yes", "--quiet", "--no-tty", "--pinentry-mode", "loopback", "--passphrase-fd", str(read_end), *arguments],
        pass_fds=(read_end,), **pipes)
    os.close(read_end)
    with os.fdopen(write_end, "w") as pipe:
        pipe.write(secret + "\n")
    return process


# -- export ----------------------------------------------------------------------------

def cmd_export(args) -> int:
    s = settings()
    bucket = bucket_name(s)
    fs = filesystem(s)
    say("Step 1 of 3: reading what the stand-in holds")
    objects = list_objects(fs, bucket)
    if not objects:
        stop("the stand-in is empty, so there is nothing to export.")
    tables = describe(s, objects)
    total = sum(size for _, size in objects)
    say(f"  {len(tables)} tables, {sum(t['rows'] for t in tables):,} rows, {len(objects):,} files, {mb(total)}")

    say("Step 2 of 3: choosing the passphrase")
    secret = passphrase(confirm=True)

    os.umask(0o077)
    EXPORTS.mkdir(exist_ok=True)
    made = datetime.now(timezone.utc)
    out = EXPORTS / f"standin-{datetime.now().strftime('%Y-%m-%d-%H%M')}.tar.gpg"
    summary = json.dumps({
        "format": FORMAT, "made_at": made.strftime("%Y-%m-%dT%H:%M:%SZ"), "bucket": bucket,
        "files": len(objects), "bytes": total,
        "tables": [{"source": t["source"], "table": t["table"], "rows": t["rows"], "root": t["root"]} for t in tables],
    }, indent=2).encode()

    say(f"Step 3 of 3: writing {out.relative_to(POC)}")
    process = gpg(["--symmetric", "--cipher-algo", "AES256", "--compress-algo", "none", "--output", str(out)], secret, stdin=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=process.stdin, mode="w|") as tar:
            entry = tarfile.TarInfo(SUMMARY)
            entry.size, entry.mtime = len(summary), int(made.timestamp())
            tar.addfile(entry, io.BytesIO(summary))
            done = 0
            for number, (path, size) in enumerate(objects, 1):
                entry = tarfile.TarInfo(path)
                entry.size, entry.mtime = size, int(made.timestamp())
                with fs.open_input_stream(path) as stream:
                    tar.addfile(entry, stream)
                done += size
                if number % 10 == 0 or number == len(objects):
                    say(f"  {number:,} of {len(objects):,} files, {mb(done)} of {mb(total)}")
        process.stdin.close()
    except BaseException:
        process.kill()
        out.unlink(missing_ok=True)
        raise
    if process.wait() != 0:
        out.unlink(missing_ok=True)
        stop("gpg failed, so no export was written.")

    digest = hashlib.sha256()
    with out.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    say(f"\nDone: {out}")
    say(f"  size     {mb(out.stat().st_size)}")
    say(f"  sha256   {digest.hexdigest()}")
    say("\nThis file holds real patient records. Send it only to someone cleared to hold them, over a channel")
    say("approved for patient data, and send the passphrase separately. `make purge` removes it from this laptop.")
    return 0


# -- import ----------------------------------------------------------------------------

def cmd_import(args) -> int:
    source = Path(args.file).expanduser()
    if not source.is_file():
        stop(f"no such file: {source}")
    s = settings()
    bucket = bucket_name(s)

    say("Step 1 of 4: opening the export")
    secret = passphrase(confirm=False)
    with tempfile.TemporaryFile() as complaints:
        process = gpg(["--decrypt", str(source)], secret, stdout=subprocess.PIPE, stderr=complaints)
        try:
            tar = tarfile.open(fileobj=process.stdout, mode="r|")
            first = tar.next()
        except tarfile.TarError:
            first = None
        if first is None or first.name != SUMMARY:
            process.kill()
            stop("could not open the file. The passphrase is wrong, or this is not a stand-in export. Nothing was changed.")
        summary = json.load(tar.extractfile(first))
        if summary.get("format") != FORMAT:
            process.kill()
            stop(f"this export is format {summary.get('format')}; these tools read format {FORMAT}. Pull the latest project. Nothing was changed.")
        if summary["bucket"] != bucket:
            process.kill()
            stop(f"the export is of bucket '{summary['bucket']}' but this stand-in uses '{bucket}'. Nothing was changed.")
        say(f"  made {summary['made_at']}: {len(summary['tables'])} tables, {sum(t['rows'] for t in summary['tables']):,} rows, "
            f"{summary['files']:,} files, {mb(summary['bytes'])}")

        say("Step 2 of 4: checking what this stand-in holds now")
        existing = list_objects(filesystem(s), bucket)
        if existing:
            held = find_tables(existing)
            say(f"  it holds {len(held) + len(find_plain_files(existing, held))} tables in {len(existing):,} files. Importing deletes them and puts the export in their place.")
            if os.environ.get("CONFIRM") != "replace":
                try:
                    answer = input("Type replace to go ahead: ")
                except EOFError:
                    answer = ""
                if answer.strip() != "replace":
                    process.kill()
                    say("Not confirmed. Nothing was changed.")
                    return 1
        else:
            say("  it is empty")

        say("Step 3 of 4: writing the files")
        target = filesystem(s, write=True)
        target.create_dir(bucket)
        target.delete_dir_contents(bucket, missing_dir_ok=True)
        incomplete = "The stand-in is now incomplete. Run the import again with a good copy of the file."
        written = size = 0
        try:
            while (member := tar.next()) is not None:
                parts = member.name.split("/")
                if not member.isfile() or parts[0] != bucket or ".." in parts or "" in parts:
                    stop(f"the export holds an entry that does not belong in the bucket ({member.name}). {incomplete}")
                with target.open_output_stream(member.name) as out:
                    shutil.copyfileobj(tar.extractfile(member), out, 1 << 20)
                written += 1
                size += member.size
                if written % 10 == 0 or written == summary["files"]:
                    say(f"  {written:,} of {summary['files']:,} files, {mb(size)} of {mb(summary['bytes'])}")
        except (tarfile.TarError, OSError) as exc:
            process.kill()
            stop(f"the file could not be read to the end ({exc}). {incomplete}")
        if process.wait() != 0 or written != summary["files"]:
            complaints.seek(0)
            detail = complaints.read().decode(errors="replace").strip().splitlines()[-1:] or ["no detail"]
            stop(f"the file is damaged or cut short: {written:,} of {summary['files']:,} files arrived ({detail[0]}). {incomplete}")

    say("Step 4 of 4: checking the rows")
    tables = {(t["source"], t["table"]): t for t in describe(s, list_objects(filesystem(s), bucket), progress=False)}
    con = connect(s)
    problems, notes = [], []
    for number, expected in enumerate(summary["tables"], 1):
        key = (expected["source"], expected["table"])
        name = ".".join(key)
        table = tables.get(key)
        if table is None:
            problems.append(f"{name} is missing")
            continue
        counted = con.execute(f"SELECT count(*) FROM {read_sql(table)}").fetchone()[0] if table["files"] else 0
        ok = counted == expected["rows"] == table["rows"]
        say(f"  {number}/{len(summary['tables'])} {name}: {counted:,} rows" + ("" if ok else f"  DIFFERENT, the export says {expected['rows']:,}"))
        if not ok:
            problems.append(f"{name} holds {counted:,} rows but the export says {expected['rows']:,}")
        manifest = MANIFESTS / f"{name}.json"
        if manifest.is_file():
            kept = json.loads(manifest.read_text()).get("rows_kept")
            if kept != expected["rows"]:
                notes.append(f"{name}: this project's totals say {kept:,} rows, the export has {expected['rows']:,}")
        else:
            notes.append(f"{name}: this project has no totals file for it")
    if problems:
        say("\nThe import did not check out:")
        for problem in problems:
            say(f"  - {problem}")
        say(incomplete)
        return 1
    say(f"\nDone. The stand-in holds {len(summary['tables'])} tables and {sum(t['rows'] for t in summary['tables']):,} rows, the same as the export.")
    if notes:
        say("\nThe export and this project's totals files (source-sample/manifests/) differ. Pull the latest project, or ask for a newer export:")
        for note in notes:
            say(f"  - {note}")
    else:
        say("It also matches this project's totals files (source-sample/manifests/).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tables")
    commands.add_parser("browse")
    commands.add_parser("export")
    commands.add_parser("import").add_argument("file")
    args = parser.parse_args()
    return {"tables": cmd_tables, "browse": cmd_browse, "export": cmd_export, "import": cmd_import}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
