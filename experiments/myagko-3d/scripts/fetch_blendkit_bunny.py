#!/usr/bin/env python3
"""Fetch the selected free Blendkit Bunny Soft Toy asset as a .blend file.

Asset: Bunny Soft Toy by Yin Wu
Base ID: eb21a8a0-d3b0-4615-becd-1a842bfac171
The asset page marks it Free and says it has an armature.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ASSET_BASE_ID = os.environ.get("BLENDKIT_ASSET_BASE_ID", "eb21a8a0-d3b0-4615-becd-1a842bfac171")
OUT = Path(os.environ.get("BLENDKIT_OUT", "experiments/myagko-3d/source/bunny.blend"))
SEARCH = "https://www.blenderkit.com/api/v1/search/"
USER_AGENT = "BlenderKit/3.21.0 myagko-asset-pipeline"


def request_json(url: str, params: dict | None = None) -> dict:
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def download(url: str, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=120) as r, dst.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)


def find_asset() -> dict:
    queries = [
        f"asset_base_id:{ASSET_BASE_ID}",
        f"assetBaseId:{ASSET_BASE_ID}",
        "Bunny Soft Toy",
    ]
    for q in queries:
        print(f"Searching Blendkit: {q}")
        data = request_json(
            SEARCH,
            {
                "query": q,
                "addon_version": "3.21.0",
                "dict_parameters": 1,
                "page_size": 20,
            },
        )
        results = data.get("results") or []
        for asset in results:
            base_id = asset.get("assetBaseId") or asset.get("asset_base_id")
            if base_id == ASSET_BASE_ID:
                return asset
        if q == "Bunny Soft Toy" and results:
            # Last-resort exact-name match, but only if the page/base-id query failed.
            for asset in results:
                if (asset.get("name") or "").strip().lower() == "bunny soft toy":
                    return asset
    raise RuntimeError("Selected Blendkit asset not found")


def choose_file(asset: dict) -> dict:
    files = asset.get("files") or []
    if not files:
        raise RuntimeError("Asset has no downloadable files in API response")
    preference = ["blend", "resolution_2K", "resolution_1K", "resolution_4K", "resolution_0_5K"]
    def key(item: dict) -> int:
        ft = item.get("fileType") or item.get("file_type") or ""
        try:
            return preference.index(ft)
        except ValueError:
            return 999
    candidates = sorted(
        [f for f in files if (f.get("fileType") or f.get("file_type") or "").startswith(("blend", "resolution_"))],
        key=key,
    )
    if not candidates:
        candidates = files
    return candidates[0]


def resolve_download(file_info: dict) -> str:
    endpoint = file_info.get("downloadUrl") or file_info.get("download_url")
    if not endpoint:
        raise RuntimeError(f"No download URL endpoint in file info: {file_info.keys()}")
    data = request_json(endpoint, {"scene_uuid": str(uuid.uuid4())})
    direct = data.get("filePath") or data.get("download_url") or data.get("url")
    if not direct:
        raise RuntimeError(f"Could not resolve direct download URL: {data}")
    return direct


def main() -> int:
    asset = find_asset()
    print("Found:", asset.get("name"), "id=", asset.get("id"), "base=", asset.get("assetBaseId"))
    file_info = choose_file(asset)
    print("Selected file type:", file_info.get("fileType"), "size:", file_info.get("fileSize"))
    direct = resolve_download(file_info)
    print("Downloading selected .blend asset...")
    download(direct, OUT)
    size = OUT.stat().st_size
    if size < 1024:
        raise RuntimeError(f"Downloaded file is unexpectedly small: {size} bytes")
    print(f"Saved {OUT} ({size/1024:.1f} KiB)")
    meta = {
        "assetBaseId": ASSET_BASE_ID,
        "assetId": asset.get("id"),
        "name": asset.get("name"),
        "author": asset.get("author", {}).get("fullName") if isinstance(asset.get("author"), dict) else asset.get("author"),
        "fileType": file_info.get("fileType"),
        "downloadedBytes": size,
        "fetchedAt": int(time.time()),
    }
    OUT.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("ERROR:", exc, file=sys.stderr)
        raise
