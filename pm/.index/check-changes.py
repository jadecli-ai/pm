#!/usr/bin/env python3
"""Check if PM system files have changed since last index generation.

Uses Merkle tree root hash comparison for O(1) change detection.
Outputs which files have changed if any.
"""

import hashlib
import json
import sys
from pathlib import Path

PM_DIR = Path(__file__).parent.parent
INDEX_FILE = PM_DIR / ".index" / "merkle-tree.json"


def hash_file(path: Path) -> str:
    """SHA256 hash of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not INDEX_FILE.exists():
        print("No index found. Run generate-merkle.py first.")
        sys.exit(1)

    index = json.loads(INDEX_FILE.read_text())
    stored_files = index.get("files", {})

    changed = []
    added = []
    removed = []

    # Check existing indexed files
    for rel_path, info in stored_files.items():
        full_path = PM_DIR / rel_path
        if not full_path.exists():
            removed.append(rel_path)
        else:
            current_hash = hash_file(full_path)
            if current_hash != info["hash"]:
                changed.append(rel_path)

    # Check for new files
    for ext in ["*.md", "*.sh"]:
        for path in PM_DIR.rglob(ext):
            if ".index" in str(path) or ".git" in str(path):
                continue
            rel_path = str(path.relative_to(PM_DIR))
            if rel_path not in stored_files:
                added.append(rel_path)

    # Report
    if not changed and not added and not removed:
        print(f"✅ Index is current (root: {index['root'][:16]}...)")
        sys.exit(0)

    print("⚠️ Index is stale. Changes detected:")
    if changed:
        print(f"\n  Modified ({len(changed)}):")
        for f in changed:
            print(f"    - {f}")
    if added:
        print(f"\n  Added ({len(added)}):")
        for f in added:
            print(f"    + {f}")
    if removed:
        print(f"\n  Removed ({len(removed)}):")
        for f in removed:
            print(f"    x {f}")

    print("\nRun: python3 .index/generate-merkle.py")
    sys.exit(1)


if __name__ == "__main__":
    main()
