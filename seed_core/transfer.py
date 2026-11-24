"""Explicit, digest-bound exchange and portable backups for venture records."""

from collections import defaultdict, deque
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile

from .schema import LEVELS, MAX_BYTES, VERSION, SeedError, canonical, digest, identifier, parse_json, require, validate_config
from .workspace import Conflict, Workspace, plain, private_root

FORMAT = "seed.venture.records"
FIELDS = {"id", "kind", "key", "revision", "saved_at", "classification",
          "provenance", "status", "data", "links", "digest"}


def read_file(path):
    path = Path(path)
    require(plain(path) and path.is_file(), "Input must be a regular file without links")
    with path.open("rb") as stream:
        return parse_json(stream.read(MAX_BYTES + 1))


def write_new(path, data):
    path = Path(path)
    parent = private_root(path.parent)
    require(parent.is_dir() and plain(path), "Output requires an existing private directory and an unlinked name")
    target = parent / path.name
    require(path.name not in {"", ".", ".."} and not os.path.lexists(target), "Output already exists")
    # Write privately first, reserve the final pathname exclusively, then publish.
    temp_path = None
    reserved = False
    try:
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".seed-write-", delete=False) as stream:
            temp_path = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        with target.open("xb"):
            reserved = True
        os.replace(temp_path, target)
        reserved = False
    finally:
        if reserved:
            target.unlink(missing_ok=True)
        if temp_path:
            temp_path.unlink(missing_ok=True)
    return target


def snapshot(workspace, *, maximum="public", ids=None, backup=False):
    require(maximum in LEVELS, "Unknown maximum classification")
    ceiling = LEVELS.index(maximum)
    if not backup:
        require(maximum != "restricted", "Restricted records can only leave via private backup")
    with workspace.connect() as cx:
        cx.execute("BEGIN")
        metadata = workspace.meta_on(cx)
        groups = defaultdict(list)
        for record in workspace.list_on(cx, history=True):
            groups[record["id"]].append(record)
        eligible = {record_id for record_id, chain in groups.items()
                    if LEVELS.index(chain[-1]["classification"]) <= ceiling
                    and (backup or chain[-1]["kind"] != "legacy")}
        # A record may depend on an older revision of a now-restricted record.
        # Drop it too, even if its own original classification was lower.
        while True:
            unsafe = {record_id for record_id in eligible for r in groups[record_id]
                      if any(link["id"] not in eligible for link in r["links"])}
            if not unsafe:
                break
            eligible -= unsafe
        if ids is not None:
            selected = {identifier(record_id) for record_id in ids}
            require(selected <= eligible, "A requested record or dependency is outside the export scope")
            while True:
                dependencies = {link["id"] for record_id in selected for r in groups[record_id] for link in r["links"]}
                if dependencies <= selected:
                    break
                selected |= dependencies
        else:
            selected = eligible
        records = [r for record_id in groups if record_id in selected for r in groups[record_id]]
        payload = {"format": FORMAT, "version": VERSION, "purpose": "backup" if backup else "exchange",
                   "venture_id": metadata["venture_id"], "maximum": maximum, "records": records}
        if backup:
            payload["workspace"] = metadata
        envelope = {"payload": payload, "sha256": digest(payload)}
        require(len(canonical(envelope)) < MAX_BYTES, "Export exceeds the transfer size limit")
        return envelope


def preview(envelope):
    data = envelope["payload"]
    return {"sha256": envelope["sha256"], "purpose": data["purpose"], "venture_id": data["venture_id"],
            "maximum": data["maximum"], "record_ids": sorted({r["id"] for r in data["records"]}),
            "revisions": len(data["records"])}


def export(workspace, path, confirmation, **selection):
    bundle = snapshot(workspace, **selection)
    require(confirmation == bundle["sha256"], "Export approval does not match the current payload")
    return write_new(path, canonical(bundle) + b"\n")


def backup(workspace, path):
    path = Path(path)
    require(path.parent.resolve() == (workspace.root / "backups").resolve() and plain(workspace.root / "backups"),
            "Backup destination must be the workspace's backups directory")
    path.parent.mkdir(exist_ok=True, mode=0o700)
    bundle = snapshot(workspace, maximum="restricted", backup=True)
    return write_new(path, canonical(bundle) + b"\n")


