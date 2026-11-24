#!/usr/bin/env python3
"""Install or archive canonical SEED skills without collecting workspace data."""

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "seed-scout": ("scout.py",),
    "seed-market": ("market.py",),
    "seed-model": ("model.py", "assumptions.example.json"),
    "seed-plan": ("plan.py", "config.example.json"),
    "seed-deck": ("deck.py",),
    "seed-investors": ("investors.py", "investors.example.csv"),
    "seed-closer": ("closer.py", "template.txt"),
    "seed-coach": ("coach.py", "questions.json"),
    "seed-terms": ("terms.py",),
    "seed-dataroom": ("dataroom.py",),
    "seed-updates": ("update.py", "metrics.example.json"),
}
COMMON = ("SKILL.md", "references/workflow.md", "agents/openai.yaml")


def skill_files(name):
    folder = ROOT / name
    for relative in (*COMMON, *FILES[name], "LICENSE"):
        path = ROOT / "LICENSE" if relative == "LICENSE" else folder / relative
        if not path.is_file() or path != path.resolve():
            raise ValueError(f"Expected plain source file without symlinks: {path}")
        yield relative, path


def publish(destination, names, archive):
    suffix = ".zip" if archive else ""
    targets = [destination / (name + suffix) for name in names]
    conflicts = [str(target) for target in targets if os.path.lexists(target)]
    if conflicts:
        raise FileExistsError("Existing targets: " + ", ".join(conflicts))
    inputs = {name: list(skill_files(name)) for name in names}
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".seed-skills-", dir=destination) as staging:
        stage = Path(staging)
        for name, target in zip(names, targets):
            if archive:
                with zipfile.ZipFile(stage / target.name, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                    for relative, source in inputs[name]:
                        entry = zipfile.ZipInfo(f"{name}/{relative}")
                        entry.external_attr = 0o100644 << 16
                        bundle.writestr(entry, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED)
            else:
                for relative, source in inputs[name]:
                    out = stage / name / relative
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, out)
        created = []
        try:
            for target in targets:
                source = stage / target.name
                if archive:
                    with source.open("rb") as data, target.open("xb") as output:
                        created.append(target)
                        shutil.copyfileobj(data, output)
                else:
                    target.mkdir()
                    created.append(target)
                    # Publish the discoverable entry point after its dependencies.
                    for item in source.iterdir():
                        if item.is_dir():
                            shutil.copytree(item, target / item.name)
                        elif item.name != "SKILL.md":
                            shutil.copyfile(item, target / item.name)
                    os.replace(source / "SKILL.md", target / "SKILL.md")
        except OSError:
            for target in reversed(created):
                if archive:
                    target.unlink()
                else:
                    shutil.rmtree(target)
            raise
    return targets


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    install = sub.add_parser("install", help="copy skills into a host discovery directory")
    install.add_argument("target", choices=("codex", "claude", "manual"))
    location = install.add_mutually_exclusive_group(required=True)
    location.add_argument("--project", type=Path)
    location.add_argument("--user", action="store_true")
    location.add_argument("--destination", type=Path)
    archive = sub.add_parser("package", help="create one upload ZIP per skill")
    archive.add_argument("--output", type=Path, default=ROOT / "dist")
    for command in (install, archive):
        command.add_argument("--skill", action="append", choices=sorted(FILES), help="repeat to select multiple")
    args = parser.parse_args(argv)

    if args.command == "package":
        destination = args.output
    elif args.target == "manual":
        if args.destination is None:
            parser.error("manual installation requires --destination")
        destination = args.destination
    else:
        if args.destination is not None:
            parser.error("use --project or --user for this host")
        base = (Path.home() if args.user else args.project).expanduser().resolve()
        if not base.is_dir():
            parser.error("the project directory must already exist")
        destination = base / (".agents" if args.target == "codex" else ".claude") / "skills"
        if destination.resolve() != destination:
            parser.error("host skill directory must stay inside its selected scope without links")

    names = sorted(set(args.skill or FILES))
    try:
        for path in publish(destination.expanduser().resolve(), names, archive=args.command == "package"):
            print(path)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
