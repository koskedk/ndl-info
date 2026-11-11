"""Command-line interface: `lake-explorer <command>`."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from . import iceberg, store as st
from .config import OUT_DIR, SNAPSHOT_DIR, Config, ConfigError, load_config
from .engine import Engine

app = typer.Typer(
    help="Explore the data lake: what is there, how it changes, and ad-hoc SQL over it. Read-only.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_show_locals=False,  # never print credentials held in local variables
)
console = Console()
err = Console(stderr=True, style="dim")


# -- helpers ------------------------------------------------------------------

def _config() -> Config:
    try:
        return load_config()
    except ConfigError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


def _source(cfg: Config, name: str):
    try:
        return cfg.source(name)
    except ConfigError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.2f}"
    return str(value)


def _size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:,.0f} {unit}" if unit in ("B", "KB") else f"{n:,.1f} {unit}"
        n /= 1024
    return ""


def _print(columns: list[str], rows: list, title: str | None = None, max_width: int = 60) -> None:
    table = Table(title=title, title_justify="left", header_style="bold")
    numeric = [bool(rows) and all(isinstance(r[i], (int, float)) or r[i] is None for r in rows) for i in range(len(columns))]
    for col, is_num in zip(columns, numeric):
        table.add_column(col, justify="right" if is_num else "left", overflow="fold", max_width=max_width)
    for row in rows:
        table.add_row(*[_fmt(v) for v in row])
    console.print(table)


def _write_csv(path: Path, columns: list[str], rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        writer.writerows(rows)


def _snapshot_dates() -> list[str]:
    if not SNAPSHOT_DIR.is_dir():
        return []
    return sorted(p.name for p in SNAPSHOT_DIR.iterdir() if (p / "tables.csv").is_file())


def _read_snapshot(day: str) -> tuple[dict[tuple[str, str], dict], dict[tuple[str, str], list[str]]]:
    tables: dict[tuple[str, str], dict] = {}
    with (SNAPSHOT_DIR / day / "tables.csv").open() as fh:
        for row in csv.DictReader(fh):
            tables[(row["source"], row["table"])] = row
    columns: dict[tuple[str, str], list[str]] = defaultdict(list)
    with (SNAPSHOT_DIR / day / "columns.csv").open() as fh:
        for row in csv.DictReader(fh):
            columns[(row["source"], row["table"])].append(row["column"])
    return tables, columns


def _inventory(cfg: Config, names: list[str]) -> list[iceberg.TableInfo]:
    infos: list[iceberg.TableInfo] = []
    failures: list[tuple[str, str, str]] = []
    with Progress(console=err, transient=True) as progress:
        for name in names:
            source = cfg.source(name)
            total = len(iceberg.list_tables(source))
            task = progress.add_task(f"Reading {name}", total=total)
            infos += iceberg.source_inventory(
                source,
                on_done=lambda: progress.advance(task),
                on_failed=lambda table, reason: failures.append((name, table, reason)),
            )
    if failures:
        _print(["source", "table", "problem"], failures, title=f"[yellow]{len(failures)} tables could not be read and are left out[/yellow]", max_width=90)
    return infos


def _engine(cfg: Config, memory: str = "4GB") -> Engine:
    last = {"shown": -1}

    def progress(done: int, total: int) -> None:
        step = done * 20 // total  # report every 5%
        if total >= 200 and step != last["shown"]:
            last["shown"] = step
            err.print(f"  reading load records: {done:,} of {total:,}")

    return Engine(cfg, memory_limit=memory, log=err.print, progress=progress)


# -- commands -----------------------------------------------------------------

@app.command()
def sources():
    """List the sources defined in sources.toml."""
    cfg = _config()
    rows = [(s.name, s.kind, f"{s.store.bucket}/{s.path}", s.description) for s in cfg.sources.values()]
    _print(["source", "kind", "location", "description"], rows, max_width=70)


@app.command()
def ls(
    path: str = typer.Argument("", help="Folder inside the bucket. Leave empty for the top level."),
    sizes: bool = typer.Option(False, "--sizes", help="Total up every file under each sub-folder (slow on big folders)."),
    store: Optional[str] = typer.Option(None, help="Store name from sources.toml. Defaults to the first one."),
):
    """List one folder of the bucket."""
    cfg = _config()
    s = cfg.stores[store] if store else next(iter(cfg.stores.values()))
    root = f"{s.bucket}/{path.strip('/')}".rstrip("/")
    rows = []
    for entry in st.ls(s, root):
        if entry.is_dir and sizes:
            with err.status(f"Sizing {entry.name}/"):
                files = [e for e in st.ls(s, entry.path, recursive=True) if not e.is_dir]
            dates = [e.modified for e in files if e.modified]
            rows.append((entry.name + "/", len(files), _size(sum(e.size for e in files)),
                         f"{min(dates):%Y-%m-%d}" if dates else "", f"{max(dates):%Y-%m-%d}" if dates else ""))
        elif entry.is_dir:
            rows.append((entry.name + "/", None, "", "", ""))
        else:
            rows.append((entry.name, 1, _size(entry.size), "", f"{entry.modified:%Y-%m-%d}" if entry.modified else ""))
    _print(["name", "files", "size", "first written", "last written"], rows, title=f"{root}/")


@app.command()
def tables(source: str = typer.Argument(..., help="Source name, e.g. tiberbu")):
    """List the tables in a source with row counts, size and last load date."""
    cfg = _config()
    src = _source(cfg, source)
    if src.kind == "parquet":
        _print(["table", "file pattern"], sorted(src.tables.items()), title=f"{source}: {src.description}")
        return
    infos = _inventory(cfg, [source])
    today = date.today()
    rows = []
    for i in sorted(infos, key=lambda i: -i.rows):
        age = (today - date.fromisoformat(i.last_load)).days if i.last_load else None
        rows.append((i.table, i.rows, _size(i.size_bytes), i.data_files, len(i.columns), i.last_load, age))
    _print(["table", "rows", "size", "files", "columns", "last load", "days ago"], rows,
           title=f"{source}: {src.description} ({len(rows)} tables, {sum(i.rows for i in infos):,} rows)")


@app.command()
def schema(source: str, table: str):
    """Show a table's columns, size and load history."""
    cfg = _config()
    src = _source(cfg, source)
    if src.kind == "parquet":
        engine = _engine(cfg)
        cols, rows = engine.run(f'DESCRIBE SELECT * FROM {source}."{table}"')
        _print(["column", "type"], [(r[0], r[1]) for r in rows], title=f"{source}.{table}")
        return
    with err.status("Reading table definition"):
        info = iceberg.table_info(src, table)
    if info is None:
        console.print(f"[red]{source}.{table} is not an Iceberg table (no metadata file found).[/red]")
        raise typer.Exit(1)
    console.print(f"[bold]{source}.{table}[/bold]  {src.store.bucket}/{src.path}/{table}")
    console.print(f"{info.rows:,} rows, {_size(info.size_bytes)} in {info.data_files:,} files, {info.snapshots:,} loads "
                  f"from {info.first_load or 'never'} to {info.last_load or 'never'}")
    if info.partitioned_by:
        console.print(f"Split by: {info.partitioned_by}")
    if info.delete_files:
        console.print(f"[yellow]{info.delete_files:,} delete files: some rows in the data files have been removed.[/yellow]")
    if src.notes:
        console.print(f"Note: {src.notes}")
    _print(["#", "column", "type"], [(c.position, c.name, c.type) for c in info.columns])


