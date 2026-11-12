"""Runs SQL over lake tables with DuckDB.

Tables are written in SQL as `source.table`, for example `tiberbu.patient`.
Each one is exposed to DuckDB as a view over the Parquet files in the table's
current Iceberg snapshot, so only the columns and rows a query needs are read.
"""

from __future__ import annotations

import re

import duckdb
import pyarrow.dataset as ds

from .config import CACHE_DIR, Config, Source
from . import iceberg, store as st


class Engine:
    def __init__(self, config: Config, memory_limit: str = "4GB", threads: int | None = None, log=None, progress=None):
        self.config = config
        self.log = log or (lambda msg: None)
        self.progress = progress  # called as progress(done, total) while a table's file list is built
        self.con = duckdb.connect()
        spill = CACHE_DIR / "duckdb_tmp"
        spill.mkdir(parents=True, exist_ok=True)
        self.con.execute(f"SET memory_limit='{memory_limit}'")
        self.con.execute(f"SET temp_directory='{spill}'")
        # A query that outgrows this fails with an error instead of filling the disk.
        self.con.execute("SET max_temp_directory_size='20GB'")
        self.con.execute("SET preserve_insertion_order=false")
        if threads:
            self.con.execute(f"SET threads={int(threads)}")
        self._registered: set[tuple[str, str]] = set()

    # -- registering tables -------------------------------------------------

    def _dataset(self, source: Source, table: str):
        fs = st.filesystem(source.store)
        if source.kind == "parquet":
            if table not in source.tables:
                known = ", ".join(source.tables) or "(none listed in sources.toml)"
                raise KeyError(f"{source.name} has no table '{table}'. Tables: {known}")
            files = st.glob(source.store, source.root, source.tables[table])
            if not files:
                raise FileNotFoundError(f"No files match {source.tables[table]} under {source.path}")
            self.log(f"{source.name}.{table}: {len(files):,} files")
            return ds.dataset(files, filesystem=fs, format="parquet", partitioning="hive")

        tbl = iceberg.open_table(source, table)
        self.log(f"{source.name}.{table}: working out which files are current (cached after the first time)")
        plan = iceberg.current_files(source, table, tbl, on_progress=self.progress)
        self.log(f"{source.name}.{table}: {plan.rows:,} rows in {len(plan.files):,} files")
        if plan.delete_files:
            # Row-level deletes cannot be applied by reading files directly; let PyIceberg do it.
            self.log(f"{source.name}.{table}: has delete files, reading through PyIceberg (slower)")
            return tbl.scan().to_arrow_batch_reader()
        if not plan.files:
            return tbl.schema().as_arrow().empty_table()
        return ds.dataset(list(plan.files), filesystem=fs, format="parquet", schema=tbl.schema().as_arrow())

    def register(self, source_name: str, table: str) -> None:
        key = (source_name, table)
        if key in self._registered:
            return
        source = self.config.source(source_name)
        handle = f"__{source_name}__{table}"
        self.con.register(handle, self._dataset(source, table))
        self.con.execute(f'CREATE SCHEMA IF NOT EXISTS "{source_name}"')
        self.con.execute(f'CREATE OR REPLACE VIEW "{source_name}"."{table}" AS SELECT * FROM "{handle}"')
        self._registered.add(key)

    def referenced_tables(self, sql: str) -> list[tuple[str, str]]:
        """source.table names used in a query, for the sources named in sources.toml."""
        names = "|".join(re.escape(n) for n in sorted(self.config.sources, key=len, reverse=True))
        pattern = rf'(?<![\w."])({names})\.("?)([A-Za-z_][A-Za-z0-9_]*)\2'
        seen: list[tuple[str, str]] = []
        for match in re.finditer(pattern, sql):
            key = (match.group(1), match.group(3))
            if key not in seen:
                seen.append(key)
        return seen

    # -- running queries ----------------------------------------------------

    def run(self, sql: str) -> tuple[list[str], list[tuple]]:
        for source_name, table in self.referenced_tables(sql):
            self.register(source_name, table)
        result = self.con.execute(sql)
        columns = [d[0] for d in result.description] if result.description else []
        return columns, result.fetchall() if columns else []
