# lake-explorer

A read-only command-line tool for exploring the data lake: what is in it, how it changes from one day to the next, and ad-hoc SQL over its tables. It never writes to the lake.

It exists because the lake keeps being loaded and new sources will be added. The questions asked during the first exploration (what tables are there, how fresh are they, which have repeated rows, where is the maternal health data) need to be repeatable.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and the VPN.

```bash
cd explorer
uv sync
uv run lake-explorer sources
```

Connection details come from the `.env` file in the project root (see `.env.example`). Nothing else needs configuring.

**If package downloads fail with the VPN on.** On this network the VPN blocks the Python package index. Run `uv sync` once with the VPN off, then connect the VPN and add `--offline` so uv does not try to check for packages:

```bash
uv run --offline lake-explorer sources
```

## Commands

| Command | What it does |
|---|---|
| `sources` | List the sources defined in `sources.toml` |
| `ls [path] [--sizes]` | List one folder of the bucket; `--sizes` totals each sub-folder |
| `tables <source>` | Tables in a source with rows, size and last load date |
| `schema <source> <table>` | A table's columns, size and load history |
| `find <text>` | Search table and column names across all sources |
| `inventory` | Record today's state of every table under `snapshots/` |
| `changes` | Compare two inventories, and list tables that have stopped loading |
| `sql "<query>"` | Run DuckDB SQL; name tables as `source.table` |
| `profile <source> <table>` | Per column: share missing, distinct values, smallest and largest |
| `dupes <source> <table> --key a,b` | Check for repeated rows on a key |

Add `--help` to any command for its options.

### Examples

```bash
# What is in Tiberbu, largest tables first
uv run lake-explorer tables tiberbu

# Which tables anywhere have a column about diagnosis
uv run lake-explorer find diagnos

# Columns of one table
uv run lake-explorer schema kenyaemr encounter_diagnosis

# A query, shown on screen
uv run lake-explorer sql "select program, count(distinct patient) as patients from tiberbu.health_program_enrollment where docstatus <> 2 group by 1 order by 2 desc"

# A saved query, written to a file as well
uv run lake-explorer sql -f queries/tiberbu_forms.sql --csv out/tiberbu_forms.csv

# Does the table repeat rows?
uv run lake-explorer dupes kenyaemr encounter_type --key source_schema,encounter_type_id

# Missing values and ranges for a few columns
uv run lake-explorer profile tiberbu patient --columns sex,dob,custom_county --where "status <> 'Disabled'"
```

## Keeping track of a lake that keeps changing

Run this regularly, for example once a week:

```bash
uv run lake-explorer inventory
uv run lake-explorer changes
```

`inventory` saves two small files under `snapshots/<date>/`: one row per table (rows, size, files, last load) and one row per column. `changes` compares the two newest dates and reports:

- new tables and tables that have disappeared
- columns added or removed
- how much each table grew, and any that shrank
- per source, how many tables have not been loaded for three or more days (add `--stale-detail` to list them)

The snapshot files hold table statistics only, no data, and are meant to be committed so the history builds up.

## Adding a new source

Add a block to `sources.toml`. No code change is needed.

A folder of Iceberg tables (one sub-folder per table):

```toml
[[source]]
name = "echis"
store = "dha"
kind = "iceberg"
path = "iceberg/echis"
description = "Community health information system"
```

Plain Parquet files, where each table is a file pattern:

```toml
[[source]]
name = "lmis"
store = "dha"
kind = "parquet"
path = "lmis/exports"
description = "Commodity stock reports"

  [source.tables]
  stock = "**/stock_*.parquet"
```

A source in a different bucket or object store needs its own store block and matching `.env` settings:

```toml
[store.bronze]
env_prefix = "BRONZE_S3"   # reads BRONZE_S3_ENDPOINT, BRONZE_S3_ACCESS_KEY, BRONZE_S3_SECRET_KEY, BRONZE_S3_BUCKETS
```

## Things to know

- **The first query on a large table is slow.** The lake has no table catalog, and some tables are made of thousands of small files. To read a table correctly the tool first works out which files belong to its current state. For a table loaded about 7,000 times this takes four to five minutes, with progress shown. The answer is cached in `.cache/`, so the next query on the same table starts straight away until the table is loaded again.
- **The connection drops now and then.** Every request is retried several times with a growing pause, so a long run survives a brief loss of the VPN.
- **Only current rows are counted.** Some table folders hold files that are no longer part of the table. The tool reads the table definition and ignores those, so its counts can be lower than a count of everything in the folder. For Tiberbu's `form_data_repository` the difference is large: the current table has 8 million rows, while the folder holds 31 million.
- **Query output can contain personal data.** The source tables hold names, phone numbers, national IDs and clinical notes. `out/` is ignored by git for that reason. Prefer totals over row listings, and do not paste row-level output into documents or chats.
- **`profile` shows the smallest and largest value of each column**, which for a name or ID column is a real person's value. Pick columns with `--columns` when profiling a table that holds personal details.
- **Memory.** Queries are capped at 4 GB and spill to disk beyond that. Raise it with `--memory 8GB` if the machine has room.

## How it works

- `sources.toml` lists the sources; `.env` holds the credentials.
- For an Iceberg source, each table is a folder with `metadata/` and `data/`. The tool finds the newest metadata file by probing version numbers (a folder can hold tens of thousands of files, so listing it is slow), and uses PyIceberg to list the data files in the current snapshot.
- Those files are handed to DuckDB as a dataset, so a query reads only the columns and rows it needs.
- Inventory figures (rows, size, last load) come from the metadata file alone, without reading data.

## Layout

```
explorer/
  sources.toml          the sources
  queries/              saved SQL
  snapshots/<date>/     inventory history (commit these)
  out/                  query output (ignored by git)
  .cache/               file lists and DuckDB spill space (ignored by git)
  src/lake_explorer/
    config.py           reads .env and sources.toml
    store.py            lists and opens files in the object store
    iceberg.py          reads Iceberg tables without a catalog
    engine.py           DuckDB over the current files of each table
    cli.py              the commands
```
