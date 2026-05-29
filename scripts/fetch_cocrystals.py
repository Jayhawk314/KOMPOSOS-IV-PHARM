#!/usr/bin/env python3
"""
Download co-crystal PDB structures listed in a benchmark manifest from RCSB.

This pulls public structural data (https://files.rcsb.org/download/<ID>.pdb)
into the local template cache so the pocket-recovery benchmark has bound-ligand
ground truth to score against. Existing files are not re-downloaded unless
--force is given.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "data" / "benchmarks" / "cocrystal_small.json"
DEFAULT_DEST = PROJECT_ROOT / "data" / "cache" / "pdb_templates"
RCSB_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"


def load_pdb_ids(manifest_path: Path) -> List[str]:
    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    ids = [str(entry["pdb_id"]).strip().upper() for entry in manifest.get("structures", [])]
    return [pdb_id for pdb_id in ids if pdb_id]


def download_pdb(pdb_id: str, dest_dir: Path, force: bool, timeout: float) -> dict:
    dest = dest_dir / f"{pdb_id}.pdb"
    if dest.exists() and not force:
        return {"pdb_id": pdb_id, "status": "cached", "path": str(dest), "bytes": dest.stat().st_size}
    url = RCSB_URL.format(pdb_id=pdb_id)
    request = urllib.request.Request(url, headers={"User-Agent": "komposos-cocrystal-benchmark/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        return {"pdb_id": pdb_id, "status": "http_error", "code": exc.code, "url": url}
    except Exception as exc:  # noqa: BLE001 - report any network failure per id
        return {"pdb_id": pdb_id, "status": "error", "error": str(exc), "url": url}
    if not payload or b"ATOM" not in payload[:200000]:
        return {"pdb_id": pdb_id, "status": "empty_or_invalid", "url": url}
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(payload)
    return {"pdb_id": pdb_id, "status": "downloaded", "path": str(dest), "bytes": len(payload)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch benchmark co-crystal PDBs from RCSB")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--force", action="store_true", help="Re-download even if cached")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--sleep", type=float, default=0.5, help="Politeness delay between downloads (s)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.manifest.exists():
        print(f"[FAIL] manifest not found: {args.manifest}", file=sys.stderr)
        return 1
    pdb_ids = load_pdb_ids(args.manifest)
    if not pdb_ids:
        print("[FAIL] no pdb_id entries in manifest", file=sys.stderr)
        return 1

    results = []
    for index, pdb_id in enumerate(pdb_ids, start=1):
        result = download_pdb(pdb_id, args.dest, args.force, args.timeout)
        results.append(result)
        print(f"[{index}/{len(pdb_ids)}] {pdb_id}: {result['status']}"
              + (f" ({result.get('bytes')} bytes)" if result.get("bytes") else ""))
        if result["status"] == "downloaded" and args.sleep > 0:
            time.sleep(args.sleep)

    ok = sum(1 for r in results if r["status"] in {"downloaded", "cached"})
    failed = [r for r in results if r["status"] not in {"downloaded", "cached"}]
    print(f"--- {ok}/{len(results)} available, {len(failed)} failed ---")
    for r in failed:
        print(f"  FAILED {r['pdb_id']}: {r['status']} {r.get('code', '')} {r.get('error', '')}".rstrip())
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
