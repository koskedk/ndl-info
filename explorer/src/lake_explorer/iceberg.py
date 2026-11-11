"""Reads Iceberg tables that live in plain folders, with no catalog.

Each table is a folder holding `metadata/` and `data/`. The newest
`*.metadata.json` file in `metadata/` describes the current state of the table.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from pyiceberg.manifest import ManifestContent
from pyiceberg.table import StaticTable

MANIFEST_WORKERS = 24  # reading manifests is network-bound, so many threads help

from .config import CACHE_DIR, Source, Store
from . import store as st


@dataclass(frozen=True)
class Column:
    position: int
    name: str
    type: str


@dataclass(frozen=True)
class TableInfo:
    source: str
    table: str
    rows: int
    data_files: int
    size_bytes: int
    delete_files: int
    snapshots: int
    partitioned_by: str
    first_load: str  # YYYY-MM-DD, or "" when the table has never been loaded
    last_load: str
    metadata_file: str
    columns: tuple[Column, ...]

    def as_row(self) -> dict:
        row = asdict(self)
        row["columns"] = len(self.columns)
        return row


def list_tables(source: Source) -> list[str]:
    """Sub-folders of an Iceberg source that look like tables (bookkeeping folders start with _)."""
    return [e.name for e in st.ls(source.store, source.root) if e.is_dir and not e.name.startswith("_")]


def _versions(store: Store, table_root: str, n: int) -> list[tuple[str, datetime]]:
    """Metadata files for version n. Writers name them NNNNN-<uuid>.metadata.json."""
    found = st.keys_with_prefix(store, f"{table_root}/metadata/{n:05d}-")
    return [(path, modified) for path, modified in found if path.endswith(".metadata.json")]


def _latest_by_listing(store: Store, table_root: str) -> str | None:
    metas = [e for e in st.ls(store, f"{table_root}/metadata") if e.name.endswith(".metadata.json")]
    if not metas:
        return None
    return max(metas, key=lambda e: (e.modified or datetime.min.replace(tzinfo=timezone.utc), e.name)).path


def latest_metadata(store: Store, table_root: str) -> str | None:
    """Path of the newest metadata file for a table, or None if the folder is not a table.

    A table loaded thousands of times has tens of thousands of files in its
    metadata folder, and listing them all takes many seconds. Version numbers
    count up from 00000 without gaps, so the newest one is found by probing:
    double the number until it is missing, then narrow down. That takes about
    25 small requests however long the history is. If the numbering does not
    start at 00000 (old versions cleaned up, or a different naming scheme),
    fall back to listing the folder.
    """
    if not _versions(store, table_root, 0):
        return _latest_by_listing(store, table_root)
    low, high = 0, 1  # low exists; high is the first candidate not yet known to exist
    while _versions(store, table_root, high):
        low, high = high, high * 2
    while high - low > 1:  # newest version is in [low, high)
        mid = (low + high) // 2
        if _versions(store, table_root, mid):
            low = mid
        else:
            high = mid
    return max(_versions(store, table_root, low), key=lambda item: item[1])[0]


def _day(ms: int | None) -> str:
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d") if ms else ""


def _type_name(t) -> str:
    return t if isinstance(t, str) else t.get("type", "complex")


def table_info(source: Source, table: str) -> TableInfo | None:
    """Row counts, size, columns and load dates, read from the metadata file only."""
    meta_path = latest_metadata(source.store, f"{source.root}/{table}")
    if meta_path is None:
        return None
    meta = st.read_json(source.store, meta_path)

    schemas = meta.get("schemas") or [meta["schema"]]
    schema = next((s for s in schemas if s.get("schema-id") == meta.get("current-schema-id")), schemas[-1])
    columns = tuple(Column(i, f["name"], _type_name(f["type"])) for i, f in enumerate(schema["fields"], 1))

    snapshots = meta.get("snapshots") or []
    current = next((s for s in snapshots if s["snapshot-id"] == meta.get("current-snapshot-id")), None)
    summary = (current or {}).get("summary", {})

    specs = meta.get("partition-specs") or []
    spec = next((s for s in specs if s.get("spec-id") == meta.get("default-spec-id")), {"fields": []})
    partitioned_by = ", ".join(f"{p['name']} ({p['transform']})" for p in spec["fields"])

    return TableInfo(
        source=source.name,
        table=table,
        rows=int(summary.get("total-records", 0)),
        data_files=int(summary.get("total-data-files", 0)),
        size_bytes=int(summary.get("total-files-size", 0)),
        delete_files=int(summary.get("total-delete-files", 0)),
        snapshots=len(snapshots),
        partitioned_by=partitioned_by,
        first_load=_day(min((s["timestamp-ms"] for s in snapshots), default=None)),
        last_load=_day(current["timestamp-ms"]) if current else "",
        metadata_file=meta_path.rsplit("/", 1)[-1],
        columns=columns,
    )


def source_inventory(source: Source, workers: int = 8, on_done=None, on_failed=None) -> list[TableInfo]:
    """table_info for every table in an Iceberg source, read in parallel."""
    names = list_tables(source)

    failed: list[tuple[str, str]] = []

    def one(name: str) -> TableInfo | None:
        try:
            return table_info(source, name)
        except Exception as exc:  # keep going; report at the end
            failed.append((name, str(exc).splitlines()[0][:200]))
            return None
        finally:
            if on_done:
                on_done()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        infos = list(pool.map(one, names))
    if on_failed:
        for name, reason in failed:
            on_failed(name, reason)
    return sorted((i for i in infos if i is not None), key=lambda i: i.table)


def _io_properties(store: Store) -> dict[str, str]:
    return {
        "s3.endpoint": store.endpoint,
        "s3.access-key-id": store.access_key,
        "s3.secret-access-key": store.secret_key,
        "s3.region": store.region,
        "s3.force-virtual-addressing": "false",
        "s3.connect-timeout": str(st.CONNECT_TIMEOUT),
        "s3.request-timeout": str(st.REQUEST_TIMEOUT),
        "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO",
    }


def open_table(source: Source, table: str) -> StaticTable:
    meta_path = latest_metadata(source.store, f"{source.root}/{table}")
    if meta_path is None:
        raise FileNotFoundError(f"{source.name}.{table} is not an Iceberg table (no metadata file found)")
    props = _io_properties(source.store)
    return st.retrying(lambda: StaticTable.from_metadata(f"s3://{meta_path}", properties=props))


@dataclass(frozen=True)
class FilePlan:
    """The data files that make up the current state of a table."""
    files: tuple[str, ...]  # bucket/key, no scheme
    rows: int
    delete_files: int


def current_files(source: Source, table: str, tbl: StaticTable, on_progress=None) -> FilePlan:
    """Data files in the table's current snapshot.

    Every load adds a manifest (a small file listing the data files it wrote),
    and a table loaded thousands of times has thousands of them. They are read
    in parallel, each with retries, and the answer is cached per metadata file.
    on_progress(done, total) is called as manifests are read.
    """
    meta_name = tbl.metadata_location.rsplit("/", 1)[-1]
    cache = CACHE_DIR / "files" / source.name / table / f"{meta_name}.json"
    if cache.is_file():
        data = json.loads(cache.read_text())
        return FilePlan(tuple(data["files"]), data["rows"], data["delete_files"])

    snapshot = tbl.current_snapshot()
    if snapshot is None:
        return FilePlan((), 0, 0)
    io = tbl.io
    manifests = st.retrying(lambda: snapshot.manifests(io))
    done = 0

    def read(manifest) -> tuple[bool, list[tuple[str, int]]]:
        entries = st.retrying(lambda: list(manifest.fetch_manifest_entry(io, discard_deleted=True)))
        return manifest.content == ManifestContent.DATA, [(e.data_file.file_path, e.data_file.record_count) for e in entries]

    files: list[str] = []
    rows = delete_files = 0
    with ThreadPoolExecutor(max_workers=MANIFEST_WORKERS) as pool:
        for is_data, entries in pool.map(read, manifests):
            done += 1
            if on_progress:
                on_progress(done, len(manifests))
            if is_data:
                files += [path.removeprefix("s3://").removeprefix("s3a://") for path, _ in entries]
                rows += sum(n for _, n in entries)
            else:
                delete_files += len(entries)

    plan = FilePlan(tuple(files), rows, delete_files)
    cache.parent.mkdir(parents=True, exist_ok=True)
    for old in cache.parent.glob("*.json"):  # keep only the newest plan per table
        old.unlink()
    cache.write_text(json.dumps({"files": plan.files, "rows": plan.rows, "delete_files": plan.delete_files}))
    return plan
