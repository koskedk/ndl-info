"""Loads connection details from .env and the list of sources from sources.toml."""

from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values, find_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]  # the explorer/ folder
DEFAULT_CONFIG = PROJECT_DIR / "sources.toml"
CACHE_DIR = PROJECT_DIR / ".cache"
SNAPSHOT_DIR = PROJECT_DIR / "snapshots"
OUT_DIR = PROJECT_DIR / "out"


class ConfigError(Exception):
    """A problem the user can fix in .env or sources.toml."""


@dataclass(frozen=True)
class Store:
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    region: str
    bucket: str

    @property
    def scheme(self) -> str:
        return "https" if self.endpoint.startswith("https") else "http"

    @property
    def host(self) -> str:
        return re.sub(r"^https?://", "", self.endpoint).rstrip("/")


@dataclass(frozen=True)
class Source:
    name: str
    store: Store
    kind: str  # "iceberg" or "parquet"
    path: str
    description: str = ""
    notes: str = ""
    tables: dict[str, str] = field(default_factory=dict)  # parquet kind only: name -> glob

    @property
    def root(self) -> str:
        """Bucket-qualified folder, without a scheme: bucket/path."""
        return f"{self.store.bucket}/{self.path}".rstrip("/")


@dataclass(frozen=True)
class Config:
    stores: dict[str, Store]
    sources: dict[str, Source]

    def source(self, name: str) -> Source:
        if name not in self.sources:
            known = ", ".join(self.sources)
            raise ConfigError(f"Unknown source '{name}'. Known sources: {known}")
        return self.sources[name]


def _load_env() -> dict[str, str]:
    """Values from the nearest .env above the working directory, overridden by real env vars."""
    values: dict[str, str] = {}
    env_file = find_dotenv(usecwd=True) or str(PROJECT_DIR.parent / ".env")
    if Path(env_file).is_file():
        values.update({k: v for k, v in dotenv_values(env_file).items() if v is not None})
    values.update(os.environ)
    return values


def load_config(path: Path | None = None) -> Config:
    path = Path(os.environ.get("LAKE_EXPLORER_CONFIG", path or DEFAULT_CONFIG))
    if not path.is_file():
        raise ConfigError(f"Sources file not found: {path}")
    raw = tomllib.loads(path.read_text())
    env = _load_env()

    stores: dict[str, Store] = {}
    for name, spec in raw.get("store", {}).items():
        prefix = spec.get("env_prefix", "").rstrip("_")
        missing = [k for k in ("ENDPOINT", "ACCESS_KEY", "SECRET_KEY") if not env.get(f"{prefix}_{k}")]
        if missing:
            wanted = ", ".join(f"{prefix}_{k}" for k in missing)
            raise ConfigError(f"Store '{name}' is missing settings in .env: {wanted}")
        bucket = spec.get("bucket") or env.get(f"{prefix}_BUCKETS", "").split(",")[0].strip()
        if not bucket:
            raise ConfigError(f"Store '{name}' has no bucket: set {prefix}_BUCKETS in .env")
        stores[name] = Store(
            name=name,
            endpoint=env[f"{prefix}_ENDPOINT"],
            access_key=env[f"{prefix}_ACCESS_KEY"],
            secret_key=env[f"{prefix}_SECRET_KEY"],
            region=env.get(f"{prefix}_REGION") or "us-east-1",
            bucket=bucket,
        )

    sources: dict[str, Source] = {}
    for spec in raw.get("source", []):
        name = spec["name"]
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ConfigError(f"Source name '{name}' must be letters, digits and underscores")
        if spec["store"] not in stores:
            raise ConfigError(f"Source '{name}' refers to unknown store '{spec['store']}'")
        kind = spec.get("kind", "iceberg")
        if kind not in ("iceberg", "parquet"):
            raise ConfigError(f"Source '{name}' has kind '{kind}'; use 'iceberg' or 'parquet'")
        sources[name] = Source(
            name=name,
            store=stores[spec["store"]],
            kind=kind,
            path=spec["path"].strip("/"),
            description=spec.get("description", ""),
            notes=spec.get("notes", ""),
            tables=dict(spec.get("tables", {})),
        )
    return Config(stores=stores, sources=sources)