def validate_bundle(bundle):
    require(isinstance(bundle, dict) and set(bundle) == {"payload", "sha256"}, "Invalid exchange envelope")
    payload = bundle["payload"]
    require(isinstance(payload, dict) and bundle["sha256"] == digest(payload), "Exchange checksum mismatch")
    require(payload.get("format") == FORMAT and type(payload.get("version")) is int
            and payload["version"] == VERSION, "Unsupported transfer format or version")
    fields = {"format", "version", "purpose", "venture_id", "maximum", "records"}
    purpose = payload.get("purpose")
    require(purpose in ("exchange", "backup"), "Unknown transfer purpose")
    require(set(payload) == (fields | {"workspace"} if purpose == "backup" else fields),
            "Unexpected exchange fields")
    identifier(payload["venture_id"])
    maximum = payload["maximum"]
    require(maximum in LEVELS and (purpose == "backup" or maximum != "restricted"), "Invalid disclosure level")
    require(isinstance(payload["records"], list), "Expected a record list")
    heads = {}
    checked = set()
    groups = defaultdict(list)
    for record in payload["records"]:
        require(isinstance(record, dict) and set(record) == FIELDS, "Unexpected revision fields")
        identifier(record["id"])
        groups[record["id"]].append(record)
    for record_id, records in groups.items():
        require(all(type(r["revision"]) is int for r in records), "Invalid record revision")
        for revision in sorted(records, key=lambda r: r["revision"]):
            Workspace.validate_revision(None, payload["venture_id"], revision, heads.get(record_id))
            require(LEVELS.index(revision["classification"]) <= LEVELS.index(maximum)
                    and (purpose == "backup" or revision["kind"] != "legacy"), "Record outside transfer scope")
            heads[record_id] = revision
            checked.add((record_id, revision["revision"]))
    graph = {}
    reverse = defaultdict(set)
    for records in groups.values():
        for revision in records:
            node = (revision["id"], revision["revision"])
            dependencies = {(link["id"], link["revision"]) for link in revision["links"]}
            require(dependencies <= checked, "Missing revision dependency in transfer")
            if revision["revision"] > 1:
                dependencies.add((revision["id"], revision["revision"] - 1))
            graph[node] = dependencies
            for parent in dependencies:
                reverse[parent].add(node)
    ready = deque(node for node, parents in graph.items() if not parents)
    traversed = 0
    while ready:
        node = ready.popleft()
        traversed += 1
        for child in reverse[node]:
            graph[child].remove(node)
            if not graph[child]:
                ready.append(child)
    require(traversed == len(graph), "Revision dependencies contain a cycle")
    if purpose == "backup":
        meta = payload["workspace"]
        require(isinstance(meta, dict) and set(meta) == {"venture_id", "created_at", "config", "schema_version"}
                and meta["venture_id"] == payload["venture_id"] and meta["schema_version"] == VERSION,
                "Invalid backup metadata")
        validate_config(meta["config"])
        try:
            require(datetime.fromisoformat(meta["created_at"]).utcoffset() == timezone.utc.utcoffset(None),
                    "Invalid workspace timestamp")
        except (TypeError, ValueError) as error:
            raise SeedError("Invalid workspace timestamp") from error
    return payload


def import_on(workspace, cx, payload):
    cx.execute("BEGIN IMMEDIATE")
    metadata = workspace.meta_on(cx)
    if payload["venture_id"] != metadata["venture_id"]:
        raise Conflict("Transfer belongs to another venture")
    staged = []
    for record in sorted(payload["records"], key=lambda r: (r["id"], r["revision"])):
        old = workspace.get_on(cx, record["id"], record["revision"])
        if old and old["digest"] != record["digest"]:
            raise Conflict("Conflicting stored revision. Review both versions before retrying.")
        if not old:
            workspace.insert_record(cx, record)
            staged.append(record)
    for record in staged:
        workspace.check_links(cx, record)
        workspace.insert_links(cx, record)
    for record_id in {r["id"] for r in staged if r["kind"] == "venture"}:
        profile = workspace.get_on(cx, record_id)
        cx.execute("UPDATE workspace SET config=? WHERE singleton=1", (canonical(profile["data"]).decode(),))
    return {"imported_revisions": len(staged), "already_present": len(payload["records"]) - len(staged)}


def import_bundle(path, bundle, confirmation, *, create=False, config=None):
    payload = validate_bundle(bundle)
    require(confirmation == bundle["sha256"], "Import approval does not match the transfer payload")
    ws = Workspace(path)
    if not create:
        require(payload["purpose"] == "exchange", "Restore backups into a new workspace")
        with ws.connect() as cx:
            return import_on(ws, cx, payload)
    meta = payload.get("workspace") or {}
    profiles = [r for r in payload["records"] if r["kind"] == "venture"]
    head = max(profiles, key=lambda r: r["revision"])["data"] if profiles else None
    if meta and head:
        require(meta["config"] == head, "Backup profile and configuration disagree")
    ws = Workspace.init(path, head or meta.get("config") or config, venture_id=payload["venture_id"],
                        created_at=meta.get("created_at"), seed_venture=False)
    try:
        with ws.connect() as cx:
            result = import_on(ws, cx, payload)
        ws.validate()
        return result
    except BaseException:
        ws.database.unlink(missing_ok=True)
        ws.internal.rmdir()
        raise
