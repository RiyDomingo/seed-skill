# Use a private venture workspace

Keep separate ventures in separate local directories outside all Git
checkouts. Select every workspace explicitly. Python 3.12 through 3.14
suffices and no database server is required.

```sh
seed_workspace="$(mktemp -d)"
python3 -m seed_core --workspace "$seed_workspace" init \
  --name "Synthetic venture" --currency USD --jurisdiction US
python3 -m seed_core --workspace "$seed_workspace" validate
```

In a packaged skill, run `python3 <skill directory>/scripts/seed_workspace.py`
in place of `python3 -m seed_core`. Each package ships the same canonical
workspace implementation.

## Capture and use original skill inputs

```sh
python3 -m seed_core --workspace "$seed_workspace" migrate /path/to/legacy/seed
python3 -m seed_core --workspace "$seed_workspace" migrate /path/to/legacy/seed --apply
python3 -m seed_core --workspace "$seed_workspace" materialize "$seed_workspace/current-run"
```

Materialization writes known JSON files to a new directory. Pass that
directory to the original tool using `--dir` where available, or
materialize a folder named `seed` within a fresh private working directory.
The original tools use the same JSON contracts they used in P1. The imported
legacy files are provenance-unknown, restricted snapshots. Unknown legacy
files and document attachments stay in the source directory. Quarantine
reports contain diagnostics and filenames, while original bytes stay in
place. The migration is create-only. Handle a changed source through an
explicit record revision after checking it.

## Review, exchange and restore

Use `put` with a JSON file for record data and optionally `--links` with a
JSON array of pinned references. Use the current revision with `--expected`
to update a record. The command preserves earlier revisions. Run `affected
RECORD_ID` after updating a dependency to identify stale outputs for review.

1. Run `preview-export` with the desired record IDs and classification.
   Public is the default. Check the IDs, classification and digest. Linked
   revisions and their dependency history accompany selected records.
2. Run `export /approved/private/path/exchange.json --confirm SHA256` with
   the same selection. A changed payload requires a new review. Validate the
   intended destination and recipient before sharing. Upload only records
   approved for the receiving ChatGPT workspace. Restricted data and raw
   legacy snapshots are excluded from exchanges.
3. In the receiving environment, run `inspect-transfer exchange.json`.
   Import with `import exchange.json --confirm SHA256`. Use `--create`
   in a fresh directory to establish the same venture ID. Supply
   `--config local-config.json` if the export excluded the venture profile.
4. Run `validate`. Use a new export to return reviewed changes. Imports
   insert matching histories and refuse conflicting revisions or a different
   venture ID. Later stale copies never replace newer local work.

ChatGPT and Work exchanges are explicit file upload and download operations.
Approval of a digest protects against payload drift. A digest does not
authenticate the sender, encrypt the file, or grant disclosure permission.
Inspect and validate inputs in the destination and protect local copies with
the OS account, storage encryption and workspace permissions.

Run `backup snapshot.json` to write a complete private JSON backup under
the workspace's `backups` directory. Restore using `inspect-transfer` and
`import --create --confirm SHA256` in a separate empty workspace. Compare
`validate` results before adopting the restored directory. Back up separate
documents outside the record store through the same private storage process.

For larger histories, `backup-db snapshot.sqlite3` uses SQLite's online
backup API without the hosted-transfer size ceiling. Keep this file private.
Run `inspect-backup-db FILE` to get its SHA-256 and
`restore-db FILE --confirm SHA256` into a new workspace. Restore checks the
snapshot identity, version, SQLite integrity and record hashes. Never upload
a full backup to a shared or hosted workspace.

Use `capture seed/model.json --links pinned-inputs.json` to register a fresh
legacy output. To save a changed output, supply its latest revision using
`--expected`. For Markdown, HTML and other generated files inside the
workspace, use `register-output` with the relative path and exact input links.
