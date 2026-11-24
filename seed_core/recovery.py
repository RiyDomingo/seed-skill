"""Verified online SQLite snapshots for complete local recovery."""

from hashlib import file_digest
import os
from pathlib import Path
import sqlite3
import tempfile

from .schema import require
from .workspace import APPLICATION_ID, VERSION, Workspace, plain, private_root


def checksum(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def verify_file(path, expected=None):
    path = Path(path)
    require(plain(path) and path.is_file(), "Backup must be a nonlinked regular file")
    result = checksum(path)
    require(expected is None or result == expected, "Backup checksum mismatch")
    return path, result


def copy_database(source, target):
    db = sqlite3.connect(source.as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        db.execute("PRAGMA trusted_schema=OFF")
        require(db.execute("PRAGMA application_id").fetchone()[0] == APPLICATION_ID
                and db.execute("PRAGMA user_version").fetchone()[0] == VERSION,
                "Unsupported database backup")
        destination = sqlite3.connect(target)
        try:
            db.backup(destination)
        finally:
            destination.close()
    finally:
        db.close()


def make_backup(workspace, name):
    require(isinstance(name, str) and name.endswith(".sqlite3") and Path(name).name == name
            and "\\" not in name and ":" not in name, "Use a plain .sqlite3 backup filename")
    folder = workspace.root / "backups"
    require(plain(folder), "Linked backups folder refused")
    folder.mkdir(mode=0o700, exist_ok=True)
    target = folder / name
    require(not os.path.lexists(target), "Backup already exists")
    with tempfile.TemporaryDirectory(dir=folder, prefix=".seed-db-") as hold:
        staged = Workspace(Path(hold) / "verification")
        staged.internal.mkdir(parents=True, mode=0o700)
        with staged.database.open("xb"):
            pass
        if os.name != "nt":
            staged.database.chmod(0o600)
        with workspace.connect() as source:
            destination = sqlite3.connect(staged.database)
            try:
                source.backup(destination)
            finally:
                destination.close()
        result = staged.validate()
        fingerprint = checksum(staged.database)
        with target.open("xb"):
            pass
        try:
            os.replace(staged.database, target)
        except BaseException:
            target.unlink(missing_ok=True)
            raise
    return {"file": str(target), "sha256": fingerprint, **result}


def restore_backup(path, source, confirmation):
    source, fingerprint = verify_file(source, confirmation)
    target = Workspace(path)
    root = private_root(target.root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=root, prefix=".seed-restore-") as hold:
        staged = Workspace(Path(hold))
        staged.internal.mkdir(mode=0o700)
        with staged.database.open("xb"):
            pass
        if os.name != "nt":
            staged.database.chmod(0o600)
        copy_database(source.resolve(), staged.database)
        require(checksum(source) == fingerprint, "Backup changed during verification")
        result = staged.validate()
        target.internal.mkdir(mode=0o700)
        try:
            os.replace(staged.database, target.database)
        except BaseException:
            target.internal.rmdir()
            raise
    return result
