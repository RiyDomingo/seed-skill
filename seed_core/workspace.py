"""Isolated SQLite workspaces with immutable, content-addressed revisions."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from uuid import UUID, uuid4, uuid5

from .schema import (
    KINDS, LEVELS, LINK_ROLES, VERSION, SeedError, canonical, date_value, digest, identifier, key_value,
    require, validate_config, validate_record,
)

APPLICATION_ID = 0x53454544
DB_DIRECTORY = ".seed"
DB_NAME = "venture.sqlite3"
DDL = """
CREATE TABLE workspace (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    venture_id TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    config TEXT NOT NULL
);
CREATE TABLE entity (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    natural_key TEXT NOT NULL,
    UNIQUE (kind, natural_key)
);
CREATE TABLE revision (
    id TEXT NOT NULL REFERENCES entity(id),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    saved_at TEXT NOT NULL,
    classification TEXT NOT NULL,
    provenance TEXT NOT NULL,
    status TEXT NOT NULL,
    data TEXT NOT NULL,
    digest TEXT NOT NULL,
    PRIMARY KEY (id, revision)
);
CREATE TABLE record_link (
    id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    target_id TEXT NOT NULL,
    target_revision INTEGER NOT NULL,
    role TEXT NOT NULL,
    PRIMARY KEY (id, revision, target_id, target_revision, role),
    FOREIGN KEY (id, revision) REFERENCES revision(id, revision),
    FOREIGN KEY (target_id, target_revision) REFERENCES revision(id, revision)
);
CREATE INDEX reverse_record_link ON record_link(target_id, target_revision);
"""


class Conflict(SeedError):
    """The saved record changed or cannot be reconciled safely."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def plain(path):
    return not path.is_symlink() and not path.is_junction()


def private_root(path):
    path = Path(path).expanduser()
    require(plain(path), "Linked workspace path refused")
    root = path.resolve()
    require(not any((p / ".git").exists() or (p / ".git").is_symlink()
                    for p in (root, *root.parents)), "Venture data must be outside Git checkouts")
    return root


def identity(venture_id, kind, key):
    return str(uuid5(UUID(venture_id), f"{kind}:{key}"))


def record_digest(record):
    return digest({k: v for k, v in record.items() if k != "digest"})


