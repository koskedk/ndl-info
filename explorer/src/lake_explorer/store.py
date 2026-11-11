"""Read-only access to the object store: listing folders and opening files."""

from __future__ import annotations

import fnmatch
import hashlib
import hmac
import json
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from typing import Callable, TypeVar
from urllib.parse import quote
from xml.etree import ElementTree

import pyarrow.fs as pafs

from .config import Store


# The lake is reached over a VPN and connections drop now and then, so every
# call is given generous timeouts and several attempts.
CONNECT_TIMEOUT = 15  # seconds
REQUEST_TIMEOUT = 120
ATTEMPTS = 6

T = TypeVar("T")


def retrying(fn: Callable[[], T], what: str = "request") -> T:
    """Run fn, retrying on network errors with a growing pause between attempts."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return fn()
        except OSError as exc:
            transient = any(word in str(exc) for word in ("NETWORK_CONNECTION", "Timeout", "timed out", "curlCode", "SLOW_DOWN", "503", "Connection reset", "Temporary failure"))
            if not transient or attempt == ATTEMPTS:
                raise
            time.sleep(min(2 ** attempt, 30))
    raise AssertionError("unreachable")


@lru_cache(maxsize=None)
def filesystem(store: Store) -> pafs.S3FileSystem:
    return pafs.S3FileSystem(
        access_key=store.access_key,
        secret_key=store.secret_key,
        endpoint_override=store.host,
        scheme=store.scheme,
        region=store.region,
        force_virtual_addressing=False,  # Ceph and most self-hosted stores need path-style
        connect_timeout=CONNECT_TIMEOUT,
        request_timeout=REQUEST_TIMEOUT,
        retry_strategy=pafs.AwsStandardS3RetryStrategy(max_attempts=ATTEMPTS),
    )


def _signed_get(store: Store, bucket: str, query: dict[str, str]) -> bytes:
    """One signed S3 GET on a bucket (AWS Signature Version 4), using only the standard library.

    pyarrow can list a whole folder but not "keys starting with X", which is what
    finding a table's newest metadata file needs. This avoids adding boto3 for one call.
    """
    now = datetime.now(timezone.utc)
    amz_date, day = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y%m%d")
    uri = "/" + quote(bucket, safe="")
    query_string = "&".join(f"{quote(k, safe='-_.~')}={quote(v, safe='-_.~')}" for k, v in sorted(query.items()))
    empty_hash = hashlib.sha256(b"").hexdigest()
    headers = {"host": store.host, "x-amz-content-sha256": empty_hash, "x-amz-date": amz_date}
    signed = ";".join(headers)
    canonical = "\n".join(["GET", uri, query_string, "".join(f"{k}:{v}\n" for k, v in headers.items()), signed, empty_hash])
    scope = f"{day}/{store.region}/s3/aws4_request"
    to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical.encode()).hexdigest()])
    key = ("AWS4" + store.secret_key).encode()
    for part in (day, store.region, "s3", "aws4_request"):
        key = hmac.new(key, part.encode(), hashlib.sha256).digest()
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    request = urllib.request.Request(
        f"{store.scheme}://{store.host}{uri}?{query_string}",
        headers={
            "x-amz-content-sha256": empty_hash,
            "x-amz-date": amz_date,
            "Authorization": f"AWS4-HMAC-SHA256 Credential={store.access_key}/{scope}, SignedHeaders={signed}, Signature={signature}",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        return response.read()


def keys_with_prefix(store: Store, path_prefix: str, limit: int = 50) -> list[tuple[str, datetime]]:
    """Up to `limit` objects whose bucket/key starts with path_prefix, as (bucket/key, modified)."""
    bucket, _, key_prefix = path_prefix.partition("/")
    body = retrying(lambda: _signed_get(store, bucket, {"list-type": "2", "prefix": key_prefix, "max-keys": str(limit)}))
    found = []
    for element in ElementTree.fromstring(body).iter():
        if element.tag.rsplit("}", 1)[-1] != "Contents":
            continue
        fields = {child.tag.rsplit("}", 1)[-1]: child.text for child in element}
        found.append((f"{bucket}/{fields['Key']}", datetime.fromisoformat(fields["LastModified"].replace("Z", "+00:00"))))
    return found


@dataclass(frozen=True)
class Entry:
    path: str  # bucket/key, no scheme
    is_dir: bool
    size: int
    modified: datetime | None

    @property
    def name(self) -> str:
        return self.path.rstrip("/").rsplit("/", 1)[-1]


def ls(store: Store, path: str, recursive: bool = False) -> list[Entry]:
    """Entries under bucket/path. Returns an empty list when the folder does not exist."""
    selector = pafs.FileSelector(path.rstrip("/"), recursive=recursive, allow_not_found=True)
    out = []
    for info in retrying(lambda: filesystem(store).get_file_info(selector)):
        is_dir = info.type == pafs.FileType.Directory
        out.append(Entry(info.path, is_dir, 0 if is_dir else (info.size or 0), info.mtime))
    return sorted(out, key=lambda e: (not e.is_dir, e.path))


def read_json(store: Store, path: str) -> dict:
    def fetch() -> bytes:
        with filesystem(store).open_input_stream(path) as stream:
            return stream.read()

    return json.loads(retrying(fetch))


def glob(store: Store, root: str, pattern: str) -> list[str]:
    """Files under root whose path relative to root matches the pattern (** crosses folders)."""
    files = [e.path for e in ls(store, root, recursive=True) if not e.is_dir]
    prefix = root.rstrip("/") + "/"
    return sorted(f for f in files if fnmatch.fnmatch(f[len(prefix):], pattern.replace("**/", "*")))
