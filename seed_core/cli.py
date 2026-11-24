"""Local-first SEED workspace and record commands."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

from .artifacts import register
from .legacy import capture, materialize, migrate
from .recovery import make_backup, restore_backup, verify_file
from .schema import KINDS, LEVELS, ORIGINS, VALIDATION, SeedError, require
from .transfer import backup, export, import_bundle, preview, read_file, snapshot, validate_bundle
from .workspace import Workspace


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path, help="absolute or relative private venture path")
    commands = parser.add_subparsers(required=True, dest="command")

    init = commands.add_parser("init", help="create an isolated local venture")
    for name in ("name", "currency", "jurisdiction"):
        init.add_argument("--" + name, required=True)

    commands.add_parser("validate", help="verify database, schema, revisions and links")
    commands.add_parser("info", help="show the selected venture configuration")
    ls = commands.add_parser("list", help="list local records")
    ls.add_argument("--kind", choices=KINDS)
    ls.add_argument("--history", action="store_true")
    get = commands.add_parser("get", help="view a revision by stable ID")
    get.add_argument("id")
    get.add_argument("--revision", type=int)
    put = commands.add_parser("put", help="add or explicitly revise a record")
    put.add_argument("kind", choices=KINDS)
    put.add_argument("key")
    put.add_argument("data", type=Path)
    put.add_argument("--expected", type=int)
    put.add_argument("--classification", choices=LEVELS, default="internal")
    put.add_argument("--provenance", choices=sorted(ORIGINS), default="unknown")
    put.add_argument("--status", choices=sorted(VALIDATION), default="draft")
    put.add_argument("--links", type=Path)
    affected = commands.add_parser("affected", help="show latest records pinned to outdated dependencies")
    affected.add_argument("id")
    trace = commands.add_parser("trace", help="view the pinned evidence graph and freshness findings")
    trace.add_argument("id")
    trace.add_argument("--on", default=datetime.now(timezone.utc).date().isoformat())

    for name in ("preview-export", "export"):
        selection = commands.add_parser(name, help="scope a portable transfer by record and classification")
        selection.add_argument("--maximum", choices=LEVELS[:-1], default="public")
        selection.add_argument("--id", action="append")
        if name == "export":
            selection.add_argument("output", type=Path)
            selection.add_argument("--confirm", required=True)
    inspect = commands.add_parser("inspect-transfer", help="validate a portable transfer before importing")
    inspect.add_argument("file", type=Path)
    incoming = commands.add_parser("import", help="apply a verified transfer or restore a backup")
    incoming.add_argument("file", type=Path)
    incoming.add_argument("--confirm", required=True)
    incoming.add_argument("--create", action="store_true")
    incoming.add_argument("--config", type=Path, help="local config if the exchange excludes the profile")
    save = commands.add_parser("backup", help="save a private portable backup")
    save.add_argument("name", help="filename ending in .json inside the workspace backups directory")
    save_db = commands.add_parser("backup-db", help="capture a complete private SQLite backup")
    save_db.add_argument("name")
    inspect_db = commands.add_parser("inspect-backup-db", help="fingerprint an offline backup before restore")
    inspect_db.add_argument("file", type=Path)
    restore_db = commands.add_parser("restore-db", help="validate and restore a SQLite backup into a new workspace")
    restore_db.add_argument("file", type=Path)
    restore_db.add_argument("--confirm", required=True)

    old = commands.add_parser("migrate", help="inventory legacy JSON or commit non-conflicting snapshots")
    old.add_argument("source", type=Path)
    old.add_argument("--apply", action="store_true")
    adapt = commands.add_parser("materialize", help="export legacy inputs into a fresh local run directory")
    adapt.add_argument("target", type=Path)
    adapt.add_argument("--file", action="append", help="select only these legacy filenames")
    saved = commands.add_parser("capture", help="record one original skill output with explicit inputs")
    saved.add_argument("file", type=Path)
    saved.add_argument("--expected", type=int)
    saved.add_argument("--links", type=Path)
    artifact = commands.add_parser("register-output", help="hash a generated workspace document and pin its inputs")
    artifact.add_argument("relative_path")
    artifact.add_argument("--name", required=True)
    artifact.add_argument("--document-type", required=True)
    artifact.add_argument("--links", required=True, type=Path)
    artifact.add_argument("--expected", type=int)
    return parser


def execute(args):
    name = args.command
    if name == "init":
        config = {field: getattr(args, field) for field in ("name", "currency", "jurisdiction")}
        return Workspace.init(args.workspace, config).metadata()
    if name == "inspect-transfer":
        bundle = read_file(args.file)
        validate_bundle(bundle)
        return preview(bundle)
    if name == "inspect-backup-db":
        return {"sha256": verify_file(args.file)[1]}
    if name == "restore-db":
        return restore_backup(args.workspace, args.file, args.confirm)
    if name == "import":
        return import_bundle(args.workspace, read_file(args.file), args.confirm, create=args.create,
                             config=read_file(args.config) if args.config else None)
    ws = Workspace(args.workspace)
    if name == "validate":
        return ws.validate()
    if name == "info":
        return ws.metadata()
    if name == "list":
        return ws.list(args.kind, history=args.history)
    if name == "get":
        result = ws.get(args.id, args.revision)
        require(result is not None, "Record or revision does not exist")
        return result
    if name == "put":
        return ws.put(args.kind, args.key, read_file(args.data), expected=args.expected,
                      classification=args.classification, provenance=args.provenance, status=args.status,
                      links=read_file(args.links) if args.links else None)
    if name == "affected":
        return ws.affected(args.id)
    if name == "trace":
        return ws.trace(args.id, args.on)
    if name == "preview-export":
        return preview(snapshot(ws, maximum=args.maximum, ids=args.id))
    if name == "export":
        return {"file": str(export(ws, args.output, args.confirm, maximum=args.maximum, ids=args.id))}
    if name == "backup":
        require(args.name.endswith(".json") and Path(args.name).name == args.name
                and "\\" not in args.name and ":" not in args.name, "Use a plain backup filename ending in .json")
        return {"file": str(backup(ws, ws.root / "backups" / args.name))}
    if name == "backup-db":
        return make_backup(ws, args.name)
    if name == "migrate":
        return migrate(ws, args.source, dry_run=not args.apply)
    if name == "materialize":
        return {"files": materialize(ws, args.target, names=args.file)}
    if name == "capture":
        return capture(ws, args.file, expected=args.expected,
                       links=read_file(args.links) if args.links else [])
    if name == "register-output":
        return register(ws, args.relative_path, name=args.name, document_type=args.document_type,
                        links=read_file(args.links), expected=args.expected)
    raise SeedError("Unknown workspace command")


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = execute(args)
    except (ValueError, OSError, sqlite3.Error, TypeError) as error:
        # Avoid echoing arbitrary untrusted or confidential input.
        print(str(error) if isinstance(error, SeedError) else "Workspace operation refused or failed",
              file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0
