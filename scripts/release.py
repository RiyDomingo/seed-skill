#!/usr/bin/env python3
"""Build and verify a local SEED candidate from the canonical sources."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import zipfile

from skills import FILES, publish, skill_files


def fingerprint(destination):
    names = sorted(FILES)
    if {path.name for path in destination.glob("*.zip")} != {name + ".zip" for name in names}:
        raise ValueError("Expected one ZIP for each canonical skill")
    report = {}
    for name in names:
        archive = destination / f"{name}.zip"
        if archive.is_symlink():
            raise ValueError(f"Expected a plain ZIP for {name}")
        expected = {f"{name}/{relative}": source for relative, source in skill_files(name)}
        with zipfile.ZipFile(archive) as bundle:
            if sorted(bundle.namelist()) != sorted(expected):
                raise ValueError(f"Packaged file list differs for {name}")
            members = bundle.infolist()
            for member in members:
                source = expected[member.filename]
                if member.external_attr >> 16 != 0o100644 or member.file_size != source.stat().st_size:
                    raise ValueError(f"Packaged file metadata differs for {member.filename}")
                if bundle.read(member) != source.read_bytes():
                    raise ValueError(f"Packaged source differs for {member.filename}")
        report[archive.name] = {"sha256": sha256(archive.read_bytes()).hexdigest(), "files": len(members),
                                "bytes": archive.stat().st_size}
    return {"format": "seed-skill-candidate-v1", "archives": report}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    destination = args.output.expanduser().resolve()
    manifest = destination / "manifest.json"
    try:
        if args.action == "build":
            if destination.exists() and any(destination.iterdir()):
                raise ValueError("Build requires a new or empty destination")
            publish(destination, sorted(FILES), archive=True)
            data = fingerprint(destination)
            with manifest.open("x", encoding="utf-8") as file:
                json.dump(data, file, indent=2, sort_keys=True)
                file.write("\n")
        else:
            data = fingerprint(destination)
            if manifest.is_symlink() or data != json.loads(manifest.read_text(encoding="utf-8")):
                raise ValueError("Candidate does not match the release manifest")
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        parser.exit(1, f"{error}\n")
    print(f"Verified {len(data['archives'])} packages against canonical sources and manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
