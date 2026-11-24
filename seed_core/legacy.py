"""Inventory, validate and safely snapshot legacy SEED JSON inputs."""

from hashlib import sha256
from pathlib import Path

from .schema import MAX_BYTES, SeedError, canonical, forbid_secrets, parse_json, require
from .transfer import write_new
from .workspace import Conflict, Workspace, identity, plain, private_root

# Names and representative top-level fields of the upstream file contracts.
FILES = {
    "config.json": {"startup": (dict,)},
    "market.json": {"tam": (int, float, dict)},
    "competitors.json": {"apps": (list,)},
    "assumptions.json": {"company": (str,), "start_month": (str,), "currency": (str,)},
    "model.json": {"assumptions": (dict,), "summary": (dict,), "months": (list,)},
    "plan.json": {"sections": (list,)},
    "investors.json": {"investors": (list,)},
    "pipeline.json": {"investors": (list,)},
    "metrics.json": {"months": (list,)},
}
ORDER = {
    "assumptions.json": ("config.json",),
    "model.json": ("assumptions.json",),
    "plan.json": ("config.json", "market.json", "competitors.json", "model.json"),
    "pipeline.json": ("config.json", "investors.json"),
    "metrics.json": ("config.json",),
}


def inventory(source):
    root = Path(source)
    require(plain(root) and root.is_dir(), "Legacy source directory is missing or linked")
    rows = []
    for name in sorted(FILES):
        path = root / name
        if not plain(path):
            rows.append((name, "quarantine", None, "linked file"))
        elif not path.exists():
            continue
        elif not path.is_file():
            rows.append((name, "quarantine", None, "nonregular file"))
        else:
            try:
                with path.open("rb") as stream:
                    raw = stream.read(MAX_BYTES + 1)
                data = parse_json(raw)
                require(isinstance(data, dict) and all(type(data.get(field)) in types
                        for field, types in FILES[name].items()), "Missing or invalid legacy fields")
                forbid_secrets(data)
            except (OSError, SeedError) as error:
                rows.append((name, "quarantine", None,
                             str(error) if isinstance(error, SeedError) else "could not read file"))
            else:
                rows.append((name, "ready", {"filename": name, "sha256": sha256(raw).hexdigest(),
                                             "document": data, "provenance_note": "Unverified legacy snapshot. Filename associations do not verify provenance"}, None))
    return rows


def migrate(workspace, source, *, dry_run=True):
    rows = inventory(source)
    statuses = []
    with workspace.connect() as cx:
        cx.execute("BEGIN" if dry_run else "BEGIN IMMEDIATE")
        vid = workspace.meta_on(cx)["venture_id"]
        ordered = sorted(rows, key=lambda row: row[0] in ORDER)
        # Resolve known inputs in dependency order. Unknown input provenance stays unknown.
        records = {}
        for name in FILES:
            record = Workspace.get_on(cx, identity(vid, "legacy", name))
            if record:
                records[name] = record
        for name, state, data, reason in ordered:
            prior = records.get(name)
            if prior and state == "ready":
                state = "duplicate" if prior["data"]["sha256"] == data["sha256"] else "conflict"
            statuses.append({"name": name, "status": state, "reason": reason})
        if dry_run:
            return statuses
        if any(row["status"] == "conflict" for row in statuses):
            raise Conflict("Legacy source conflicts with a saved snapshot. Inventory the migration first.")
        candidates = {name: data for name, state, data, _reason in rows if state == "ready" and name not in records}
        while candidates:
            ready = [name for name in candidates if not (set(ORDER.get(name, ())) & candidates.keys())]
            for name in ready:
                links = [{"id": records[dep]["id"], "revision": records[dep]["revision"], "role": "dependency"}
                         for dep in ORDER.get(name, ()) if dep in records]
                records[name] = Workspace.put_on(cx, "legacy", name, candidates.pop(name),
                                                 classification="restricted", links=links)
        quarantined = [row for row in statuses if row["status"] == "quarantine"]
        if quarantined:
            # Preserve only safe diagnostic metadata. The quarantined source bytes stay untouched.
            report = {"summary": "Quarantined legacy inputs", "entries": quarantined}
            key = "quarantine:" + sha256(canonical(report)).hexdigest()
            Workspace.put_on(cx, "decision", key, report, classification="restricted")
    return statuses


def materialize(workspace, target, *, names=None):
    root = private_root(target)
    require(not root.exists(), "Materialize into a new private directory")
    selected = set(names) if names else None
    with workspace.connect() as cx:
        cx.execute("BEGIN")
        records = workspace.list_on(cx, "legacy")
        if selected:
            require(selected <= {r["key"] for r in records}, "Requested legacy snapshot is missing")
            records = [r for r in records if r["key"] in selected]
        pending = list(records)
        seen = set()
        while pending:
            record = pending.pop()
            if record["id"] in seen:
                continue
            seen.add(record["id"])
            for ref in record["links"]:
                latest = workspace.get_on(cx, ref["id"])
                require(latest and latest["revision"] == ref["revision"],
                        "Stale legacy dependency. Select only current inputs and regenerate the output.")
                pending.append(latest)
    root.mkdir(mode=0o700)
    written = []
    try:
        for record in records:
            name = record["data"]["filename"]
            require(name in FILES and name == record["key"], "Unexpected legacy filename")
            written.append(write_new(root / name, canonical(record["data"]["document"]) + b"\n"))
    except BaseException:
        for path in written:
            path.unlink(missing_ok=True)
        root.rmdir()
        raise
    return [path.name for path in written]


def capture(workspace, path, *, expected=None, links=()):
    """Record an explicit revision of one original CLI JSON artifact."""
    path = Path(path)
    require(path.name in FILES, "Unsupported legacy JSON filename")
    row = next((row for row in inventory(path.parent) if row[0] == path.name), None)
    require(row is not None and row[1] == "ready", "Legacy output is missing or failed validation")
    return workspace.put("legacy", path.name, row[2], expected=expected,
                         links=list(links), classification="restricted")
