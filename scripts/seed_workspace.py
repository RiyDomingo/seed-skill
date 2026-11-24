"""Run the bundled SEED workspace CLI without installing Python dependencies."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from seed_core.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