@app.command()
def inventory(
    source: Optional[list[str]] = typer.Option(None, "--source", "-s", help="Limit to these sources. Repeatable."),
):
    """Record today's state of every Iceberg table (rows, size, columns, last load) under snapshots/."""
    cfg = _config()
    names = source or [n for n, s in cfg.sources.items() if s.kind == "iceberg"]
    for n in names:
        if _source(cfg, n).kind != "iceberg":
            console.print(f"[red]{n} is not an Iceberg source; inventory covers Iceberg sources only.[/red]")
            raise typer.Exit(1)
    infos = _inventory(cfg, names)

    out = SNAPSHOT_DIR / date.today().isoformat()
    # A partial run (--source) must not wipe other sources already recorded today.
    kept_tables, kept_columns = [], []
    if (out / "tables.csv").is_file():
        old_tables, _ = _read_snapshot(out.name)
        kept_tables = [list(r.values()) for (s, _t), r in old_tables.items() if s not in names]
        with (out / "columns.csv").open() as fh:
            kept_columns = [list(r.values()) for r in csv.DictReader(fh) if r["source"] not in names]

    table_cols = ["source", "table", "rows", "data_files", "size_bytes", "delete_files", "snapshots",
                  "partitioned_by", "first_load", "last_load", "metadata_file", "columns"]
    _write_csv(out / "tables.csv", table_cols, sorted(kept_tables + [[i.as_row()[c] for c in table_cols] for i in infos]))
    _write_csv(out / "columns.csv", ["source", "table", "position", "column", "type"],
               sorted(kept_columns + [[i.source, i.table, c.position, c.name, c.type] for i in infos for c in i.columns],
                      key=lambda r: (r[0], r[1], int(r[2]))))

    by_source: dict[str, list[iceberg.TableInfo]] = defaultdict(list)
    for i in infos:
        by_source[i.source].append(i)
    rows = [(n, len(v), sum(i.rows for i in v), _size(sum(i.size_bytes for i in v)), max((i.last_load for i in v), default=""))
            for n, v in by_source.items()]
    _print(["source", "tables", "rows", "size", "last load"], rows, title=f"Inventory saved to {out}")
    console.print("Run [bold]lake-explorer changes[/bold] to compare with the previous inventory.")


