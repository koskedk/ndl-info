# NHAI proof of concept: sources

This project has one job: to give you a local S3 store holding a sample of DHA's data lake for a few facilities (the sample sites), laid out exactly as the lake is. Everything else in the proof of concept reads from it. The transformation work (silver, gold, the Data Vault and the Master Patient Index) is a separate project, `ndl-poc-transform`, which connects to this store as its bronze.

The overall plan, the roadmap and where things stand are in [PLAN.md](PLAN.md).

The local store is called the stand-in. **It holds real patient records, with names and identifiers.** Read "Handling the data" below before you import it.

## What you need

- Docker, with Docker Compose
- [uv](https://docs.astral.sh/uv/), which installs the Python tools on first use
- `make` and `gpg` (GnuPG)
- On Windows, run everything inside WSL

You do not need the VPN. The data comes to you as one encrypted file.

## Getting started

1. Get the project and start the stand-in. The first run creates your own local settings and keys.

   ```bash
   git clone <this repository>
   cd ndl-poc-sources
   make up
   ```

2. Ask the project lead for the current export file and its passphrase. They arrive separately.

3. Import it. You are asked for the passphrase; the import then checks every table's row count.

   ```bash
   make import-source FILE=~/Downloads/standin-2026-11-16-1500.tar.gpg
   ```

4. Look at what you have.

   ```bash
   make tables          # the tables and their row counts
   make browse-rows     # a web page for reading rows with SQL, at http://localhost:4213
   ```

   The files themselves can be browsed at `http://127.0.0.1:8888/buckets/dha-analytics/iceberg/`.

## Connecting another project to it

The stand-in is an S3 store at `http://127.0.0.1:8333` (the port is `STANDIN_S3_PORT` in `.env`), bucket `dha-analytics`, with path-style addressing. Its tables are Iceberg folders under `iceberg/<source folder>/<table>/`, with no table catalog. The read-only key is in `.env` (`STANDIN_S3_ACCESS_KEY` and `STANDIN_S3_SECRET_KEY`); use that one, never the write key. From inside a Docker container the address is `http://host.docker.internal:<port>`.

When the lead samples more tables, they send a new export. Pull the project, then import the new file; it replaces what you have.

## Commands

Run `make help` for the full list.

| Command | What it does |
|---|---|
| `make up` / `make down` | Starts or stops the services. Data is kept |
| `make tables` | Lists the tables in the stand-in with their row counts |
| `make browse-rows` | Opens a web page for reading rows with SQL |
| `make import-source FILE=...` | Replaces the stand-in with an export |
| `make export-source` | Writes the stand-in to one encrypted file under `exports/` |
| `make reset-source` | Deletes the stand-in only |
| `make purge` | Deletes every copy of the data on this laptop |

## Handling the data

- **Keep it on this laptop.** No rows in documents, chats, screenshots or AI assistants. Totals only.
- **Never commit it.** The data lives in a Docker volume, outside the project folder. Exports, keys and working files are ignored by git; do not force-add them.
- **Pass an export on only to someone cleared to hold the data**, over a channel approved for patient data, with the passphrase sent separately.
- **Use an encrypted disk.** Deleted files can be recovered from an unencrypted one.
- **Run `make purge` when you are done.** It removes the stand-in, working files and local exports, and checks that nothing is left.

## What is in the project

| Folder or file | What it is |
|---|---|
| `PLAN.md` | The plan: what is built, in what order, and what has been found so far |
| `compose.yaml` | Every service, grouped in profiles |
| `Makefile` | The commands above |
| `source-sample/` | What the stand-in holds: the tables, the facilities, how each column was treated, and the totals of each table |
| `transform/` | Two lists the sample depends on: the Master Facility List with the sample sites, and the list of personal data fields. The models themselves are in `ndl-poc-transform` |
| `tools/` | The program behind `tables`, `browse-rows`, `export-source` and `import-source` |
| `ops/` | Local settings and service configuration |
| `purge.sh` | The program behind `make purge` |


## How the stand-in is kept up to date

The stand-in is sampled from DHA's lake by the project lead, who has the VPN access and the sampling tools. Those tools, the planning papers and the exploration notes are not in this project. What is here is everything needed to hold the sample and hand it to the projects that build on it.

Start with [source-sample/README.md](source-sample/README.md) to understand the data: there is no folder per facility, and record IDs repeat across facilities and counties.
