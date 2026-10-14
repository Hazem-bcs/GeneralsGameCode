#!/usr/bin/env python3
"""Invalidate VC6 objects when headers change; VC6 emits no Ninja depfiles.

Only source timestamps are refreshed. Existing builds and backups are preserved.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def prepare(repo):
    repo = Path(repo)
    build = repo / "build/docker"
    if not build.exists():
        return
    files = subprocess.check_output(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repo).decode().split("\0")
    digest = hashlib.sha256()
    for name in sorted(set(files)):
        if Path(name).suffix.lower() in (".h", ".hpp", ".inl"):
            digest.update(name.encode())
            digest.update((repo / name).read_bytes())
    signature = digest.hexdigest()
    stamp = build / ".vc6-header-signature"
    if stamp.exists() and stamp.read_text() == signature:
        return
    sources = {repo / name for name in files
               if Path(name).suffix.lower() in (".c", ".cpp", ".cxx", ".rc")}
    # Include dependency sources materialized by CMake, too.
    commands = repo / "compile_commands.json"
    if commands.exists():
        sources.update(Path(item["file"]) for item in json.loads(commands.read_text()))
    touched = 0
    for source in sources:
        if source.is_file():
            os.utime(source, None)
            touched += 1
    # On failure the touched sources remain newer than their old objects, so retries are safe.
    stamp.write_text(signature)
    print(f"VC6 headers changed: refreshing {touched} source timestamps for a coherent rebuild")


if __name__ == "__main__":
    prepare(Path(__file__).resolve().parent.parent)