@app.command()
def changes(
    since: Optional[str] = typer.Option(None, "--from", help="Earlier inventory date (YYYY-MM-DD). Default: second newest."),
    until: Optional[str] = typer.Option(None, "--to", help="Later inventory date. Default: newest."),
    stale_days: int = typer.Option(3, help="Flag tables not loaded for this many days before the later inventory."),
    stale_detail: bool = typer.Option(False, "--stale-detail", help="List every table that has stopped loading."),
):
    """Compare two inventories: new and dropped tables, column changes, growth, and tables that stopped loading."""
    days = _snapshot_dates()
    if not days:
        console.print("No inventory yet. Run [bold]lake-explorer inventory[/bold] first.")
        raise typer.Exit(1)
    until = until or days[-1]
    new_tables, new_cols = _read_snapshot(until)

    as_of = date.fromisoformat(until)
    stale = []
    per_source: dict[str, dict] = defaultdict(lambda: {"tables": 0, "stale": 0, "loads": []})
    for (s, t), row in sorted(new_tables.items()):
        summary = per_source[s]
        summary["tables"] += 1
        if row["last_load"]:
            summary["loads"].append(row["last_load"])
        if not row["last_load"]:
            stale.append((s, t, "never loaded", None))
            summary["stale"] += 1
        elif (as_of - date.fromisoformat(row["last_load"])).days >= stale_days:
            stale.append((s, t, row["last_load"], (as_of - date.fromisoformat(row["last_load"])).days))
            summary["stale"] += 1
    _print(["source", "tables", f"not loaded for {stale_days}+ days", "newest load", "oldest load"],
           [(s, v["tables"], v["stale"], max(v["loads"], default=""), min(v["loads"], default="")) for s, v in per_source.items()],
           title=f"Freshness as of {until}")
    if stale and stale_detail:
        _print(["source", "table", "last load", "days before inventory"], stale,
               title=f"Not loaded for {stale_days}+ days as of {until} ({len(stale)} tables)")
    elif stale:
        console.print(f"{len(stale)} tables have not been loaded for {stale_days}+ days. Add --stale-detail to list them.")

    earlier = [d for d in days if d < until]
    since = since or (earlier[-1] if earlier else None)
    if since is None:
        console.print(f"Only one inventory exists ({until}), so there is nothing to compare yet.")
        return
    old_tables, old_cols = _read_snapshot(since)
    console.print(f"\n[bold]Changes from {since} to {until}[/bold]")

    added = sorted(set(new_tables) - set(old_tables))
    dropped = sorted(set(old_tables) - set(new_tables))
    if added:
        _print(["source", "table", "rows"], [(s, t, int(new_tables[(s, t)]["rows"])) for s, t in added], title="New tables")
    if dropped:
        _print(["source", "table"], dropped, title="Tables no longer present")

    col_changes = []
    for key in sorted(set(new_tables) & set(old_tables)):
        plus = [c for c in new_cols[key] if c not in old_cols[key]]
        minus = [c for c in old_cols[key] if c not in new_cols[key]]
        if plus or minus:
            col_changes.append((*key, ", ".join(plus), ", ".join(minus)))
    if col_changes:
        _print(["source", "table", "columns added", "columns removed"], col_changes, title="Column changes")

    growth = []
    for key in set(new_tables) & set(old_tables):
        before, after = int(old_tables[key]["rows"]), int(new_tables[key]["rows"])
        if before != after:
            growth.append((*key, before, after, after - before, round(100 * (after - before) / before, 1) if before else None))
    growth.sort(key=lambda r: -abs(r[4]))
    if growth:
        _print(["source", "table", "rows before", "rows after", "change", "% change"], growth[:40],
               title=f"Row count changes ({len(growth)} tables; largest 40 shown)")
        shrunk = [g for g in growth if g[4] < 0]
        if shrunk:
            console.print(f"[yellow]{len(shrunk)} tables have fewer rows than before, which is unusual for an append-only lake.[/yellow]")
    if not (added or dropped or col_changes or growth):
        console.print("No differences.")