class Workspace:
    def __init__(self, path):
        self.root = private_root(path)
        self.internal = self.root / DB_DIRECTORY
        self.database = self.internal / DB_NAME
        require(plain(self.internal) and plain(self.database), "Linked workspace database refused")
        for name in ("-journal", "-wal", "-shm"):
            companion = self.database.with_name(DB_NAME + name)
            require(plain(companion) and (not companion.exists() or companion.is_file()),
                    "Workspace database companion is not a regular file")

    @classmethod
    def init(cls, path, config, *, venture_id=None, created_at=None, seed_venture=True):
        validate_config(config)
        ws = cls(path)
        ws.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            ws.internal.mkdir(mode=0o700)
        except FileExistsError as error:
            raise SeedError("Workspace already exists or initialization needs recovery") from error
        try:
            with ws.database.open("xb"):
                pass
            if os.name != "nt":
                ws.database.chmod(0o600)
            with ws.connect(validate=False) as cx:
                cx.executescript(DDL)
                cx.execute(f"PRAGMA application_id={APPLICATION_ID}")
                cx.execute(f"PRAGMA user_version={VERSION}")
                vid = identifier(venture_id) if venture_id else str(uuid4())
                cx.execute("INSERT INTO workspace VALUES (1,?,?,?)", (vid, created_at or now(),
                                                                      canonical(config).decode()))
                if seed_venture:
                    ws.put_on(cx, "venture", "profile", config, provenance="founder",
                              classification="internal")
        except BaseException:
            ws.database.unlink(missing_ok=True)
            ws.internal.rmdir()
            raise
        return ws

    @contextmanager
    def connect(self, *, validate=True):
        require(plain(self.internal) and plain(self.database) and self.database.is_file(),
                "Workspace database is missing or linked. Initialize a private workspace first.")
        db = sqlite3.connect(self.database.as_uri() + "?mode=rw", uri=True, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA trusted_schema=OFF")
            if validate:
                require(db.execute("PRAGMA application_id").fetchone()[0] == APPLICATION_ID
                        and db.execute("PRAGMA user_version").fetchone()[0] == VERSION,
                        "Unsupported workspace or schema version")
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def meta_on(cx):
        row = cx.execute("SELECT venture_id, created_at, config FROM workspace WHERE singleton=1").fetchone()
        require(row is not None, "Missing workspace configuration")
        return {"venture_id": identifier(row["venture_id"]), "created_at": row["created_at"],
                "config": json.loads(row["config"]), "schema_version": VERSION}

    def metadata(self):
        with self.connect() as cx:
            return self.meta_on(cx)

    @staticmethod
    def get_on(cx, record_id, revision=None):
        identifier(record_id)
        row = cx.execute(
            """SELECT e.kind,e.natural_key,r.* FROM entity e JOIN revision r USING(id)
               WHERE r.id=? AND (? IS NULL OR r.revision=?) ORDER BY r.revision DESC LIMIT 1""",
            (record_id, revision, revision),
        ).fetchone()
        if row is None:
            return None
        links = cx.execute(
            """SELECT target_id AS id,target_revision AS revision,role FROM record_link
               WHERE id=? AND revision=? ORDER BY target_id,target_revision,role""",
            (record_id, row["revision"]),
        )
        return {"id": row["id"], "kind": row["kind"], "key": row["natural_key"],
                "revision": row["revision"], "saved_at": row["saved_at"],
                "classification": row["classification"], "provenance": row["provenance"],
                "status": row["status"], "data": json.loads(row["data"]),
                "links": [dict(link) for link in links], "digest": row["digest"]}

    def get(self, record_id, revision=None):
        with self.connect() as cx:
            return self.get_on(cx, record_id, revision)

    def list(self, kind=None, *, history=False):
        with self.connect() as cx:
            return self.list_on(cx, kind, history=history)

    @classmethod
    def list_on(cls, cx, kind=None, *, history=False):
        require(kind is None or kind in KINDS, "Unknown record kind")
        query = "SELECT e.id,r.revision FROM entity e JOIN revision r USING(id) WHERE (? IS NULL OR e.kind=?)"
        if not history:
            query += " AND r.revision=(SELECT MAX(revision) FROM revision WHERE id=e.id)"
        query += " ORDER BY e.kind,e.natural_key,r.revision"
        return [cls.get_on(cx, row["id"], row["revision"]) for row in cx.execute(query, (kind, kind))]

    @classmethod
    def check_links(cls, cx, record):
        for link in record["links"]:
            target = cls.get_on(cx, link["id"], link["revision"])
            require(target is not None and target["kind"] in LINK_ROLES[link["role"]],
                    "Invalid or missing pinned dependency")
            require(target["id"] != record["id"], "A record cannot reference itself")
            require(LEVELS.index(record["classification"]) >= LEVELS.index(target["classification"]),
                    "Record is less confidential than its dependency")
            if record["kind"] == "claim" and record["provenance"] == "verified_external":
                if link["role"] == "evidence":
                    require(target["status"] in {"reviewed", "approved"},
                            "Verified claims require reviewed evidence records")

    @staticmethod
    def insert_record(cx, record):
        cx.execute("INSERT OR IGNORE INTO entity VALUES (?,?,?)",
                   (record["id"], record["kind"], record["key"]))
        cx.execute("INSERT INTO revision VALUES (?,?,?,?,?,?,?,?)",
                   (record["id"], record["revision"], record["saved_at"], record["classification"],
                    record["provenance"], record["status"], canonical(record["data"]).decode(), record["digest"]))

    @staticmethod
    def insert_links(cx, record):
        cx.executemany("INSERT INTO record_link VALUES (?,?,?,?,?)", [
            (record["id"], record["revision"], link["id"], link["revision"], link["role"])
            for link in record["links"]
        ])

    @classmethod
    def put_on(cls, cx, kind, key, data, *, expected=None, classification="internal",
               provenance="unknown", status="draft", links=None):
        links = [] if links is None else links
        validate_record(kind, data, provenance, classification, status, links)
        links = sorted(links, key=lambda link: (link["id"], link["revision"], link["role"]))
        require(expected is None or type(expected) is int and expected > 0, "Invalid expected revision")
        require(kind != "venture" or key_value(key) == "profile", "A workspace has one venture profile")
        key = key_value(key)
        workspace = cls.meta_on(cx)
        record_id = identity(workspace["venture_id"], kind, key)
        previous = cls.get_on(cx, record_id)
        content = {"classification": classification, "provenance": provenance, "status": status,
                   "data": data, "links": links}
        if previous and canonical({k: previous[k] for k in content}) == canonical(content):
            return previous
        if (previous["revision"] if previous else None) != expected:
            raise Conflict("Expected revision does not match the stored record")
        if previous:
            require(LEVELS.index(classification) >= LEVELS.index(previous["classification"]),
                    "Cannot lower classification of a revision chain")
        record = {"id": record_id, "kind": kind, "key": key, "revision": (expected or 0) + 1,
                  "saved_at": now(), **content}
        record["digest"] = record_digest(record)
        cls.check_links(cx, record)
        cls.insert_record(cx, record)
        cls.insert_links(cx, record)
        if kind == "venture":
            cx.execute("UPDATE workspace SET config=? WHERE singleton=1", (canonical(data).decode(),))
        return record

    def put(self, kind, key, data, **options):
        with self.connect() as cx:
            cx.execute("BEGIN IMMEDIATE")
            return self.put_on(cx, kind, key, data, **options)

    def affected(self, record_id):
        with self.connect() as cx:
            origin = self.get_on(cx, record_id)
            require(origin is not None, "Unknown record")
            rows = cx.execute(
                """WITH RECURSIVE affected(id,revision) AS (
                     SELECT id,revision FROM record_link WHERE target_id=? AND target_revision<?
                     UNION SELECT r.id,r.revision FROM record_link r JOIN affected a
                     ON r.target_id=a.id AND r.target_revision=a.revision
                   ) SELECT DISTINCT id,revision FROM affected a
                     WHERE revision=(SELECT MAX(revision) FROM revision WHERE id=a.id)
                     ORDER BY id""", (record_id, origin["revision"]),
            )
            return [self.get_on(cx, row["id"], row["revision"]) for row in rows]

    def trace(self, record_id, on):
        day = date_value(on, "review date")
        with self.connect() as cx:
            cx.execute("BEGIN")
            current = self.get_on(cx, record_id)
            require(current is not None, "Unknown record")
            records = []
            findings = []
            seen = set()
            queue = [current]
            while queue:
                record = queue.pop()
                node = (record["id"], record["revision"])
                if node in seen:
                    continue
                seen.add(node)
                records.append(record)
                data = record["data"]
                if record["status"] == "disputed":
                    findings.append({"id": record["id"], "type": "disputed"})
                if data.get("valid_until") and date_value(data["valid_until"], "valid_until") < day:
                    findings.append({"id": record["id"], "type": "expired"})
                if record["kind"] == "source" and data.get("max_age_days") is not None:
                    age = (day - date_value(data["retrieved_on"], "retrieved_on")).days
                    if age > data["max_age_days"]:
                        findings.append({"id": record["id"], "type": "stale_source"})
                for link in record["links"]:
                    target = self.get_on(cx, link["id"], link["revision"])
                    latest = self.get_on(cx, link["id"])
                    require(target is not None, "Missing pinned revision")
                    if latest["revision"] != target["revision"]:
                        findings.append({"id": record["id"], "type": "stale_dependency",
                                         "target": target["id"], "pinned": target["revision"],
                                         "latest": latest["revision"]})
                    if link["role"] == "contradicts":
                        findings.append({"id": record["id"], "type": "conflicting_evidence",
                                         "target": target["id"]})
                    queue.append(target)
            return {"records": records, "findings": findings}

    def validate(self):
        with self.connect() as cx:
            cx.execute("BEGIN")
            require(cx.execute("PRAGMA quick_check").fetchone()[0] == "ok"
                    and not cx.execute("PRAGMA foreign_key_check").fetchone(), "Database integrity failure")
            metadata = self.meta_on(cx)
            validate_config(metadata["config"])
            history = self.list_on(cx, history=True)
            heads = {}
            for record in history:
                self.validate_revision(cx, metadata["venture_id"], record, heads.get(record["id"]))
                heads[record["id"]] = record
            profile = self.get_on(cx, identity(metadata["venture_id"], "venture", "profile"))
            if profile:
                require(profile["data"] == metadata["config"], "Workspace configuration mismatch")
            return {"venture_id": metadata["venture_id"], "records": len(heads), "revisions": len(history)}

    @classmethod
    def validate_revision(cls, cx, venture_id, record, previous):
        require(record["kind"] != "venture" or record["key"] == "profile", "Invalid venture profile")
        require(record["key"] == key_value(record["key"])
                and record["id"] == identity(venture_id, record["kind"], record["key"])
                and record["digest"] == record_digest(record), "Record identity or integrity check failed")
        require(type(record["revision"]) is int and record["revision"] == (previous["revision"] if previous else 0) + 1,
                "Non-contiguous revision history")
        try:
            saved = datetime.fromisoformat(record["saved_at"])
            require(saved.utcoffset() == timezone.utc.utcoffset(saved), "Non-UTC revision timestamp")
        except (ValueError, TypeError) as error:
            raise SeedError("Invalid revision timestamp") from error
        validate_record(record["kind"], record["data"], record["provenance"], record["classification"],
                        record["status"], record["links"])
        if previous:
            require(LEVELS.index(record["classification"]) >= LEVELS.index(previous["classification"]),
                    "Invalid disclosure transition")
        if cx is not None:
            cls.check_links(cx, record)
