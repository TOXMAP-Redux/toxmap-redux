"""
R2 large-file uploader — uses boto3 S3 multipart upload.

Wrangler's `r2 object put` has a 300 MiB hard limit and cannot upload the
PMTiles basemap extract (~2–5 GiB). This script uses R2's S3 Compatibility
API, which has no file-size limit.

Usage:
    export R2_ACCOUNT_ID="your-account-id"
    export R2_ACCESS_KEY_ID="your-r2-access-key-id"
    export R2_SECRET_ACCESS_KEY="your-r2-secret-access-key"
    python scripts/upload_r2.py ~/Downloads/basemap_us.pmtiles toxmap-data basemap_us.pmtiles

Requirements:
    pip install boto3
"""

import os
import sys

import boto3
from botocore.config import Config


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Error: environment variable {name} is not set.")
        print("Set all three R2_* variables before running this script.")
        sys.exit(1)
    return value


class _Progress:
    """Print a single-line upload progress indicator."""

    def __init__(self, total_bytes: int) -> None:
        self._total = total_bytes
        self._seen = 0

    def __call__(self, bytes_transferred: int) -> None:
        self._seen += bytes_transferred
        pct = self._seen / self._total * 100
        done = self._seen / 1024**3
        total = self._total / 1024**3
        print(f"\r  {pct:5.1f}%  {done:.2f} / {total:.2f} GiB", end="", flush=True)


def upload(local_path: str, bucket: str, object_key: str) -> None:
    account_id = _require_env("R2_ACCOUNT_ID")
    access_key = _require_env("R2_ACCESS_KEY_ID")
    secret_key = _require_env("R2_SECRET_ACCESS_KEY")

    expanded = os.path.expanduser(local_path)
    if not os.path.exists(expanded):
        print(f"Error: file not found: {expanded}")
        sys.exit(1)

    file_size = os.path.getsize(expanded)
    print(f"Uploading {expanded}")
    print(f"  → s3://{bucket}/{object_key}")
    print(f"  Size: {file_size / 1024**3:.2f} GiB")
    print()

    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    s3.upload_file(
        expanded,
        bucket,
        object_key,
        ExtraArgs={"ContentType": "application/octet-stream"},
        Callback=_Progress(file_size),
    )
    print(f"\n\n✓ Upload complete: {bucket}/{object_key}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/upload_r2.py <local-file> <bucket> <object-key>")
        print("Example: python scripts/upload_r2.py ~/Downloads/basemap_us.pmtiles toxmap-data basemap_us.pmtiles")
        sys.exit(1)
    upload(sys.argv[1], sys.argv[2], sys.argv[3])