@app.command()
def find(text: str = typer.Argument(..., help="Part of a table or column name, e.g. diagnos")):
    """Search table and column names in the newest inventory."""
    days = _snapshot_dates()
    if not days:
        console.print("No inventory yet. Run [bold]lake-explorer inventory[/bold] first.")
        raise typer.Exit(1)
    tables_, columns_ = _read_snapshot(days[-1])
    needle = text.lower()
    hits = []
    for (s, t), row in sorted(tables_.items()):
        cols = [c for c in columns_[(s, t)] if needle in c.lower()]
        if needle in t.lower() or cols:
            hits.append((s, t, int(row["rows"]), row["last_load"], ", ".join(cols)))
    _print(["source", "table", "rows", "last load", "matching columns"], hits,
           title=f"'{text}' in the inventory of {days[-1]} ({len(hits)} tables)", max_width=80)


@app.command()
def sql(
    query: Optional[str] = typer.Argument(None, help='SQL. Name tables as source.table, e.g. "select count(*) from tiberbu.patient"'),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="Read the SQL from a file instead."),
    limit: int = typer.Option(50, help="Rows to show on screen."),
    save: Optional[Path] = typer.Option(None, "--csv", help="Also write all rows to this CSV file."),
    memory: str = typer.Option("4GB", help="Memory DuckDB may use before spilling to disk."),
):
    """Run a DuckDB SQL query over lake tables."""
    if (query is None) == (file is None):
        console.print("[red]Give a query, or --file, but not both.[/red]")
        raise typer.Exit(1)
    text = file.read_text() if file else query
    cfg = _config()
    engine = _engine(cfg, memory)
    started = datetime.now()
    with err.status("Running query"):
        columns, rows = engine.run(text)
    if save:
        _write_csv(save, columns, rows)
        err.print(f"Wrote {len(rows):,} rows to {save}")
    _print(columns, rows[:limit])
    more = f" (showing {limit})" if len(rows) > limit else ""
    err.print(f"{len(rows):,} rows{more} in {(datetime.now() - started).total_seconds():.1f}s")


@app.command()
def profile(
    source: str,
    table: str,
    columns: Optional[str] = typer.Option(None, help="Comma-separated columns. Default: all."),
    where: Optional[str] = typer.Option(None, help="Optional SQL filter, e.g. \"docstatus <> 2\""),
    memory: str = typer.Option("4GB"),
):
    """Per column: how many values are missing, how many distinct values, smallest and largest."""
    cfg = _config()
    _source(cfg, source)
    engine = _engine(cfg, memory)
    select = ", ".join(f'"{c.strip()}"' for c in columns.split(",")) if columns else "*"
    filt = f" WHERE {where}" if where else ""
    with err.status("Profiling"):
        cols, rows = engine.run(f'SUMMARIZE SELECT {select} FROM {source}."{table}"{filt}')
    idx = {c: i for i, c in enumerate(cols)}
    out = [(r[idx["column_name"]], r[idx["column_type"]], r[idx["count"]], float(r[idx["null_percentage"]] or 0),
            r[idx["approx_unique"]], str(r[idx["min"]])[:40] if r[idx["min"]] is not None else "",
            str(r[idx["max"]])[:40] if r[idx["max"]] is not None else "") for r in rows]
    _print(["column", "type", "rows", "% missing", "distinct (approx)", "smallest", "largest"], out,
           title=f"{source}.{table}{filt}")


@app.command()
def dupes(
    source: str,
    table: str,
    key: str = typer.Option(..., help="Comma-separated columns that should identify one row, e.g. source_schema,encounter_id"),
    memory: str = typer.Option("4GB"),
):
    """Check whether a table holds repeated rows for the same key."""
    cfg = _config()
    _source(cfg, source)
    engine = _engine(cfg, memory)
    keys = ", ".join(f'"{k.strip()}"' for k in key.split(","))
    with err.status("Counting"):
        _, rows = engine.run(
            f'WITH g AS (SELECT count(*) AS c FROM {source}."{table}" GROUP BY {keys}) '
            "SELECT coalesce(sum(c), 0), count(*), count(*) FILTER (WHERE c > 1), coalesce(max(c), 0) FROM g"
        )
    total, distinct, repeated, worst = rows[0]
    _print(["rows", "distinct keys", "keys with repeats", "most copies of one key"], [(total, distinct, repeated, worst)],
           title=f"{source}.{table} by ({key})")
    if repeated:
        console.print(f"[yellow]{total - distinct:,} rows are extra copies ({100 * (total - distinct) / total:.1f}% of the table).[/yellow]")
    else:
        console.print("[green]No repeated keys.[/green]")


def main() -> None:
    try:
        app()
    except ConfigError as exc:
        console.print(f"[red]{exc}[/red]")
        raise SystemExit(1)
