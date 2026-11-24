"""Load a script from a skill folder (the folder names have hyphens)."""

import importlib.util
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "tests", "fixtures")


def load(folder, name):
    path = os.path.join(ROOT, folder, name + ".py")
    spec = importlib.util.spec_from_file_location("seed_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod



def symlink(test, source, target, *, directory=False):
    try:
        os.symlink(source, target, target_is_directory=directory)
    except OSError as error:
        if getattr(error, "winerror", None) == 1314:
            test.skipTest("Windows runner lacks permission to create symbolic links")
        raise
