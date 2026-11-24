import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from _load import symlink, ROOT

SCRIPT = Path(ROOT) / "scripts" / "skills.py"
SPEC = importlib.util.spec_from_file_location("seed_skills", SCRIPT)
skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skills)


class Packaging(unittest.TestCase):
    def test_every_archive_matches_installed_files_and_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(skills.main(["install", "codex", "--project", str(project)]), 0)
                self.assertEqual(skills.main(["package", "--output", str(root / "zip")]), 0)
            for name, resources in skills.FILES.items():
                with self.subTest(name=name):
                    install = project / ".agents" / "skills" / name
                    script = resources[0] if resources else "scripts/seed_workspace.py"
                    expected = {*skills.COMMON, *skills.SHARED, "LICENSE", *resources}
                    self.assertEqual({p.relative_to(install).as_posix() for p in install.rglob("*") if p.is_file()},
                                     expected)
                    with zipfile.ZipFile(root / "zip" / f"{name}.zip") as bundle:
                        self.assertEqual(set(bundle.namelist()), {f"{name}/{item}" for item in expected})
                        self.assertIsNone(bundle.testzip())
                        for item in expected:
                            self.assertEqual(bundle.read(f"{name}/{item}"), (install / item).read_bytes())
                    result = subprocess.run([sys.executable, str(install / script), "--help"], cwd=project,
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_install_locations_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            targets = [
                (["codex", "--user"], root / ".agents/skills"),
                (["manual", "--destination", str(root / "manual")], root / "manual"),
            ]
            (root / "project").mkdir()
            with patch.object(skills.Path, "home", return_value=root), contextlib.redirect_stdout(io.StringIO()):
                for args, destination in targets:
                    with self.subTest(args=args):
                        command = ["install", *args, "--skill", "seed-model"]
                        self.assertEqual(skills.main(command), 0)
                        existing = destination / "seed-model/SKILL.md"
                        existing.write_text("Existing local customization.")
                        with contextlib.redirect_stderr(io.StringIO()):
                            self.assertEqual(skills.main(command), 1)
                        self.assertEqual(existing.read_text(), "Existing local customization.")

    def test_install_refuses_redirected_host_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            outside = root / "outside"
            project.mkdir()
            outside.mkdir()
            symlink(self, outside, project / ".agents", directory=True)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                skills.main(["install", "codex", "--project", str(project)])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(list(outside.iterdir()), [])

    def test_archive_copy_failure_removes_only_new_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "existing.txt"
            existing.write_text("Keep")
            copy = skills.shutil.copyfileobj

            def interrupt_second(source, destination):
                if destination.name.endswith("seed-model.zip"):
                    destination.write(b"incomplete")
                    raise OSError("Synthetic write error")
                return copy(source, destination)

            with patch.object(skills.shutil, "copyfileobj", side_effect=interrupt_second):
                with self.assertRaisesRegex(OSError, "Synthetic write error"):
                    skills.publish(root, ["seed-market", "seed-model"], archive=True)
            self.assertEqual(list(root.iterdir()), [existing])

    def test_package_refuses_link_and_excludes_unlisted_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "seed-market"
            source.mkdir()
            inputs = [*skills.COMMON, *skills.FILES["seed-market"]]
            for item in inputs:
                path = source / item
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("Public fixture")
            for path in skills.SHARED.values():
                item = root / path
                item.parent.mkdir(parents=True, exist_ok=True)
                item.write_text("Public shared fixture")
            (root / "LICENSE").write_text("Fixture licence")
            private = source / "private.json"
            private.write_text("Private fixture")
            with patch.object(skills, "ROOT", root):
                target, = skills.publish(root / "safe", ["seed-market"], archive=True)
                with zipfile.ZipFile(target) as bundle:
                    self.assertNotIn("seed-market/private.json", bundle.namelist())
                entry = source / "market.py"
                entry.unlink()
                symlink(self, private, entry)
                with self.assertRaisesRegex(ValueError, "without symlinks"):
                    skills.publish(root / "blocked", ["seed-market"], archive=True)
                self.assertFalse((root / "blocked").exists())


class PackagedWorkspace(unittest.TestCase):
    def test_installed_adapter_reuses_venture_inputs_and_records_new_plan(self):
        import json
        from _load import FIX

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(skills.main(["install", "codex", "--project", str(root),
                                              "--skill", "seed-plan"]), 0)
            package = root / ".agents/skills/seed-plan"
            executable = package / "scripts/seed_workspace.py"

            def core(*args):
                result = subprocess.run([sys.executable, str(executable), "--workspace",
                                         str(root / "venture"), *map(str, args)], cwd=root,
                                        capture_output=True, text=True, encoding="utf-8", timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            core("init", "--name", "Synthetic cross-skill venture", "--currency", "USD", "--jurisdiction", "US")
            source = Path(FIX) / "seed-plan/leashly"
            migrated = core("migrate", source, "--apply")
            self.assertEqual(len([row for row in migrated if row["status"] == "ready"]), 5)
            target = root / "venture/seed"
            core("materialize", target)
            result = subprocess.run([sys.executable, str(package / "plan.py"), "build", "--dir", str(target),
                                     "--today", "2026-10-26"], capture_output=True, text=True,
                                    encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Every check passed", result.stdout)
            inputs = [record for record in core("list", "--kind", "legacy") if record["key"] != "plan.json"]
            links = root / "links.json"
            links.write_text(json.dumps([{"id": row["id"], "revision": row["revision"], "role": "dependency"}
                                         for row in inputs]))
            captured = core("capture", target / "plan.json", "--links", links, "--expected", 1)
            self.assertEqual(captured["revision"], 2)
            self.assertEqual(len(captured["links"]), 4)
            output = core("register-output", "seed/plan.md", "--name", "Synthetic plan",
                          "--document-type", "plan", "--links", links)
            self.assertEqual(output["classification"], "restricted")
            self.assertEqual(core("validate")["records"], 7)
            self.assertEqual(core("preview-export")["record_ids"], [])
